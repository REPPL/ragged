"""VectorStore abstraction layer for ragged.

Provides pluggable vector database backends enabling flexibility in storage
and retrieval strategies. Supports ChromaDB (universal) and LEANN (macOS/Linux).

Platform-aware backend selection:
- macOS/Linux: LEANN by default (97% storage savings)
- Windows: ChromaDB (LEANN not available)

Version: 0.4.3
"""

from ragged.vectorstore.interface import VectorStore, VectorStoreDocument, VectorStoreQueryResult
from ragged.vectorstore.factory import VectorStoreFactory, VectorStoreType
from ragged.vectorstore.exceptions import (
    VectorStoreError,
    VectorStoreNotFoundError,
    VectorStoreConnectionError,
)
from ragged.vectorstore.platform import (
    get_default_backend,
    detect_platform_backend_support,
    get_platform_info,
)

__all__ = [
    # Core interface
    "VectorStore",
    "VectorStoreDocument",
    "VectorStoreQueryResult",
    # Factory
    "VectorStoreFactory",
    "VectorStoreType",
    # Platform detection
    "get_default_backend",
    "detect_platform_backend_support",
    "get_platform_info",
    # Exceptions
    "VectorStoreError",
    "VectorStoreNotFoundError",
    "VectorStoreConnectionError",
]

__version__ = "0.4.3"
