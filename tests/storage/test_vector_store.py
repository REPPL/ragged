"""Tests for vector store (ChromaDB wrapper)."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.storage.vector_store import VectorStore


class TestVectorStore:
    """Tests for VectorStore class."""

    @pytest.fixture
    def mock_chroma_client(self):
        """Create a mock ChromaDB client."""
        with patch("src.storage.vector_store.chromadb.HttpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock collection
            mock_collection = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection

            yield mock_client, mock_collection

    def test_init_success(self, mock_chroma_client):
        """Test successful initialization of VectorStore."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        assert store is not None
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )

    def test_add_embeddings(self, mock_chroma_client):
        """Test adding embeddings to the store."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        # Add embeddings
        ids = ["id1", "id2"]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        documents = ["doc1", "doc2"]
        metadatas = [{"key": "value1"}, {"key": "value2"}]

        store.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        mock_collection.add.assert_called_once_with(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def test_query_embeddings(self, mock_chroma_client):
        """Test querying embeddings."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        # Mock query response
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "value1"}, {"key": "value2"}]]
        }

        # Query
        query_embedding = [0.1, 0.2, 0.3]
        results = store.query(query_embedding, top_k=2)

        assert results is not None
        mock_collection.query.assert_called_once()

    def test_delete_embeddings(self, mock_chroma_client):
        """Test deleting embeddings."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        ids = ["id1", "id2"]
        store.delete(ids=ids)

        mock_collection.delete.assert_called_once_with(ids=ids)

    def test_count(self, mock_chroma_client):
        """Test counting embeddings."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        mock_collection.count.return_value = 42

        count = store.count()

        assert count == 42
        mock_collection.count.assert_called_once()

    def test_clear(self, mock_chroma_client):
        """Test clearing collection."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        # Mock count and get for clearing
        mock_collection.count.return_value = 2
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"]
        }

        store.clear()

        # Should delete all IDs
        mock_collection.delete.assert_called()

    def test_health_check_success(self, mock_chroma_client):
        """Test health check with available service."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        mock_client.heartbeat.return_value = 12345

        is_healthy = store.health_check()

        assert is_healthy is True
        mock_client.heartbeat.assert_called_once()

    def test_health_check_failure(self, mock_chroma_client):
        """Test health check with unavailable service."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        mock_client.heartbeat.side_effect = Exception("Connection failed")

        is_healthy = store.health_check()

        assert is_healthy is False

    def test_add_with_invalid_dimensions(self, mock_chroma_client):
        """Test adding embeddings with mismatched dimensions."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        # Mock an error from ChromaDB
        mock_collection.add.side_effect = ValueError("Dimension mismatch")

        with pytest.raises(ValueError):
            store.add(
                ids=["id1"],
                embeddings=[[0.1, 0.2]],  # Wrong dimension
                documents=["doc1"],
                metadatas=[{"key": "value"}]
            )

    def test_query_with_filters(self, mock_chroma_client):
        """Test querying with metadata filters."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        mock_collection.query.return_value = {
            "ids": [["id1"]],
            "distances": [[0.1]],
            "documents": [["doc1"]],
            "metadatas": [[{"key": "value1"}]]
        }

        query_embedding = [0.1, 0.2, 0.3]
        metadata_filter = {"key": "value1"}

        results = store.query(
            query_embedding,
            top_k=1,
            where=metadata_filter
        )

        assert results is not None
        # Verify filter was passed
        call_kwargs = mock_collection.query.call_args[1]
        assert "where" in call_kwargs or len(mock_collection.query.call_args[0]) > 0

    def test_empty_collection_count(self, mock_chroma_client):
        """Test count on empty collection."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        mock_collection.count.return_value = 0

        count = store.count()

        assert count == 0

    def test_clear_empty_collection(self, mock_chroma_client):
        """Test clearing an already empty collection."""
        mock_client, mock_collection = mock_chroma_client

        store = VectorStore(
            chroma_url="http://localhost:8001",
            collection_name="test_collection"
        )

        mock_collection.count.return_value = 0

        # Should not raise error
        store.clear()

        # Should not call delete if collection is empty
        mock_collection.delete.assert_not_called()
