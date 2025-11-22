"""
VectorStore factory for creating database instances.

Provides a simple factory function to instantiate vector stores based on
configuration, enabling easy switching between different backends.

v0.3.6: Initial factory implementation for multi-backend support.
"""

from typing import Optional

from src.config.settings import get_settings
from src.storage.vectorstore_interface import VectorStore
from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_vectorstore(
    backend: Optional[str] = None,
    collection_name: str = "ragged_documents",
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> VectorStore:
    """
    Factory function to create a VectorStore instance.

    Args:
        backend: Backend type ('chromadb', 'leann', 'qdrant', etc.)
                 If None, defaults to configured backend
        collection_name: Name of the collection/index
        host: Database host (backend-specific)
        port: Database port (backend-specific)

    Returns:
        VectorStore instance for the specified backend

    Raises:
        ValueError: If backend is not supported
        ImportError: If required backend package is not installed

    Example:
        >>> # Use default backend (from config)
        >>> store = get_vectorstore()
        >>>
        >>> # Explicitly specify backend
        >>> store = get_vectorstore(backend="chromadb", collection_name="my_docs")
        >>>
        >>> # Future: Support for other backends
        >>> store = get_vectorstore(backend="leann", collection_name="research")
    """
    # Get backend from config if not specified
    if backend is None:
        settings = get_settings()
        # v0.3.6: Default to chromadb, future versions will read from config
        backend = getattr(settings, 'vectorstore_backend', 'chromadb')

    backend = backend.lower()
    logger.info(f"Creating VectorStore with backend: {backend}")

    if backend == "chromadb":
        from src.storage.chromadb_store import ChromaDBStore
        return ChromaDBStore(
            collection_name=collection_name,
            host=host,
            port=port,
        )
    elif backend == "leann":
        # v0.4.0: LEANN integration
        raise NotImplementedError(
            "LEANN backend will be available in v0.4.0. "
            "See roadmap: docs/development/roadmap/version/v0.4/"
        )
    elif backend == "qdrant":
        # Future: Qdrant support
        raise NotImplementedError(
            "Qdrant backend not yet implemented. "
            "Currently supported: chromadb"
        )
    elif backend == "weaviate":
        # Future: Weaviate support
        raise NotImplementedError(
            "Weaviate backend not yet implemented. "
            "Currently supported: chromadb"
        )
    else:
        raise ValueError(
            f"Unknown vector store backend: {backend}. "
            f"Supported backends: chromadb (more coming in v0.4.0)"
        )
