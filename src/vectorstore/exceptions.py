"""Exceptions for VectorStore operations."""


class VectorStoreError(Exception):
    """Base exception for vector store errors."""

    pass


class VectorStoreNotFoundError(VectorStoreError):
    """Raised when a vector store or collection is not found."""

    pass


class VectorStoreConnectionError(VectorStoreError):
    """Raised when connection to vector store fails."""

    pass


class VectorStoreQueryError(VectorStoreError):
    """Raised when a query operation fails."""

    pass


class VectorStoreConfigError(VectorStoreError):
    """Raised when vector store configuration is invalid."""

    pass
