"""Tests for metrics storage.

v0.6.4 OPTIMISE-004 Phase 1: Metrics Collection Framework
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ragged.analytics.models import CacheMetrics, ModelMetrics, QueryMetrics, RetrievalMetrics
from ragged.analytics.storage import MetricsStorage


@pytest.fixture
def temp_storage():
    """Create temporary metrics storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metrics.db"
        storage = MetricsStorage(db_path=db_path, retention_days=7, max_size_mb=100)
        yield storage


class TestMetricsStorage:
    """Test suite for MetricsStorage."""

    def test_initialization(self, temp_storage):
        """Test storage initializes correctly."""
        assert temp_storage.db_path.exists()
        assert temp_storage.retention_days == 7
        assert temp_storage.max_size_mb == 100

    def test_store_query_metrics(self, temp_storage):
        """Test storing query metrics."""
        metrics = QueryMetrics(
            query_id="test-query-1",
            query_hash="abc123",
            timestamp=datetime.now(),
            query_length=50,
            query_type="factual",
            complexity=3,
            domain="technical",
            total_latency_ms=250.5,
            selected_model="llama3.2:3b",
            cache_hit=False,
            success=True,
        )

        temp_storage.store_query_metrics(metrics)

        # Verify storage worked (health check shows count)
        health = temp_storage.health_check()
        assert health["table_counts"]["query_metrics"] == 1

    def test_store_retrieval_metrics(self, temp_storage):
        """Test storing retrieval metrics."""
        metrics = RetrievalMetrics(
            retrieval_id="test-retrieval-1",
            query_id="test-query-1",
            timestamp=datetime.now(),
            k=5,
            domain="technical",
            retrieval_latency_ms=150.0,
            results_count=5,
            avg_score=0.85,
            domain_boost_applied=True,
        )

        temp_storage.store_retrieval_metrics(metrics)

        health = temp_storage.health_check()
        assert health["table_counts"]["retrieval_metrics"] == 1

    def test_store_model_metrics(self, temp_storage):
        """Test storing model metrics."""
        metrics = ModelMetrics(
            model_id="llama3.2:3b",
            timestamp=datetime.now(),
            invocation_count=10,
            total_latency_ms=2500.0,
            avg_latency_ms=250.0,
            total_input_tokens=500,
            total_output_tokens=200,
        )

        temp_storage.store_model_metrics(metrics)

        health = temp_storage.health_check()
        assert health["table_counts"]["model_metrics"] == 1

    def test_store_cache_metrics(self, temp_storage):
        """Test storing cache metrics."""
        metrics = CacheMetrics(
            cache_layer="query_classification",
            timestamp=datetime.now(),
            total_requests=100,
            cache_hits=60,
            cache_misses=40,
            hit_rate=0.6,
            cache_size_entries=50,
            cache_size_bytes=1024 * 1024,  # 1MB
        )

        temp_storage.store_cache_metrics(metrics)

        health = temp_storage.health_check()
        assert health["table_counts"]["cache_metrics"] == 1

    def test_cleanup_old_metrics(self, temp_storage):
        """Test retention policy enforcement."""
        # Store old metrics (10 days ago)
        old_timestamp = datetime.now() - timedelta(days=10)
        old_metrics = QueryMetrics(
            query_id="old-query",
            query_hash="old-hash",
            timestamp=old_timestamp,
            query_length=10,
            total_latency_ms=100.0,
            success=True,
        )

        # Store recent metrics
        recent_metrics = QueryMetrics(
            query_id="recent-query",
            query_hash="recent-hash",
            timestamp=datetime.now(),
            query_length=10,
            total_latency_ms=100.0,
            success=True,
        )

        temp_storage.store_query_metrics(old_metrics)
        temp_storage.store_query_metrics(recent_metrics)

        # Verify both stored
        health = temp_storage.health_check()
        assert health["table_counts"]["query_metrics"] == 2

        # Cleanup (retention is 7 days)
        deleted = temp_storage.cleanup_old_metrics()

        # Only old metrics should be deleted
        assert deleted == 1

        health = temp_storage.health_check()
        assert health["table_counts"]["query_metrics"] == 1

    def test_database_size(self, temp_storage):
        """Test database size calculation."""
        # Empty database should be very small
        initial_size = temp_storage.get_database_size_mb()
        assert initial_size < 1.0  # Less than 1MB

        # Add some data
        for i in range(100):
            metrics = QueryMetrics(
                query_id=f"query-{i}",
                query_hash=f"hash-{i}",
                timestamp=datetime.now(),
                query_length=100,
                total_latency_ms=250.0,
                success=True,
            )
            temp_storage.store_query_metrics(metrics)

        # Size should increase
        new_size = temp_storage.get_database_size_mb()
        assert new_size > initial_size

    def test_health_check(self, temp_storage):
        """Test storage health check."""
        health = temp_storage.health_check()

        assert "database_path" in health
        assert "database_size_mb" in health
        assert "size_limit_mb" in health
        assert "size_utilization_percent" in health
        assert "retention_days" in health
        assert "table_counts" in health
        assert "healthy" in health

        assert health["healthy"] is True  # Empty database is healthy

    def test_default_paths(self):
        """Test default database path handling."""
        storage = MetricsStorage()
        expected_path = Path.home() / ".ragged" / "analytics.db"
        assert storage.db_path == expected_path
