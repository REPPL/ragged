"""Caching module for intelligent query optimisation.

Provides multi-layer caching infrastructure with TTL, LRU eviction,
and smart caching strategies for improved query performance.

v0.6.4 OPTIMISE-005: Smart Caching Strategy
"""

from ragged.caching.cache import Cache, CacheConfig, CacheStats
from ragged.caching.key_generator import CacheKeyGenerator

__all__ = [
    # Core
    "Cache",
    "CacheConfig",
    "CacheStats",
    # Key Generation
    "CacheKeyGenerator",
]
