"""Cache manager for coordinating multiple cache layers.

Provides unified interface for managing classification, routing, domain,
retrieval, and LLM response caches with integrated analytics.

v0.6.4 OPTIMISE-005 Phase 2: Cache Integration
"""

from __future__ import annotations

import logging
from typing import Optional

from ragged.caching.cache import Cache, CacheConfig

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage multiple cache layers with unified interface.

    Coordinates caching across all optimization layers:
    - Query classification cache (v0.6.1)
    - Model routing cache (v0.6.2)
    - Domain detection cache (v0.6.3)
    - Retrieval results cache
    - LLM response cache
    """

    def __init__(self, enabled: bool = True):
        """Initialize cache manager.

        Args:
            enabled: Enable/disable all caching
        """
        self.enabled = enabled

        # Initialize cache layers with appropriate configurations
        self.classification_cache = Cache(
            CacheConfig(
                max_entries=10000,
                ttl_seconds=3600,  # 1 hour
                eviction_policy="lru",
            )
        )

        self.routing_cache = Cache(
            CacheConfig(
                max_entries=10000,
                ttl_seconds=3600,  # 1 hour
                eviction_policy="lru",
            )
        )

        self.domain_cache = Cache(
            CacheConfig(
                max_entries=5000,
                ttl_seconds=86400,  # 24 hours (domains are stable)
                eviction_policy="lru",
            )
        )

        self.retrieval_cache = Cache(
            CacheConfig(
                max_entries=1000,
                ttl_seconds=1800,  # 30 minutes
                eviction_policy="lru",
            )
        )

        self.llm_cache = Cache(
            CacheConfig(
                max_entries=500,
                ttl_seconds=900,  # 15 minutes (responses can become stale)
                eviction_policy="lru",
            )
        )

        logger.info(
            f"Initialized CacheManager with {5} cache layers (enabled={enabled})"
        )

    def get_classification(self, key: str) -> Optional[any]:
        """Get cached classification result.

        Args:
            key: Cache key

        Returns:
            Cached classification or None
        """
        if not self.enabled:
            return None
        return self.classification_cache.get(key)

    def set_classification(self, key: str, value: any) -> None:
        """Cache classification result.

        Args:
            key: Cache key
            value: Classification result
        """
        if self.enabled:
            self.classification_cache.set(key, value)

    def get_routing(self, key: str) -> Optional[any]:
        """Get cached routing decision.

        Args:
            key: Cache key

        Returns:
            Cached routing decision or None
        """
        if not self.enabled:
            return None
        return self.routing_cache.get(key)

    def set_routing(self, key: str, value: any) -> None:
        """Cache routing decision.

        Args:
            key: Cache key
            value: Routing decision
        """
        if self.enabled:
            self.routing_cache.set(key, value)

    def get_domain(self, key: str) -> Optional[any]:
        """Get cached domain detection result.

        Args:
            key: Cache key

        Returns:
            Cached domain result or None
        """
        if not self.enabled:
            return None
        return self.domain_cache.get(key)

    def set_domain(self, key: str, value: any) -> None:
        """Cache domain detection result.

        Args:
            key: Cache key
            value: Domain detection result
        """
        if self.enabled:
            self.domain_cache.set(key, value)

    def get_retrieval(self, key: str) -> Optional[any]:
        """Get cached retrieval results.

        Args:
            key: Cache key

        Returns:
            Cached retrieval results or None
        """
        if not self.enabled:
            return None
        return self.retrieval_cache.get(key)

    def set_retrieval(self, key: str, value: any) -> None:
        """Cache retrieval results.

        Args:
            key: Cache key
            value: Retrieval results
        """
        if self.enabled:
            self.retrieval_cache.set(key, value)

    def get_llm(self, key: str) -> Optional[any]:
        """Get cached LLM response.

        Args:
            key: Cache key

        Returns:
            Cached LLM response or None
        """
        if not self.enabled:
            return None
        return self.llm_cache.get(key)

    def set_llm(self, key: str, value: any) -> None:
        """Cache LLM response.

        Args:
            key: Cache key
            value: LLM response
        """
        if self.enabled:
            self.llm_cache.set(key, value)

    def clear_all(self) -> None:
        """Clear all cache layers."""
        self.classification_cache.clear()
        self.routing_cache.clear()
        self.domain_cache.clear()
        self.retrieval_cache.clear()
        self.llm_cache.clear()
        logger.info("Cleared all cache layers")

    def get_stats(self) -> dict[str, any]:
        """Get statistics for all cache layers.

        Returns:
            Dictionary with stats for each layer
        """
        return {
            "enabled": self.enabled,
            "classification": self.classification_cache.get_stats(),
            "routing": self.routing_cache.get_stats(),
            "domain": self.domain_cache.get_stats(),
            "retrieval": self.retrieval_cache.get_stats(),
            "llm": self.llm_cache.get_stats(),
            "total_entries": (
                self.classification_cache.stats.current_entries
                + self.routing_cache.stats.current_entries
                + self.domain_cache.stats.current_entries
                + self.retrieval_cache.stats.current_entries
                + self.llm_cache.stats.current_entries
            ),
            "total_size_mb": (
                self.classification_cache.stats.current_size_bytes
                + self.routing_cache.stats.current_size_bytes
                + self.domain_cache.stats.current_size_bytes
                + self.retrieval_cache.stats.current_size_bytes
                + self.llm_cache.stats.current_size_bytes
            )
            / (1024 * 1024),
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(enabled: bool = True) -> CacheManager:
    """Get global cache manager instance.

    Args:
        enabled: Enable/disable caching (only used on first call)

    Returns:
        Cache manager singleton
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(enabled=enabled)

    return _cache_manager
