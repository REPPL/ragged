"""Tests for cache management commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.cache import cache


class TestCacheInfo:
    """Test cache info command."""

    def test_cache_info_help(self, cli_runner: CliRunner):
        """Test cache info help."""
        result = cli_runner.invoke(cache, ["info", "--help"])
        assert result.exit_code == 0
        assert "Show cache information" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_info_display(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test displaying cache information."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["info"])
        assert result.exit_code == 0
        assert "Cache Information" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_info_json_format(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test cache info in JSON format."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["info", "--format", "json"])
        assert result.exit_code == 0


class TestCacheClear:
    """Test cache clear command."""

    def test_cache_clear_help(self, cli_runner: CliRunner):
        """Test cache clear help."""
        result = cli_runner.invoke(cache, ["clear", "--help"])
        assert result.exit_code == 0
        assert "Clear caches" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_clear_no_cache(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test clearing when no cache exists."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["clear", "--type", "history", "--yes"])
        assert result.exit_code == 0
        assert "No" in result.output or "cache" in result.output.lower()

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_clear_with_yes_flag(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test clearing cache with --yes flag."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        # Create a dummy cache file
        (tmp_path / "query_history.json").write_text("{}")

        result = cli_runner.invoke(cache, ["clear", "--type", "history", "--yes"])
        assert result.exit_code == 0

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_clear_all_types(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test clearing all cache types."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["clear", "--type", "all", "--yes"])
        assert result.exit_code == 0


class TestCacheClean:
    """Test cache clean command."""

    def test_cache_clean_help(self, cli_runner: CliRunner):
        """Test cache clean help."""
        result = cli_runner.invoke(cache, ["clean", "--help"])
        assert result.exit_code == 0
        assert "Clean old cache files" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_clean_dry_run(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test cache clean in dry-run mode."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["clean", "--older-than", "7", "--dry-run"])
        assert result.exit_code == 0
        # Should mention dry run or no files
        assert "DRY RUN" in result.output or "No files" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_clean_with_threshold(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test cache clean with age threshold."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["clean", "--older-than", "30", "--dry-run"])
        assert result.exit_code == 0


class TestCacheStats:
    """Test cache stats command."""

    def test_cache_stats_help(self, cli_runner: CliRunner):
        """Test cache stats help."""
        result = cli_runner.invoke(cache, ["stats", "--help"])
        assert result.exit_code == 0
        assert "Show cache statistics" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_stats_display(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test displaying cache statistics."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["stats"])
        assert result.exit_code == 0
        assert "Cache Statistics" in result.output

    @patch("src.cli.commands.cache.get_settings")
    def test_cache_stats_json_format(self, mock_settings, cli_runner: CliRunner, tmp_path):
        """Test cache stats in JSON format."""
        settings = MagicMock()
        settings.data_dir = str(tmp_path)
        mock_settings.return_value = settings

        result = cli_runner.invoke(cache, ["stats", "--format", "json"])
        assert result.exit_code == 0
