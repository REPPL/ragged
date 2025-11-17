"""
Factory for creating embedding models based on configuration.

Provides a simple interface to instantiate the correct embedder
based on application settings.
"""

from typing import Optional

from src.config.settings import EmbeddingModel, get_settings
from src.embeddings.base import BaseEmbedder
from src.embeddings.ollama_embedder import OllamaEmbedder
from src.embeddings.sentence_transformer import SentenceTransformerEmbedder
from src.utils.logging import get_logger

logger = get_logger(__name__)


def create_embedder(
    model_type: Optional[EmbeddingModel] = None,
    model_name: Optional[str] = None,
) -> BaseEmbedder:
    """
    Create an embedder instance based on configuration.

    Args:
        model_type: Type of embedding model (uses config if None)
        model_name: Name of specific model (uses config if None)

    Returns:
        Configured embedder instance

    Raises:
        ValueError: If model_type is not supported

    TODO: Implement factory logic:
          1. Get settings if parameters are None
          2. Check model_type and create appropriate embedder
          3. Log which embedder is being created
          4. Return embedder instance

    Examples:
        >>> embedder = create_embedder()  # Uses config
        >>> embedder = create_embedder(
        ...     model_type=EmbeddingModel.SENTENCE_TRANSFORMERS,
        ...     model_name="all-mpnet-base-v2"
        ... )
    """
    settings = get_settings()

    if model_type is None:
        model_type = settings.embedding_model

    if model_name is None:
        model_name = settings.embedding_model_name

    logger.info(f"Creating embedder: {model_type.value} ({model_name})")

    if model_type == EmbeddingModel.SENTENCE_TRANSFORMERS:
        return SentenceTransformerEmbedder(model_name=model_name)
    elif model_type == EmbeddingModel.OLLAMA:
        return OllamaEmbedder(model_name=model_name)
    else:
        raise ValueError(f"Unsupported embedding model type: {model_type}")


def get_embedder() -> BaseEmbedder:
    """
    Get a cached embedder instance (singleton pattern).

    Returns:
        Embedder instance

    TODO: Implement caching:
          Option 1: Use functools.lru_cache on create_embedder
          Option 2: Implement module-level cache
          For now, just call create_embedder()
    """
    # For v0.1, no caching - just create fresh each time
    return create_embedder()
