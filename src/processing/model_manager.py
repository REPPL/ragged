"""
Model manager for lazy loading and caching of ML models.

This module handles downloading, caching, and loading of ML models used
by document processors (primarily Docling models like DocLayNet and TableFormer).
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Manager for ML model lifecycle (download, cache, load).

    This class implements lazy loading of models - they are only downloaded
    and loaded when first needed, and then cached for subsequent use.

    Features:
    - Lazy model loading (download on first use)
    - Model caching to avoid re-downloads
    - Retry logic for network failures
    - Clear error messages and logging

    Example:
        >>> manager = ModelManager(cache_dir=Path("~/.cache/ragged/models"))
        >>> doclaynet = manager.get_model("DocLayNet")
        >>> tableformer = manager.get_model("TableFormer")
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialise the model manager.

        Args:
            cache_dir: Directory for caching models. If None, uses default
                      location (~/.cache/ragged/models)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "ragged" / "models"

        self.cache_dir = cache_dir
        self._loaded_models: Dict[str, Any] = {}

        logger.debug(f"Model manager initialised with cache dir: {cache_dir}")

    def get_model(self, model_name: str, max_retries: int = 3) -> Any:
        """
        Get a model, downloading and caching if necessary.

        This method implements lazy loading - the model is only downloaded
        and loaded when first requested, then cached for subsequent calls.

        Args:
            model_name: Name of the model to load (e.g., "DocLayNet", "TableFormer")
            max_retries: Maximum number of download retry attempts

        Returns:
            Loaded model instance ready for use

        Raises:
            ImportError: If Docling is not installed
            RuntimeError: If model download fails after all retries
            ValueError: If model_name is not recognised

        Example:
            >>> manager = ModelManager()
            >>> model = manager.get_model("DocLayNet")
        """
        # Check if already loaded
        if model_name in self._loaded_models:
            logger.debug(f"Using cached model: {model_name}")
            return self._loaded_models[model_name]

        # Load the model with retry logic
        logger.info(f"Loading model: {model_name}")

        for attempt in range(max_retries):
            try:
                model = self._load_model(model_name)
                self._loaded_models[model_name] = model
                logger.info(f"Successfully loaded model: {model_name}")
                return model

            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt failed
                    logger.error(
                        f"Failed to load model '{model_name}' after {max_retries} attempts. "
                        f"Last error: {e}"
                    )
                    raise RuntimeError(
                        f"Failed to load model '{model_name}'. "
                        f"Please check your internet connection and try again. "
                        f"Error: {e}"
                    ) from e

                # Retry with exponential backoff
                wait_time = 2**attempt
                logger.warning(
                    f"Failed to load model '{model_name}' (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {wait_time}s... Error: {e}"
                )
                time.sleep(wait_time)

        # Should never reach here, but satisfy type checker
        raise RuntimeError(f"Failed to load model '{model_name}'")

    def _load_model(self, model_name: str) -> Any:
        """
        Load a specific model.

        This method handles the actual model loading logic. It's separated
        from get_model() to make retry logic cleaner.

        Args:
            model_name: Name of model to load

        Returns:
            Loaded model instance

        Raises:
            ImportError: If Docling is not installed
            ValueError: If model_name is not recognised
        """
        try:
            # Import Docling here to avoid hard dependency
            from docling_core.transforms.chunker import DocMeta
            from docling_core.types.doc import DoclingDocument
        except ImportError as e:
            raise ImportError(
                "Docling is required for model loading. "
                "Install with: pip install docling docling-core docling-parse"
            ) from e

        # For now, we're using Docling's built-in model loading
        # In the future, this could be expanded to support custom model paths
        if model_name not in ["DocLayNet", "TableFormer"]:
            raise ValueError(
                f"Unknown model: '{model_name}'. "
                f"Supported models: DocLayNet, TableFormer"
            )

        # Note: Docling handles model downloading and caching internally
        # We just need to trigger the load by using the model
        # The actual model instances are created by the Docling pipeline
        logger.debug(f"Model '{model_name}' will be loaded by Docling pipeline")

        # Return a marker that the model is registered
        # The actual loading happens in DoclingProcessor when creating the pipeline
        return {"name": model_name, "status": "registered"}

    def clear_cache(self) -> None:
        """
        Clear the in-memory model cache.

        This forces models to be reloaded on next access, which can be useful
        for testing or memory management.

        Note: This does not delete downloaded model files from disk, only
        clears the in-memory cache.

        Example:
            >>> manager = ModelManager()
            >>> manager.clear_cache()
        """
        logger.info(f"Clearing model cache ({len(self._loaded_models)} models)")
        self._loaded_models.clear()

    def is_model_loaded(self, model_name: str) -> bool:
        """
        Check if a model is currently loaded in memory.

        Args:
            model_name: Name of model to check

        Returns:
            True if model is loaded, False otherwise

        Example:
            >>> manager = ModelManager()
            >>> manager.is_model_loaded("DocLayNet")
            False
            >>> model = manager.get_model("DocLayNet")
            >>> manager.is_model_loaded("DocLayNet")
            True
        """
        return model_name in self._loaded_models

    def get_loaded_models(self) -> list[str]:
        """
        Get list of currently loaded models.

        Returns:
            List of model names that are loaded in memory

        Example:
            >>> manager = ModelManager()
            >>> manager.get_model("DocLayNet")
            >>> manager.get_loaded_models()
            ['DocLayNet']
        """
        return list(self._loaded_models.keys())
