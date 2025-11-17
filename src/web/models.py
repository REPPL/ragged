"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


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
    sources: List[Source]
    retrieval_method: str
    total_time: Optional[float] = None


class UploadResponse(BaseModel):
    """Response model for file upload."""

    filename: str
    size: int
    status: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    services: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: Optional[str] = None
    status_code: int
