"""
Document chunking orchestration and metadata creation.

v0.3.3: Updated to support intelligent chunking strategies (semantic, hierarchical)
"""

import re
from pathlib import Path
from typing import Any, Optional

from src.chunking.splitters.page_tracking import (
    build_page_position_map,
    estimate_page_from_position,
    map_chunks_to_pages,
)
from src.chunking.token_counter import count_tokens
from src.ingestion.models import Chunk, ChunkMetadata, Document
from src.utils.logging import get_logger

logger = get_logger(__name__)


def chunk_document(document: Document, splitter: Optional[Any] = None, strategy: str | None = None) -> Document:
    """
    Chunk a document and add chunk metadata with page tracking.

    v0.3.3: Supports multiple chunking strategies via ChunkerFactory.

    Args:
        document: Document to chunk
        splitter: Optional custom splitter (overrides strategy parameter)
        strategy: Chunking strategy ("fixed", "semantic", "hierarchical")
                 If None and splitter is None, uses settings.chunking_strategy

    Returns:
        Document with chunks added

    Example:
        >>> # Use configured strategy
        >>> doc = chunk_document(document)
        >>>
        >>> # Override with specific strategy
        >>> doc = chunk_document(document, strategy="semantic")
        >>>
        >>> # Provide custom splitter
        >>> custom_splitter = SemanticChunker(similarity_threshold=0.8)
        >>> doc = chunk_document(document, splitter=custom_splitter)
    """
    # Lazy import to avoid circular dependencies
    if splitter is None:
        from src.chunking.factory import ChunkerFactory
        splitter = ChunkerFactory.create_chunker(strategy)

    logger.info(f"Chunking document: {document.document_id}")

    # Build page position map from original content
    original_content = document.content
    page_positions = build_page_position_map(original_content)

    # Remove page markers for chunking
    clean_content = re.sub(r'<!-- PAGE \d+ -->\n?', '', original_content)

    # Split content (using cleaned content without markers)
    text_chunks = splitter.split_text(clean_content)
    total_chunks = len(text_chunks)

    logger.info(f"Created {total_chunks} chunks")

    # Map chunks to their page numbers
    chunk_pages = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

    # Get total pages for fallback estimation
    # Keep None for documents without pages (TXT, MD, HTML)
    total_pages = document.metadata.page_count

    # Create Chunk objects with metadata
    chunks = []
    for i, text in enumerate(text_chunks):
        # Get page info for this chunk
        page_number, page_range = chunk_pages[i] if i < len(chunk_pages) else (None, None)

        # Fallback: estimate page if not found AND document has pages (PDF)
        # TXT/MD/HTML files have page_count=None, so they'll keep page_number=None (correct)
        if page_number is None and total_pages is not None and total_pages > 0:
            page_number = estimate_page_from_position(i, total_chunks, total_pages)

        # Get overlap value (may not exist for all chunker types)
        # Semantic chunkers don't use traditional overlap
        chunk_overlap = getattr(splitter, 'chunk_overlap', 0)

        chunk_metadata = ChunkMetadata(
            document_id=document.document_id,
            document_path=document.metadata.file_path,
            file_hash=document.metadata.file_hash,
            content_hash=document.metadata.content_hash,
            chunk_position=i,
            total_chunks=total_chunks,
            overlap_with_previous=0 if i == 0 else chunk_overlap,
            overlap_with_next=0 if i == total_chunks - 1 else chunk_overlap,
            page_number=page_number,
            page_range=page_range,
        )

        chunk = Chunk(
            text=text,
            tokens=count_tokens(text),
            position=i,
            document_id=document.document_id,
            metadata=chunk_metadata,
        )
        chunks.append(chunk)

    # Add chunks to document
    document.add_chunks(chunks)

    return document


def create_chunk_metadata(
    document_id: str,
    document_path: Path,
    file_hash: str,
    content_hash: str,
    position: int,
    total_chunks: int,
    previous_text: str = "",
    next_text: str = "",
) -> ChunkMetadata:
    """Create metadata for a chunk."""
    # Calculate overlap
    overlap_prev = 0
    overlap_next = 0

    # Simple overlap calculation (could be more sophisticated)
    if previous_text:
        overlap_prev = min(len(previous_text), 100)
    if next_text:
        overlap_next = min(len(next_text), 100)

    return ChunkMetadata(
        document_id=document_id,
        document_path=document_path,
        file_hash=file_hash,
        content_hash=content_hash,
        chunk_position=position,
        total_chunks=total_chunks,
        overlap_with_previous=overlap_prev,
        overlap_with_next=overlap_next,
    )
