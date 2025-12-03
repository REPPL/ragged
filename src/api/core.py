"""Core RAG service implementation.

Phase 0 Infrastructure: Unified service layer for all interfaces.

The RAGService class encapsulates all RAG business logic, providing:
- Direct API for CLI and agents (no HTTP overhead)
- Event bus integration for real-time updates
- User context for access control and personalisation
- Consistent behaviour across all interfaces

Design Principles:
- Single source of truth for RAG operations
- Interface-agnostic (no HTTP/FastAPI dependencies)
- Event-driven for observability
- User-aware for future multi-tenancy

Usage:
    >>> from ragged.api import get_rag_service
    >>>
    >>> # Get service (singleton)
    >>> service = get_rag_service()
    >>>
    >>> # Initialise (called once at startup)
    >>> await service.initialize()
    >>>
    >>> # Query documents
    >>> result = await service.query("What is RAG?")
    >>> print(result.answer)
    >>>
    >>> # Ingest documents
    >>> result = await service.ingest_file("/path/to/doc.pdf")
    >>> print(f"Created {result.chunks_created} chunks")
"""

import asyncio
import logging
import threading
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from ragged.api.errors import (
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
    RetrievalMethod,
    ServiceStatus,
    SourceInfo,
)
from ragged.auth.user import User, get_current_user
from ragged.core.events import (
    DocumentEvent,
    QueryEvent,
    SystemEvent,
    get_event_bus,
)

logger = logging.getLogger(__name__)


class RAGService:
    """Core RAG service providing unified API for all interfaces.

    This service encapsulates all RAG operations (query, ingest, manage)
    and can be used directly by CLI, agents, or wrapped by HTTP APIs.

    Thread Safety:
        The service is thread-safe for concurrent operations.
        Initialisation should be called once at startup.

    Event Integration:
        All operations publish events to the event bus for:
        - Real-time UI updates
        - Agent coordination
        - Audit logging
        - Performance monitoring

    Example:
        >>> service = RAGService()
        >>> await service.initialize()
        >>> result = await service.query("What is retrieval augmented generation?")
        >>> print(result.answer)
    """

    VERSION = "0.6.16"

    def __init__(self):
        """Initialise RAG service (components initialised later)."""
        self._settings = None
        self._embedder = None
        self._vector_store = None
        self._hybrid_retriever = None
        self._llm_client = None

        self._initialized = False
        self._lock = threading.RLock()
        self._start_time = datetime.now()

        self._event_bus = get_event_bus()

        logger.debug("RAGService created (not yet initialised)")

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialised and ready."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialise all service components.

        This method should be called once during application startup.
        It initialises embedders, vector stores, retrievers, and LLM clients.

        Raises:
            Exception: If critical components fail to initialise
        """
        if self._initialized:
            logger.debug("Service already initialised")
            return

        with self._lock:
            if self._initialized:
                return

            try:
                logger.info("Initialising RAG service components...")

                # Import here to avoid circular imports
                from ragged.config.settings import get_settings
                from ragged.embeddings.factory import get_embedder
                from ragged.generation.ollama_client import OllamaClient
                from ragged.retrieval.bm25 import BM25Retriever
                from ragged.retrieval.hybrid import HybridRetriever
                from ragged.retrieval.retriever import Retriever
                from ragged.storage.vector_store import VectorStore

                # Initialise settings
                self._settings = get_settings()
                logger.info("Settings loaded")

                # Initialise embedder
                self._embedder = get_embedder()
                logger.info(f"Embedder initialised: {self._settings.embedding_model}")

                # Initialise vector store
                self._vector_store = VectorStore()
                logger.info("Vector store connected")

                # Initialise retrievers
                vector_retriever = Retriever(
                    vector_store=self._vector_store,
                    embedder=self._embedder
                )
                bm25_retriever = BM25Retriever()
                self._hybrid_retriever = HybridRetriever(
                    vector_retriever=vector_retriever,
                    bm25_retriever=bm25_retriever
                )
                logger.info("Hybrid retriever initialised")

                # Initialise LLM client
                self._llm_client = OllamaClient()
                logger.info(f"LLM client initialised: {self._settings.llm_model}")

                self._initialized = True
                self._start_time = datetime.now()

                # Publish system event
                await self._event_bus.publish(SystemEvent(
                    event_type="system.started",
                    component="rag_service",
                    status="healthy",
                    message="RAG service initialised successfully",
                    severity="info",
                ))

                logger.info("RAG service initialised successfully")

            except Exception as e:
                logger.exception("Failed to initialise RAG service")

                # Publish failure event
                await self._event_bus.publish(SystemEvent(
                    event_type="system.error",
                    component="rag_service",
                    status="failed",
                    message=f"Initialisation failed: {str(e)}",
                    severity="critical",
                ))

                raise

    def _ensure_initialized(self) -> None:
        """Ensure service is initialised, raise error if not."""
        if not self._initialized:
            raise ServiceNotReadyError()

    # === Query Operations ===

    async def query(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID,
        user: User | None = None,
    ) -> QueryResult:
        """Execute a RAG query.

        Retrieves relevant documents and generates an answer using the LLM.

        Args:
            query: The search query text
            collection: Collection to search
            top_k: Number of results to retrieve
            retrieval_method: Method to use for retrieval
            user: User making the query (uses current user if not provided)

        Returns:
            QueryResult with answer and sources

        Raises:
            ServiceNotReadyError: If service is not initialised
            QueryError: If query processing fails
        """
        self._ensure_initialized()

        if user is None:
            user = get_current_user()

        start_time = time.time()

        # Publish query started event
        await self._event_bus.publish(QueryEvent(
            event_type="query.started",
            query_text=query,
            session_id=user.user_id,
        ))

        try:
            # Import prompts here to avoid circular imports
            from ragged.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt

            # Retrieve relevant chunks
            results = self._hybrid_retriever.retrieve(
                query=query,
                top_k=top_k
            )

            if not results:
                latency_ms = (time.time() - start_time) * 1000
                return QueryResult(
                    answer="I couldn't find any relevant documents to answer your question. "
                           "Please try uploading documents first or rephrase your query.",
                    sources=[],
                    retrieval_method=retrieval_method.value,
                    query=query,
                    latency_ms=latency_ms,
                    model=self._settings.llm_model if self._settings else None,
                )

            # Build prompt from results
            prompt = build_rag_prompt(query, results)

            # Generate answer
            answer = self._llm_client.generate(
                prompt=prompt,
                system=RAG_SYSTEM_PROMPT
            )

            # Format sources
            sources = []
            for i, result in enumerate(results):
                source = SourceInfo(
                    chunk_id=result.chunk_id,
                    document_id=result.metadata.get("document_id", result.chunk_id),
                    filename=result.metadata.get("filename", "unknown"),
                    chunk_index=result.metadata.get("chunk_index", i),
                    score=result.score,
                    text=result.text,
                    metadata=result.metadata,
                )
                sources.append(source)

            latency_ms = (time.time() - start_time) * 1000

            # Publish query completed event
            await self._event_bus.publish(QueryEvent(
                event_type="query.completed",
                query_text=query,
                session_id=user.user_id,
                latency_ms=int(latency_ms),
                result_count=len(sources),
            ))

            return QueryResult(
                answer=answer,
                sources=sources,
                retrieval_method=retrieval_method.value,
                query=query,
                latency_ms=latency_ms,
                model=self._settings.llm_model if self._settings else None,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            # Publish query failed event
            await self._event_bus.publish(QueryEvent(
                event_type="query.failed",
                query_text=query,
                session_id=user.user_id,
                latency_ms=int(latency_ms),
                error=str(e),
            ))

            logger.exception("Error processing query")
            raise QueryError(
                message=f"Error processing query: {str(e)}",
                query=query,
            ) from e

    async def query_stream(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID,
        user: User | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute a streaming RAG query.

        Yields status updates and tokens as they are generated.

        Args:
            query: The search query text
            collection: Collection to search
            top_k: Number of results to retrieve
            retrieval_method: Method to use for retrieval
            user: User making the query

        Yields:
            Dictionary events with type and data

        Raises:
            ServiceNotReadyError: If service is not initialised
            QueryError: If query processing fails
        """
        self._ensure_initialized()

        if user is None:
            user = get_current_user()

        start_time = time.time()

        try:
            from ragged.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt

            # Status: Retrieving
            yield {"event": "status", "data": {"message": "Retrieving documents..."}}

            # Retrieve relevant chunks
            results = self._hybrid_retriever.retrieve(
                query=query,
                top_k=top_k
            )

            # Status: Retrieved
            yield {
                "event": "retrieved",
                "data": {"count": len(results), "method": retrieval_method.value}
            }

            if not results:
                yield {"event": "status", "data": {"message": "No relevant documents found"}}
                yield {"event": "complete", "data": {"total_time": time.time() - start_time}}
                return

            # Build prompt from results
            prompt = build_rag_prompt(query, results)

            # Status: Generating
            yield {"event": "status", "data": {"message": "Generating answer..."}}

            # Generate answer (streaming)
            answer_stream = self._llm_client.generate_stream(
                prompt=prompt,
                system=RAG_SYSTEM_PROMPT
            )

            for token in answer_stream:
                yield {"event": "token", "data": {"token": token}}

            # Format sources
            sources = []
            for i, result in enumerate(results):
                source = {
                    "id": result.chunk_id,
                    "filename": result.metadata.get("filename", "unknown"),
                    "chunk_index": result.metadata.get("chunk_index", i),
                    "score": result.score,
                    "excerpt": result.text[:200] + "..." if len(result.text) > 200 else result.text
                }
                sources.append(source)

            yield {"event": "sources", "data": sources}

            # Complete
            total_time = time.time() - start_time
            yield {"event": "complete", "data": {"total_time": total_time}}

        except Exception as e:
            logger.exception("Error during streaming query")
            yield {"event": "error", "data": {"error": str(e)}}

    # === Ingestion Operations ===

    async def ingest_file(
        self,
        file_path: str | Path,
        collection: str = "default",
        user: User | None = None,
    ) -> IngestionResult:
        """Ingest a document file.

        Loads, chunks, embeds, and stores a document.

        Args:
            file_path: Path to the document file
            collection: Target collection
            user: User performing the ingestion

        Returns:
            IngestionResult with ingestion details

        Raises:
            ServiceNotReadyError: If service is not initialised
            IngestionError: If ingestion fails
        """
        self._ensure_initialized()

        if user is None:
            user = get_current_user()

        file_path = Path(file_path)
        start_time = time.time()
        document_id = str(uuid.uuid4())

        # Validate file
        allowed_extensions = {".pdf", ".txt", ".md", ".html", ".docx"}
        if file_path.suffix.lower() not in allowed_extensions:
            raise IngestionError(
                message=f"Unsupported file type: {file_path.suffix}. "
                        f"Allowed: {allowed_extensions}",
                filename=file_path.name,
            )

        if not file_path.exists():
            raise IngestionError(
                message=f"File not found: {file_path}",
                filename=file_path.name,
            )

        # Publish ingestion started event
        await self._event_bus.publish(DocumentEvent(
            event_type="document.ingest_started",
            document_id=document_id,
            document_path=str(file_path),
            action="ingest",
        ))

        try:
            from ragged.chunking.splitters import chunk_document
            from ragged.ingestion.loaders import load_document

            # Load document
            logger.info(f"Loading document: {file_path.name}")
            document = load_document(file_path)

            # Chunk document
            logger.info(f"Chunking document: {file_path.name}")
            document = chunk_document(document)
            chunks = document.chunks

            if not chunks:
                raise IngestionError(
                    message=f"No content could be extracted from {file_path.name}",
                    filename=file_path.name,
                )

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            texts = [chunk.text for chunk in chunks]

            try:
                embeddings = self._embedder.embed_batch(texts)
            except Exception as e:
                raise EmbeddingError(
                    message=f"Failed to generate embeddings: {str(e)}",
                    model=self._settings.embedding_model if self._settings else None,
                ) from e

            # Store in vector database
            logger.info(f"Storing {len(chunks)} chunks in vector store")
            metadatas = []
            doc_ids = []
            for chunk in chunks:
                metadata = chunk.metadata.model_dump()
                metadata["document_id"] = document_id
                metadatas.append(metadata)
                doc_ids.append(chunk.chunk_id)

            self._vector_store.add(
                ids=doc_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            # Update hybrid retriever with new data
            if self._hybrid_retriever:
                self._hybrid_retriever.update_bm25_index(
                    documents=texts,
                    doc_ids=doc_ids,
                    metadatas=metadatas
                )

            duration_ms = (time.time() - start_time) * 1000
            file_size = file_path.stat().st_size

            # Publish ingestion completed event
            await self._event_bus.publish(DocumentEvent(
                event_type="document.ingest_completed",
                document_id=document_id,
                document_path=str(file_path),
                action="ingest",
                chunk_count=len(chunks),
            ))

            logger.info(f"Successfully ingested {file_path.name}")

            return IngestionResult(
                document_id=document_id,
                filename=file_path.name,
                chunks_created=len(chunks),
                size_bytes=file_size,
                collection=collection,
                status="success",
                message=f"Successfully ingested {len(chunks)} chunks",
                duration_ms=duration_ms,
            )

        except (IngestionError, EmbeddingError):
            raise
        except Exception as e:
            # Publish ingestion failed event
            await self._event_bus.publish(DocumentEvent(
                event_type="document.ingest_failed",
                document_id=document_id,
                document_path=str(file_path),
                action="ingest",
            ))

            logger.exception(f"Error ingesting {file_path.name}")
            raise IngestionError(
                message=f"Error ingesting document: {str(e)}",
                filename=file_path.name,
            ) from e

    async def ingest_text(
        self,
        text: str,
        filename: str = "inline_text.txt",
        collection: str = "default",
        user: User | None = None,
    ) -> IngestionResult:
        """Ingest text content directly.

        Useful for agent-generated content or clipboard data.

        Args:
            text: Text content to ingest
            filename: Virtual filename for the content
            collection: Target collection
            user: User performing the ingestion

        Returns:
            IngestionResult with ingestion details
        """
        self._ensure_initialized()

        import tempfile

        # Write text to temporary file and ingest
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False
        ) as f:
            f.write(text)
            temp_path = Path(f.name)

        try:
            result = await self.ingest_file(
                file_path=temp_path,
                collection=collection,
                user=user,
            )
            # Override filename
            result.filename = filename
            return result
        finally:
            temp_path.unlink(missing_ok=True)

    # === Collection Operations ===

    async def list_collections(self) -> list[CollectionInfo]:
        """List available collections.

        Returns:
            List of collection information
        """
        self._ensure_initialized()

        # Single-collection implementation (multi-collection planned for v1.0)
        # Currently returns a unified default collection
        return [
            CollectionInfo(
                name="default",
                document_count=0,
                chunk_count=self._vector_store.count() if self._vector_store else 0,
            )
        ]

    async def get_collection(self, name: str) -> CollectionInfo | None:
        """Get information about a specific collection.

        Args:
            name: Collection name

        Returns:
            CollectionInfo if found, None otherwise
        """
        collections = await self.list_collections()
        for collection in collections:
            if collection.name == name:
                return collection
        return None

    async def clear_collection(self, name: str) -> bool:
        """Clear all documents from a collection.

        Args:
            name: Collection name

        Returns:
            True if collection was cleared
        """
        self._ensure_initialized()

        # Collection clearing not yet implemented (planned for v1.0)
        raise NotImplementedError(
            f"Collection clearing not yet implemented: {name}. "
            "Multi-collection support planned for v1.0."
        )

    # === Health & Status ===

    async def health_check(self) -> HealthStatus:
        """Check service health.

        Returns:
            HealthStatus with component statuses
        """
        services = []

        # API service
        services.append(ServiceStatus(
            name="api",
            status="healthy" if self._initialized else "not_initialized",
        ))

        # Retriever
        services.append(ServiceStatus(
            name="retriever",
            status="healthy" if self._hybrid_retriever else "not_initialized",
        ))

        # LLM
        services.append(ServiceStatus(
            name="llm",
            status="healthy" if self._llm_client else "not_initialized",
        ))

        # Embedder
        services.append(ServiceStatus(
            name="embedder",
            status="healthy" if self._embedder else "not_initialized",
        ))

        # Determine overall status
        statuses = [s.status for s in services]
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        uptime = (datetime.now() - self._start_time).total_seconds()

        return HealthStatus(
            status=overall_status,
            version=self.VERSION,
            services=services,
            uptime_seconds=uptime,
        )


# === Global Service Instance ===


_rag_service: RAGService | None = None
_rag_service_lock = threading.Lock()


def get_rag_service() -> RAGService:
    """Get the global RAG service instance.

    Returns the same RAGService instance on subsequent calls.
    Thread-safe singleton pattern.

    Note: Call service.initialize() before using the service.

    Returns:
        RAGService: The global RAG service instance

    Example:
        >>> from ragged.api import get_rag_service
        >>> service = get_rag_service()
        >>> await service.initialize()
        >>> result = await service.query("What is RAG?")
    """
    global _rag_service

    if _rag_service is None:
        with _rag_service_lock:
            if _rag_service is None:
                _rag_service = RAGService()
                logger.info("Global RAGService created")

    return _rag_service


def reset_rag_service() -> None:
    """Reset the global RAG service (for testing).

    Creates a new RAGService instance, discarding all state.
    """
    global _rag_service

    with _rag_service_lock:
        _rag_service = RAGService()
        logger.info("Global RAGService reset")
