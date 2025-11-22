"""Tests for VectorStore interface and implementations."""

import pytest
import numpy as np
from pathlib import Path
import tempfile

from ragged.vectorstore.interface import VectorStore, VectorStoreDocument, VectorStoreQueryResult
from ragged.vectorstore.factory import VectorStoreFactory, VectorStoreType
from ragged.vectorstore.exceptions import VectorStoreConfigError


class TestVectorStoreFactory:
    """Tests for VectorStoreFactory."""

    def test_create_chromadb(self, tmp_path):
        """Test creating ChromaDB backend."""
        config = {"persist_directory": str(tmp_path / "chroma")}
        store = VectorStoreFactory.create(backend="chromadb", config=config)
        assert store is not None
        assert store.health_check()

    def test_create_auto_backend(self, tmp_path):
        """Test auto-selecting backend."""
        store = VectorStoreFactory.create(backend="auto")
        assert store is not None
        assert store.health_check()

    def test_create_unknown_backend_raises(self):
        """Test that unknown backend raises error."""
        with pytest.raises(VectorStoreConfigError):
            VectorStoreFactory.create(backend="unknown")

    def test_get_available_backends(self):
        """Test getting available backends."""
        backends = VectorStoreFactory.get_available_backends()
        assert isinstance(backends, list)
        assert "chromadb" in backends  # Should be available

    def test_get_backend_support_info(self):
        """Test getting backend support information."""
        info = VectorStoreFactory.get_backend_support_info()

        assert "platform" in info
        assert "backend_support" in info
        assert "available_backends" in info
        assert "default_backend" in info

        # ChromaDB should always be supported
        assert info["backend_support"]["chromadb"] is True
        assert info["default_backend"] in ("chromadb", "leann")


class TestVectorStoreDocument:
    """Tests for VectorStoreDocument."""

    def test_create_document(self):
        """Test creating a document."""
        doc = VectorStoreDocument(
            id="doc1",
            content="Test content",
            embedding=np.array([0.1, 0.2, 0.3]),
            metadata={"key": "value"},
        )
        assert doc.id == "doc1"
        assert doc.content == "Test content"

    def test_document_to_dict(self):
        """Test converting document to dict."""
        doc = VectorStoreDocument(
            id="doc1",
            content="Test",
            embedding=np.array([0.1, 0.2]),
            metadata={"key": "value"},
        )
        data = doc.to_dict()
        assert data["id"] == "doc1"
        assert data["content"] == "Test"
        assert data["embedding"] == [0.1, 0.2]
        assert data["metadata"]["key"] == "value"


class TestChromaDBStore:
    """Tests for ChromaDB implementation."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create ChromaDB store for testing."""
        config = {"persist_directory": str(tmp_path / "chroma")}
        return VectorStoreFactory.create(backend="chromadb", config=config)

    def test_health_check(self, store):
        """Test health check."""
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

    def test_count(self, store):
        """Test counting documents."""
        ids = ["doc1", "doc2"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        documents = ["Doc 1", "Doc 2"]
        metadatas = [{"source": "test"}, {"source": "test"}]

        store.add(ids, embeddings, documents, metadatas, collection_name="count_test")
        count = store.count(collection_name="count_test")
        assert count == 2

    def test_delete(self, store):
        """Test deleting documents."""
        ids = ["doc1", "doc2", "doc3"]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        metadatas = [{"source": "test"}, {"source": "test"}, {"source": "test"}]

        store.add(ids, embeddings, documents, metadatas, collection_name="delete_test")
        deleted = store.delete(["doc1"], collection_name="delete_test")
        assert deleted == 1

        remaining = store.count(collection_name="delete_test")
        assert remaining == 2

    def test_list_collections(self, store):
        """Test listing collections."""
        store.create_collection("test_collection_1", metadata={"type": "test"})
        store.create_collection("test_collection_2", metadata={"type": "test"})

        collections = store.list_collections()
        assert "test_collection_1" in collections
        assert "test_collection_2" in collections
