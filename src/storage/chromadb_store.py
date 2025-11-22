"""
ChromaDB vector store implementation.

Provides ChromaDB-specific implementation of the VectorStore interface,
with automatic connection management, error handling, circuit breaker protection,
and metadata serialization.

v0.3.6: Refactored to implement VectorStore interface for multi-backend support.
"""

import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from urllib.parse import urlparse

import numpy as np

# Disable ChromaDB telemetry for privacy
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'

if TYPE_CHECKING:
    import chromadb
else:
    try:
        import chromadb
    except ImportError:
        chromadb = None  # type: ignore[assignment]

from src.config.settings import get_settings
from src.exceptions import VectorStoreConnectionError, VectorStoreError
from src.storage.metadata_serializer import (
    deserialize_batch_metadata,
    deserialize_metadata,
    serialize_batch_metadata,
)
from src.storage.vectorstore_interface import VectorStore
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.logging import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


# v0.2.9: Circuit breaker for ChromaDB protection
_chroma_circuit_breaker = CircuitBreaker(
    name="chromadb",
    failure_threshold=5,
    recovery_timeout=30.0,
)


class ChromaDBStore(VectorStore):
    """
    ChromaDB implementation of VectorStore interface.

    Handles connection management, collection CRUD, and vector operations
    with circuit breaker protection and automatic retry.

    Example:
        >>> from src.storage.chromadb_store import ChromaDBStore
        >>> store = ChromaDBStore(collection_name="my_docs")
        >>> store.add(
        ...     ids=["doc1"],
        ...     embeddings=np.array([[0.1, 0.2, 0.3]]),
        ...     documents=["Sample text"],
        ...     metadatas=[{"source": "test.txt"}]
        ... )
    """

    def __init__(
        self,
        collection_name: str = "ragged_documents",
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """
        Initialize ChromaDB vector store connection.

        Args:
            collection_name: Name of the ChromaDB collection
            host: ChromaDB server host (defaults to settings)
            port: ChromaDB server port (defaults to settings)

        Raises:
            ImportError: If chromadb is not installed
        """
        if chromadb is None:
            raise ImportError("chromadb required: pip install chromadb")

        self._collection_name = collection_name

        settings = get_settings()

        # Parse host and port from URL if not provided
        if host is None or port is None:
            chroma_url = settings.chroma_url
            parsed = urlparse(chroma_url)
            host = host or parsed.hostname or "localhost"
            port = port or parsed.port or 8001

        logger.info(f"Connecting to ChromaDB at {host}:{port}")

        # Create ChromaDB client
        self.client = chromadb.HttpClient(host=host, port=port)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "ragged document chunks"}
        )

        logger.info(f"Using collection: {collection_name}")

    def health_check(self) -> bool:
        """
        Check if ChromaDB is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.heartbeat()
            return True
        except (ConnectionError, TimeoutError, AttributeError) as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False

    def add(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Add embeddings to ChromaDB.

        Args:
            ids: List of unique IDs for the chunks
            embeddings: Array of embeddings shape (n, dimensions)
            documents: List of full text for each chunk
            metadatas: List of metadata dicts for each chunk
        """
        embeddings_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings

        # Serialise metadata for ChromaDB compatibility
        serialized_metadatas = serialize_batch_metadata(metadatas)

        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=documents,
            metadatas=serialized_metadatas,  # type: ignore[arg-type]
        )
        logger.info(f"Added {len(ids)} embeddings to collection {self._collection_name}")

    @with_retry(max_attempts=3, base_delay=1.0, retryable_exceptions=(ConnectionError, TimeoutError, VectorStoreConnectionError))
    def _query_internal(
        self,
        query_list: List[List[float]],
        k: int,
        where: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Internal query method with circuit breaker protection.

        v0.2.9: Protected by circuit breaker and retry decorator.
        """
        try:
            results = _chroma_circuit_breaker.call(
                self.collection.query,
                query_embeddings=query_list,
                n_results=k,
                where=where,
            )
            return cast(Dict[str, Any], results)
        except (ConnectionError, TimeoutError) as e:
            raise VectorStoreConnectionError(f"ChromaDB connection failed: {e}")
        except Exception as e:
            raise VectorStoreError(f"Query failed: {e}")

    def query(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query ChromaDB for similar vectors.

        v0.2.9: Uses automatic retry with exponential backoff and circuit breaker.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            where: Optional metadata filter

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'
        """
        if isinstance(query_embedding, np.ndarray):
            query_list = [query_embedding.tolist()]
        elif isinstance(query_embedding, list):
            # Already a list - wrap in outer list for ChromaDB batch format
            query_list = [query_embedding]
        else:
            # Single value - convert to nested list
            query_list = [[float(query_embedding)]]

        # v0.2.9: Check if advanced error recovery is enabled
        settings = get_settings()
        if settings.feature_flags.enable_advanced_error_recovery:
            results = self._query_internal(query_list, k, where)
        else:
            # Fallback to old behaviour
            results = self.collection.query(
                query_embeddings=query_list,
                n_results=k,
                where=where,
            )
            results = cast(Dict[str, Any], results)

        # Deserialise metadata in results
        if results and results.get("metadatas"):
            metadatas = results["metadatas"]
            # ChromaDB returns nested lists for batch queries
            if metadatas and isinstance(metadatas[0], list):
                # Batch query: list of lists
                deserialized_batches = [
                    deserialize_batch_metadata(batch)  # type: ignore[arg-type]
                    for batch in metadatas
                ]
                results["metadatas"] = deserialized_batches  # type: ignore[typeddict-item]
            else:
                # Single query: list of dicts
                results["metadatas"] = deserialize_batch_metadata(metadatas)  # type: ignore[arg-type, typeddict-item]

        return results

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Delete embeddings from ChromaDB.

        Args:
            ids: List of IDs to delete
            where: Metadata filter for deletion
        """
        if ids:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} embeddings by ID")
        elif where:
            self.collection.delete(where=where)
            logger.info(f"Deleted embeddings matching filter: {where}")

    def update_metadata(
        self,
        ids: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Update metadata for existing embeddings in ChromaDB.

        Args:
            ids: List of IDs to update
            metadatas: List of metadata dicts (one per ID)

        Raises:
            ValueError: If ids and metadatas have different lengths
        """
        if len(ids) != len(metadatas):
            raise ValueError("ids and metadatas must have same length")

        # Serialise metadata for ChromaDB
        serialized_metadatas = serialize_batch_metadata(metadatas)

        self.collection.update(
            ids=ids,
            metadatas=serialized_metadatas,  # type: ignore[arg-type]
        )
        logger.info(f"Updated metadata for {len(ids)} embeddings")

    def get_documents_by_metadata(self, where: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get documents from ChromaDB matching metadata filter.

        Useful for duplicate detection by querying for existing documents
        with the same file_hash or document_path.

        Args:
            where: Metadata filter (e.g., {"file_hash": "abc123..."})

        Returns:
            Dict with 'ids', 'documents', 'metadatas' of matching documents
            Returns empty dict if no matches found.
        """
        try:
            results = self.collection.get(where=where)
            logger.debug(f"Found {len(results.get('ids', []))} documents matching filter")

            # Deserialise metadata in results
            if results and results.get("metadatas"):
                results["metadatas"] = deserialize_batch_metadata(results["metadatas"])  # type: ignore[arg-type, typeddict-item]

            return cast(Dict[str, Any], results)
        except (ConnectionError, TimeoutError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to get documents by metadata: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List documents from ChromaDB with pagination.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            where: Optional metadata filter

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'total'
        """
        try:
            # Get total count first
            if where:
                # ChromaDB doesn't provide count with filter, so get all and count
                all_results = self.collection.get(where=where)
                total = len(all_results.get("ids", []))
            else:
                total = self.collection.count()

            # Get paginated results
            results = self.collection.get(
                where=where,
                limit=limit,
                offset=offset,
            )

            # Deserialise metadata
            if results and results.get("metadatas"):
                results["metadatas"] = deserialize_batch_metadata(results["metadatas"])  # type: ignore[arg-type, typeddict-item]

            # Add total count
            results["total"] = total  # type: ignore[typeddict-item]

            return cast(Dict[str, Any], results)
        except (ConnectionError, TimeoutError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to list documents: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "total": 0}

    def count(self) -> int:
        """
        Get count of embeddings in ChromaDB collection.

        Returns:
            Number of embeddings
        """
        return self.collection.count()

    def clear(self) -> None:
        """
        Clear all embeddings from the ChromaDB collection.

        Warning: This operation is irreversible!

        Raises:
            VectorStoreError: If clear operation fails
        """
        try:
            self.client.delete_collection(self._collection_name)
            self.collection = self.client.create_collection(
                name=self._collection_name,
                metadata={"description": "ragged document chunks"}
            )
            logger.info(f"Cleared collection {self._collection_name}")
        except (ConnectionError, TimeoutError, ValueError, AttributeError) as e:
            logger.error(f"Failed to clear collection: {e}")
            raise VectorStoreError(f"Failed to clear collection: {e}")

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the ChromaDB collection.

        Returns:
            Dict with collection metadata
        """
        return {
            "name": self._collection_name,
            "count": self.count(),
            "metadata": self.collection.metadata,
        }
