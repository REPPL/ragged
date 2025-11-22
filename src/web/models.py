"""Pydantic models for API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str = Field(..., min_length=1, description="Search query")
    collection: str = Field(default="default", description="Collection name")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    retrieval_method: Literal["vector", "bm25", "hybrid"] = Field(
        default="hybrid",
        description="Retrieval method: vector (semantic), bm25 (keyword), or hybrid"
    )
    stream: bool = Field(default=True, description="Stream response via SSE")


class Source(BaseModel):
    """Source document information."""

    id: str
    filename: str
    chunk_index: int
    score: float
    excerpt: str = Field(..., description="Relevant text excerpt")


class QueryResponse(BaseModel):
    """Response model for query endpoint (non-streaming)."""

    answer: str
    sources: list[Source]
    retrieval_method: str
    total_time: float | None = None


class UploadResponse(BaseModel):
    """Response model for file upload."""

    filename: str
    size: int
    status: str
    message: str | None = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    services: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None
    status_code: int
