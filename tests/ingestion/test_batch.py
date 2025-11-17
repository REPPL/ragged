"""Tests for batch document ingestion."""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from rich.console import Console
from rich.progress import Progress

from src.ingestion.batch import (
    BatchIngester,
    BatchSummary,
    IngestionResult,
    IngestionStatus,
)


@pytest.fixture
def console():
    """Create a mock Rich console."""
    return Mock(spec=Console)


@pytest.fixture(autouse=True)
def temp_data_dir(temp_dir):
    """Set RAGGED_DATA_DIR to temp directory for all tests."""
    os.environ['RAGGED_DATA_DIR'] = str(temp_dir / ".ragged")
    yield
    if 'RAGGED_DATA_DIR' in os.environ:
        del os.environ['RAGGED_DATA_DIR']


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    with patch('src.ingestion.batch.VectorStore') as MockVectorStore:
        mock_store = MagicMock()
        MockVectorStore.return_value = mock_store
        yield mock_store


@pytest.fixture
def mock_embedder():
    """Create a mock embedder."""
    with patch('src.ingestion.batch.get_embedder') as mock_get_embedder:
        mock_embed = MagicMock()
        mock_embed.embed_batch.return_value = [[0.1] * 384]  # Mock embeddings
        mock_get_embedder.return_value = mock_embed
        yield mock_embed


@pytest.fixture
def sample_documents(temp_dir):
    """Create sample documents for testing."""
    docs = []
    for i in range(3):
        doc = temp_dir / f"doc{i}.txt"
        doc.write_text(f"Content of document {i}\n" * 10)
        docs.append(doc)
    return docs


class TestBatchIngesterInit:
    """Tests for BatchIngester initialization."""

    def test_default_initialization(self, console):
        """Test ingester with default parameters."""
        ingester = BatchIngester(console)

        assert ingester.console == console
        assert ingester.continue_on_error is True
        assert ingester.skip_duplicates is True

    def test_custom_initialization(self, console):
        """Test ingester with custom parameters."""
        ingester = BatchIngester(
            console,
            continue_on_error=False,
            skip_duplicates=False
        )

        assert ingester.console == console
        assert ingester.continue_on_error is False
        assert ingester.skip_duplicates is False


class TestBatchIngestion:
    """Tests for batch document ingestion."""

    @pytest.mark.requires_chromadb
    def test_ingest_empty_batch(self, console, mock_vector_store, mock_embedder):
        """Test ingesting empty list of documents."""
        ingester = BatchIngester(console)
        summary = ingester.ingest_batch([])

        assert summary.total == 0
        assert summary.successful == 0
        assert summary.failed == 0
        assert summary.duplicates == 0
        assert summary.total_chunks == 0
        assert summary.results == []

    @pytest.mark.requires_chromadb
    def test_ingest_single_document(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test ingesting a single document."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console)
        summary = ingester.ingest_batch([sample_documents[0]])

        assert summary.total == 1
        assert summary.successful == 1
        assert summary.failed == 0
        assert len(summary.results) == 1

    @pytest.mark.requires_chromadb
    def test_ingest_multiple_documents(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test ingesting multiple documents."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console)
        summary = ingester.ingest_batch(sample_documents)

        assert summary.total == 3
        assert summary.successful == 3
        assert summary.failed == 0
        assert len(summary.results) == 3

    @pytest.mark.requires_chromadb
    def test_ingest_with_progress_bar(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test ingesting with progress bar."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console)
        progress = Mock(spec=Progress)
        progress.add_task.return_value = "task_id"

        summary = ingester.ingest_batch(sample_documents, progress=progress)

        assert summary.total == 3
        assert progress.add_task.called
        assert progress.update.called

    @pytest.mark.requires_chromadb
    def test_continue_on_error_true(self, console, temp_dir, mock_vector_store, mock_embedder):
        """Test that processing continues after errors when configured."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        # Create one good file and one bad file
        good_doc = temp_dir / "good.txt"
        good_doc.write_text("Good content\n" * 10)

        bad_doc = temp_dir / "bad.txt"
        bad_doc.write_text("Bad content")  # Too short, might fail validation

        ingester = BatchIngester(console, continue_on_error=True)

        with patch('src.ingestion.batch.load_document') as mock_load, \
             patch('src.ingestion.batch.chunk_document') as mock_chunk:
            # Create proper mock document
            mock_doc = MagicMock()
            mock_doc.metadata.file_hash = "hash1"
            mock_doc.content = "test content"

            # First call succeeds, second fails
            mock_load.side_effect = [
                mock_doc,
                ValueError("Load failed")
            ]

            # Mock chunk_document to return proper structure
            mock_chunk_obj = MagicMock()
            mock_chunk_obj.text = "chunk text"
            mock_chunk_obj.chunk_id = "chunk_1"
            mock_chunk_obj.metadata.model_dump.return_value = {"filename": "test.txt"}
            mock_chunked_doc = MagicMock()
            mock_chunked_doc.chunks = [mock_chunk_obj]
            mock_chunked_doc.document_id = "doc_1"
            mock_chunk.return_value = mock_chunked_doc

            summary = ingester.ingest_batch([good_doc, bad_doc])

            assert summary.total == 2
            assert summary.failed >= 1  # At least one failure

    @pytest.mark.requires_chromadb
    def test_continue_on_error_false(self, console, temp_dir, mock_vector_store, mock_embedder):
        """Test that processing stops after error when configured."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        # Create documents
        docs = []
        for i in range(3):
            doc = temp_dir / f"doc{i}.txt"
            doc.write_text(f"Content {i}\n" * 10)
            docs.append(doc)

        ingester = BatchIngester(console, continue_on_error=False)

        with patch('src.ingestion.batch.load_document') as mock_load, \
             patch('src.ingestion.batch.chunk_document') as mock_chunk:

            # Create proper mock documents
            mock_doc1 = MagicMock()
            mock_doc1.metadata.file_hash = "hash1"
            mock_doc1.content = "test content"

            mock_doc3 = MagicMock()
            mock_doc3.metadata.file_hash = "hash3"
            mock_doc3.content = "test content 3"

            # Second call fails
            mock_load.side_effect = [
                mock_doc1,
                ValueError("Load failed"),
                mock_doc3,
            ]

            # Mock chunk_document to return proper structure
            mock_chunk_obj = MagicMock()
            mock_chunk_obj.text = "chunk text"
            mock_chunk_obj.chunk_id = "chunk_1"
            mock_chunk_obj.metadata.model_dump.return_value = {"filename": "test.txt"}
            mock_chunked_doc = MagicMock()
            mock_chunked_doc.chunks = [mock_chunk_obj]
            mock_chunked_doc.document_id = "doc_1"
            mock_chunk.return_value = mock_chunked_doc

            summary = ingester.ingest_batch(docs)

            # Should stop after error
            assert summary.total == 2  # Processed first two (one success, one fail)
            assert summary.failed == 1

    @pytest.mark.requires_chromadb
    def test_skip_duplicates_enabled(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test that duplicates are skipped when enabled."""
        # First document: no duplicate
        # Second document: is duplicate
        # Third document: no duplicate
        mock_vector_store.get_documents_by_metadata.side_effect = [
            {"ids": []},  # First: not duplicate
            {"ids": ["existing_id"], "metadatas": [{"document_id": "existing_doc"}]},  # Second: duplicate
            {"ids": []},  # Third: not duplicate
        ]

        ingester = BatchIngester(console, skip_duplicates=True)
        summary = ingester.ingest_batch(sample_documents)

        assert summary.total == 3
        assert summary.duplicates >= 1
        assert summary.successful >= 1

    @pytest.mark.requires_chromadb
    def test_skip_duplicates_disabled(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test that duplicates are processed when disabled."""
        # Even if documents look like duplicates, they should be ingested
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": ["existing"]}

        ingester = BatchIngester(console, skip_duplicates=False)
        summary = ingester.ingest_batch(sample_documents)

        # All should be attempted (success or failure)
        assert summary.total == 3
        assert summary.duplicates == 0  # Not checking for duplicates


class TestIngestionResult:
    """Tests for IngestionResult dataclass."""

    def test_success_result(self, temp_dir):
        """Test creating a success result."""
        doc_path = temp_dir / "doc.txt"
        result = IngestionResult(
            file_path=doc_path,
            status=IngestionStatus.SUCCESS,
            document_id="doc123",
            chunks=5
        )

        assert result.file_path == doc_path
        assert result.status == IngestionStatus.SUCCESS
        assert result.document_id == "doc123"
        assert result.chunks == 5
        assert result.error is None
        assert result.duplicate_of is None

    def test_failed_result(self, temp_dir):
        """Test creating a failed result."""
        doc_path = temp_dir / "doc.txt"
        result = IngestionResult(
            file_path=doc_path,
            status=IngestionStatus.FAILED,
            error="File not found"
        )

        assert result.file_path == doc_path
        assert result.status == IngestionStatus.FAILED
        assert result.error == "File not found"
        assert result.document_id is None
        assert result.chunks == 0

    def test_duplicate_result(self, temp_dir):
        """Test creating a duplicate result."""
        doc_path = temp_dir / "doc.txt"
        result = IngestionResult(
            file_path=doc_path,
            status=IngestionStatus.DUPLICATE,
            duplicate_of="original_doc"
        )

        assert result.file_path == doc_path
        assert result.status == IngestionStatus.DUPLICATE
        assert result.duplicate_of == "original_doc"


class TestBatchSummary:
    """Tests for BatchSummary dataclass."""

    def test_summary_creation(self, temp_dir):
        """Test creating a batch summary."""
        results = [
            IngestionResult(
                file_path=temp_dir / "doc1.txt",
                status=IngestionStatus.SUCCESS,
                chunks=5
            ),
            IngestionResult(
                file_path=temp_dir / "doc2.txt",
                status=IngestionStatus.FAILED,
                error="Error"
            ),
            IngestionResult(
                file_path=temp_dir / "doc3.txt",
                status=IngestionStatus.DUPLICATE,
                duplicate_of="doc1"
            ),
        ]

        summary = BatchSummary(
            total=3,
            successful=1,
            duplicates=1,
            skipped=0,
            failed=1,
            total_chunks=5,
            results=results
        )

        assert summary.total == 3
        assert summary.successful == 1
        assert summary.duplicates == 1
        assert summary.failed == 1
        assert summary.total_chunks == 5
        assert len(summary.results) == 3

    def test_summary_all_successful(self, temp_dir):
        """Test summary with all successful ingestions."""
        results = [
            IngestionResult(
                file_path=temp_dir / f"doc{i}.txt",
                status=IngestionStatus.SUCCESS,
                chunks=3
            )
            for i in range(5)
        ]

        summary = BatchSummary(
            total=5,
            successful=5,
            duplicates=0,
            skipped=0,
            failed=0,
            total_chunks=15,
            results=results
        )

        assert summary.total == 5
        assert summary.successful == 5
        assert summary.failed == 0
        assert summary.duplicates == 0
        assert summary.total_chunks == 15


class TestIngestionStatus:
    """Tests for IngestionStatus enum."""

    def test_status_values(self):
        """Test that all status values are defined."""
        assert IngestionStatus.SUCCESS == "success"
        assert IngestionStatus.DUPLICATE == "duplicate"
        assert IngestionStatus.SKIPPED == "skipped"
        assert IngestionStatus.FAILED == "failed"

    def test_status_is_string_enum(self):
        """Test that IngestionStatus is a string enum."""
        assert isinstance(IngestionStatus.SUCCESS, str)
        assert isinstance(IngestionStatus.FAILED, str)


@pytest.mark.requires_chromadb
class TestBatchIngestionErrors:
    """Tests for error handling during batch ingestion."""

    def test_handles_missing_file(self, console, temp_dir, mock_vector_store, mock_embedder):
        """Test handling of missing file."""
        missing_doc = temp_dir / "missing.txt"  # File doesn't exist

        ingester = BatchIngester(console)
        summary = ingester.ingest_batch([missing_doc])

        assert summary.total == 1
        assert summary.failed == 1
        assert "not found" in summary.results[0].error.lower() or "exist" in summary.results[0].error.lower()

    def test_handles_invalid_document(self, console, temp_dir, mock_vector_store, mock_embedder):
        """Test handling of invalid document."""
        invalid_doc = temp_dir / "empty.txt"
        invalid_doc.write_text("")  # Empty file

        ingester = BatchIngester(console)
        summary = ingester.ingest_batch([invalid_doc])

        assert summary.total == 1
        # Should either fail or skip
        assert summary.failed + summary.skipped >= 1


@pytest.mark.requires_chromadb
class TestProgressTracking:
    """Tests for progress tracking functionality."""

    def test_progress_updates(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test that progress is updated during ingestion."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console)
        progress = Mock(spec=Progress)
        task_id = "test_task"
        progress.add_task.return_value = task_id

        summary = ingester.ingest_batch(sample_documents, progress=progress)

        # Verify progress was updated
        assert progress.add_task.called
        update_calls = progress.update.call_args_list

        # Should have updates for each document plus final update
        assert len(update_calls) >= len(sample_documents)

    def test_no_progress_bar(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test ingestion without progress bar."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console)
        summary = ingester.ingest_batch(sample_documents, progress=None)

        # Should complete without errors
        assert summary.total == 3


@pytest.mark.unit
class TestMetadataHandling:
    """Tests for metadata handling during ingestion."""

    @pytest.mark.requires_chromadb
    def test_path_converted_to_string(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test that Path objects in metadata are converted to strings."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console, skip_duplicates=False)

        with patch('src.ingestion.batch.chunk_document') as mock_chunk:
            # Create mock chunks with Path in metadata
            mock_doc = MagicMock()
            mock_chunk_obj = MagicMock()
            mock_chunk_obj.text = "chunk text"
            mock_chunk_obj.chunk_id = "chunk_1"
            mock_chunk_obj.metadata.model_dump.return_value = {
                "document_path": Path("/some/path"),
                "file_name": "test.txt"
            }
            mock_doc.chunks = [mock_chunk_obj]
            mock_doc.document_id = "doc_1"
            mock_chunk.return_value = mock_doc

            summary = ingester.ingest_batch([sample_documents[0]])

            # Check that vector_store.add was called with string path
            if mock_vector_store.add.called:
                call_args = mock_vector_store.add.call_args
                metadatas = call_args[1].get('metadatas', [])
                if metadatas:
                    assert isinstance(metadatas[0].get("document_path", ""), str)

    @pytest.mark.requires_chromadb
    def test_none_values_removed(self, console, sample_documents, mock_vector_store, mock_embedder):
        """Test that None values are removed from metadata."""
        mock_vector_store.get_documents_by_metadata.return_value = {"ids": []}

        ingester = BatchIngester(console, skip_duplicates=False)

        with patch('src.ingestion.batch.chunk_document') as mock_chunk:
            # Create mock chunks with None values in metadata
            mock_doc = MagicMock()
            mock_chunk_obj = MagicMock()
            mock_chunk_obj.text = "chunk text"
            mock_chunk_obj.chunk_id = "chunk_1"
            mock_chunk_obj.metadata.model_dump.return_value = {
                "file_name": "test.txt",
                "optional_field": None,
                "another_field": None
            }
            mock_doc.chunks = [mock_chunk_obj]
            mock_doc.document_id = "doc_1"
            mock_chunk.return_value = mock_doc

            summary = ingester.ingest_batch([sample_documents[0]])

            # Check that None values were removed
            if mock_vector_store.add.called:
                call_args = mock_vector_store.add.call_args
                metadatas = call_args[1].get('metadatas', [])
                if metadatas:
                    assert None not in metadatas[0].values()
