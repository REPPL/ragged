"""Benchmark tests for caching performance validation.

v0.6.4 OPTIMISE-005 Phase 4: Testing & Benchmarking

Success criteria:
- Cache hit rate 40-60% after warmup
- 20-30% latency reduction for cached queries
- Cache memory usage <1GB
- Cache overhead <10ms per query
"""

import time
from unittest.mock import Mock

import pytest

from ragged.caching.cache import Cache, CacheConfig
from ragged.caching.manager import CacheManager
from ragged.caching.smart_cache import SmartCache
from ragged.caching.wrappers import CachedQueryClassifier
from ragged.optimisation.query_classifier import (
    QueryClassification,
    QueryIntent,
    QueryType,
)


class TestCacheHitRate:
    """Test cache hit rate targets."""

    def test_hit_rate_after_warmup(self):
        """Test cache achieves good hit rate with realistic workload."""
        cache = Cache(CacheConfig(max_entries=100))

        # Simulate cold start with diverse queries
        cold_queries = [f"query_{i}" for i in range(100)]  # 100 unique queries

        hits = 0
        misses = 0

        # Cold start - all misses
        for query in cold_queries:
            result = cache.get(query)
            if result is None:
                cache.set(query, f"result_{query}")
                misses += 1
            else:
                hits += 1

        # Warm phase - repeat some queries (40% repetition)
        warm_queries = cold_queries[:40] * 2  # Repeat first 40 queries

        for query in warm_queries:
            result = cache.get(query)
            if result is None:
                cache.set(query, f"result_{query}")
                misses += 1
            else:
                hits += 1

        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

        # With 100 cold + 80 warm (40 repeated twice), expect 80/180 = 44% hit rate
        assert hit_rate >= 0.40, f"Hit rate {hit_rate:.2%} below 40% target"
        assert hit_rate <= 0.60, f"Hit rate {hit_rate:.2%} within expected range"

    def test_hit_rate_with_frequency_tracking(self):
        """Test hit rate improves with frequency tracking."""
        smart_cache = SmartCache()
        cache = Cache(CacheConfig(max_entries=50))

        # Simulate realistic query patterns (80/20 rule)
        hot_queries = [f"hot_{i}" for i in range(10)]  # 10 hot queries
        cold_queries = [f"cold_{i}" for i in range(40)]  # 40 cold queries

        queries = []
        # Hot queries accessed 80% of the time
        for _ in range(80):
            queries.extend(hot_queries)
        # Cold queries accessed 20% of the time
        for _ in range(20):
            queries.extend(cold_queries)

        import random

        random.shuffle(queries)

        hits = 0
        misses = 0

        for query in queries:
            cache_key = f"key_{query}"
            smart_cache.record_access(cache_key, query=query)

            result = cache.get(cache_key)
            if result is None:
                cache.set(cache_key, f"result_{query}")
                misses += 1
            else:
                hits += 1

        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

        # With 80/20 pattern, should achieve >50% hit rate
        assert hit_rate >= 0.50, f"Hit rate {hit_rate:.2%} below 50% target"

    def test_cache_stats_tracking(self):
        """Test cache stats accurately track hit rate."""
        cache = Cache()

        # Perform operations
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.set("key2", "value2")
        cache.get("key1")  # Hit
        cache.get("key2")  # Hit

        stats = cache.get_stats()

        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.75  # 3/4


class TestLatencyReduction:
    """Test latency improvement targets."""

    def test_cached_query_latency(self):
        """Test cached queries have lower latency."""
        mock_classifier = Mock()
        mock_result = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        # Simulate slow classification (50ms)
        def slow_classify(query):
            time.sleep(0.05)
            return mock_result

        mock_classifier.classify = slow_classify

        cached = CachedQueryClassifier(mock_classifier, cache_enabled=True)

        # First call (uncached) - should be slow
        start = time.time()
        cached.classify("test query")
        uncached_time = time.time() - start

        # Second call (cached) - should be fast
        start = time.time()
        cached.classify("test query")
        cached_time = time.time() - start

        # Calculate improvement
        improvement = (uncached_time - cached_time) / uncached_time

        # Should see >90% latency reduction (cached should be <5ms)
        assert improvement >= 0.90, f"Latency improvement {improvement:.1%} below 90%"
        assert cached_time < 0.005, f"Cached latency {cached_time*1000:.1f}ms above 5ms"

    def test_cache_overhead(self):
        """Test cache overhead is minimal (<10ms)."""
        cache = Cache()

        # Measure overhead of cache operations
        iterations = 100
        start = time.time()
        for i in range(iterations):
            cache.set(f"key_{i}", f"value_{i}")
            cache.get(f"key_{i}")
        total_time = time.time() - start

        overhead_per_operation = (total_time / (iterations * 2)) * 1000  # ms

        assert (
            overhead_per_operation < 10
        ), f"Cache overhead {overhead_per_operation:.2f}ms exceeds 10ms target"


class TestMemoryUsage:
    """Test cache memory usage targets."""

    def test_cache_size_estimation(self):
        """Test cache size estimation is reasonable."""
        cache = Cache(CacheConfig(max_entries=1000))

        # Add 1000 small entries
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}" * 10)  # ~100 bytes each

        stats = cache.get_stats()
        size_mb = stats["current_size_mb"]

        # Should be <10MB for 1000 small entries
        assert size_mb < 10, f"Cache size {size_mb:.2f}MB exceeds expected 10MB"

    def test_cache_manager_total_size(self):
        """Test cache manager tracks total size across layers."""
        manager = CacheManager(enabled=True)

        # Add data to multiple layers
        manager.set_classification("key1", {"type": "factual"})
        manager.set_routing("key2", {"model": "llama3.2:3b"})
        manager.set_domain("key3", {"domain": "technical"})

        stats = manager.get_stats()
        total_size_mb = stats["total_size_mb"]

        # Should be minimal for a few entries
        assert total_size_mb < 1, f"Total size {total_size_mb:.2f}MB unexpectedly high"

    def test_large_cache_memory_usage(self):
        """Test large cache stays under 1GB limit."""
        # Simulate large cache with size limit
        cache = Cache(CacheConfig(max_entries=10000, max_size_bytes=1024 * 1024 * 1024))

        # Add entries until we hit a reasonable size
        for i in range(1000):
            # Each entry ~1KB
            cache.set(f"key_{i}", "x" * 1024)

        stats = cache.get_stats()
        size_mb = stats["current_size_mb"]

        # Should be ~1MB for 1000 entries of 1KB each
        assert size_mb < 10, f"Cache size {size_mb:.2f}MB exceeds expected 10MB"
        assert size_mb > 0.5, f"Cache size {size_mb:.2f}MB unexpectedly low"


class TestCacheCoherency:
    """Test cache coherency and consistency."""

    def test_cache_invalidation(self):
        """Test cache invalidation works correctly."""
        cache = Cache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_ttl_expiration(self):
        """Test TTL expiration maintains coherency."""
        cache = Cache(CacheConfig(ttl_seconds=1))

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        assert cache.get("key1") is None

    def test_cache_manager_layer_isolation(self):
        """Test cache layers are properly isolated."""
        manager = CacheManager()

        manager.set_classification("key1", {"type": "factual"})
        manager.set_routing("key1", {"model": "llama3.2:3b"})

        # Same key in different layers should return different values
        classification = manager.get_classification("key1")
        routing = manager.get_routing("key1")

        assert classification != routing
        assert classification == {"type": "factual"}
        assert routing == {"model": "llama3.2:3b"}

    def test_concurrent_access_safety(self):
        """Test cache handles concurrent access safely."""
        import threading

        cache = Cache()
        errors = []

        def worker(worker_id):
            try:
                for i in range(100):
                    cache.set(f"key_{worker_id}_{i}", f"value_{worker_id}_{i}")
                    cache.get(f"key_{worker_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent access errors: {errors}"

    def test_cache_clear_coherency(self):
        """Test clearing cache maintains coherency."""
        manager = CacheManager()

        # Populate multiple layers
        manager.set_classification("key1", {"type": "factual"})
        manager.set_routing("key2", {"model": "llama3.2:3b"})
        manager.set_domain("key3", {"domain": "technical"})

        manager.clear_all()

        # All layers should be empty
        assert manager.get_classification("key1") is None
        assert manager.get_routing("key2") is None
        assert manager.get_domain("key3") is None


class TestIntegrationPerformance:
    """Integration tests for overall caching performance."""

    def test_end_to_end_caching_workflow(self):
        """Test complete caching workflow performs within targets."""
        mock_classifier = Mock()
        mock_classifier.classify.return_value = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        cached_classifier = CachedQueryClassifier(mock_classifier)
        smart_cache = SmartCache()

        # Simulate realistic workload
        queries = [
            "What is RAG?",
            "How does RAG work?",
            "What is RAG?",  # Repeat
            "What are embeddings?",
            "How does RAG work?",  # Repeat
            "What is RAG?",  # Repeat
        ]

        start = time.time()
        for query in queries:
            cached_classifier.classify(query)
            smart_cache.record_access(query, query=query)

        total_time = time.time() - start
        avg_time = (total_time / len(queries)) * 1000  # ms

        # Average time per query should be low
        assert avg_time < 50, f"Average query time {avg_time:.1f}ms exceeds 50ms"

        # Check smart cache identified patterns
        hot_keys = smart_cache.get_hot_keys(top_n=3)
        assert len(hot_keys) > 0, "Smart cache failed to identify hot keys"

    def test_cache_effectiveness_with_realistic_patterns(self):
        """Test cache effectiveness with realistic query patterns."""
        cache = Cache(CacheConfig(max_entries=100))
        smart_cache = SmartCache()

        # Realistic pattern: mix of common and unique queries
        common_queries = ["What is X?", "How does Y work?", "Why Z?"]
        unique_queries = [f"Unique query {i}" for i in range(50)]

        queries = []
        # 70% common queries
        for _ in range(70):
            queries.extend(common_queries)
        # 30% unique queries
        queries.extend(unique_queries)

        import random

        random.shuffle(queries)

        hits = 0
        misses = 0

        for query in queries:
            smart_cache.record_access(query, query=query)

            result = cache.get(query)
            if result is None:
                cache.set(query, f"result for {query}")
                misses += 1
            else:
                hits += 1

        hit_rate = hits / (hits + misses)

        # With 70% common queries, hit rate should be >40%
        assert hit_rate >= 0.40, f"Hit rate {hit_rate:.2%} below 40% target"

        # Check smart cache identified hot queries
        hot_keys = smart_cache.get_hot_keys(top_n=10)
        assert len(hot_keys) >= 3, "Smart cache should identify multiple hot keys"
