"""Multi-modal query processing for text and vision queries.

This module processes queries that can include text, images, or both (hybrid)
and generates appropriate embeddings for retrieval.

v0.5.1: Initial multi-modal query processing
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Query type enumeration for multi-modal retrieval."""

    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"
    HYBRID = "hybrid"


@dataclass
class QueryEmbeddings:
    """
    Container for query embeddings.

    Attributes:
        query_type: Type of query (text_only, image_only, hybrid)
        text_embedding: 384-dim text embedding (None for image-only)
        vision_embedding: 128-dim vision embedding (None for text-only)
        text_query: Original text query string
        image_path: Path to query image file
    """

    query_type: QueryType
    text_embedding: np.ndarray | None = None
    vision_embedding: np.ndarray | None = None
    text_query: str | None = None
    image_path: Path | None = None

    def __post_init__(self):
        """Validate embedding presence based on query type."""
        if self.query_type == QueryType.TEXT_ONLY:
            if self.text_embedding is None:
                raise ValueError("Text-only query requires text embedding")

        elif self.query_type == QueryType.IMAGE_ONLY:
            if self.vision_embedding is None:
                raise ValueError("Image-only query requires vision embedding")

        elif self.query_type == QueryType.HYBRID:
            if self.text_embedding is None or self.vision_embedding is None:
                raise ValueError("Hybrid query requires both text and vision embeddings")


class MultiModalQueryProcessor:
    """
    Process multi-modal queries (text, image, or both).

    Handles:
    - Text query embedding generation
    - Image query embedding generation
    - Hybrid query processing
    - Query type detection

    Example:
        >>> processor = MultiModalQueryProcessor()
        >>> # Text query
        >>> result = processor.process_query(text="database schema")
        >>> result.query_type
        'text_only'
        >>> # Hybrid query
        >>> result = processor.process_query(text="architecture", image="diagram.png")
        >>> result.query_type
        'hybrid'
    """

    def __init__(
        self,
        text_embedder: Any | None = None,
        vision_embedder: Any | None = None,
    ):
        """
        Initialise multi-modal query processor.

        Args:
            text_embedder: Text embedding model (TextEmbedder or similar)
            vision_embedder: Vision embedding model (ColPaliEmbedder)
        """
        if text_embedder is None:
            from src.embeddings.factory import get_embedder

            self.text_embedder = get_embedder()
        else:
            self.text_embedder = text_embedder

        self.vision_embedder = vision_embedder

        logger.info(
            f"Initialised MultiModalQueryProcessor "
            f"(vision_enabled={vision_embedder is not None})"
        )

    def process_query(
        self,
        text: str | None = None,
        image: Path | Image.Image | str | None = None,
    ) -> QueryEmbeddings:
        """
        Process query and generate embeddings.

        Args:
            text: Text query string
            image: Image query (file path or PIL Image)

        Returns:
            QueryEmbeddings container with generated embeddings

        Raises:
            ValueError: If both text and image are None
            RuntimeError: If image query requested but vision embedder not available

        Example:
            >>> processor = MultiModalQueryProcessor()
            >>> result = processor.process_query(text="schema")
            >>> result.text_embedding.shape
            (384,)
        """
        if text is None and image is None:
            raise ValueError("At least one of text or image must be provided")

        # Determine query type
        if text and image:
            query_type = QueryType.HYBRID
        elif text:
            query_type = QueryType.TEXT_ONLY
        else:
            query_type = QueryType.IMAGE_ONLY

        logger.debug(f"Processing {query_type} query")

        # Generate text embedding if needed
        text_embedding = None
        if text:
            text_embedding = self.text_embedder.embed(text)
            logger.debug(f"Generated text embedding: {text_embedding.shape}")

        # Generate vision embedding if needed
        vision_embedding = None
        image_path = None

        if image:
            if self.vision_embedder is None:
                raise RuntimeError(
                    "Image query requested but vision embedder not initialised. "
                    "Ensure ColPali is configured with --vision flag."
                )

            # Convert to PIL Image if path provided
            if isinstance(image, (str, Path)):
                # SECURITY FIX (CRITICAL-2): Validate file path to prevent path traversal
                from src.utils.security import validate_file_path, validate_mime_type

                image_path = Path(image)

                # Validate path is safe and within allowed directory
                validated_path = validate_file_path(image_path, allowed_base=None)

                # Validate MIME type to ensure it's actually an image
                mime_type = validate_mime_type(
                    validated_path,
                    expected_types=["image/png", "image/jpeg", "application/pdf"],
                )
                logger.debug(f"Validated image file: {validated_path} (type: {mime_type})")

                image = Image.open(validated_path)

            # Generate vision embedding for single image
            vision_embedding = self.vision_embedder.embed_page(image)
            logger.debug(f"Generated vision embedding: {vision_embedding.shape}")

        return QueryEmbeddings(
            query_type=query_type,
            text_embedding=text_embedding,
            vision_embedding=vision_embedding,
            text_query=text,
            image_path=image_path,
        )

    def process_text(self, text: str) -> QueryEmbeddings:
        """
        Process text-only query.

        Args:
            text: Query text

        Returns:
            QueryEmbeddings with text embedding

        Example:
            >>> processor = MultiModalQueryProcessor()
            >>> result = processor.process_text("database")
            >>> result.query_type
            'text_only'
        """
        return self.process_query(text=text, image=None)

    def process_image(self, image: Path | Image.Image | str) -> QueryEmbeddings:
        """
        Process image-only query.

        Args:
            image: Query image (path or PIL Image)

        Returns:
            QueryEmbeddings with vision embedding

        Raises:
            RuntimeError: If vision embedder not available

        Example:
            >>> processor = MultiModalQueryProcessor(vision_embedder=embedder)
            >>> result = processor.process_image("diagram.png")
            >>> result.query_type
            'image_only'
        """
        return self.process_query(text=None, image=image)

    def process_hybrid(self, text: str, image: Path | Image.Image | str) -> QueryEmbeddings:
        """
        Process hybrid text+image query.

        Args:
            text: Query text
            image: Query image (path or PIL Image)

        Returns:
            QueryEmbeddings with both embeddings

        Example:
            >>> processor = MultiModalQueryProcessor(vision_embedder=embedder)
            >>> result = processor.process_hybrid("architecture", "diagram.png")
            >>> result.query_type
            'hybrid'
        """
        return self.process_query(text=text, image=image)
