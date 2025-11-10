"""
Data models for document ingestion.

This module defines Pydantic models for documents, chunks, and metadata
with validation and type safety.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DocumentMetadata(BaseModel):
    """Metadata for an ingested document."""

    file_path: Path
    file_size: int = Field(gt=0, description="File size in bytes")
    file_hash: str = Field(description="SHA256 hash of file content")
    created_at: datetime
    modified_at: datetime
    format: str = Field(description="Document format (pdf, txt, md, html)")
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: Optional[int] = Field(default=None, gt=0)

    @field_validator("file_hash")
    @classmethod
    def validate_hash(cls, v: str) -> str:
        """Validate that hash is a valid SHA256 hex string."""
        if len(v) != 64:
            raise ValueError("file_hash must be a 64-character SHA256 hex string")
        try:
            int(v, 16)  # Verify it's valid hex
        except ValueError:
            raise ValueError("file_hash must be a valid hexadecimal string")
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
    chunk_position: int = Field(ge=0, description="0-indexed position in document")
    total_chunks: int = Field(gt=0, description="Total number of chunks in document")
    overlap_with_previous: int = Field(
        ge=0, description="Number of characters overlapping with previous chunk"
    )
    overlap_with_next: int = Field(
        ge=0, description="Number of characters overlapping with next chunk"
    )
    page_number: Optional[int] = Field(
        default=None, ge=1, description="Page number where this chunk starts (for PDFs)"
    )
    page_range: Optional[str] = Field(
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
    chunks: List[Chunk] = Field(default_factory=list)

    @classmethod
    def from_file(
        cls,
        file_path: Path,
        content: str,
        format: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        page_count: Optional[int] = None,
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

        # Generate hash
        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Create metadata
        metadata = DocumentMetadata(
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            created_at=datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc),
            modified_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
            format=format,
            title=title,
            author=author,
            page_count=page_count,
        )

        return cls(content=content, metadata=metadata)

    def add_chunks(self, chunks: List[Chunk]) -> None:
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
