"""
Vector storage and retrieval.

v0.3.6: Vectorstore abstraction for multi-backend support.
v0.3.7a: Document version tracking.
"""

# Abstract interface (for type hints and subclassing)
from src.storage.vectorstore_interface import VectorStore as VectorStoreInterface

# ChromaDB implementation (backward compatible)
from src.storage.vector_store import VectorStore

# Factory function (recommended for new code)
from src.storage.vectorstore_factory import get_vectorstore

# Specific implementations
from src.storage.chromadb_store import ChromaDBStore

# Version tracking (v0.3.7a)
from src.storage.version_tracker import VersionTracker, DocumentVersion

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
