"""VectorStore abstraction layer for ragged.

Provides pluggable vector database backends enabling flexibility in storage
and retrieval strategies. Supports ChromaDB (default) and LEANN (v0.4.3+).

Version: 0.4.2
"""

from ragged.vectorstore.interface import VectorStore, VectorStoreDocument, VectorStoreQueryResult
from ragged.vectorstore.factory import VectorStoreFactory, VectorStoreType
from ragged.vectorstore.exceptions import (
    VectorStoreError,
    VectorStoreNotFoundError,
    VectorStoreConnectionError,
)

__all__ = [
    # Core interface
    "VectorStore",
    "VectorStoreDocument",
    "VectorStoreQueryResult",
    # Factory
    "VectorStoreFactory",
    "VectorStoreType",
    # Exceptions
    "VectorStoreError",
    "VectorStoreNotFoundError",
    "VectorStoreConnectionError",
]

__version__ = "0.4.2"
