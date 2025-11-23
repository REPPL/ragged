"""Tests for interest profile management (v0.4.7)."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from ragged.memory.profile import (
    TopicInterest,
    InterestProfile,
    ProfileManager,
)
from ragged.memory.confidence import (
    ConfidenceCalculator,
    update_topic_confidence,
)
from ragged.memory.topics import Topic


class TestTopicInterest:
    """Tests for TopicInterest dataclass."""

    def test_topic_interest_creation(self):
        """Test creating topic interest with defaults."""
        interest = TopicInterest(topic="RAG")

        assert interest.topic == "RAG"
        assert interest.frequency == 1
        assert interest.recency == 1.0
        assert 0.0 <= interest.confidence <= 1.0
        assert isinstance(interest.first_seen, datetime)
        assert isinstance(interest.last_seen, datetime)
        assert interest.related_documents == []
        assert interest.co_occurring_topics == {}

    def test_topic_interest_validation(self):
        """Test topic interest validation."""
        # Valid
        TopicInterest(topic="test", recency=0.5, confidence=0.8, frequency=5)

        # Invalid recency
        with pytest.raises(ValueError, match="Recency must be 0.0-1.0"):
            TopicInterest(topic="test", recency=1.5)

        # Invalid confidence
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            TopicInterest(topic="test", confidence=-0.1)

        # Invalid frequency
        with pytest.raises(ValueError, match="Frequency must be >= 1"):
            TopicInterest(topic="test", frequency=0)

    def test_topic_interest_serialization(self):
        """Test to_dict/from_dict roundtrip."""
        interest = TopicInterest(
            topic="RAG",
            frequency=10,
            recency=0.8,
            confidence=0.9,
            related_documents=["doc1", "doc2"],
            co_occurring_topics={"privacy": 3, "vector": 2},
        )

        interest_dict = interest.to_dict()
        restored = TopicInterest.from_dict(interest_dict)

        assert restored.topic == interest.topic
        assert restored.frequency == interest.frequency
        assert restored.recency == interest.recency
        assert restored.confidence == interest.confidence
        assert restored.related_documents == interest.related_documents
        assert restored.co_occurring_topics == interest.co_occurring_topics


class TestInterestProfile:
    """Tests for InterestProfile."""

    def test_profile_creation(self):
        """Test creating empty profile."""
        profile = InterestProfile(persona="researcher")

        assert profile.persona == "researcher"
        assert profile.topics == {}
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)

    def test_update_topic_interest_new(self):
        """Test adding new topic to profile."""
        profile = InterestProfile(persona="user")
        topic = Topic(name="RAG", confidence=0.9)

        profile.update_topic_interest(topic, doc_ids=["doc1.pdf"])

        assert "rag" in profile.topics  # Normalized to lowercase
        interest = profile.topics["rag"]
        assert interest.frequency == 1
        assert interest.recency == 1.0
        assert "doc1.pdf" in interest.related_documents

    def test_update_topic_interest_existing(self):
        """Test updating existing topic in profile."""
        profile = InterestProfile(persona="user")
        topic = Topic(name="RAG", confidence=0.9)

        # First update
        profile.update_topic_interest(topic, doc_ids=["doc1.pdf"])

        # Second update
        profile.update_topic_interest(topic, doc_ids=["doc2.pdf"])

        interest = profile.topics["rag"]
        assert interest.frequency == 2
        assert interest.recency == 1.0  # Reset to 1.0 on update
        assert "doc1.pdf" in interest.related_documents
        assert "doc2.pdf" in interest.related_documents

    def test_update_topic_with_related_topics(self):
        """Test updating topic with co-occurring topics."""
        profile = InterestProfile(persona="user")
        topic = Topic(name="RAG", confidence=0.9)

        profile.update_topic_interest(topic, related_topics=["privacy", "vector search"])

        interest = profile.topics["rag"]
        assert "privacy" in interest.co_occurring_topics
        assert "vector search" in interest.co_occurring_topics
        assert interest.co_occurring_topics["privacy"] == 1

        # Update again with same related topics
        profile.update_topic_interest(topic, related_topics=["privacy"])
        assert interest.co_occurring_topics["privacy"] == 2

    def test_get_top_topics(self):
        """Test getting top topics by confidence."""
        profile = InterestProfile(persona="user")

        # Add topics with different confidences
        profile.update_topic_interest(Topic(name="RAG", confidence=0.9))
        profile.update_topic_interest(Topic(name="privacy", confidence=0.8))
        profile.update_topic_interest(Topic(name="vector", confidence=0.5))
        profile.update_topic_interest(Topic(name="low", confidence=0.2))

        # Get top 2
        top = profile.get_top_topics(limit=2, min_confidence=0.3)

        assert len(top) == 2
        assert top[0].topic == "rag"  # Highest confidence
        assert top[1].topic == "privacy"

    def test_get_topic(self):
        """Test getting specific topic."""
        profile = InterestProfile(persona="user")
        profile.update_topic_interest(Topic(name="RAG", confidence=0.9))

        # Case-insensitive lookup
        interest = profile.get_topic("RAG")
        assert interest is not None
        assert interest.topic == "rag"

        interest = profile.get_topic("rag")
        assert interest is not None

        # Non-existent topic
        assert profile.get_topic("missing") is None

    def test_remove_topic(self):
        """Test removing topic from profile."""
        profile = InterestProfile(persona="user")
        profile.update_topic_interest(Topic(name="RAG", confidence=0.9))

        assert profile.remove_topic("RAG") is True
        assert "rag" not in profile.topics

        # Removing non-existent topic
        assert profile.remove_topic("missing") is False

    def test_apply_time_decay(self):
        """Test applying time decay to topics."""
        profile = InterestProfile(persona="user")

        # Add topic and manually set last_seen to past
        profile.update_topic_interest(Topic(name="old", confidence=0.9))
        profile.topics["old"].last_seen = datetime.now() - timedelta(days=60)

        # Add recent topic
        profile.update_topic_interest(Topic(name="recent", confidence=0.9))

        profile.apply_time_decay(decay_rate=0.1, decay_days=30)

        # Old topic should have lower recency
        assert profile.topics["old"].recency < profile.topics["recent"].recency

    def test_profile_json_export_import(self):
        """Test JSON export/import roundtrip."""
        profile = InterestProfile(persona="researcher")
        profile.update_topic_interest(Topic(name="RAG", confidence=0.9), doc_ids=["doc1.pdf"])
        profile.update_topic_interest(Topic(name="privacy", confidence=0.8))

        # Export
        json_str = profile.export_to_json()
        data = json.loads(json_str)

        assert data["persona"] == "researcher"
        assert "rag" in data["topics"]
        assert "privacy" in data["topics"]

        # Import
        restored = InterestProfile.import_from_json(json_str)

        assert restored.persona == profile.persona
        assert len(restored.topics) == len(profile.topics)
        assert "rag" in restored.topics
        assert restored.topics["rag"].frequency == 1


class TestProfileManager:
    """Tests for ProfileManager."""

    def test_manager_initialization(self, tmp_path):
        """Test initializing profile manager."""
        db_path = tmp_path / "profiles.db"
        manager = ProfileManager(db_path)

        assert db_path.exists()

    def test_get_profile_new(self, tmp_path):
        """Test getting new profile (auto-create)."""
        manager = ProfileManager(tmp_path / "profiles.db")

        profile = manager.get_profile("researcher")

        assert profile.persona == "researcher"
        assert len(profile.topics) == 0

    def test_save_and_load_profile(self, tmp_path):
        """Test saving and loading profile."""
        manager = ProfileManager(tmp_path / "profiles.db")

        # Create and save profile
        profile = manager.get_profile("researcher")
        profile.update_topic_interest(Topic(name="RAG", confidence=0.9))
        manager.save_profile(profile)

        # Load in new manager instance
        manager2 = ProfileManager(tmp_path / "profiles.db")
        loaded = manager2.get_profile("researcher")

        assert "rag" in loaded.topics
        assert loaded.topics["rag"].frequency == 1

    def test_delete_profile(self, tmp_path):
        """Test deleting profile."""
        manager = ProfileManager(tmp_path / "profiles.db")

        # Create and save profile
        profile = manager.get_profile("researcher")
        manager.save_profile(profile)

        # Delete
        assert manager.delete_profile("researcher") is True

        # Verify deleted (get creates new empty profile)
        new_profile = manager.get_profile("researcher")
        assert len(new_profile.topics) == 0

        # Delete non-existent
        assert manager.delete_profile("missing") is False

    def test_list_personas(self, tmp_path):
        """Test listing all personas."""
        manager = ProfileManager(tmp_path / "profiles.db")

        # Create multiple profiles
        for persona in ["researcher", "developer", "student"]:
            profile = manager.get_profile(persona)
            manager.save_profile(profile)

        personas = manager.list_personas()

        assert len(personas) == 3
        assert "researcher" in personas
        assert "developer" in personas
        assert "student" in personas

    def test_export_all_profiles(self, tmp_path):
        """Test exporting all profiles to JSON."""
        manager = ProfileManager(tmp_path / "profiles.db")

        # Create profiles
        for persona in ["researcher", "developer"]:
            profile = manager.get_profile(persona)
            profile.update_topic_interest(Topic(name="test", confidence=0.9))
            manager.save_profile(profile)

        # Export
        export_path = tmp_path / "export.json"
        manager.export_all_profiles(export_path)

        assert export_path.exists()

        # Verify content
        with open(export_path) as f:
            data = json.load(f)

        assert "researcher" in data
        assert "developer" in data
        assert "test" in data["researcher"]["topics"]


class TestConfidenceCalculator:
    """Tests for ConfidenceCalculator."""

    def test_calculator_initialization(self):
        """Test creating confidence calculator."""
        calc = ConfidenceCalculator()

        assert calc.frequency_weight == 0.35
        assert calc.recency_weight == 0.30
        assert calc.consistency_weight == 0.20
        assert calc.depth_weight == 0.15

    def test_custom_weights(self):
        """Test custom weight configuration."""
        calc = ConfidenceCalculator(
            frequency_weight=0.5,
            recency_weight=0.3,
            consistency_weight=0.1,
            depth_weight=0.1,
        )

        assert calc.frequency_weight == 0.5

    def test_invalid_weights(self):
        """Test weights must sum to 1.0."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            ConfidenceCalculator(
                frequency_weight=0.5,
                recency_weight=0.3,
                consistency_weight=0.1,
                depth_weight=0.05,  # Sum = 0.95, not 1.0
            )

    def test_frequency_score(self):
        """Test frequency score calculation."""
        calc = ConfidenceCalculator()

        assert calc.calculate_frequency_score(1) == 0.1
        assert calc.calculate_frequency_score(5) == 0.5
        assert calc.calculate_frequency_score(10) == 1.0
        assert calc.calculate_frequency_score(20) == 1.0  # Capped at 1.0

    def test_recency_score(self):
        """Test recency score calculation."""
        calc = ConfidenceCalculator()

        # Just seen
        score_now = calc.calculate_recency_score(datetime.now())
        assert score_now == 1.0

        # 30 days ago (1 decay period)
        score_30d = calc.calculate_recency_score(datetime.now() - timedelta(days=30))
        assert 0.9 < score_30d < 1.0  # Slight decay

        # 90 days ago (3 decay periods)
        score_90d = calc.calculate_recency_score(datetime.now() - timedelta(days=90))
        assert score_90d < score_30d  # More decay

    def test_consistency_score_single_occurrence(self):
        """Test consistency score for single occurrence."""
        calc = ConfidenceCalculator()

        score = calc.calculate_consistency_score(
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            frequency=1,
        )

        assert score == 0.3  # Low score for single occurrence

    def test_consistency_score_regular_pattern(self):
        """Test consistency score for regular pattern."""
        calc = ConfidenceCalculator()

        # Regular pattern: once per day for 10 days
        now = datetime.now()
        timestamps = [now - timedelta(days=i) for i in range(10)]

        score = calc.calculate_consistency_score(
            first_seen=timestamps[-1],
            last_seen=timestamps[0],
            frequency=10,
            timestamps=timestamps,
        )

        assert score > 0.7  # High score for regular pattern

    def test_depth_score(self):
        """Test depth score calculation."""
        calc = ConfidenceCalculator()

        assert calc.calculate_depth_score([]) == 0.0
        assert calc.calculate_depth_score(["doc1"]) == 0.02
        assert calc.calculate_depth_score(["doc" + str(i) for i in range(25)]) == 0.5
        assert calc.calculate_depth_score(["doc" + str(i) for i in range(50)]) == 1.0

    def test_calculate_confidence(self):
        """Test overall confidence calculation."""
        calc = ConfidenceCalculator()

        confidence = calc.calculate_confidence(
            frequency=24,
            last_seen=datetime.now(),
            first_seen=datetime.now() - timedelta(days=30),
            related_documents=["doc1", "doc2"],
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably high

    def test_update_topic_confidence(self):
        """Test updating topic confidence."""
        interest = TopicInterest(
            topic="RAG",
            frequency=24,
            last_seen=datetime.now(),
            first_seen=datetime.now() - timedelta(days=30),
            related_documents=["doc1", "doc2"],
        )

        original_confidence = interest.confidence

        update_topic_confidence(interest)

        assert interest.confidence != original_confidence
        assert 0.0 <= interest.confidence <= 1.0


class TestIntegration:
    """Integration tests for profile and confidence systems."""

    def test_realistic_profile_workflow(self, tmp_path):
        """Test realistic profile building workflow."""
        manager = ProfileManager(tmp_path / "profiles.db")
        calculator = ConfidenceCalculator()

        # Simulate user research session
        profile = manager.get_profile("researcher")

        # Day 1: Research RAG
        topics = [
            Topic(name="RAG", confidence=0.9),
            Topic(name="retrieval", confidence=0.8),
            Topic(name="vector search", confidence=0.7),
        ]

        for topic in topics:
            profile.update_topic_interest(
                topic,
                doc_ids=["rag_paper_2023.pdf"],
                related_topics=[t.name for t in topics if t.name != topic.name],
            )

        # Update confidences
        for interest in profile.topics.values():
            update_topic_confidence(interest, calculator)

        # Save
        manager.save_profile(profile)

        # Verify
        top_topics = profile.get_top_topics(limit=3)
        assert len(top_topics) == 3
        assert all(t.confidence > 0.5 for t in top_topics)

        # Verify co-occurrence
        rag_interest = profile.get_topic("RAG")
        assert "retrieval" in rag_interest.co_occurring_topics
        assert "vector search" in rag_interest.co_occurring_topics
