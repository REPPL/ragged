"""API error definitions.

Phase 0 Infrastructure: Consistent error handling across all interfaces.

Error Hierarchy:
    APIError (base)
    ├── ServiceNotReadyError - Services not initialised
    ├── QueryError - Query processing failures
    ├── IngestionError - Document ingestion failures
    ├── EmbeddingError - Embedding generation failures
    └── DocumentNotFoundError - Document/chunk not found
"""


class APIError(Exception):
    """Base class for API errors.

    All API errors inherit from this class, enabling consistent
    error handling across CLI, UI, and agent interfaces.

    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        details: Optional additional error details
    """

    def __init__(
        self,
        message: str,
        code: str = "API_ERROR",
        details: dict | None = None,
    ):
        """Initialise API error.

        Args:
            message: Human-readable error message
            code: Error code for programmatic handling
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert error to dictionary for serialisation.

        Returns:
            Dictionary representation of the error
        """
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class ServiceNotReadyError(APIError):
    """Raised when services are not initialised.

    This typically occurs during startup before all components
    are ready, or after a critical failure.
    """

    def __init__(
        self,
        message: str = "Services not initialised. Please wait for startup to complete.",
        details: dict | None = None,
    ):
        """Initialise service not ready error."""
        super().__init__(
            message=message,
            code="SERVICE_NOT_READY",
            details=details,
        )


class QueryError(APIError):
    """Raised when query processing fails.

    May occur due to retrieval failures, LLM errors,
    or invalid query parameters.
    """

    def __init__(
        self,
        message: str,
        query: str | None = None,
        details: dict | None = None,
    ):
        """Initialise query error.

        Args:
            message: Human-readable error message
            query: The query that failed (optional)
            details: Optional additional error details
        """
        error_details = details or {}
        if query:
            error_details["query"] = query

        super().__init__(
            message=message,
            code="QUERY_ERROR",
            details=error_details,
        )


class IngestionError(APIError):
    """Raised when document ingestion fails.

    May occur due to unsupported file formats, parsing errors,
    or storage failures.
    """

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        details: dict | None = None,
    ):
        """Initialise ingestion error.

        Args:
            message: Human-readable error message
            filename: The file that failed to ingest (optional)
            details: Optional additional error details
        """
        error_details = details or {}
        if filename:
            error_details["filename"] = filename

        super().__init__(
            message=message,
            code="INGESTION_ERROR",
            details=error_details,
        )


class EmbeddingError(APIError):
    """Raised when embedding generation fails.

    May occur due to model loading issues, GPU memory errors,
    or invalid input text.
    """

    def __init__(
        self,
        message: str,
        model: str | None = None,
        details: dict | None = None,
    ):
        """Initialise embedding error.

        Args:
            message: Human-readable error message
            model: The embedding model that failed (optional)
            details: Optional additional error details
        """
        error_details = details or {}
        if model:
            error_details["model"] = model

        super().__init__(
            message=message,
            code="EMBEDDING_ERROR",
            details=error_details,
        )


class DocumentNotFoundError(APIError):
    """Raised when a document or chunk is not found.

    May occur when querying for specific document IDs
    that don't exist in the collection.
    """

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        collection: str | None = None,
        details: dict | None = None,
    ):
        """Initialise document not found error.

        Args:
            message: Human-readable error message
            document_id: The document ID that wasn't found (optional)
            collection: The collection that was searched (optional)
            details: Optional additional error details
        """
        error_details = details or {}
        if document_id:
            error_details["document_id"] = document_id
        if collection:
            error_details["collection"] = collection

        super().__init__(
            message=message,
            code="DOCUMENT_NOT_FOUND",
            details=error_details,
        )
