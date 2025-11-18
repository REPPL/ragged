"""Tests for comprehensive health check system.

v0.2.9: Tests for enhanced health checks with deep diagnostics.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psutil  # type: ignore[import-untyped]

from src.utils.health import (
    HealthChecker,
    HealthStatus,
    HealthCheckResult,
)


@pytest.fixture
def health_checker():
    """Create health checker instance for testing."""
    return HealthChecker()


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_is_healthy(self):
        """Test is_healthy method."""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="All good",
        )
        assert result.is_healthy() is True
        assert result.is_degraded() is False
        assert result.is_unhealthy() is False

    def test_is_degraded(self):
        """Test is_degraded method."""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.DEGRADED,
            message="Warning",
        )
        assert result.is_healthy() is False
        assert result.is_degraded() is True
        assert result.is_unhealthy() is False

    def test_is_unhealthy(self):
        """Test is_unhealthy method."""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.UNHEALTHY,
            message="Error",
        )
        assert result.is_healthy() is False
        assert result.is_degraded() is False
        assert result.is_unhealthy() is True


class TestOllamaCheck:
    """Tests for Ollama health check."""

    @patch('src.utils.health.OllamaClient')
    def test_ollama_healthy(self, mock_client_class, health_checker):
        """Test Ollama service healthy."""
        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_client_class.return_value = mock_client

        result = health_checker.check_ollama()

        assert result.name == "ollama"
        assert result.is_healthy()
        assert "running" in result.message.lower()

    @patch('src.utils.health.OllamaClient')
    def test_ollama_unhealthy(self, mock_client_class, health_checker):
        """Test Ollama service not responding."""
        mock_client = Mock()
        mock_client.health_check.return_value = False
        mock_client_class.return_value = mock_client

        result = health_checker.check_ollama()

        assert result.is_unhealthy()
        assert "not responding" in result.message.lower()

    @patch('src.utils.health.OllamaClient')
    def test_ollama_error(self, mock_client_class, health_checker):
        """Test Ollama health check error."""
        mock_client_class.side_effect = Exception("Connection failed")

        result = health_checker.check_ollama()

        assert result.is_unhealthy()
        assert result.error == "Connection failed"


class TestChromaDBCheck:
    """Tests for ChromaDB health check."""

    @patch('src.utils.health.VectorStore')
    def test_chromadb_healthy(self, mock_store_class, health_checker):
        """Test ChromaDB healthy."""
        mock_store = Mock()
        mock_store.health_check.return_value = True
        mock_store.count.return_value = 100
        mock_store_class.return_value = mock_store

        result = health_checker.check_chromadb()

        assert result.is_healthy()
        assert "100" in result.message
        assert result.details["chunk_count"] == 100

    @patch('src.utils.health.VectorStore')
    def test_chromadb_unhealthy(self, mock_store_class, health_checker):
        """Test ChromaDB not responding."""
        mock_store = Mock()
        mock_store.health_check.return_value = False
        mock_store_class.return_value = mock_store

        result = health_checker.check_chromadb()

        assert result.is_unhealthy()


class TestEmbedderCheck:
    """Tests for embedder health check."""

    @patch('src.utils.health.get_embedder')
    def test_embedder_healthy(self, mock_get_embedder, health_checker):
        """Test embedder healthy (fast initialization)."""
        mock_embedder = Mock()
        mock_embedder.embed_text.return_value = [0.1] * 768
        mock_get_embedder.return_value = mock_embedder

        result = health_checker.check_embedder()

        # Should be healthy if init <500ms
        assert result.details is not None
        assert "init_time_ms" in result.details
        assert "embed_time_ms" in result.details

    @patch('src.utils.health.get_embedder')
    def test_embedder_slow_init(self, mock_get_embedder, health_checker):
        """Test embedder with slow initialization."""
        import time

        def slow_embedder():
            time.sleep(0.6)  # >500ms
            mock_embedder = Mock()
            mock_embedder.embed_text.return_value = [0.1] * 768
            return mock_embedder

        mock_get_embedder.side_effect = slow_embedder

        result = health_checker.check_embedder()

        # Should be degraded due to slow init
        assert result.is_degraded()
        assert "slow" in result.message.lower()


class TestDiskSpaceCheck:
    """Tests for disk space health check."""

    @patch('psutil.disk_usage')
    def test_disk_space_healthy(self, mock_disk_usage, health_checker):
        """Test sufficient disk space."""
        mock_usage = Mock()
        mock_usage.free = 10 * (1024 ** 3)  # 10GB
        mock_usage.total = 100 * (1024 ** 3)
        mock_usage.percent = 90.0
        mock_disk_usage.return_value = mock_usage

        result = health_checker.check_disk_space()

        assert result.is_healthy()
        assert result.details["free_gb"] == 10.0

    @patch('psutil.disk_usage')
    def test_disk_space_degraded(self, mock_disk_usage, health_checker):
        """Test low disk space (degraded)."""
        mock_usage = Mock()
        mock_usage.free = 2 * (1024 ** 3)  # 2GB (degraded <5GB)
        mock_usage.total = 100 * (1024 ** 3)
        mock_usage.percent = 98.0
        mock_disk_usage.return_value = mock_usage

        result = health_checker.check_disk_space()

        assert result.is_degraded()
        assert "warning" in result.message.lower()

    @patch('psutil.disk_usage')
    def test_disk_space_critical(self, mock_disk_usage, health_checker):
        """Test critical disk space."""
        mock_usage = Mock()
        mock_usage.free = 0.5 * (1024 ** 3)  # 500MB (critical <1GB)
        mock_usage.total = 100 * (1024 ** 3)
        mock_usage.percent = 99.5
        mock_disk_usage.return_value = mock_usage

        result = health_checker.check_disk_space()

        assert result.is_unhealthy()
        assert "critical" in result.message.lower()


class TestMemoryCheck:
    """Tests for memory availability health check."""

    @patch('psutil.virtual_memory')
    def test_memory_healthy(self, mock_memory, health_checker):
        """Test sufficient memory."""
        mock_mem = Mock()
        mock_mem.available = 8 * (1024 ** 3)  # 8GB
        mock_mem.total = 16 * (1024 ** 3)
        mock_mem.percent = 50.0
        mock_memory.return_value = mock_mem

        result = health_checker.check_memory_available()

        assert result.is_healthy()
        assert result.details["available_gb"] == 8.0

    @patch('psutil.virtual_memory')
    def test_memory_degraded(self, mock_memory, health_checker):
        """Test low memory (degraded)."""
        mock_mem = Mock()
        mock_mem.available = 1.5 * (1024 ** 3)  # 1.5GB (degraded <2GB)
        mock_mem.total = 16 * (1024 ** 3)
        mock_mem.percent = 90.0
        mock_memory.return_value = mock_mem

        result = health_checker.check_memory_available()

        assert result.is_degraded()

    @patch('psutil.virtual_memory')
    def test_memory_critical(self, mock_memory, health_checker):
        """Test critical memory."""
        mock_mem = Mock()
        mock_mem.available = 0.3 * (1024 ** 3)  # 300MB (critical <512MB)
        mock_mem.total = 16 * (1024 ** 3)
        mock_mem.percent = 98.0
        mock_memory.return_value = mock_mem

        result = health_checker.check_memory_available()

        assert result.is_unhealthy()


class TestCacheCheck:
    """Tests for cache status health check."""

    @patch('src.utils.health.get_settings')
    @patch('src.utils.health._embedder_cache', {"default": Mock()})
    def test_cache_healthy(self, mock_get_settings, health_checker):
        """Test cache is healthy (enabled and populated)."""
        mock_settings = Mock()
        mock_settings.feature_flags.enable_embedder_caching = True
        mock_get_settings.return_value = mock_settings

        result = health_checker.check_cache_status()

        assert result.is_healthy()
        assert result.details["cached_embedders"] == 1

    @patch('src.utils.health.get_settings')
    @patch('src.utils.health._embedder_cache', {})
    def test_cache_empty(self, mock_get_settings, health_checker):
        """Test cache is empty (cold start)."""
        mock_settings = Mock()
        mock_settings.feature_flags.enable_embedder_caching = True
        mock_get_settings.return_value = mock_settings

        result = health_checker.check_cache_status()

        assert result.is_degraded()
        assert "empty" in result.message.lower()

    @patch('src.utils.health.get_settings')
    def test_cache_disabled(self, mock_get_settings, health_checker):
        """Test caching is disabled."""
        mock_settings = Mock()
        mock_settings.feature_flags.enable_embedder_caching = False
        mock_get_settings.return_value = mock_settings

        result = health_checker.check_cache_status()

        assert result.is_degraded()
        assert "disabled" in result.message.lower()


class TestDeepChecks:
    """Tests for deep diagnostic checks."""

    @patch('src.utils.health.VectorStore')
    @patch('src.utils.health.get_embedder')
    def test_query_performance_healthy(self, mock_get_embedder, mock_store_class, health_checker):
        """Test query performance is healthy."""
        # Setup mocks
        mock_store = Mock()
        mock_store.count.return_value = 100
        mock_store.query.return_value = {"ids": ["1", "2", "3"]}
        mock_store_class.return_value = mock_store

        mock_embedder = Mock()
        mock_embedder.embed_text.return_value = [0.1] * 768
        mock_get_embedder.return_value = mock_embedder

        result = health_checker.check_query_performance()

        # Fast query should be healthy
        assert result.details is not None
        assert "query_time_ms" in result.details

    @patch('src.utils.health.VectorStore')
    def test_query_performance_no_data(self, mock_store_class, health_checker):
        """Test query performance with no data indexed."""
        mock_store = Mock()
        mock_store.count.return_value = 0
        mock_store_class.return_value = mock_store

        result = health_checker.check_query_performance()

        assert result.is_degraded()
        assert "no data" in result.message.lower()

    @patch('src.utils.health.VectorStore')
    def test_index_integrity_healthy(self, mock_store_class, health_checker):
        """Test index integrity is good."""
        mock_store = Mock()
        mock_store.count.return_value = 100
        mock_store.query.return_value = {
            "ids": ["1", "2"],
            "metadatas": [
                {"document_id": "doc1", "chunk_index": 0},
                {"document_id": "doc2", "chunk_index": 0},
            ],
        }
        mock_store_class.return_value = mock_store

        result = health_checker.check_index_integrity()

        assert result.is_healthy()

    @patch('src.utils.health.VectorStore')
    def test_index_integrity_missing_metadata(self, mock_store_class, health_checker):
        """Test index with missing metadata."""
        mock_store = Mock()
        mock_store.count.return_value = 100
        mock_store.query.return_value = {
            "ids": ["1", "2"],
            "metadatas": [
                {"document_id": "doc1"},  # Missing chunk_index
                {"chunk_index": 0},  # Missing document_id
            ],
        }
        mock_store_class.return_value = mock_store

        result = health_checker.check_index_integrity()

        assert result.is_degraded()

    @patch('src.utils.health.OllamaClient')
    def test_network_latency_healthy(self, mock_client_class, health_checker):
        """Test network latency is healthy."""
        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_client_class.return_value = mock_client

        result = health_checker.check_network_latency()

        # Fast response should be healthy
        assert result.details is not None
        assert "latency_ms" in result.details


class TestHealthCheckerAggregation:
    """Tests for health checker aggregation methods."""

    def test_run_basic_checks(self, health_checker):
        """Test running basic checks returns all basic checks."""
        with patch.object(health_checker, 'check_ollama') as mock_ollama, \
             patch.object(health_checker, 'check_chromadb') as mock_chromadb, \
             patch.object(health_checker, 'check_embedder') as mock_embedder, \
             patch.object(health_checker, 'check_disk_space') as mock_disk, \
             patch.object(health_checker, 'check_memory_available') as mock_memory, \
             patch.object(health_checker, 'check_cache_status') as mock_cache:

            # Setup mocks to return healthy results
            for mock_check in [mock_ollama, mock_chromadb, mock_embedder, mock_disk, mock_memory, mock_cache]:
                mock_check.return_value = HealthCheckResult(
                    name="test",
                    status=HealthStatus.HEALTHY,
                    message="OK",
                )

            results = health_checker.run_basic_checks()

            assert len(results) == 6
            assert all(mock_check.called for mock_check in [mock_ollama, mock_chromadb, mock_embedder, mock_disk, mock_memory, mock_cache])

    def test_run_all_checks_basic_only(self, health_checker):
        """Test run_all_checks without deep flag."""
        with patch.object(health_checker, 'run_basic_checks') as mock_basic, \
             patch.object(health_checker, 'run_deep_checks') as mock_deep:

            mock_basic.return_value = [
                HealthCheckResult(name="test", status=HealthStatus.HEALTHY, message="OK")
            ]

            results = health_checker.run_all_checks(deep=False)

            assert mock_basic.called
            assert not mock_deep.called
            assert len(results) == 1

    def test_run_all_checks_with_deep(self, health_checker):
        """Test run_all_checks with deep flag."""
        with patch.object(health_checker, 'run_basic_checks') as mock_basic, \
             patch.object(health_checker, 'run_deep_checks') as mock_deep:

            mock_basic.return_value = [
                HealthCheckResult(name="basic", status=HealthStatus.HEALTHY, message="OK")
            ]
            mock_deep.return_value = [
                HealthCheckResult(name="deep", status=HealthStatus.HEALTHY, message="OK")
            ]

            results = health_checker.run_all_checks(deep=True)

            assert mock_basic.called
            assert mock_deep.called
            assert len(results) == 2
