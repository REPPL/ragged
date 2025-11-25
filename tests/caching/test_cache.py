"""Tests for cache implementation.

v0.6.4 OPTIMISE-005 Phase 1: Caching Infrastructure
"""

import time

import pytest

from ragged.caching.cache import Cache, CacheConfig, CacheStats


class TestCacheConfig:
    """Test suite for CacheConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()

        assert config.max_entries == 1000
        assert config.ttl_seconds == 3600
        assert config.max_size_bytes == 0
        assert config.eviction_policy == "lru"

    def test_custom_config(self):
        """Test custom configuration."""
        config = CacheConfig(
            max_entries=500,
            ttl_seconds=1800,
            max_size_bytes=1024 * 1024,
            eviction_policy="lfu",
        )

        assert config.max_entries == 500
        assert config.ttl_seconds == 1800
        assert config.max_size_bytes == 1024 * 1024
        assert config.eviction_policy == "lfu"


class TestCacheStats:
    """Test suite for CacheStats."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = CacheStats()

        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.evictions == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        stats.total_requests = 10
        stats.cache_hits = 6
        stats.cache_misses = 4

        assert stats.hit_rate == 0.6

    def test_reset(self):
        """Test statistics reset."""
        stats = CacheStats()
        stats.total_requests = 100
        stats.cache_hits = 60
        stats.cache_misses = 40
        stats.evictions = 10

        stats.reset()

        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.evictions == 0


class TestCache:
    """Test suite for Cache."""

    def test_initialization(self):
        """Test cache initialises correctly."""
        cache = Cache()

        assert cache.config.max_entries == 1000
        assert cache.stats.total_requests == 0

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = Cache()

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"
        assert cache.stats.cache_hits == 1
        assert cache.stats.total_requests == 1

    def test_get_nonexistent(self):
        """Test getting non-existent key."""
        cache = Cache()

        result = cache.get("nonexistent")

        assert result is None
        assert cache.stats.cache_misses == 1

    def test_update_existing_key(self):
        """Test updating existing cache entry."""
        cache = Cache()

        cache.set("key1", "value1")
        cache.set("key1", "value2")
        result = cache.get("key1")

        assert result == "value2"

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        config = CacheConfig(ttl_seconds=1)
        cache = Cache(config)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        result = cache.get("key1")
        assert result is None
        assert cache.stats.evictions == 1

    def test_custom_ttl(self):
        """Test custom TTL override."""
        cache = Cache()

        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"

        time.sleep(1.1)

        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """Test LRU eviction when max entries exceeded."""
        config = CacheConfig(max_entries=3, eviction_policy="lru")
        cache = Cache(config)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New entry

    def test_delete(self):
        """Test deleting cache entry."""
        cache = Cache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        deleted = cache.delete("key1")

        assert deleted is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        cache = Cache()

        deleted = cache.delete("nonexistent")

        assert deleted is False

    def test_clear(self):
        """Test clearing entire cache."""
        cache = Cache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        assert cache.stats.current_entries == 0

    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = Cache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()

        assert stats["total_requests"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["current_entries"] == 2

    def test_reset_stats(self):
        """Test resetting cache statistics."""
        cache = Cache()

        cache.set("key1", "value1")
        cache.get("key1")

        cache.reset_stats()

        stats = cache.get_stats()
        assert stats["total_requests"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0

    def test_size_estimation(self):
        """Test cache size estimation."""
        cache = Cache()

        cache.set("key1", "small")
        cache.set("key2", "a" * 1000)

        stats = cache.get_stats()
        assert stats["current_size_bytes"] > 0
        assert stats["current_size_mb"] > 0

    def test_max_size_eviction(self):
        """Test eviction when max size exceeded."""
        config = CacheConfig(max_size_bytes=100, max_entries=1000)
        cache = Cache(config)

        # Add entries until size limit reached
        cache.set("key1", "a" * 50)
        cache.set("key2", "b" * 60)  # Should trigger eviction

        # key1 should be evicted (LRU)
        assert cache.get("key1") is None
        assert cache.get("key2") == "b" * 60

    def test_lfu_eviction(self):
        """Test LFU eviction policy."""
        config = CacheConfig(max_entries=3, eviction_policy="lfu")
        cache = Cache(config)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 and key3 multiple times
        for _ in range(5):
            cache.get("key1")
            cache.get("key3")

        # key2 is least frequently used
        cache.set("key4", "value4")  # Should evict key2

        assert cache.get("key1") is not None
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is not None
