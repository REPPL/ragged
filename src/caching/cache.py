"""In-memory cache with LRU eviction and TTL support.

Provides fast, thread-safe caching with automatic eviction and statistics.

v0.6.4 OPTIMISE-005 Phase 1: Caching Infrastructure
"""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache instances.

    Attributes:
        max_entries: Maximum number of cache entries
        ttl_seconds: Time-to-live in seconds (0 = no expiration)
        max_size_bytes: Maximum cache size in bytes (0 = unlimited)
        eviction_policy: Eviction policy ("lru", "lfu", "ttl")
    """

    max_entries: int = 1000
    ttl_seconds: int = 3600  # 1 hour default
    max_size_bytes: int = 0  # Unlimited by default
    eviction_policy: str = "lru"  # LRU by default


@dataclass
class CacheStats:
    """Cache statistics tracking.

    Tracks hit rates, latency, and memory usage.
    """

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    current_entries: int = 0
    current_size_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    def reset(self) -> None:
        """Reset statistics."""
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.evictions = 0


@dataclass
class CacheEntry:
    """Individual cache entry with metadata.

    Attributes:
        value: Cached value
        created_at: Entry creation time
        expires_at: Optional expiration time
        access_count: Number of times accessed (for LFU)
        size_bytes: Approximate size in bytes
    """

    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    access_count: int = 0
    size_bytes: int = 0


class Cache:
    """Thread-safe in-memory cache with LRU eviction and TTL.

    Features:
    - LRU (Least Recently Used) eviction
    - TTL (Time To Live) support
    - Thread-safe operations
    - Statistics tracking
    - Memory-aware eviction
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialise cache.

        Args:
            config: Cache configuration (uses defaults if not provided)
        """
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.stats = CacheStats()

        logger.info(
            f"Initialised cache: max_entries={self.config.max_entries}, "
            f"ttl={self.config.ttl_seconds}s, policy={self.config.eviction_policy}"
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            self.stats.total_requests += 1

            if key not in self._cache:
                self.stats.cache_misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.expires_at and time.time() > entry.expires_at:
                self._cache.pop(key)
                self.stats.cache_misses += 1
                self.stats.evictions += 1
                return None

            # Update access metadata
            entry.access_count += 1

            # Move to end for LRU (most recently used)
            self._cache.move_to_end(key)

            self.stats.cache_hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override (seconds)
        """
        with self._lock:
            # Calculate expiration
            ttl_seconds = ttl if ttl is not None else self.config.ttl_seconds
            expires_at = None
            if ttl_seconds > 0:
                expires_at = time.time() + ttl_seconds

            # Estimate size (rough approximation)
            size_bytes = self._estimate_size(value)

            # Create entry
            entry = CacheEntry(
                value=value,
                expires_at=expires_at,
                size_bytes=size_bytes,
            )

            # Check if key exists (update case)
            if key in self._cache:
                old_entry = self._cache[key]
                self.stats.current_size_bytes -= old_entry.size_bytes
                self._cache.pop(key)

            # Add to cache
            self._cache[key] = entry
            self.stats.current_entries = len(self._cache)
            self.stats.current_size_bytes += size_bytes

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            # Enforce limits
            self._enforce_limits()

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self.stats.current_entries = len(self._cache)
                self.stats.current_size_bytes -= entry.size_bytes
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self.stats.current_entries = 0
            self.stats.current_size_bytes = 0
            logger.info("Cache cleared")

    def _enforce_limits(self) -> None:
        """Enforce cache size and entry limits.

        Evicts entries based on eviction policy.
        """
        # Evict expired entries first
        self._evict_expired()

        # Enforce max entries limit
        while len(self._cache) > self.config.max_entries:
            self._evict_one()

        # Enforce max size limit
        if self.config.max_size_bytes > 0:
            while self.stats.current_size_bytes > self.config.max_size_bytes:
                self._evict_one()

    def _evict_expired(self) -> None:
        """Evict all expired entries."""
        now = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if entry.expires_at and now > entry.expires_at
        ]

        for key in expired_keys:
            entry = self._cache.pop(key)
            self.stats.current_entries = len(self._cache)
            self.stats.current_size_bytes -= entry.size_bytes
            self.stats.evictions += 1

    def _evict_one(self) -> None:
        """Evict one entry based on eviction policy."""
        if not self._cache:
            return

        if self.config.eviction_policy == "lru":
            # Remove least recently used (first item in OrderedDict)
            key, entry = self._cache.popitem(last=False)
        elif self.config.eviction_policy == "lfu":
            # Remove least frequently used
            key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
            entry = self._cache.pop(key)
        elif self.config.eviction_policy == "ttl":
            # Remove oldest entry
            key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            entry = self._cache.pop(key)
        else:
            # Default to LRU
            key, entry = self._cache.popitem(last=False)

        self.stats.current_entries = len(self._cache)
        self.stats.current_size_bytes -= entry.size_bytes
        self.stats.evictions += 1

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of a value in bytes.

        Args:
            value: Value to estimate size for

        Returns:
            Estimated size in bytes
        """
        # Rough approximation
        if isinstance(value, str):
            return len(value.encode("utf-8"))
        elif isinstance(value, bytes):
            return len(value)
        elif isinstance(value, (int, float, bool)):
            return 8  # Approximate
        elif isinstance(value, (list, tuple)):
            return sum(self._estimate_size(item) for item in value)
        elif isinstance(value, dict):
            return sum(
                self._estimate_size(k) + self._estimate_size(v)
                for k, v in value.items()
            )
        else:
            # Very rough estimate for other types
            return 100

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "hit_rate": self.stats.hit_rate,
                "evictions": self.stats.evictions,
                "current_entries": self.stats.current_entries,
                "current_size_bytes": self.stats.current_size_bytes,
                "current_size_mb": self.stats.current_size_bytes / (1024 * 1024),
                "max_entries": self.config.max_entries,
                "ttl_seconds": self.config.ttl_seconds,
                "eviction_policy": self.config.eviction_policy,
            }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self.stats.reset()
            logger.info("Cache statistics reset")
