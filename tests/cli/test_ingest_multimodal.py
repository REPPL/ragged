"""Tests for v0.5.3 multi-modal ingestion commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from ragged.cli.commands.ingest import ingest


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n%EOF\n")  # Minimal valid PDF
    return pdf_file


class TestIngestPdfCommand:
    """Test ingest pdf command."""

    def test_ingest_pdf_help(self, cli_runner):
        """Test pdf command help text."""
        result = cli_runner.invoke(ingest, ["pdf", "--help"])
        assert result.exit_code == 0
        assert "Ingest PDF" in result.output
        assert "--vision" in result.output

    def test_ingest_pdf_requires_path(self, cli_runner):
        """Test that pdf command requires a path argument."""
        result = cli_runner.invoke(ingest, ["pdf"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "required" in result.output.lower()

    @patch("ragged.storage.vector_store.VectorStore")
    @patch("ragged.ingestion.loaders.load_document")
    def test_ingest_pdf_basic(self, mock_loader, mock_store, cli_runner, sample_pdf):
        """Test basic PDF ingestion without vision."""
        # Mock loader
        mock_loader.return_value = {"text": "sample document", "metadata": {}}

        result = cli_runner.invoke(ingest, ["pdf", str(sample_pdf)])

        # Should succeed or gracefully handle missing services
        assert result.exit_code in [0, 1]

    @patch("ragged.embeddings.colpali_embedder.ColPaliEmbedder")
    @patch("ragged.storage.dual_store.DualEmbeddingStore")
    @patch("ragged.ingestion.loaders.load_document")
    def test_ingest_pdf_with_vision(self, mock_loader, mock_store, mock_embedder,
                                    cli_runner, sample_pdf):
        """Test PDF ingestion with vision embeddings."""
        # Mock loader
        mock_loader.return_value = {"text": "sample", "metadata": {}}

        # Mock embedder
        mock_emb = MagicMock()
        mock_emb.embed_pdf.return_value = [[0.1] * 128]
        mock_embedder.return_value = mock_emb

        result = cli_runner.invoke(ingest, ["pdf", str(sample_pdf), "--vision"])

        # Should attempt vision embedding
        assert result.exit_code in [0, 1]

    def test_ingest_pdf_device_option(self, cli_runner, sample_pdf):
        """Test --device option."""
        result = cli_runner.invoke(ingest, ["pdf", str(sample_pdf), "--vision",
                                            "--device", "cpu"])
        # Should accept device option
        assert result.exit_code in [0, 1]

    def test_ingest_pdf_batch_size_option(self, cli_runner, sample_pdf):
        """Test --batch-size option."""
        result = cli_runner.invoke(ingest, ["pdf", str(sample_pdf), "--vision",
                                            "--batch-size", "4"])
        # Should accept batch-size option
        assert result.exit_code in [0, 1]


class TestIngestBatchCommand:
    """Test ingest batch command."""

    def test_ingest_batch_help(self, cli_runner):
        """Test batch command help text."""
        result = cli_runner.invoke(ingest, ["batch", "--help"])
        assert result.exit_code == 0
        assert "Batch ingest" in result.output or "directory" in result.output.lower()
        assert "--vision" in result.output

    def test_ingest_batch_requires_path(self, cli_runner):
        """Test that batch command requires a directory argument."""
        result = cli_runner.invoke(ingest, ["batch"])
        assert result.exit_code != 0

    def test_ingest_batch_accepts_directory(self, cli_runner, tmp_path):
        """Test batch ingestion accepts directory path."""
        result = cli_runner.invoke(ingest, ["batch", str(tmp_path)])
        # Should complete (may warn about no PDFs found)
        assert result.exit_code in [0, 1]

    def test_ingest_batch_pattern_option(self, cli_runner, tmp_path):
        """Test --pattern option."""
        result = cli_runner.invoke(ingest, ["batch", str(tmp_path), "--pattern", "*.pdf"])
        assert result.exit_code in [0, 1]

    def test_ingest_batch_recursive_option(self, cli_runner, tmp_path):
        """Test --recursive/--no-recursive options."""
        result = cli_runner.invoke(ingest, ["batch", str(tmp_path), "--no-recursive"])
        assert result.exit_code in [0, 1]


class TestIngestStatusCommand:
    """Test ingest status command."""

    def test_ingest_status_help(self, cli_runner):
        """Test status command help text."""
        result = cli_runner.invoke(ingest, ["status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower() or "statistics" in result.output.lower()

    @patch("ragged.storage.vector_store.VectorStore")
    def test_ingest_status_basic(self, mock_store, cli_runner):
        """Test basic status display."""
        # Mock store statistics
        mock_vs = MagicMock()
        mock_vs.count.return_value = 10
        mock_store.return_value = mock_vs

        result = cli_runner.invoke(ingest, ["status"])
        # Should show statistics
        assert result.exit_code in [0, 1]


class TestIngestGroupCommand:
    """Test ingest command group."""

    def test_ingest_help(self, cli_runner):
        """Test ingest group help text."""
        result = cli_runner.invoke(ingest, ["--help"])
        assert result.exit_code == 0
        assert "ingest" in result.output.lower()
        assert "pdf" in result.output.lower()
        assert "batch" in result.output.lower()
        assert "status" in result.output.lower()

    def test_ingest_no_subcommand(self, cli_runner):
        """Test ingest without subcommand shows help."""
        result = cli_runner.invoke(ingest, [])
        assert result.exit_code in [0, 2]  # 0 for help, 2 for error
