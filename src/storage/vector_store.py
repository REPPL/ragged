"""
ChromaDB vector store interface (backward compatibility).

v0.3.6: This module now re-exports ChromaDBStore as VectorStore for backward
compatibility. New code should use:
    from src.storage.vectorstore_factory import get_vectorstore

The VectorStore class is now an abstract interface. See:
    - src/storage/vectorstore_interface.py for the abstract interface
    - src/storage/chromadb_store.py for the ChromaDB implementation
    - src.storage.vectorstore_factory.py for the factory function
"""

# Backward compatibility: Import ChromaDBStore and alias as VectorStore
from src.storage.chromadb_store import ChromaDBStore as VectorStore  # noqa: F401

# Re-export for backward compatibility
__all__ = ["VectorStore"]


# v0.3.6: Legacy VectorStore class is now ChromaDBStore
# For new code, use:
#   from src.storage.vectorstore_factory import get_vectorstore
#   store = get_vectorstore(backend="chromadb")
#
# This maintains 100% backward compatibility while enabling future multi-backend support.
# Original implementation moved to chromadb_store.py
