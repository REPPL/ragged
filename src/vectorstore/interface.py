"""VectorStore abstract interface.

Defines the contract that all vector database implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class VectorStoreDocument:
    """Unified document representation across backends."""

    id: str
    content: str
    embedding: np.ndarray | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "metadata": self.metadata or {},
        }


@dataclass
class VectorStoreQueryResult:
    """Unified query result representation."""

    documents: list[VectorStoreDocument]
    distances: list[float]
    ids: list[str]


class VectorStore(ABC):
    """Abstract base class for vector store backends."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check if vector store is accessible and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def add(
        self,
        ids: list[str],
        embeddings: np.ndarray,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        collection_name: str = "default",
    ) -> None:
        """Add documents to the vector store.

        Args:
            ids: Document IDs
            embeddings: Document embeddings
            documents: Document content
            metadatas: Document metadata
            collection_name: Collection/index name
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        collection_name: str = "default",
        filter_dict: dict[str, Any] | None = None,
    ) -> VectorStoreQueryResult:
        """Search for similar documents.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            collection_name: Collection to search
            filter_dict: Metadata filters

        Returns:
            Query results with documents and distances
        """
        pass

    @abstractmethod
    def delete(
        self,
        document_ids: list[str],
        collection_name: str = "default",
    ) -> int:
        """Delete documents from the vector store.

        Args:
            document_ids: IDs of documents to delete
            collection_name: Collection name

        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    def update(
        self,
        ids: list[str],
        embeddings: np.ndarray | None = None,
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        collection_name: str = "default",
    ) -> int:
        """Update documents in the vector store.

        Args:
            ids: Document IDs to update
            embeddings: New embeddings (optional)
            documents: New content (optional)
            metadatas: New metadata (optional)
            collection_name: Collection name

        Returns:
            Number of documents updated
        """
        pass

    @abstractmethod
    def get(
        self,
        document_ids: list[str],
        collection_name: str = "default",
    ) -> list[VectorStoreDocument]:
        """Get documents by ID.

        Args:
            document_ids: Document IDs to retrieve
            collection_name: Collection name

        Returns:
            List of documents
        """
        pass

    @abstractmethod
    def count(self, collection_name: str = "default") -> int:
        """Count documents in collection.

        Args:
            collection_name: Collection name

        Returns:
            Number of documents
        """
        pass

    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all collections.

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    def create_collection(self, name: str, metadata: dict | None = None) -> None:
        """Create a new collection.

        Args:
            name: Collection name
            metadata: Optional collection metadata
        """
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        """Delete a collection.

        Args:
            name: Collection name
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connection to vector store."""
        pass
