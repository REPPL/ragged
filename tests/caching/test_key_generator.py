"""Tests for cache key generation.

v0.6.4 OPTIMISE-005 Phase 1: Caching Infrastructure
"""

import pytest

from ragged.caching.key_generator import CacheKeyGenerator


class TestCacheKeyGenerator:
    """Test suite for CacheKeyGenerator."""

    def test_deterministic_keys(self):
        """Test key generation is deterministic."""
        key1 = CacheKeyGenerator.generate_key("test", param=123)
        key2 = CacheKeyGenerator.generate_key("test", param=123)

        assert key1 == key2

    def test_different_args_different_keys(self):
        """Test different arguments produce different keys."""
        key1 = CacheKeyGenerator.generate_key("test1")
        key2 = CacheKeyGenerator.generate_key("test2")

        assert key1 != key2

    def test_order_matters(self):
        """Test argument order affects key."""
        key1 = CacheKeyGenerator.generate_key("a", "b")
        key2 = CacheKeyGenerator.generate_key("b", "a")

        assert key1 != key2

    def test_kwargs_order_independent(self):
        """Test keyword arguments order doesn't affect key."""
        key1 = CacheKeyGenerator.generate_key(a=1, b=2, c=3)
        key2 = CacheKeyGenerator.generate_key(c=3, a=1, b=2)

        assert key1 == key2  # Should be same (sorted internally)

    def test_query_key_generation(self):
        """Test query-specific key generation."""
        key = CacheKeyGenerator.generate_query_key(
            "What is machine learning?", model="llama3.2:3b"
        )

        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex = 64 chars

    def test_classification_key(self):
        """Test classification cache key."""
        key1 = CacheKeyGenerator.generate_classification_key("test query")
        key2 = CacheKeyGenerator.generate_classification_key("test query")

        assert key1 == key2
        assert len(key1) == 64

    def test_routing_key(self):
        """Test routing cache key."""
        key1 = CacheKeyGenerator.generate_routing_key("factual", 3)
        key2 = CacheKeyGenerator.generate_routing_key("factual", 3)
        key3 = CacheKeyGenerator.generate_routing_key("analytical", 3)

        assert key1 == key2
        assert key1 != key3

    def test_domain_key(self):
        """Test domain detection cache key."""
        key = CacheKeyGenerator.generate_domain_key("technical text")

        assert isinstance(key, str)
        assert len(key) == 64

    def test_retrieval_key(self):
        """Test retrieval results cache key."""
        key1 = CacheKeyGenerator.generate_retrieval_key("query", k=5)
        key2 = CacheKeyGenerator.generate_retrieval_key("query", k=5, domain="tech")
        key3 = CacheKeyGenerator.generate_retrieval_key("query", k=10)

        assert key1 != key2  # Different domain
        assert key1 != key3  # Different k
        assert len(key1) == 64

    def test_llm_key(self):
        """Test LLM response cache key."""
        key = CacheKeyGenerator.generate_llm_key(
            "query", model="llama3.2:3b", context_hash="abc123"
        )

        assert isinstance(key, str)
        assert len(key) == 64

    def test_complex_types(self):
        """Test key generation with complex types."""
        key1 = CacheKeyGenerator.generate_key(
            query="test", metadata={"domain": "tech", "complexity": 5}
        )
        key2 = CacheKeyGenerator.generate_key(
            query="test", metadata={"complexity": 5, "domain": "tech"}
        )

        assert key1 == key2  # Dict serialised with sorted keys

    def test_none_values(self):
        """Test key generation with None values."""
        key1 = CacheKeyGenerator.generate_key("test", param=None)
        key2 = CacheKeyGenerator.generate_key("test", param=None)

        assert key1 == key2

    def test_boolean_values(self):
        """Test key generation with boolean values."""
        key1 = CacheKeyGenerator.generate_key("test", flag=True)
        key2 = CacheKeyGenerator.generate_key("test", flag=False)

        assert key1 != key2
