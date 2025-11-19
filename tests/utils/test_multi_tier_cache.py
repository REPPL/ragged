"""Tests for multi-tier caching system.

v0.2.9: Tests for L1/L2/L3 caches and cache coherency.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil
import time

from src.utils.multi_tier_cache import (
    L1QueryEmbeddingCache,
    L2DocumentEmbeddingCache,
    MultiTierCache,
    EmbeddingCacheEntry,
)


class TestEmbeddingCacheEntry:
    """Tests for EmbeddingCacheEntry dataclass."""

    def test_create_entry(self):
        """Test creating cache entry."""
        embedding = np.array([1.0, 2.0, 3.0])
        entry = EmbeddingCacheEntry(key="test_key", embedding=embedding)

        assert entry.key == "test_key"
        assert np.array_equal(entry.embedding, embedding)
        assert entry.access_count == 0

    def test_touch_updates_access(self):
        """Test touch() updates access time and count."""
        embedding = np.array([1.0, 2.0, 3.0])
        entry = EmbeddingCacheEntry(key="test_key", embedding=embedding)

        original_time = entry.accessed_at
        time.sleep(0.01)

        entry.touch()

        assert entry.access_count == 1
        assert entry.accessed_at > original_time

    def test_multiple_touches(self):
        """Test multiple touch() calls increment count."""
        embedding = np.array([1.0, 2.0, 3.0])
        entry = EmbeddingCacheEntry(key="test_key", embedding=embedding)

        for i in range(5):
            entry.touch()

        assert entry.access_count == 5


class TestL1QueryEmbeddingCache:
    """Tests for L1 query embedding cache."""

    def test_initialization(self):
        """Test L1 cache initialization."""
        cache = L1QueryEmbeddingCache(maxsize=100)

        assert cache.maxsize == 100
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_set_and_get(self):
        """Test storing and retrieving embeddings."""
        cache = L1QueryEmbeddingCache(maxsize=10)
        query = "test query"
        embedding = np.array([1.0, 2.0, 3.0])

        # Store
        cache.set(query, embedding)

        # Retrieve
        result = cache.get(query)

        assert result is not None
        assert np.array_equal(result, embedding)
        assert cache._hits == 1
        assert cache._misses == 0

    def test_cache_miss(self):
        """Test cache miss."""
        cache = L1QueryEmbeddingCache(maxsize=10)

        result = cache.get("nonexistent query")

        assert result is None
        assert cache._hits == 0
        assert cache._misses == 1

    def test_lru_eviction(self):
        """Test LRU eviction when at capacity."""
        cache = L1QueryEmbeddingCache(maxsize=3)

        # Fill cache
        cache.set("query1", np.array([1.0]))
        cache.set("query2", np.array([2.0]))
        cache.set("query3", np.array([3.0]))

        # Add fourth item, should evict query1
        cache.set("query4", np.array([4.0]))

        assert cache.get("query1") is None  # Evicted
        assert cache.get("query2") is not None
        assert cache.get("query3") is not None
        assert cache.get("query4") is not None

    def test_lru_order_updated_on_access(self):
        """Test LRU order updates on access."""
        cache = L1QueryEmbeddingCache(maxsize=3)

        cache.set("query1", np.array([1.0]))
        cache.set("query2", np.array([2.0]))
        cache.set("query3", np.array([3.0]))

        # Access query1 to make it most recent
        cache.get("query1")

        # Add fourth item, should evict query2 (oldest)
        cache.set("query4", np.array([4.0]))

        assert cache.get("query1") is not None  # Not evicted
        assert cache.get("query2") is None  # Evicted
        assert cache.get("query3") is not None
        assert cache.get("query4") is not None

    def test_access_count_tracking(self):
        """Test access count tracking."""
        cache = L1QueryEmbeddingCache(maxsize=10)
        query = "test query"
        embedding = np.array([1.0, 2.0, 3.0])

        cache.set(query, embedding)

        # Access multiple times
        for _ in range(5):
            cache.get(query)

        # Check access count via stats
        key = list(cache._cache.keys())[0]
        entry = cache._cache[key]
        assert entry.access_count == 5

    def test_clear(self):
        """Test clearing cache."""
        cache = L1QueryEmbeddingCache(maxsize=10)

        cache.set("query1", np.array([1.0]))
        cache.set("query2", np.array([2.0]))
        cache.get("query1")

        cache.clear()

        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_stats(self):
        """Test cache statistics."""
        cache = L1QueryEmbeddingCache(maxsize=10)

        cache.set("query1", np.array([1.0]))
        cache.set("query2", np.array([2.0]))

        cache.get("query1")  # Hit
        cache.get("query2")  # Hit
        cache.get("query3")  # Miss

        stats = cache.stats()

        assert stats["tier"] == "L1"
        assert stats["type"] == "query_embeddings"
        assert stats["size"] == 2
        assert stats["maxsize"] == 10
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2/3)
        assert stats["utilization"] == 0.2

    def test_thread_safety(self):
        """Test thread-safe operations."""
        import threading

        cache = L1QueryEmbeddingCache(maxsize=100)
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    query = f"query_{worker_id}_{i}"
                    embedding = np.array([float(worker_id), float(i)])
                    cache.set(query, embedding)
                    result = cache.get(query)
                    assert result is not None
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestL2DocumentEmbeddingCache:
    """Tests for L2 document embedding cache."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_cache_dir):
        """Test L2 cache initialization."""
        cache = L2DocumentEmbeddingCache(
            cache_dir=temp_cache_dir,
            maxsize=100,
            memory_index_size=10
        )

        assert cache.cache_dir == temp_cache_dir
        assert cache.maxsize == 100
        assert cache.memory_index_size == 10
        assert len(cache._index) == 0
        assert len(cache._hot_cache) == 0

    def test_set_and_get(self, temp_cache_dir):
        """Test storing and retrieving document embeddings."""
        cache = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=10)

        doc_id = "doc123"
        embedding = np.array([1.0, 2.0, 3.0])

        # Store
        cache.set(doc_id, embedding)

        # Retrieve
        result = cache.get(doc_id)

        assert result is not None
        assert np.array_equal(result, embedding)
        assert cache._hits == 1
        assert cache._disk_reads == 0  # Hot cache hit

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss."""
        cache = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=10)

        result = cache.get("nonexistent_doc")

        assert result is None
        assert cache._misses == 1

    def test_disk_persistence(self, temp_cache_dir):
        """Test embeddings are persisted to disk."""
        doc_id = "doc123"
        embedding = np.array([1.0, 2.0, 3.0])

        # Create cache, store embedding, destroy
        cache1 = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=10)
        cache1.set(doc_id, embedding)
        del cache1

        # Create new cache, should load from disk
        cache2 = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=10)
        result = cache2.get(doc_id)

        assert result is not None
        assert np.array_equal(result, embedding)

    def test_hot_cache_eviction(self, temp_cache_dir):
        """Test hot cache LRU eviction."""
        cache = L2DocumentEmbeddingCache(
            cache_dir=temp_cache_dir,
            maxsize=100,
            memory_index_size=2  # Small hot cache
        )

        # Add 3 documents
        cache.set("doc1", np.array([1.0]))
        cache.set("doc2", np.array([2.0]))
        cache.set("doc3", np.array([3.0]))

        # Hot cache should only have doc2 and doc3
        assert len(cache._hot_cache) == 2

    def test_disk_eviction(self, temp_cache_dir):
        """Test disk LRU eviction when at maxsize."""
        cache = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=3)

        # Fill cache
        cache.set("doc1", np.array([1.0]))
        cache.set("doc2", np.array([2.0]))
        cache.set("doc3", np.array([3.0]))

        # Add fourth, should evict doc1
        cache.set("doc4", np.array([4.0]))

        assert cache.get("doc1") is None  # Evicted
        assert cache.get("doc2") is not None
        assert cache.get("doc3") is not None
        assert cache.get("doc4") is not None

    def test_disk_read_from_cold(self, temp_cache_dir):
        """Test reading from disk when not in hot cache."""
        cache = L2DocumentEmbeddingCache(
            cache_dir=temp_cache_dir,
            maxsize=10,
            memory_index_size=1  # Very small hot cache
        )

        cache.set("doc1", np.array([1.0]))
        cache.set("doc2", np.array([2.0]))

        # Clear hot cache manually to simulate cold read
        cache._hot_cache.clear()

        # Read should work from disk
        result = cache.get("doc1")

        assert result is not None
        assert np.array_equal(result, np.array([1.0]))
        assert cache._disk_reads == 1

    def test_access_count_tracking(self, temp_cache_dir):
        """Test access count tracking in index."""
        cache = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=10)

        doc_id = "doc123"
        cache.set(doc_id, np.array([1.0, 2.0, 3.0]))

        # Access multiple times
        for _ in range(3):
            cache.get(doc_id)

        # Check access count in index
        from src.utils.hashing import hash_content
        key = hash_content(doc_id)
        assert cache._index[key]["access_count"] == 3

    def test_clear(self, temp_cache_dir):
        """Test clearing cache."""
        cache = L2DocumentEmbeddingCache(cache_dir=temp_cache_dir, maxsize=10)

        cache.set("doc1", np.array([1.0]))
        cache.set("doc2", np.array([2.0]))

        cache.clear()

        assert len(cache._index) == 0
        assert len(cache._hot_cache) == 0
        assert cache.get("doc1") is None
        assert cache.get("doc2") is None

    def test_stats(self, temp_cache_dir):
        """Test cache statistics."""
        cache = L2DocumentEmbeddingCache(
            cache_dir=temp_cache_dir,
            maxsize=10,
            memory_index_size=5
        )

        cache.set("doc1", np.array([1.0]))
        cache.set("doc2", np.array([2.0]))

        cache.get("doc1")  # Hit
        cache.get("doc3")  # Miss

        stats = cache.stats()

        assert stats["tier"] == "L2"
        assert stats["type"] == "document_embeddings"
        assert stats["size"] == 2
        assert stats["maxsize"] == 10
        assert stats["hot_cache_size"] == 2
        assert stats["hot_cache_maxsize"] == 5
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["utilization"] == 0.2


class TestMultiTierCache:
    """Tests for multi-tier cache orchestration."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_initialization_all_tiers(self, temp_cache_dir):
        """Test initializing all cache tiers."""
        cache = MultiTierCache(
            cache_dir=temp_cache_dir,
            l1_maxsize=100,
            l2_maxsize=500,
            l3_maxsize=50
        )

        assert cache.l1 is not None
        assert cache.l2 is not None
        assert cache.l3 is not None

    def test_initialization_selective_tiers(self, temp_cache_dir):
        """Test disabling specific tiers."""
        cache = MultiTierCache(
            cache_dir=temp_cache_dir,
            enable_l1=True,
            enable_l2=False,
            enable_l3=True
        )

        assert cache.l1 is not None
        assert cache.l2 is None
        assert cache.l3 is not None

    def test_l1_query_embedding_operations(self, temp_cache_dir):
        """Test L1 query embedding get/set."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        query = "test query"
        embedding = np.array([1.0, 2.0, 3.0])

        # Set
        cache.set_query_embedding(query, embedding)

        # Get
        result = cache.get_query_embedding(query)

        assert result is not None
        assert np.array_equal(result, embedding)

    def test_l1_disabled(self, temp_cache_dir):
        """Test L1 operations when disabled."""
        cache = MultiTierCache(cache_dir=temp_cache_dir, enable_l1=False)

        query = "test query"
        embedding = np.array([1.0, 2.0, 3.0])

        # Operations should not fail, just do nothing
        cache.set_query_embedding(query, embedding)
        result = cache.get_query_embedding(query)

        assert result is None

    def test_l2_document_embedding_operations(self, temp_cache_dir):
        """Test L2 document embedding get/set."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        doc_id = "doc123"
        embedding = np.array([1.0, 2.0, 3.0])

        # Set
        cache.set_document_embedding(doc_id, embedding)

        # Get
        result = cache.get_document_embedding(doc_id)

        assert result is not None
        assert np.array_equal(result, embedding)

    def test_l2_disabled(self, temp_cache_dir):
        """Test L2 operations when disabled."""
        cache = MultiTierCache(cache_dir=temp_cache_dir, enable_l2=False)

        doc_id = "doc123"
        embedding = np.array([1.0, 2.0, 3.0])

        # Operations should not fail, just do nothing
        cache.set_document_embedding(doc_id, embedding)
        result = cache.get_document_embedding(doc_id)

        assert result is None

    def test_l3_query_result_operations(self, temp_cache_dir):
        """Test L3 query result get/set."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        query = "test query"
        result_data = {"documents": ["doc1", "doc2"], "scores": [0.9, 0.8]}

        # Set
        cache.set_query_result(
            query=query,
            result=result_data,
            collection="test_collection",
            method="hybrid",
            top_k=5
        )

        # Get
        result = cache.get_query_result(
            query=query,
            collection="test_collection",
            method="hybrid",
            top_k=5
        )

        assert result is not None
        assert result == result_data

    def test_l3_disabled(self, temp_cache_dir):
        """Test L3 operations when disabled."""
        cache = MultiTierCache(cache_dir=temp_cache_dir, enable_l3=False)

        query = "test query"
        result_data = {"documents": ["doc1"]}

        # Operations should not fail, just do nothing
        cache.set_query_result(query, result_data)
        result = cache.get_query_result(query)

        assert result is None

    def test_invalidate_document(self, temp_cache_dir):
        """Test document invalidation."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        doc_id = "doc123"
        embedding = np.array([1.0, 2.0, 3.0])

        # Store in L2
        cache.set_document_embedding(doc_id, embedding)
        assert cache.get_document_embedding(doc_id) is not None

        # Invalidate
        cache.invalidate_document(doc_id)

        # Should be removed
        assert cache.get_document_embedding(doc_id) is None

    def test_clear_all(self, temp_cache_dir):
        """Test clearing all tiers."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        # Populate all tiers
        cache.set_query_embedding("query1", np.array([1.0]))
        cache.set_document_embedding("doc1", np.array([2.0]))
        cache.set_query_result("query1", {"data": "result"})

        # Clear all
        cache.clear_all()

        # Verify all empty
        assert cache.get_query_embedding("query1") is None
        assert cache.get_document_embedding("doc1") is None
        assert cache.get_query_result("query1") is None

    def test_get_stats_all_tiers(self, temp_cache_dir):
        """Test unified statistics across all tiers."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        # Add some data to each tier
        cache.set_query_embedding("query1", np.array([1.0]))
        cache.set_document_embedding("doc1", np.array([2.0]))
        cache.set_query_result("query1", {"data": "result"})

        # Trigger some hits and misses
        cache.get_query_embedding("query1")  # Hit
        cache.get_query_embedding("query2")  # Miss
        cache.get_document_embedding("doc1")  # Hit
        cache.get_document_embedding("doc2")  # Miss

        stats = cache.get_stats()

        assert "l1" in stats
        assert "l2" in stats
        assert "l3" in stats
        assert "overall" in stats

        assert stats["overall"]["active_tiers"] == 3
        assert stats["overall"]["total_hits"] >= 2
        assert stats["overall"]["total_misses"] >= 2

    def test_get_stats_partial_tiers(self, temp_cache_dir):
        """Test stats with only some tiers enabled."""
        cache = MultiTierCache(
            cache_dir=temp_cache_dir,
            enable_l1=True,
            enable_l2=False,
            enable_l3=True
        )

        stats = cache.get_stats()

        assert "l1" in stats
        assert "l2" not in stats
        assert "l3" in stats
        assert stats["overall"]["active_tiers"] == 2


class TestCacheCoherency:
    """Integration tests for cache coherency."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_document_update_invalidation(self, temp_cache_dir):
        """Test cache invalidation when document is updated."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        doc_id = "doc123"
        old_embedding = np.array([1.0, 2.0, 3.0])
        new_embedding = np.array([4.0, 5.0, 6.0])

        # Cache old embedding
        cache.set_document_embedding(doc_id, old_embedding)
        assert np.array_equal(cache.get_document_embedding(doc_id), old_embedding)

        # Simulate document update
        cache.invalidate_document(doc_id)

        # Cache should be invalidated
        assert cache.get_document_embedding(doc_id) is None

        # Cache new embedding
        cache.set_document_embedding(doc_id, new_embedding)
        assert np.array_equal(cache.get_document_embedding(doc_id), new_embedding)

    def test_multi_tier_workflow(self, temp_cache_dir):
        """Test realistic multi-tier caching workflow."""
        cache = MultiTierCache(cache_dir=temp_cache_dir)

        # Query 1: Cache miss, populate all tiers
        query1 = "What is machine learning?"
        query1_embedding = np.array([0.1, 0.2, 0.3])
        query1_result = {"documents": ["doc1", "doc2"], "scores": [0.9, 0.8]}

        cache.set_query_embedding(query1, query1_embedding)
        cache.set_query_result(query1, query1_result)

        # Query 2: Same query, cache hits
        assert np.array_equal(cache.get_query_embedding(query1), query1_embedding)
        assert cache.get_query_result(query1) == query1_result

        # Document embedding caching
        doc_id = "doc1"
        doc_embedding = np.array([0.5, 0.6, 0.7])
        cache.set_document_embedding(doc_id, doc_embedding)

        # Verify all tiers working
        stats = cache.get_stats()
        assert stats["l1"]["hits"] >= 1
        assert stats["l3"]["hits"] >= 1

    def test_graceful_tier_failure(self, temp_cache_dir):
        """Test graceful degradation when tier fails."""
        cache = MultiTierCache(
            cache_dir=temp_cache_dir,
            enable_l1=True,
            enable_l2=False,  # L2 disabled
            enable_l3=True
        )

        # L1 and L3 should still work
        cache.set_query_embedding("query1", np.array([1.0]))
        cache.set_query_result("query1", {"data": "result"})

        assert cache.get_query_embedding("query1") is not None
        assert cache.get_query_result("query1") is not None

        # L2 operations silently do nothing
        cache.set_document_embedding("doc1", np.array([2.0]))
        assert cache.get_document_embedding("doc1") is None
