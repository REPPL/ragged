"""FastAPI application for ragged v0.2."""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from src.web.models import (
    QueryRequest,
    QueryResponse,
    Source,
    UploadResponse,
    HealthResponse,
    ErrorResponse,
)

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

# Global state (will be initialized on startup)
_hybrid_retriever: Optional[object] = None
_llm_client: Optional[object] = None


@app.on_event("startup")
async def startup_event():
    """Initialize retrievers and LLM client on startup."""
    # Note: In production, these would be properly initialized
    # For now, we'll handle gracefully if not available
    pass


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    services = {
        "api": "healthy",
        "retriever": "healthy" if _hybrid_retriever else "not_initialized",
        "llm": "healthy" if _llm_client else "not_initialized",
    }

    all_healthy = all(s == "healthy" for s in services.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        version="0.2.0",
        services=services
    )


@app.post("/api/query")
async def query(request: QueryRequest):
    """Query endpoint with optional SSE streaming.

    Retrieves relevant documents using hybrid search and generates
    an answer using the LLM.
    """
    start_time = time.time()

    if request.stream:
        async def stream_response():
            # Status: Retrieving
            yield f"event: status\n"
            yield f"data: {json.dumps({'message': 'Retrieving documents...'})}\n\n"
            await asyncio.sleep(0.1)

            # Status: Retrieved (placeholder)
            yield f"event: retrieved\n"
            yield f"data: {json.dumps({'count': request.top_k, 'method': request.retrieval_method})}\n\n"

            # Status: Generating
            yield f"event: status\n"
            yield f"data: {json.dumps({'message': 'Generating answer...'})}\n\n"

            # Stream answer tokens (placeholder)
            answer = f"This is a placeholder answer for query: '{request.query}' using {request.retrieval_method} retrieval."
            for token in answer.split():
                yield f"event: token\n"
                yield f"data: {json.dumps({'token': token + ' '})}\n\n"
                await asyncio.sleep(0.05)

            # Sources (placeholder)
            sources = [
                {
                    "id": "chunk_1",
                    "filename": "example.pdf",
                    "chunk_index": 0,
                    "score": 0.85,
                    "excerpt": "Example excerpt..."
                }
            ]
            yield f"event: sources\n"
            yield f"data: {json.dumps(sources)}\n\n"

            # Complete
            total_time = time.time() - start_time
            yield f"event: complete\n"
            yield f"data: {json.dumps({'total_time': total_time})}\n\n"

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:
        # Non-streaming response (placeholder)
        answer = f"This is a placeholder answer for: '{request.query}'"
        sources = [
            Source(
                id="chunk_1",
                filename="example.pdf",
                chunk_index=0,
                score=0.85,
                excerpt="Example excerpt from document..."
            )
        ]

        total_time = time.time() - start_time

        return QueryResponse(
            answer=answer,
            sources=sources,
            retrieval_method=request.retrieval_method,
            total_time=total_time
        )


@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    """Document upload endpoint.

    Accepts PDF, TXT, MD, HTML files and ingests them into the collection.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".txt", ".md", ".html"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    # Read file content
    content = await file.read()

    # Placeholder: In production, this would process and ingest the document
    return UploadResponse(
        filename=file.filename,
        size=len(content),
        status="success",
        message=f"File {file.filename} uploaded successfully (placeholder)"
    )


@app.get("/api/collections")
async def list_collections():
    """List available collections."""
    # Placeholder
    return {"collections": ["default"]}


@app.delete("/api/collections/{collection_name}")
async def clear_collection(collection_name: str):
    """Clear all documents from a collection."""
    # Placeholder
    return {"status": "success", "collection": collection_name, "message": "Collection cleared (placeholder)"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
