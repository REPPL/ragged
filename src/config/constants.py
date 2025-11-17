"""Application-wide constants and configuration values.

Centralises magic numbers to improve maintainability and configurability.
"""

# Memory Management
DEFAULT_MEMORY_LIMIT_PERCENTAGE = 0.8  # Use 80% of available RAM by default

# Network & API Timeouts (seconds)
DEFAULT_API_TIMEOUT = 30  # Default timeout for API calls
SHORT_API_TIMEOUT = 5  # Quick timeout for health checks
LONG_API_TIMEOUT = 60  # Extended timeout for upload/processing operations

# Retry Configuration
DEFAULT_MAX_RETRIES = 3  # Default retry attempts for failed operations
EXPONENTIAL_BACKOFF_BASE = 2  # Base for exponential backoff: wait = base ** attempt

# LLM Generation Parameters
DEFAULT_LLM_TEMPERATURE = 0.7  # Default sampling temperature (0.0-1.0)

# Web UI Retry Configuration
UI_STARTUP_MAX_RETRIES = 10  # Max retries when waiting for API startup
UI_STARTUP_RETRY_DELAY = 2.0  # Delay between startup retries (seconds)
UI_HEALTH_CHECK_MAX_RETRIES = 1  # Quick health check attempts
UI_HEALTH_CHECK_RETRY_DELAY = 0.5  # Quick health check delay (seconds)

# Embedding Dimensions (for common models)
DEFAULT_EMBEDDING_DIMENSION = 768  # Default dimension for most embedding models
FALLBACK_EMBEDDING_DIMENSION = 384  # Fallback dimension when embeddings unavailable
EMBEDDING_DIMENSIONS = {
    "all-mpnet-base-v2": 768,
    "all-MiniLM-L6-v2": 384,  # Lightweight model commonly used
    "nomic-embed-text": 768,
}
