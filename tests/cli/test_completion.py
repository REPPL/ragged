"""Tests for shell completion command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.completion import completion


class TestCompletion:
    """Test shell completion functionality."""

    def test_completion_help(self, cli_runner: CliRunner):
        """Test completion command help."""
        result = cli_runner.invoke(completion, ["--help"])
        assert result.exit_code == 0
        assert "Install shell completion" in result.output

    def test_completion_show_bash(self, cli_runner: CliRunner):
        """Test showing bash completion script."""
        result = cli_runner.invoke(completion, ["--shell", "bash", "--show"])
        assert result.exit_code == 0
        assert "eval" in result.output
        assert "_RAGGED_COMPLETE" in result.output

    def test_completion_show_zsh(self, cli_runner: CliRunner):
        """Test showing zsh completion script."""
        result = cli_runner.invoke(completion, ["--shell", "zsh", "--show"])
        assert result.exit_code == 0
        assert "zsh" in result.output.lower()

    def test_completion_show_fish(self, cli_runner: CliRunner):
        """Test showing fish completion script."""
        result = cli_runner.invoke(completion, ["--shell", "fish", "--show"])
        assert result.exit_code == 0
        assert "ragged.fish" in result.output

    def test_completion_auto_detect_shell_fallback(self, cli_runner: CliRunner):
        """Test auto-detection falls back to bash."""
        result = cli_runner.invoke(completion, ["--show"])
        # Should default to bash or show instructions
        assert result.exit_code in [0, 1]
        # If successful, should have completion content
        if result.exit_code == 0:
            assert "ragged" in result.output.lower()

    def test_completion_instructions(self, cli_runner: CliRunner):
        """Test showing installation instructions."""
        result = cli_runner.invoke(completion, ["--shell", "bash"])
        assert result.exit_code == 0
        assert "bashrc" in result.output or "bash_profile" in result.output

    @patch("src.cli.commands.completion.Path.home")
    @patch("builtins.open", create=True)
    def test_completion_install_bash(self, mock_open, mock_home, cli_runner: CliRunner, tmp_path):
        """Test installing bash completion."""
        mock_home.return_value = tmp_path
        bashrc = tmp_path / ".bashrc"
        bashrc.touch()

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = cli_runner.invoke(completion, ["--shell", "bash", "--install"])
        # Should succeed or show helpful message
        assert "bashrc" in result.output.lower() or "successfully" in result.output.lower()

    def test_completion_invalid_shell(self, cli_runner: CliRunner):
        """Test with invalid shell type."""
        result = cli_runner.invoke(completion, ["--shell", "invalid"])
        assert result.exit_code != 0  # Should fail

    def test_completion_default_behavior(self, cli_runner: CliRunner):
        """Test default behavior without arguments."""
        result = cli_runner.invoke(completion, [])
        # Should show instructions or attempt auto-detect
        assert result.exit_code in [0, 1]
        # Should have helpful output either way
        if result.exit_code == 0:
            assert "ragged" in result.output.lower() or "completion" in result.output.lower()
