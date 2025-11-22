"""Text splitting strategies for creating semantic chunks.

This module maintains backwards compatibility by importing from the refactored
splitters submodule. All functionality has been split into logical modules:
- splitters/recursive_splitter.py: RecursiveCharacterTextSplitter class
- splitters/page_tracking.py: Page position mapping and tracking
- splitters/chunking.py: Document chunking orchestration
"""

# Import all public components for backwards compatibility
from src.chunking.splitters.chunking import chunk_document, create_chunk_metadata
from src.chunking.splitters.page_tracking import (
    build_clean_to_orig_map as _build_clean_to_orig_map,
)

# Internal functions (previously module-level, now in page_tracking)
from src.chunking.splitters.page_tracking import (
    build_page_position_map as _build_page_position_map,
)
from src.chunking.splitters.page_tracking import (
    estimate_page_from_position as _estimate_page_from_position,
)
from src.chunking.splitters.page_tracking import (
    get_page_for_position as _get_page_for_position,
)
from src.chunking.splitters.page_tracking import (
    map_chunks_to_pages as _map_chunks_to_pages,
)
from src.chunking.splitters.recursive_splitter import RecursiveCharacterTextSplitter

__all__ = [
    "RecursiveCharacterTextSplitter",
    "chunk_document",
    "create_chunk_metadata",
    # Internal functions (prefixed with _) for backwards compatibility
    "_build_page_position_map",
    "_get_page_for_position",
    "_build_clean_to_orig_map",
    "_map_chunks_to_pages",
    "_estimate_page_from_position",
]
