"""Document Library API router.

Provides endpoints for document management:
- List, filter, and paginate documents
- Get document details and previews
- Update document metadata
- Delete documents (single and bulk)
- List tags and document types

v0.9.0: Initial implementation
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ragged.storage.vector_store import VectorStore
from ragged.utils.logging import get_logger
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

logger = get_logger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_vector_store() -> VectorStore:
    """Dependency to get the global vector store instance.

    Returns:
        VectorStore: The initialised vector store

    Raises:
        HTTPException: If vector store is not initialised
    """
    # Import here to avoid circular imports
    from ragged.web import api

    if api._vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="Vector store not initialised. Please wait for startup to complete."
        )
    return api._vector_store


def _extract_document_id(chunk_id: str) -> str:
    """Extract document ID from chunk ID.

    Chunk IDs follow pattern: {doc_hash}_{chunk_index}
    Document ID is the hash portion.

    Args:
        chunk_id: Full chunk identifier

    Returns:
        Document identifier (hash portion)
    """
    parts = chunk_id.rsplit("_", 1)
    return parts[0] if len(parts) > 1 else chunk_id


def _build_document_response(
    doc_id: str,
    chunks_data: dict[str, Any],
) -> DocumentResponse | None:
    """Build a DocumentResponse from chunk data.

    Groups chunks by document ID and extracts metadata.

    Args:
        doc_id: Document identifier
        chunks_data: Raw chunk data from vector store

    Returns:
        DocumentResponse or None if no matching chunks
    """
    ids = chunks_data.get("ids", [])
    metadatas = chunks_data.get("metadatas", [])

    if not ids:
        return None

    # Find chunks belonging to this document
    doc_chunks = []
    for i, chunk_id in enumerate(ids):
        if _extract_document_id(chunk_id) == doc_id:
            doc_chunks.append({
                "id": chunk_id,
                "metadata": metadatas[i] if i < len(metadatas) else {}
            })

    if not doc_chunks:
        return None

    # Use first chunk's metadata as document metadata
    first_metadata = doc_chunks[0]["metadata"]

    # Parse dates from metadata if present
    created_at = None
    updated_at = None
    if created_str := first_metadata.get("created_at"):
        try:
            created_at = datetime.fromisoformat(created_str)
        except (ValueError, TypeError):
            pass
    if updated_str := first_metadata.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(updated_str)
        except (ValueError, TypeError):
            pass

    metadata = DocumentMetadata(
        filename=first_metadata.get("filename", "unknown"),
        file_type=first_metadata.get("file_type") or first_metadata.get("extension"),
        file_size=first_metadata.get("file_size"),
        created_at=created_at,
        updated_at=updated_at,
        tags=first_metadata.get("tags", []),
        chunk_count=len(doc_chunks),
        collection=first_metadata.get("collection", "default"),
        custom={
            k: v for k, v in first_metadata.items()
            if k not in {
                "filename", "file_type", "extension", "file_size",
                "created_at", "updated_at", "tags", "collection",
                "chunk_index", "chunk_id", "document_path"
            }
        }
    )

    return DocumentResponse(
        id=doc_id,
        metadata=metadata,
        status="indexed"
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum documents to return"),
    offset: int = Query(default=0, ge=0, description="Number of documents to skip"),
    file_type: str | None = Query(default=None, description="Filter by file type"),
    tags: list[str] | None = Query(default=None, description="Filter by tags"),
    collection: str = Query(default="default", description="Collection to list from"),
    search: str | None = Query(default=None, description="Search in filename"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", description="Sort direction"),
    vector_store: VectorStore = Depends(get_vector_store),
) -> DocumentListResponse:
    """List documents with filtering, sorting, and pagination.

    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        file_type: Filter by file type/extension
        tags: Filter by tags (any match)
        collection: Collection to list from
        search: Search in filename
        sort_by: Field to sort by
        sort_order: Sort direction (asc/desc)
        vector_store: Injected vector store dependency

    Returns:
        DocumentListResponse with paginated documents
    """
    try:
        # Build metadata filter
        where: dict[str, Any] | None = None
        if file_type:
            where = where or {}
            where["file_type"] = file_type
        if collection != "default":
            where = where or {}
            where["collection"] = collection

        # Get all chunks (we need to group by document)
        # Note: ChromaDB doesn't support full-text search on metadata,
        # so filename search is done in Python
        result = vector_store.list(limit=1000, offset=0, where=where)

        ids = result.get("ids", [])
        metadatas = result.get("metadatas", [])

        # Group chunks by document ID
        doc_map: dict[str, dict[str, Any]] = {}
        for i, chunk_id in enumerate(ids):
            doc_id = _extract_document_id(chunk_id)
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "ids": [],
                    "metadatas": []
                }
            doc_map[doc_id]["ids"].append(chunk_id)
            if i < len(metadatas):
                doc_map[doc_id]["metadatas"].append(metadatas[i])

        # Build document responses
        documents = []
        for doc_id, chunks_data in doc_map.items():
            doc_response = _build_document_response(doc_id, chunks_data)
            if doc_response:
                # Apply filename search filter
                if search and search.lower() not in doc_response.metadata.filename.lower():
                    continue
                # Apply tag filter (any match)
                if tags and not any(t in doc_response.metadata.tags for t in tags):
                    continue
                documents.append(doc_response)

        # Sort documents
        reverse = sort_order == "desc"
        if sort_by == "filename":
            documents.sort(key=lambda d: d.metadata.filename.lower(), reverse=reverse)
        elif sort_by == "file_size":
            documents.sort(key=lambda d: d.metadata.file_size or 0, reverse=reverse)
        elif sort_by == "created_at":
            documents.sort(
                key=lambda d: d.metadata.created_at or datetime.min,
                reverse=reverse
            )
        elif sort_by == "updated_at":
            documents.sort(
                key=lambda d: d.metadata.updated_at or datetime.min,
                reverse=reverse
            )

        # Apply pagination
        total = len(documents)
        paginated = documents[offset:offset + limit]

        return DocumentListResponse(
            documents=paginated,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total
        )

    except Exception as e:
        logger.exception("Error listing documents")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        ) from e


@router.get("/tags", response_model=TagsResponse)
async def list_tags(
    collection: str = Query(default="default", description="Collection to get tags from"),
    vector_store: VectorStore = Depends(get_vector_store),
) -> TagsResponse:
    """List all unique tags across documents.

    Args:
        collection: Collection to get tags from
        vector_store: Injected vector store dependency

    Returns:
        TagsResponse with unique tags
    """
    try:
        where = {"collection": collection} if collection != "default" else None
        result = vector_store.list(limit=10000, offset=0, where=where)

        metadatas = result.get("metadatas", [])

        # Collect unique tags
        tags_set: set[str] = set()
        for metadata in metadatas:
            if isinstance(metadata, dict):
                doc_tags = metadata.get("tags", [])
                if isinstance(doc_tags, list):
                    tags_set.update(doc_tags)

        tags = sorted(list(tags_set))

        return TagsResponse(
            tags=tags,
            count=len(tags)
        )

    except Exception as e:
        logger.exception("Error listing tags")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tags: {str(e)}"
        ) from e


@router.get("/types", response_model=DocumentTypesResponse)
async def list_document_types(
    collection: str = Query(default="default", description="Collection to get types from"),
    vector_store: VectorStore = Depends(get_vector_store),
) -> DocumentTypesResponse:
    """List all unique document types.

    Args:
        collection: Collection to get types from
        vector_store: Injected vector store dependency

    Returns:
        DocumentTypesResponse with unique types
    """
    try:
        where = {"collection": collection} if collection != "default" else None
        result = vector_store.list(limit=10000, offset=0, where=where)

        metadatas = result.get("metadatas", [])

        # Collect unique types
        types_set: set[str] = set()
        for metadata in metadatas:
            if isinstance(metadata, dict):
                file_type = metadata.get("file_type") or metadata.get("extension")
                if file_type:
                    types_set.add(file_type)

        types = sorted(list(types_set))

        return DocumentTypesResponse(
            types=types,
            count=len(types)
        )

    except Exception as e:
        logger.exception("Error listing document types")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing document types: {str(e)}"
        ) from e


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    vector_store: VectorStore = Depends(get_vector_store),
) -> DocumentResponse:
    """Get a single document by ID.

    Args:
        document_id: Document unique identifier
        vector_store: Injected vector store dependency

    Returns:
        DocumentResponse with document details

    Raises:
        HTTPException: If document not found
    """
    try:
        # Get all chunks for this document
        result = vector_store.list(limit=1000, offset=0)

        ids = result.get("ids", [])
        metadatas = result.get("metadatas", [])

        # Find chunks belonging to this document
        doc_chunks = {"ids": [], "metadatas": []}
        for i, chunk_id in enumerate(ids):
            if _extract_document_id(chunk_id) == document_id:
                doc_chunks["ids"].append(chunk_id)
                if i < len(metadatas):
                    doc_chunks["metadatas"].append(metadatas[i])

        if not doc_chunks["ids"]:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        doc_response = _build_document_response(document_id, doc_chunks)
        if not doc_response:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        return doc_response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting document")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document: {str(e)}"
        ) from e


@router.get("/{document_id}/preview", response_model=DocumentPreviewResponse)
async def get_document_preview(
    document_id: str,
    max_length: int = Query(default=1000, ge=100, le=5000, description="Maximum preview length"),
    vector_store: VectorStore = Depends(get_vector_store),
) -> DocumentPreviewResponse:
    """Get a text preview of a document.

    Args:
        document_id: Document unique identifier
        max_length: Maximum preview length in characters
        vector_store: Injected vector store dependency

    Returns:
        DocumentPreviewResponse with text preview

    Raises:
        HTTPException: If document not found
    """
    try:
        # Get all chunks for this document
        result = vector_store.list(limit=1000, offset=0)

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        # Collect chunks for this document, sorted by chunk index
        doc_chunks: list[tuple[int, str]] = []
        filename = "unknown"

        for i, chunk_id in enumerate(ids):
            if _extract_document_id(chunk_id) == document_id:
                chunk_index = 0
                if i < len(metadatas):
                    chunk_index = metadatas[i].get("chunk_index", 0)
                    if not filename or filename == "unknown":
                        filename = metadatas[i].get("filename", "unknown")
                text = documents[i] if i < len(documents) else ""
                doc_chunks.append((chunk_index, text))

        if not doc_chunks:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        # Sort by chunk index and concatenate
        doc_chunks.sort(key=lambda x: x[0])
        full_text = "\n".join(text for _, text in doc_chunks)
        total_length = len(full_text)

        # Truncate if needed
        truncated = len(full_text) > max_length
        preview = full_text[:max_length] if truncated else full_text

        return DocumentPreviewResponse(
            id=document_id,
            filename=filename,
            preview=preview,
            total_length=total_length,
            truncated=truncated
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting document preview")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document preview: {str(e)}"
        ) from e


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    vector_store: VectorStore = Depends(get_vector_store),
) -> list[ChunkResponse]:
    """Get all chunks for a document.

    Args:
        document_id: Document unique identifier
        vector_store: Injected vector store dependency

    Returns:
        List of ChunkResponse objects

    Raises:
        HTTPException: If document not found
    """
    try:
        # Get all chunks for this document
        result = vector_store.list(limit=1000, offset=0)

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        # Collect chunks for this document
        chunks: list[ChunkResponse] = []

        for i, chunk_id in enumerate(ids):
            if _extract_document_id(chunk_id) == document_id:
                chunk_index = 0
                metadata: dict[str, Any] = {}
                if i < len(metadatas):
                    metadata = metadatas[i]
                    chunk_index = metadata.get("chunk_index", 0)
                content = documents[i] if i < len(documents) else ""

                chunks.append(ChunkResponse(
                    id=chunk_id,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    content=content,
                    metadata=metadata
                ))

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        # Sort by chunk index
        chunks.sort(key=lambda c: c.chunk_index)

        return chunks

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting document chunks")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document chunks: {str(e)}"
        ) from e


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update: DocumentUpdateRequest,
    vector_store: VectorStore = Depends(get_vector_store),
) -> DocumentResponse:
    """Update document metadata.

    Args:
        document_id: Document unique identifier
        update: Metadata update request
        vector_store: Injected vector store dependency

    Returns:
        Updated DocumentResponse

    Raises:
        HTTPException: If document not found
    """
    try:
        # Get all chunks for this document
        result = vector_store.list(limit=1000, offset=0)

        ids = result.get("ids", [])
        metadatas = result.get("metadatas", [])

        # Find chunks belonging to this document
        chunk_ids: list[str] = []
        chunk_metadatas: list[dict[str, Any]] = []

        for i, chunk_id in enumerate(ids):
            if _extract_document_id(chunk_id) == document_id:
                chunk_ids.append(chunk_id)
                metadata = metadatas[i] if i < len(metadatas) else {}
                chunk_metadatas.append(metadata)

        if not chunk_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        # Update metadata for all chunks
        updated_metadatas: list[dict[str, Any]] = []
        for metadata in chunk_metadatas:
            updated = dict(metadata)
            if update.tags is not None:
                updated["tags"] = update.tags
            if update.custom is not None:
                updated.update(update.custom)
            updated["updated_at"] = datetime.now(UTC).isoformat()
            updated_metadatas.append(updated)

        # Update in vector store
        vector_store.update_metadata(chunk_ids, updated_metadatas)

        # Return updated document
        doc_response = _build_document_response(
            document_id,
            {"ids": chunk_ids, "metadatas": updated_metadatas}
        )
        if not doc_response:
            raise HTTPException(
                status_code=500,
                detail="Failed to build updated document response"
            )

        return doc_response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating document")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating document: {str(e)}"
        ) from e


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    vector_store: VectorStore = Depends(get_vector_store),
) -> DeleteResponse:
    """Delete a document and all its chunks.

    Args:
        document_id: Document unique identifier
        vector_store: Injected vector store dependency

    Returns:
        DeleteResponse with deletion result

    Raises:
        HTTPException: If document not found
    """
    try:
        # Get all chunks for this document
        result = vector_store.list(limit=1000, offset=0)

        ids = result.get("ids", [])

        # Find chunks belonging to this document
        chunk_ids = [
            chunk_id for chunk_id in ids
            if _extract_document_id(chunk_id) == document_id
        ]

        if not chunk_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        # Delete chunks
        vector_store.delete(ids=chunk_ids)

        logger.info(f"Deleted document {document_id} ({len(chunk_ids)} chunks)")

        return DeleteResponse(
            deleted=1,
            ids=[document_id]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting document")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        ) from e


@router.delete("", response_model=DeleteResponse)
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    vector_store: VectorStore = Depends(get_vector_store),
) -> DeleteResponse:
    """Delete multiple documents.

    Args:
        request: BulkDeleteRequest with document IDs
        vector_store: Injected vector store dependency

    Returns:
        DeleteResponse with deletion result
    """
    try:
        # Get all chunks
        result = vector_store.list(limit=10000, offset=0)
        ids = result.get("ids", [])

        # Find all chunk IDs for requested documents
        chunk_ids_to_delete: list[str] = []
        deleted_doc_ids: list[str] = []

        for doc_id in request.ids:
            doc_chunk_ids = [
                chunk_id for chunk_id in ids
                if _extract_document_id(chunk_id) == doc_id
            ]
            if doc_chunk_ids:
                chunk_ids_to_delete.extend(doc_chunk_ids)
                deleted_doc_ids.append(doc_id)

        if chunk_ids_to_delete:
            vector_store.delete(ids=chunk_ids_to_delete)
            logger.info(f"Bulk deleted {len(deleted_doc_ids)} documents ({len(chunk_ids_to_delete)} chunks)")

        return DeleteResponse(
            deleted=len(deleted_doc_ids),
            ids=deleted_doc_ids
        )

    except Exception as e:
        logger.exception("Error bulk deleting documents")
        raise HTTPException(
            status_code=500,
            detail=f"Error bulk deleting documents: {str(e)}"
        ) from e
