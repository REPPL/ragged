"""Tests for document ingestion (add) command."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest
from click.testing import CliRunner

from src.cli.commands.add import add
from src.ingestion.models import Document, DocumentMetadata, Chunk, ChunkMetadata


@pytest.fixture
def sample_html_path(tmp_path: Path) -> Path:
    """Create a sample HTML document for testing."""
    html_path = tmp_path / "sample.html"
    html_path.write_text("""
    <html>
    <head><title>Test Document</title></head>
    <body>
        <h1>Test Heading</h1>
        <p>This is test content.</p>
    </body>
    </html>
    """)
    return html_path


@pytest.fixture
def sample_markdown_path(tmp_path: Path) -> Path:
    """Create a sample Markdown document for testing."""
    md_path = tmp_path / "sample.md"
    md_path.write_text("# Test Document\n\nThis is test content.\n")
    return md_path


@pytest.fixture
def sample_folder(tmp_path: Path) -> Path:
    """Create a sample folder with multiple documents."""
    folder = tmp_path / "documents"
    folder.mkdir()

    # Create various document types
    (folder / "doc1.txt").write_text("Document 1 content")
    (folder / "doc2.md").write_text("# Document 2\n\nContent")
    (folder / "doc3.html").write_text("<html><body>Document 3</body></html>")

    # Create subdirectory
    subfolder = folder / "subfolder"
    subfolder.mkdir()
    (subfolder / "doc4.txt").write_text("Document 4 in subfolder")

    return folder


@pytest.fixture
def mock_document():
    """Create a mock document with chunks."""
    doc = Document(
        document_id="test-doc-123",
        content="Test content",
        metadata=DocumentMetadata(
            document_path=Path("/tmp/test.txt"),
            document_format="txt",
            title="Test Document",
            file_hash="abc123",
        ),
        chunks=[
            Chunk(
                chunk_id="chunk-1",
                text="Test content",
                metadata=ChunkMetadata(
                    chunk_index=0,
                    document_id="test-doc-123",
                    document_path=Path("/tmp/test.txt"),
                    file_hash="abc123",
                ),
            )
        ],
    )
    return doc


class TestAddHelp:
    """Test add command help text."""

    def test_add_help(self, cli_runner: CliRunner):
        """Test that help text is displayed."""
        result = cli_runner.invoke(add, ["--help"])
        assert result.exit_code == 0
        assert "Ingest document(s) into the system" in result.output
        assert "PATH" in result.output
        assert "--format" in result.output
        assert "--recursive" in result.output


class TestSingleFileIngestion:
    """Test ingesting single files of various formats."""

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_add_text_file(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_document_path,
        mock_document,
    ):
        """Test adding a text file."""
        # Setup mocks
        mock_load.return_value = mock_document
        mock_chunk.return_value = mock_document
        embedder = MagicMock()
        embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        mock_embedder.return_value = embedder

        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {"ids": []}
        mock_store.return_value = store_instance

        result = cli_runner.invoke(add, [str(sample_document_path)])

        assert result.exit_code == 0
        assert "Document ingested" in result.output
        assert "Chunks: 1" in result.output

        # Verify document was loaded
        mock_load.assert_called_once()
        # Verify document was chunked
        mock_chunk.assert_called_once()
        # Verify embeddings were generated
        embedder.embed_batch.assert_called_once()
        # Verify document was stored
        store_instance.add.assert_called_once()

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_add_html_file(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_html_path,
        mock_document,
    ):
        """Test adding an HTML file."""
        mock_load.return_value = mock_document
        mock_chunk.return_value = mock_document
        embedder = MagicMock()
        embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        mock_embedder.return_value = embedder

        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {"ids": []}
        mock_store.return_value = store_instance

        result = cli_runner.invoke(add, [str(sample_html_path)])

        assert result.exit_code == 0
        assert "Document ingested" in result.output

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_add_with_format_option(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_document_path,
        mock_document,
    ):
        """Test adding a file with explicit format."""
        mock_load.return_value = mock_document
        mock_chunk.return_value = mock_document
        embedder = MagicMock()
        embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        mock_embedder.return_value = embedder

        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {"ids": []}
        mock_store.return_value = store_instance

        result = cli_runner.invoke(add, [str(sample_document_path), "--format", "txt"])

        assert result.exit_code == 0
        # Verify format was passed to load_document
        call_args = mock_load.call_args
        assert call_args[1]["format"] == "txt"


class TestFolderIngestion:
    """Test ingesting entire folders."""

    @patch("src.cli.commands.add.BatchIngester")
    @patch("src.cli.commands.add.DocumentScanner")
    def test_add_folder_recursive(
        self,
        mock_scanner,
        mock_batch_ingester,
        cli_runner,
        sample_folder,
    ):
        """Test adding a folder recursively."""
        # Setup scanner mock
        scanner_instance = MagicMock()
        scanner_instance.scan.return_value = [
            sample_folder / "doc1.txt",
            sample_folder / "doc2.md",
            sample_folder / "doc3.html",
            sample_folder / "subfolder" / "doc4.txt",
        ]
        mock_scanner.return_value = scanner_instance

        # Setup batch ingester mock
        batch_instance = MagicMock()
        summary = MagicMock()
        summary.successful = 4
        summary.duplicates = 0
        summary.failed = 0
        summary.total_chunks = 10
        summary.results = []
        batch_instance.ingest_batch.return_value = summary
        mock_batch_ingester.return_value = batch_instance

        result = cli_runner.invoke(add, [str(sample_folder), "--recursive"])

        assert result.exit_code == 0
        assert "Found 4 documents" in result.output
        assert "Successful: 4" in result.output
        assert "Failed: 0" in result.output

        # Verify scanner was called
        scanner_instance.scan.assert_called_once_with(sample_folder)
        # Verify batch ingester was used
        batch_instance.ingest_batch.assert_called_once()

    @patch("src.cli.commands.add.BatchIngester")
    @patch("src.cli.commands.add.DocumentScanner")
    def test_add_folder_no_recursive(
        self,
        mock_scanner,
        mock_batch_ingester,
        cli_runner,
        sample_folder,
    ):
        """Test adding a folder without recursion."""
        scanner_instance = MagicMock()
        # Only top-level files (no subfolder files)
        scanner_instance.scan.return_value = [
            sample_folder / "doc1.txt",
            sample_folder / "doc2.md",
            sample_folder / "doc3.html",
        ]
        mock_scanner.return_value = scanner_instance

        batch_instance = MagicMock()
        summary = MagicMock()
        summary.successful = 3
        summary.duplicates = 0
        summary.failed = 0
        summary.total_chunks = 8
        summary.results = []
        batch_instance.ingest_batch.return_value = summary
        mock_batch_ingester.return_value = batch_instance

        result = cli_runner.invoke(add, [str(sample_folder), "--no-recursive"])

        assert result.exit_code == 0
        assert "Found 3 documents" in result.output

    @patch("src.cli.commands.add.BatchIngester")
    @patch("src.cli.commands.add.DocumentScanner")
    def test_add_folder_with_max_depth(
        self,
        mock_scanner,
        mock_batch_ingester,
        cli_runner,
        sample_folder,
    ):
        """Test adding a folder with max depth limit."""
        scanner_instance = MagicMock()
        scanner_instance.scan.return_value = [
            sample_folder / "doc1.txt",
            sample_folder / "doc2.md",
        ]
        mock_scanner.return_value = scanner_instance

        batch_instance = MagicMock()
        summary = MagicMock()
        summary.successful = 2
        summary.duplicates = 0
        summary.failed = 0
        summary.total_chunks = 5
        summary.results = []
        batch_instance.ingest_batch.return_value = summary
        mock_batch_ingester.return_value = batch_instance

        result = cli_runner.invoke(add, [str(sample_folder), "--max-depth", "1"])

        assert result.exit_code == 0
        # Verify max_depth was used in scanner
        call_args = mock_scanner.call_args
        assert call_args[1]["max_depth"] == 1

    @patch("src.cli.commands.add.DocumentScanner")
    def test_add_empty_folder(
        self,
        mock_scanner,
        cli_runner,
        tmp_path,
    ):
        """Test adding an empty folder."""
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()

        scanner_instance = MagicMock()
        scanner_instance.scan.return_value = []
        mock_scanner.return_value = scanner_instance

        result = cli_runner.invoke(add, [str(empty_folder)])

        assert result.exit_code == 0
        assert "No supported documents found" in result.output
        assert "Supported formats: PDF, TXT, MD, HTML" in result.output


class TestDuplicateHandling:
    """Test duplicate document detection."""

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_duplicate_detection_user_cancels(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_document_path,
        mock_document,
    ):
        """Test that duplicate is detected and user can cancel."""
        mock_load.return_value = mock_document
        mock_chunk.return_value = mock_document
        embedder = MagicMock()
        embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        mock_embedder.return_value = embedder

        # Simulate existing document
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk-1"],
            "metadatas": [{
                "document_id": "existing-doc",
                "document_path": str(sample_document_path),
            }]
        }
        mock_store.return_value = store_instance

        # User inputs 'n' to cancel
        result = cli_runner.invoke(add, [str(sample_document_path)], input="n\n")

        assert result.exit_code == 0
        assert "Document already exists" in result.output
        assert "Cancelled" in result.output
        # Verify document was NOT stored
        store_instance.add.assert_not_called()

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_duplicate_detection_user_overwrites(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_document_path,
        mock_document,
    ):
        """Test that duplicate can be overwritten."""
        mock_load.return_value = mock_document
        mock_chunk.return_value = mock_document
        embedder = MagicMock()
        embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        mock_embedder.return_value = embedder

        # Simulate existing document
        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {
            "ids": ["chunk-1", "chunk-2"],
            "metadatas": [{
                "document_id": "existing-doc",
                "document_path": str(sample_document_path),
            }]
        }
        mock_store.return_value = store_instance

        # User inputs 'y' to overwrite
        result = cli_runner.invoke(add, [str(sample_document_path)], input="y\n")

        assert result.exit_code == 0
        assert "Document already exists" in result.output
        assert "Removed old chunks" in result.output
        # Verify old chunks were deleted
        store_instance.delete.assert_called_once_with(ids=["chunk-1", "chunk-2"])
        # Verify new document was stored
        store_instance.add.assert_called_once()

    @patch("src.cli.commands.add.BatchIngester")
    @patch("src.cli.commands.add.DocumentScanner")
    def test_folder_skips_duplicates(
        self,
        mock_scanner,
        mock_batch_ingester,
        cli_runner,
        sample_folder,
    ):
        """Test that folder ingestion auto-skips duplicates."""
        scanner_instance = MagicMock()
        scanner_instance.scan.return_value = [
            sample_folder / "doc1.txt",
            sample_folder / "doc2.md",
        ]
        mock_scanner.return_value = scanner_instance

        batch_instance = MagicMock()
        summary = MagicMock()
        summary.successful = 1
        summary.duplicates = 1
        summary.failed = 0
        summary.total_chunks = 3
        summary.results = []
        batch_instance.ingest_batch.return_value = summary
        mock_batch_ingester.return_value = batch_instance

        result = cli_runner.invoke(add, [str(sample_folder)])

        assert result.exit_code == 0
        assert "Successful: 1" in result.output
        assert "Duplicates: 1" in result.output


class TestErrorHandling:
    """Test error handling in add command."""

    def test_add_nonexistent_path(self, cli_runner):
        """Test adding a nonexistent path."""
        result = cli_runner.invoke(add, ["/nonexistent/path.txt"])

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower() or "Error" in result.output

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_add_loading_error(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_document_path,
    ):
        """Test handling of document loading errors."""
        mock_load.side_effect = Exception("Failed to load document")

        result = cli_runner.invoke(add, [str(sample_document_path)])

        assert result.exit_code == 1
        assert "Failed to ingest document" in result.output

    @patch("src.cli.commands.add.BatchIngester")
    @patch("src.cli.commands.add.DocumentScanner")
    def test_folder_with_failures(
        self,
        mock_scanner,
        mock_batch_ingester,
        cli_runner,
        sample_folder,
    ):
        """Test folder ingestion with some failures."""
        from src.ingestion.batch import IngestionResult, IngestionStatus

        scanner_instance = MagicMock()
        scanner_instance.scan.return_value = [
            sample_folder / "doc1.txt",
            sample_folder / "doc2.md",
            sample_folder / "doc3.html",
        ]
        mock_scanner.return_value = scanner_instance

        batch_instance = MagicMock()
        summary = MagicMock()
        summary.successful = 2
        summary.duplicates = 0
        summary.failed = 1
        summary.total_chunks = 6
        summary.results = [
            IngestionResult(
                file_path=sample_folder / "doc3.html",
                status=IngestionStatus.FAILED,
                error="Parse error",
            )
        ]
        batch_instance.ingest_batch.return_value = summary
        mock_batch_ingester.return_value = batch_instance

        result = cli_runner.invoke(add, [str(sample_folder)])

        assert result.exit_code == 0
        assert "Successful: 2" in result.output
        assert "Failed: 1" in result.output
        assert "Failed documents:" in result.output
        assert "doc3.html" in result.output

    @patch("src.cli.commands.add.BatchIngester")
    @patch("src.cli.commands.add.DocumentScanner")
    def test_folder_fail_fast(
        self,
        mock_scanner,
        mock_batch_ingester,
        cli_runner,
        sample_folder,
    ):
        """Test folder ingestion with --fail-fast flag."""
        scanner_instance = MagicMock()
        scanner_instance.scan.return_value = [
            sample_folder / "doc1.txt",
        ]
        mock_scanner.return_value = scanner_instance

        batch_instance = MagicMock()
        summary = MagicMock()
        summary.successful = 0
        summary.duplicates = 0
        summary.failed = 1
        summary.total_chunks = 0
        summary.results = []
        batch_instance.ingest_batch.return_value = summary
        mock_batch_ingester.return_value = batch_instance

        result = cli_runner.invoke(add, [str(sample_folder), "--fail-fast"])

        # Verify continue_on_error=False was passed to BatchIngester
        call_args = mock_batch_ingester.call_args
        assert call_args[1]["continue_on_error"] is False


class TestProgressReporting:
    """Test progress reporting during ingestion."""

    @patch("src.cli.commands.add.VectorStore")
    @patch("src.cli.commands.add.get_embedder")
    @patch("src.cli.commands.add.chunk_document")
    @patch("src.cli.commands.add.load_document")
    def test_progress_messages(
        self,
        mock_load,
        mock_chunk,
        mock_embedder,
        mock_store,
        cli_runner,
        sample_document_path,
        mock_document,
    ):
        """Test that progress messages are displayed."""
        mock_load.return_value = mock_document
        mock_chunk.return_value = mock_document
        embedder = MagicMock()
        embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        mock_embedder.return_value = embedder

        store_instance = MagicMock()
        store_instance.get_documents_by_metadata.return_value = {"ids": []}
        mock_store.return_value = store_instance

        result = cli_runner.invoke(add, [str(sample_document_path)])

        assert result.exit_code == 0
        # Check for progress indicators
        assert "Ingesting document" in result.output or "Processing" in result.output
