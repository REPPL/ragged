"""Tests for profile analytics (v0.4.8)."""

import pytest
from datetime import datetime, timedelta

from ragged.memory.analytics import ProfileAnalytics, ProfileStatistics
from ragged.memory.profile import ProfileManager, InterestProfile, TopicInterest
from ragged.retrieval.retriever import RetrievedChunk


@pytest.fixture
def profile_manager(tmp_path):
    """Create profile manager with test database."""
    db_path = tmp_path / "test_profiles.db"
    return ProfileManager(db_path=str(db_path))


@pytest.fixture
def sample_profile(profile_manager):
    """Create sample profile with varied topics."""
    profile = InterestProfile(persona="test_user")

    # Add topics with varying confidence
    profile.topics["rag"] = TopicInterest(
        topic="rag",
        frequency=10,
        recency=1.0,
        confidence=0.95,
        first_seen=datetime.now() - timedelta(days=30),
        last_seen=datetime.now(),
        related_documents=["doc1", "doc2", "doc3"],
    )

    profile.topics["machine learning"] = TopicInterest(
        topic="machine learning",
        frequency=5,
        recency=0.8,
        confidence=0.75,
        first_seen=datetime.now() - timedelta(days=20),
        last_seen=datetime.now() - timedelta(days=1),
        related_documents=["doc4"],
    )

    profile.topics["python"] = TopicInterest(
        topic="python",
        frequency=3,
        recency=0.5,
        confidence=0.45,
        first_seen=datetime.now() - timedelta(days=15),
        last_seen=datetime.now() - timedelta(days=5),
        related_documents=[],
    )

    profile_manager.save_profile(profile)
    return profile


@pytest.fixture
def analytics(profile_manager):
    """Create analytics engine."""
    return ProfileAnalytics(profile_manager)


class TestProfileAnalytics:
    """Tests for ProfileAnalytics."""

    def test_initialization(self, analytics):
        """Test analytics initialisation."""
        assert analytics is not None

    def test_get_profile_statistics(self, analytics, sample_profile):
        """Test getting profile statistics."""
        stats = analytics.get_profile_statistics("test_user")

        assert isinstance(stats, ProfileStatistics)
        assert stats.persona == "test_user"
        assert stats.total_topics == 3
        assert stats.high_confidence_topics == 2  # rag, ml
        assert stats.profile_age_days >= 0

    def test_get_profile_statistics_nonexistent(self, analytics):
        """Test getting statistics for nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            analytics.get_profile_statistics("nonexistent")

    def test_topic_distribution(self, analytics, sample_profile):
        """Test topic distribution calculation."""
        stats = analytics.get_profile_statistics("test_user")

        dist = stats.topic_distribution
        assert isinstance(dist, dict)

        # Check ranges exist
        assert "0.0-0.3" in dist
        assert "0.3-0.5" in dist
        assert "0.5-0.7" in dist
        assert "0.7-0.9" in dist
        assert "0.9-1.0" in dist

        # Verify distribution adds up
        assert sum(dist.values()) == 3

    def test_top_topics(self, analytics, sample_profile):
        """Test top topics extraction."""
        stats = analytics.get_profile_statistics("test_user")

        top_topics = stats.top_topics
        assert len(top_topics) <= 10
        assert len(top_topics) == 3  # We have 3 topics

        # Should be sorted by confidence
        confidences = [conf for _, conf, _ in top_topics]
        assert confidences == sorted(confidences, reverse=True)

        # Top topic should be RAG
        assert top_topics[0][0] == "rag"

    def test_compare_ranking(self, analytics):
        """Test ranking comparison."""
        base_results = [
            RetrievedChunk(
                text="doc1", score=0.1, chunk_id="c1", document_id="d1",
                document_path="/d1", chunk_position=0, metadata={}
            ),
            RetrievedChunk(
                text="doc2", score=0.2, chunk_id="c2", document_id="d2",
                document_path="/d2", chunk_position=0, metadata={}
            ),
            RetrievedChunk(
                text="doc3", score=0.3, chunk_id="c3", document_id="d3",
                document_path="/d3", chunk_position=0, metadata={}
            ),
        ]

        personalised_results = [
            base_results[2],  # c3 promoted
            base_results[0],  # c1 same
            base_results[1],  # c2 demoted
        ]

        comparison = analytics.compare_ranking(base_results, personalised_results)

        assert comparison["overlap"] == 3
        assert len(comparison["promoted"]) > 0
        assert len(comparison["demoted"]) > 0
        assert comparison["avg_rank_change"] > 0

    def test_compare_ranking_with_new_docs(self, analytics):
        """Test ranking comparison with different doc sets."""
        base_results = [
            RetrievedChunk(
                text="doc1", score=0.1, chunk_id="c1", document_id="d1",
                document_path="/d1", chunk_position=0, metadata={}
            ),
            RetrievedChunk(
                text="doc2", score=0.2, chunk_id="c2", document_id="d2",
                document_path="/d2", chunk_position=0, metadata={}
            ),
        ]

        personalised_results = [
            base_results[0],  # c1
            RetrievedChunk(  # New doc
                text="doc3", score=0.15, chunk_id="c3", document_id="d3",
                document_path="/d3", chunk_position=0, metadata={}
            ),
        ]

        comparison = analytics.compare_ranking(base_results, personalised_results)

        assert comparison["overlap"] == 1  # Only c1
        assert len(comparison["new_docs"]) == 1  # c3 is new
        assert len(comparison["removed_docs"]) == 1  # c2 removed

    def test_calculate_topic_impact(self, analytics, sample_profile):
        """Test topic impact calculation."""
        impacts = analytics.calculate_topic_impact("test_user", top_n=5)

        assert len(impacts) <= 5
        assert len(impacts) == 3  # We have 3 topics

        # Should be sorted by impact
        impact_scores = [score for _, score in impacts]
        assert impact_scores == sorted(impact_scores, reverse=True)

        # All impacts should be non-negative
        assert all(score >= 0 for _, score in impacts)

    def test_get_profile_health_score(self, analytics, sample_profile):
        """Test profile health score calculation."""
        health = analytics.get_profile_health_score("test_user")

        assert 0.0 <= health <= 1.0

    def test_health_score_empty_profile(self, analytics, profile_manager):
        """Test health score for empty profile."""
        empty_profile = InterestProfile(persona="empty_user")
        profile_manager.save_profile(empty_profile)

        health = analytics.get_profile_health_score("empty_user")

        assert health == 0.0

    def test_generate_profile_report(self, analytics, sample_profile):
        """Test report generation."""
        report = analytics.generate_profile_report("test_user")

        assert isinstance(report, str)
        assert "test_user" in report
        assert "Profile Health" in report
        assert "Statistics" in report
        assert "Topic Distribution" in report
        assert "Top Topics" in report
        assert "Most Impactful Topics" in report

    def test_health_label(self, analytics):
        """Test health label generation."""
        assert analytics._health_label(0.2) == "Poor"
        assert analytics._health_label(0.4) == "Fair"
        assert analytics._health_label(0.6) == "Good"
        assert analytics._health_label(0.8) == "Excellent"
