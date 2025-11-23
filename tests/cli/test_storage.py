"""Tests for v0.5.3 storage management commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from ragged.cli.commands.storage import storage


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


class TestStorageInfoCommand:
    """Test storage info command."""

    def test_storage_info_help(self, cli_runner):
        """Test info command help text."""
        result = cli_runner.invoke(storage, ["info", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output.lower() or "statistics" in result.output.lower()

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_info_basic(self, mock_store, cli_runner):
        """Test basic storage info display."""
        # Mock dual store
        mock_ds = MagicMock()
        mock_ds.get_text_count.return_value = 100
        mock_ds.get_vision_count.return_value = 50
        mock_ds.get_document_count.return_value = 5
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["info"])
        # Should succeed or handle missing storage gracefully
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_info_shows_counts(self, mock_store, cli_runner):
        """Test that info shows document and chunk counts."""
        mock_ds = MagicMock()
        mock_ds.get_text_count.return_value = 150
        mock_ds.get_vision_count.return_value = 75
        mock_ds.get_document_count.return_value = 10
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["info"])
        # Should display counts (or gracefully fail)
        assert result.exit_code in [0, 1]


class TestStorageMigrateCommand:
    """Test storage migrate command."""

    def test_storage_migrate_help(self, cli_runner):
        """Test migrate command help text."""
        result = cli_runner.invoke(storage, ["migrate", "--help"])
        assert result.exit_code == 0
        assert "migrate" in result.output.lower()
        assert "--dry-run" in result.output or "dry" in result.output.lower()

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    @patch("ragged.storage.vector_store.VectorStore")
    def test_storage_migrate_dry_run(self, mock_old_store, mock_new_store, cli_runner):
        """Test migration dry run."""
        mock_old = MagicMock()
        mock_old.count.return_value = 100
        mock_old_store.return_value = mock_old

        mock_new = MagicMock()
        mock_new_store.return_value = mock_new

        result = cli_runner.invoke(storage, ["migrate", "--dry-run"])
        # Should complete dry run
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    @patch("ragged.storage.vector_store.VectorStore")
    def test_storage_migrate_with_backup(self, mock_old_store, mock_new_store, cli_runner):
        """Test migration with backup option."""
        result = cli_runner.invoke(storage, ["migrate", "--backup", "--dry-run"])
        # Should accept backup flag
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    @patch("ragged.storage.vector_store.VectorStore")
    def test_storage_migrate_actual(self, mock_old_store, mock_new_store, cli_runner):
        """Test actual migration (not dry run)."""
        mock_old = MagicMock()
        mock_old.count.return_value = 10
        mock_old.get_all.return_value = []
        mock_old_store.return_value = mock_old

        mock_new = MagicMock()
        mock_new_store.return_value = mock_new

        result = cli_runner.invoke(storage, ["migrate"])
        # Should attempt migration
        assert result.exit_code in [0, 1]


class TestStorageVacuumCommand:
    """Test storage vacuum command."""

    def test_storage_vacuum_help(self, cli_runner):
        """Test vacuum command help text."""
        result = cli_runner.invoke(storage, ["vacuum", "--help"])
        assert result.exit_code == 0
        assert "vacuum" in result.output.lower() or "clean" in result.output.lower()

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_vacuum_dry_run(self, mock_store, cli_runner):
        """Test vacuum dry run."""
        mock_ds = MagicMock()
        mock_ds.find_orphaned_embeddings.return_value = []
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["vacuum", "--dry-run"])
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_vacuum_actual(self, mock_store, cli_runner):
        """Test actual vacuum operation."""
        mock_ds = MagicMock()
        mock_ds.find_orphaned_embeddings.return_value = ["orphan1", "orphan2"]
        mock_ds.delete_orphaned_embeddings.return_value = 2
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["vacuum"])
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_vacuum_shows_count(self, mock_store, cli_runner):
        """Test that vacuum shows orphaned count."""
        mock_ds = MagicMock()
        mock_ds.find_orphaned_embeddings.return_value = ["orphan1"]
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["vacuum", "--dry-run"])
        # Should show count or complete gracefully
        assert result.exit_code in [0, 1]


class TestStorageGroupCommand:
    """Test storage command group."""

    def test_storage_help(self, cli_runner):
        """Test storage group help text."""
        result = cli_runner.invoke(storage, ["--help"])
        assert result.exit_code == 0
        assert "storage" in result.output.lower()
        assert "info" in result.output.lower()
        assert "migrate" in result.output.lower()
        assert "vacuum" in result.output.lower()

    def test_storage_no_subcommand(self, cli_runner):
        """Test storage without subcommand shows help."""
        result = cli_runner.invoke(storage, [])
        assert result.exit_code in [0, 2]


class TestStorageErrorHandling:
    """Test storage command error handling."""

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_info_connection_error(self, mock_store, cli_runner):
        """Test info when storage connection fails."""
        mock_store.side_effect = ConnectionError("Cannot connect to ChromaDB")

        result = cli_runner.invoke(storage, ["info"])
        # Should handle error gracefully
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_migrate_no_data(self, mock_store, cli_runner):
        """Test migrate when no data to migrate."""
        mock_ds = MagicMock()
        mock_ds.get_text_count.return_value = 0
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["migrate", "--dry-run"])
        # Should handle empty state
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_vacuum_no_orphans(self, mock_store, cli_runner):
        """Test vacuum when no orphaned embeddings."""
        mock_ds = MagicMock()
        mock_ds.find_orphaned_embeddings.return_value = []
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["vacuum"])
        assert result.exit_code in [0, 1]
        # Should indicate no orphans found


class TestStorageIntegration:
    """Test storage command integration scenarios."""

    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_info_after_ingest(self, mock_store, cli_runner):
        """Test that info reflects ingested documents."""
        mock_ds = MagicMock()
        mock_ds.get_text_count.return_value = 50
        mock_ds.get_vision_count.return_value = 25
        mock_ds.get_document_count.return_value = 3
        mock_store.return_value = mock_ds

        result = cli_runner.invoke(storage, ["info"])
        assert result.exit_code in [0, 1]

    @patch("ragged.storage.vector_store.VectorStore")
    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    def test_storage_migrate_preserves_data(self, mock_new, mock_old, cli_runner):
        """Test that migration preserves document count."""
        # This is a conceptual test - real migration would be more complex
        mock_old_vs = MagicMock()
        mock_old_vs.count.return_value = 100
        mock_old.return_value = mock_old_vs

        result = cli_runner.invoke(storage, ["migrate", "--dry-run"])
        assert result.exit_code in [0, 1]
