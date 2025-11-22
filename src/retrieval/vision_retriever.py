"""Vision-aware retrieval engine for multi-modal queries.

This module provides the main retrieval interface for text, image, and hybrid
queries, integrating with the dual embedding storage layer.

v0.5.1: Initial vision-aware retrieval
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.retrieval.query_processor import MultiModalQueryProcessor, QueryEmbeddings, QueryType
from src.storage.dual_store import DualEmbeddingStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """
    Single retrieval result.

    Attributes:
        document_id: Parent document UUID
        embedding_id: Unique embedding identifier
        score: Relevance score (higher = more relevant)
        embedding_type: "text" or "vision"
        metadata: Full metadata dictionary
        rank: Position in results (1-indexed)
    """

    document_id: str
    embedding_id: str
    score: float
    embedding_type: str
    metadata: dict[str, Any]
    rank: int


@dataclass
class RetrievalResponse:
    """
    Complete retrieval response.

    Attributes:
        results: List of retrieval results (ranked)
        query_type: Type of query executed
        total_results: Total number of results
        execution_time_ms: Query execution time in milliseconds
    """

    results: list[RetrievalResult]
    query_type: QueryType
    total_results: int
    execution_time_ms: float


class VisionRetriever:
    """
    Multi-modal retrieval engine for text and vision queries.

    Supports:
    - Text-only queries (traditional semantic search)
    - Image-only queries (visual similarity search)
    - Hybrid text+image queries (multi-modal fusion)
    - Visual content boosting (diagrams, tables)

    Example:
        >>> retriever = VisionRetriever()
        >>> # Text query
        >>> response = retriever.query(text="database schema", n_results=10)
        >>> len(response.results)
        10
        >>> # Hybrid query
        >>> response = retriever.query(
        ...     text="architecture",
        ...     image="diagram.png",
        ...     text_weight=0.6,
        ...     vision_weight=0.4
        ... )
    """

    def __init__(
        self,
        store: DualEmbeddingStore | None = None,
        query_processor: MultiModalQueryProcessor | None = None,
        default_text_weight: float = 0.5,
        default_vision_weight: float = 0.5,
    ):
        """
        Initialise vision-aware retriever.

        Args:
            store: Dual embedding storage
            query_processor: Multi-modal query processor
            default_text_weight: Default weight for text scores (0-1)
            default_vision_weight: Default weight for vision scores (0-1)
        """
        self.store = store or DualEmbeddingStore()
        self.query_processor = query_processor or MultiModalQueryProcessor()

        self.default_text_weight = default_text_weight
        self.default_vision_weight = default_vision_weight

        logger.info(
            f"Initialised VisionRetriever "
            f"(text_weight={default_text_weight}, vision_weight={default_vision_weight})"
        )

    def query(
        self,
        text: str | None = None,
        image: Path | Image.Image | str | None = None,
        n_results: int = 10,
        text_weight: float | None = None,
        vision_weight: float | None = None,
        boost_diagrams: bool = False,
        boost_tables: bool = False,
        filter_metadata: dict[str, Any] | None = None,
    ) -> RetrievalResponse:
        """
        Execute multi-modal query.

        Args:
            text: Text query string
            image: Image query (path or PIL Image)
            n_results: Number of results to return
            text_weight: Weight for text scores (None = use default)
            vision_weight: Weight for vision scores (None = use default)
            boost_diagrams: Boost results containing diagrams
            boost_tables: Boost results containing tables
            filter_metadata: Additional metadata filters

        Returns:
            RetrievalResponse with ranked results

        Raises:
            ValueError: If both text and image are None

        Example:
            >>> retriever = VisionRetriever()
            >>> response = retriever.query(
            ...     text="database schema",
            ...     n_results=5,
            ...     boost_diagrams=True
            ... )
            >>> len(response.results) <= 5
            True
        """
        start_time = time.time()

        # Process query
        query_embeddings = self.query_processor.process_query(text=text, image=image)

        # Use default weights if not specified
        if text_weight is None:
            text_weight = self.default_text_weight
        if vision_weight is None:
            vision_weight = self.default_vision_weight

        logger.info(
            f"Executing {query_embeddings.query_type} query "
            f"(n={n_results}, text_w={text_weight}, vision_w={vision_weight})"
        )

        # Execute appropriate retrieval strategy
        if query_embeddings.query_type == QueryType.TEXT_ONLY:
            raw_results = self._query_text_only(query_embeddings, n_results, filter_metadata)

        elif query_embeddings.query_type == QueryType.IMAGE_ONLY:
            raw_results = self._query_image_only(query_embeddings, n_results, filter_metadata)

        else:  # HYBRID
            raw_results = self._query_hybrid(
                query_embeddings, n_results, text_weight, vision_weight, filter_metadata
            )

        # Apply visual content boosting if requested
        if boost_diagrams or boost_tables:
            raw_results = self._apply_visual_boost(raw_results, boost_diagrams, boost_tables)

        # Convert to RetrievalResult objects
        results = []
        for i, (embedding_id, score, metadata) in enumerate(raw_results):
            results.append(
                RetrievalResult(
                    document_id=metadata.get("document_id", "unknown"),
                    embedding_id=embedding_id,
                    score=score,
                    embedding_type=metadata.get("embedding_type", "unknown"),
                    metadata=metadata,
                    rank=i + 1,
                )
            )

        execution_time = (time.time() - start_time) * 1000  # ms

        logger.info(f"Retrieved {len(results)} results in {execution_time:.2f}ms")

        return RetrievalResponse(
            results=results,
            query_type=query_embeddings.query_type,
            total_results=len(results),
            execution_time_ms=execution_time,
        )

    def _query_text_only(
        self,
        query: QueryEmbeddings,
        n_results: int,
        filter_metadata: dict[str, Any] | None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Execute text-only query."""
        results = self.store.query_text(
            query_embedding=query.text_embedding, k=n_results, where_filter=filter_metadata
        )

        return self._format_raw_results(results)

    def _query_image_only(
        self,
        query: QueryEmbeddings,
        n_results: int,
        filter_metadata: dict[str, Any] | None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Execute image-only query."""
        results = self.store.query_vision(
            query_embedding=query.vision_embedding, k=n_results, where_filter=filter_metadata
        )

        return self._format_raw_results(results)

    def _query_hybrid(
        self,
        query: QueryEmbeddings,
        n_results: int,
        text_weight: float,
        vision_weight: float,
        filter_metadata: dict[str, Any] | None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Execute hybrid text+vision query."""
        results = self.store.query_hybrid(
            text_embedding=query.text_embedding,
            vision_embedding=query.vision_embedding,
            k=n_results,
            text_weight=text_weight,
            vision_weight=vision_weight,
            where_filter=filter_metadata,
        )

        return self._format_raw_results(results)

    def _format_raw_results(
        self, raw_results: dict[str, Any]
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """
        Convert ChromaDB results to (id, score, metadata) tuples.

        Args:
            raw_results: Raw results from DualEmbeddingStore

        Returns:
            List of (embedding_id, score, metadata) tuples
        """
        formatted = []

        ids = raw_results.get("ids", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]
        rrf_scores = raw_results.get("rrf_scores", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]

        # Use RRF scores if available (hybrid queries), otherwise convert distances to scores
        if rrf_scores:
            scores = rrf_scores
        elif distances:
            # Convert distances to scores (lower distance = higher score)
            max_distance = max(distances) if distances else 1.0
            if max_distance == 0:
                max_distance = 1.0
            scores = [1.0 - (d / max_distance) for d in distances]
        else:
            scores = [1.0] * len(ids)

        for i, embedding_id in enumerate(ids):
            score = scores[i] if i < len(scores) else 0.0
            metadata = metadatas[i] if i < len(metadatas) else {}

            formatted.append((embedding_id, score, metadata))

        return formatted

    def _apply_visual_boost(
        self,
        results: list[tuple[str, float, dict[str, Any]]],
        boost_diagrams: bool,
        boost_tables: bool,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """
        Boost scores for results with visual content.

        Args:
            results: Raw results (id, score, metadata)
            boost_diagrams: Boost results with diagrams
            boost_tables: Boost results with tables

        Returns:
            Re-ranked results with boosted scores
        """
        boosted = []
        diagram_boost = 1.2  # 20% score increase
        table_boost = 1.15  # 15% score increase

        for embedding_id, score, metadata in results:
            boosted_score = score

            if boost_diagrams and metadata.get("has_diagrams", False):
                boosted_score *= diagram_boost
                logger.debug(f"Boosted {embedding_id} for diagrams")

            if boost_tables and metadata.get("has_tables", False):
                boosted_score *= table_boost
                logger.debug(f"Boosted {embedding_id} for tables")

            boosted.append((embedding_id, boosted_score, metadata))

        # Re-sort by boosted scores
        boosted.sort(key=lambda x: x[1], reverse=True)

        return boosted

    def query_text(
        self,
        text: str,
        n_results: int = 10,
        boost_diagrams: bool = False,
        boost_tables: bool = False,
    ) -> RetrievalResponse:
        """
        Convenience method for text-only queries.

        Args:
            text: Query text
            n_results: Number of results
            boost_diagrams: Boost results with diagrams
            boost_tables: Boost results with tables

        Returns:
            Retrieval response
        """
        return self.query(
            text=text,
            n_results=n_results,
            boost_diagrams=boost_diagrams,
            boost_tables=boost_tables,
        )

    def query_image(
        self,
        image: Path | Image.Image | str,
        n_results: int = 10,
    ) -> RetrievalResponse:
        """
        Convenience method for image-only queries.

        Args:
            image: Query image (path or PIL Image)
            n_results: Number of results

        Returns:
            Retrieval response
        """
        return self.query(image=image, n_results=n_results)

    def query_hybrid(
        self,
        text: str,
        image: Path | Image.Image | str,
        n_results: int = 10,
        text_weight: float = 0.5,
        vision_weight: float = 0.5,
    ) -> RetrievalResponse:
        """
        Convenience method for hybrid queries.

        Args:
            text: Query text
            image: Query image (path or PIL Image)
            n_results: Number of results
            text_weight: Weight for text scores
            vision_weight: Weight for vision scores

        Returns:
            Retrieval response
        """
        return self.query(
            text=text,
            image=image,
            n_results=n_results,
            text_weight=text_weight,
            vision_weight=vision_weight,
        )
