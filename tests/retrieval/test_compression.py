"""Tests for contextual compression module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.retrieval.compression import ContextualCompressor, CompressionResult
from src.retrieval.retriever import RetrievedChunk


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        RetrievedChunk(
            text="Machine learning is a subset of AI. It enables systems to learn from data. This is very useful for predictions.",
            score=0.9,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/doc1.pdf",
            chunk_position=0,
            metadata={},
        ),
        RetrievedChunk(
            text="Deep learning uses neural networks. Neural networks have multiple layers. They can learn complex patterns.",
            score=0.8,
            chunk_id="2",
            document_id="doc1",
            document_path="/path/doc1.pdf",
            chunk_position=1,
            metadata={},
        ),
    ]


class TestCompressionResult:
    """Test CompressionResult dataclass."""

    def test_compression_result_creation(self):
        """Test creating a CompressionResult."""
        result = CompressionResult(
            original_length=1000,
            compressed_length=500,
            compression_ratio=0.5,
            chunks_processed=5,
            sentences_extracted=10,
        )

        assert result.original_length == 1000
        assert result.compressed_length == 500
        assert result.compression_ratio == 0.5
        assert result.chunks_processed == 5


class TestContextualCompressor:
    """Test ContextualCompressor class."""

    def test_compressor_initialization(self):
        """Test compressor initialization."""
        compressor = ContextualCompressor(
            target_compression_ratio=0.6,
            min_sentence_score=0.4,
        )

        assert compressor.target_compression_ratio == 0.6
        assert compressor.min_sentence_score == 0.4
        assert compressor.context_sentences == 1

    def test_compress_empty_chunks(self):
        """Test compressing empty chunks list."""
        compressor = ContextualCompressor()

        compressed, result = compressor.compress("test query", [])

        assert len(compressed) == 0
        assert result.original_length == 0
        assert result.compression_ratio == 1.0

    def test_split_sentences(self):
        """Test sentence splitting."""
        compressor = ContextualCompressor()

        text = "First sentence. Second sentence! Third sentence?"
        sentences = compressor._split_sentences(text)

        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]

    def test_split_sentences_empty(self):
        """Test sentence splitting with empty text."""
        compressor = ContextualCompressor()

        sentences = compressor._split_sentences("")

        assert len(sentences) == 0

    @patch('src.retrieval.compression.SentenceTransformer')
    def test_compress_with_model(self, mock_transformer, sample_chunks):
        """Test compression with mock model."""
        # Mock model
        mock_model = MagicMock()
        # Mock embeddings (query + sentences)
        mock_model.encode.side_effect = [
            np.array([1.0, 0.0, 0.0]),  # Query embedding
            np.array([[1.0, 0.0, 0.0], [0.8, 0.2, 0.0], [0.5, 0.5, 0.0]]),  # Sentence embeddings
            np.array([[0.9, 0.1, 0.0], [0.7, 0.3, 0.0], [0.6, 0.4, 0.0]]),  # More sentence embeddings
        ]
        mock_transformer.return_value = mock_model

        compressor = ContextualCompressor(target_compression_ratio=0.5)
        compressor._model = mock_model

        compressed, result = compressor.compress("What is machine learning?", sample_chunks)

        assert len(compressed) <= len(sample_chunks)
        assert result.compression_ratio <= 1.0
        assert result.chunks_processed == 2

    def test_select_sentences_with_scores(self):
        """Test sentence selection based on scores."""
        compressor = ContextualCompressor(
            target_compression_ratio=0.5,
            min_sentence_score=0.3,
        )

        scores = np.array([0.9, 0.7, 0.5, 0.2, 0.1])

        selected = compressor._select_sentences(scores, target_ratio=0.5)

        # Should select top 50% (at least 2 out of 5)
        assert len(selected) >= 2
        # Should be above threshold
        assert all(scores[i] >= compressor.min_sentence_score or i == selected[0] for i in selected)

    def test_select_sentences_all_below_threshold(self):
        """Test sentence selection when all scores below threshold."""
        compressor = ContextualCompressor(min_sentence_score=0.9)

        scores = np.array([0.5, 0.4, 0.3])

        selected = compressor._select_sentences(scores, target_ratio=0.5)

        # Should select at least top 1
        assert len(selected) >= 1

    def test_add_context_sentences(self):
        """Test adding context sentences."""
        compressor = ContextualCompressor(context_sentences=1)

        selected = [2]  # Only middle sentence selected
        total = 5

        expanded = compressor._add_context(selected, total)

        # Should include sentence 2 and neighbors (1, 3)
        assert 2 in expanded
        assert 1 in expanded or 3 in expanded

    def test_reconstruct_text(self):
        """Test text reconstruction from selected sentences."""
        compressor = ContextualCompressor()

        sentences = ["First.", "Second.", "Third.", "Fourth."]
        selected = [0, 2]  # First and third

        reconstructed = compressor._reconstruct_text(sentences, selected)

        assert "First" in reconstructed
        assert "Third" in reconstructed
        assert "Second" not in reconstructed

    def test_reconstruct_text_empty_selection(self):
        """Test text reconstruction with empty selection."""
        compressor = ContextualCompressor()

        sentences = ["First.", "Second."]
        selected = []

        reconstructed = compressor._reconstruct_text(sentences, selected)

        assert reconstructed == ""

    @patch('src.retrieval.compression.SentenceTransformer')
    def test_fallback_on_error(self, mock_transformer, sample_chunks):
        """Test fallback when compression fails."""
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Model error")
        mock_transformer.return_value = mock_model

        compressor = ContextualCompressor()
        compressor._model = mock_model

        compressed, result = compressor.compress("query", sample_chunks)

        # Should fallback to original chunks
        assert len(compressed) == len(sample_chunks)
        assert result.compression_ratio == 1.0
