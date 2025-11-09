"""
Text splitting strategies for creating semantic chunks.
"""

from typing import List
from uuid import uuid4

from src.chunking.token_counter import count_tokens
from src.config.settings import get_settings
from src.ingestion.models import Chunk, ChunkMetadata, Document
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RecursiveCharacterTextSplitter:
    """Recursively split text into chunks, trying different separators."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None,
    ):
        """Initialize the text splitter."""
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})")

        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive splitting."""
        if not text:
            return []

        return self._split_recursive(text, self.separators)

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text by trying separators in order."""
        if not separators:
            # No more separators, split by character
            return self._split_by_characters(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split by current separator
        if separator:
            splits = text.split(separator)
        else:
            # Empty separator means split by character
            return self._split_by_characters(text)

        # Process splits
        chunks = []
        current_chunk = ""

        for split in splits:
            # Check token count
            test_chunk = current_chunk + (separator if current_chunk else "") + split
            token_count = count_tokens(test_chunk)

            if token_count <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is ready
                if current_chunk:
                    chunks.append(current_chunk)

                # Check if split itself is too large
                if count_tokens(split) > self.chunk_size:
                    # Recursively split this piece
                    sub_chunks = self._split_recursive(split, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split

        # Add remaining
        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap
        return self._add_overlap(chunks)

    def _split_by_characters(self, text: str) -> List[str]:
        """Split text by character count."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Estimate character count for chunk_size tokens
            char_estimate = self.chunk_size * 4  # ~4 chars per token

            end = min(start + char_estimate, text_length)
            chunk = text[start:end]

            # Adjust if we exceeded token limit
            while count_tokens(chunk) > self.chunk_size and len(chunk) > 1:
                end = start + int(len(chunk) * 0.9)
                chunk = text[start:end]

            chunks.append(chunk)
            start = end

        return self._add_overlap(chunks)

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between chunks."""
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks

        overlapped = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # Get overlap from previous chunk
            overlap_chars = self.chunk_overlap * 4  # Rough estimate
            overlap_text = prev_chunk[-overlap_chars:] if len(prev_chunk) > overlap_chars else prev_chunk

            # Prepend overlap to current chunk
            overlapped_chunk = overlap_text + " " + curr_chunk
            overlapped.append(overlapped_chunk)

        return overlapped


def chunk_document(document: Document, splitter: RecursiveCharacterTextSplitter = None) -> Document:
    """Chunk a document and add chunk metadata."""
    if splitter is None:
        splitter = RecursiveCharacterTextSplitter()

    logger.info(f"Chunking document: {document.document_id}")

    # Split content
    text_chunks = splitter.split_text(document.content)
    total_chunks = len(text_chunks)

    logger.info(f"Created {total_chunks} chunks")

    # Create Chunk objects with metadata
    chunks = []
    for i, text in enumerate(text_chunks):
        chunk_metadata = ChunkMetadata(
            document_id=document.document_id,
            document_path=document.metadata.file_path,
            chunk_position=i,
            total_chunks=total_chunks,
            overlap_with_previous=0 if i == 0 else splitter.chunk_overlap,
            overlap_with_next=0 if i == total_chunks - 1 else splitter.chunk_overlap,
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
    document_path,
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
        chunk_position=position,
        total_chunks=total_chunks,
        overlap_with_previous=overlap_prev,
        overlap_with_next=overlap_next,
    )
