"""Tests for memory CLI commands.

v0.4.5: Test coverage for memory/interaction management CLI
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from ragged.cli.commands.memory import memory
from ragged.cli.commands.persona import persona
from ragged.memory.interactions import InteractionTracker
from ragged.memory.persona import PersonaManager


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
def manager(temp_storage, monkeypatch):
    """Create PersonaManager with temp storage."""
    # Patch get_settings to use temp storage
    from ragged.config.settings import Settings

    def mock_get_settings():
        settings = Settings()
        settings.data_dir = str(temp_storage)
        return settings

    monkeypatch.setattr("ragged.memory.persona.get_settings", mock_get_settings)
    monkeypatch.setattr("ragged.memory.interactions.get_settings", mock_get_settings)
    return PersonaManager()


@pytest.fixture
def tracker_with_data(manager, runner):
    """Create tracker with sample data."""
    # Create persona first
    runner.invoke(persona, ["create", "researcher"])
    runner.invoke(persona, ["switch", "researcher"])

    # Create tracker and add interactions
    tracker = InteractionTracker(persona="researcher")

    # Add sample interactions
    tracker.record_interaction(
        query="What is RAG?",
        response="Retrieval-Augmented Generation...",
        model_used="llama3",
        latency_ms=150.5,
    )
    tracker.record_interaction(
        query="How does embeddings work?",
        response="Embeddings are...",
        model_used="llama3",
        latency_ms=120.0,
    )
    tracker.record_interaction(
        query="Explain vector databases",
        response="Vector databases...",
        model_used="mistral",
        latency_ms=200.0,
    )

    return tracker


class TestMemoryList:
    """Test memory list command."""

    def test_list_empty_interactions(self, runner, manager):
        """Test listing when no interactions exist."""
        result = runner.invoke(memory, ["list"])

        assert result.exit_code == 0
        assert "No interactions found" in result.output

    def test_list_interactions(self, runner, manager, tracker_with_data):
        """Test listing interactions."""
        result = runner.invoke(memory, ["list", "--persona", "researcher"])

        assert result.exit_code == 0
        assert "What is RAG?" in result.output
        assert "How does embeddings work?" in result.output

    def test_list_with_limit(self, runner, manager, tracker_with_data):
        """Test listing with limit."""
        result = runner.invoke(memory, ["list", "--persona", "researcher", "--limit", "2"])

        assert result.exit_code == 0
        # Should show max 2 interactions
        assert "showing 2 of 2" in result.output

    def test_list_json_format(self, runner, manager, tracker_with_data):
        """Test listing in JSON format."""
        result = runner.invoke(
            memory, ["list", "--persona", "researcher", "--format", "json"]
        )

        assert result.exit_code == 0
        # Check for JSON-like output
        assert "researcher" in result.output


class TestMemoryShow:
    """Test memory show command."""

    def test_show_interaction(self, runner, manager, tracker_with_data):
        """Test showing interaction details."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Show interaction
        result = runner.invoke(memory, ["show", interaction_id])

        assert result.exit_code == 0
        assert "Interaction Details" in result.output
        assert interaction_id in result.output

    def test_show_nonexistent_interaction(self, runner, manager):
        """Test showing nonexistent interaction fails."""
        result = runner.invoke(memory, ["show", "nonexistent-id"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_show_json_format(self, runner, manager, tracker_with_data):
        """Test showing interaction in JSON format."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Show as JSON
        result = runner.invoke(memory, ["show", interaction_id, "--format", "json"])

        assert result.exit_code == 0


class TestMemoryDelete:
    """Test memory delete command."""

    def test_delete_with_confirmation(self, runner, manager, tracker_with_data):
        """Test deleting interaction with --yes flag."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Delete with confirmation
        result = runner.invoke(memory, ["delete", interaction_id, "--yes"])

        assert result.exit_code == 0
        assert "✓ Deleted interaction" in result.output

    def test_delete_nonexistent_interaction(self, runner, manager):
        """Test deleting nonexistent interaction fails."""
        result = runner.invoke(memory, ["delete", "nonexistent-id", "--yes"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_without_confirmation(self, runner, manager, tracker_with_data):
        """Test delete prompts for confirmation without --yes."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Try to delete without --yes (will prompt)
        result = runner.invoke(memory, ["delete", interaction_id], input="n\n")

        # Should be cancelled
        assert result.exit_code == 0
        assert "Cancelled" in result.output


class TestMemoryExport:
    """Test memory export command."""

    def test_export_interactions(self, runner, manager, tracker_with_data, temp_storage):
        """Test exporting interactions to JSON."""
        output_file = temp_storage / "export.json"

        result = runner.invoke(
            memory, ["export", str(output_file), "--persona", "researcher"]
        )

        assert result.exit_code == 0
        assert "✓ Exported 3 interactions" in result.output
        assert output_file.exists()

        # Verify JSON content
        with open(output_file) as f:
            data = json.load(f)
        assert data["interaction_count"] == 3
        assert data["persona"] == "researcher"

    def test_export_empty_persona(self, runner, manager, temp_storage):
        """Test exporting when no interactions exist."""
        output_file = temp_storage / "export.json"

        # Create persona without interactions
        runner.invoke(persona, ["create", "empty-persona"])

        result = runner.invoke(
            memory, ["export", str(output_file), "--persona", "empty-persona"]
        )

        assert result.exit_code == 0
        assert "✓ Exported 0 interactions" in result.output


class TestMemoryClear:
    """Test memory clear command."""

    def test_clear_with_confirmation(self, runner, manager, tracker_with_data):
        """Test clearing interactions with --yes flag."""
        result = runner.invoke(memory, ["clear", "--persona", "researcher", "--yes"])

        assert result.exit_code == 0
        assert "✓ Deleted 3 interaction(s)" in result.output

        # Verify cleared
        list_result = runner.invoke(memory, ["list", "--persona", "researcher"])
        assert "No interactions found" in list_result.output

    def test_clear_without_persona(self, runner, manager):
        """Test clearing without persona fails."""
        result = runner.invoke(memory, ["clear", "--yes"])

        assert result.exit_code == 1
        assert "No persona specified" in result.output

    def test_clear_without_confirmation(self, runner, manager, tracker_with_data):
        """Test clear prompts for confirmation without --yes."""
        result = runner.invoke(
            memory, ["clear", "--persona", "researcher"], input="n\n"
        )

        # Should be cancelled
        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify not cleared
        list_result = runner.invoke(memory, ["list", "--persona", "researcher"])
        assert "What is RAG?" in list_result.output

    def test_clear_empty_persona(self, runner, manager):
        """Test clearing when no interactions exist."""
        # Create persona without interactions
        runner.invoke(persona, ["create", "empty-persona"])

        result = runner.invoke(memory, ["clear", "--persona", "empty-persona", "--yes"])

        assert result.exit_code == 0
        assert "No interactions found" in result.output


class TestMemoryFeedback:
    """Test memory feedback command."""

    def test_add_positive_feedback(self, runner, manager, tracker_with_data):
        """Test adding positive feedback."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Add feedback
        result = runner.invoke(memory, ["feedback", interaction_id, "positive"])

        assert result.exit_code == 0
        assert "✓ Added positive feedback" in result.output

    def test_add_negative_feedback(self, runner, manager, tracker_with_data):
        """Test adding negative feedback."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Add feedback
        result = runner.invoke(memory, ["feedback", interaction_id, "negative"])

        assert result.exit_code == 0
        assert "✓ Added negative feedback" in result.output

    def test_add_neutral_feedback(self, runner, manager, tracker_with_data):
        """Test adding neutral feedback."""
        # Get interaction ID
        interactions = tracker_with_data.list_interactions(limit=1)
        interaction_id = interactions[0].id

        # Add feedback
        result = runner.invoke(memory, ["feedback", interaction_id, "neutral"])

        assert result.exit_code == 0
        assert "✓ Added neutral feedback" in result.output

    def test_add_feedback_to_nonexistent(self, runner, manager):
        """Test adding feedback to nonexistent interaction fails."""
        result = runner.invoke(memory, ["feedback", "nonexistent-id", "positive"])

        assert result.exit_code == 1
        assert "not found" in result.output


class TestMemoryStats:
    """Test memory stats command."""

    def test_stats_with_data(self, runner, manager, tracker_with_data):
        """Test showing memory statistics."""
        result = runner.invoke(memory, ["stats", "--persona", "researcher"])

        assert result.exit_code == 0
        assert "Memory Statistics" in result.output
        assert "Total Interactions: 3" in result.output
        assert "llama3" in result.output or "mistral" in result.output

    def test_stats_empty_persona(self, runner, manager):
        """Test stats when no interactions exist."""
        # Create persona without interactions
        runner.invoke(persona, ["create", "empty-persona"])

        result = runner.invoke(memory, ["stats", "--persona", "empty-persona"])

        assert result.exit_code == 0
        assert "No interactions found" in result.output

    def test_stats_json_format(self, runner, manager, tracker_with_data):
        """Test stats in JSON format."""
        result = runner.invoke(
            memory, ["stats", "--persona", "researcher", "--format", "json"]
        )

        assert result.exit_code == 0


class TestMemoryIntegration:
    """Integration tests for memory commands."""

    def test_full_memory_workflow(self, runner, manager, temp_storage):
        """Test complete memory workflow."""
        # Create persona
        runner.invoke(persona, ["create", "researcher"])
        runner.invoke(persona, ["switch", "researcher"])

        # Create tracker and add interactions
        tracker = InteractionTracker(persona="researcher")
        interaction = tracker.record_interaction(
            query="Test query",
            response="Test response",
            model_used="llama3",
            latency_ms=100.0,
        )

        # List interactions
        list_result = runner.invoke(memory, ["list", "--persona", "researcher"])
        assert "Test query" in list_result.output

        # Show interaction
        show_result = runner.invoke(memory, ["show", interaction.id])
        assert "Test query" in show_result.output

        # Add feedback
        feedback_result = runner.invoke(
            memory, ["feedback", interaction.id, "positive"]
        )
        assert feedback_result.exit_code == 0

        # Export interactions
        export_file = temp_storage / "export.json"
        export_result = runner.invoke(
            memory, ["export", str(export_file), "--persona", "researcher"]
        )
        assert export_result.exit_code == 0
        assert export_file.exists()

        # Stats
        stats_result = runner.invoke(memory, ["stats", "--persona", "researcher"])
        assert "Total Interactions: 1" in stats_result.output

        # Clear interactions
        clear_result = runner.invoke(
            memory, ["clear", "--persona", "researcher", "--yes"]
        )
        assert clear_result.exit_code == 0

        # Verify cleared
        list_final = runner.invoke(memory, ["list", "--persona", "researcher"])
        assert "No interactions found" in list_final.output
