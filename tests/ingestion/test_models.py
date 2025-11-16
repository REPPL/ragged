"""Tests for ingestion data models."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.ingestion.models import Chunk, ChunkMetadata, Document, DocumentMetadata


class TestDocumentMetadata:
    """Test suite for DocumentMetadata model."""

    def test_valid_metadata(self, sample_txt_path: Path) -> None:
        """Test creating valid document metadata."""
        metadata = DocumentMetadata(
            file_path=sample_txt_path,
            file_size=1000,
            file_hash="a" * 64,  # Valid SHA256 hex
            content_hash="b" * 64,  # Valid SHA256 hex
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
            format="txt",
        )

        assert metadata.file_path == sample_txt_path
        assert metadata.file_size == 1000
        assert metadata.format == "txt"
        assert metadata.content_hash == "b" * 64

    def test_invalid_file_hash(self, sample_txt_path: Path) -> None:
        """Test that invalid hash raises error."""
        with pytest.raises(ValidationError):
            DocumentMetadata(
                file_path=sample_txt_path,
                file_size=1000,
                file_hash="invalid",  # Too short
                content_hash="b" * 64,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
                format="txt",
            )

    def test_invalid_format(self, sample_txt_path: Path) -> None:
        """Test that unsupported format raises error."""
        with pytest.raises(ValidationError):
            DocumentMetadata(
                file_path=sample_txt_path,
                file_size=1000,
                file_hash="a" * 64,
                content_hash="b" * 64,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
                format="docx",  # Unsupported
            )

    def test_negative_file_size(self, sample_txt_path: Path) -> None:
        """Test that negative file size raises error."""
        with pytest.raises(ValidationError):
            DocumentMetadata(
                file_path=sample_txt_path,
                file_size=-100,
                file_hash="a" * 64,
                content_hash="b" * 64,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
                format="txt",
            )

    def test_format_case_insensitive(self, sample_txt_path: Path) -> None:
        """Test that format is case-insensitive."""
        metadata = DocumentMetadata(
            file_path=sample_txt_path,
            file_size=1000,
            file_hash="a" * 64,
            content_hash="b" * 64,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
            format="PDF",  # Uppercase
        )

        assert metadata.format == "pdf"  # Normalized to lowercase


class TestChunkMetadata:
    """Test suite for ChunkMetadata model."""

    def test_valid_chunk_metadata(self, sample_txt_path: Path) -> None:
        """Test creating valid chunk metadata."""
        metadata = ChunkMetadata(
            document_id="doc123",
            document_path=sample_txt_path,
            file_hash="a" * 64,
            content_hash="b" * 64,
            chunk_position=0,
            total_chunks=5,
            overlap_with_previous=0,
            overlap_with_next=10,
        )

        assert metadata.document_id == "doc123"
        assert metadata.chunk_position == 0
        assert metadata.total_chunks == 5

    def test_position_greater_than_total(self, sample_txt_path: Path) -> None:
        """Test that position >= total_chunks raises error."""
        with pytest.raises(ValidationError):
            ChunkMetadata(
                document_id="doc123",
                document_path=sample_txt_path,
                chunk_position=5,  # >= total_chunks
                total_chunks=5,
                overlap_with_previous=0,
                overlap_with_next=0,
            )

    def test_negative_overlap(self, sample_txt_path: Path) -> None:
        """Test that negative overlap raises error."""
        with pytest.raises(ValidationError):
            ChunkMetadata(
                document_id="doc123",
                document_path=sample_txt_path,
                chunk_position=0,
                total_chunks=5,
                overlap_with_previous=-10,  # Negative
                overlap_with_next=0,
            )


class TestChunk:
    """Test suite for Chunk model."""

    def test_valid_chunk(self, sample_txt_path: Path) -> None:
        """Test creating a valid chunk."""
        metadata = ChunkMetadata(
            document_id="doc123",
            document_path=sample_txt_path,
            file_hash="a" * 64,
            content_hash="b" * 64,
            chunk_position=0,
            total_chunks=1,
            overlap_with_previous=0,
            overlap_with_next=0,
        )

        chunk = Chunk(
            text="This is a test chunk.",
            tokens=5,
            position=0,
            document_id="doc123",
            metadata=metadata,
        )

        assert chunk.text == "This is a test chunk."
        assert chunk.tokens == 5
        assert chunk.chunk_id is not None  # Auto-generated

    def test_empty_text(self, sample_txt_path: Path) -> None:
        """Test that empty text raises error."""
        metadata = ChunkMetadata(
            document_id="doc123",
            document_path=sample_txt_path,
            file_hash="a" * 64,
            content_hash="b" * 64,
            chunk_position=0,
            total_chunks=1,
            overlap_with_previous=0,
            overlap_with_next=0,
        )

        with pytest.raises(ValidationError):
            Chunk(
                text="",  # Empty
                tokens=0,
                position=0,
                document_id="doc123",
                metadata=metadata,
            )

    def test_chunk_repr(self, sample_txt_path: Path) -> None:
        """Test chunk string representation."""
        metadata = ChunkMetadata(
            document_id="doc123",
            document_path=sample_txt_path,
            file_hash="a" * 64,
            content_hash="b" * 64,
            chunk_position=0,
            total_chunks=1,
            overlap_with_previous=0,
            overlap_with_next=0,
        )

        chunk = Chunk(
            text="Short text",
            tokens=2,
            position=0,
            document_id="doc123",
            metadata=metadata,
        )

        repr_str = repr(chunk)
        assert "Short text" in repr_str
        assert "tokens=2" in repr_str


class TestDocument:
    """Test suite for Document model."""

    def test_valid_document(self, sample_txt_path: Path) -> None:
        """Test creating a valid document."""
        metadata = DocumentMetadata(
            file_path=sample_txt_path,
            file_size=100,
            file_hash="a" * 64,
            content_hash="b" * 64,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
            format="txt",
        )

        doc = Document(content="Sample content", metadata=metadata)

        assert doc.content == "Sample content"
        assert doc.document_id is not None
        assert len(doc.chunks) == 0  # No chunks initially

    def test_from_file(self, sample_txt_path: Path) -> None:
        """Test creating document from file."""
        content = sample_txt_path.read_text()

        doc = Document.from_file(
            file_path=sample_txt_path,
            content=content,
            format="txt",
            title="Test Document",
        )

        assert doc.content == content
        assert doc.metadata.file_path == sample_txt_path
        assert doc.metadata.format == "txt"
        assert doc.metadata.title == "Test Document"
        assert doc.metadata.file_size > 0
        assert len(doc.metadata.file_hash) == 64

    def test_from_file_nonexistent(self, temp_dir: Path) -> None:
        """Test that from_file raises error for nonexistent file."""
        nonexistent = temp_dir / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            Document.from_file(
                file_path=nonexistent, content="content", format="txt"
            )

    def test_add_chunks(self, sample_txt_path: Path) -> None:
        """Test adding chunks to document."""
        doc = Document.from_file(
            file_path=sample_txt_path,
            content="Sample content",
            format="txt",
        )

        chunk_metadata = ChunkMetadata(
            document_id=doc.document_id,
            document_path=sample_txt_path,
            file_hash="a" * 64,
            content_hash="b" * 64,
            chunk_position=0,
            total_chunks=1,
            overlap_with_previous=0,
            overlap_with_next=0,
        )

        chunk = Chunk(
            text="Sample content",
            tokens=2,
            position=0,
            document_id=doc.document_id,
            metadata=chunk_metadata,
        )

        doc.add_chunks([chunk])

        assert len(doc.chunks) == 1
        assert doc.chunks[0].text == "Sample content"

    def test_document_repr(self, sample_txt_path: Path) -> None:
        """Test document string representation."""
        doc = Document.from_file(
            file_path=sample_txt_path,
            content="Sample",
            format="txt",
        )

        repr_str = repr(doc)
        assert sample_txt_path.name in repr_str
        assert "chunks=0" in repr_str
