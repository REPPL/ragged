"""Pydantic schemas for API endpoints.

This module provides request/response schemas organised by feature domain.
"""

from ragged.web.schemas.documents import (
    BulkDeleteRequest,
    ChunkResponse,
    DeleteResponse,
    DocumentListParams,
    DocumentListResponse,
    DocumentMetadata,
    DocumentPreviewResponse,
    DocumentResponse,
    DocumentTypesResponse,
    DocumentUpdateRequest,
    TagsResponse,
)

__all__ = [
    "BulkDeleteRequest",
    "ChunkResponse",
    "DeleteResponse",
    "DocumentListParams",
    "DocumentListResponse",
    "DocumentMetadata",
    "DocumentPreviewResponse",
    "DocumentResponse",
    "DocumentTypesResponse",
    "DocumentUpdateRequest",
    "TagsResponse",
]
