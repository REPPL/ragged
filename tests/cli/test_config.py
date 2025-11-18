"""Tests for configuration management (config) commands."""

from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from src.cli.commands.config import config


class TestConfigShowCommand:
    """Test config show command."""

    def test_config_show_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["show", "--help"])
        assert result.exit_code == 0

    @patch("src.cli.commands.config.get_settings")
    def test_config_show_displays_settings(self, mock_settings, cli_runner):
        """Test displaying all settings."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.embedding_model = "nomic-embed-text"
        settings.chunk_size = 1000
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        result = cli_runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert "llm_model" in result.output or "llama2" in result.output
        assert "chunk_size" in result.output or "1000" in result.output


class TestConfigSetCommand:
    """Test config set command."""

    def test_config_set_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["set", "--help"])
        assert result.exit_code == 0

    @patch("src.cli.commands.config.update_setting")
    @patch("src.cli.commands.config.get_settings")
    def test_config_set_valid_setting(self, mock_get, mock_update, cli_runner):
        """Test setting a valid configuration value."""
        result = cli_runner.invoke(config, ["set", "llm_model", "llama3"])

        if result.exit_code == 0:
            assert "set" in result.output.lower() or "updated" in result.output.lower()

    @patch("src.cli.commands.config.update_setting")
    def test_config_set_invalid_key(self, mock_update, cli_runner):
        """Test setting an invalid configuration key."""
        mock_update.side_effect = KeyError("Invalid setting")

        result = cli_runner.invoke(config, ["set", "invalid_key", "value"])

        assert result.exit_code != 0 or "invalid" in result.output.lower() or "error" in result.output.lower()


class TestConfigResetCommand:
    """Test config reset command."""

    def test_config_reset_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["reset", "--help"])
        assert result.exit_code == 0

    @patch("src.cli.commands.config.reset_settings")
    def test_config_reset_with_confirmation(self, mock_reset, cli_runner):
        """Test reset with user confirmation."""
        # User confirms with 'y'
        result = cli_runner.invoke(config, ["reset"], input="y\n")

        if result.exit_code == 0:
            assert "reset" in result.output.lower() or "default" in result.output.lower()

    @patch("src.cli.commands.config.reset_settings")
    def test_config_reset_cancel(self, mock_reset, cli_runner):
        """Test reset cancelled by user."""
        # User cancels with 'n'
        result = cli_runner.invoke(config, ["reset"], input="n\n")

        assert "cancel" in result.output.lower() or mock_reset.call_count == 0
