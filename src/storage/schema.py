"""
Dual embedding storage schema for text and vision embeddings.

This module defines the metadata structures and ID generation patterns
for storing both text embeddings (384-dim) and vision embeddings (128-dim)
in a unified ChromaDB collection.

The schema supports:
- Text embeddings from document chunks
- Vision embeddings from PDF pages
- Hybrid retrieval combining both modalities

v0.5.0: Initial dual embedding schema
"""

from datetime import datetime
from enum import Enum
from typing import TypedDict


class EmbeddingType(str, Enum):
    """Embedding type enumeration for dual storage."""

    TEXT = "text"
    VISION = "vision"


# Base metadata (shared by both types)


class BaseMetadata(TypedDict):
    """
    Base metadata for all embeddings.

    All embeddings (text and vision) share these common fields.
    """

    document_id: str  # Parent document UUID
    embedding_type: str  # EmbeddingType value ("text" or "vision")
    created_at: str  # ISO 8601 timestamp


# Text embedding metadata


class TextMetadata(BaseMetadata):
    """
    Metadata for text embeddings.

    Used for document chunks processed through text embedding models
    (e.g., all-MiniLM-L6-v2).
    """

    chunk_id: str  # Unique chunk identifier
    chunk_index: int  # Position in document (0-indexed)
    text_content: str  # Actual text content
    char_count: int  # Character count
    page_number: int | None  # Source page number (if available)


# Vision embedding metadata


class VisionMetadata(BaseMetadata):
    """
    Metadata for vision embeddings.

    Used for PDF pages processed through ColPali vision model.
    """

    page_number: int  # PDF page number (0-indexed for consistency)
    image_hash: str  # SHA-256 hash of rendered page image
    has_diagrams: bool  # Whether page contains diagrams/charts
    has_tables: bool  # Whether page contains tables
    layout_complexity: str  # "simple" | "moderate" | "complex"


# ID generation utilities


def generate_embedding_id(document_id: str, embedding_type: EmbeddingType, index: int) -> str:
    """
    Generate unique embedding identifier.

    Format:
    - Text: "{document_id}_chunk_{index}_text"
    - Vision: "{document_id}_page_{index}_vision"

    Args:
        document_id: Parent document UUID
        embedding_type: Type of embedding (TEXT or VISION)
        index: Chunk index (text) or page number (vision), 0-indexed

    Returns:
        Unique embedding ID

    Example:
        >>> generate_embedding_id("abc123", EmbeddingType.TEXT, 5)
        'abc123_chunk_5_text'
        >>> generate_embedding_id("abc123", EmbeddingType.VISION, 3)
        'abc123_page_3_vision'
    """
    if embedding_type == EmbeddingType.TEXT:
        return f"{document_id}_chunk_{index}_text"
    else:  # VISION
        return f"{document_id}_page_{index}_vision"


def create_text_metadata(
    document_id: str,
    chunk_id: str,
    chunk_index: int,
    text_content: str,
    page_number: int | None = None,
) -> TextMetadata:
    """
    Create metadata for text embedding.

    Args:
        document_id: Parent document UUID
        chunk_id: Unique chunk identifier
        chunk_index: Position in document (0-indexed)
        text_content: Actual text content
        page_number: Source page number (optional, 0-indexed)

    Returns:
        Complete text metadata dictionary

    Example:
        >>> metadata = create_text_metadata(
        ...     "doc_123", "chunk_5", 5, "Sample text content", page_number=2
        ... )
        >>> metadata["embedding_type"]
        'text'
        >>> metadata["chunk_index"]
        5
    """
    return TextMetadata(
        document_id=document_id,
        embedding_type=EmbeddingType.TEXT.value,
        created_at=datetime.utcnow().isoformat(),
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        text_content=text_content,
        char_count=len(text_content),
        page_number=page_number,
    )


def create_vision_metadata(
    document_id: str,
    page_number: int,
    image_hash: str,
    has_diagrams: bool = False,
    has_tables: bool = False,
    layout_complexity: str = "simple",
) -> VisionMetadata:
    """
    Create metadata for vision embedding.

    Args:
        document_id: Parent document UUID
        page_number: PDF page number (0-indexed)
        image_hash: SHA-256 hash of rendered page image
        has_diagrams: Whether page contains diagrams/charts
        has_tables: Whether page contains tables
        layout_complexity: Layout complexity ("simple", "moderate", "complex")

    Returns:
        Complete vision metadata dictionary

    Example:
        >>> metadata = create_vision_metadata(
        ...     "doc_123", 5, "abc123def456", has_diagrams=True, layout_complexity="complex"
        ... )
        >>> metadata["embedding_type"]
        'vision'
        >>> metadata["has_diagrams"]
        True
    """
    return VisionMetadata(
        document_id=document_id,
        embedding_type=EmbeddingType.VISION.value,
        created_at=datetime.utcnow().isoformat(),
        page_number=page_number,
        image_hash=image_hash,
        has_diagrams=has_diagrams,
        has_tables=has_tables,
        layout_complexity=layout_complexity,
    )


def parse_embedding_id(embedding_id: str) -> dict[str, str | int]:
    """
    Parse embedding ID to extract document ID, type, and index.

    Args:
        embedding_id: Embedding ID in standard format

    Returns:
        Dictionary with 'document_id', 'type', and 'index'

    Raises:
        ValueError: If ID format is invalid

    Example:
        >>> parse_embedding_id("abc123_chunk_5_text")
        {'document_id': 'abc123', 'type': 'text', 'index': 5}
        >>> parse_embedding_id("abc123_page_3_vision")
        {'document_id': 'abc123', 'type': 'vision', 'index': 3}
    """
    # Split from right to extract type
    parts = embedding_id.rsplit("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid embedding ID format: {embedding_id}")

    remaining, emb_type = parts

    # Validate type
    if emb_type not in ("text", "vision"):
        raise ValueError(f"Invalid embedding type in ID: {emb_type}")

    # Split again to extract index
    parts = remaining.rsplit("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid embedding ID format: {embedding_id}")

    remaining, index_str = parts

    # Extract index
    try:
        index = int(index_str)
    except ValueError as e:
        raise ValueError(f"Invalid index in embedding ID: {index_str}") from e

    # Split once more to remove "chunk" or "page" prefix
    parts = remaining.rsplit("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid embedding ID format: {embedding_id}")

    document_id, prefix = parts

    # Validate prefix matches type
    expected_prefix = "chunk" if emb_type == "text" else "page"
    if prefix != expected_prefix:
        raise ValueError(
            f"Invalid prefix '{prefix}' for embedding type '{emb_type}' "
            f"(expected '{expected_prefix}')"
        )

    return {"document_id": document_id, "type": emb_type, "index": index}
