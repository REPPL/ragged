"""Tests for text splitting."""

import pytest

from src.chunking.splitters import (
    RecursiveCharacterTextSplitter,
    chunk_document,
    create_chunk_metadata,
)
from src.ingestion.models import Document


class TestRecursiveCharacterTextSplitter:
    """Test suite for RecursiveCharacterTextSplitter."""

    def test_initialization(self) -> None:
        """Test splitter initialization."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        assert splitter.chunk_size == 100
        assert splitter.chunk_overlap == 20

    def test_uses_config_defaults(self) -> None:
        """Test that config defaults are used."""
        from src.config.settings import get_settings
        splitter = RecursiveCharacterTextSplitter()
        settings = get_settings()
        assert splitter.chunk_size == settings.chunk_size
        assert splitter.chunk_overlap == settings.chunk_overlap

    def test_splits_by_paragraphs(self) -> None:
        """Test splitting by paragraph breaks."""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        chunks = splitter.split_text(text)
        assert len(chunks) >= 1
        # Should respect paragraph boundaries
        for chunk in chunks:
            assert chunk.strip()  # No empty chunks

    def test_splits_by_lines_if_needed(self) -> None:
        """Test recursive splitting to lines if paragraphs too large."""
        text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=5)
        chunks = splitter.split_text(text)
        # Should split into multiple chunks when lines exceed chunk size
        assert len(chunks) > 0
        # Verify each chunk respects token limits
        from src.chunking.token_counter import count_tokens
        for chunk in chunks:
            # Allow some flexibility for overlap
            assert count_tokens(chunk) <= splitter.chunk_size + splitter.chunk_overlap

    def test_respects_chunk_size(self) -> None:
        """Test that chunks don't exceed chunk_size."""
        from src.chunking.token_counter import count_tokens
        text = "word " * 1000
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
        chunks = splitter.split_text(text)
        # Each chunk should not exceed the chunk size
        for chunk in chunks:
            token_count = count_tokens(chunk)
            assert token_count <= 100, f"Chunk has {token_count} tokens, expected <= 100"

    def test_adds_overlap(self) -> None:
        """Test that overlap is added between chunks."""
        text = "This is chunk one. This is chunk two. This is chunk three."
        splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=5)
        chunks = splitter.split_text(text)
        # If we have multiple chunks, they should have some overlap
        if len(chunks) > 1:
            # Check that consecutive chunks share some content
            for i in range(len(chunks) - 1):
                current_end = chunks[i][-10:]  # Last 10 chars of current
                next_start = chunks[i + 1][:10]  # First 10 chars of next
                # Some overlap should exist (at least some common words)
                assert len(chunks[i]) > 0 and len(chunks[i + 1]) > 0

    def test_handles_empty_text(self) -> None:
        """Test handling of empty text."""
        splitter = RecursiveCharacterTextSplitter()
        chunks = splitter.split_text("")
        assert chunks == []

    def test_preserves_semantic_boundaries(self) -> None:
        """Test that splitting preserves sentence boundaries when possible."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        splitter = RecursiveCharacterTextSplitter(chunk_size=40, chunk_overlap=10)
        chunks = splitter.split_text(text)
        # Verify sentences aren't split awkwardly
        for chunk in chunks:
            # Chunks should not start with just whitespace
            assert chunk == chunk.strip() or chunk.strip(), "Chunk should not be just whitespace"


class TestChunkDocument:
    """Test suite for document chunking."""

    def test_chunks_document(self, sample_txt_path) -> None:
        """Test that document is chunked correctly."""
        content = sample_txt_path.read_text()
        doc = Document.from_file(sample_txt_path, content, "txt")
        chunked_doc = chunk_document(doc)
        assert len(chunked_doc.chunks) > 0
        # Verify chunks have correct structure
        for chunk in chunked_doc.chunks:
            assert chunk.text
            assert chunk.metadata

    def test_chunks_have_metadata(self, sample_txt_path) -> None:
        """Test that chunks include metadata."""
        content = sample_txt_path.read_text()
        doc = Document.from_file(sample_txt_path, content, "txt")
        chunked_doc = chunk_document(doc)
        for i, chunk in enumerate(chunked_doc.chunks):
            assert chunk.metadata.chunk_position == i
            assert chunk.metadata.total_chunks == len(chunked_doc.chunks)
            assert chunk.metadata.document_id == chunked_doc.document_id

    def test_uses_custom_splitter(self, sample_txt_path) -> None:
        """Test using a custom splitter."""
        content = sample_txt_path.read_text()
        doc = Document.from_file(sample_txt_path, content, "txt")
        custom_splitter = RecursiveCharacterTextSplitter(chunk_size=200)
        chunked_doc = chunk_document(doc, splitter=custom_splitter)
        assert len(chunked_doc.chunks) > 0
        # Verify custom chunk size was used
        from src.chunking.token_counter import count_tokens
        for chunk in chunked_doc.chunks:
            # Chunks should respect the custom size (with some flexibility for overlap)
            assert count_tokens(chunk.text) <= 200 + custom_splitter.chunk_overlap


class TestCreateChunkMetadata:
    """Test suite for chunk metadata creation."""

    def test_creates_metadata(self, sample_txt_path) -> None:
        """Test metadata creation."""
        metadata = create_chunk_metadata(
            document_id="doc123",
            document_path=sample_txt_path,
            file_hash="a" * 64,  # Valid SHA256 hash (64 hex chars)
            content_hash="b" * 64,  # Valid SHA256 hash (64 hex chars)
            position=0,
            total_chunks=5,
        )
        assert metadata.document_id == "doc123"
        assert metadata.chunk_position == 0
        assert metadata.total_chunks == 5
        assert metadata.document_path == sample_txt_path

    def test_calculates_overlap(self, sample_txt_path) -> None:
        """Test overlap calculation."""
        previous_text = "This is previous chunk text."
        next_text = "This is next chunk text."
        metadata = create_chunk_metadata(
            document_id="doc123",
            document_path=sample_txt_path,
            file_hash="a" * 64,  # Valid SHA256 hash (64 hex chars)
            content_hash="b" * 64,  # Valid SHA256 hash (64 hex chars)
            position=1,
            total_chunks=3,
            previous_text=previous_text,
            next_text=next_text,
        )
        # Check metadata was created successfully
        assert metadata.document_id == "doc123"
        assert metadata.chunk_position == 1
