"""Factory for creating VectorStore instances."""

from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from ragged.vectorstore.interface import VectorStore
from ragged.vectorstore.exceptions import VectorStoreConfigError

logger = logging.getLogger(__name__)


class VectorStoreType(Enum):
    """Supported vector store backends."""

    CHROMADB = "chromadb"
    LEANN = "leann"  # Available in v0.4.3+


class VectorStoreFactory:
    """Factory for creating VectorStore instances."""

    @staticmethod
    def create(
        backend: str = "chromadb",
        config: Optional[Dict[str, Any]] = None,
    ) -> VectorStore:
        """Create a VectorStore instance.

        Args:
            backend: Backend type ("chromadb" or "leann")
            config: Backend-specific configuration

        Returns:
            VectorStore instance

        Raises:
            VectorStoreConfigError: If backend is unknown or unavailable
        """
        config = config or {}

        if backend == VectorStoreType.CHROMADB.value:
            try:
                from ragged.vectorstore.chromadb_store import ChromaDBStore

                return ChromaDBStore(config=config)
            except ImportError as e:
                raise VectorStoreConfigError(
                    f"ChromaDB backend not available: {e}. Install with: pip install chromadb"
                )

        elif backend == VectorStoreType.LEANN.value:
            try:
                from ragged.vectorstore.leann_store import LEANNStore

                return LEANNStore(config=config)
            except ImportError as e:
                raise VectorStoreConfigError(
                    f"LEANN backend not available: {e}. Will be available in v0.4.3+"
                )

        else:
            raise VectorStoreConfigError(
                f"Unknown backend: {backend}. Supported: {[t.value for t in VectorStoreType]}"
            )

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> VectorStore:
        """Create VectorStore from configuration dictionary.

        Args:
            config: Configuration with 'backend' and backend-specific settings

        Returns:
            VectorStore instance
        """
        backend = config.get("backend", "chromadb")
        backend_config = config.get(backend, {})

        return VectorStoreFactory.create(backend=backend, config=backend_config)

    @staticmethod
    def get_available_backends() -> list[str]:
        """Get list of available backends.

        Returns:
            List of backend names
        """
        available = []

        # Check ChromaDB
        try:
            import chromadb

            available.append(VectorStoreType.CHROMADB.value)
        except ImportError:
            pass

        # Check LEANN (will be available in v0.4.3)
        try:
            import leann

            available.append(VectorStoreType.LEANN.value)
        except ImportError:
            pass

        return available
