"""Caching module for intelligent query optimisation.

Provides multi-layer caching infrastructure with TTL, LRU eviction,
and smart caching strategies for improved query performance.

v0.6.4 OPTIMISE-005: Smart Caching Strategy
"""

from ragged.caching.cache import Cache, CacheConfig, CacheStats
from ragged.caching.key_generator import CacheKeyGenerator
from ragged.caching.manager import CacheManager, get_cache_manager
from ragged.caching.wrappers import (
    CachedDomainDetector,
    CachedLLM,
    CachedModelRouter,
    CachedQueryClassifier,
    CachedRetriever,
)

__all__ = [
    # Core
    "Cache",
    "CacheConfig",
    "CacheStats",
    # Manager
    "CacheManager",
    "get_cache_manager",
    # Key Generation
    "CacheKeyGenerator",
    # Wrappers
    "CachedQueryClassifier",
    "CachedModelRouter",
    "CachedDomainDetector",
    "CachedRetriever",
    "CachedLLM",
]
