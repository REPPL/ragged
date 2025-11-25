"""Tests for metrics collector.

v0.6.4 OPTIMISE-004 Phase 1: Metrics Collection Framework
"""

import tempfile
from pathlib import Path

import pytest

from ragged.analytics.collector import MetricsCollector, get_metrics_collector
from ragged.analytics.storage import MetricsStorage


@pytest.fixture
def temp_collector():
    """Create temporary metrics collector."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metrics.db"
        storage = MetricsStorage(db_path=db_path)
        collector = MetricsCollector(storage=storage, enabled=True, async_writes=False)
        yield collector


class TestMetricsCollector:
    """Test suite for MetricsCollector."""

    def test_initialization(self, temp_collector):
        """Test collector initializes correctly."""
        assert temp_collector.enabled is True
        assert temp_collector.async_writes is False
        assert temp_collector.storage is not None

    def test_record_query(self, temp_collector):
        """Test recording query metrics."""
        query_id = temp_collector.record_query(
            query="What is machine learning?",
            query_type="factual",
            complexity=2,
            domain="technical",
            total_latency_ms=250.0,
            selected_model="llama3.2:3b",
            success=True,
        )

        assert query_id != ""
        assert len(query_id) == 36  # UUID format

        # Verify stored
        health = temp_collector.storage.health_check()
        assert health["table_counts"]["query_metrics"] == 1

    def test_record_query_disabled(self):
        """Test recording when disabled returns empty ID."""
        collector = MetricsCollector(enabled=False)
        query_id = collector.record_query(
            query="test",
            total_latency_ms=100.0,
        )

        assert query_id == ""

    def test_record_retrieval(self, temp_collector):
        """Test recording retrieval metrics."""
        # First record a query
        query_id = temp_collector.record_query(
            query="test query",
            total_latency_ms=300.0,
        )

        # Then record retrieval
        retrieval_id = temp_collector.record_retrieval(
            query_id=query_id,
            k=5,
            retrieval_latency_ms=150.0,
            results_count=5,
            avg_score=0.85,
            domain="technical",
            domain_boost_applied=True,
        )

        assert retrieval_id != ""
        assert len(retrieval_id) == 36  # UUID

        health = temp_collector.storage.health_check()
        assert health["table_counts"]["retrieval_metrics"] == 1

    def test_update_model_stats(self, temp_collector):
        """Test updating model statistics."""
        # Update stats multiple times
        for i in range(5):
            temp_collector.update_model_stats(
                model_id="llama3.2:3b",
                latency_ms=250.0 + i * 10,  # Varying latency
                input_tokens=100,
                output_tokens=50,
                gpu_memory_mb=1024.0,
                gpu_utilization=75.0,
            )

        # Check in-memory aggregation
        assert "llama3.2:3b" in temp_collector._model_stats
        stats = temp_collector._model_stats["llama3.2:3b"]

        assert stats.invocation_count == 5
        assert stats.total_input_tokens == 500  # 100 * 5
        assert stats.total_output_tokens == 250  # 50 * 5
        assert stats.avg_latency_ms > 250.0  # Average should be >250 due to increments
        assert stats.gpu_memory_used_mb == 1024.0  # Latest value

    def test_update_cache_stats_hit(self, temp_collector):
        """Test updating cache statistics for hits."""
        temp_collector.update_cache_stats(
            cache_layer="query_classification",
            hit=True,
            latency_ms=5.0,
            cache_size_entries=100,
            cache_size_bytes=1024 * 1024,  # 1MB
        )

        # Check in-memory aggregation
        assert "query_classification" in temp_collector._cache_stats
        stats = temp_collector._cache_stats["query_classification"]

        assert stats.total_requests == 1
        assert stats.cache_hits == 1
        assert stats.cache_misses == 0
        assert stats.hit_rate == 1.0
        assert stats.avg_hit_latency_ms == 5.0
        assert stats.cache_size_mb == 1.0

    def test_update_cache_stats_miss(self, temp_collector):
        """Test updating cache statistics for misses."""
        temp_collector.update_cache_stats(
            cache_layer="retrieval_results",
            hit=False,
            latency_ms=250.0,
            cache_size_entries=50,
            cache_size_bytes=512 * 1024,  # 512KB
        )

        stats = temp_collector._cache_stats["retrieval_results"]

        assert stats.total_requests == 1
        assert stats.cache_hits == 0
        assert stats.cache_misses == 1
        assert stats.hit_rate == 0.0
        assert stats.avg_miss_latency_ms == 250.0

    def test_cache_stats_hit_rate_calculation(self, temp_collector):
        """Test cache hit rate calculation with mixed hits/misses."""
        # 6 hits, 4 misses = 60% hit rate
        for i in range(10):
            hit = i < 6  # First 6 are hits
            temp_collector.update_cache_stats(
                cache_layer="test_cache",
                hit=hit,
                latency_ms=10.0 if hit else 100.0,
                cache_size_entries=10,
                cache_size_bytes=10240,
            )

        stats = temp_collector._cache_stats["test_cache"]

        assert stats.total_requests == 10
        assert stats.cache_hits == 6
        assert stats.cache_misses == 4
        assert stats.hit_rate == 0.6

    def test_cache_latency_saved_calculation(self, temp_collector):
        """Test latency saved calculation for cache hits."""
        # First, establish miss latency
        temp_collector.update_cache_stats(
            cache_layer="test_cache",
            hit=False,
            latency_ms=500.0,  # Misses take 500ms
            cache_size_entries=1,
            cache_size_bytes=1024,
        )

        # Then cache hits (should save ~490ms each)
        for _ in range(5):
            temp_collector.update_cache_stats(
                cache_layer="test_cache",
                hit=True,
                latency_ms=10.0,  # Hits take 10ms
                cache_size_entries=1,
                cache_size_bytes=1024,
            )

        stats = temp_collector._cache_stats["test_cache"]

        # Should have saved roughly (500 - 10) * 5 = 2450ms
        assert stats.latency_saved_ms > 2000  # Allow some margin for running averages

    def test_flush_aggregated_metrics(self, temp_collector):
        """Test flushing aggregated metrics to storage."""
        # Update some stats
        temp_collector.update_model_stats(
            model_id="llama3.2:3b",
            latency_ms=250.0,
            input_tokens=100,
            output_tokens=50,
        )

        temp_collector.update_cache_stats(
            cache_layer="test_cache",
            hit=True,
            latency_ms=5.0,
            cache_size_entries=10,
            cache_size_bytes=10240,
        )

        # Flush to storage
        temp_collector.flush_aggregated_metrics()

        # Verify stored
        health = temp_collector.storage.health_check()
        assert health["table_counts"]["model_metrics"] >= 1
        assert health["table_counts"]["cache_metrics"] >= 1

    def test_query_hashing(self, temp_collector):
        """Test query privacy-preserving hashing."""
        hash1 = temp_collector._hash_query("What is machine learning?")
        hash2 = temp_collector._hash_query("What is machine learning?")
        hash3 = temp_collector._hash_query("What is deep learning?")

        # Same query should produce same hash
        assert hash1 == hash2

        # Different query should produce different hash
        assert hash1 != hash3

        # Hash should be fixed length
        assert len(hash1) == 16

    def test_health_check(self, temp_collector):
        """Test collector health check."""
        health = temp_collector.health_check()

        assert "enabled" in health
        assert "async_writes" in health
        assert "model_stats_count" in health
        assert "cache_stats_count" in health
        assert "storage" in health

        assert health["enabled"] is True

    def test_get_metrics_collector_singleton(self):
        """Test global singleton pattern."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # Should return same instance
        assert collector1 is collector2

    def test_error_handling_in_storage(self, temp_collector):
        """Test that storage errors don't crash collection."""
        # Create invalid metrics that might cause storage errors
        # Collector should handle gracefully and log errors

        # This should not raise an exception
        query_id = temp_collector.record_query(
            query="test" * 10000,  # Very long query
            total_latency_ms=100.0,
        )

        # Should still return a query ID even if storage fails
        assert query_id != ""
