"""
Vector storage and retrieval.

v0.3.6: Vectorstore abstraction for multi-backend support.
v0.3.7a: Document version tracking.
"""

# Abstract interface (for type hints and subclassing)
# Specific implementations
from ragged.storage.chromadb_store import ChromaDBStore

# ChromaDB implementation (backward compatible)
from ragged.storage.vector_store import VectorStore

# Factory function (recommended for new code)
from ragged.storage.vectorstore_factory import get_vectorstore
from ragged.storage.vectorstore_interface import VectorStore as VectorStoreInterface

# Version tracking (v0.3.7a)
from ragged.storage.version_tracker import DocumentVersion, VersionTracker

__all__ = [
    # Abstract interface
    "VectorStoreInterface",
    # Backward compatible VectorStore (ChromaDBStore alias)
    "VectorStore",
    # Factory function (recommended)
    "get_vectorstore",
    # Specific implementations
    "ChromaDBStore",
    # Version tracking (v0.3.7a)
    "VersionTracker",
    "DocumentVersion",
]
