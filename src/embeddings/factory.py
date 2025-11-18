"""
Factory for creating embedding models based on configuration.

Provides a simple interface to instantiate the correct embedder
based on application settings, with optional singleton caching
for 4-30x performance improvement (v0.2.9).
"""

import threading
from collections import OrderedDict
from typing import Dict, Optional

from src.config.settings import EmbeddingModel, get_settings
from src.embeddings.base import BaseEmbedder
from src.embeddings.ollama_embedder import OllamaEmbedder
from src.embeddings.sentence_transformer import SentenceTransformerEmbedder
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Module-level cache for singleton pattern (v0.2.9)
_embedder_cache: OrderedDict[str, BaseEmbedder] = OrderedDict()
_cache_lock = threading.Lock()
_warmup_started = False
_max_cache_size = 3  # Maximum number of models to cache (LRU eviction)


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


def get_embedder(
    model_type: Optional[EmbeddingModel] = None,
    model_name: Optional[str] = None
) -> BaseEmbedder:
    """
    Get a cached embedder instance (singleton pattern).

    v0.2.9: Implements singleton caching for 4-30x performance improvement.
    - Cold start: ~2-3s → <0.5s (4-6x faster)
    - Warm start: ~2-3s → <0.1s (20-30x faster)

    Args:
        model_type: Type of embedding model (uses config if None)
        model_name: Name of specific model (uses config if None)

    Returns:
        Embedder instance (cached if feature enabled)

    Example:
        >>> embedder = get_embedder()  # Uses cached instance
        >>> embedder.embed_text("hello")  # Instant (no model reload)
    """
    settings = get_settings()

    # Feature flag check (v0.2.9)
    if not settings.feature_flags.enable_embedder_caching:
        # Fallback to old behaviour (recreate every time)
        logger.debug("Embedder caching disabled, creating fresh instance")
        return create_embedder(model_type, model_name)

    # Determine cache key
    if model_type is None:
        model_type = settings.embedding_model
    if model_name is None:
        model_name = settings.embedding_model_name

    cache_key = f"{model_type.value}:{model_name}"

    # Thread-safe cache access
    with _cache_lock:
        if cache_key in _embedder_cache:
            # Move to end (mark as recently used)
            _embedder_cache.move_to_end(cache_key)
            logger.debug(f"Returning cached embedder (key: {cache_key})")
            return _embedder_cache[cache_key]

        # Not in cache - need to create
        logger.info(f"Creating and caching new embedder: {cache_key}")

        # Check if cache is full - evict LRU if needed
        if len(_embedder_cache) >= _max_cache_size:
            lru_key = next(iter(_embedder_cache))
            logger.info(f"Cache full, evicting LRU embedder: {lru_key}")
            del _embedder_cache[lru_key]

        # Create and cache new embedder
        _embedder_cache[cache_key] = create_embedder(model_type, model_name)
        logger.info(f"Embedder cached (key: {cache_key})")

        return _embedder_cache[cache_key]


def clear_embedder_cache() -> int:
    """
    Clear the embedder cache.

    Useful for freeing memory or forcing model reload.

    Returns:
        Number of cached embedders that were cleared

    Example:
        >>> count = clear_embedder_cache()
        >>> print(f"Cleared {count} cached embedders")
    """
    with _cache_lock:
        count = len(_embedder_cache)
        _embedder_cache.clear()
        if count > 0:
            logger.info(f"Cleared {count} cached embedder(s)")
        return count


def get_cache_stats() -> Dict[str, any]:
    """
    Get embedder cache statistics.

    Returns:
        Dictionary with cache stats (size, keys)

    Example:
        >>> stats = get_cache_stats()
        >>> print(f"Cached models: {stats['size']}")
    """
    with _cache_lock:
        return {
            "size": len(_embedder_cache),
            "models": list(_embedder_cache.keys()),
            "enabled": get_settings().feature_flags.enable_embedder_caching
        }


def warmup_embedder_cache() -> None:
    """
    Warm up the embedder cache by preloading the default model.

    v0.2.9: Progressive warm-up - preload embedder in background thread
    to eliminate cold start penalty on first query.

    This function is safe to call multiple times (idempotent).

    Example:
        >>> warmup_embedder_cache()  # Preload in background
        >>> # Later queries will be instant
    """
    global _warmup_started

    settings = get_settings()

    # Only warm up if caching is enabled
    if not settings.feature_flags.enable_embedder_caching:
        logger.debug("Embedder caching disabled, skipping warm-up")
        return

    # Prevent multiple warm-up threads
    with _cache_lock:
        if _warmup_started:
            logger.debug("Warm-up already started, skipping")
            return
        _warmup_started = True

    def _warmup_thread():
        """Background thread to preload embedder."""
        try:
            logger.info("Starting embedder warm-up (background)")
            # Preload the default embedder
            get_embedder()
            logger.info("Embedder warm-up complete")
        except Exception as e:
            logger.warning(f"Embedder warm-up failed: {e}")
            # Reset flag so it can be retried
            global _warmup_started
            with _cache_lock:
                _warmup_started = False

    # Start background thread (daemon so it doesn't block shutdown)
    thread = threading.Thread(target=_warmup_thread, daemon=True, name="EmbedderWarmup")
    thread.start()
    logger.debug("Embedder warm-up thread started")
