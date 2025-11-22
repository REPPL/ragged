"""
Abstract base class for embedding models.

This module defines the interface that all embedding implementations must follow,
enabling swappable backends (SentenceTransformers, Ollama, etc.).
"""

from abc import ABC, abstractmethod
from typing import cast

import numpy as np


class BaseEmbedder(ABC):
    """
    Abstract base class for text embedding models.

    All embedding implementations must inherit from this class and implement
    the required methods.
    """

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Numpy array of shape (dimensions,) containing the embedding

        TODO: Implement in subclasses
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Embed multiple text strings efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            Numpy array of shape (len(texts), dimensions) containing embeddings

        TODO: Implement batch processing for efficiency
              Should be faster than calling embed_text multiple times
        """
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """
        Get the dimensionality of embeddings produced by this model.

        Returns:
            Number of dimensions in output embeddings

        TODO: Return model-specific dimensions
              - SentenceTransformers all-MiniLM-L6-v2: 384
              - Ollama nomic-embed-text: 768
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the name of the embedding model.

        Returns:
            Model name string

        TODO: Return model identifier
        """
        pass

    def normalize(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize an embedding to unit length.

        Args:
            embedding: Embedding vector to normalize

        Returns:
            Normalized embedding vector

        TODO: Implement L2 normalization:
              embedding / np.linalg.norm(embedding)
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return cast(np.ndarray, embedding / norm)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score between -1 and 1
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
