"""Factory for creating VectorStore instances."""

from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from ragged.vectorstore.interface import VectorStore
from ragged.vectorstore.exceptions import VectorStoreConfigError
from ragged.vectorstore.platform import (
    get_default_backend,
    detect_platform_backend_support,
    get_platform_info,
)

logger = logging.getLogger(__name__)


class VectorStoreType(Enum):
    """Supported vector store backends."""

    CHROMADB = "chromadb"
    LEANN = "leann"  # Available in v0.4.3+


class VectorStoreFactory:
    """Factory for creating VectorStore instances."""

    @staticmethod
    def create(
        backend: str = "auto",
        config: Optional[Dict[str, Any]] = None,
    ) -> VectorStore:
        """Create a VectorStore instance.

        Args:
            backend: Backend type ("auto", "chromadb", or "leann")
                - "auto": Auto-detect best available backend (default)
                - "chromadb": Force ChromaDB backend
                - "leann": Force LEANN backend (requires macOS/Linux)
            config: Backend-specific configuration

        Returns:
            VectorStore instance

        Raises:
            VectorStoreConfigError: If backend is unknown or unavailable
        """
        config = config or {}

        # Auto-select backend if requested
        if backend == "auto":
            backend = get_default_backend()
            logger.info(f"Auto-selected backend: {backend}")

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
                platform_info = get_platform_info()
                platform_name = platform_info["system"]

                if platform_name == "Windows":
                    raise VectorStoreConfigError(
                        f"LEANN backend not available on Windows. "
                        f"LEANN requires macOS or Linux. "
                        f"Use ChromaDB backend instead (fully functional)."
                    )
                else:
                    raise VectorStoreConfigError(
                        f"LEANN backend not available: {e}. "
                        f"Install with: pip install ragged[leann]"
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
        """Get list of available backends on current platform.

        Returns:
            List of backend names that are available
        """
        available = []

        # Check ChromaDB
        try:
            import chromadb

            available.append(VectorStoreType.CHROMADB.value)
        except ImportError:
            pass

        # Check LEANN (platform-dependent: macOS, Linux only)
        try:
            import leann

            available.append(VectorStoreType.LEANN.value)
        except ImportError:
            pass

        return available

    @staticmethod
    def get_backend_support_info() -> Dict[str, Any]:
        """Get detailed backend support information for current platform.

        Returns:
            Dictionary with platform info and backend availability
        """
        platform_info = get_platform_info()
        backend_support = detect_platform_backend_support()
        available_backends = VectorStoreFactory.get_available_backends()

        return {
            "platform": platform_info,
            "backend_support": backend_support,
            "available_backends": available_backends,
            "default_backend": get_default_backend(),
        }
