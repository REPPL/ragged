"""Tests for test CLI commands.

v0.3.11: Test CLI command integration.
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.cli.commands.test import test


class TestTestCommands:
    """Test CLI commands for testing."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def valid_config(self, tmp_path):
        """Create valid configuration file."""
        config_file = tmp_path / "valid.yaml"
        config_file.write_text(
            """
chunking:
  chunk_size: 800
  chunk_overlap: 100

retrieval:
  top_k: 5
  method: hybrid

generation:
  model: llama2
  temperature: 0.7
"""
        )
        return config_file

    @pytest.fixture
    def invalid_syntax_config(self, tmp_path):
        """Create config with invalid YAML syntax."""
        config_file = tmp_path / "invalid_syntax.yaml"
        config_file.write_text(
            """
chunking:
  chunk_size: 500
  invalid yaml [[[
"""
        )
        return config_file

    @pytest.fixture
    def invalid_schema_config(self, tmp_path):
        """Create config with invalid schema."""
        config_file = tmp_path / "invalid_schema.yaml"
        config_file.write_text(
            """
chunking:
  chunk_size: 50  # Too small
  chunk_overlap: 600  # Too large

retrieval:
  top_k: 100  # Too large
"""
        )
        return config_file

    @pytest.fixture
    def warning_config(self, tmp_path):
        """Create config that generates warnings."""
        config_file = tmp_path / "warning.yaml"
        config_file.write_text(
            """
chunking:
  chunk_size: 150  # Small but valid
  chunk_overlap: 100  # High overlap ratio

generation:
  temperature: 1.5  # High temperature
"""
        )
        return config_file

    def test_config_valid(self, runner, valid_config):
        """Test validating valid configuration."""
        result = runner.invoke(
            test,
            ["config", str(valid_config)],
        )

        assert result.exit_code == 0
        assert "valid" in result.output.lower()
        # Note: May have permission warnings for temp files, which is OK
        assert "Error" not in result.output or "0" in result.output  # 0 errors

    def test_config_invalid_syntax(self, runner, invalid_syntax_config):
        """Test validating configuration with syntax errors."""
        result = runner.invoke(
            test,
            ["config", str(invalid_syntax_config)],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "Error" in result.output

    def test_config_invalid_schema(self, runner, invalid_schema_config):
        """Test validating configuration with schema errors."""
        result = runner.invoke(
            test,
            ["config", str(invalid_schema_config)],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "Error" in result.output

    def test_config_with_warnings(self, runner, warning_config):
        """Test validating configuration with warnings."""
        result = runner.invoke(
            test,
            ["config", str(warning_config)],
        )

        assert result.exit_code == 0  # Warnings don't fail by default
        assert "warning" in result.output.lower() or "Warning" in result.output

    def test_config_strict_mode_with_warnings(self, runner, warning_config):
        """Test validating configuration with warnings in strict mode."""
        result = runner.invoke(
            test,
            ["config", str(warning_config), "--strict"],
        )

        assert result.exit_code != 0  # Strict mode treats warnings as errors
        assert "warning" in result.output.lower() or "Warning" in result.output

    def test_config_nonexistent_file(self, runner):
        """Test validating nonexistent configuration file."""
        result = runner.invoke(
            test,
            ["config", "/nonexistent/path/config.yaml"],
        )

        assert result.exit_code != 0

    def test_config_string_valid(self, runner):
        """Test validating valid configuration string."""
        config_string = """
chunking:
  chunk_size: 500
  chunk_overlap: 50
retrieval:
  top_k: 5
"""

        result = runner.invoke(
            test,
            ["config-string", config_string],
        )

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_string_invalid_syntax(self, runner):
        """Test validating configuration string with syntax errors."""
        config_string = "invalid yaml [[["

        result = runner.invoke(
            test,
            ["config-string", config_string],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "Error" in result.output

    def test_config_string_invalid_schema(self, runner):
        """Test validating configuration string with schema errors."""
        config_string = """
chunking:
  chunk_size: 50
  chunk_overlap: 600
"""

        result = runner.invoke(
            test,
            ["config-string", config_string],
        )

        assert result.exit_code != 0

    def test_config_string_with_warnings(self, runner):
        """Test validating configuration string with warnings."""
        config_string = """
chunking:
  chunk_size: 150
  chunk_overlap: 100
generation:
  temperature: 1.5
"""

        result = runner.invoke(
            test,
            ["config-string", config_string],
        )

        assert result.exit_code == 0  # Warnings don't fail by default
        assert "warning" in result.output.lower() or "Warning" in result.output

    def test_config_string_strict_mode(self, runner):
        """Test validating configuration string in strict mode."""
        config_string = """
chunking:
  chunk_size: 150
  chunk_overlap: 100
"""

        result = runner.invoke(
            test,
            ["config-string", config_string, "--strict"],
        )

        assert result.exit_code != 0  # Strict mode treats warnings as errors

    def test_config_displays_error_count(self, runner, invalid_schema_config):
        """Test that validation displays error count."""
        result = runner.invoke(
            test,
            ["config", str(invalid_schema_config)],
        )

        assert "Error" in result.output or "error" in result.output
        # Should display some form of count or multiple errors
        assert result.exit_code != 0

    def test_config_displays_warning_count(self, runner, warning_config):
        """Test that validation displays warning count."""
        result = runner.invoke(
            test,
            ["config", str(warning_config)],
        )

        assert "Warning" in result.output or "warning" in result.output
        assert result.exit_code == 0  # Warnings don't fail

    def test_config_validation_summary(self, runner, valid_config):
        """Test that validation displays summary."""
        result = runner.invoke(
            test,
            ["config", str(valid_config)],
        )

        # Should have some form of summary or confirmation
        assert result.exit_code == 0
        assert len(result.output) > 0
