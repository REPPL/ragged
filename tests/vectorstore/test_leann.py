"""Tests for LEANN VectorStore implementation."""

import pytest
import numpy as np
from pathlib import Path

from ragged.vectorstore.interface import VectorStoreDocument
from ragged.vectorstore.exceptions import VectorStoreNotFoundError

# Check if LEANN is available
try:
    from ragged.vectorstore.leann_store import LEANNStore, LEANN_AVAILABLE
except ImportError:
    LEANN_AVAILABLE = False
    LEANNStore = None


@pytest.mark.skipif(not LEANN_AVAILABLE, reason="LEANN not available on this platform")
class TestLEANNStore:
    """Tests for LEANN VectorStore implementation."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create LEANN store for testing."""
        config = {"persist_directory": str(tmp_path / "leann")}
        return LEANNStore(config=config)

    def test_health_check(self, store):
        """Test LEANN health check."""
        assert store.health_check()

    def test_add_and_search(self, store):
        """Test adding and searching documents."""
        # Add documents
        ids = ["doc1", "doc2", "doc3"]
        embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
        documents = ["First doc", "Second doc", "Third doc"]
        metadatas = [{"type": "test"} for _ in range(3)]

        store.add(ids, embeddings, documents, metadatas, collection_name="test")

        # Search
        query_embedding = np.array([0.1, 0.2, 0.3])
        results = store.search(query_embedding, n_results=2, collection_name="test")

        assert len(results.documents) > 0
        assert results.documents[0].id in ids

    def test_search_with_filter(self, store):
        """Test searching with metadata filter."""
        # Add documents with different metadata
        ids = ["doc1", "doc2", "doc3"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        metadatas = [{"type": "A"}, {"type": "B"}, {"type": "A"}]

        store.add(ids, embeddings, documents, metadatas, collection_name="filter_test")

        # Search with filter
        query_embedding = np.array([0.1, 0.2])
        results = store.search(
            query_embedding, n_results=5, collection_name="filter_test", filter_dict={"type": "A"}
        )

        # Should only return docs with type "A"
        for doc in results.documents:
            assert doc.metadata["type"] == "A"

    def test_count(self, store):
        """Test counting documents."""
        ids = ["doc1", "doc2"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        documents = ["Doc 1", "Doc 2"]
        metadatas = [{}, {}]

        store.add(ids, embeddings, documents, metadatas, collection_name="count_test")
        count = store.count(collection_name="count_test")
        assert count == 2

    def test_delete(self, store):
        """Test deleting documents."""
        ids = ["doc1", "doc2", "doc3"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        metadatas = [{}, {}, {}]

        store.add(ids, embeddings, documents, metadatas, collection_name="delete_test")
        deleted = store.delete(["doc1"], collection_name="delete_test")
        assert deleted == 1

        remaining = store.count(collection_name="delete_test")
        assert remaining == 2

    def test_update(self, store):
        """Test updating documents."""
        ids = ["doc1", "doc2"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        documents = ["Doc 1", "Doc 2"]
        metadatas = [{"version": 1}, {"version": 1}]

        store.add(ids, embeddings, documents, metadatas, collection_name="update_test")

        # Update metadata
        new_metadatas = [{"version": 2}]
        updated = store.update(["doc1"], metadatas=new_metadatas, collection_name="update_test")
        assert updated == 1

        # Verify update
        docs = store.get(["doc1"], collection_name="update_test")
        assert docs[0].metadata["version"] == 2

    def test_get(self, store):
        """Test getting documents by ID."""
        ids = ["doc1", "doc2"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        documents = ["Doc 1", "Doc 2"]
        metadatas = [{"key": "value1"}, {"key": "value2"}]

        store.add(ids, embeddings, documents, metadatas, collection_name="get_test")

        docs = store.get(["doc1"], collection_name="get_test")
        assert len(docs) == 1
        assert docs[0].id == "doc1"
        assert docs[0].content == "Doc 1"

    def test_list_collections(self, store):
        """Test listing collections."""
        store.create_collection("test_collection_1")
        store.create_collection("test_collection_2")

        collections = store.list_collections()
        assert "test_collection_1" in collections
        assert "test_collection_2" in collections

    def test_delete_collection(self, store):
        """Test deleting collections."""
        store.create_collection("to_delete")
        assert "to_delete" in store.list_collections()

        store.delete_collection("to_delete")
        assert "to_delete" not in store.list_collections()

    def test_search_nonexistent_collection_raises(self, store):
        """Test searching nonexistent collection raises error."""
        query_embedding = np.array([0.1, 0.2])

        with pytest.raises(VectorStoreNotFoundError):
            store.search(query_embedding, collection_name="nonexistent")


@pytest.mark.skipif(LEANN_AVAILABLE, reason="Test for when LEANN is not available")
def test_leann_import_error_when_not_available():
    """Test that importing LEANN raises ImportError when not available."""
    with pytest.raises(ImportError, match="LEANN not installed"):
        from ragged.vectorstore.leann_store import LEANNStore

        LEANNStore()


class TestLEANNFactoryIntegration:
    """Test LEANN integration with VectorStoreFactory."""

    @pytest.mark.skipif(not LEANN_AVAILABLE, reason="LEANN not available")
    def test_factory_creates_leann_store(self, tmp_path):
        """Test factory can create LEANN store when available."""
        from ragged.vectorstore.factory import VectorStoreFactory

        config = {"persist_directory": str(tmp_path / "leann")}
        store = VectorStoreFactory.create(backend="leann", config=config)

        assert store is not None
        assert store.health_check()

    def test_factory_auto_selection(self):
        """Test factory auto-selects appropriate backend."""
        from ragged.vectorstore.factory import VectorStoreFactory

        # Auto-selection should work regardless of platform
        store = VectorStoreFactory.create(backend="auto")
        assert store is not None
        assert store.health_check()
