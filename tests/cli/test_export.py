"""Tests for export and import commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.exportimport import export


class TestExportBackup:
    """Test export backup command."""

    def test_export_backup_help(self, cli_runner: CliRunner):
        """Test export backup help."""
        result = cli_runner.invoke(export, ["backup", "--help"])
        assert result.exit_code == 0
        assert "Create a backup" in result.output

    @patch("src.storage.vector_store.VectorStore")
    def test_export_backup_empty_database(self, mock_vector_store, cli_runner: CliRunner, tmp_path):
        """Test backing up empty database."""
        store_instance = MagicMock()
        store_instance._collection_name = "test_collection"
        store_instance.collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        mock_vector_store.return_value = store_instance

        output_file = tmp_path / "backup.json"
        result = cli_runner.invoke(export, ["backup", "--output", str(output_file)])
        assert result.exit_code == 0
        assert "No data to export" in result.output

    @patch("src.storage.vector_store.VectorStore")
    def test_export_backup_with_data(self, mock_vector_store, cli_runner: CliRunner, tmp_path):
        """Test backing up with data."""
        store_instance = MagicMock()
        store_instance._collection_name = "test_collection"
        store_instance.collection.get.return_value = {
            "ids": ["chunk1", "chunk2"],
            "documents": ["doc1 content", "doc2 content"],
            "metadatas": [{"document_path": "doc1.pdf"}, {"document_path": "doc2.pdf"}],
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
        }
        mock_vector_store.return_value = store_instance

        output_file = tmp_path / "backup.json"
        result = cli_runner.invoke(export, ["backup", "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Backup created successfully" in result.output

    @patch("src.storage.vector_store.VectorStore")
    def test_export_backup_compressed(self, mock_vector_store, cli_runner: CliRunner, tmp_path):
        """Test creating compressed backup."""
        store_instance = MagicMock()
        store_instance._collection_name = "test_collection"
        store_instance.collection.get.return_value = {
            "ids": ["chunk1"],
            "documents": ["content"],
            "metadatas": [{"document_path": "doc1.pdf"}],
            "embeddings": [[0.1, 0.2]],
        }
        mock_vector_store.return_value = store_instance

        output_file = tmp_path / "backup.json.gz"
        result = cli_runner.invoke(export, ["backup", "--output", str(output_file), "--compress"])
        assert result.exit_code == 0
        assert output_file.exists()

    @patch("src.storage.vector_store.VectorStore")
    @patch("src.cli.commands.exportimport.get_settings")
    def test_export_backup_with_config(self, mock_settings, mock_vector_store, cli_runner: CliRunner, tmp_path):
        """Test backup including configuration."""
        settings = MagicMock()
        settings.embedding_model = "test-model"
        settings.llm_model = "test-llm"
        settings.retrieval_method = "hybrid"
        settings.chunk_size = 1000
        settings.chunk_overlap = 200
        mock_settings.return_value = settings

        store_instance = MagicMock()
        store_instance._collection_name = "test_collection"
        store_instance.collection.get.return_value = {
            "ids": ["chunk1"],
            "documents": ["content"],
            "metadatas": [{"document_path": "doc1.pdf"}],
            "embeddings": [[0.1, 0.2]],
        }
        mock_vector_store.return_value = store_instance

        output_file = tmp_path / "backup.json"
        result = cli_runner.invoke(export, ["backup", "--output", str(output_file), "--include-config"])
        assert result.exit_code == 0


class TestExportRestore:
    """Test export restore command."""

    def test_export_restore_help(self, cli_runner: CliRunner):
        """Test export restore help."""
        result = cli_runner.invoke(export, ["restore", "--help"])
        assert result.exit_code == 0
        assert "Restore data from a backup" in result.output

    def test_export_restore_nonexistent_file(self, cli_runner: CliRunner):
        """Test restoring from non-existent file."""
        result = cli_runner.invoke(export, ["restore", "/nonexistent/backup.json", "--yes"])
        assert result.exit_code != 0  # Should fail

    @patch("src.storage.vector_store.VectorStore")
    def test_export_restore_invalid_backup(self, mock_vector_store, cli_runner: CliRunner, tmp_path):
        """Test restoring from invalid backup file."""
        backup_file = tmp_path / "invalid.json"
        backup_file.write_text("{}")  # Invalid backup format

        result = cli_runner.invoke(export, ["restore", str(backup_file), "--yes"])
        assert result.exit_code == 1
        assert "Invalid" in result.output


class TestExportInfo:
    """Test export info command."""

    def test_export_info_help(self, cli_runner: CliRunner):
        """Test export info help."""
        result = cli_runner.invoke(export, ["info", "--help"])
        assert result.exit_code == 0
        assert "Show information about a backup" in result.output

    def test_export_info_nonexistent_file(self, cli_runner: CliRunner):
        """Test showing info for non-existent file."""
        result = cli_runner.invoke(export, ["info", "/nonexistent/backup.json"])
        assert result.exit_code != 0

    def test_export_info_valid_backup(self, cli_runner: CliRunner, tmp_path):
        """Test showing info for valid backup."""
        import json

        backup_file = tmp_path / "backup.json"
        backup_data = {
            "version": "0.2.8",
            "ragged_version": "0.2.8",
            "export_timestamp": "2025-01-01T12:00:00",
            "collection_name": "test",
            "total_chunks": 10,
            "include_embeddings": True,
            "chunks": [],
        }
        backup_file.write_text(json.dumps(backup_data))

        result = cli_runner.invoke(export, ["info", str(backup_file)])
        assert result.exit_code == 0
        assert "Backup Information" in result.output
        assert "10" in result.output  # total_chunks


class TestExportList:
    """Test export list command."""

    def test_export_list_help(self, cli_runner: CliRunner):
        """Test export list help."""
        result = cli_runner.invoke(export, ["list", "--help"])
        assert result.exit_code == 0
        assert "List available backup files" in result.output

    def test_export_list_empty_directory(self, cli_runner: CliRunner, tmp_path):
        """Test listing backups in empty directory."""
        result = cli_runner.invoke(export, ["list", "--directory", str(tmp_path)])
        assert result.exit_code == 0
        assert "No backup files found" in result.output

    def test_export_list_with_backups(self, cli_runner: CliRunner, tmp_path):
        """Test listing directory with backups."""
        # Create dummy backup files
        (tmp_path / "ragged_backup_20250101_120000.json").write_text("{}")
        (tmp_path / "ragged_backup_20250102_120000.json.gz").write_text("{}")

        result = cli_runner.invoke(export, ["list", "--directory", str(tmp_path)])
        assert result.exit_code == 0
        assert "2" in result.output  # 2 backup files
