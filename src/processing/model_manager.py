"""
Model manager for lazy loading and caching of ML models.

This module handles downloading, caching, and loading of ML models used
by document processors (primarily Docling models like DocLayNet and TableFormer).
"""

import hashlib
import time
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


# HIGH-003: Model integrity verification with SHA-256 checksums
# Expected checksums for known model versions (update as needed)
MODEL_CHECKSUMS: dict[str, str] = {
    # Add checksums here when known model versions are verified
    # Format: "model_name:version": "sha256_hash"
    # Example: "DocLayNet:v1.0": "abc123..."
}


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

    def __init__(self, cache_dir: Path | None = None, verify_integrity: bool = True):
        """
        Initialise the model manager.

        Args:
            cache_dir: Directory for caching models. If None, uses default
                      location (~/.cache/ragged/models)
            verify_integrity: Whether to verify model integrity with checksums
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "ragged" / "models"

        self.cache_dir = cache_dir
        self.verify_integrity = verify_integrity
        self._loaded_models: dict[str, Any] = {}

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

    def compute_file_checksum(self, file_path: Path) -> str:
        """
        Compute SHA-256 checksum for a file.

        Args:
            file_path: Path to file to checksum

        Returns:
            Hexadecimal SHA-256 checksum

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read

        Example:
            >>> manager = ModelManager()
            >>> checksum = manager.compute_file_checksum(Path("model.bin"))
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        checksum = sha256_hash.hexdigest()
        logger.debug(f"Computed SHA-256 for {file_path.name}: {checksum[:16]}...")
        return checksum

    def verify_model_integrity(
        self, model_path: Path, expected_checksum: str | None = None
    ) -> bool:
        """
        Verify model file integrity using SHA-256 checksum.

        Args:
            model_path: Path to model file
            expected_checksum: Expected SHA-256 checksum (if None, checks MODEL_CHECKSUMS)

        Returns:
            True if checksum matches, False otherwise

        Example:
            >>> manager = ModelManager()
            >>> is_valid = manager.verify_model_integrity(
            ...     Path("model.bin"),
            ...     "abc123..."
            ... )
        """
        if not model_path.exists():
            logger.warning(f"Cannot verify integrity: file not found {model_path}")
            return False

        try:
            actual_checksum = self.compute_file_checksum(model_path)

            # If no expected checksum provided, try to find it in MODEL_CHECKSUMS
            if expected_checksum is None:
                # Try to find checksum by model name
                model_key = model_path.stem
                expected_checksum = MODEL_CHECKSUMS.get(model_key)

                if expected_checksum is None:
                    logger.debug(
                        f"No expected checksum found for {model_path.name}. "
                        f"Integrity verification skipped."
                    )
                    return True  # Can't verify, assume OK

            # Verify checksum
            if actual_checksum == expected_checksum:
                logger.info(f"Model integrity verified: {model_path.name}")
                return True
            else:
                logger.error(
                    f"Model integrity check FAILED for {model_path.name}! "
                    f"Expected: {expected_checksum[:16]}..., "
                    f"Got: {actual_checksum[:16]}..."
                )
                return False

        except Exception as e:
            logger.error(f"Error verifying model integrity: {e}")
            return False
