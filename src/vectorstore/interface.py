"""VectorStore abstract interface.

Defines the contract that all vector database implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class VectorStoreDocument:
    """Unified document representation across backends."""

    id: str
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
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

    documents: List[VectorStoreDocument]
    distances: List[float]
    ids: List[str]


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
        ids: List[str],
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
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
        filter_dict: Optional[Dict[str, Any]] = None,
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
        document_ids: List[str],
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
        ids: List[str],
        embeddings: Optional[np.ndarray] = None,
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
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
        document_ids: List[str],
        collection_name: str = "default",
    ) -> List[VectorStoreDocument]:
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
    def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> None:
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
