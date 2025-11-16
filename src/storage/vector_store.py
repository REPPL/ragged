"""
ChromaDB vector store interface.

Provides a wrapper around ChromaDB for storing and retrieving document embeddings
with automatic connection management and error handling.
"""

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import numpy as np

# Disable ChromaDB telemetry for privacy
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'

try:
    import chromadb
except ImportError:
    chromadb = None

from src.config.settings import get_settings
from src.storage.metadata_serialiser import (
    deserialise_batch_metadata,
    deserialise_metadata,
    serialise_batch_metadata,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    ChromaDB vector store for document chunks.

    Handles connection management, collection CRUD, and vector operations.
    """

    def __init__(
        self,
        collection_name: str = "ragged_documents",
        host: str = None,
        port: int = None,
    ):
        """Initialize vector store connection."""
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
        except Exception as e:
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
        Add embeddings to the vector store.

        Args:
            ids: List of unique IDs for the chunks
            embeddings: Array of embeddings shape (n, dimensions)
            documents: List of full text for each chunk
            metadatas: List of metadata dicts for each chunk

        Example:
            >>> store = VectorStore()
            >>> store.add(
            ...     ids=["chunk1", "chunk2"],
            ...     embeddings=np.array([[0.1, 0.2], [0.3, 0.4]]),
            ...     documents=["text1", "text2"],
            ...     metadatas=[{"doc": "1"}, {"doc": "2"}]
            ... )
        """
        embeddings_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings

        # Serialise metadata for ChromaDB compatibility
        serialised_metadatas = serialise_batch_metadata(metadatas)

        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=documents,
            metadatas=serialised_metadatas,
        )
        logger.info(f"Added {len(ids)} embeddings to collection {self._collection_name}")

    def query(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query for similar vectors.

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

        results = self.collection.query(
            query_embeddings=query_list,
            n_results=k,
            where=where,
        )

        # Deserialise metadata in results
        if results and results.get("metadatas"):
            # ChromaDB returns nested lists for batch queries
            if isinstance(results["metadatas"][0], list):
                # Batch query: list of lists
                results["metadatas"] = [
                    deserialise_batch_metadata(batch) for batch in results["metadatas"]
                ]
            else:
                # Single query: list of dicts
                results["metadatas"] = deserialise_batch_metadata(results["metadatas"])

        return results

    def get_documents_by_metadata(self, where: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get documents matching metadata filter.

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
                results["metadatas"] = deserialise_batch_metadata(results["metadatas"])

            return results
        except Exception as e:
            logger.error(f"Failed to get documents by metadata: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Delete embeddings from the store.

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

    def count(self) -> int:
        """
        Get count of embeddings in store.

        Returns:
            Number of embeddings
        """
        return self.collection.count()

    def clear(self) -> None:
        """
        Clear all embeddings from the collection.
        """
        try:
            self.client.delete_collection(self._collection_name)
            self.collection = self.client.create_collection(
                name=self._collection_name,
                metadata={"description": "ragged document chunks"}
            )
            logger.info(f"Cleared collection {self._collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.

        Returns:
            Dict with collection metadata
        """
        return {
            "name": self._collection_name,
            "count": self.count(),
            "metadata": self.collection.metadata,
        }
