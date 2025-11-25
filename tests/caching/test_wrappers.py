"""Tests for cached wrappers.

v0.6.4 OPTIMISE-005 Phase 2: Cache Integration
"""

from unittest.mock import MagicMock, Mock

import pytest

from ragged.caching.manager import get_cache_manager
from ragged.caching.wrappers import (
    CachedDomainDetector,
    CachedLLM,
    CachedModelRouter,
    CachedQueryClassifier,
    CachedRetriever,
)
from ragged.optimisation.query_classifier import (
    QueryClassification,
    QueryIntent,
    QueryType,
)


class TestCachedQueryClassifier:
    """Test suite for CachedQueryClassifier."""

    def setup_method(self):
        """Reset cache manager before each test."""
        # Clear global cache
        cache_mgr = get_cache_manager()
        cache_mgr.clear_all()

    def test_cache_hit_on_second_call(self):
        """Test classification result cached on second call."""
        # Create mock classifier
        mock_classifier = Mock()
        mock_result = QueryClassification(
            query="test query",
            query_type=QueryType.FACTUAL,
            complexity=3,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )
        mock_classifier.classify.return_value = mock_result

        # Wrap with cache
        cached = CachedQueryClassifier(mock_classifier, cache_enabled=True)

        # First call - should miss cache
        result1 = cached.classify("test query")
        assert result1 == mock_result
        assert mock_classifier.classify.call_count == 1

        # Second call - should hit cache
        result2 = cached.classify("test query")
        assert result2 == mock_result
        assert mock_classifier.classify.call_count == 1  # Not called again

    def test_different_queries_different_cache(self):
        """Test different queries produce different cache entries."""
        mock_classifier = Mock()
        mock_classifier.classify.return_value = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        cached = CachedQueryClassifier(mock_classifier)

        cached.classify("query1")
        cached.classify("query2")

        # Both should call the classifier (different cache keys)
        assert mock_classifier.classify.call_count == 2

    def test_disabled_cache_always_calls_classifier(self):
        """Test disabled cache always calls classifier."""
        mock_classifier = Mock()
        mock_classifier.classify.return_value = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        cached = CachedQueryClassifier(mock_classifier, cache_enabled=False)

        cached.classify("test query")
        cached.classify("test query")

        # Should call classifier both times
        assert mock_classifier.classify.call_count == 2


class TestCachedModelRouter:
    """Test suite for CachedModelRouter."""

    def setup_method(self):
        """Reset cache manager before each test."""
        cache_mgr = get_cache_manager()
        cache_mgr.clear_all()

    def test_cache_hit_on_second_call(self):
        """Test routing decision cached on second call."""
        mock_router = Mock()
        mock_result = {"model": "llama3.2:3b", "max_tokens": 512}
        mock_router.select_model.return_value = mock_result

        cached = CachedModelRouter(mock_router, cache_enabled=True)

        # First call
        result1 = cached.select_model("factual", complexity=3)
        assert result1 == mock_result
        assert mock_router.select_model.call_count == 1

        # Second call - should hit cache
        result2 = cached.select_model("factual", complexity=3)
        assert result2 == mock_result
        assert mock_router.select_model.call_count == 1

    def test_different_params_different_cache(self):
        """Test different parameters produce different cache entries."""
        mock_router = Mock()
        mock_router.select_model.return_value = {"model": "llama3.2:3b"}

        cached = CachedModelRouter(mock_router)

        cached.select_model("factual", complexity=3)
        cached.select_model("conceptual", complexity=5)
        cached.select_model("factual", complexity=5)

        # All should call router (different cache keys)
        assert mock_router.select_model.call_count == 3

    def test_disabled_cache_always_calls_router(self):
        """Test disabled cache always calls router."""
        mock_router = Mock()
        mock_router.select_model.return_value = {"model": "llama3.2:3b"}

        cached = CachedModelRouter(mock_router, cache_enabled=False)

        cached.select_model("factual", complexity=3)
        cached.select_model("factual", complexity=3)

        assert mock_router.select_model.call_count == 2


class TestCachedDomainDetector:
    """Test suite for CachedDomainDetector."""

    def setup_method(self):
        """Reset cache manager before each test."""
        cache_mgr = get_cache_manager()
        cache_mgr.clear_all()

    def test_cache_hit_on_second_call(self):
        """Test domain detection cached on second call."""
        mock_detector = Mock()
        mock_result = {"primary_domain": "technical", "confidence": 0.85}
        mock_detector.detect_domain.return_value = mock_result

        cached = CachedDomainDetector(mock_detector, cache_enabled=True)

        # First call
        result1 = cached.detect_domain("test text")
        assert result1 == mock_result
        assert mock_detector.detect_domain.call_count == 1

        # Second call - should hit cache
        result2 = cached.detect_domain("test text")
        assert result2 == mock_result
        assert mock_detector.detect_domain.call_count == 1

    def test_different_text_different_cache(self):
        """Test different text produces different cache entries."""
        mock_detector = Mock()
        mock_detector.detect_domain.return_value = {"primary_domain": "tech"}

        cached = CachedDomainDetector(mock_detector)

        cached.detect_domain("text1")
        cached.detect_domain("text2")

        assert mock_detector.detect_domain.call_count == 2

    def test_disabled_cache_always_calls_detector(self):
        """Test disabled cache always calls detector."""
        mock_detector = Mock()
        mock_detector.detect_domain.return_value = {"primary_domain": "tech"}

        cached = CachedDomainDetector(mock_detector, cache_enabled=False)

        cached.detect_domain("test text")
        cached.detect_domain("test text")

        assert mock_detector.detect_domain.call_count == 2


class TestCachedRetriever:
    """Test suite for CachedRetriever."""

    def setup_method(self):
        """Reset cache manager before each test."""
        cache_mgr = get_cache_manager()
        cache_mgr.clear_all()

    def test_cache_hit_on_second_call(self):
        """Test retrieval results cached on second call."""
        mock_retriever = Mock()
        mock_result = {"chunks": [{"text": "chunk1", "score": 0.9}]}
        mock_retriever.retrieve.return_value = mock_result

        cached = CachedRetriever(mock_retriever, cache_enabled=True)

        # First call
        result1 = cached.retrieve("test query", k=5)
        assert result1 == mock_result
        assert mock_retriever.retrieve.call_count == 1

        # Second call - should hit cache
        result2 = cached.retrieve("test query", k=5)
        assert result2 == mock_result
        assert mock_retriever.retrieve.call_count == 1

    def test_different_params_different_cache(self):
        """Test different parameters produce different cache entries."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = {"chunks": []}

        cached = CachedRetriever(mock_retriever)

        cached.retrieve("query", k=5)
        cached.retrieve("query", k=10)
        cached.retrieve("query", k=5, domain="tech")

        # All should call retriever (different cache keys)
        assert mock_retriever.retrieve.call_count == 3

    def test_disabled_cache_always_calls_retriever(self):
        """Test disabled cache always calls retriever."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = {"chunks": []}

        cached = CachedRetriever(mock_retriever, cache_enabled=False)

        cached.retrieve("query", k=5)
        cached.retrieve("query", k=5)

        assert mock_retriever.retrieve.call_count == 2


class TestCachedLLM:
    """Test suite for CachedLLM."""

    def setup_method(self):
        """Reset cache manager before each test."""
        cache_mgr = get_cache_manager()
        cache_mgr.clear_all()

    def test_cache_hit_on_second_call(self):
        """Test LLM response cached on second call."""
        mock_llm = Mock()
        mock_result = {"response": "test response", "model": "llama3.2:3b"}
        mock_llm.generate.return_value = mock_result

        cached = CachedLLM(mock_llm, cache_enabled=True)

        # First call
        result1 = cached.generate("query", model="llama3.2:3b", context="context")
        assert result1 == mock_result
        assert mock_llm.generate.call_count == 1

        # Second call - should hit cache
        result2 = cached.generate("query", model="llama3.2:3b", context="context")
        assert result2 == mock_result
        assert mock_llm.generate.call_count == 1

    def test_different_query_different_cache(self):
        """Test different queries produce different cache entries."""
        mock_llm = Mock()
        mock_llm.generate.return_value = {"response": "test"}

        cached = CachedLLM(mock_llm)

        cached.generate("query1", model="llama3.2:3b", context="context")
        cached.generate("query2", model="llama3.2:3b", context="context")

        assert mock_llm.generate.call_count == 2

    def test_different_model_different_cache(self):
        """Test different models produce different cache entries."""
        mock_llm = Mock()
        mock_llm.generate.return_value = {"response": "test"}

        cached = CachedLLM(mock_llm)

        cached.generate("query", model="llama3.2:3b", context="context")
        cached.generate("query", model="llama3.2:1b", context="context")

        assert mock_llm.generate.call_count == 2

    def test_different_context_different_cache(self):
        """Test different contexts produce different cache entries."""
        mock_llm = Mock()
        mock_llm.generate.return_value = {"response": "test"}

        cached = CachedLLM(mock_llm)

        cached.generate("query", model="llama3.2:3b", context="context1")
        cached.generate("query", model="llama3.2:3b", context="context2")

        # Should call LLM twice (different context hashes)
        assert mock_llm.generate.call_count == 2

    def test_disabled_cache_always_calls_llm(self):
        """Test disabled cache always calls LLM."""
        mock_llm = Mock()
        mock_llm.generate.return_value = {"response": "test"}

        cached = CachedLLM(mock_llm, cache_enabled=False)

        cached.generate("query", model="llama3.2:3b", context="context")
        cached.generate("query", model="llama3.2:3b", context="context")

        assert mock_llm.generate.call_count == 2


class TestCacheIntegration:
    """Integration tests across all wrappers."""

    def setup_method(self):
        """Reset cache manager before each test."""
        cache_mgr = get_cache_manager()
        cache_mgr.clear_all()

    def test_multiple_wrappers_share_manager(self):
        """Test multiple wrappers share same cache manager."""
        mock_classifier = Mock()
        mock_classifier.classify.return_value = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        mock_router = Mock()
        mock_router.select_model.return_value = {"model": "llama3.2:3b"}

        cached_classifier = CachedQueryClassifier(mock_classifier)
        cached_router = CachedModelRouter(mock_router)

        # Both should share same cache manager
        assert cached_classifier.cache_manager is cached_router.cache_manager

    def test_cache_stats_across_wrappers(self):
        """Test cache statistics work across all wrappers."""
        # Create mocks
        mock_classifier = Mock()
        mock_classifier.classify.return_value = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        mock_router = Mock()
        mock_router.select_model.return_value = {"model": "llama3.2:3b"}

        # Wrap with cache
        cached_classifier = CachedQueryClassifier(mock_classifier)
        cached_router = CachedModelRouter(mock_router)

        # Perform operations
        cached_classifier.classify("query")
        cached_router.select_model("factual", complexity=3)

        # Get stats
        stats = cached_classifier.cache_manager.get_stats()

        assert stats["enabled"] is True
        assert stats["total_entries"] >= 2  # At least 2 entries cached

    def test_clear_all_affects_all_wrappers(self):
        """Test clearing cache affects all wrappers."""
        mock_classifier = Mock()
        mock_classifier.classify.return_value = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            complexity=1,
            intent=QueryIntent.LOOKUP,
            is_multi_hop=False,
            domain_hints=[],
        )

        mock_router = Mock()
        mock_router.select_model.return_value = {"model": "llama3.2:3b"}

        cached_classifier = CachedQueryClassifier(mock_classifier)
        cached_router = CachedModelRouter(mock_router)

        # Cache some data
        cached_classifier.classify("query")
        cached_router.select_model("factual", complexity=3)

        # Clear all caches
        cached_classifier.cache_manager.clear_all()

        # Next calls should miss cache
        cached_classifier.classify("query")
        cached_router.select_model("factual", complexity=3)

        assert mock_classifier.classify.call_count == 2  # Called twice
        assert mock_router.select_model.call_count == 2  # Called twice
