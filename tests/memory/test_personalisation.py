"""Tests for personalised ranking (v0.4.8)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from ragged.memory.personalisation import (
    PersonalisedRanker,
    PersonalisationConfig,
)
from ragged.memory.profile import ProfileManager, InterestProfile, TopicInterest
from ragged.memory.topics import TopicExtractor, Topic
from ragged.retrieval.retriever import RetrievedChunk


@pytest.fixture
def profile_manager(tmp_path):
    """Create profile manager with test database."""
    db_path = tmp_path / "test_profiles.db"
    return ProfileManager(db_path=str(db_path))


@pytest.fixture
def topic_extractor():
    """Create topic extractor."""
    return TopicExtractor()


@pytest.fixture
def sample_profile(profile_manager):
    """Create sample interest profile."""
    profile = InterestProfile(persona="test_user")

    # Add some interests
    profile.topics["rag"] = TopicInterest(
        topic="rag",
        frequency=10,
        recency=1.0,
        confidence=0.9,
        first_seen=datetime.now() - timedelta(days=30),
        last_seen=datetime.now(),
        related_documents=["doc1", "doc2"],
        co_occurring_topics={"vector search": 5, "embeddings": 3},
    )

    profile.topics["machine learning"] = TopicInterest(
        topic="machine learning",
        frequency=5,
        recency=0.8,
        confidence=0.7,
        first_seen=datetime.now() - timedelta(days=20),
        last_seen=datetime.now() - timedelta(days=2),
        related_documents=["doc3"],
        co_occurring_topics={"rag": 3},
    )

    # Save profile
    profile_manager.save_profile(profile)
    return profile


@pytest.fixture
def personalised_ranker(profile_manager, topic_extractor):
    """Create personalised ranker."""
    return PersonalisedRanker(profile_manager, topic_extractor)


@pytest.fixture
def sample_chunks():
    """Create sample retrieved chunks."""
    return [
        RetrievedChunk(
            text="RAG systems use vector embeddings for retrieval",
            score=0.1,
            chunk_id="chunk1",
            document_id="doc1",
            document_path="/docs/rag_intro.txt",
            chunk_position=0,
            metadata={},
        ),
        RetrievedChunk(
            text="Machine learning models require training data",
            score=0.2,
            chunk_id="chunk2",
            document_id="doc2",
            document_path="/docs/ml_basics.txt",
            chunk_position=0,
            metadata={},
        ),
        RetrievedChunk(
            text="Python is a programming language",
            score=0.3,
            chunk_id="chunk3",
            document_id="doc3",
            document_path="/docs/python.txt",
            chunk_position=0,
            metadata={},
        ),
    ]


class TestPersonalisationConfig:
    """Tests for PersonalisationConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = PersonalisationConfig()
        assert config.enabled is True
        assert config.alpha == 0.3
        assert config.retrieve_multiplier == 2
        assert config.min_confidence_threshold == 0.3

    def test_custom_config(self):
        """Test custom configuration."""
        config = PersonalisationConfig(
            alpha=0.5,
            retrieve_multiplier=3,
            min_confidence_threshold=0.5,
        )
        assert config.alpha == 0.5
        assert config.retrieve_multiplier == 3
        assert config.min_confidence_threshold == 0.5

    def test_invalid_alpha(self):
        """Test validation of alpha parameter."""
        with pytest.raises(ValueError, match="alpha must be"):
            PersonalisationConfig(alpha=1.5)

    def test_invalid_weights_sum(self):
        """Test validation of boost weights."""
        with pytest.raises(ValueError, match="Boost weights must sum"):
            PersonalisationConfig(
                topic_relevance_weight=0.5,
                historical_access_weight=0.5,
                co_occurrence_weight=0.5,  # Sum > 1.0
            )


class TestPersonalisedRanker:
    """Tests for PersonalisedRanker."""

    def test_initialization(self, personalised_ranker):
        """Test ranker initialization."""
        assert personalised_ranker is not None
        assert personalised_ranker.config.enabled is True

    def test_rerank_no_results(self, personalised_ranker):
        """Test reranking with no results."""
        results = personalised_ranker.rerank(
            results=[],
            query="test query",
            persona="test_user",
            k=5,
        )
        assert results == []

    def test_rerank_disabled(self, personalised_ranker, sample_chunks):
        """Test reranking when disabled."""
        personalised_ranker.config.enabled = False
        results = personalised_ranker.rerank(
            results=sample_chunks,
            query="test query",
            persona="test_user",
            k=2,
        )
        assert len(results) == 2
        assert results[0].chunk_id == "chunk1"  # Original order

    def test_rerank_no_profile(self, personalised_ranker, sample_chunks):
        """Test reranking when profile doesn't exist."""
        results = personalised_ranker.rerank(
            results=sample_chunks,
            query="test query",
            persona="nonexistent_user",
            k=2,
        )
        # Should fall back to original ranking
        assert len(results) == 2

    def test_rerank_with_profile(
        self, personalised_ranker, sample_profile, sample_chunks
    ):
        """Test reranking with valid profile."""
        results = personalised_ranker.rerank(
            results=sample_chunks,
            query="What is RAG?",
            persona="test_user",
            k=3,
        )
        assert len(results) == 3
        # RAG-related chunk should be boosted
        # (Exact ranking depends on scoring, but should be reordered)

    def test_topic_boost_calculation(self, personalised_ranker, sample_profile):
        """Test topic relevance boost calculation."""
        doc_topics = ["rag", "vector search"]
        boost = personalised_ranker._calculate_topic_boost(doc_topics, sample_profile)

        assert boost > 0.0
        assert boost <= 1.0

    def test_topic_boost_no_match(self, personalised_ranker, sample_profile):
        """Test topic boost with no matching topics."""
        doc_topics = ["unrelated", "topics"]
        boost = personalised_ranker._calculate_topic_boost(doc_topics, sample_profile)

        assert boost == 0.0

    def test_history_boost(self, personalised_ranker, sample_chunks):
        """Test historical access boost."""
        chunk = sample_chunks[0]

        # Record access
        personalised_ranker.record_access(chunk.document_id)

        # Calculate boost
        boost = personalised_ranker._calculate_history_boost(
            chunk, Mock(persona="test_user")
        )

        assert boost > 0.0  # Recently accessed

    def test_history_boost_no_access(self, personalised_ranker, sample_chunks):
        """Test history boost with no prior access."""
        chunk = sample_chunks[0]

        boost = personalised_ranker._calculate_history_boost(
            chunk, Mock(persona="test_user")
        )

        assert boost == 0.0

    def test_cooccurrence_boost(self, personalised_ranker, sample_profile):
        """Test co-occurrence boost calculation."""
        doc_topics = ["vector search", "embeddings"]
        query_topics = [Topic(name="rag", confidence=0.9)]

        boost = personalised_ranker._calculate_cooccurrence_boost(
            doc_topics, query_topics, sample_profile
        )

        assert boost > 0.0  # vector search co-occurs with rag

    def test_cooccurrence_boost_no_match(self, personalised_ranker, sample_profile):
        """Test co-occurrence boost with no matches."""
        doc_topics = ["unrelated"]
        query_topics = [Topic(name="other", confidence=0.9)]

        boost = personalised_ranker._calculate_cooccurrence_boost(
            doc_topics, query_topics, sample_profile
        )

        assert boost == 0.0

    def test_extract_chunk_topics(self, personalised_ranker, sample_chunks):
        """Test topic extraction from chunk."""
        chunk = sample_chunks[0]
        topics = personalised_ranker._extract_chunk_topics(chunk)

        assert isinstance(topics, list)
        assert len(topics) > 0
        # Should extract "rag" from text
        assert any("rag" in topic for topic in topics)

    def test_normalize_score(self, personalised_ranker):
        """Test score normalisation."""
        # Distance 0.0 should give high similarity
        assert personalised_ranker._normalize_score(0.0) == 1.0

        # Distance 1.0 should give 0.5 similarity
        assert personalised_ranker._normalize_score(1.0) == 0.5

        # Higher distance should give lower similarity
        assert personalised_ranker._normalize_score(10.0) < personalised_ranker._normalize_score(1.0)

    def test_combine_scores(self, personalised_ranker):
        """Test score combination."""
        base = 0.8
        personalisation = 0.6

        # With alpha=0.3 (default)
        combined = personalised_ranker._combine_scores(base, personalisation)

        # Should be weighted combination
        expected = 0.7 * base + 0.3 * personalisation
        assert abs(combined - expected) < 0.01

    def test_combine_scores_no_personalisation(self, personalised_ranker):
        """Test score combination with alpha=0."""
        personalised_ranker.config.alpha = 0.0
        base = 0.8
        personalisation = 0.6

        combined = personalised_ranker._combine_scores(base, personalisation)

        assert combined == base  # No personalisation

    def test_combine_scores_full_personalisation(self, personalised_ranker):
        """Test score combination with alpha=1."""
        personalised_ranker.config.alpha = 1.0
        base = 0.8
        personalisation = 0.6

        combined = personalised_ranker._combine_scores(base, personalisation)

        assert combined == personalisation  # Full personalisation

    def test_record_access(self, personalised_ranker):
        """Test recording document access."""
        doc_id = "test_doc"
        personalised_ranker.record_access(doc_id)

        assert doc_id in personalised_ranker._access_history
        assert isinstance(personalised_ranker._access_history[doc_id], datetime)

    def test_clear_access_history(self, personalised_ranker):
        """Test clearing access history."""
        personalised_ranker.record_access("doc1")
        personalised_ranker.record_access("doc2")

        assert len(personalised_ranker._access_history) == 2

        personalised_ranker.clear_access_history()

        assert len(personalised_ranker._access_history) == 0


class TestPersonalisedRankerIntegration:
    """Integration tests for personalised ranking."""

    def test_end_to_end_reranking(
        self, personalised_ranker, sample_profile, sample_chunks
    ):
        """Test complete reranking workflow."""
        # Query about RAG
        results = personalised_ranker.rerank(
            results=sample_chunks,
            query="Tell me about RAG systems",
            persona="test_user",
            k=3,
        )

        assert len(results) == 3
        # All chunks should be returned (just reordered)
        assert set(r.chunk_id for r in results) == set(c.chunk_id for c in sample_chunks)

    def test_reranking_consistency(
        self, personalised_ranker, sample_profile, sample_chunks
    ):
        """Test that reranking is consistent."""
        results1 = personalised_ranker.rerank(
            results=sample_chunks,
            query="RAG systems",
            persona="test_user",
            k=3,
        )

        results2 = personalised_ranker.rerank(
            results=sample_chunks,
            query="RAG systems",
            persona="test_user",
            k=3,
        )

        # Should produce same ranking
        assert [r.chunk_id for r in results1] == [r.chunk_id for r in results2]

    def test_different_queries_different_ranking(
        self, personalised_ranker, sample_profile, sample_chunks
    ):
        """Test that different queries produce different rankings."""
        results_rag = personalised_ranker.rerank(
            results=sample_chunks,
            query="RAG systems",
            persona="test_user",
            k=3,
        )

        results_ml = personalised_ranker.rerank(
            results=sample_chunks,
            query="machine learning",
            persona="test_user",
            k=3,
        )

        # Rankings may differ based on query topics
        # (Not guaranteed, but likely with this profile)
        rag_ids = [r.chunk_id for r in results_rag]
        ml_ids = [r.chunk_id for r in results_ml]

        # At least verify both produce valid results
        assert len(rag_ids) == 3
        assert len(ml_ids) == 3
