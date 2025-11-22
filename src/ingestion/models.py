"""
Data models for document ingestion.

This module defines Pydantic models for documents, chunks, and metadata
with validation and type safety.
"""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.utils.hashing import hash_content, hash_file_content


class DocumentMetadata(BaseModel):
    """Metadata for an ingested document."""

    file_path: Path
    file_size: int = Field(gt=0, description="File size in bytes")
    file_hash: str = Field(description="SHA256 hash of file content")
    content_hash: str = Field(description="SHA256 hash of first 1KB + last 1KB (for duplicate detection)")
    created_at: datetime
    modified_at: datetime
    format: str = Field(description="Document format (pdf, txt, md, html)")
    title: str | None = None
    author: str | None = None
    page_count: int | None = Field(default=None, gt=0)

    @field_validator("file_hash", "content_hash")
    @classmethod
    def validate_hash(cls, v: str) -> str:
        """Validate that hash is a valid SHA256 hex string."""
        if len(v) != 64:
            raise ValueError("Hash must be a 64-character SHA256 hex string")
        try:
            int(v, 16)  # Verify it's valid hex
        except ValueError:
            raise ValueError("Hash must be a valid hexadecimal string")
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate that format is supported."""
        valid_formats = {"pdf", "txt", "md", "html"}
        if v.lower() not in valid_formats:
            raise ValueError(f"format must be one of {valid_formats}, got {v}")
        return v.lower()

    model_config = ConfigDict(frozen=False)


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""

    document_id: str
    document_path: Path
    file_hash: str = Field(description="SHA256 hash of source document (full content)")
    content_hash: str = Field(description="SHA256 hash of partial content (for duplicate detection)")
    chunk_position: int = Field(ge=0, description="0-indexed position in document")
    total_chunks: int = Field(gt=0, description="Total number of chunks in document")
    overlap_with_previous: int = Field(
        ge=0, description="Number of characters overlapping with previous chunk"
    )
    overlap_with_next: int = Field(
        ge=0, description="Number of characters overlapping with next chunk"
    )
    page_number: int | None = Field(
        default=None, ge=1, description="Page number where this chunk starts (for PDFs)"
    )
    page_range: str | None = Field(
        default=None, description="Page range if chunk spans multiple pages (e.g., '5-7')"
    )

    @model_validator(mode="after")
    def validate_position_vs_total(self) -> "ChunkMetadata":
        """Validate that position is less than total chunks."""
        if self.chunk_position >= self.total_chunks:
            raise ValueError(
                f"chunk_position ({self.chunk_position}) must be less than "
                f"total_chunks ({self.total_chunks})"
            )
        return self


class Chunk(BaseModel):
    """A chunk of text from a document."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(min_length=1, description="Chunk text content")
    tokens: int = Field(gt=0, description="Number of tokens in chunk")
    position: int = Field(ge=0, description="Position in document")
    document_id: str
    metadata: ChunkMetadata

    def __repr__(self) -> str:
        """String representation showing truncated text."""
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Chunk(id={self.chunk_id[:8]}, tokens={self.tokens}, text='{preview}')"


class Document(BaseModel):
    """A document with content, metadata, and chunks."""

    document_id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(min_length=1, description="Full document content")
    metadata: DocumentMetadata
    chunks: list[Chunk] = Field(default_factory=list)

    @classmethod
    def from_file(
        cls,
        file_path: Path,
        content: str,
        format: str,
        title: str | None = None,
        author: str | None = None,
        page_count: int | None = None,
    ) -> "Document":
        """
        Create a Document from a file.

        Args:
            file_path: Path to the source file
            content: Extracted text content
            format: Document format (pdf, txt, md, html)
            title: Document title (optional)
            author: Document author (optional)
            page_count: Number of pages (optional, for PDFs)

        Returns:
            Document instance with metadata populated
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file stats
        stats = file_path.stat()
        file_size = stats.st_size

        # Generate full content hash
        file_hash = hash_content(content)

        # Generate partial content hash (first 1KB + last 1KB) for duplicate detection
        content_hash = hash_file_content(content, sample_size=1024)

        # Create metadata
        metadata = DocumentMetadata(
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            content_hash=content_hash,
            created_at=datetime.fromtimestamp(stats.st_ctime, tz=UTC),
            modified_at=datetime.fromtimestamp(stats.st_mtime, tz=UTC),
            format=format,
            title=title,
            author=author,
            page_count=page_count,
        )

        return cls(content=content, metadata=metadata)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Add chunks to the document.

        Args:
            chunks: List of chunks to add
        """
        self.chunks = chunks

    def __repr__(self) -> str:
        """String representation showing key info."""
        return (
            f"Document(id={self.document_id[:8]}, "
            f"path={self.metadata.file_path.name}, "
            f"chunks={len(self.chunks)})"
        )
