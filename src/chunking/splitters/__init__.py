"""Text splitting strategies for creating semantic chunks."""

from src.chunking.splitters.chunking import chunk_document, create_chunk_metadata
from src.chunking.splitters.recursive_splitter import RecursiveCharacterTextSplitter

__all__ = [
    "RecursiveCharacterTextSplitter",
    "chunk_document",
    "create_chunk_metadata",
]
