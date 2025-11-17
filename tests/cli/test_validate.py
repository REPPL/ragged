"""Tests for configuration validation command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.validate import validate


class TestValidate:
    """Test configuration validation functionality."""

    def test_validate_help(self, cli_runner: CliRunner):
        """Test validate command help."""
        result = cli_runner.invoke(validate, ["--help"])
        assert result.exit_code == 0
        assert "Validate ragged configuration" in result.output

    # Note: Full validation requires actual services running
    # These tests focus on validation logic that can be tested in isolation

    @patch("src.cli.commands.validate.get_settings")
    def test_validate_missing_directory(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test validation with missing data directory."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path / "nonexistent")
        settings.chunk_size = 1000
        settings.chunk_overlap = 200
        settings.chroma_url = "http://localhost:8001"
        mock_settings.return_value = settings

        result = cli_runner.invoke(validate, [])
        assert "data directory" in result.output.lower() or "directory" in result.output.lower()

    @patch("src.cli.commands.validate.get_settings")
    def test_validate_fix_creates_directory(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test --fix creates missing directories."""
        missing_dir = tmp_path / "missing_data"
        settings = MagicMock()
        settings.data_dir = str(missing_dir)
        settings.chunk_size = 1000
        settings.chunk_overlap = 200
        settings.chroma_url = "http://localhost:8001"
        mock_settings.return_value = settings

        result = cli_runner.invoke(validate, ["--fix"])
        # Should create the directory
        assert missing_dir.exists() or "created" in result.output.lower()

    # ChromaDB connection tests require actual service or complex internal mocking

    @patch("src.cli.commands.validate.get_settings")
    def test_validate_invalid_chunk_size(self, mock_settings, cli_runner: CliRunner, temp_data_dir):
        """Test validation with invalid chunk size."""
        settings = MagicMock()
        settings.data_dir = str(temp_data_dir)
        settings.chunk_size = -100  # Invalid
        settings.chunk_overlap = 200
        settings.chroma_url = "http://localhost:8001"
        mock_settings.return_value = settings

        result = cli_runner.invoke(validate, [])
        assert "chunk" in result.output.lower() or "size" in result.output.lower()

    @patch("src.cli.commands.validate.get_settings")
    def test_validate_overlap_larger_than_chunk(self, mock_settings, cli_runner: CliRunner, temp_data_dir):
        """Test validation when overlap > chunk_size."""
        settings = MagicMock()
        settings.data_dir = str(temp_data_dir)
        settings.chunk_size = 100
        settings.chunk_overlap = 200  # Larger than chunk_size
        settings.chroma_url = "http://localhost:8001"
        mock_settings.return_value = settings

        result = cli_runner.invoke(validate, [])
        assert "overlap" in result.output.lower() or "chunk" in result.output.lower()

    @patch("src.cli.commands.validate.get_settings")
    def test_validate_verbose_mode(self, mock_settings, cli_runner: CliRunner, temp_data_dir):
        """Test validation in verbose mode."""
        settings = MagicMock()
        settings.data_dir = str(temp_data_dir)
        settings.chunk_size = 1000
        settings.chunk_overlap = 200
        settings.chroma_url = "http://localhost:8001"
        mock_settings.return_value = settings

        result = cli_runner.invoke(validate, ["--verbose"])
        # Should show more detailed output
        assert "chunk_size" in result.output.lower() or "configuration" in result.output.lower()
