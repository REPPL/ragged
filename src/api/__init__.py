"""Core API layer for ragged.

Phase 0 Infrastructure: Unified API interface enabling:
- Direct usage by CLI (no HTTP overhead)
- Agent tool integration (v0.9)
- WebUI backend (FastAPI wrapper)
- Consistent behaviour across all interfaces

Usage:
    >>> from ragged.api import RAGService, get_rag_service
    >>>
    >>> # Get service instance (singleton)
    >>> service = get_rag_service()
    >>>
    >>> # Query documents
    >>> result = await service.query("What is RAG?")
    >>> print(result.answer)
    >>>
    >>> # Ingest document
    >>> await service.ingest_file("/path/to/document.pdf")
"""

from ragged.api.core import RAGService, get_rag_service, reset_rag_service
from ragged.api.errors import (
    APIError,
    DocumentNotFoundError,
    EmbeddingError,
    IngestionError,
    QueryError,
    ServiceNotReadyError,
)
from ragged.api.models import (
    CollectionInfo,
    DocumentInfo,
    HealthStatus,
    IngestionResult,
    QueryRequest,
    QueryResult,
    ServiceStatus,
    SourceInfo,
)

__all__ = [
    # Service
    "RAGService",
    "get_rag_service",
    "reset_rag_service",
    # Errors
    "APIError",
    "ServiceNotReadyError",
    "QueryError",
    "IngestionError",
    "EmbeddingError",
    "DocumentNotFoundError",
    # Models
    "QueryRequest",
    "QueryResult",
    "SourceInfo",
    "IngestionResult",
    "DocumentInfo",
    "CollectionInfo",
    "HealthStatus",
    "ServiceStatus",
]
