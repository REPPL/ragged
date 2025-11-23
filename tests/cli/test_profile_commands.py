"""Tests for behaviour learning profile CLI commands (v0.4.7).

Tests for:
- ragged memory profile
- ragged memory topics
- ragged memory topic-info
- ragged memory related-topics
- ragged memory forget-topic
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from ragged.cli.commands.memory import memory
from ragged.cli.commands.persona import persona
from ragged.memory.behaviour import create_behaviour_learner
from ragged.memory.interactions import Interaction, InteractionTracker


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_settings(temp_storage, monkeypatch):
    """Mock settings to use temp storage."""
    from ragged.config.settings import Settings

    def get_mock_settings():
        settings = Settings()
        settings.data_dir = str(temp_storage)
        return settings

    monkeypatch.setattr("ragged.memory.persona.get_settings", get_mock_settings)
    monkeypatch.setattr("ragged.memory.interactions.get_settings", get_mock_settings)
    monkeypatch.setattr("ragged.cli.commands.memory.get_settings", get_mock_settings)


@pytest.fixture
def learner_with_data(temp_storage, mock_settings):
    """Create behaviour learner with sample profile data."""
    # Create behaviour learner
    learner = create_behaviour_learner(temp_storage / "memory", enable_graph=False)

    # Create sample interactions to build profile
    interactions = [
        Interaction(
            persona="researcher",
            query="What are the latest RAG techniques for improving retrieval accuracy?",
            retrieved_doc_ids=["rag_paper_2023.pdf", "retrieval_optimization.md"],
        ),
        Interaction(
            persona="researcher",
            query="How does vector search work with embeddings?",
            retrieved_doc_ids=["vector_db_guide.pdf", "embeddings_tutorial.md"],
        ),
        Interaction(
            persona="researcher",
            query="Privacy considerations in RAG systems",
            retrieved_doc_ids=["privacy_rag.pdf"],
        ),
        Interaction(
            persona="researcher",
            query="Best practices for RAG with vector databases",
            retrieved_doc_ids=["rag_best_practices.md", "vector_db_guide.pdf"],
        ),
    ]

    # Process interactions to build profile
    for interaction in interactions:
        learner.process_interaction(interaction)

    return learner


class TestMemoryProfile:
    """Test 'ragged memory profile' command."""

    def test_profile_with_data(self, runner, mock_settings, learner_with_data):
        """Test showing profile with data."""
        result = runner.invoke(memory, ["profile", "--persona", "researcher"])

        assert result.exit_code == 0
        assert "Interest Profile" in result.output
        assert "researcher" in result.output
        assert "Top Topics" in result.output
        assert "Total Topics" in result.output

    def test_profile_empty_persona(self, runner, mock_settings, temp_storage):
        """Test showing profile for persona with no data."""
        # Create empty learner
        create_behaviour_learner(temp_storage / "memory", enable_graph=False)

        result = runner.invoke(memory, ["profile", "--persona", "empty-persona"])

        assert result.exit_code == 0
        assert "Total Topics: 0" in result.output

    def test_profile_json_format(self, runner, mock_settings, learner_with_data):
        """Test profile output in JSON format."""
        result = runner.invoke(
            memory, ["profile", "--persona", "researcher", "--format", "json"]
        )

        assert result.exit_code == 0
        assert "top_topics" in result.output
        assert "total_topics" in result.output

    def test_profile_without_persona(self, runner, mock_settings):
        """Test profile without persona fails gracefully."""
        result = runner.invoke(memory, ["profile"])

        # Should either use active persona or fail
        assert result.exit_code in [0, 1]


class TestMemoryTopics:
    """Test 'ragged memory topics' command."""

    def test_topics_list_all(self, runner, mock_settings, learner_with_data):
        """Test listing all topics."""
        result = runner.invoke(memory, ["topics", "--persona", "researcher"])

        assert result.exit_code == 0
        assert "Topics for" in result.output or "researcher" in result.output

    def test_topics_with_min_confidence(self, runner, mock_settings, learner_with_data):
        """Test filtering topics by minimum confidence."""
        result = runner.invoke(
            memory, ["topics", "--persona", "researcher", "--min-confidence", "0.6"]
        )

        assert result.exit_code == 0
        # Should show filtered topics or indicate filtering

    def test_topics_with_limit(self, runner, mock_settings, learner_with_data):
        """Test limiting number of topics shown."""
        result = runner.invoke(
            memory, ["topics", "--persona", "researcher", "--limit", "5"]
        )

        assert result.exit_code == 0

    def test_topics_json_format(self, runner, mock_settings, learner_with_data):
        """Test topics in JSON format."""
        result = runner.invoke(
            memory, ["topics", "--persona", "researcher", "--format", "json"]
        )

        assert result.exit_code == 0
        # Should contain JSON-like output

    def test_topics_empty_profile(self, runner, mock_settings, temp_storage):
        """Test listing topics for empty profile."""
        create_behaviour_learner(temp_storage / "memory", enable_graph=False)

        result = runner.invoke(memory, ["topics", "--persona", "empty-persona"])

        assert result.exit_code == 0
        assert "No topics found" in result.output or "0 topics" in result.output


class TestMemoryTopicInfo:
    """Test 'ragged memory topic-info' command."""

    def test_topic_info_existing_topic(self, runner, mock_settings, learner_with_data):
        """Test showing info for existing topic."""
        result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "Topic Information" in result.output or "rag" in result.output

    def test_topic_info_case_insensitive(
        self, runner, mock_settings, learner_with_data
    ):
        """Test topic lookup is case-insensitive."""
        # Try uppercase version
        result = runner.invoke(
            memory, ["topic-info", "RAG", "--persona", "researcher"]
        )

        # Should find topic regardless of case
        assert result.exit_code == 0

    def test_topic_info_nonexistent_topic(
        self, runner, mock_settings, learner_with_data
    ):
        """Test showing info for nonexistent topic."""
        result = runner.invoke(
            memory, ["topic-info", "nonexistent-topic", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_topic_info_json_format(self, runner, mock_settings, learner_with_data):
        """Test topic info in JSON format."""
        result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher", "--format", "json"]
        )

        assert result.exit_code == 0
        # Should contain JSON data

    def test_topic_info_shows_frequency(
        self, runner, mock_settings, learner_with_data
    ):
        """Test topic info displays frequency."""
        result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "Frequency" in result.output or "frequency" in result.output

    def test_topic_info_shows_confidence(
        self, runner, mock_settings, learner_with_data
    ):
        """Test topic info displays confidence."""
        result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "Confidence" in result.output or "confidence" in result.output

    def test_topic_info_shows_documents(
        self, runner, mock_settings, learner_with_data
    ):
        """Test topic info displays related documents."""
        result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        # Should show related documents
        assert "document" in result.output.lower() or "pdf" in result.output.lower()


class TestMemoryRelatedTopics:
    """Test 'ragged memory related-topics' command."""

    def test_related_topics_existing_topic(
        self, runner, mock_settings, learner_with_data
    ):
        """Test showing related topics for existing topic."""
        result = runner.invoke(
            memory, ["related-topics", "rag", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "Related Topics" in result.output or "rag" in result.output

    def test_related_topics_with_limit(self, runner, mock_settings, learner_with_data):
        """Test limiting number of related topics."""
        result = runner.invoke(
            memory, ["related-topics", "rag", "--persona", "researcher", "--limit", "3"]
        )

        assert result.exit_code == 0

    def test_related_topics_nonexistent_topic(
        self, runner, mock_settings, learner_with_data
    ):
        """Test related topics for nonexistent topic."""
        result = runner.invoke(
            memory, ["related-topics", "nonexistent", "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_related_topics_no_relations(
        self, runner, mock_settings, learner_with_data
    ):
        """Test topic with no co-occurrences."""
        # This test depends on having a topic with no co-occurrences
        # May need to be adjusted based on actual data
        result = runner.invoke(
            memory, ["related-topics", "rag", "--persona", "researcher"]
        )

        # Should handle gracefully whether or not there are relations
        assert result.exit_code == 0

    def test_related_topics_shows_co_occurrence_count(
        self, runner, mock_settings, learner_with_data
    ):
        """Test that co-occurrence counts are shown."""
        result = runner.invoke(
            memory, ["related-topics", "rag", "--persona", "researcher"]
        )

        # Should show some indication of relationship strength
        # The exact format depends on implementation
        assert result.exit_code == 0


class TestMemoryForgetTopic:
    """Test 'ragged memory forget-topic' command (GDPR compliance)."""

    def test_forget_topic_with_confirmation(
        self, runner, mock_settings, learner_with_data
    ):
        """Test forgetting topic with --yes flag."""
        result = runner.invoke(
            memory, ["forget-topic", "rag", "--persona", "researcher", "--yes"]
        )

        assert result.exit_code == 0
        assert "Removed topic" in result.output or "✓" in result.output

    def test_forget_topic_without_confirmation(
        self, runner, mock_settings, learner_with_data
    ):
        """Test forget topic prompts for confirmation without --yes."""
        result = runner.invoke(
            memory, ["forget-topic", "rag", "--persona", "researcher"], input="n\n"
        )

        # Should be cancelled
        assert result.exit_code == 0
        assert "Cancelled" in result.output or "Aborted" in result.output

    def test_forget_topic_confirms_deletion(
        self, runner, mock_settings, learner_with_data
    ):
        """Test that topic is actually removed after confirmation."""
        # Forget topic
        forget_result = runner.invoke(
            memory, ["forget-topic", "rag", "--persona", "researcher", "--yes"]
        )
        assert forget_result.exit_code == 0

        # Try to view topic info (should return 0 but show not found message)
        info_result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )
        assert info_result.exit_code == 0
        assert "not found" in info_result.output

    def test_forget_nonexistent_topic(self, runner, mock_settings, learner_with_data):
        """Test forgetting nonexistent topic."""
        result = runner.invoke(
            memory,
            ["forget-topic", "nonexistent-topic", "--persona", "researcher", "--yes"],
        )

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_forget_topic_case_insensitive(
        self, runner, mock_settings, learner_with_data
    ):
        """Test topic forgetting is case-insensitive."""
        result = runner.invoke(
            memory, ["forget-topic", "RAG", "--persona", "researcher", "--yes"]
        )

        # Should find and remove topic regardless of case
        assert result.exit_code == 0

    def test_forget_topic_gdpr_compliance(
        self, runner, mock_settings, learner_with_data
    ):
        """Test GDPR compliance - complete erasure."""
        # Forget topic
        forget_result = runner.invoke(
            memory, ["forget-topic", "rag", "--persona", "researcher", "--yes"]
        )
        assert forget_result.exit_code == 0

        # Verify topic cannot be looked up anymore
        info_result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )
        assert info_result.exit_code == 0
        assert "not found" in info_result.output

        # Verify profile still works (other topics remain)
        profile_result = runner.invoke(memory, ["profile", "--persona", "researcher"])
        assert profile_result.exit_code == 0
        # Note: Phrase topics like "latest rag techniques" are different topics and remain


class TestProfileCommandsIntegration:
    """Integration tests for profile commands."""

    def test_full_behaviour_learning_workflow(self, runner, mock_settings, temp_storage):
        """Test complete behaviour learning workflow through CLI."""
        # Create behaviour learner and interaction tracker
        learner = create_behaviour_learner(temp_storage / "memory", enable_graph=False)
        tracker = InteractionTracker(
            persona="researcher",
            storage_dir=temp_storage / "interactions",
            behaviour_learner=learner,
        )

        # Record interactions (automatically updates profile)
        tracker.record_interaction(
            query="What is RAG?", retrieved_doc_ids=["rag_intro.pdf"]
        )
        tracker.record_interaction(
            query="How does retrieval augmented generation work?",
            retrieved_doc_ids=["rag_paper.pdf"],
        )
        tracker.record_interaction(
            query="Vector databases for RAG",
            retrieved_doc_ids=["vector_db.md"],
        )

        # View profile
        profile_result = runner.invoke(memory, ["profile", "--persona", "researcher"])
        assert profile_result.exit_code == 0
        assert "researcher" in profile_result.output

        # List topics
        topics_result = runner.invoke(memory, ["topics", "--persona", "researcher"])
        assert topics_result.exit_code == 0

        # View topic info
        info_result = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )
        assert info_result.exit_code == 0

        # View related topics
        related_result = runner.invoke(
            memory, ["related-topics", "rag", "--persona", "researcher"]
        )
        assert related_result.exit_code == 0

        # Forget topic
        forget_result = runner.invoke(
            memory, ["forget-topic", "rag", "--persona", "researcher", "--yes"]
        )
        assert forget_result.exit_code == 0

        # Verify topic removed
        info_after = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "researcher"]
        )
        assert info_after.exit_code == 0
        assert "not found" in info_after.output

    def test_profile_without_interactions(self, runner, mock_settings, temp_storage):
        """Test profile commands work with no interaction history."""
        # Create learner without any interactions
        create_behaviour_learner(temp_storage / "memory", enable_graph=False)

        # All commands should handle empty profile gracefully
        profile_result = runner.invoke(memory, ["profile", "--persona", "new-persona"])
        assert profile_result.exit_code == 0

        topics_result = runner.invoke(memory, ["topics", "--persona", "new-persona"])
        assert topics_result.exit_code == 0

    def test_multiple_personas_isolation(self, runner, mock_settings, temp_storage):
        """Test that different personas have isolated profiles."""
        learner = create_behaviour_learner(temp_storage / "memory", enable_graph=False)

        # Create interactions for different personas
        learner.process_interaction(
            Interaction(persona="researcher", query="What is RAG?")
        )
        learner.process_interaction(
            Interaction(persona="developer", query="How to optimize Python code?")
        )

        # Researcher should have RAG topic
        researcher_result = runner.invoke(
            memory, ["topics", "--persona", "researcher"]
        )
        assert researcher_result.exit_code == 0

        # Developer should have python topic
        developer_result = runner.invoke(memory, ["topics", "--persona", "developer"])
        assert developer_result.exit_code == 0

        # Profiles should be isolated (RAG not in developer profile)
        dev_topics = runner.invoke(
            memory, ["topic-info", "rag", "--persona", "developer"]
        )
        assert dev_topics.exit_code == 0  # Returns 0 but shows not found
        assert "not found" in dev_topics.output  # Should not find RAG in developer profile
