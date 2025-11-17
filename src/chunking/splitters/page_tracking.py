"""Page tracking and mapping for document chunks."""

import re
from typing import List, Tuple, Optional


def build_page_position_map(content: str) -> List[Tuple[int, int]]:
    """Build a map of page markers and their positions in the content.

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


def get_page_for_position(position: int, page_positions: List[Tuple[int, int]]) -> int:
    """Determine which page a given position falls on.

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


def build_clean_to_orig_map(original_content: str) -> List[int]:
    """Build a mapping from cleaned content positions to original content positions.

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


def map_chunks_to_pages(
    text_chunks: List[str],
    clean_content: str,
    original_content: str,
    page_positions: List[Tuple[int, int]]
) -> List[Tuple[Optional[int], Optional[str]]]:
    """Map text chunks to their page numbers.

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
    clean_to_orig = build_clean_to_orig_map(original_content)

    chunk_pages: List[Tuple[Optional[int], Optional[str]]] = []
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
            start_page = get_page_for_position(orig_start, page_positions)
            end_page = get_page_for_position(orig_end, page_positions)

            if start_page == end_page:
                chunk_pages.append((start_page, None))
            else:
                chunk_pages.append((start_page, f"{start_page}-{end_page}"))
        else:
            # Fallback
            chunk_pages.append((None, None))

        current_pos = chunk_end

    return chunk_pages


def estimate_page_from_position(chunk_position: int, total_chunks: int, total_pages: int) -> int:
    """Estimate page number from chunk position when precise tracking fails.

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
