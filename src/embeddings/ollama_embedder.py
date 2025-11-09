"""
Ollama-based embedding implementation.

Uses Ollama API to generate embeddings using models like nomic-embed-text.
"""

import time
from typing import List

import numpy as np

try:
    import ollama
except ImportError:
    ollama = None

from src.config.settings import get_settings
from src.embeddings.base import BaseEmbedder
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaEmbedder(BaseEmbedder):
    """
    Embedding using Ollama API.

    Supports various embedding models available through Ollama including
    nomic-embed-text, mxbai-embed-large, etc.
    """

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str = None,
        timeout: int = 30,
        max_retries: int = 3,
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
        if ollama is None:
            raise ImportError("ollama required: pip install ollama")

        self._model_name = model_name
        self._timeout = timeout
        self._max_retries = max_retries

        settings = get_settings()
        self._base_url = base_url or settings.ollama_url

        # Create Ollama client
        self.client = ollama.Client(host=self._base_url)

        # Verify model and get dimensions
        self._verify_model_available()
        self._dimensions = self._get_dimensions()

    def _verify_model_available(self) -> None:
        """Verify that the embedding model is available in Ollama."""
        try:
            models = self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]

            if not any(self._model_name in name for name in model_names):
                logger.warning(
                    f"Model {self._model_name} not found. "
                    f"Install with: ollama pull {self._model_name}"
                )
        except Exception as e:
            logger.warning(f"Could not verify model availability: {e}")

    def _get_dimensions(self) -> int:
        """Get embedding dimensions by making a test embedding."""
        try:
            test_embedding = self.embed_text("test")
            return len(test_embedding)
        except Exception:
            # Default for nomic-embed-text
            logger.warning("Could not determine dimensions, using default 768")
            return 768

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string with retry logic."""
        for attempt in range(self._max_retries):
            try:
                response = self.client.embeddings(
                    model=self._model_name,
                    prompt=text
                )
                return np.array(response['embedding'], dtype=np.float32)
            except Exception as e:
                if attempt == self._max_retries - 1:
                    logger.error(f"Failed to embed after {self._max_retries} attempts: {e}")
                    raise
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {wait_time}s")
                time.sleep(wait_time)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
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
