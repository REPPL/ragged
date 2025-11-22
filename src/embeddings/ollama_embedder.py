"""
Ollama-based embedding implementation.

Uses Ollama API to generate embeddings using models like nomic-embed-text.
"""

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import ollama as ollama_module
else:
    try:
        import ollama as ollama_module
    except ImportError:
        ollama_module = None  # type: ignore[assignment]

from src.config.constants import (
    DEFAULT_API_TIMEOUT,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_MAX_RETRIES,
)
from src.config.settings import get_settings
from src.embeddings.base import BaseEmbedder
from src.exceptions import EmbeddingError, LLMConnectionError
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.logging import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


# v0.2.9: Circuit breaker for Ollama API protection
_ollama_circuit_breaker = CircuitBreaker(
    name="ollama_embeddings",
    failure_threshold=5,
    recovery_timeout=30.0,
)


class OllamaEmbedder(BaseEmbedder):
    """
    Embedding using Ollama API.

    Supports various embedding models available through Ollama including
    nomic-embed-text, mxbai-embed-large, etc.
    """

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str | None = None,
        timeout: int = DEFAULT_API_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize Ollama embedder.

        Args:
            model_name: Name of Ollama embedding model
            base_url: Ollama API base URL (uses config if None)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        TODO: Implement initialization:
              1. Get base_url from config if not provided
              2. Create Ollama client
              3. Verify model is available
        """
        if ollama_module is None:
            raise ImportError("ollama required: pip install ollama")

        self._model_name = model_name
        self._timeout = timeout
        self._max_retries = max_retries

        settings = get_settings()
        self._base_url = base_url or settings.ollama_url

        # Create Ollama client
        self.client = ollama_module.Client(host=self._base_url)

        # Verify model and get dimensions
        self._verify_model_available()
        self._dimensions = self._get_dimensions()

    def _verify_model_available(self) -> None:
        """Verify that the embedding model is available in Ollama."""
        try:
            models = self.client.list()
            model_names = [m.model for m in models.models if m.model is not None]

            if not any(self._model_name in name for name in model_names):
                logger.warning(
                    f"Model {self._model_name} not found. "
                    f"Install with: ollama pull {self._model_name}"
                )
        except (ConnectionError, TimeoutError, AttributeError) as e:
            logger.warning(f"Could not verify model availability: {e}")

    def _get_dimensions(self) -> int:
        """Get embedding dimensions by making a test embedding."""
        try:
            test_embedding = self.embed_text("test")
            return len(test_embedding)
        except (ConnectionError, TimeoutError, KeyError, ValueError, TypeError):
            # Default for nomic-embed-text
            logger.warning(f"Could not determine dimensions, using default {DEFAULT_EMBEDDING_DIMENSION}")
            return DEFAULT_EMBEDDING_DIMENSION

    @with_retry(max_attempts=3, base_delay=1.0, retryable_exceptions=(ConnectionError, TimeoutError, LLMConnectionError, EmbeddingError))
    def _embed_text_internal(self, text: str) -> np.ndarray:
        """
        Internal method to embed text with circuit breaker protection.

        v0.2.9: Protected by circuit breaker and retry decorator for >98% success rate.
        """
        try:
            response = _ollama_circuit_breaker.call(
                self.client.embeddings,
                model=self._model_name,
                prompt=text
            )
            return np.array(response['embedding'], dtype=np.float32)
        except (KeyError, ValueError, TypeError) as e:
            raise EmbeddingError(f"Invalid embedding response: {e}")
        except (ConnectionError, TimeoutError) as e:
            raise LLMConnectionError(f"Ollama connection failed: {e}")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        v0.2.9: Uses automatic retry with exponential backoff and circuit breaker.
        """
        settings = get_settings()
        if not settings.feature_flags.enable_advanced_error_recovery:
            # Fallback to old behaviour
            try:
                response = self.client.embeddings(
                    model=self._model_name,
                    prompt=text
                )
                return np.array(response['embedding'], dtype=np.float32)
            except Exception as e:
                logger.error(f"Embedding failed: {e}")
                raise

        # v0.2.9: Use advanced error recovery
        return self._embed_text_internal(text)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed multiple texts (calls embed_text for each)."""
        embeddings = []

        for i, text in enumerate(texts):
            if i > 0 and i % 100 == 0:
                logger.info(f"Embedded {i}/{len(texts)} texts")

            embedding = self.embed_text(text)
            embeddings.append(embedding)

        return np.array(embeddings, dtype=np.float32)

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name
