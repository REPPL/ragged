"""
VectorStore abstract interface.

Defines the standard interface that all vector database implementations must follow,
enabling ragged to support multiple vector database backends (ChromaDB, LEANN,
Qdrant, Weaviate, etc.) with zero code changes.

v0.3.6: Initial abstraction layer for multi-backend support.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np


class VectorStore(ABC):
    """
    Abstract base class for vector database implementations.

    All vector store backends must implement this interface to ensure
    consistent behaviour across different database systems.

    Example:
        >>> class MyVectorStore(VectorStore):
        ...     def add(self, ids, embeddings, documents, metadatas):
        ...         # Implementation-specific logic
        ...         pass
    """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the vector database is accessible and healthy.

        Returns:
            True if the database is accessible and responding, False otherwise
        """
        pass

    @abstractmethod
    def add(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Add documents with their embeddings to the vector store.

        Args:
            ids: List of unique identifiers for each document chunk
            embeddings: Numpy array of shape (n, dimensions) containing embeddings
            documents: List of document text content
            metadatas: List of metadata dictionaries for each document

        Raises:
            VectorStoreError: If the add operation fails

        Example:
            >>> store.add(
            ...     ids=["doc1", "doc2"],
            ...     embeddings=np.array([[0.1, 0.2], [0.3, 0.4]]),
            ...     documents=["text 1", "text 2"],
            ...     metadatas=[{"source": "file1.txt"}, {"source": "file2.txt"}]
            ... )
        """
        pass

    @abstractmethod
    def query(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.

        Args:
            query_embedding: Query embedding vector as numpy array
            k: Number of similar documents to return (default: 5)
            where: Optional metadata filter as dictionary

        Returns:
            Dictionary containing:
                - ids: List of document IDs
                - documents: List of document texts
                - metadatas: List of metadata dictionaries
                - distances: List of similarity distances

        Example:
            >>> results = store.query(
            ...     query_embedding=np.array([0.1, 0.2, 0.3]),
            ...     k=3,
            ...     where={"source": "research/*.pdf"}
            ... )
            >>> print(results["ids"])
            ['doc1', 'doc2', 'doc3']
        """
        pass

    @abstractmethod
    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Delete documents from the vector store.

        Either ids or where must be provided. If both are provided,
        ids takes precedence.

        Args:
            ids: List of document IDs to delete
            where: Metadata filter to select documents for deletion

        Raises:
            ValueError: If neither ids nor where is provided

        Example:
            >>> # Delete by IDs
            >>> store.delete(ids=["doc1", "doc2"])
            >>>
            >>> # Delete by metadata filter
            >>> store.delete(where={"source": "deprecated/*"})
        """
        pass

    @abstractmethod
    def update_metadata(
        self,
        ids: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Update metadata for existing documents.

        Args:
            ids: List of document IDs to update
            metadatas: List of new metadata dictionaries (one per ID)

        Raises:
            ValueError: If lengths of ids and metadatas don't match
            VectorStoreError: If update fails

        Example:
            >>> store.update_metadata(
            ...     ids=["doc1", "doc2"],
            ...     metadatas=[
            ...         {"category": "research", "priority": "high"},
            ...         {"category": "notes", "priority": "low"}
            ...     ]
            ... )
        """
        pass

    @abstractmethod
    def get_documents_by_metadata(
        self,
        where: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Retrieve documents matching a metadata filter.

        Useful for duplicate detection and metadata-based queries.

        Args:
            where: Metadata filter dictionary

        Returns:
            Dictionary containing:
                - ids: List of matching document IDs
                - documents: List of document texts
                - metadatas: List of metadata dictionaries

        Example:
            >>> # Find documents with specific file hash (duplicate detection)
            >>> results = store.get_documents_by_metadata(
            ...     where={"file_hash": "abc123def456"}
            ... )
            >>> if results["ids"]:
            ...     print("Duplicate found!")
        """
        pass

    @abstractmethod
    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List documents with pagination support.

        Args:
            limit: Maximum number of documents to return (default: 100)
            offset: Number of documents to skip (default: 0)
            where: Optional metadata filter

        Returns:
            Dictionary containing:
                - ids: List of document IDs
                - documents: List of document texts
                - metadatas: List of metadata dictionaries
                - total: Total number of matching documents

        Example:
            >>> # Get first page
            >>> page1 = store.list(limit=50, offset=0)
            >>> # Get second page
            >>> page2 = store.list(limit=50, offset=50)
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get the total number of documents in the vector store.

        Returns:
            Total count of documents

        Example:
            >>> total = store.count()
            >>> print(f"Vector store contains {total} documents")
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all documents from the vector store.

        Warning: This operation is irreversible!

        Raises:
            VectorStoreError: If clear operation fails

        Example:
            >>> # Clear all documents (use with caution!)
            >>> store.clear()
        """
        pass

    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the vector store collection.

        Returns:
            Dictionary containing collection metadata such as:
                - name: Collection name
                - count: Number of documents
                - metadata: Additional backend-specific metadata

        Example:
            >>> info = store.get_collection_info()
            >>> print(f"Collection: {info['name']}, Documents: {info['count']}")
        """
        pass
