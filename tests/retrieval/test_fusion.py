"""Tests for fusion algorithms (RRF and weighted fusion)."""

import pytest
from src.retrieval.fusion import reciprocal_rank_fusion, weighted_fusion


@pytest.fixture
def sample_rankings():
    """Sample rankings from two different retrieval methods."""
    # Format: (doc_id, content, score, metadata)
    ranking1 = [
        ("doc1", "First document", 0.95, {"source": "method1"}),
        ("doc2", "Second document", 0.85, {"source": "method1"}),
        ("doc3", "Third document", 0.75, {"source": "method1"}),
    ]

    ranking2 = [
        ("doc2", "Second document", 0.90, {"source": "method2"}),
        ("doc4", "Fourth document", 0.80, {"source": "method2"}),
        ("doc1", "First document", 0.70, {"source": "method2"}),
    ]

    return [ranking1, ranking2]


@pytest.fixture
def empty_rankings():
    """Empty rankings for edge case testing."""
    return [[], []]


class TestReciprocalRankFusion:
    """Test Reciprocal Rank Fusion algorithm."""

    def test_rrf_basic(self, sample_rankings):
        """Test basic RRF fusion."""
        results = reciprocal_rank_fusion(sample_rankings, k=60)

        assert len(results) > 0
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 4 for r in results)

    def test_rrf_combines_rankings(self, sample_rankings):
        """Test RRF combines documents from both rankings."""
        results = reciprocal_rank_fusion(sample_rankings, k=60)

        doc_ids = [doc_id for doc_id, _, _, _ in results]

        # Should include docs from both rankings
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        assert "doc3" in doc_ids
        assert "doc4" in doc_ids

    def test_rrf_boost_common_documents(self, sample_rankings):
        """Test RRF boosts documents appearing in multiple rankings."""
        results = reciprocal_rank_fusion(sample_rankings, k=60)

        # doc1 and doc2 appear in both rankings, should be ranked higher
        # Extract doc_ids and their positions
        doc_ids = [doc_id for doc_id, _, _, _ in results]

        # doc1 and doc2 should be in top positions
        assert "doc1" in doc_ids[:2] or "doc2" in doc_ids[:2]

    def test_rrf_scores_descending(self, sample_rankings):
        """Test RRF scores are in descending order."""
        results = reciprocal_rank_fusion(sample_rankings, k=60)

        scores = [score for _, _, score, _ in results]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_with_different_k(self):
        """Test RRF with different k values."""
        rankings = [
            [("doc1", "content", 1.0, {})],
            [("doc2", "content", 1.0, {})],
        ]

        results_k60 = reciprocal_rank_fusion(rankings, k=60)
        results_k100 = reciprocal_rank_fusion(rankings, k=100)

        # Different k values should produce different scores
        scores_k60 = [s for _, _, s, _ in results_k60]
        scores_k100 = [s for _, _, s, _ in results_k100]

        assert scores_k60 != scores_k100

    def test_rrf_empty_rankings(self, empty_rankings):
        """Test RRF with empty rankings."""
        results = reciprocal_rank_fusion(empty_rankings, k=60)
        assert results == []

    def test_rrf_single_ranking(self):
        """Test RRF with single ranking."""
        rankings = [
            [
                ("doc1", "First", 0.9, {}),
                ("doc2", "Second", 0.8, {}),
            ]
        ]

        results = reciprocal_rank_fusion(rankings, k=60)

        assert len(results) == 2
        assert results[0][0] == "doc1"  # Maintains order

    def test_rrf_preserves_metadata(self, sample_rankings):
        """Test RRF preserves document metadata."""
        results = reciprocal_rank_fusion(sample_rankings, k=60)

        for doc_id, content, score, metadata in results:
            assert isinstance(metadata, dict)
            # Should have metadata from first occurrence
            if doc_id == "doc1":
                assert "source" in metadata


class TestWeightedFusion:
    """Test weighted score fusion algorithm."""

    def test_weighted_basic(self, sample_rankings):
        """Test basic weighted fusion."""
        weights = [0.6, 0.4]
        results = weighted_fusion(sample_rankings, weights)

        assert len(results) > 0
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 4 for r in results)

    def test_weighted_equal_weights(self, sample_rankings):
        """Test weighted fusion with equal weights."""
        weights = [0.5, 0.5]
        results = weighted_fusion(sample_rankings, weights)

        # Should combine all unique documents
        doc_ids = [doc_id for doc_id, _, _, _ in results]
        assert len(set(doc_ids)) == 4  # 4 unique docs

    def test_weighted_scores_descending(self, sample_rankings):
        """Test weighted scores are descending."""
        weights = [0.6, 0.4]
        results = weighted_fusion(sample_rankings, weights)

        scores = [score for _, _, score, _ in results]
        assert scores == sorted(scores, reverse=True)

    def test_weighted_different_weights(self, sample_rankings):
        """Test different weight distributions."""
        results_heavy1 = weighted_fusion(sample_rankings, [0.9, 0.1])
        results_heavy2 = weighted_fusion(sample_rankings, [0.1, 0.9])

        scores_heavy1 = [s for _, _, s, _ in results_heavy1]
        scores_heavy2 = [s for _, _, s, _ in results_heavy2]

        # Different weights should produce different scores
        assert scores_heavy1 != scores_heavy2

    def test_weighted_invalid_weight_count(self, sample_rankings):
        """Test weighted fusion with wrong number of weights."""
        with pytest.raises(ValueError, match="must match number of weights"):
            weighted_fusion(sample_rankings, [0.5])  # Only 1 weight for 2 rankings

    def test_weighted_weights_not_sum_to_one(self, sample_rankings):
        """Test weighted fusion with weights not summing to 1.0."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            weighted_fusion(sample_rankings, [0.3, 0.3])  # Sum = 0.6

    def test_weighted_empty_rankings(self, empty_rankings):
        """Test weighted fusion with empty rankings."""
        results = weighted_fusion(empty_rankings, [0.5, 0.5])
        assert results == []

    def test_weighted_preserves_content(self, sample_rankings):
        """Test weighted fusion preserves document content."""
        results = weighted_fusion(sample_rankings, [0.5, 0.5])

        for doc_id, content, score, metadata in results:
            assert isinstance(content, str)
            assert len(content) > 0

    def test_weighted_normalization(self):
        """Test score normalization in weighted fusion."""
        rankings = [
            [
                ("doc1", "content", 100.0, {}),  # High raw score
                ("doc2", "content", 50.0, {}),
            ],
            [
                ("doc3", "content", 1.0, {}),  # Low raw score
                ("doc4", "content", 0.5, {}),
            ],
        ]

        results = weighted_fusion(rankings, [0.5, 0.5])

        # All scores should be normalized to reasonable range
        scores = [s for _, _, s, _ in results]
        assert all(0 <= s <= 1.0 for s in scores)
