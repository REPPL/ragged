"""Tests for persona CLI commands.

v0.4.5: Test coverage for persona management CLI
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from ragged.cli.commands.persona import persona
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
    return PersonaManager()


class TestPersonaCreate:
    """Test persona create command."""

    def test_create_basic_persona(self, runner, manager):
        """Test creating basic persona."""
        result = runner.invoke(
            persona, ["create", "researcher", "--description", "ML researcher"]
        )

        assert result.exit_code == 0
        assert "✓ Created persona: researcher" in result.output
        assert "ML researcher" in result.output

    def test_create_with_focus(self, runner, manager):
        """Test creating persona with focus areas."""
        result = runner.invoke(
            persona,
            [
                "create",
                "researcher",
                "--focus",
                "RAG",
                "--focus",
                "NLP",
                "--description",
                "ML researcher",
            ],
        )

        assert result.exit_code == 0
        assert "✓ Created persona: researcher" in result.output
        assert "RAG, NLP" in result.output

    def test_create_with_projects(self, runner, manager):
        """Test creating persona with projects."""
        result = runner.invoke(
            persona,
            [
                "create",
                "researcher",
                "--project",
                "thesis",
                "--project",
                "paper",
            ],
        )

        assert result.exit_code == 0
        assert "✓ Created persona: researcher" in result.output
        assert "thesis, paper" in result.output

    def test_create_duplicate_persona(self, runner, manager):
        """Test creating duplicate persona fails."""
        # Create first persona
        result1 = runner.invoke(persona, ["create", "researcher"])
        assert result1.exit_code == 0

        # Try to create duplicate
        result2 = runner.invoke(persona, ["create", "researcher"])
        assert result2.exit_code == 1
        assert "already exists" in result2.output


class TestPersonaList:
    """Test persona list command."""

    def test_list_empty(self, runner, manager):
        """Test listing when no personas exist."""
        result = runner.invoke(persona, ["list"])

        assert result.exit_code == 0
        assert "No personas created yet" in result.output

    def test_list_single_persona(self, runner, manager):
        """Test listing single persona."""
        # Create persona
        runner.invoke(persona, ["create", "researcher", "--description", "ML researcher"])

        # List
        result = runner.invoke(persona, ["list"])

        assert result.exit_code == 0
        assert "researcher" in result.output
        assert "ML researcher" in result.output

    def test_list_multiple_personas(self, runner, manager):
        """Test listing multiple personas."""
        # Create personas
        runner.invoke(persona, ["create", "researcher"])
        runner.invoke(persona, ["create", "student"])
        runner.invoke(persona, ["create", "developer"])

        # List
        result = runner.invoke(persona, ["list"])

        assert result.exit_code == 0
        assert "researcher" in result.output
        assert "student" in result.output
        assert "developer" in result.output
        assert "Personas (3)" in result.output

    def test_list_json_format(self, runner, manager):
        """Test listing in JSON format."""
        # Create persona
        runner.invoke(persona, ["create", "researcher"])

        # List as JSON
        result = runner.invoke(persona, ["list", "--format", "json"])

        assert result.exit_code == 0
        assert '"name": "researcher"' in result.output or "researcher" in result.output


class TestPersonaSwitch:
    """Test persona switch command."""

    def test_switch_to_existing_persona(self, runner, manager):
        """Test switching to existing persona."""
        # Create persona
        runner.invoke(persona, ["create", "researcher"])

        # Switch
        result = runner.invoke(persona, ["switch", "researcher"])

        assert result.exit_code == 0
        assert "✓ Switched to persona: researcher" in result.output

    def test_switch_to_nonexistent_persona(self, runner, manager):
        """Test switching to nonexistent persona fails."""
        result = runner.invoke(persona, ["switch", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_switch_updates_usage(self, runner, manager):
        """Test switching updates usage count."""
        # Create and switch
        runner.invoke(persona, ["create", "researcher"])
        runner.invoke(persona, ["switch", "researcher"])

        # Switch again
        result = runner.invoke(persona, ["switch", "researcher"])

        assert result.exit_code == 0
        assert "#2 times" in result.output


class TestPersonaShow:
    """Test persona show command."""

    def test_show_existing_persona(self, runner, manager):
        """Test showing existing persona details."""
        # Create persona
        runner.invoke(
            persona,
            [
                "create",
                "researcher",
                "--description",
                "ML researcher",
                "--focus",
                "RAG",
            ],
        )

        # Show
        result = runner.invoke(persona, ["show", "researcher"])

        assert result.exit_code == 0
        assert "Persona: researcher" in result.output
        assert "ML researcher" in result.output
        assert "RAG" in result.output

    def test_show_nonexistent_persona(self, runner, manager):
        """Test showing nonexistent persona fails."""
        result = runner.invoke(persona, ["show", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_show_json_format(self, runner, manager):
        """Test showing persona in JSON format."""
        # Create persona
        runner.invoke(persona, ["create", "researcher"])

        # Show as JSON
        result = runner.invoke(persona, ["show", "researcher", "--format", "json"])

        assert result.exit_code == 0
        assert "researcher" in result.output


class TestPersonaDelete:
    """Test persona delete command."""

    def test_delete_with_confirmation(self, runner, manager):
        """Test deleting persona with --yes flag."""
        # Create persona
        runner.invoke(persona, ["create", "researcher"])

        # Delete with confirmation
        result = runner.invoke(persona, ["delete", "researcher", "--yes"])

        assert result.exit_code == 0
        assert "✓ Deleted persona: researcher" in result.output

    def test_delete_nonexistent_persona(self, runner, manager):
        """Test deleting nonexistent persona fails."""
        result = runner.invoke(persona, ["delete", "nonexistent", "--yes"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_without_confirmation(self, runner, manager):
        """Test delete prompts for confirmation without --yes."""
        # Create persona
        runner.invoke(persona, ["create", "researcher"])

        # Try to delete without --yes (will prompt)
        result = runner.invoke(persona, ["delete", "researcher"], input="n\n")

        # Should be cancelled
        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify persona still exists
        list_result = runner.invoke(persona, ["list"])
        assert "researcher" in list_result.output


class TestPersonaActive:
    """Test persona active command."""

    def test_active_when_none_set(self, runner, manager):
        """Test active command when no persona is active."""
        result = runner.invoke(persona, ["active"])

        assert result.exit_code == 0
        assert "No active persona set" in result.output

    def test_active_after_switch(self, runner, manager):
        """Test active command after switching persona."""
        # Create and switch
        runner.invoke(persona, ["create", "researcher", "--description", "ML researcher"])
        runner.invoke(persona, ["switch", "researcher"])

        # Check active
        result = runner.invoke(persona, ["active"])

        assert result.exit_code == 0
        assert "Active Persona: researcher" in result.output
        assert "ML researcher" in result.output


class TestPersonaIntegration:
    """Integration tests for persona commands."""

    def test_full_persona_workflow(self, runner, manager):
        """Test complete persona workflow."""
        # Create persona
        create_result = runner.invoke(
            persona,
            [
                "create",
                "researcher",
                "--description",
                "ML researcher",
                "--focus",
                "RAG",
                "--focus",
                "NLP",
            ],
        )
        assert create_result.exit_code == 0

        # List personas
        list_result = runner.invoke(persona, ["list"])
        assert "researcher" in list_result.output

        # Switch to persona
        switch_result = runner.invoke(persona, ["switch", "researcher"])
        assert switch_result.exit_code == 0

        # Show details
        show_result = runner.invoke(persona, ["show", "researcher"])
        assert "RAG, NLP" in show_result.output

        # Check active
        active_result = runner.invoke(persona, ["active"])
        assert "researcher" in active_result.output

        # Delete persona
        delete_result = runner.invoke(persona, ["delete", "researcher", "--yes"])
        assert delete_result.exit_code == 0

        # Verify deleted
        list_final = runner.invoke(persona, ["list"])
        assert "No personas created yet" in list_final.output
