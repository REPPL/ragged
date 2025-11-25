"""API data models.

Phase 0 Infrastructure: Shared models for CLI, UI, and agent interfaces.

These models are designed to be:
- Interface-agnostic (no HTTP/FastAPI dependencies)
- Serialisable (to_dict methods for JSON/storage)
- Type-safe (dataclasses with validation)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class RetrievalMethod(Enum):
    """Retrieval method for queries."""

    VECTOR = "vector"  # Semantic/embedding-based
    BM25 = "bm25"  # Keyword/BM25-based
    HYBRID = "hybrid"  # Combined vector + BM25


@dataclass
class QueryRequest:
    """Request for a RAG query.

    Attributes:
        query: The search query text
        collection: Collection to search (default: "default")
        top_k: Number of results to retrieve (default: 5)
        retrieval_method: Method to use for retrieval
        include_sources: Whether to include source excerpts
        stream: Whether to stream the response
        user_id: User making the query (for personalisation)
    """

    query: str
    collection: str = "default"
    top_k: int = 5
    retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID
    include_sources: bool = True
    stream: bool = False
    user_id: str | None = None

    def __post_init__(self):
        """Validate query request."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")


@dataclass
class SourceInfo:
    """Information about a source document/chunk.

    Attributes:
        chunk_id: Unique chunk identifier
        document_id: Parent document identifier
        filename: Original filename
        chunk_index: Index within the document
        score: Relevance score (0-1)
        text: Full chunk text
        excerpt: Short excerpt for display
        metadata: Additional metadata
    """

    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    score: float
    text: str
    excerpt: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate excerpt if not provided."""
        if not self.excerpt and self.text:
            max_len = 200
            self.excerpt = self.text[:max_len] + "..." if len(self.text) > max_len else self.text

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "chunk_index": self.chunk_index,
            "score": self.score,
            "text": self.text,
            "excerpt": self.excerpt,
            "metadata": self.metadata,
        }


@dataclass
class QueryResult:
    """Result of a RAG query.

    Attributes:
        answer: Generated answer text
        sources: Source documents used
        retrieval_method: Method used for retrieval
        query: Original query
        latency_ms: Total processing time in milliseconds
        tokens_used: Tokens used for generation (if available)
        model: LLM model used
        timestamp: Query timestamp
    """

    answer: str
    sources: list[SourceInfo]
    retrieval_method: str
    query: str
    latency_ms: float = 0
    tokens_used: int | None = None
    model: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "retrieval_method": self.retrieval_method,
            "query": self.query,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class IngestionResult:
    """Result of document ingestion.

    Attributes:
        document_id: Unique document identifier
        filename: Original filename
        chunks_created: Number of chunks created
        size_bytes: File size in bytes
        collection: Target collection
        status: Ingestion status
        message: Status message
        duration_ms: Processing time in milliseconds
        timestamp: Ingestion timestamp
    """

    document_id: str
    filename: str
    chunks_created: int
    size_bytes: int
    collection: str
    status: Literal["success", "partial", "failed"]
    message: str = ""
    duration_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "chunks_created": self.chunks_created,
            "size_bytes": self.size_bytes,
            "collection": self.collection,
            "status": self.status,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DocumentInfo:
    """Information about an ingested document.

    Attributes:
        document_id: Unique document identifier
        filename: Original filename
        chunk_count: Number of chunks
        size_bytes: File size in bytes
        collection: Collection containing the document
        ingested_at: Ingestion timestamp
        metadata: Additional metadata
    """

    document_id: str
    filename: str
    chunk_count: int
    size_bytes: int
    collection: str
    ingested_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "chunk_count": self.chunk_count,
            "size_bytes": self.size_bytes,
            "collection": self.collection,
            "ingested_at": self.ingested_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CollectionInfo:
    """Information about a document collection.

    Attributes:
        name: Collection name
        document_count: Number of documents
        chunk_count: Total number of chunks
        created_at: Creation timestamp
        metadata: Additional metadata
    """

    name: str
    document_count: int
    chunk_count: int
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "name": self.name,
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


@dataclass
class ServiceStatus:
    """Status of a service component.

    Attributes:
        name: Service name
        status: Service status (healthy, degraded, unhealthy)
        message: Status message
        details: Additional status details
    """

    name: str
    status: Literal["healthy", "degraded", "unhealthy", "not_initialized"]
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Overall system health status.

    Attributes:
        status: Overall status
        version: System version
        services: Individual service statuses
        uptime_seconds: System uptime in seconds
        timestamp: Status check timestamp
    """

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    services: list[ServiceStatus]
    uptime_seconds: float = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "status": self.status,
            "version": self.version,
            "services": {s.name: s.status for s in self.services},
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
        }
