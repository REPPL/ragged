"""
SentenceTransformer-based embedding implementation.

Uses the sentence-transformers library to generate embeddings locally
on CPU or GPU.
"""

from typing import TYPE_CHECKING, cast

import numpy as np

if TYPE_CHECKING:
    import torch as torch_module
    from sentence_transformers import SentenceTransformer as SentenceTransformerType
else:
    try:
        import torch as torch_module
        from sentence_transformers import SentenceTransformer as SentenceTransformerType
    except ImportError:
        SentenceTransformerType = None  # type: ignore[assignment, misc]
        torch_module = None  # type: ignore[assignment]

from src.config.settings import get_settings
from src.embeddings.base import BaseEmbedder
from src.embeddings.batch_tuner import BatchTuner
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Embedding using SentenceTransformers library.

    Supports local embedding generation with automatic device detection
    (CPU/CUDA/MPS).
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
        batch_size: int = 32,
    ):
        """Initialize SentenceTransformer embedder."""
        if SentenceTransformerType is None:
            raise ImportError("sentence-transformers required: pip install sentence-transformers torch")

        self._model_name = model_name
        self._batch_size = batch_size

        # Device detection
        if device is None:
            if torch_module and torch_module.cuda.is_available():
                device = "cuda"
            elif torch_module and hasattr(torch_module.backends, 'mps') and torch_module.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self._device = device

        # Load model
        logger.info(f"Loading SentenceTransformer model: {model_name} on {device}")
        self.model = SentenceTransformerType(model_name, device=device)

        # v0.2.9: Initialize batch tuner if enabled
        settings = get_settings()
        if settings.feature_flags.enable_batch_auto_tuning:
            self.batch_tuner: BatchTuner | None = BatchTuner(initial_size=batch_size)
            logger.info("Batch auto-tuning enabled")
        else:
            self.batch_tuner = None

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return cast(np.ndarray, self.model.encode([text], convert_to_numpy=True)[0])

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed multiple texts efficiently in batch.

        v0.2.9: Uses intelligent batch size tuning when enabled.
        """
        # v0.2.9: Use batch tuner if enabled
        if self.batch_tuner:
            batch_size = self.batch_tuner.suggest_batch_size(texts)
        else:
            batch_size = self._batch_size

        return self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        dim = self.model.get_sentence_embedding_dimension()
        return dim if dim is not None else 384  # Default fallback

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name
