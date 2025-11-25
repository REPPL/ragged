"""Tests for cache manager.

v0.6.4 OPTIMISE-005 Phase 2: Cache Integration
"""

import pytest

from ragged.caching.manager import CacheManager, get_cache_manager


class TestCacheManager:
    """Test suite for CacheManager."""

    def test_initialization(self):
        """Test manager initializes with all cache layers."""
        manager = CacheManager(enabled=True)

        assert manager.enabled is True
        assert manager.classification_cache is not None
        assert manager.routing_cache is not None
        assert manager.domain_cache is not None
        assert manager.retrieval_cache is not None
        assert manager.llm_cache is not None

    def test_disabled_manager(self):
        """Test disabled manager returns None for gets."""
        manager = CacheManager(enabled=False)

        manager.set_classification("key1", "value1")
        result = manager.get_classification("key1")

        assert result is None  # Disabled manager doesn't cache

    def test_classification_cache(self):
        """Test classification caching."""
        manager = CacheManager()

        manager.set_classification("key1", {"type": "factual"})
        result = manager.get_classification("key1")

        assert result == {"type": "factual"}

    def test_routing_cache(self):
        """Test routing caching."""
        manager = CacheManager()

        manager.set_routing("key1", {"model": "llama3.2:3b"})
        result = manager.get_routing("key1")

        assert result == {"model": "llama3.2:3b"}

    def test_domain_cache(self):
        """Test domain caching."""
        manager = CacheManager()

        manager.set_domain("key1", {"domain": "technical"})
        result = manager.get_domain("key1")

        assert result == {"domain": "technical"}

    def test_retrieval_cache(self):
        """Test retrieval caching."""
        manager = CacheManager()

        manager.set_retrieval("key1", {"chunks": []})
        result = manager.get_retrieval("key1")

        assert result == {"chunks": []}

    def test_llm_cache(self):
        """Test LLM response caching."""
        manager = CacheManager()

        manager.set_llm("key1", {"response": "test"})
        result = manager.get_llm("key1")

        assert result == {"response": "test"}

    def test_clear_all(self):
        """Test clearing all cache layers."""
        manager = CacheManager()

        manager.set_classification("key1", "value1")
        manager.set_routing("key2", "value2")
        manager.set_domain("key3", "value3")
        manager.set_retrieval("key4", "value4")
        manager.set_llm("key5", "value5")

        manager.clear_all()

        assert manager.get_classification("key1") is None
        assert manager.get_routing("key2") is None
        assert manager.get_domain("key3") is None
        assert manager.get_retrieval("key4") is None
        assert manager.get_llm("key5") is None

    def test_get_stats(self):
        """Test getting statistics for all layers."""
        manager = CacheManager()

        manager.set_classification("key1", "value1")
        manager.set_routing("key2", "value2")

        stats = manager.get_stats()

        assert "enabled" in stats
        assert "classification" in stats
        assert "routing" in stats
        assert "domain" in stats
        assert "retrieval" in stats
        assert "llm" in stats
        assert "total_entries" in stats
        assert "total_size_mb" in stats

        assert stats["enabled"] is True
        assert stats["total_entries"] >= 2

    def test_different_ttl_per_layer(self):
        """Test that different layers have different TTL settings."""
        manager = CacheManager()

        # Check TTL settings
        assert manager.classification_cache.config.ttl_seconds == 3600  # 1 hour
        assert manager.routing_cache.config.ttl_seconds == 3600  # 1 hour
        assert manager.domain_cache.config.ttl_seconds == 86400  # 24 hours
        assert manager.retrieval_cache.config.ttl_seconds == 1800  # 30 minutes
        assert manager.llm_cache.config.ttl_seconds == 900  # 15 minutes

    def test_get_cache_manager_singleton(self):
        """Test global singleton pattern."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        assert manager1 is manager2  # Same instance
