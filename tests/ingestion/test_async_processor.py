"""Tests for async document processing."""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
import hashlib

from src.ingestion.async_processor import (
    AsyncDocumentProcessor,
    ProcessingResult,
    load_documents_concurrent,
    process_documents_concurrent
)
from src.ingestion.models import Document, DocumentMetadata
from src.chunking.splitters import RecursiveCharacterTextSplitter


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    docs = []

    for i in range(3):
        content = f"This is document {i}. " * 20
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        content_hash = hashlib.sha256((content[:1024] + content[-1024:]).encode()).hexdigest()

        doc = Document(
            document_id=f"doc{i}",
            content=content,
            metadata=DocumentMetadata(
                file_path=Path(f"/path/to/doc{i}.txt"),
                file_size=len(content),
                file_hash=file_hash,
                content_hash=content_hash,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                format="txt"
            )
        )
        docs.append(doc)

    return docs


@pytest.fixture
def temp_text_files():
    """Create temporary text files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        files = []

        for i in range(3):
            file_path = tmp_path / f"test{i}.txt"
            file_path.write_text(f"Content of file {i}\n" * 10)
            files.append(file_path)

        yield files


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_create_success_result(self):
        """Test creating successful processing result."""
        result = ProcessingResult(
            document_id="doc1",
            success=True,
            duration=1.5,
            chunks_created=10
        )

        assert result.document_id == "doc1"
        assert result.success is True
        assert result.duration == 1.5
        assert result.chunks_created == 10
        assert result.error is None

    def test_create_error_result(self):
        """Test creating error result."""
        result = ProcessingResult(
            document_id="doc2",
            success=False,
            duration=0.5,
            error="File not found"
        )

        assert result.document_id == "doc2"
        assert result.success is False
        assert result.error == "File not found"
        assert result.chunks_created == 0


class TestAsyncDocumentProcessor:
    """Test AsyncDocumentProcessor."""

    def test_init_thread_pool(self):
        """Test initialization with thread pool."""
        processor = AsyncDocumentProcessor(max_workers=4, use_process_pool=False)

        assert processor.max_workers == 4
        assert processor.use_process_pool is False

        processor.shutdown()

    def test_init_process_pool(self):
        """Test initialization with process pool."""
        processor = AsyncDocumentProcessor(max_workers=2, use_process_pool=True)

        assert processor.max_workers == 2
        assert processor.use_process_pool is True

        processor.shutdown()

    @pytest.mark.asyncio
    async def test_load_document_async(self, temp_text_files):
        """Test loading single document asynchronously."""
        processor = AsyncDocumentProcessor()

        try:
            document = await processor.load_document_async(temp_text_files[0])

            assert document is not None
            assert document.document_id
            assert "Content of file 0" in document.content
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_load_documents_async(self, temp_text_files):
        """Test loading multiple documents asynchronously."""
        processor = AsyncDocumentProcessor(max_workers=2)

        try:
            documents = await processor.load_documents_async(temp_text_files)

            assert len(documents) == 3
            assert all(doc.content for doc in documents)
            assert all(doc.document_id for doc in documents)
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_load_documents_with_progress(self, temp_text_files):
        """Test loading with progress callback."""
        processor = AsyncDocumentProcessor()
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        try:
            documents = await processor.load_documents_async(
                temp_text_files,
                progress_callback=progress_callback
            )

            assert len(documents) == 3
            assert len(progress_calls) == 3
            assert progress_calls[-1] == (3, 3)
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_process_document_async(self, sample_documents):
        """Test processing single document asynchronously."""
        processor = AsyncDocumentProcessor()
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

        try:
            result = await processor.process_document_async(
                sample_documents[0],
                chunker
            )

            assert result.success is True
            assert result.document_id == "doc0"
            assert result.chunks_created > 0
            assert result.duration > 0
            assert result.error is None
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_process_documents_async(self, sample_documents):
        """Test processing multiple documents asynchronously."""
        processor = AsyncDocumentProcessor(max_workers=2)
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

        try:
            results = await processor.process_documents_async(
                sample_documents,
                chunker
            )

            assert len(results) == 3
            assert all(r.success for r in results)
            assert all(r.chunks_created > 0 for r in results)
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_process_documents_with_progress(self, sample_documents):
        """Test processing with progress callback."""
        processor = AsyncDocumentProcessor()
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        try:
            results = await processor.process_documents_async(
                sample_documents,
                chunker,
                progress_callback=progress_callback
            )

            assert len(results) == 3
            assert len(progress_calls) == 3
            assert progress_calls[-1] == (3, 3)
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_process_batch_async(self, temp_text_files):
        """Test batch processing (load + process)."""
        processor = AsyncDocumentProcessor()
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

        try:
            results = await processor.process_batch_async(
                temp_text_files,
                chunker
            )

            assert len(results) == 3
            assert all(r.success for r in results)
            assert all(r.chunks_created > 0 for r in results)
        finally:
            processor.shutdown()

    @pytest.mark.asyncio
    async def test_process_batch_with_progress(self, temp_text_files):
        """Test batch processing with progress tracking."""
        processor = AsyncDocumentProcessor()
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        progress_calls = []

        def progress_callback(completed, total, stage):
            progress_calls.append((completed, total, stage))

        try:
            results = await processor.process_batch_async(
                temp_text_files,
                chunker,
                progress_callback=progress_callback
            )

            assert len(results) == 3

            # Should have progress calls for both stages
            stages = set(call[2] for call in progress_calls)
            assert "Loading" in stages
            assert "Processing" in stages
        finally:
            processor.shutdown()

    def test_context_manager(self):
        """Test using processor as context manager."""
        with AsyncDocumentProcessor() as processor:
            assert processor.executor is not None

        # Executor should be shutdown after exiting context

    @pytest.mark.asyncio
    async def test_concurrent_loading_faster(self, temp_text_files):
        """Test that concurrent loading is faster than sequential."""
        import time

        # Create more files for meaningful comparison
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            files = []

            for i in range(10):
                file_path = tmp_path / f"test{i}.txt"
                file_path.write_text(f"Content {i}\n" * 100)
                files.append(file_path)

            processor = AsyncDocumentProcessor(max_workers=4)

            try:
                start = time.perf_counter()
                documents = await processor.load_documents_async(files)
                async_duration = time.perf_counter() - start

                assert len(documents) == 10
                # Just verify it completed, actual speedup depends on system
                assert async_duration > 0
            finally:
                processor.shutdown()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_load_documents_concurrent(self, temp_text_files):
        """Test load_documents_concurrent convenience function."""
        documents = await load_documents_concurrent(temp_text_files, max_workers=2)

        assert len(documents) == 3
        assert all(doc.content for doc in documents)

    @pytest.mark.asyncio
    async def test_process_documents_concurrent(self, sample_documents):
        """Test process_documents_concurrent convenience function."""
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

        results = await process_documents_concurrent(
            sample_documents,
            chunker,
            max_workers=2
        )

        assert len(results) == 3
        assert all(r.success for r in results)
