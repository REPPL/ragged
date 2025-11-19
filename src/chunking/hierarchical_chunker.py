"""
Hierarchical chunking with parent-child relationships.

Creates two levels of chunks:
- Parent chunks: Broader context (1500-3000 chars)
- Child chunks: Specific content (300-800 chars)

Child chunks link to their parent for improved context during generation.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.chunking.token_counter import count_tokens
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HierarchicalChunk:
    """
    Chunk with hierarchical metadata.

    Attributes:
        text: Chunk content
        chunk_id: Unique chunk identifier
        level: "parent" or "child"
        parent_id: ID of parent chunk (None for parents)
        parent_text: Full text of parent chunk (for context)
        child_ids: List of child IDs (for parents)
        position: Position in document
    """

    text: str
    chunk_id: str
    level: str  # "parent" or "child"
    parent_id: Optional[str] = None
    parent_text: Optional[str] = None
    child_ids: Optional[List[str]] = None
    position: int = 0


class HierarchicalChunker:
    """
    Chunker that creates parent-child chunk relationships.

    Parents provide broader context, children provide specific content for
    precise retrieval. When a child is retrieved, its parent is included in
    the LLM context for improved answer quality.
    """

    def __init__(
        self,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 500,
        parent_overlap: int = 200,
        child_overlap: int = 50,
    ):
        """
        Initialise hierarchical chunker.

        Args:
            parent_chunk_size: Target size for parent chunks (chars)
            child_chunk_size: Target size for child chunks (chars)
            parent_overlap: Overlap between parent chunks (chars)
            child_overlap: Overlap between child chunks (chars)
        """
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.parent_overlap = parent_overlap
        self.child_overlap = child_overlap

        # Validation
        if parent_chunk_size <= child_chunk_size:
            raise ValueError(
                f"parent_chunk_size ({parent_chunk_size}) must be > child_chunk_size ({child_chunk_size})"
            )

        # Get chunk_overlap from settings for compatibility with existing interface
        settings = get_settings()
        self.chunk_overlap = settings.chunk_overlap

        logger.info(
            f"HierarchicalChunker initialised (parent={parent_chunk_size}, child={child_chunk_size})"
        )

    def split_text(self, text: str) -> List[str]:
        """
        Split text into hierarchical chunks.

        Returns child chunks only (for backwards compatibility with existing interface).
        Parent chunks are stored in metadata.

        Args:
            text: Text to split

        Returns:
            List of child chunk texts (parent text stored in metadata)
        """
        hierarchical_chunks = self.create_hierarchy(text)

        # Return only child chunks for backwards compatibility
        child_chunks = [
            chunk.text for chunk in hierarchical_chunks if chunk.level == "child"
        ]

        return child_chunks

    def create_hierarchy(
        self, text: str, document_id: str = "doc"
    ) -> List[HierarchicalChunk]:
        """
        Create full parent-child hierarchy.

        Args:
            text: Text to chunk
            document_id: Document identifier for chunk IDs

        Returns:
            List of HierarchicalChunk objects (both parents and children)

        Example:
            >>> chunker = HierarchicalChunker()
            >>> hierarchy = chunker.create_hierarchy(document_text, "doc1")
            >>> parents = [c for c in hierarchy if c.level == "parent"]
            >>> children = [c for c in hierarchy if c.level == "child"]
        """
        if not text or len(text.strip()) == 0:
            return []

        try:
            # Step 1: Create parent chunks
            parent_texts = self._create_parent_chunks(text)

            # Step 2: For each parent, create child chunks
            all_chunks = []
            child_position = 0

            for parent_idx, parent_text in enumerate(parent_texts):
                parent_id = f"{document_id}_parent_{parent_idx}"

                # Create child chunks for this parent
                child_texts = self._create_child_chunks(parent_text)

                child_ids = []
                for child_idx, child_text in enumerate(child_texts):
                    child_id = f"{document_id}_child_{child_position}"
                    child_ids.append(child_id)

                    # Create child chunk
                    child_chunk = HierarchicalChunk(
                        text=child_text,
                        chunk_id=child_id,
                        level="child",
                        parent_id=parent_id,
                        parent_text=parent_text,  # Store parent for context
                        position=child_position,
                    )
                    all_chunks.append(child_chunk)
                    child_position += 1

                # Create parent chunk
                parent_chunk = HierarchicalChunk(
                    text=parent_text,
                    chunk_id=parent_id,
                    level="parent",
                    child_ids=child_ids,
                    position=parent_idx,
                )
                all_chunks.append(parent_chunk)

            logger.info(
                f"Created hierarchy: {len(parent_texts)} parents, {child_position} children"
            )

            return all_chunks

        except Exception as e:
            logger.error(f"Hierarchical chunking failed: {e}", exc_info=True)
            # Fallback: create simple chunks as children
            return self._fallback_chunks(text, document_id)

    def _create_parent_chunks(self, text: str) -> List[str]:
        """
        Create parent chunks (broader context).

        Args:
            text: Full text

        Returns:
            List of parent chunk texts
        """
        return self._split_with_overlap(
            text, self.parent_chunk_size, self.parent_overlap
        )

    def _create_child_chunks(self, parent_text: str) -> List[str]:
        """
        Create child chunks within a parent chunk.

        Args:
            parent_text: Parent chunk text

        Returns:
            List of child chunk texts
        """
        return self._split_with_overlap(
            parent_text, self.child_chunk_size, self.child_overlap
        )

    def _split_with_overlap(
        self, text: str, chunk_size: int, overlap: int
    ) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to split
            chunk_size: Target chunk size (chars)
            overlap: Overlap between chunks (chars)

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            # End position
            end = min(start + chunk_size, text_len)

            # Try to break at sentence boundary if not at end
            if end < text_len:
                # Look for sentence boundary near end
                boundary_match = re.search(r'[.!?]\s', text[max(end - 100, start):end])
                if boundary_match:
                    end = max(end - 100, start) + boundary_match.end()

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start forward by (chunk_size - overlap)
            start += chunk_size - overlap

            # Prevent infinite loop
            if start <= len(chunks[-1] if chunks else ""):
                start = end

        return chunks

    def _fallback_chunks(
        self, text: str, document_id: str
    ) -> List[HierarchicalChunk]:
        """
        Fallback to simple chunking if hierarchical fails.

        Args:
            text: Text to chunk
            document_id: Document ID

        Returns:
            List of simple chunks marked as children
        """
        logger.warning("Using fallback chunking for hierarchy")

        # Simple character-based chunks
        chunk_texts = self._split_with_overlap(
            text, self.child_chunk_size, self.child_overlap
        )

        chunks = []
        for i, chunk_text in enumerate(chunk_texts):
            chunk = HierarchicalChunk(
                text=chunk_text,
                chunk_id=f"{document_id}_child_{i}",
                level="child",
                position=i,
            )
            chunks.append(chunk)

        return chunks

    @staticmethod
    def get_parent_text(chunk: HierarchicalChunk) -> Optional[str]:
        """
        Get parent text for a child chunk.

        Args:
            chunk: Child chunk

        Returns:
            Parent text if available, None otherwise
        """
        if chunk.level == "child":
            return chunk.parent_text
        return None

    @staticmethod
    def format_with_parent(
        child_text: str, parent_text: Optional[str]
    ) -> str:
        """
        Format child text with parent context for LLM.

        Args:
            child_text: Child chunk text
            parent_text: Parent chunk text (if available)

        Returns:
            Formatted text with context

        Example:
            >>> formatted = HierarchicalChunker.format_with_parent(child, parent)
            >>> # Returns:
            >>> # '''
            >>> # BROADER CONTEXT:
            >>> # {parent text}
            >>> #
            >>> # SPECIFIC CONTENT:
            >>> # {child text}
            >>> # '''
        """
        if parent_text:
            return f"""BROADER CONTEXT:
{parent_text}

SPECIFIC CONTENT:
{child_text}"""
        else:
            return child_text
