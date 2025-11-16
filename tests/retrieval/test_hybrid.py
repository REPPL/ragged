"""Tests for hybrid retrieval combining vector and BM25 search."""

import pytest
from unittest.mock import Mock, MagicMock
from src.retrieval.hybrid import HybridRetriever, HybridConfig
from src.retrieval.retriever import RetrievedChunk
from src.retrieval.bm25 import BM25Retriever


@pytest.fixture
def mock_vector_retriever():
    """Mock vector retriever."""
    mock = Mock()
    mock.retrieve = Mock(return_value=[
        RetrievedChunk(
            text="Vector result 1",
            score=0.95,
            chunk_id="vec1",
            document_id="doc1",
            document_path="file1.txt",
            chunk_position=0,
            metadata={"source_file": "file1.txt", "chunk_index": 0}
        ),
        RetrievedChunk(
            text="Vector result 2",
            score=0.85,
            chunk_id="vec2",
            document_id="doc2",
            document_path="file2.txt",
            chunk_position=0,
            metadata={"source_file": "file2.txt", "chunk_index": 0}
        ),
        RetrievedChunk(
            text="Vector result 3",
            score=0.75,
            chunk_id="vec3",
            document_id="doc3",
            document_path="file3.txt",
            chunk_position=0,
            metadata={"source_file": "file3.txt", "chunk_index": 0}
        ),
    ])
    return mock


@pytest.fixture
def mock_bm25_retriever():
    """Mock BM25 retriever."""
    mock = Mock(spec=BM25Retriever)
    mock.search = Mock(return_value=[
        ("bm25_1", "BM25 result 1", 5.2, {"source_file": "file1.txt", "chunk_index": 0}),
        ("bm25_2", "BM25 result 2", 4.8, {"source_file": "file4.txt", "chunk_index": 0}),
        ("vec2", "Vector result 2", 4.5, {"source_file": "file2.txt", "chunk_index": 0}),
    ])
    mock.index_documents = Mock()
    return mock


@pytest.fixture
def hybrid_retriever(mock_vector_retriever, mock_bm25_retriever):
    """Hybrid retriever with mocked components."""
    return HybridRetriever(mock_vector_retriever, mock_bm25_retriever)


class TestHybridConfig:
    """Test HybridConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = HybridConfig()

        assert config.method == "hybrid"
        assert config.fusion == "rrf"
        assert config.rrf_k == 60
        assert config.alpha == 0.5
        assert config.top_k_multiplier == 2

    def test_custom_config(self):
        """Test custom configuration."""
        config = HybridConfig(
            method="vector",
            fusion="weighted",
            rrf_k=100,
            alpha=0.7,
            top_k_multiplier=3
        )

        assert config.method == "vector"
        assert config.fusion == "weighted"
        assert config.rrf_k == 100
        assert config.alpha == 0.7
        assert config.top_k_multiplier == 3


class TestHybridRetrieverInit:
    """Test HybridRetriever initialization."""

    def test_init_default_config(self, mock_vector_retriever, mock_bm25_retriever):
        """Test initialization with default config."""
        retriever = HybridRetriever(mock_vector_retriever, mock_bm25_retriever)

        assert retriever.vector == mock_vector_retriever
        assert retriever.bm25 == mock_bm25_retriever
        assert isinstance(retriever.config, HybridConfig)
        assert retriever.config.method == "hybrid"

    def test_init_custom_config(self, mock_vector_retriever, mock_bm25_retriever):
        """Test initialization with custom config."""
        config = HybridConfig(method="vector", alpha=0.8)
        retriever = HybridRetriever(mock_vector_retriever, mock_bm25_retriever, config)

        assert retriever.config == config
        assert retriever.config.alpha == 0.8


class TestVectorOnlyRetrieval:
    """Test vector-only retrieval mode."""

    def test_vector_only_mode(self, hybrid_retriever, mock_vector_retriever):
        """Test retrieval using vector mode."""
        results = hybrid_retriever.retrieve("test query", top_k=5, method="vector")

        # Should call only vector retriever (note: Retriever.retrieve uses k= parameter)
        mock_vector_retriever.retrieve.assert_called_once_with("test query", k=5)
        assert len(results) == 3  # From mock

    def test_vector_only_returns_chunks(self, hybrid_retriever):
        """Test vector-only returns RetrievedChunk objects."""
        results = hybrid_retriever.retrieve("test query", method="vector")

        assert all(isinstance(chunk, RetrievedChunk) for chunk in results)


class TestBM25OnlyRetrieval:
    """Test BM25-only retrieval mode."""

    def test_bm25_only_mode(self, hybrid_retriever, mock_bm25_retriever):
        """Test retrieval using BM25 mode."""
        results = hybrid_retriever.retrieve("test query", top_k=5, method="bm25")

        # Should call only BM25 retriever
        mock_bm25_retriever.search.assert_called_once_with("test query", top_k=5)
        assert len(results) == 3  # From mock

    def test_bm25_only_converts_to_chunks(self, hybrid_retriever):
        """Test BM25-only converts tuples to RetrievedChunk objects."""
        results = hybrid_retriever.retrieve("test query", method="bm25")

        assert all(isinstance(chunk, RetrievedChunk) for chunk in results)

        # Check conversion is correct
        first_chunk = results[0]
        assert first_chunk.chunk_id == "bm25_1"
        assert first_chunk.text == "BM25 result 1"
        assert first_chunk.score == 5.2
        assert first_chunk.document_path == "file1.txt"


class TestHybridRetrieval:
    """Test hybrid retrieval mode."""

    def test_hybrid_mode(self, hybrid_retriever, mock_vector_retriever, mock_bm25_retriever):
        """Test hybrid retrieval calls both methods."""
        results = hybrid_retriever.retrieve("test query", top_k=5, method="hybrid")

        # Should call both retrievers with expanded k
        expected_k = 5 * hybrid_retriever.config.top_k_multiplier
        mock_vector_retriever.retrieve.assert_called_once_with("test query", top_k=expected_k)
        mock_bm25_retriever.search.assert_called_once_with("test query", top_k=expected_k)

        assert len(results) > 0
        assert all(isinstance(chunk, RetrievedChunk) for chunk in results)

    def test_hybrid_limits_results(self, hybrid_retriever):
        """Test hybrid mode respects top_k limit."""
        results = hybrid_retriever.retrieve("test query", top_k=3, method="hybrid")

        assert len(results) <= 3

    def test_hybrid_fusion_rrf(self, mock_vector_retriever, mock_bm25_retriever):
        """Test hybrid uses RRF fusion by default."""
        config = HybridConfig(fusion="rrf")
        retriever = HybridRetriever(mock_vector_retriever, mock_bm25_retriever, config)

        results = retriever.retrieve("test query", top_k=5, method="hybrid")

        # Should return fused results
        assert len(results) > 0

    def test_hybrid_fusion_weighted(self, mock_vector_retriever, mock_bm25_retriever):
        """Test hybrid uses weighted fusion when configured."""
        config = HybridConfig(fusion="weighted", alpha=0.7)
        retriever = HybridRetriever(mock_vector_retriever, mock_bm25_retriever, config)

        results = retriever.retrieve("test query", top_k=5, method="hybrid")

        # Should return fused results
        assert len(results) > 0


class TestRetrieveMethodSelection:
    """Test retrieval method selection logic."""

    def test_default_method_from_config(self, mock_vector_retriever, mock_bm25_retriever):
        """Test using default method from config."""
        config = HybridConfig(method="bm25")
        retriever = HybridRetriever(mock_vector_retriever, mock_bm25_retriever, config)

        results = retriever.retrieve("test query", top_k=5)

        # Should use BM25 from config
        mock_bm25_retriever.search.assert_called_once()

    def test_method_override(self, hybrid_retriever, mock_vector_retriever):
        """Test method parameter overrides config."""
        # Config has method="hybrid", but we override with "vector"
        results = hybrid_retriever.retrieve("test query", top_k=5, method="vector")

        mock_vector_retriever.retrieve.assert_called_once()

    def test_invalid_method_raises(self, hybrid_retriever):
        """Test invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown retrieval method"):
            hybrid_retriever.retrieve("test query", method="invalid")


class TestUpdateBM25Index:
    """Test BM25 index update functionality."""

    def test_update_bm25_index(self, hybrid_retriever, mock_bm25_retriever):
        """Test updating BM25 index."""
        documents = ["doc1", "doc2", "doc3"]
        doc_ids = ["id1", "id2", "id3"]
        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        hybrid_retriever.update_bm25_index(documents, doc_ids, metadatas)

        # Should call BM25 index_documents
        mock_bm25_retriever.index_documents.assert_called_once_with(
            documents, doc_ids, metadatas
        )

    def test_update_bm25_index_without_metadata(self, hybrid_retriever, mock_bm25_retriever):
        """Test updating BM25 index without metadata."""
        documents = ["doc1", "doc2"]
        doc_ids = ["id1", "id2"]

        hybrid_retriever.update_bm25_index(documents, doc_ids)

        mock_bm25_retriever.index_documents.assert_called_once_with(
            documents, doc_ids, None
        )


class TestHybridIntegration:
    """Integration tests with real BM25 retriever."""

    @pytest.fixture
    def real_bm25_retriever(self):
        """Real BM25 retriever with sample data."""
        retriever = BM25Retriever()
        documents = [
            "Machine learning is a subset of AI",
            "Python is great for data science",
            "Neural networks power deep learning",
        ]
        doc_ids = ["ml", "python", "nn"]
        metadatas = [
            {"source_file": "ai.txt", "chunk_index": 0},
            {"source_file": "prog.txt", "chunk_index": 0},
            {"source_file": "dl.txt", "chunk_index": 0},
        ]
        retriever.index_documents(documents, doc_ids, metadatas)
        return retriever

    def test_hybrid_with_real_bm25(self, mock_vector_retriever, real_bm25_retriever):
        """Test hybrid retrieval with real BM25 component."""
        retriever = HybridRetriever(mock_vector_retriever, real_bm25_retriever)

        results = retriever.retrieve("machine learning", top_k=3, method="hybrid")

        assert len(results) > 0
        assert all(isinstance(chunk, RetrievedChunk) for chunk in results)

    def test_bm25_mode_with_real_retriever(self, mock_vector_retriever, real_bm25_retriever):
        """Test BM25-only mode with real retriever."""
        retriever = HybridRetriever(mock_vector_retriever, real_bm25_retriever)

        results = retriever.retrieve("Python", top_k=2, method="bm25")

        assert len(results) > 0
        # Should find Python document
        assert any("Python" in chunk.text for chunk in results)
