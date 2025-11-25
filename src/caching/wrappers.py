"""Cached wrappers for optimization modules.

Provides caching decorators and wrappers for query classification,
model routing, domain detection, and other optimization features.

v0.6.4 OPTIMISE-005 Phase 2: Cache Integration
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from ragged.caching.key_generator import CacheKeyGenerator
from ragged.caching.manager import get_cache_manager

if TYPE_CHECKING:
    from ragged.optimisation.query_classifier import QueryClassification, QueryClassifier

logger = logging.getLogger(__name__)


class CachedQueryClassifier:
    """Cached wrapper for QueryClassifier.

    Caches classification results to avoid repeated analysis of same queries.
    """

    def __init__(self, classifier: QueryClassifier, cache_enabled: bool = True):
        """Initialize cached classifier.

        Args:
            classifier: QueryClassifier instance to wrap
            cache_enabled: Enable/disable caching
        """
        self.classifier = classifier
        self.cache_enabled = cache_enabled
        self.cache_manager = get_cache_manager(enabled=cache_enabled)

    def classify(self, query: str) -> QueryClassification:
        """Classify query with caching.

        Args:
            query: Query string

        Returns:
            QueryClassification (from cache or fresh)
        """
        # Generate cache key
        cache_key = CacheKeyGenerator.generate_classification_key(query)

        # Try cache first
        if self.cache_enabled:
            cached = self.cache_manager.get_classification(cache_key)
            if cached is not None:
                logger.debug(f"Classification cache hit for query: {query[:50]}...")
                return cached

        # Cache miss - perform classification
        result = self.classifier.classify(query)

        # Store in cache
        if self.cache_enabled:
            self.cache_manager.set_classification(cache_key, result)
            logger.debug(f"Classification cached for query: {query[:50]}...")

        return result


class CachedModelRouter:
    """Cached wrapper for ModelRouter.

    Caches routing decisions based on query classification.
    """

    def __init__(self, router: Any, cache_enabled: bool = True):
        """Initialize cached router.

        Args:
            router: ModelRouter instance to wrap
            cache_enabled: Enable/disable caching
        """
        self.router = router
        self.cache_enabled = cache_enabled
        self.cache_manager = get_cache_manager(enabled=cache_enabled)

    def select_model(
        self, query_type: str, complexity: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Select model with caching.

        Args:
            query_type: Query type from classification
            complexity: Query complexity score
            **kwargs: Additional routing parameters

        Returns:
            Routing decision
        """
        # Generate cache key
        cache_key = CacheKeyGenerator.generate_routing_key(query_type, complexity)

        # Try cache first
        if self.cache_enabled:
            cached = self.cache_manager.get_routing(cache_key)
            if cached is not None:
                logger.debug(
                    f"Routing cache hit for type={query_type}, complexity={complexity}"
                )
                return cached

        # Cache miss - perform routing
        result = self.router.select_model(query_type, complexity, **kwargs)

        # Store in cache
        if self.cache_enabled:
            self.cache_manager.set_routing(cache_key, result)
            logger.debug(
                f"Routing cached for type={query_type}, complexity={complexity}"
            )

        return result


class CachedDomainDetector:
    """Cached wrapper for DomainDetector.

    Caches domain detection results for text content.
    """

    def __init__(self, detector: Any, cache_enabled: bool = True):
        """Initialize cached domain detector.

        Args:
            detector: DomainDetector instance to wrap
            cache_enabled: Enable/disable caching
        """
        self.detector = detector
        self.cache_enabled = cache_enabled
        self.cache_manager = get_cache_manager(enabled=cache_enabled)

    def detect_domain(self, text: str, **kwargs: Any) -> Any:
        """Detect domain with caching.

        Args:
            text: Text to analyze
            **kwargs: Additional detection parameters

        Returns:
            Domain detection result
        """
        # Generate cache key
        cache_key = CacheKeyGenerator.generate_domain_key(text)

        # Try cache first
        if self.cache_enabled:
            cached = self.cache_manager.get_domain(cache_key)
            if cached is not None:
                logger.debug(f"Domain cache hit for text: {text[:50]}...")
                return cached

        # Cache miss - perform detection
        result = self.detector.detect_domain(text, **kwargs)

        # Store in cache
        if self.cache_enabled:
            self.cache_manager.set_domain(cache_key, result)
            logger.debug(f"Domain cached for text: {text[:50]}...")

        return result


class CachedRetriever:
    """Cached wrapper for retrieval operations.

    Caches retrieval results based on query and parameters.
    """

    def __init__(self, retriever: Any, cache_enabled: bool = True):
        """Initialize cached retriever.

        Args:
            retriever: Retriever instance to wrap
            cache_enabled: Enable/disable caching
        """
        self.retriever = retriever
        self.cache_enabled = cache_enabled
        self.cache_manager = get_cache_manager(enabled=cache_enabled)

    def retrieve(
        self, query: str, k: int = 5, domain: Optional[str] = None, **kwargs: Any
    ) -> Any:
        """Retrieve with caching.

        Args:
            query: Query string
            k: Number of results
            domain: Optional domain filter
            **kwargs: Additional retrieval parameters

        Returns:
            Retrieval results
        """
        # Generate cache key
        cache_key = CacheKeyGenerator.generate_retrieval_key(query, k, domain)

        # Try cache first
        if self.cache_enabled:
            cached = self.cache_manager.get_retrieval(cache_key)
            if cached is not None:
                logger.debug(f"Retrieval cache hit for query: {query[:50]}...")
                return cached

        # Cache miss - perform retrieval
        result = self.retriever.retrieve(query, k=k, domain=domain, **kwargs)

        # Store in cache
        if self.cache_enabled:
            self.cache_manager.set_retrieval(cache_key, result)
            logger.debug(f"Retrieval cached for query: {query[:50]}...")

        return result


class CachedLLM:
    """Cached wrapper for LLM operations.

    Caches LLM responses based on query, model, and context.
    """

    def __init__(self, llm: Any, cache_enabled: bool = True):
        """Initialize cached LLM.

        Args:
            llm: LLM client instance to wrap
            cache_enabled: Enable/disable caching
        """
        self.llm = llm
        self.cache_enabled = cache_enabled
        self.cache_manager = get_cache_manager(enabled=cache_enabled)

    def generate(
        self, query: str, model: str, context: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Generate response with caching.

        Args:
            query: Query string
            model: Model identifier
            context: Retrieval context
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        # Hash context for cache key (context can be very long)
        import hashlib

        context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()[:16]

        # Generate cache key
        cache_key = CacheKeyGenerator.generate_llm_key(query, model, context_hash)

        # Try cache first
        if self.cache_enabled:
            cached = self.cache_manager.get_llm(cache_key)
            if cached is not None:
                logger.debug(f"LLM cache hit for query: {query[:50]}...")
                return cached

        # Cache miss - perform generation
        result = self.llm.generate(query, model=model, context=context, **kwargs)

        # Store in cache
        if self.cache_enabled:
            self.cache_manager.set_llm(cache_key, result)
            logger.debug(f"LLM response cached for query: {query[:50]}...")

        return result
