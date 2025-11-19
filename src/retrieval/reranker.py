"""
Cross-encoder reranking for improved retrieval precision.

Uses cross-encoder models to rerank retrieved chunks for better top-k accuracy.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Type hint for RetrievedChunk (avoid circular import)
try:
    from src.retrieval.retriever import RetrievedChunk
except ImportError:
    RetrievedChunk = any  # type: ignore


@dataclass
class RerankResult:
    """Result of reranking operation."""

    original_count: int
    reranked_count: int
    rerank_model: str
    score_improvement: float  # Average score improvement


class Reranker:
    """
    Reranks retrieved chunks using cross-encoder models.

    Cross-encoders jointly encode query and document, providing better
    relevance scores than bi-encoder similarity.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size: int = 32,
    ):
        """
        Initialise reranker.

        Args:
            model_name: Cross-encoder model name from sentence-transformers
            batch_size: Batch size for processing chunks
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None  # Lazy load
        self._load_lock = False

        logger.info(f"Reranker initialised with model={model_name}")

    def _load_model(self):
        """Lazy load the cross-encoder model."""
        if self._model is not None:
            return

        if self._load_lock:
            logger.warning("Model loading already in progress")
            return

        self._load_lock = True

        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
            logger.info("Cross-encoder model loaded successfully")

        except ImportError:
            logger.error(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}", exc_info=True)
            raise
        finally:
            self._load_lock = False

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: Optional[int] = None,
    ) -> Tuple[List[RetrievedChunk], RerankResult]:
        """
        Rerank retrieved chunks using cross-encoder.

        Args:
            query: Original query
            chunks: List of retrieved chunks to rerank
            top_k: Number of top chunks to return (None = return all reranked)

        Returns:
            Tuple of (reranked_chunks, rerank_result)

        Example:
            >>> reranker = Reranker()
            >>> reranked, result = reranker.rerank("What is ML?", chunks, top_k=5)
            >>> print(f"Reranked {result.original_count} → {result.reranked_count}")
        """
        if not chunks:
            logger.warning("No chunks to rerank")
            return [], RerankResult(
                original_count=0,
                reranked_count=0,
                rerank_model=self.model_name,
                score_improvement=0.0,
            )

        # Ensure model is loaded
        self._load_model()

        if self._model is None:
            logger.error("Cross-encoder model not available, returning original order")
            return chunks[:top_k] if top_k else chunks, RerankResult(
                original_count=len(chunks),
                reranked_count=top_k or len(chunks),
                rerank_model=self.model_name,
                score_improvement=0.0,
            )

        original_count = len(chunks)

        # Prepare query-document pairs
        pairs = [[query, chunk.text] for chunk in chunks]

        # Score with cross-encoder (in batches for efficiency)
        try:
            scores = []
            for i in range(0, len(pairs), self.batch_size):
                batch = pairs[i:i + self.batch_size]
                batch_scores = self._model.predict(batch)
                scores.extend(batch_scores)

            scores = np.array(scores)

            # Calculate score improvement
            original_scores = np.array([chunk.score for chunk in chunks])
            score_improvement = float(np.mean(scores - original_scores))

            # Sort by scores (descending)
            sorted_indices = np.argsort(scores)[::-1]

            # Update chunk scores and reorder
            reranked_chunks = []
            for idx in sorted_indices:
                chunk = chunks[idx]
                # Update score with cross-encoder score
                chunk.score = float(scores[idx])
                reranked_chunks.append(chunk)

            # Take top-k if specified
            if top_k is not None:
                reranked_chunks = reranked_chunks[:top_k]

            result = RerankResult(
                original_count=original_count,
                reranked_count=len(reranked_chunks),
                rerank_model=self.model_name,
                score_improvement=score_improvement,
            )

            logger.info(
                f"Reranked {original_count} → {len(reranked_chunks)} chunks, "
                f"score improvement: {score_improvement:.3f}"
            )

            return reranked_chunks, result

        except Exception as e:
            logger.error(f"Reranking failed: {e}", exc_info=True)
            # Fallback to original order
            return chunks[:top_k] if top_k else chunks, RerankResult(
                original_count=original_count,
                reranked_count=top_k or original_count,
                rerank_model=self.model_name,
                score_improvement=0.0,
            )

    def rerank_with_scores(
        self,
        query: str,
        texts: List[str],
        top_k: Optional[int] = None,
    ) -> List[Tuple[str, float]]:
        """
        Rerank texts and return with scores.

        Simpler interface when you don't have RetrievedChunk objects.

        Args:
            query: Query string
            texts: List of text strings to rerank
            top_k: Number of top results to return

        Returns:
            List of (text, score) tuples, sorted by relevance

        Example:
            >>> reranker = Reranker()
            >>> results = reranker.rerank_with_scores("What is ML?", texts, top_k=3)
            >>> for text, score in results:
            ...     print(f"{score:.3f}: {text[:50]}")
        """
        if not texts:
            return []

        # Ensure model is loaded
        self._load_model()

        if self._model is None:
            logger.error("Cross-encoder model not available")
            return [(text, 0.0) for text in texts[:top_k]] if top_k else [(text, 0.0) for text in texts]

        # Prepare pairs
        pairs = [[query, text] for text in texts]

        # Score
        try:
            scores = []
            for i in range(0, len(pairs), self.batch_size):
                batch = pairs[i:i + self.batch_size]
                batch_scores = self._model.predict(batch)
                scores.extend(batch_scores)

            scores = np.array(scores)

            # Sort by scores
            sorted_indices = np.argsort(scores)[::-1]

            # Return top-k
            results = [(texts[idx], float(scores[idx])) for idx in sorted_indices]

            if top_k is not None:
                results = results[:top_k]

            return results

        except Exception as e:
            logger.error(f"Reranking failed: {e}", exc_info=True)
            return [(text, 0.0) for text in texts[:top_k]] if top_k else [(text, 0.0) for text in texts]
