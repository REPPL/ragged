"""
Text splitting strategies for creating semantic chunks.
"""

import re
from typing import List, Tuple
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


def _build_page_position_map(content: str) -> List[Tuple[int, int]]:
    """
    Build a map of page markers and their positions in the content.

    Args:
        content: Document content with <!-- PAGE N --> markers

    Returns:
        List of (page_number, position) tuples
    """
    page_positions = []
    # Match <!-- PAGE N --> markers
    pattern = r'<!-- PAGE (\d+) -->'

    for match in re.finditer(pattern, content):
        page_num = int(match.group(1))
        position = match.start()
        page_positions.append((page_num, position))

    return page_positions


def _get_page_for_position(position: int, page_positions: List[Tuple[int, int]]) -> int:
    """
    Determine which page a given position falls on.

    Args:
        position: Character position in the content
        page_positions: List of (page_number, position) tuples

    Returns:
        Page number (1-indexed)
    """
    if not page_positions:
        return 1  # Default to page 1 if no markers

    # Find the last page marker that comes before or at this position
    current_page = 1
    for page_num, page_pos in page_positions:
        if page_pos <= position:
            current_page = page_num
        else:
            break

    return current_page


def _build_clean_to_orig_map(original_content: str) -> List[int]:
    """
    Build a mapping from cleaned content positions to original content positions.

    When we remove page markers for chunking, we need to map chunk positions
    back to the original content positions to determine page numbers.

    Args:
        original_content: Content with <!-- PAGE N --> markers

    Returns:
        List where index i contains the corresponding position in original content
    """
    # Pattern for page markers
    pattern = r'<!-- PAGE \d+ -->\n?'

    # Build the mapping
    mapping = []
    orig_pos = 0
    clean_pos = 0

    for match in re.finditer(pattern, original_content):
        marker_start = match.start()
        marker_end = match.end()

        # Add mappings for content before this marker
        while orig_pos < marker_start:
            mapping.append(orig_pos)
            orig_pos += 1
            clean_pos += 1

        # Skip the marker in original but don't advance clean position
        orig_pos = marker_end

    # Add remaining content
    while orig_pos < len(original_content):
        mapping.append(orig_pos)
        orig_pos += 1
        clean_pos += 1

    return mapping


def _map_chunks_to_pages(
    text_chunks: List[str],
    clean_content: str,
    original_content: str,
    page_positions: List[Tuple[int, int]]
) -> List[Tuple[int, str]]:
    """
    Map text chunks to their page numbers.

    Args:
        text_chunks: List of chunk text strings
        clean_content: Content without page markers (used for chunking)
        original_content: Original content with page markers
        page_positions: List of (page_number, position) tuples

    Returns:
        List of (page_number, page_range) tuples for each chunk.
        page_range is None for single-page chunks, or "N-M" for multi-page.
    """
    if not page_positions:
        # No page markers, return None for all chunks
        return [(None, None) for _ in text_chunks]

    # Build position mapping
    clean_to_orig = _build_clean_to_orig_map(original_content)

    chunk_pages = []
    current_pos = 0

    for chunk_text in text_chunks:
        # Find where this chunk starts and ends in the clean content
        chunk_start = clean_content.find(chunk_text, current_pos)

        if chunk_start == -1:
            # Chunk not found (shouldn't happen, but handle gracefully)
            chunk_pages.append((None, None))
            continue

        chunk_end = chunk_start + len(chunk_text)

        # Map to original positions
        if chunk_start < len(clean_to_orig) and chunk_end <= len(clean_to_orig):
            orig_start = clean_to_orig[chunk_start]
            orig_end = clean_to_orig[chunk_end - 1] if chunk_end > 0 else orig_start

            # Determine page numbers
            start_page = _get_page_for_position(orig_start, page_positions)
            end_page = _get_page_for_position(orig_end, page_positions)

            if start_page == end_page:
                chunk_pages.append((start_page, None))
            else:
                chunk_pages.append((start_page, f"{start_page}-{end_page}"))
        else:
            # Fallback
            chunk_pages.append((None, None))

        current_pos = chunk_end

    return chunk_pages


def _estimate_page_from_position(chunk_position: int, total_chunks: int, total_pages: int) -> int:
    """
    Estimate page number from chunk position when precise tracking fails.

    Args:
        chunk_position: Position of chunk (0-indexed)
        total_chunks: Total number of chunks
        total_pages: Total number of pages in document

    Returns:
        Estimated page number (1-indexed)
    """
    if total_pages <= 1:
        return 1

    # Linear interpolation
    progress = chunk_position / max(total_chunks - 1, 1)
    estimated_page = int(progress * (total_pages - 1)) + 1

    return min(max(estimated_page, 1), total_pages)


def chunk_document(document: Document, splitter: RecursiveCharacterTextSplitter = None) -> Document:
    """Chunk a document and add chunk metadata with page tracking."""
    if splitter is None:
        splitter = RecursiveCharacterTextSplitter()

    logger.info(f"Chunking document: {document.document_id}")

    # Build page position map from original content
    original_content = document.content
    page_positions = _build_page_position_map(original_content)

    # Remove page markers for chunking
    clean_content = re.sub(r'<!-- PAGE \d+ -->\n?', '', original_content)

    # Split content (using cleaned content without markers)
    text_chunks = splitter.split_text(clean_content)
    total_chunks = len(text_chunks)

    logger.info(f"Created {total_chunks} chunks")

    # Map chunks to their page numbers
    chunk_pages = _map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

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
            page_number = _estimate_page_from_position(i, total_chunks, total_pages)

        chunk_metadata = ChunkMetadata(
            document_id=document.document_id,
            document_path=document.metadata.file_path,
            file_hash=document.metadata.file_hash,
            content_hash=document.metadata.content_hash,
            chunk_position=i,
            total_chunks=total_chunks,
            overlap_with_previous=0 if i == 0 else splitter.chunk_overlap,
            overlap_with_next=0 if i == total_chunks - 1 else splitter.chunk_overlap,
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
    document_path,
    file_hash: str,
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
        chunk_position=position,
        total_chunks=total_chunks,
        overlap_with_previous=overlap_prev,
        overlap_with_next=overlap_next,
    )
