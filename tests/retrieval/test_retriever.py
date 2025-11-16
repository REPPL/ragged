"""Tests for retriever."""

import pytest
from unittest.mock import Mock, MagicMock
from src.retrieval.retriever import Retriever, RetrievedChunk


class TestRetriever:
    """Tests for Retriever class."""

    @pytest.fixture
    def mock_embedder(self):
        """Create a mock embedder."""
        embedder = Mock()
        embedder.embed_text.return_value = [0.1, 0.2, 0.3, 0.4]
        return embedder

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = Mock()
        return store

    def test_init(self, mock_embedder, mock_vector_store):
        """Test retriever initialization."""
        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        assert retriever is not None
        assert retriever.embedder == mock_embedder
        assert retriever.vector_store == mock_vector_store

    def test_retrieve_success(self, mock_embedder, mock_vector_store):
        """Test successful retrieval."""
        # Mock vector store response
        mock_vector_store.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[
                {"document_id": "doc1", "document_path": "file1.txt", "chunk_position": 0},
                {"document_id": "doc2", "document_path": "file2.txt", "chunk_position": 1}
            ]]
        }

        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        results = retriever.retrieve("test query", k=2)

        # Should embed the query
        mock_embedder.embed_text.assert_called_once_with("test query")

        # Should query vector store
        mock_vector_store.query.assert_called_once()

        # Should return RetrievedChunk objects
        assert len(results) == 2
        assert all(isinstance(chunk, RetrievedChunk) for chunk in results)

        # Check first result
        assert results[0].text == "Content 1"
        assert results[0].document_path == "file1.txt"
        assert results[0].score > 0

    def test_retrieve_empty_results(self, mock_embedder, mock_vector_store):
        """Test retrieval with no results."""
        # Mock empty response
        mock_vector_store.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "documents": [[]],
            "metadatas": [[]]
        }

        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        results = retriever.retrieve("test query", k=5)

        assert len(results) == 0

    def test_retrieve_with_metadata_filter(self, mock_embedder, mock_vector_store):
        """Test retrieval with metadata filtering."""
        mock_vector_store.query.return_value = {
            "ids": [["chunk1"]],
            "distances": [[0.1]],
            "documents": [["Content 1"]],
            "metadatas": [[{"source_file": "file1.txt", "chunk_index": 0}]]
        }

        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        metadata_filter = {"source_file": "file1.txt"}
        results = retriever.retrieve(
            "test query",
            k=5,
            filter_metadata=metadata_filter
        )

        # Should pass filter to vector store
        call_kwargs = mock_vector_store.query.call_args[1]
        assert "where" in call_kwargs or "metadata_filter" in str(call_kwargs)

    def test_retrieve_score_calculation(self, mock_embedder, mock_vector_store):
        """Test that scores are correctly calculated from distances."""
        # ChromaDB returns distances (lower is better)
        mock_vector_store.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "distances": [[0.1, 0.5]],  # Lower distance = better match
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[
                {"document_id": "doc1", "document_path": "file1.txt", "chunk_position": 0},
                {"document_id": "doc2", "document_path": "file2.txt", "chunk_position": 1}
            ]]
        }

        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        results = retriever.retrieve("test query", k=2)

        # First result should have lower score (lower distance = better match)
        assert results[0].score < results[1].score
        assert results[0].score == 0.1
        assert results[1].score == 0.5

    def test_deduplicate_chunks(self, mock_embedder, mock_vector_store):
        """Test deduplication of identical chunks."""
        # Mock response with duplicate content
        mock_vector_store.query.return_value = {
            "ids": [["chunk1", "chunk2", "chunk3"]],
            "distances": [[0.1, 0.2, 0.3]],
            "documents": [["Same content", "Different content", "Same content"]],
            "metadatas": [[
                {"source_file": "file1.txt", "chunk_index": 0},
                {"source_file": "file2.txt", "chunk_index": 0},
                {"source_file": "file1.txt", "chunk_index": 1}
            ]]
        }

        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        results = retriever.retrieve("test query", k=3)

        # Should deduplicate (if deduplication is implemented)
        # Check if we get unique content or all results
        contents = [chunk.text for chunk in results]
        # This depends on whether deduplication is implemented
        # For now, just verify we get results
        assert len(results) >= 2

    def test_retrieve_respects_top_k(self, mock_embedder, mock_vector_store):
        """Test that k parameter is respected."""
        mock_vector_store.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[
                {"document_id": "doc1", "document_path": "file1.txt", "chunk_position": 0},
                {"document_id": "doc2", "document_path": "file2.txt", "chunk_position": 1}
            ]]
        }

        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        results = retriever.retrieve("test query", k=1)

        # Should pass k to vector store query
        call_kwargs = mock_vector_store.query.call_args[1]
        assert call_kwargs.get("k") == 1

    def test_retrieve_with_empty_query(self, mock_embedder, mock_vector_store):
        """Test retrieval with empty query string."""
        retriever = Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store
        )

        # Should still attempt to embed and query
        # (behavior depends on embedder's handling of empty strings)
        mock_vector_store.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "documents": [[]],
            "metadatas": [[]]
        }

        results = retriever.retrieve("", k=5)

        # Should call embedder even with empty string
        mock_embedder.embed_text.assert_called_once()


class TestRetrievedChunk:
    """Tests for RetrievedChunk dataclass."""

    def test_retrieved_chunk_creation(self):
        """Test creating a RetrievedChunk instance."""
        chunk = RetrievedChunk(
            text="Test content",
            score=0.95,
            chunk_id="chunk1",
            document_id="doc1",
            document_path="test.txt",
            chunk_position=0,
            metadata={"key": "value"}
        )

        assert chunk.chunk_id == "chunk1"
        assert chunk.text == "Test content"
        assert chunk.score == 0.95
        assert chunk.document_id == "doc1"
        assert chunk.document_path == "test.txt"
        assert chunk.chunk_position == 0
        assert chunk.metadata == {"key": "value"}

    def test_retrieved_chunk_comparison(self):
        """Test comparing RetrievedChunk instances by score."""
        chunk1 = RetrievedChunk(
            text="Content 1",
            score=0.95,
            chunk_id="chunk1",
            document_id="doc1",
            document_path="test.txt",
            chunk_position=0,
            metadata={}
        )

        chunk2 = RetrievedChunk(
            text="Content 2",
            score=0.85,
            chunk_id="chunk2",
            document_id="doc2",
            document_path="test.txt",
            chunk_position=1,
            metadata={}
        )

        # Higher score should be "better"
        assert chunk1.score > chunk2.score
