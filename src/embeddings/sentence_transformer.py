"""
SentenceTransformer-based embedding implementation.

Uses the sentence-transformers library to generate embeddings locally
on CPU or GPU.
"""

from typing import List

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError:
    SentenceTransformer = None
    torch = None

from src.embeddings.base import BaseEmbedder
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
        device: str = None,
        batch_size: int = 32,
    ):
        """Initialize SentenceTransformer embedder."""
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers required: pip install sentence-transformers torch")

        self._model_name = model_name
        self._batch_size = batch_size

        # Device detection
        if device is None:
            if torch and torch.cuda.is_available():
                device = "cuda"
            elif torch and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self._device = device

        # Load model
        logger.info(f"Loading SentenceTransformer model: {model_name} on {device}")
        self.model = SentenceTransformer(model_name, device=device)

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return self.model.encode([text], convert_to_numpy=True)[0]

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts efficiently in batch."""
        return self.model.encode(
            texts,
            batch_size=self._batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name
