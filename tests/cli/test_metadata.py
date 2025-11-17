"""Tests for metadata management commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.metadata import metadata


class TestMetadataList:
    """Test metadata list command."""

    def test_metadata_list_help(self, cli_runner: CliRunner):
        """Test metadata list help."""
        result = cli_runner.invoke(metadata, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all documents" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_list_empty(self, mock_vector_store, cli_runner: CliRunner):
        """Test listing metadata when no documents exist."""
        store_instance = MagicMock()
        store_instance.collection.get.return_value = {
            "ids": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["list"])
        assert result.exit_code == 0
        assert "No documents found" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_list_with_documents(self, mock_vector_store, cli_runner: CliRunner):
        """Test listing metadata with documents."""
        store_instance = MagicMock()
        store_instance.collection.get.return_value = {
            "ids": ["chunk1", "chunk2", "chunk3"],
            "metadatas": [
                {"document_path": "doc1.pdf", "total_pages": 10, "file_hash": "hash1", "ingestion_date": "2025-01-01"},
                {"document_path": "doc1.pdf", "total_pages": 10, "file_hash": "hash1", "ingestion_date": "2025-01-01"},
                {"document_path": "doc2.pdf", "total_pages": 5, "file_hash": "hash2", "ingestion_date": "2025-01-02"},
            ],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["list"])
        assert result.exit_code == 0
        # Should show 2 unique documents
        assert "doc1.pdf" in result.output
        assert "doc2.pdf" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_list_json_format(self, mock_vector_store, cli_runner: CliRunner):
        """Test listing metadata in JSON format."""
        store_instance = MagicMock()
        store_instance.collection.get.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"document_path": "doc1.pdf", "total_pages": 10}],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["list", "--format", "json"])
        assert result.exit_code == 0
        assert "doc1.pdf" in result.output


class TestMetadataShow:
    """Test metadata show command."""

    def test_metadata_show_help(self, cli_runner: CliRunner):
        """Test metadata show help."""
        result = cli_runner.invoke(metadata, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show metadata for a specific document" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_show_not_found(self, mock_vector_store, cli_runner: CliRunner):
        """Test showing metadata for non-existent document."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["show", "nonexistent.pdf"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_show_found(self, mock_vector_store, cli_runner: CliRunner):
        """Test showing metadata for existing document."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1", "chunk2"],
            "metadatas": [
                {"document_path": "doc1.pdf", "total_pages": 10, "file_hash": "hash1"},
                {"document_path": "doc1.pdf", "total_pages": 10, "file_hash": "hash1"},
            ],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["show", "doc1.pdf"])
        assert result.exit_code == 0
        assert "doc1.pdf" in result.output
        assert "2" in result.output  # 2 chunks

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_show_json_format(self, mock_vector_store, cli_runner: CliRunner):
        """Test showing metadata in JSON format."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"document_path": "doc1.pdf", "total_pages": 10}],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["show", "doc1.pdf", "--format", "json"])
        assert result.exit_code == 0
        assert "document_path" in result.output


class TestMetadataUpdate:
    """Test metadata update command."""

    def test_metadata_update_help(self, cli_runner: CliRunner):
        """Test metadata update help."""
        result = cli_runner.invoke(metadata, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update metadata for a document" in result.output

    def test_metadata_update_no_updates(self, cli_runner: CliRunner):
        """Test update with no --set or --delete options."""
        result = cli_runner.invoke(metadata, ["update", "doc1.pdf"])
        assert result.exit_code == 0
        assert "No updates specified" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_update_not_found(self, mock_vector_store, cli_runner: CliRunner):
        """Test updating non-existent document."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["update", "nonexistent.pdf", "--set", "category=test"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_update_set(self, mock_vector_store, cli_runner: CliRunner):
        """Test setting metadata values."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1", "chunk2"],
            "metadatas": [
                {"document_path": "doc1.pdf"},
                {"document_path": "doc1.pdf"},
            ],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["update", "doc1.pdf", "--set", "category=research"])
        assert result.exit_code == 0
        assert "Updated metadata" in result.output
        assert "2 chunks" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_update_multiple_sets(self, mock_vector_store, cli_runner: CliRunner):
        """Test setting multiple metadata values."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"document_path": "doc1.pdf"}],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(
            metadata,
            ["update", "doc1.pdf", "--set", "category=research", "--set", "priority=high"]
        )
        assert result.exit_code == 0
        assert "Updated metadata" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_update_delete(self, mock_vector_store, cli_runner: CliRunner):
        """Test deleting metadata keys."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"document_path": "doc1.pdf", "old_key": "value"}],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["update", "doc1.pdf", "--delete", "old_key"])
        assert result.exit_code == 0
        assert "Updated metadata" in result.output

    def test_metadata_update_invalid_format(self, cli_runner: CliRunner):
        """Test update with invalid key=value format."""
        result = cli_runner.invoke(metadata, ["update", "doc1.pdf", "--set", "invalidformat"])
        assert result.exit_code == 1
        assert "Invalid" in result.output or "key=value" in result.output


class TestMetadataSearch:
    """Test metadata search command."""

    def test_metadata_search_help(self, cli_runner: CliRunner):
        """Test metadata search help."""
        result = cli_runner.invoke(metadata, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search documents by metadata" in result.output

    def test_metadata_search_no_filters(self, cli_runner: CliRunner):
        """Test search with no filters."""
        result = cli_runner.invoke(metadata, ["search"])
        assert result.exit_code == 0
        assert "No filters specified" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_search_no_results(self, mock_vector_store, cli_runner: CliRunner):
        """Test search with no matching documents."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["search", "--filter", "category=nonexistent"])
        assert result.exit_code == 0
        assert "No documents found" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_search_with_results(self, mock_vector_store, cli_runner: CliRunner):
        """Test search with matching documents."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1", "chunk2", "chunk3"],
            "metadatas": [
                {"document_path": "doc1.pdf", "category": "research"},
                {"document_path": "doc1.pdf", "category": "research"},
                {"document_path": "doc2.pdf", "category": "research"},
            ],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(metadata, ["search", "--filter", "category=research"])
        assert result.exit_code == 0
        assert "2" in result.output  # 2 documents
        assert "doc1.pdf" in result.output
        assert "doc2.pdf" in result.output

    @patch("src.cli.commands.metadata.VectorStore")
    def test_metadata_search_multiple_filters(self, mock_vector_store, cli_runner: CliRunner):
        """Test search with multiple filters."""
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"document_path": "doc1.pdf", "category": "research", "priority": "high"}],
        }
        mock_vector_store.return_value = store_instance

        result = cli_runner.invoke(
            metadata,
            ["search", "--filter", "category=research", "--filter", "priority=high"]
        )
        assert result.exit_code == 0
        assert "doc1.pdf" in result.output

    def test_metadata_search_invalid_format(self, cli_runner: CliRunner):
        """Test search with invalid filter format."""
        result = cli_runner.invoke(metadata, ["search", "--filter", "invalidformat"])
        assert result.exit_code == 1
        assert "Invalid" in result.output or "key=value" in result.output
