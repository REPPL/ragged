"""Tests for custom exception system."""

import pytest
from src.exceptions import (
    # Base
    RaggedError,
    # Ingestion
    IngestionError,
    DocumentLoadError,
    DocumentParseError,
    ChunkingError,
    UnsupportedFormatError,
    BatchProcessingError,
    # Storage
    StorageError,
    VectorStoreError,
    VectorStoreConnectionError,
    EmbeddingError,
    MetadataSerialisationError,
    # Retrieval
    RetrievalError,
    QueryError,
    SearchError,
    NoResultsError,
    RerankingError,
    # Generation
    GenerationError,
    LLMConnectionError,
    LLMGenerationError,
    PromptError,
    ModelNotFoundError,
    # Configuration
    ConfigurationError,
    InvalidConfigError,
    MissingConfigError,
    PathConfigError,
    # Validation
    ValidationError,
    InvalidInputError,
    InvalidPathError,
    # Resource
    ResourceError,
    ResourceNotFoundError,
    ResourceExhaustedError,
    MemoryLimitExceededError,
    # API
    APIError,
    ServiceNotInitialisedError,
    RequestValidationError,
    # Helper
    wrap_exception,
)


class TestBaseException:
    """Tests for base RaggedError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = RaggedError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self):
        """Test error with details dictionary."""
        error = RaggedError("Test error", {"key": "value", "count": 5})
        assert error.message == "Test error"
        assert error.details == {"key": "value", "count": 5}
        assert "key=value" in str(error)
        assert "count=5" in str(error)

    def test_error_inheritance(self):
        """Test that all errors inherit from RaggedError."""
        error = IngestionError("test")
        assert isinstance(error, RaggedError)
        assert isinstance(error, Exception)


class TestIngestionErrors:
    """Tests for ingestion-related exceptions."""

    def test_document_load_error(self):
        """Test DocumentLoadError."""
        error = DocumentLoadError("Failed to load", {"path": "/path/to/file.pdf"})
        assert isinstance(error, IngestionError)
        assert "Failed to load" in str(error)
        assert "path=/path/to/file.pdf" in str(error)

    def test_document_parse_error(self):
        """Test DocumentParseError."""
        error = DocumentParseError("Parse failed")
        assert isinstance(error, IngestionError)

    def test_chunking_error(self):
        """Test ChunkingError."""
        error = ChunkingError("Chunking failed", {"chunk_size": 512})
        assert isinstance(error, IngestionError)
        assert "chunk_size=512" in str(error)

    def test_unsupported_format_error(self):
        """Test UnsupportedFormatError with supported formats."""
        error = UnsupportedFormatError(".docx", ["pdf", "txt", "md"])
        assert isinstance(error, IngestionError)
        assert ".docx" in str(error)
        assert "pdf" in str(error)
        assert "txt" in str(error)
        assert error.format == ".docx"
        assert error.supported_formats == ["pdf", "txt", "md"]

    def test_unsupported_format_error_no_list(self):
        """Test UnsupportedFormatError without supported list."""
        error = UnsupportedFormatError(".docx")
        assert ".docx" in str(error)
        assert error.supported_formats == []

    def test_batch_processing_error(self):
        """Test BatchProcessingError."""
        error = BatchProcessingError("Batch failed", {"batch_size": 100})
        assert isinstance(error, IngestionError)


class TestStorageErrors:
    """Tests for storage-related exceptions."""

    def test_vector_store_error(self):
        """Test VectorStoreError."""
        error = VectorStoreError("Store failed")
        assert isinstance(error, StorageError)

    def test_vector_store_connection_error(self):
        """Test VectorStoreConnectionError."""
        error = VectorStoreConnectionError("Connection failed", {"host": "localhost"})
        assert isinstance(error, VectorStoreError)
        assert isinstance(error, StorageError)

    def test_embedding_error(self):
        """Test EmbeddingError."""
        error = EmbeddingError("Embedding failed")
        assert isinstance(error, StorageError)

    def test_metadata_serialisation_error(self):
        """Test MetadataSerialisationError."""
        error = MetadataSerialisationError("Serialisation failed")
        assert isinstance(error, StorageError)


class TestRetrievalErrors:
    """Tests for retrieval-related exceptions."""

    def test_query_error(self):
        """Test QueryError."""
        error = QueryError("Query failed", {"query": "test"})
        assert isinstance(error, RetrievalError)

    def test_search_error(self):
        """Test SearchError."""
        error = SearchError("Search failed")
        assert isinstance(error, RetrievalError)

    def test_no_results_error(self):
        """Test NoResultsError."""
        error = NoResultsError("machine learning")
        assert isinstance(error, RetrievalError)
        assert "No results found" in str(error)
        assert "machine learning" in str(error)
        assert error.details["query"] == "machine learning"

    def test_reranking_error(self):
        """Test RerankingError."""
        error = RerankingError("Reranking failed")
        assert isinstance(error, RetrievalError)


class TestGenerationErrors:
    """Tests for generation-related exceptions."""

    def test_llm_connection_error(self):
        """Test LLMConnectionError."""
        error = LLMConnectionError("Connection failed", {"url": "http://localhost:11434"})
        assert isinstance(error, GenerationError)

    def test_llm_generation_error(self):
        """Test LLMGenerationError."""
        error = LLMGenerationError("Generation failed")
        assert isinstance(error, GenerationError)

    def test_prompt_error(self):
        """Test PromptError."""
        error = PromptError("Invalid prompt")
        assert isinstance(error, GenerationError)

    def test_model_not_found_error_with_list(self):
        """Test ModelNotFoundError with available models."""
        error = ModelNotFoundError("llama3:latest", ["mistral:7b", "qwen:2.5b"])
        assert isinstance(error, GenerationError)
        assert "llama3:latest" in str(error)
        assert "mistral:7b" in str(error)
        assert error.model == "llama3:latest"
        assert error.available_models == ["mistral:7b", "qwen:2.5b"]

    def test_model_not_found_error_no_list(self):
        """Test ModelNotFoundError without available models."""
        error = ModelNotFoundError("llama3:latest")
        assert "llama3:latest" in str(error)
        assert error.available_models == []


class TestConfigurationErrors:
    """Tests for configuration-related exceptions."""

    def test_invalid_config_error(self):
        """Test InvalidConfigError."""
        error = InvalidConfigError("Invalid config")
        assert isinstance(error, ConfigurationError)

    def test_missing_config_error(self):
        """Test MissingConfigError."""
        error = MissingConfigError("RAGGED_DATA_DIR")
        assert isinstance(error, ConfigurationError)
        assert "RAGGED_DATA_DIR" in str(error)
        assert error.details["key"] == "RAGGED_DATA_DIR"

    def test_path_config_error(self):
        """Test PathConfigError."""
        error = PathConfigError("Invalid path")
        assert isinstance(error, ConfigurationError)


class TestValidationErrors:
    """Tests for validation-related exceptions."""

    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        error = InvalidInputError("Input validation failed")
        assert isinstance(error, ValidationError)

    def test_invalid_path_error(self):
        """Test InvalidPathError."""
        error = InvalidPathError("Invalid path", {"path": "/invalid"})
        assert isinstance(error, ValidationError)


class TestResourceErrors:
    """Tests for resource-related exceptions."""

    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError."""
        error = ResourceNotFoundError("Resource not found")
        assert isinstance(error, ResourceError)

    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError."""
        error = ResourceExhaustedError("Resource exhausted")
        assert isinstance(error, ResourceError)

    def test_memory_limit_exceeded_error(self):
        """Test MemoryLimitExceededError."""
        error = MemoryLimitExceededError("batch_processing", 500, 750)
        assert isinstance(error, ResourceExhaustedError)
        assert isinstance(error, ResourceError)
        assert "batch_processing" in str(error)
        assert error.details["operation"] == "batch_processing"
        assert error.details["limit_mb"] == 500
        assert error.details["usage_mb"] == 750


class TestAPIErrors:
    """Tests for API-related exceptions."""

    def test_service_not_initialised_error(self):
        """Test ServiceNotInitialisedError."""
        error = ServiceNotInitialisedError("vector_store")
        assert isinstance(error, APIError)
        assert "vector_store" in str(error)
        assert error.details["service"] == "vector_store"

    def test_request_validation_error(self):
        """Test RequestValidationError."""
        error = RequestValidationError("Invalid request")
        assert isinstance(error, APIError)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_wrap_exception_basic(self):
        """Test wrapping a basic exception."""
        original = ValueError("Invalid value")
        wrapped = wrap_exception(original)

        assert isinstance(wrapped, RaggedError)
        assert "Invalid value" in str(wrapped)
        assert wrapped.details["original_type"] == "ValueError"
        assert wrapped.details["original_message"] == "Invalid value"

    def test_wrap_exception_with_context(self):
        """Test wrapping an exception with context."""
        original = FileNotFoundError("File not found")
        wrapped = wrap_exception(original, "Loading document")

        assert isinstance(wrapped, RaggedError)
        assert "Loading document" in str(wrapped)
        assert "File not found" in str(wrapped)
        assert wrapped.details["context"] == "Loading document"
        assert wrapped.details["original_type"] == "FileNotFoundError"

    def test_wrap_exception_preserves_type(self):
        """Test that wrapping preserves original type information."""
        original = KeyError("missing_key")
        wrapped = wrap_exception(original, "Config lookup")

        assert wrapped.details["original_type"] == "KeyError"
        assert "KeyError" not in str(RaggedError.__name__)  # Not in hierarchy


class TestExceptionHierarchy:
    """Tests for exception hierarchy structure."""

    def test_catch_all_ragged_errors(self):
        """Test that all errors can be caught with RaggedError."""
        errors = [
            DocumentLoadError("test"),
            VectorStoreError("test"),
            QueryError("test"),
            LLMConnectionError("test"),
            InvalidConfigError("test"),
            ResourceNotFoundError("test"),
        ]

        for error in errors:
            assert isinstance(error, RaggedError)

    def test_catch_specific_category(self):
        """Test catching specific error categories."""
        # All ingestion errors
        ingestion_errors = [
            DocumentLoadError("test"),
            DocumentParseError("test"),
            ChunkingError("test"),
        ]

        for error in ingestion_errors:
            assert isinstance(error, IngestionError)
            assert isinstance(error, RaggedError)

    def test_error_hierarchy_depth(self):
        """Test multi-level hierarchy."""
        error = VectorStoreConnectionError("test")

        # Three levels: VectorStoreConnectionError -> VectorStoreError -> StorageError -> RaggedError
        assert isinstance(error, VectorStoreConnectionError)
        assert isinstance(error, VectorStoreError)
        assert isinstance(error, StorageError)
        assert isinstance(error, RaggedError)
        assert isinstance(error, Exception)


class TestErrorContextPreservation:
    """Tests for error context and details preservation."""

    def test_details_preserved(self):
        """Test that details are preserved through hierarchy."""
        error = DocumentLoadError("Failed", {"path": "/test", "format": "pdf"})

        assert error.details["path"] == "/test"
        assert error.details["format"] == "pdf"

    def test_empty_details_dict(self):
        """Test that errors work with no details."""
        error = QueryError("Failed")
        assert error.details == {}
        assert str(error) == "Failed"

    def test_details_in_message(self):
        """Test that details appear in formatted message."""
        error = MemoryLimitExceededError("ingestion", 100, 150)

        message = str(error)
        assert "ingestion" in message
        assert "limit_mb=100" in message
        assert "usage_mb=150" in message
