"""Query result caching with LRU eviction policy.

Improves query performance by caching retrieval results.
"""

from typing import Optional, Any, Dict, Tuple
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
import json

from src.utils.hashing import hash_content, hash_query
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0

    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class LRUCache:
    """LRU (Least Recently Used) cache for query results.

    Features:
    - Automatic eviction of least recently used items
    - Hit/miss statistics tracking
    - TTL support (optional)
    - Size-based eviction
    """

    def __init__(
        self,
        maxsize: int = 128,
        ttl_seconds: Optional[int] = None
    ):
        """Initialize LRU cache.

        Args:
            maxsize: Maximum number of entries to cache
            ttl_seconds: Time-to-live in seconds (None = no expiration)
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, **kwargs: Any) -> str:
        """Create cache key from query and parameters.

        Args:
            query: Query string
            **kwargs: Additional parameters (collection, method, top_k, etc.)

        Returns:
            Cache key string
        """
        # Create deterministic key from query and sorted kwargs
        key_parts = [query]
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}={kwargs[k]}")

        key_string = "|".join(key_parts)

        # Hash for fixed-length key
        return hash_content(key_string)

    def get(self, query: str, **kwargs: Any) -> Optional[Any]:
        """Get cached result if available.

        Args:
            query: Query string
            **kwargs: Query parameters

        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(query, **kwargs)

        if key not in self._cache:
            self._misses += 1
            logger.debug(f"Cache miss for query: {query[:50]}...")
            return None

        entry = self._cache[key]

        # Check TTL expiration
        if self.ttl_seconds:
            age = (datetime.now() - entry.created_at).total_seconds()
            if age > self.ttl_seconds:
                logger.debug(f"Cache entry expired (age={age}s)")
                del self._cache[key]
                self._misses += 1
                return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.touch()
        self._hits += 1

        logger.debug(
            f"Cache hit for query: {query[:50]}... "
            f"(accessed {entry.access_count} times)"
        )

        return entry.value

    def set(self, query: str, value: Any, **kwargs: Any) -> None:
        """Store result in cache.

        Args:
            query: Query string
            value: Result to cache
            **kwargs: Query parameters
        """
        key = self._make_key(query, **kwargs)

        # Estimate size (simple approximation)
        size_bytes = len(str(value))

        # Remove oldest entry if at capacity
        if len(self._cache) >= self.maxsize and key not in self._cache:
            oldest_key = next(iter(self._cache))
            logger.debug(f"Evicting oldest cache entry: {oldest_key[:16]}...")
            del self._cache[oldest_key]

        # Create or update entry
        entry = CacheEntry(
            key=key,
            value=value,
            size_bytes=size_bytes
        )

        self._cache[key] = entry
        self._cache.move_to_end(key)

        logger.debug(
            f"Cached result for query: {query[:50]}... "
            f"(size={size_bytes} bytes)"
        )

    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info(f"Cleared {count} cache entries")

    def invalidate(self, query: str, **kwargs: Any) -> bool:
        """Invalidate specific cache entry.

        Args:
            query: Query string
            **kwargs: Query parameters

        Returns:
            True if entry was removed, False if not found
        """
        key = self._make_key(query, **kwargs)

        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache entry for query: {query[:50]}...")
            return True

        return False

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        total_size = sum(entry.size_bytes for entry in self._cache.values())
        avg_size = total_size / len(self._cache) if self._cache else 0

        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "total_size_bytes": total_size,
            "avg_entry_size_bytes": avg_size,
        }

    def __len__(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)

    def __contains__(self, query: str) -> bool:
        """Check if query is cached (approximate)."""
        # Note: This checks without kwargs, so it's approximate
        key_prefix = hash_query(query)
        return any(key.startswith(key_prefix) for key in self._cache.keys())


class QueryCache(LRUCache):
    """Specialized cache for RAG query results.

    Extends LRUCache with RAG-specific functionality.
    """

    def get_result(
        self,
        query: str,
        collection: str = "default",
        method: str = "hybrid",
        top_k: int = 5
    ) -> Optional[Any]:
        """Get cached query result.

        Args:
            query: Query string
            collection: Collection name
            method: Retrieval method
            top_k: Number of results

        Returns:
            Cached result or None
        """
        return self.get(
            query,
            collection=collection,
            method=method,
            top_k=top_k
        )

    def set_result(
        self,
        query: str,
        result: Any,
        collection: str = "default",
        method: str = "hybrid",
        top_k: int = 5
    ) -> None:
        """Store query result in cache.

        Args:
            query: Query string
            result: Result to cache
            collection: Collection name
            method: Retrieval method
            top_k: Number of results
        """
        self.set(
            query,
            result,
            collection=collection,
            method=method,
            top_k=top_k
        )

    def invalidate_collection(self, collection: str) -> int:
        """Invalidate all entries for a collection.

        Args:
            collection: Collection name

        Returns:
            Number of entries invalidated
        """
        # Find all keys with this collection
        to_remove = []
        for key, entry in self._cache.items():
            # Simple check - could be improved with better metadata
            if collection in str(entry.value):
                to_remove.append(key)

        for key in to_remove:
            del self._cache[key]

        logger.info(
            f"Invalidated {len(to_remove)} cache entries for "
            f"collection '{collection}'"
        )

        return len(to_remove)
