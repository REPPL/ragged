"""Tests for behaviour learning system (v0.4.7)."""

import pytest
from pathlib import Path

from ragged.memory.behaviour import BehaviourLearner, create_behaviour_learner
from ragged.memory.interactions import Interaction, InteractionTracker
from ragged.memory.profile import ProfileManager
from ragged.memory.topic_config import TopicExtractionConfig


class TestBehaviourLearner:
    """Tests for BehaviourLearner class."""

    def test_learner_initialization(self, tmp_path):
        """Test initializing behaviour learner."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        assert learner.profile_manager == manager
        assert learner.extractor is not None
        assert learner.confidence_calculator is not None
        assert learner.knowledge_graph is None
        assert learner.enable_graph_updates is False

    def test_learner_with_custom_config(self, tmp_path):
        """Test learner with custom configuration."""
        manager = ProfileManager(tmp_path / "profiles.db")
        config = TopicExtractionConfig(min_topic_length=5, confidence_threshold=0.5)

        learner = BehaviourLearner(manager, topic_config=config)

        assert learner.extractor.min_topic_length == 5
        assert learner.extractor.min_confidence == 0.5

    def test_process_interaction(self, tmp_path):
        """Test processing single interaction."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        interaction = Interaction(
            persona="researcher",
            query="What are the latest RAG techniques for improving retrieval accuracy?",
            retrieved_doc_ids=["rag_paper_2023.pdf", "retrieval_optimization.md"],
        )

        profile = learner.process_interaction(interaction)

        # Should have extracted topics
        assert len(profile.topics) > 0

        # Should have "rag" topic (capitalized term)
        assert "rag" in profile.topics

        # Topics should have document IDs
        for topic in profile.topics.values():
            assert len(topic.related_documents) > 0

    def test_process_interaction_updates_profile(self, tmp_path):
        """Test that processing updates existing profile."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        # First interaction
        interaction1 = Interaction(
            persona="user",
            query="What is RAG?",
            retrieved_doc_ids=["doc1.pdf"],
        )

        profile1 = learner.process_interaction(interaction1)
        initial_frequency = profile1.topics["rag"].frequency if "rag" in profile1.topics else 0

        # Second interaction (same persona, similar topic)
        interaction2 = Interaction(
            persona="user",
            query="How does RAG work with vector databases?",
            retrieved_doc_ids=["doc2.pdf"],
        )

        profile2 = learner.process_interaction(interaction2)

        # Should have updated frequency
        if "rag" in profile2.topics:
            assert profile2.topics["rag"].frequency > initial_frequency

    def test_process_interaction_co_occurrence(self, tmp_path):
        """Test co-occurring topic detection."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        interaction = Interaction(
            persona="user",
            query="RAG techniques with vector search and privacy considerations",
        )

        profile = learner.process_interaction(interaction)

        # Topics should have co-occurring relationships
        if "rag" in profile.topics:
            rag_topic = profile.topics["rag"]
            # Should have detected other topics as co-occurring
            assert len(rag_topic.co_occurring_topics) > 0

    def test_process_batch(self, tmp_path):
        """Test batch processing of interactions."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        interactions = [
            Interaction(persona="user", query="What is RAG?"),
            Interaction(persona="user", query="How does vector search work?"),
            Interaction(persona="user", query="Privacy in machine learning"),
        ]

        learner.process_batch(interactions)

        # Should have processed all interactions
        profile = manager.get_profile("user")
        assert len(profile.topics) >= 3  # At least RAG, vector, privacy

    def test_get_persona_insights(self, tmp_path):
        """Test getting persona insights."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        # Add some interactions
        interactions = [
            Interaction(persona="researcher", query="What is RAG?"),
            Interaction(persona="researcher", query="How does RAG work?"),
            Interaction(persona="researcher", query="RAG with vector databases"),
        ]

        for interaction in interactions:
            learner.process_interaction(interaction)

        insights = learner.get_persona_insights("researcher")

        assert "top_topics" in insights
        assert "total_topics" in insights
        assert "profile_age_days" in insights
        assert "most_related_topics" in insights

        assert len(insights["top_topics"]) > 0
        assert insights["total_topics"] > 0

    def test_forget_topic(self, tmp_path):
        """Test forgetting (removing) topic from profile."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        interaction = Interaction(persona="user", query="What is RAG?")
        learner.process_interaction(interaction)

        # Verify topic exists
        profile = manager.get_profile("user")
        assert "rag" in profile.topics

        # Forget topic
        removed = learner.forget_topic("user", "RAG")  # Case-insensitive
        assert removed is True

        # Verify topic removed
        profile = manager.get_profile("user")
        assert "rag" not in profile.topics

    def test_reset_profile(self, tmp_path):
        """Test resetting entire profile."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        interaction = Interaction(persona="user", query="What is RAG?")
        learner.process_interaction(interaction)

        # Reset profile
        reset = learner.reset_profile("user")
        assert reset is True

        # Profile should be empty (new profile created on get)
        profile = manager.get_profile("user")
        assert len(profile.topics) == 0

    def test_export_profile(self, tmp_path):
        """Test exporting profile as JSON."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        interaction = Interaction(persona="user", query="What is RAG?")
        learner.process_interaction(interaction)

        json_data = learner.export_profile("user")

        assert '"persona"' in json_data
        assert '"topics"' in json_data
        assert "user" in json_data

    def test_create_behaviour_learner(self, tmp_path):
        """Test helper function to create learner."""
        learner = create_behaviour_learner(tmp_path, enable_graph=False)

        assert learner.profile_manager is not None
        assert learner.knowledge_graph is None

    def test_multiple_personas(self, tmp_path):
        """Test learning for multiple personas (isolation)."""
        manager = ProfileManager(tmp_path / "profiles.db")
        learner = BehaviourLearner(manager)

        # Different personas with different interests
        learner.process_interaction(
            Interaction(persona="researcher", query="What is RAG?")
        )
        learner.process_interaction(
            Interaction(persona="developer", query="How to optimize Python code?")
        )

        researcher_profile = manager.get_profile("researcher")
        developer_profile = manager.get_profile("developer")

        # Profiles should be isolated
        assert "rag" in researcher_profile.topics
        assert "rag" not in developer_profile.topics
        assert "python" in developer_profile.topics
        assert "python" not in researcher_profile.topics


class TestInteractionTrackerIntegration:
    """Tests for InteractionTracker + BehaviourLearner integration."""

    def test_tracker_without_learner(self, tmp_path):
        """Test tracker works without behaviour learner (backwards compatible)."""
        tracker = InteractionTracker(
            persona="user",
            storage_dir=tmp_path / "interactions",
        )

        interaction = tracker.record_interaction(query="What is RAG?")

        assert interaction.query == "What is RAG?"
        assert interaction.persona == "user"

    def test_tracker_with_learner(self, tmp_path):
        """Test tracker with behaviour learner integration."""
        # Create learner
        learner = create_behaviour_learner(tmp_path / "memory")

        # Create tracker with learner
        tracker = InteractionTracker(
            persona="researcher",
            storage_dir=tmp_path / "interactions",
            behaviour_learner=learner,
        )

        # Record interaction
        tracker.record_interaction(
            query="What are the latest RAG techniques?",
            retrieved_doc_ids=["rag_paper.pdf"],
        )

        # Verify profile was updated automatically
        profile = learner.profile_manager.get_profile("researcher")
        assert len(profile.topics) > 0
        assert "rag" in profile.topics

    def test_learner_failure_doesnt_break_recording(self, tmp_path):
        """Test that learner failures don't prevent interaction recording."""
        manager = ProfileManager(tmp_path / "profiles.db")

        # Create a broken learner (no extractor)
        class BrokenLearner:
            profile_manager = manager

            def process_interaction(self, interaction):
                raise RuntimeError("Learner is broken!")

        tracker = InteractionTracker(
            persona="user",
            storage_dir=tmp_path / "interactions",
            behaviour_learner=BrokenLearner(),
        )

        # Should still record interaction despite learner failure
        interaction = tracker.record_interaction(query="Test query")

        assert interaction.query == "Test query"

        # Verify interaction was stored
        loaded = tracker.get_interaction(interaction.id)
        assert loaded.query == "Test query"

    def test_realistic_workflow(self, tmp_path):
        """Test realistic end-to-end workflow."""
        # Setup
        learner = create_behaviour_learner(tmp_path / "memory")
        tracker = InteractionTracker(
            persona="researcher",
            storage_dir=tmp_path / "interactions",
            behaviour_learner=learner,
        )

        # Simulate research session
        queries = [
            "What is RAG?",
            "How does retrieval augmented generation work?",
            "Best practices for vector databases",
            "Privacy considerations in RAG systems",
        ]

        for query in queries:
            tracker.record_interaction(
                query=query,
                retrieved_doc_ids=[f"doc_{i}.pdf" for i in range(3)],
            )

        # Get insights
        insights = learner.get_persona_insights("researcher")

        assert insights["total_topics"] >= 4  # RAG, retrieval, vector, privacy
        assert len(insights["top_topics"]) > 0

        # Top topic should be RAG (appears in multiple queries)
        top_topic = insights["top_topics"][0]["topic"]
        assert "rag" in top_topic or "retrieval" in top_topic
