"""Tests for query history commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.history import history, QueryHistory


class TestQueryHistoryClass:
    """Test QueryHistory class functionality."""

    def test_query_history_init(self, tmp_path):
        """Test QueryHistory initialization."""
        history_file = tmp_path / "history.json"
        qh = QueryHistory(history_file)
        assert qh.history_file == history_file
        assert history_file.exists()

    def test_add_query(self, tmp_path):
        """Test adding a query to history."""
        history_file = tmp_path / "history.json"
        qh = QueryHistory(history_file)
        qh.add_query("What is ML?", top_k=5, answer="Machine Learning", sources=["doc1.pdf"])

        history = qh.get_history()
        assert len(history) == 1
        assert history[0]["query"] == "What is ML?"
        assert history[0]["answer"] == "Machine Learning"

    def test_get_history_with_limit(self, tmp_path):
        """Test getting history with limit."""
        history_file = tmp_path / "history.json"
        qh = QueryHistory(history_file)

        for i in range(10):
            qh.add_query(f"Query {i}")

        history = qh.get_history(limit=5)
        assert len(history) == 5

    def test_get_history_with_search(self, tmp_path):
        """Test searching history."""
        history_file = tmp_path / "history.json"
        qh = QueryHistory(history_file)

        qh.add_query("What is ML?", answer="Machine Learning")
        qh.add_query("What is AI?", answer="Artificial Intelligence")

        history = qh.get_history(search="ML")
        assert len(history) == 1
        assert "ML" in history[0]["query"]

    def test_get_query_by_id(self, tmp_path):
        """Test getting specific query by ID."""
        history_file = tmp_path / "history.json"
        qh = QueryHistory(history_file)

        qh.add_query("Test query")
        query = qh.get_query_by_id(1)

        assert query is not None
        assert query["query"] == "Test query"

    def test_clear_history(self, tmp_path):
        """Test clearing history."""
        history_file = tmp_path / "history.json"
        qh = QueryHistory(history_file)

        qh.add_query("Query 1")
        qh.add_query("Query 2")
        count = qh.clear_history()

        assert count == 2
        assert len(qh.get_history()) == 0

    def test_export_history(self, tmp_path):
        """Test exporting history."""
        history_file = tmp_path / "history.json"
        export_file = tmp_path / "export.json"
        qh = QueryHistory(history_file)

        qh.add_query("Test query")
        count = qh.export_history(export_file)

        assert count == 1
        assert export_file.exists()


class TestHistoryList:
    """Test history list command."""

    def test_history_list_help(self, cli_runner: CliRunner):
        """Test history list help."""
        result = cli_runner.invoke(history, ["list", "--help"])
        assert result.exit_code == 0
        assert "List query history" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_list_empty(self, mock_history, cli_runner: CliRunner):
        """Test listing empty history."""
        history_instance = MagicMock()
        history_instance.get_history.return_value = []
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["list"])
        assert result.exit_code == 0
        assert "No query history found" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_list_with_entries(self, mock_history, cli_runner: CliRunner):
        """Test listing history with entries."""
        history_instance = MagicMock()
        history_instance.get_history.return_value = [
            {"id": 1, "timestamp": "2025-01-01T12:00:00", "query": "Test query", "top_k": 5, "sources": []},
        ]
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["list"])
        assert result.exit_code == 0
        assert "Test query" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_list_with_limit(self, mock_history, cli_runner: CliRunner):
        """Test listing history with limit."""
        history_instance = MagicMock()
        history_instance.get_history.return_value = []
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["list", "--limit", "10"])
        assert result.exit_code == 0

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_list_with_search(self, mock_history, cli_runner: CliRunner):
        """Test listing history with search."""
        history_instance = MagicMock()
        history_instance.get_history.return_value = []
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["list", "--search", "ML"])
        assert result.exit_code == 0

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_list_json_format(self, mock_history, cli_runner: CliRunner):
        """Test listing history in JSON format."""
        history_instance = MagicMock()
        history_instance.get_history.return_value = [
            {"id": 1, "timestamp": "2025-01-01T12:00:00", "query": "Test", "top_k": 5, "sources": []},
        ]
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["list", "--format", "json"])
        assert result.exit_code == 0


class TestHistoryShow:
    """Test history show command."""

    def test_history_show_help(self, cli_runner: CliRunner):
        """Test history show help."""
        result = cli_runner.invoke(history, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show full details" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_show_not_found(self, mock_history, cli_runner: CliRunner):
        """Test showing non-existent query."""
        history_instance = MagicMock()
        history_instance.get_query_by_id.return_value = None
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["show", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_show_found(self, mock_history, cli_runner: CliRunner):
        """Test showing existing query."""
        history_instance = MagicMock()
        history_instance.get_query_by_id.return_value = {
            "id": 1,
            "timestamp": "2025-01-01T12:00:00",
            "query": "Test query",
            "top_k": 5,
            "answer": "Test answer",
            "sources": ["doc1.pdf"],
        }
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["show", "1"])
        assert result.exit_code == 0
        assert "Test query" in result.output


class TestHistoryClear:
    """Test history clear command."""

    def test_history_clear_help(self, cli_runner: CliRunner):
        """Test history clear help."""
        result = cli_runner.invoke(history, ["clear", "--help"])
        assert result.exit_code == 0
        assert "Clear all query history" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_clear_with_confirmation(self, mock_history, cli_runner: CliRunner):
        """Test clearing history with confirmation."""
        history_instance = MagicMock()
        history_instance.get_history.return_value = [{"query": "test", "timestamp": "2025-01-01"}]
        history_instance.clear_history.return_value = 1
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["clear"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output or "Abort" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_clear_with_yes_flag(self, mock_history, cli_runner: CliRunner):
        """Test clearing history with --yes flag."""
        history_instance = MagicMock()
        history_instance.clear_history.return_value = 5
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["clear", "--yes"])
        assert result.exit_code == 0
        assert "Cleared 5" in result.output


class TestHistoryExport:
    """Test history export command."""

    def test_history_export_help(self, cli_runner: CliRunner):
        """Test history export help."""
        result = cli_runner.invoke(history, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export query history" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_export_success(self, mock_history, cli_runner: CliRunner, tmp_path):
        """Test exporting history successfully."""
        export_file = tmp_path / "export.json"
        history_instance = MagicMock()
        history_instance.export_history.return_value = 10
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["export", str(export_file)])
        assert result.exit_code == 0
        assert "Exported 10" in result.output


class TestHistoryReplay:
    """Test history replay command."""

    def test_history_replay_help(self, cli_runner: CliRunner):
        """Test history replay help."""
        result = cli_runner.invoke(history, ["replay", "--help"])
        assert result.exit_code == 0
        assert "Replay a query" in result.output

    @patch("src.cli.commands.history.QueryHistory")
    def test_history_replay_not_found(self, mock_history, cli_runner: CliRunner):
        """Test replaying non-existent query."""
        history_instance = MagicMock()
        history_instance.get_query_by_id.return_value = None
        mock_history.return_value = history_instance

        result = cli_runner.invoke(history, ["replay", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()
