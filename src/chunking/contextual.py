"""Contextual chunking with document and section headers.

Enhances chunks with surrounding context for better retrieval and generation.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.chunking.splitters import RecursiveCharacterTextSplitter
from src.ingestion.models import Chunk, ChunkMetadata, Document
from src.utils.hashing import hash_content
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContextualChunk:
    """Chunk with additional context."""

    content: str
    document_context: str  # e.g., "From: research_paper.pdf"
    section_context: str | None = None  # e.g., "Section: Introduction"
    chunk_index: int = 0
    total_chunks: int = 0

    def to_enriched_text(self) -> str:
        """Convert to enriched text with context headers.

        Returns:
            Text with context prepended for better semantic understanding
        """
        parts = [f"[{self.document_context}]"]

        if self.section_context:
            parts.append(f"[{self.section_context}]")

        parts.append(f"\n{self.content}")

        return "\n".join(parts)

    def to_metadata(self) -> dict[str, Any]:
        """Convert to metadata dict.

        Returns:
            Metadata dictionary
        """
        return {
            "document_context": self.document_context,
            "section_context": self.section_context,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
        }


class ContextualChunker:
    """Chunker that adds document and section context to chunks.

    Improves retrieval by adding structural context to each chunk.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        add_document_context: bool = True,
        add_section_context: bool = True,
    ):
        """Initialize contextual chunker.

        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
            add_document_context: Whether to add document context headers
            add_section_context: Whether to detect and add section headers
        """
        self.base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.add_document_context = add_document_context
        self.add_section_context = add_section_context

    def _calculate_overlap(self, previous_chunk: str, current_chunk: str) -> int:
        """Calculate character overlap between consecutive chunks.

        Finds the longest suffix of previous_chunk that matches a prefix of current_chunk.

        Args:
            previous_chunk: Text of the previous chunk
            current_chunk: Text of the current chunk

        Returns:
            Number of overlapping characters
        """
        max_overlap = 0
        max_possible = min(len(previous_chunk), len(current_chunk))

        # Check all possible overlap lengths from longest to shortest
        for length in range(max_possible, 0, -1):
            if previous_chunk[-length:] == current_chunk[:length]:
                max_overlap = length
                break  # Found the longest match, no need to continue

        return max_overlap

    def chunk_document(self, document: Document) -> list[Chunk]:
        """Chunk a document with contextual enrichment.

        Args:
            document: Document to chunk

        Returns:
            List of enriched chunks
        """
        # Split into base chunks
        text_chunks = self.base_splitter.split_text(document.content)

        if not text_chunks:
            return []

        # Create contextual chunks
        contextual_chunks = []
        total_chunks = len(text_chunks)

        for i, text_chunk in enumerate(text_chunks):
            # Extract document context
            doc_context = self._get_document_context(document)

            # Extract section context
            section_context = None
            if self.add_section_context:
                section_context = self._extract_section_context(text_chunk)

            # Create contextual chunk
            ctx_chunk = ContextualChunk(
                content=text_chunk,
                document_context=doc_context,
                section_context=section_context,
                chunk_index=i,
                total_chunks=total_chunks
            )

            # Convert to enriched text
            enriched_text = ctx_chunk.to_enriched_text()

            # Create Chunk object with enriched content
            # Count tokens (simple whitespace split for now)
            token_count = len(enriched_text.split())

            # Calculate content hash for this chunk
            chunk_content_hash = hash_content(enriched_text)

            # Calculate overlap with previous chunk
            overlap_prev = 0
            if i > 0:
                overlap_prev = self._calculate_overlap(text_chunks[i - 1], text_chunk)

            # Calculate overlap with next chunk
            overlap_next = 0
            if i < len(text_chunks) - 1:
                overlap_next = self._calculate_overlap(text_chunk, text_chunks[i + 1])

            chunk = Chunk(
                chunk_id=f"{document.document_id}_chunk_{i}",
                text=enriched_text,  # Use enriched text for embedding
                tokens=max(1, token_count),  # Ensure at least 1 token
                position=i,
                document_id=document.document_id,
                metadata=ChunkMetadata(
                    document_id=document.document_id,
                    document_path=document.metadata.file_path,
                    file_hash=document.metadata.file_hash,
                    content_hash=chunk_content_hash,
                    chunk_position=i,
                    total_chunks=total_chunks,
                    overlap_with_previous=overlap_prev,
                    overlap_with_next=overlap_next
                )
            )

            contextual_chunks.append(chunk)

        logger.info(
            f"Created {len(contextual_chunks)} contextual chunks from document "
            f"{document.metadata.file_path}"
        )

        return contextual_chunks

    def _get_document_context(self, document: Document) -> str:
        """Extract document context string.

        Args:
            document: Source document

        Returns:
            Document context string
        """
        if not self.add_document_context:
            return ""

        # Use filename as context
        source_path = Path(document.metadata.file_path)
        filename = source_path.name

        # Add document type if available
        doc_type = document.metadata.format
        if doc_type:
            return f"From: {filename} ({doc_type})"

        return f"From: {filename}"

    def _extract_section_context(self, text: str) -> str | None:
        """Extract section context from chunk text.

        Looks for common section headers like:
        - # Heading (Markdown)
        - CHAPTER 1 (all caps)
        - 1. Introduction (numbered sections)

        Args:
            text: Chunk text

        Returns:
            Section context string or None
        """
        lines = text.strip().split('\n')

        for i, line in enumerate(lines[:5]):  # Check first 5 lines only
            line = line.strip()

            # Markdown headers
            if line.startswith('#'):
                header = line.lstrip('#').strip()
                return f"Section: {header}"

            # All-caps headers (INTRODUCTION, CHAPTER 1, etc.)
            if line.isupper() and len(line.split()) <= 6:
                return f"Section: {line.title()}"

            # Numbered sections (1. Introduction, 1.1 Overview)
            numbered_match = re.match(r'^[\d.]+\s+(.+)$', line)
            if numbered_match and i == 0:  # Only if at start
                return f"Section: {numbered_match.group(1)}"

        return None


class ContextCompressor:
    """Compress retrieved context for prompting.

    Reduces token usage while preserving key information.
    """

    def __init__(self, max_tokens: int = 2000):
        """Initialize context compressor.

        Args:
            max_tokens: Maximum tokens for compressed context
        """
        self.max_tokens = max_tokens

    def compress(
        self,
        chunks: list[Chunk],
        query: str,
        preserve_order: bool = True
    ) -> str:
        """Compress chunks into context string.

        Args:
            chunks: Retrieved chunks
            query: Original query
            preserve_order: Whether to preserve retrieval order

        Returns:
            Compressed context string
        """
        if not chunks:
            return ""

        # Build context from chunks
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            # Use chunk text
            text = chunk.text

            # Add source attribution
            source = chunk.metadata.document_path
            source_name = Path(source).name

            context_parts.append(f"[Source {i}: {source_name}]\n{text}\n")

        full_context = "\n---\n\n".join(context_parts)

        # TODO: Implement token-based truncation if needed
        # For now, return full context
        return full_context

    def compress_with_query_focus(
        self,
        chunks: list[Chunk],
        query: str
    ) -> str:
        """Compress context with focus on query-relevant sentences.

        Args:
            chunks: Retrieved chunks
            query: Original query

        Returns:
            Query-focused compressed context
        """
        # Simple implementation: return full chunks
        # Could be enhanced with sentence-level relevance scoring
        return self.compress(chunks, query)
