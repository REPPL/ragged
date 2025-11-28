"""Pydantic schemas for Document Library API.

Provides request/response models for document management endpoints:
- Document listing with filtering, sorting, and pagination
- Document metadata retrieval and updates
- Document preview and chunk access
- Bulk operations
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document metadata returned with document responses."""

    filename: str
    file_type: str | None = Field(None, description="MIME type or extension")
    file_size: int | None = Field(None, description="File size in bytes")
    created_at: datetime | None = Field(None, description="Document creation time")
    updated_at: datetime | None = Field(None, description="Last modification time")
    tags: list[str] = Field(default_factory=list, description="User-assigned tags")
    chunk_count: int = Field(0, description="Number of chunks in document")
    collection: str = Field("default", description="Collection name")
    custom: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom metadata"
    )


class DocumentResponse(BaseModel):
    """Response model for a single document."""

    id: str = Field(..., description="Document unique identifier")
    metadata: DocumentMetadata
    status: Literal["indexed", "processing", "failed"] = Field(
        "indexed", description="Document processing status"
    )


class ChunkResponse(BaseModel):
    """Response model for a document chunk."""

    id: str = Field(..., description="Chunk unique identifier")
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., ge=0, description="Position in document")
    content: str = Field(..., description="Chunk text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Chunk-specific metadata"
    )


class DocumentPreviewResponse(BaseModel):
    """Response model for document preview."""

    id: str = Field(..., description="Document unique identifier")
    filename: str
    preview: str = Field(..., description="Text preview (first 1000 characters)")
    total_length: int = Field(..., description="Total document text length")
    truncated: bool = Field(..., description="Whether preview was truncated")


class DocumentListParams(BaseModel):
    """Query parameters for document listing."""

    # Pagination
    limit: int = Field(
        default=50, ge=1, le=200, description="Maximum documents to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of documents to skip")

    # Filtering
    file_type: str | None = Field(None, description="Filter by file type/extension")
    tags: list[str] | None = Field(None, description="Filter by tags (any match)")
    collection: str = Field("default", description="Collection to list from")
    search: str | None = Field(None, description="Search in filename")
    created_after: datetime | None = Field(None, description="Filter by creation date")
    created_before: datetime | None = Field(None, description="Filter by creation date")

    # Sorting
    sort_by: Literal["filename", "created_at", "updated_at", "file_size"] = Field(
        default="created_at", description="Field to sort by"
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc", description="Sort direction"
    )


class DocumentListResponse(BaseModel):
    """Response model for document listing."""

    documents: list[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total matching documents")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")
    has_more: bool = Field(..., description="Whether more results exist")


class DocumentUpdateRequest(BaseModel):
    """Request model for updating document metadata."""

    tags: list[str] | None = Field(None, description="New tags (replaces existing)")
    custom: dict[str, Any] | None = Field(
        None, description="Custom metadata to merge"
    )


class BulkDeleteRequest(BaseModel):
    """Request model for bulk document deletion."""

    ids: list[str] = Field(
        ..., min_length=1, max_length=100, description="Document IDs to delete"
    )


class TagsResponse(BaseModel):
    """Response model for listing all tags."""

    tags: list[str] = Field(..., description="All unique tags across documents")
    count: int = Field(..., description="Number of unique tags")


class DocumentTypesResponse(BaseModel):
    """Response model for listing document types."""

    types: list[str] = Field(..., description="All unique file types")
    count: int = Field(..., description="Number of unique types")


class DeleteResponse(BaseModel):
    """Response model for delete operations."""

    deleted: int = Field(..., description="Number of documents deleted")
    ids: list[str] = Field(..., description="IDs of deleted documents")
