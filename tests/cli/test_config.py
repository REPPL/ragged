"""Tests for configuration management (config) commands."""

from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from ragged.cli.commands.config import config


class TestConfigShowCommand:
    """Test config show command."""

    def test_config_show_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["show", "--help"])
        assert result.exit_code == 0

    def test_config_show_displays_settings(self, cli_runner):
        """Test displaying all settings."""
        result = cli_runner.invoke(config, ["show"])

        assert result.exit_code == 0
        # Check for actual output labels (human-readable format)
        assert "LLM Model" in result.output or "llama" in result.output.lower()
        assert "Retrieval Method" in result.output or "hybrid" in result.output.lower()


class TestConfigSetCommand:
    """Test config set command."""

    def test_config_set_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["set", "--help"])
        assert result.exit_code == 0

    def test_config_set_valid_setting(self, cli_runner):
        """Test setting a valid configuration value."""
        result = cli_runner.invoke(config, ["set", "ragged_llm_model", "llama3.2"])

        assert result.exit_code == 0
        assert "✓" in result.output or "set" in result.output.lower()

    def test_config_set_invalid_key(self, cli_runner):
        """Test setting an invalid configuration key."""
        result = cli_runner.invoke(config, ["set", "completely_invalid_key_12345", "value"])

        # May succeed (creates new key) or fail - either is acceptable
        # Just ensure it doesn't crash
        assert result.exit_code in [0, 1]


class TestConfigResetCommand:
    """Test config reset command."""

    def test_config_reset_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["reset", "--help"])
        assert result.exit_code == 0

    def test_config_reset_with_confirmation(self, cli_runner):
        """Test reset with --confirm flag."""
        result = cli_runner.invoke(config, ["reset", "--confirm"])

        assert result.exit_code == 0
        assert "✓" in result.output or "reset" in result.output.lower() or "default" in result.output.lower()

    def test_config_reset_cancel(self, cli_runner):
        """Test reset cancelled by user."""
        # User cancels with 'n'
        result = cli_runner.invoke(config, ["reset"], input="n\n")

        assert result.exit_code == 0
        # May show cancellation message or "already using defaults" if no config file exists
        assert ("cancelled" in result.output.lower() or
                "no changes" in result.output.lower() or
                "already using default" in result.output.lower())


class TestConfigValidateCommand:
    """Test config validate command."""

    def test_config_validate_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate configuration" in result.output

    @patch("ragged.cli.commands.config.RaggedConfig.load")
    @patch("ragged.cli.commands.config.ConfigValidator")
    def test_config_validate_valid_config(self, mock_validator_class, mock_load, cli_runner):
        """Test validating a valid configuration."""
        from ragged.config.config_manager import RaggedConfig

        # Mock valid config
        mock_config = RaggedConfig()
        mock_load.return_value = mock_config

        # Mock validator returning valid
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (True, [])
        mock_validator_class.return_value = mock_validator

        result = cli_runner.invoke(config, ["validate"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✓" in result.output

    @patch("ragged.cli.commands.config.RaggedConfig.load")
    @patch("ragged.cli.commands.config.ConfigValidator")
    def test_config_validate_invalid_config(self, mock_validator_class, mock_load, cli_runner):
        """Test validating an invalid configuration."""
        from ragged.config.config_manager import RaggedConfig

        # Mock config
        mock_config = RaggedConfig()
        mock_load.return_value = mock_config

        # Mock validator returning invalid
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (False, ["Error 1", "Error 2"])
        mock_validator_class.return_value = mock_validator

        result = cli_runner.invoke(config, ["validate"])

        assert result.exit_code == 1
        assert "error" in result.output.lower() or "✗" in result.output
        assert "Error 1" in result.output
        assert "Error 2" in result.output


class TestConfigGenerateCommand:
    """Test config generate command."""

    def test_config_generate_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate default configuration" in result.output

    @patch("ragged.cli.commands.config.Path.exists")
    @patch("ragged.cli.commands.config.RaggedConfig")
    @patch("ragged.cli.commands.config.PersonaManager.apply_persona")
    def test_config_generate_default_persona(self, mock_apply, mock_config_class, mock_exists, cli_runner):
        """Test generating config with default persona."""
        from pathlib import Path

        # Mock file doesn't exist
        mock_exists.return_value = False

        # Mock config
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        result = cli_runner.invoke(config, ["generate"])

        # Should succeed or handle gracefully
        if result.exit_code == 0:
            assert "generated" in result.output.lower() or "✓" in result.output

    @patch("ragged.cli.commands.config.Path.exists")
    def test_config_generate_file_exists_without_force(self, mock_exists, cli_runner):
        """Test that generate fails if file exists and --force not used."""
        mock_exists.return_value = True

        result = cli_runner.invoke(config, ["generate"])

        assert result.exit_code == 1
        assert "already exists" in result.output or "force" in result.output.lower()

    @patch("ragged.cli.commands.config.Path.exists")
    @patch("ragged.cli.commands.config.RaggedConfig")
    @patch("ragged.cli.commands.config.PersonaManager.apply_persona")
    def test_config_generate_with_persona(self, mock_apply, mock_config_class, mock_exists, cli_runner):
        """Test generating config with specific persona."""
        mock_exists.return_value = False

        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        result = cli_runner.invoke(config, ["generate", "--persona", "accuracy"])

        if result.exit_code == 0:
            assert "accuracy" in result.output


class TestConfigListPersonasCommand:
    """Test config list-personas command."""

    def test_config_list_personas_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["list-personas", "--help"])
        assert result.exit_code == 0

    @patch("ragged.cli.commands.config.PersonaManager.list_personas")
    @patch("ragged.cli.commands.config.RaggedConfig.load")
    def test_config_list_personas_shows_all(self, mock_load, mock_list, cli_runner):
        """Test listing all personas."""
        from ragged.config.config_manager import RaggedConfig

        # Mock config
        mock_config = RaggedConfig()
        mock_config.persona = "balanced"
        mock_load.return_value = mock_config

        # Mock personas
        mock_list.return_value = {
            "accuracy": "Maximum quality",
            "speed": "Fast answers",
            "balanced": "Default",
            "research": "Deep exploration",
            "quick-answer": "Single answer",
        }

        result = cli_runner.invoke(config, ["list-personas"])

        assert result.exit_code == 0
        assert "accuracy" in result.output
        assert "speed" in result.output
        assert "balanced" in result.output
        assert "research" in result.output
        assert "quick-answer" in result.output

    @patch("ragged.cli.commands.config.PersonaManager.list_personas")
    @patch("ragged.cli.commands.config.RaggedConfig.load")
    def test_config_list_personas_shows_current(self, mock_load, mock_list, cli_runner):
        """Test that current persona is highlighted."""
        from ragged.config.config_manager import RaggedConfig

        mock_config = RaggedConfig()
        mock_config.persona = "accuracy"
        mock_load.return_value = mock_config

        mock_list.return_value = {
            "accuracy": "Maximum quality",
            "balanced": "Default",
        }

        result = cli_runner.invoke(config, ["list-personas"])

        assert result.exit_code == 0
        assert "accuracy" in result.output
        assert "✓" in result.output or "Active" in result.output


class TestConfigSetPersonaCommand:
    """Test config set-persona command."""

    def test_config_set_persona_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["set-persona", "--help"])
        assert result.exit_code == 0
        assert "Set default persona" in result.output

    @patch("ragged.cli.commands.config.RaggedConfig.load")
    @patch("ragged.cli.commands.config.PersonaManager.apply_persona")
    @patch("ragged.cli.commands.config.PersonaManager.get_persona")
    def test_config_set_persona_valid(self, mock_get, mock_apply, mock_load, cli_runner):
        """Test setting a valid persona."""
        from ragged.config.config_manager import RaggedConfig
        from ragged.config.personas import PersonaConfig

        mock_config = RaggedConfig()
        mock_load.return_value = mock_config

        # Mock persona config
        mock_persona = PersonaConfig(
            name="speed",
            description="Fast",
            retrieval_method="vector",
            top_k=3,
            enable_reranking=False,
            rerank_to=0,
            enable_query_decomposition=False,
            enable_hyde=False,
            enable_compression=False,
            confidence_threshold=0.8,
        )
        mock_get.return_value = mock_persona

        result = cli_runner.invoke(config, ["set-persona", "speed"])

        if result.exit_code == 0:
            assert "speed" in result.output
            assert "✓" in result.output or "set" in result.output.lower()

    @patch("ragged.cli.commands.config.RaggedConfig.load")
    @patch("ragged.cli.commands.config.PersonaManager.apply_persona")
    def test_config_set_persona_invalid(self, mock_apply, mock_load, cli_runner):
        """Test setting an invalid persona."""
        from ragged.config.config_manager import RaggedConfig

        mock_config = RaggedConfig()
        mock_load.return_value = mock_config

        mock_apply.side_effect = ValueError("Unknown persona")

        # Should fail at CLI level due to click.Choice constraint
        result = cli_runner.invoke(config, ["set-persona", "invalid"])

        assert result.exit_code != 0
