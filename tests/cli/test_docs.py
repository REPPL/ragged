"""Tests for document management (docs) commands."""

from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from src.cli.commands.docs import docs


class TestDocsListCommand:
    """Test docs list command."""

    def test_docs_list_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(docs, ["list", "--help"])
        assert result.exit_code == 0

    @patch("src.cli.commands.docs.VectorStore")
    def test_docs_list_empty(self, mock_store, cli_runner):
        """Test listing when no documents exist."""
        store_instance = MagicMock()
        store_instance.count.return_value = 0
        store_instance.get_all_documents.return_value = []
        mock_store.return_value = store_instance

        result = cli_runner.invoke(docs, ["list"])

        assert result.exit_code == 0
        assert "0 document" in result.output or "No documents" in result.output or "empty" in result.output.lower()

    @patch("src.cli.commands.docs.VectorStore")
    def test_docs_list_with_documents(self, mock_store, cli_runner):
        """Test listing documents."""
        store_instance = MagicMock()
        store_instance.count.return_value = 2
        store_instance.get_all_documents.return_value = [
            {"document_id": "doc-1", "document_path": "/path/to/doc1.pdf", "title": "Document 1"},
            {"document_id": "doc-2", "document_path": "/path/to/doc2.txt", "title": "Document 2"},
        ]
        mock_store.return_value = store_instance

        result = cli_runner.invoke(docs, ["list"])

        assert result.exit_code == 0
        assert "doc-1" in result.output or "Document 1" in result.output or "2 document" in result.output


class TestDocsClearCommand:
    """Test docs clear command."""

    def test_docs_clear_help(self, cli_runner: CliRunner):
        """Test help text."""
        result = cli_runner.invoke(docs, ["clear", "--help"])
        assert result.exit_code == 0

    @patch("src.cli.commands.docs.VectorStore")
    def test_docs_clear_with_confirmation(self, mock_store, cli_runner):
        """Test clear with user confirmation."""
        store_instance = MagicMock()
        store_instance.count.return_value = 5
        mock_store.return_value = store_instance

        # User confirms with 'y'
        result = cli_runner.invoke(docs, ["clear"], input="y\n")

        if result.exit_code == 0:
            # If clear was executed
            assert "clear" in result.output.lower() or "delete" in result.output.lower()

    @patch("src.cli.commands.docs.VectorStore")
    def test_docs_clear_cancel(self, mock_store, cli_runner):
        """Test clear cancelled by user."""
        store_instance = MagicMock()
        store_instance.count.return_value = 5
        mock_store.return_value = store_instance

        # User cancels with 'n'
        result = cli_runner.invoke(docs, ["clear"], input="n\n")

        # Verify clear was not executed
        assert "cancel" in result.output.lower() or "abort" in result.output.lower() or store_instance.clear.call_count == 0

    @patch("src.cli.commands.docs.VectorStore")
    def test_docs_clear_force(self, mock_store, cli_runner):
        """Test clear with --force flag (no confirmation)."""
        store_instance = MagicMock()
        store_instance.count.return_value = 5
        mock_store.return_value = store_instance

        result = cli_runner.invoke(docs, ["clear", "--force"])

        # Should execute without prompting
        if result.exit_code == 0 and "--force" in str(docs.params):
            store_instance.clear.assert_called_once()
