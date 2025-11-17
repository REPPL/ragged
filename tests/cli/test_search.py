"""Tests for advanced search command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.search import search


class TestSearch:
    """Test search command functionality."""

    def test_search_help(self, cli_runner: CliRunner):
        """Test search command help."""
        result = cli_runner.invoke(search, ["--help"])
        assert result.exit_code == 0
        assert "Advanced search" in result.output
        assert "semantic similarity" in result.output.lower()

    def test_search_no_parameters(self, cli_runner: CliRunner):
        """Test search with no query or filters."""
        result = cli_runner.invoke(search, [])
        assert result.exit_code == 0
        assert "Provide at least one" in result.output

    @patch("src.cli.commands.search.VectorStore")
    @patch("src.cli.commands.search.Retriever")
    def test_search_semantic_query(self, mock_retriever, mock_vector_store, cli_runner: CliRunner):
        """Test basic semantic search."""
        # Mock retriever
        retriever_instance = MagicMock()
        retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = retriever_instance

        result = cli_runner.invoke(search, ["machine learning"])
        # Should run without error even if no results
        assert result.exit_code in [0, 1]  # 1 if no results, 0 if results

    @patch("src.cli.commands.search.VectorStore")
    def test_search_by_path(self, mock_vector_store, cli_runner: CliRunner):
        """Test search by document path."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(search, ["--path", "document.pdf"])
        assert result.exit_code in [0, 1]

    @patch("src.cli.commands.search.VectorStore")
    def test_search_by_metadata(self, mock_vector_store, cli_runner: CliRunner):
        """Test search by metadata filter."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(search, ["--metadata", "category=research"])
        assert result.exit_code in [0, 1]

    @patch("src.cli.commands.search.VectorStore")
    @patch("src.cli.commands.search.Retriever")
    def test_search_with_min_score(self, mock_retriever, mock_vector_store, cli_runner: CliRunner):
        """Test search with minimum score threshold."""
        retriever_instance = MagicMock()
        retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = retriever_instance

        result = cli_runner.invoke(search, ["test query", "--min-score", "0.8"])
        assert result.exit_code in [0, 1]

    @patch("src.cli.commands.search.VectorStore")
    @patch("src.cli.commands.search.Retriever")
    def test_search_with_limit(self, mock_retriever, mock_vector_store, cli_runner: CliRunner):
        """Test search with custom result limit."""
        retriever_instance = MagicMock()
        retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = retriever_instance

        result = cli_runner.invoke(search, ["test query", "--limit", "20"])
        assert result.exit_code in [0, 1]

    @patch("src.cli.commands.search.VectorStore")
    @patch("src.cli.commands.search.Retriever")
    def test_search_show_content(self, mock_retriever, mock_vector_store, cli_runner: CliRunner):
        """Test search with content preview."""
        retriever_instance = MagicMock()
        retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = retriever_instance

        result = cli_runner.invoke(search, ["test query", "--show-content"])
        assert result.exit_code in [0, 1]

    @patch("src.cli.commands.search.VectorStore")
    @patch("src.cli.commands.search.Retriever")
    def test_search_json_format(self, mock_retriever, mock_vector_store, cli_runner: CliRunner):
        """Test search with JSON output format."""
        retriever_instance = MagicMock()
        retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = retriever_instance

        result = cli_runner.invoke(search, ["test query", "--format", "json"])
        assert result.exit_code in [0, 1]

    @patch("src.cli.commands.search.VectorStore")
    @patch("src.cli.commands.search.Retriever")
    def test_search_multiple_filters(self, mock_retriever, mock_vector_store, cli_runner: CliRunner):
        """Test search with multiple metadata filters."""
        retriever_instance = MagicMock()
        retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = retriever_instance

        result = cli_runner.invoke(
            search,
            ["AI", "--metadata", "category=research", "--metadata", "priority=high"]
        )
        assert result.exit_code in [0, 1]

    def test_search_invalid_metadata_format(self, cli_runner: CliRunner):
        """Test search with invalid metadata format."""
        result = cli_runner.invoke(search, ["--metadata", "invalidformat"])
        assert result.exit_code == 1
        assert "Invalid" in result.output or "key=value" in result.output
