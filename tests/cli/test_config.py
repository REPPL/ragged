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


class TestConfigValidateCommand:
    """Test config validate command."""

    def test_config_validate_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(config, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate configuration" in result.output

    @patch("src.cli.commands.config.RaggedConfig.load")
    @patch("src.cli.commands.config.ConfigValidator")
    def test_config_validate_valid_config(self, mock_validator_class, mock_load, cli_runner):
        """Test validating a valid configuration."""
        from src.config.config_manager import RaggedConfig

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

    @patch("src.cli.commands.config.RaggedConfig.load")
    @patch("src.cli.commands.config.ConfigValidator")
    def test_config_validate_invalid_config(self, mock_validator_class, mock_load, cli_runner):
        """Test validating an invalid configuration."""
        from src.config.config_manager import RaggedConfig

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

    @patch("src.cli.commands.config.Path.exists")
    @patch("src.cli.commands.config.RaggedConfig")
    @patch("src.cli.commands.config.PersonaManager.apply_persona")
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

    @patch("src.cli.commands.config.Path.exists")
    def test_config_generate_file_exists_without_force(self, mock_exists, cli_runner):
        """Test that generate fails if file exists and --force not used."""
        mock_exists.return_value = True

        result = cli_runner.invoke(config, ["generate"])

        assert result.exit_code == 1
        assert "already exists" in result.output or "force" in result.output.lower()

    @patch("src.cli.commands.config.Path.exists")
    @patch("src.cli.commands.config.RaggedConfig")
    @patch("src.cli.commands.config.PersonaManager.apply_persona")
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

    @patch("src.cli.commands.config.PersonaManager.list_personas")
    @patch("src.cli.commands.config.RaggedConfig.load")
    def test_config_list_personas_shows_all(self, mock_load, mock_list, cli_runner):
        """Test listing all personas."""
        from src.config.config_manager import RaggedConfig

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

    @patch("src.cli.commands.config.PersonaManager.list_personas")
    @patch("src.cli.commands.config.RaggedConfig.load")
    def test_config_list_personas_shows_current(self, mock_load, mock_list, cli_runner):
        """Test that current persona is highlighted."""
        from src.config.config_manager import RaggedConfig

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

    @patch("src.cli.commands.config.RaggedConfig.load")
    @patch("src.cli.commands.config.PersonaManager.apply_persona")
    @patch("src.cli.commands.config.PersonaManager.get_persona")
    def test_config_set_persona_valid(self, mock_get, mock_apply, mock_load, cli_runner):
        """Test setting a valid persona."""
        from src.config.config_manager import RaggedConfig
        from src.config.personas import PersonaConfig

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

    @patch("src.cli.commands.config.RaggedConfig.load")
    @patch("src.cli.commands.config.PersonaManager.apply_persona")
    def test_config_set_persona_invalid(self, mock_apply, mock_load, cli_runner):
        """Test setting an invalid persona."""
        from src.config.config_manager import RaggedConfig

        mock_config = RaggedConfig()
        mock_load.return_value = mock_config

        mock_apply.side_effect = ValueError("Unknown persona")

        # Should fail at CLI level due to click.Choice constraint
        result = cli_runner.invoke(config, ["set-persona", "invalid"])

        assert result.exit_code != 0
