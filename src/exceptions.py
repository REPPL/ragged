"""Custom exceptions for ragged.

Provides a hierarchical exception system with specific error types
for different components of the RAG system.
"""

from typing import Any, Optional


class RaggedError(Exception):
    """Base exception for all ragged errors.

    All custom exceptions inherit from this base class,
    making it easy to catch any ragged-specific error.
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """Initialise error with message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dictionary with error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with details."""
        if not self.details:
            return self.message

        details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
        return f"{self.message} ({details_str})"


# Ingestion Errors

class IngestionError(RaggedError):
    """Base exception for document ingestion errors."""
    pass


class DocumentLoadError(IngestionError):
    """Failed to load document from file."""
    pass


class DocumentParseError(IngestionError):
    """Failed to parse document content."""
    pass


class ChunkingError(IngestionError):
    """Failed to chunk document."""
    pass


class UnsupportedFormatError(IngestionError):
    """Document format not supported."""

    def __init__(self, format: str, supported_formats: Optional[list[str]] = None):
        """Initialise with format information.

        Args:
            format: The unsupported format
            supported_formats: List of supported formats
        """
        self.format = format
        self.supported_formats = supported_formats or []

        if self.supported_formats:
            message = f"Format '{format}' not supported. Supported: {', '.join(self.supported_formats)}"
        else:
            message = f"Format '{format}' not supported"

        super().__init__(message, {"format": format})


class BatchProcessingError(IngestionError):
    """Batch processing failed."""
    pass


# Storage Errors

class StorageError(RaggedError):
    """Base exception for storage errors."""
    pass


class VectorStoreError(StorageError):
    """Vector store operation failed."""
    pass


class VectorStoreConnectionError(VectorStoreError):
    """Failed to connect to vector store."""
    pass


class EmbeddingError(StorageError):
    """Failed to generate or store embeddings."""
    pass


class MetadataSerialisationError(StorageError):
    """Failed to serialise metadata for storage."""
    pass


# Retrieval Errors

class RetrievalError(RaggedError):
    """Base exception for retrieval errors."""
    pass


class QueryError(RetrievalError):
    """Query processing failed."""
    pass


class SearchError(RetrievalError):
    """Search operation failed."""
    pass


class NoResultsError(RetrievalError):
    """No results found for query."""

    def __init__(self, query: str):
        """Initialise with query that returned no results.

        Args:
            query: The search query
        """
        super().__init__(
            f"No results found for query",
            {"query": query}
        )


class RerankingError(RetrievalError):
    """Result reranking failed."""
    pass


# Generation Errors

class GenerationError(RaggedError):
    """Base exception for text generation errors."""
    pass


class LLMConnectionError(GenerationError):
    """Failed to connect to LLM service."""
    pass


class LLMGenerationError(GenerationError):
    """LLM text generation failed."""
    pass


class PromptError(GenerationError):
    """Prompt construction or validation failed."""
    pass


class ModelNotFoundError(GenerationError):
    """Requested model not available."""

    def __init__(self, model: str, available_models: Optional[list[str]] = None):
        """Initialise with model information.

        Args:
            model: The requested model
            available_models: List of available models
        """
        self.model = model
        self.available_models = available_models or []

        if self.available_models:
            message = f"Model '{model}' not found. Available: {', '.join(self.available_models)}"
        else:
            message = f"Model '{model}' not found"

        super().__init__(message, {"model": model})


# Configuration Errors

class ConfigurationError(RaggedError):
    """Base exception for configuration errors."""
    pass


class InvalidConfigError(ConfigurationError):
    """Configuration validation failed."""
    pass


class MissingConfigError(ConfigurationError):
    """Required configuration missing."""

    def __init__(self, key: str):
        """Initialise with missing config key.

        Args:
            key: The missing configuration key
        """
        super().__init__(
            f"Required configuration missing: {key}",
            {"key": key}
        )


class PathConfigError(ConfigurationError):
    """Path configuration invalid."""
    pass


# Validation Errors

class ValidationError(RaggedError):
    """Base exception for validation errors."""
    pass


class InvalidInputError(ValidationError):
    """Input validation failed."""
    pass


class InvalidPathError(ValidationError):
    """Path validation failed."""
    pass


# Resource Errors

class ResourceError(RaggedError):
    """Base exception for resource errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Required resource not found."""
    pass


class ResourceExhaustedError(ResourceError):
    """Resource limits exceeded (memory, disk, etc.)."""
    pass


class MemoryLimitExceededError(ResourceExhaustedError):
    """Memory limit exceeded during operation."""

    def __init__(self, operation: str, limit_mb: int, usage_mb: int):
        """Initialise with memory information.

        Args:
            operation: Operation that exceeded limit
            limit_mb: Memory limit in MB
            usage_mb: Actual usage in MB
        """
        super().__init__(
            f"Memory limit exceeded during {operation}",
            {
                "operation": operation,
                "limit_mb": limit_mb,
                "usage_mb": usage_mb
            }
        )


# API Errors

class APIError(RaggedError):
    """Base exception for API errors."""
    pass


class ServiceNotInitializedError(APIError):
    """Required service not initialised."""

    def __init__(self, service: str):
        """Initialise with service name.

        Args:
            service: Name of uninitialised service
        """
        super().__init__(
            f"Service not initialised: {service}",
            {"service": service}
        )


class RequestValidationError(APIError):
    """API request validation failed."""
    pass


# Helper Functions

def wrap_exception(error: Exception, context: Optional[str] = None) -> RaggedError:
    """Wrap a generic exception in a RaggedError.

    Useful for converting third-party exceptions to our hierarchy.

    Args:
        error: Original exception
        context: Optional context description

    Returns:
        RaggedError with wrapped exception
    """
    message = f"{context}: {str(error)}" if context else str(error)
    details = {
        "original_type": type(error).__name__,
        "original_message": str(error)
    }

    if context:
        details["context"] = context

    return RaggedError(message, details)
