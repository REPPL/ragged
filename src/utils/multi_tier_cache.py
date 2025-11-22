"""Multi-tier caching for embeddings and results.

v0.2.9: Three-tier caching strategy for 30-50x performance improvement.
v0.2.10: Replaced pickle with safe JSON serialization (FEAT-SEC-001).

Tiers:
- L1: Query embedding cache (fast, small, in-memory)
- L2: Document embedding cache (medium, disk-backed with LRU)
- L3: Retrieved results cache (comprehensive, existing QueryCache)
"""

import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from src.retrieval.cache import QueryCache
from src.utils.hashing import hash_content
from src.utils.logging import get_logger
from src.utils.serialization import list_to_numpy_array, load_json, numpy_array_to_list, save_json

logger = get_logger(__name__)


@dataclass
class EmbeddingCacheEntry:
    """Cache entry for embeddings."""

    key: str
    embedding: np.ndarray
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class L1QueryEmbeddingCache:
    """L1: Fast in-memory cache for query embeddings.

    Characteristics:
    - Very fast (in-memory only)
    - Small size (100-500 queries)
    - No persistence
    - Thread-safe

    Use case: Recently used queries, repeat searches.
    """

    def __init__(self, maxsize: int = 500):
        """Initialize L1 cache.

        Args:
            maxsize: Maximum number of query embeddings to cache
        """
        self.maxsize = maxsize
        self._cache: OrderedDict[str, EmbeddingCacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

        logger.info(f"Initialized L1 query embedding cache (maxsize={maxsize})")

    def get(self, query: str) -> np.ndarray | None:
        """Get cached query embedding.

        Args:
            query: Query string

        Returns:
            Cached embedding or None if not found
        """
        key = hash_content(query)

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                logger.debug(f"L1 cache miss: {query[:50]}...")
                return None

            entry = self._cache[key]
            self._cache.move_to_end(key)  # Update LRU order
            entry.touch()
            self._hits += 1

            logger.debug(
                f"L1 cache hit: {query[:50]}... "
                f"(accessed {entry.access_count} times)"
            )

            return entry.embedding

    def set(self, query: str, embedding: np.ndarray) -> None:
        """Store query embedding in cache.

        Args:
            query: Query string
            embedding: Query embedding vector
        """
        key = hash_content(query)

        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.maxsize and key not in self._cache:
                oldest_key = next(iter(self._cache))
                logger.debug(f"L1 evicting oldest: {oldest_key[:16]}...")
                del self._cache[oldest_key]

            # Store entry
            entry = EmbeddingCacheEntry(key=key, embedding=embedding)
            self._cache[key] = entry
            self._cache.move_to_end(key)

            logger.debug(
                f"L1 cached query embedding: {query[:50]}... "
                f"(shape={embedding.shape})"
            )

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info(f"Cleared L1 cache ({count} entries)")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "tier": "L1",
                "type": "query_embeddings",
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "utilization": len(self._cache) / self.maxsize,
            }


class L2DocumentEmbeddingCache:
    """L2: Disk-backed cache for document embeddings.

    Characteristics:
    - Medium speed (disk I/O with in-memory index)
    - Medium size (1000-10000 documents)
    - Persistent across restarts
    - LRU eviction policy

    Use case: Frequently accessed documents, stable corpus.
    """

    def __init__(
        self,
        cache_dir: Path,
        maxsize: int = 5000,
        memory_index_size: int = 1000
    ):
        """Initialize L2 cache.

        Args:
            cache_dir: Directory for cache files
            maxsize: Maximum number of document embeddings
            memory_index_size: Number of hot entries to keep in memory
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.maxsize = maxsize
        self.memory_index_size = memory_index_size

        # In-memory hot cache (subset of disk cache)
        self._hot_cache: OrderedDict[str, np.ndarray] = OrderedDict()

        # Disk index tracking all entries (v0.2.10: migrated from .pkl to .json)
        self._index_path = self.cache_dir / "l2_index.json"
        self._index: OrderedDict[str, dict[str, Any]] = self._load_index()

        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._disk_reads = 0
        self._disk_writes = 0

        logger.info(
            f"Initialized L2 document embedding cache "
            f"(maxsize={maxsize}, hot={memory_index_size}, dir={cache_dir})"
        )

    def _load_index(self) -> OrderedDict:
        """Load disk index if exists.

        Security: Replaced pickle with JSON (v0.2.10 FEAT-SEC-001).
        Automatically migrates legacy .pkl index files to .json.
        """
        # Try loading JSON index first
        if self._index_path.exists():
            try:
                data = load_json(self._index_path)
                # Convert to OrderedDict (JSON loads as regular dict)
                index = OrderedDict(data.get("entries", {}))
                logger.info(f"Loaded L2 index: {len(index)} entries")
                return index
            except Exception as e:
                logger.warning(f"Failed to load L2 JSON index: {e}")

        # Try loading legacy pickle index for migration
        pkl_index_path = self.cache_dir / "l2_index.pkl"
        if pkl_index_path.exists():
            try:
                import pickle
                with open(pkl_index_path, "rb") as f:
                    index = pickle.load(f)  # noqa: S301 (migration only)
                logger.info(f"Loaded legacy L2 pickle index: {len(index)} entries")
                logger.info("Auto-migrating L2 index from pickle to JSON...")
                # Save as JSON and remove legacy pkl
                self._index = index
                self._save_index()
                pkl_index_path.unlink()
                logger.info("L2 index migration complete")
                return index
            except Exception as e:
                logger.warning(f"Failed to load legacy L2 pickle index: {e}")

        return OrderedDict()

    def _save_index(self) -> None:
        """Save disk index using safe JSON serialization.

        Security: Replaced pickle with JSON (v0.2.10 FEAT-SEC-001).
        """
        try:
            # Convert datetime objects to ISO strings for JSON compatibility
            serializable_index = {}
            for key, value in self._index.items():
                serializable_entry = value.copy()
                if "created_at" in serializable_entry:
                    serializable_entry["created_at"] = serializable_entry["created_at"].isoformat()
                if "accessed_at" in serializable_entry:
                    serializable_entry["accessed_at"] = serializable_entry["accessed_at"].isoformat()
                if "shape" in serializable_entry:
                    serializable_entry["shape"] = list(serializable_entry["shape"])
                serializable_index[key] = serializable_entry

            data = {"version": "1.0", "entries": serializable_index}
            save_json(data, self._index_path)
        except Exception as e:
            logger.error(f"Failed to save L2 index: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key.

        Note: v0.2.10 migrated from .pkl to .json for security.
        """
        return self.cache_dir / f"{key}.json"

    def _save_embedding_to_disk(self, key: str, embedding: np.ndarray) -> None:
        """Save embedding to disk as JSON.

        Args:
            key: Cache key
            embedding: Numpy array to save

        Security: Replaced pickle with JSON (v0.2.10 FEAT-SEC-001).
        """
        cache_path = self._get_cache_path(key)
        data = {
            "version": "1.0",
            "embedding": numpy_array_to_list(embedding),
            "dtype": str(embedding.dtype),
            "shape": list(embedding.shape),
        }
        save_json(data, cache_path)

    def get(self, doc_id: str) -> np.ndarray | None:
        """Get cached document embedding.

        Args:
            doc_id: Document identifier

        Returns:
            Cached embedding or None if not found
        """
        key = hash_content(doc_id)

        with self._lock:
            # Check hot cache first
            if key in self._hot_cache:
                self._hits += 1
                self._hot_cache.move_to_end(key)
                logger.debug(f"L2 hot cache hit: {doc_id[:50]}...")
                return self._hot_cache[key]

            # Check disk index
            if key not in self._index:
                self._misses += 1
                logger.debug(f"L2 cache miss: {doc_id[:50]}...")
                return None

            # Load from disk (try JSON first, fallback to legacy .pkl for migration)
            cache_path = self._get_cache_path(key)
            pkl_cache_path = self.cache_dir / f"{key}.pkl"

            if not cache_path.exists() and not pkl_cache_path.exists():
                logger.warning(f"L2 index inconsistency: {key} not on disk")
                del self._index[key]
                self._misses += 1
                return None

            try:
                # Try loading JSON cache file
                if cache_path.exists():
                    data = load_json(cache_path)
                    embedding = list_to_numpy_array(data["embedding"])
                # Fallback to legacy pickle for migration
                elif pkl_cache_path.exists():
                    import pickle
                    with open(pkl_cache_path, "rb") as f:
                        embedding = pickle.load(f)  # noqa: S301 (migration only)
                    logger.debug(f"Auto-migrating embedding {key[:16]}... from pickle to JSON")
                    # Save as JSON and remove legacy pkl
                    self._save_embedding_to_disk(key, embedding)
                    pkl_cache_path.unlink()
                else:
                    # Should not reach here due to earlier check
                    self._misses += 1
                    return None

                self._disk_reads += 1
                self._hits += 1

                # Update index LRU
                self._index.move_to_end(key)
                self._index[key]["accessed_at"] = datetime.now()
                self._index[key]["access_count"] += 1

                # Add to hot cache
                self._hot_cache[key] = embedding
                self._hot_cache.move_to_end(key)

                # Evict from hot cache if needed
                if len(self._hot_cache) > self.memory_index_size:
                    oldest_hot_key = next(iter(self._hot_cache))
                    del self._hot_cache[oldest_hot_key]

                logger.debug(
                    f"L2 disk cache hit: {doc_id[:50]}... "
                    f"(accessed {self._index[key]['access_count']} times)"
                )

                return embedding

            except Exception as e:
                logger.error(f"Failed to load L2 cache entry: {e}")
                self._misses += 1
                return None

    def set(self, doc_id: str, embedding: np.ndarray) -> None:
        """Store document embedding in cache.

        Args:
            doc_id: Document identifier
            embedding: Document embedding vector
        """
        key = hash_content(doc_id)

        with self._lock:
            # Evict oldest from disk if at capacity
            if len(self._index) >= self.maxsize and key not in self._index:
                oldest_key = next(iter(self._index))
                oldest_path = self._get_cache_path(oldest_key)

                if oldest_path.exists():
                    oldest_path.unlink()

                del self._index[oldest_key]

                # Remove from hot cache if present
                if oldest_key in self._hot_cache:
                    del self._hot_cache[oldest_key]

                logger.debug(f"L2 evicting oldest: {oldest_key[:16]}...")

            # Save to disk using safe JSON serialization
            try:
                self._save_embedding_to_disk(key, embedding)

                self._disk_writes += 1

                # Update index
                self._index[key] = {
                    "doc_id": doc_id,
                    "created_at": datetime.now(),
                    "accessed_at": datetime.now(),
                    "access_count": 0,
                    "shape": embedding.shape,
                }
                self._index.move_to_end(key)
                self._save_index()

                # Add to hot cache
                self._hot_cache[key] = embedding
                self._hot_cache.move_to_end(key)

                # Evict from hot cache if needed
                if len(self._hot_cache) > self.memory_index_size:
                    oldest_hot_key = next(iter(self._hot_cache))
                    del self._hot_cache[oldest_hot_key]

                logger.debug(
                    f"L2 cached document embedding: {doc_id[:50]}... "
                    f"(shape={embedding.shape})"
                )

            except Exception as e:
                logger.error(f"Failed to save L2 cache entry: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            # Clear disk files
            for key in self._index.keys():
                cache_path = self._get_cache_path(key)
                if cache_path.exists():
                    cache_path.unlink()

            # Clear index
            count = len(self._index)
            self._index.clear()
            self._hot_cache.clear()
            self._save_index()

            self._hits = 0
            self._misses = 0
            self._disk_reads = 0
            self._disk_writes = 0

            logger.info(f"Cleared L2 cache ({count} entries)")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "tier": "L2",
                "type": "document_embeddings",
                "size": len(self._index),
                "maxsize": self.maxsize,
                "hot_cache_size": len(self._hot_cache),
                "hot_cache_maxsize": self.memory_index_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "disk_reads": self._disk_reads,
                "disk_writes": self._disk_writes,
                "utilization": len(self._index) / self.maxsize,
            }


class MultiTierCache:
    """Multi-tier caching system combining L1, L2, and L3 caches.

    Cache hierarchy:
    1. L1: Query embeddings (fast, in-memory)
    2. L2: Document embeddings (disk-backed)
    3. L3: Retrieved results (existing QueryCache)

    Features:
    - Automatic tier selection
    - Cache coherency across tiers
    - Unified statistics
    - Graceful degradation if tier unavailable
    """

    def __init__(
        self,
        cache_dir: Path,
        l1_maxsize: int = 500,
        l2_maxsize: int = 5000,
        l3_maxsize: int = 128,
        enable_l1: bool = True,
        enable_l2: bool = True,
        enable_l3: bool = True,
    ):
        """Initialize multi-tier cache.

        Args:
            cache_dir: Directory for persistent cache files
            l1_maxsize: L1 cache size (query embeddings)
            l2_maxsize: L2 cache size (document embeddings)
            l3_maxsize: L3 cache size (results)
            enable_l1: Enable L1 cache
            enable_l2: Enable L2 cache
            enable_l3: Enable L3 cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize tiers
        self.l1: L1QueryEmbeddingCache | None = None
        self.l2: L2DocumentEmbeddingCache | None = None
        self.l3: QueryCache | None = None

        if enable_l1:
            try:
                self.l1 = L1QueryEmbeddingCache(maxsize=l1_maxsize)
            except Exception as e:
                logger.warning(f"Failed to initialize L1 cache: {e}")

        if enable_l2:
            try:
                l2_dir = self.cache_dir / "l2_embeddings"
                self.l2 = L2DocumentEmbeddingCache(
                    cache_dir=l2_dir,
                    maxsize=l2_maxsize
                )
            except Exception as e:
                logger.warning(f"Failed to initialize L2 cache: {e}")

        if enable_l3:
            try:
                self.l3 = QueryCache(maxsize=l3_maxsize)
            except Exception as e:
                logger.warning(f"Failed to initialize L3 cache: {e}")

        logger.info(
            f"Initialized multi-tier cache: "
            f"L1={'enabled' if self.l1 else 'disabled'}, "
            f"L2={'enabled' if self.l2 else 'disabled'}, "
            f"L3={'enabled' if self.l3 else 'disabled'}"
        )

    # L1 operations
    def get_query_embedding(self, query: str) -> np.ndarray | None:
        """Get cached query embedding from L1.

        Args:
            query: Query string

        Returns:
            Cached embedding or None
        """
        if self.l1 is None:
            return None

        return self.l1.get(query)

    def set_query_embedding(self, query: str, embedding: np.ndarray) -> None:
        """Store query embedding in L1.

        Args:
            query: Query string
            embedding: Query embedding
        """
        if self.l1 is not None:
            self.l1.set(query, embedding)

    # L2 operations
    def get_document_embedding(self, doc_id: str) -> np.ndarray | None:
        """Get cached document embedding from L2.

        Args:
            doc_id: Document identifier

        Returns:
            Cached embedding or None
        """
        if self.l2 is None:
            return None

        return self.l2.get(doc_id)

    def set_document_embedding(self, doc_id: str, embedding: np.ndarray) -> None:
        """Store document embedding in L2.

        Args:
            doc_id: Document identifier
            embedding: Document embedding
        """
        if self.l2 is not None:
            self.l2.set(doc_id, embedding)

    # L3 operations (delegate to QueryCache)
    def get_query_result(
        self,
        query: str,
        collection: str = "default",
        method: str = "hybrid",
        top_k: int = 5
    ) -> Any | None:
        """Get cached query result from L3.

        Args:
            query: Query string
            collection: Collection name
            method: Retrieval method
            top_k: Number of results

        Returns:
            Cached result or None
        """
        if self.l3 is None:
            return None

        return self.l3.get_result(
            query=query,
            collection=collection,
            method=method,
            top_k=top_k
        )

    def set_query_result(
        self,
        query: str,
        result: Any,
        collection: str = "default",
        method: str = "hybrid",
        top_k: int = 5
    ) -> None:
        """Store query result in L3.

        Args:
            query: Query string
            result: Result to cache
            collection: Collection name
            method: Retrieval method
            top_k: Number of results
        """
        if self.l3 is not None:
            self.l3.set_result(
                query=query,
                result=result,
                collection=collection,
                method=method,
                top_k=top_k
            )

    # Cache coherency
    def invalidate_document(self, doc_id: str) -> None:
        """Invalidate all cache entries related to a document.

        Ensures cache coherency when document is updated/deleted.

        Args:
            doc_id: Document identifier
        """
        # Invalidate L2 document embedding
        if self.l2 is not None:
            key = hash_content(doc_id)
            with self.l2._lock:
                if key in self.l2._index:
                    cache_path = self.l2._get_cache_path(key)
                    if cache_path.exists():
                        cache_path.unlink()
                    del self.l2._index[key]

                if key in self.l2._hot_cache:
                    del self.l2._hot_cache[key]

                self.l2._save_index()

        # L3 invalidation handled separately (invalidate_collection)
        logger.info(f"Invalidated cache for document: {doc_id[:50]}...")

    def invalidate_collection(self, collection: str) -> None:
        """Invalidate all cache entries for a collection.

        Args:
            collection: Collection name
        """
        # L3 result cache
        if self.l3 is not None:
            count = self.l3.invalidate_collection(collection)
            logger.info(f"Invalidated {count} L3 entries for collection '{collection}'")

        # L1 and L2 not collection-specific, so no action needed

    def clear_all(self) -> None:
        """Clear all cache tiers."""
        if self.l1 is not None:
            self.l1.clear()

        if self.l2 is not None:
            self.l2.clear()

        if self.l3 is not None:
            self.l3.clear()

        logger.info("Cleared all cache tiers")

    def get_stats(self) -> dict[str, Any]:
        """Get unified statistics across all tiers.

        Returns:
            Dictionary with stats for each tier
        """
        stats = {}

        if self.l1 is not None:
            stats["l1"] = self.l1.stats()

        if self.l2 is not None:
            stats["l2"] = self.l2.stats()

        if self.l3 is not None:
            stats["l3"] = self.l3.stats()

        # Overall statistics
        total_hits = sum(s.get("hits", 0) for s in stats.values())
        total_misses = sum(s.get("misses", 0) for s in stats.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

        stats["overall"] = {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": overall_hit_rate,
            "active_tiers": len(stats) - 1,  # Exclude "overall" itself
        }

        return stats
