"""FastAPI application for ragged v0.2."""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union, cast

from src.chunking.splitters import chunk_document
from src.config.settings import Settings, get_settings
from src.embeddings.base import BaseEmbedder
from src.embeddings.factory import get_embedder
from src.generation.ollama_client import OllamaClient
from src.generation.prompts import build_rag_prompt, RAG_SYSTEM_PROMPT
from src.ingestion.loaders import load_document
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.retriever import Retriever
from src.retrieval.bm25 import BM25Retriever
from src.storage.vector_store import VectorStore
from src.utils.logging import get_logger
from src.web.models import (
    QueryRequest,
    QueryResponse,
    Source,
    UploadResponse,
    HealthResponse,
    ErrorResponse,
)

logger = get_logger(__name__)

app = FastAPI(
    title="ragged API",
    version="0.2.0",
    description="Privacy-first local RAG system with hybrid retrieval"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (initialized on startup)
_settings: Optional[Settings] = None
_embedder: Optional[BaseEmbedder] = None
_vector_store: Optional[VectorStore] = None
_hybrid_retriever: Optional[HybridRetriever] = None
_llm_client: Optional[OllamaClient] = None


@app.on_event("startup")
async def startup_event() -> None:
    """Initialise retrievers and LLM client on startup."""
    global _settings, _embedder, _vector_store, _hybrid_retriever, _llm_client

    try:
        logger.info("Initialising ragged API services...")

        # Initialise settings
        _settings = get_settings()
        logger.info("Settings loaded")

        # Initialise embedder
        _embedder = get_embedder()
        logger.info(f"Embedder initialised: {_settings.embedding_model}")

        # Initialise vector store
        _vector_store = VectorStore()
        logger.info("Vector store connected")

        # Initialise retrievers
        vector_retriever = Retriever(vector_store=_vector_store, embedder=_embedder)
        bm25_retriever = BM25Retriever()
        _hybrid_retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever
        )
        logger.info("Hybrid retriever initialised")

        # Initialise LLM client
        _llm_client = OllamaClient()
        logger.info(f"LLM client initialised: {_settings.llm_model}")

        logger.info("All services initialised successfully")

    except Exception:  # noqa: BLE001 - Allow API to start even if services fail
        logger.exception("Failed to initialise services")
        # Services will be None, API will return appropriate errors


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    services = {
        "api": "healthy",
        "retriever": "healthy" if _hybrid_retriever else "not_initialized",
        "llm": "healthy" if _llm_client else "not_initialized",
    }

    all_healthy = all(s == "healthy" for s in services.values())
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        version="0.2.0",
        services=services
    )


@app.post("/api/query", response_model=None)
async def query(request: QueryRequest) -> Union[StreamingResponse, QueryResponse]:
    """Query endpoint with optional SSE streaming.

    Retrieves relevant documents using hybrid search and generates
    an answer using the LLM.
    """
    # Check if services are initialized
    if not _hybrid_retriever or not _llm_client:
        raise HTTPException(
            status_code=503,
            detail="Services not initialised. Please wait for startup to complete."
        )

    start_time = time.time()

    try:
        if request.stream:
            async def stream_response() -> Any:
                """Stream RAG response with Server-Sent Events.

                Yields Server-Sent Events for real-time status updates and streaming response.
                Events include: status, retrieved, chunk (response chunks), and complete.

                Yields:
                    SSE-formatted strings with event type and JSON data

                Raises:
                    HTTPException: If retrieval or generation fails
                """
                try:
                    # Status: Retrieving
                    yield f"event: status\n"
                    yield f"data: {json.dumps({'message': 'Retrieving documents...'})}\n\n"

                    # Retrieve relevant chunks
                    results = _hybrid_retriever.retrieve(
                        query=request.query,
                        top_k=request.top_k
                    )

                    # Status: Retrieved
                    yield f"event: retrieved\n"
                    yield f"data: {json.dumps({'count': len(results), 'method': request.retrieval_method})}\n\n"

                    if not results:
                        yield f"event: status\n"
                        yield f"data: {json.dumps({'message': 'No relevant documents found'})}\n\n"
                        yield f"event: complete\n"
                        yield f"data: {json.dumps({'total_time': time.time() - start_time})}\n\n"
                        return

                    # Build prompt from results
                    prompt = build_rag_prompt(request.query, results)

                    # Status: Generating
                    yield f"event: status\n"
                    yield f"data: {json.dumps({'message': 'Generating answer...'})}\n\n"

                    # Generate answer (streaming)
                    answer_stream = _llm_client.generate_stream(
                        prompt=prompt,
                        system=RAG_SYSTEM_PROMPT
                    )

                    for token in answer_stream:
                        yield f"event: token\n"
                        yield f"data: {json.dumps({'token': token})}\n\n"

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

                    yield f"event: sources\n"
                    yield f"data: {json.dumps(sources)}\n\n"

                    # Complete
                    total_time = time.time() - start_time
                    yield f"event: complete\n"
                    yield f"data: {json.dumps({'total_time': total_time})}\n\n"

                except Exception as e:  # noqa: BLE001 - Send error event to client
                    logger.exception("Error during streaming query")
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(stream_response(), media_type="text/event-stream")
        else:
            # Non-streaming response
            # Retrieve relevant chunks
            results = _hybrid_retriever.retrieve(
                query=request.query,
                top_k=request.top_k
            )

            if not results:
                return QueryResponse(
                    answer="I couldn't find any relevant documents to answer your question. Please try uploading documents first or rephrase your query.",
                    sources=[],
                    retrieval_method=request.retrieval_method,
                    total_time=time.time() - start_time
                )

            # Build prompt from results
            prompt = build_rag_prompt(request.query, results)

            # Generate answer
            answer = _llm_client.generate(
                prompt=prompt,
                system=RAG_SYSTEM_PROMPT
            )

            # Format sources
            sources = [
                Source(
                    id=result.chunk_id,
                    filename=result.metadata.get("filename", "unknown"),
                    chunk_index=result.metadata.get("chunk_index", i),
                    score=result.score,
                    excerpt=result.text[:200] + "..." if len(result.text) > 200 else result.text
                )
                for i, result in enumerate(results)
            ]

            total_time = time.time() - start_time

            return QueryResponse(
                answer=answer,
                sources=sources,
                retrieval_method=request.retrieval_method,
                total_time=total_time
            )

    except Exception as e:  # noqa: BLE001 - Convert to HTTP exception
        logger.exception("Error processing query")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        ) from e


@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    """Document upload endpoint.

    Accepts PDF, TXT, MD, HTML files and ingests them into the collection.
    """
    # Check if services are initialized
    if not _embedder or not _vector_store:
        raise HTTPException(
            status_code=503,
            detail="Services not initialised. Please wait for startup to complete."
        )

    # Validate file type
    allowed_extensions = {".pdf", ".txt", ".md", ".html"}
    filename = file.filename or "unknown"
    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    # Read file content
    content = await file.read()

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        # Load document
        logger.info(f"Loading document: {file.filename}")
        document = load_document(temp_path)

        # Chunk document
        logger.info(f"Chunking document: {file.filename}")
        document = chunk_document(document)
        chunks = document.chunks

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail=f"No content could be extracted from {file.filename}"
            )

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        texts = [chunk.text for chunk in chunks]
        embeddings = _embedder.embed_batch(texts)

        # Store in vector database
        logger.info(f"Storing {len(chunks)} chunks in vector store")
        metadatas = [chunk.metadata.model_dump() for chunk in chunks]
        doc_ids = [chunk.chunk_id for chunk in chunks]
        _vector_store.add(
            ids=doc_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        # Update hybrid retriever with new data
        if _hybrid_retriever:
            _hybrid_retriever.update_bm25_index(
                documents=texts,
                doc_ids=doc_ids,
                metadatas=metadatas
            )

        logger.info(f"Successfully ingested {filename}")

        return UploadResponse(
            filename=filename,
            size=len(content),
            status="success",
            message=f"Successfully ingested {len(chunks)} chunks from {filename}"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:  # noqa: BLE001 - Convert to HTTP exception
        logger.exception(f"Error ingesting {filename}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting document: {str(e)}"
        ) from e
    finally:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/collections")
async def list_collections() -> Dict[str, Any]:
    """List available collections."""
    # Placeholder
    return {"collections": ["default"]}


@app.delete("/api/collections/{collection_name}")
async def clear_collection(collection_name: str) -> Dict[str, Any]:
    """Clear all documents from a collection."""
    # Placeholder
    return {"status": "success", "collection": collection_name, "message": "Collection cleared (placeholder)"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
