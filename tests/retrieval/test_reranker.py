"""Tests for reranking module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.retrieval.reranker import Reranker, RerankResult
from src.retrieval.retriever import RetrievedChunk


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        RetrievedChunk(
            text="Machine learning is a subset of AI.",
            score=0.5,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/doc1.pdf",
            chunk_position=0,
            metadata={},
        ),
        RetrievedChunk(
            text="Deep learning uses neural networks.",
            score=0.6,
            chunk_id="2",
            document_id="doc1",
            document_path="/path/doc1.pdf",
            chunk_position=1,
            metadata={},
        ),
        RetrievedChunk(
            text="Supervised learning requires labeled data.",
            score=0.7,
            chunk_id="3",
            document_id="doc1",
            document_path="/path/doc1.pdf",
            chunk_position=2,
            metadata={},
        ),
    ]


class TestRerankResult:
    """Test RerankResult dataclass."""

    def test_rerank_result_creation(self):
        """Test creating a RerankResult."""
        result = RerankResult(
            original_count=10,
            reranked_count=5,
            rerank_model="test-model",
            score_improvement=0.15,
        )

        assert result.original_count == 10
        assert result.reranked_count == 5
        assert result.score_improvement == 0.15


class TestReranker:
    """Test Reranker class."""

    def test_reranker_initialization(self):
        """Test reranker initialization."""
        reranker = Reranker(model_name="test-model")

        assert reranker.model_name == "test-model"
        assert reranker.batch_size == 32
        assert reranker._model is None  # Lazy load

    def test_rerank_empty_chunks(self, sample_chunks):
        """Test reranking with empty chunks list."""
        reranker = Reranker()

        reranked, result = reranker.rerank("test query", [])

        assert len(reranked) == 0
        assert result.original_count == 0
        assert result.reranked_count == 0

    @patch('src.retrieval.reranker.CrossEncoder')
    def test_rerank_with_model(self, mock_cross_encoder, sample_chunks):
        """Test reranking with mock cross-encoder model."""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9, 0.8, 0.7])
        mock_cross_encoder.return_value = mock_model

        reranker = Reranker()
        reranker._model = mock_model

        reranked, result = reranker.rerank("What is machine learning?", sample_chunks, top_k=2)

        assert len(reranked) == 2
        assert result.original_count == 3
        assert result.reranked_count == 2
        # First chunk should have highest score
        assert reranked[0].score > reranked[1].score

    @patch('src.retrieval.reranker.CrossEncoder')
    def test_rerank_updates_scores(self, mock_cross_encoder, sample_chunks):
        """Test that reranking updates chunk scores."""
        mock_model = MagicMock()
        new_scores = np.array([0.95, 0.85, 0.75])
        mock_model.predict.return_value = new_scores
        mock_cross_encoder.return_value = mock_model

        reranker = Reranker()
        reranker._model = mock_model

        reranked, _ = reranker.rerank("test query", sample_chunks)

        # Scores should be updated
        assert reranked[0].score == pytest.approx(0.95)
        assert reranked[1].score == pytest.approx(0.85)
        assert reranked[2].score == pytest.approx(0.75)

    @patch('src.retrieval.reranker.CrossEncoder')
    def test_rerank_with_scores_simple(self, mock_cross_encoder):
        """Test rerank_with_scores method."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9, 0.7, 0.8])
        mock_cross_encoder.return_value = mock_model

        reranker = Reranker()
        reranker._model = mock_model

        texts = ["Text 1", "Text 2", "Text 3"]
        results = reranker.rerank_with_scores("query", texts, top_k=2)

        assert len(results) == 2
        assert results[0][1] > results[1][1]  # Scores descending

    def test_rerank_with_scores_empty(self):
        """Test rerank_with_scores with empty texts."""
        reranker = Reranker()

        results = reranker.rerank_with_scores("query", [])

        assert len(results) == 0

    @patch('src.retrieval.reranker.CrossEncoder')
    def test_fallback_on_error(self, mock_cross_encoder, sample_chunks):
        """Test fallback when reranking fails."""
        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("Reranking error")
        mock_cross_encoder.return_value = mock_model

        reranker = Reranker()
        reranker._model = mock_model

        reranked, result = reranker.rerank("query", sample_chunks, top_k=2)

        # Should fallback to original order with top_k
        assert len(reranked) == 2
        assert result.original_count == 3
        assert result.score_improvement == 0.0

    @patch('src.retrieval.reranker.CrossEncoder')
    def test_batch_processing(self, mock_cross_encoder, sample_chunks):
        """Test that batch processing works."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9, 0.8, 0.7])
        mock_cross_encoder.return_value = mock_model

        reranker = Reranker(batch_size=2)
        reranker._model = mock_model

        # With 3 chunks and batch_size=2, should call predict twice
        reranked, _ = reranker.rerank("query", sample_chunks)

        # Check that model was called (batching happens internally)
        assert mock_model.predict.called
