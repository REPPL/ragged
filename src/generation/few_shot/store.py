"""Few-shot example storage and retrieval."""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from src.config.constants import FALLBACK_EMBEDDING_DIMENSION
from src.generation.few_shot.models import FewShotExample
from src.utils.path_utils import ensure_directory

logger = logging.getLogger(__name__)


class FewShotExampleStore:
    """Store and retrieve few-shot examples."""

    def __init__(self, storage_path: Path | None = None, embedder: Any = None):
        """Initialise example store.

        Args:
            storage_path: Path to JSON file for persistence
            embedder: Optional embedder for semantic similarity search
        """
        self.storage_path = storage_path or Path("data/few_shot_examples.json")
        self.embedder = embedder
        self.examples: list[FewShotExample] = []
        self.example_embeddings: list[np.ndarray] = []  # Query embeddings for examples
        self._load_examples()

    def _load_examples(self) -> None:
        """Load examples from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.examples = [
                        FewShotExample.from_dict(ex) for ex in data
                    ]
                logger.info(f"Loaded {len(self.examples)} few-shot examples")

                # Compute embeddings for loaded examples if embedder available
                if self.embedder:
                    self._compute_example_embeddings()
            except Exception:  # noqa: BLE001 - Graceful degradation on startup
                logger.exception("Failed to load examples")
                self.examples = []
                self.example_embeddings = []
        else:
            logger.info("No existing examples found")
            self.examples = []
            self.example_embeddings = []

    def _compute_example_embeddings(self) -> None:
        """Compute embeddings for all examples."""
        if not self.embedder:
            return

        self.example_embeddings = []
        for example in self.examples:
            try:
                embedding = self.embedder.embed_text(example.query)
                self.example_embeddings.append(np.array(embedding))
            except Exception:  # noqa: BLE001 - Continue processing other examples
                logger.warning("Failed to embed example query", exc_info=True)
                # Use zero vector as fallback
                self.example_embeddings.append(np.zeros(FALLBACK_EMBEDDING_DIMENSION))

        logger.debug(f"Computed embeddings for {len(self.example_embeddings)} examples")

    def save_examples(self) -> None:
        """Save examples to storage."""
        try:
            ensure_directory(self.storage_path.parent)
            with open(self.storage_path, 'w') as f:
                data = [ex.to_dict() for ex in self.examples]
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.examples)} examples to {self.storage_path}")
        except Exception:  # noqa: BLE001 - Non-critical operation, graceful degradation
            logger.exception("Failed to save examples")

    def add_example(
        self,
        query: str,
        context: str,
        answer: str,
        category: str | None = None,
        tags: list[str] | None = None
    ) -> FewShotExample:
        """Add a new example.

        Args:
            query: Question/query
            context: Retrieved context
            answer: High-quality answer
            category: Optional category
            tags: Optional tags

        Returns:
            Created example
        """
        example = FewShotExample(
            query=query,
            context=context,
            answer=answer,
            category=category,
            tags=tags or []
        )

        self.examples.append(example)

        # Compute embedding for new example if embedder available
        if self.embedder:
            try:
                embedding = self.embedder.embed_text(query)
                self.example_embeddings.append(np.array(embedding))
            except Exception:  # noqa: BLE001 - Fallback to zero vector on failure
                logger.warning("Failed to embed new example", exc_info=True)
                self.example_embeddings.append(np.zeros(FALLBACK_EMBEDDING_DIMENSION))

        self.save_examples()

        logger.info(f"Added new example (total: {len(self.examples)})")
        return example

    def get_all_examples(self) -> list[FewShotExample]:
        """Get all examples.

        Returns:
            List of all examples
        """
        return self.examples

    def get_by_category(self, category: str) -> list[FewShotExample]:
        """Get examples by category.

        Args:
            category: Category name

        Returns:
            List of examples in category
        """
        return [ex for ex in self.examples if ex.category == category]

    def get_by_tags(self, tags: list[str]) -> list[FewShotExample]:
        """Get examples matching any of the given tags.

        Args:
            tags: List of tags to match

        Returns:
            List of matching examples
        """
        return [
            ex for ex in self.examples
            if ex.tags and any(tag in ex.tags for tag in tags)
        ]

    def search_similar(
        self,
        query: str,
        top_k: int = 3,
        category: str | None = None
    ) -> list[FewShotExample]:
        """Search for similar examples using semantic similarity.

        Uses embedding-based cosine similarity if embedder available,
        otherwise falls back to keyword matching.

        Args:
            query: Query to match
            top_k: Number of examples to return
            category: Optional category filter

        Returns:
            List of similar examples
        """
        # Filter by category if specified
        candidates = (
            self.get_by_category(category)
            if category
            else self.examples
        )

        if not candidates:
            return []

        # Use embedding-based search if embedder available
        if self.embedder and self.example_embeddings:
            return self._search_by_embedding(query, candidates, top_k, category)
        else:
            # Fallback to keyword search
            return self._search_by_keywords(query, candidates, top_k)

    def _search_by_embedding(
        self,
        query: str,
        candidates: list[FewShotExample],
        top_k: int,
        category: str | None = None
    ) -> list[FewShotExample]:
        """Search using embedding-based cosine similarity.

        Args:
            query: Query text
            candidates: Candidate examples to search
            top_k: Number to return
            category: Optional category filter

        Returns:
            Top-k most similar examples
        """
        try:
            # Embed query
            query_embedding = np.array(self.embedder.embed_text(query))

            # Get indices of candidates in full examples list
            if category:
                candidate_indices = [
                    i for i, ex in enumerate(self.examples)
                    if ex.category == category
                ]
            else:
                candidate_indices = list(range(len(self.examples)))

            # Compute cosine similarities
            scored = []
            for idx in candidate_indices:
                if idx < len(self.example_embeddings):
                    example_emb = self.example_embeddings[idx]
                    # Cosine similarity
                    similarity = np.dot(query_embedding, example_emb) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(example_emb) + 1e-10
                    )
                    scored.append((similarity, self.examples[idx]))

            # Sort by similarity descending
            scored.sort(key=lambda x: x[0], reverse=True)

            # Return top-k
            return [ex for _, ex in scored[:top_k]]

        except Exception:  # noqa: BLE001 - Fallback to keyword search on any error
            logger.warning("Embedding-based search failed, falling back to keywords", exc_info=True)
            return self._search_by_keywords(query, candidates, top_k)

    def _search_by_keywords(
        self,
        query: str,
        candidates: list[FewShotExample],
        top_k: int
    ) -> list[FewShotExample]:
        """Search using keyword matching (fallback).

        Args:
            query: Query text
            candidates: Candidate examples
            top_k: Number to return

        Returns:
            Top-k examples by keyword overlap
        """
        # Simple keyword matching
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score each example by word overlap
        scored = []
        for example in candidates:
            example_words = set(example.query.lower().split())
            overlap = len(query_words & example_words)
            scored.append((overlap, example))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top-k
        return [ex for _, ex in scored[:top_k]]

    def clear(self) -> None:
        """Clear all examples."""
        self.examples = []
        self.example_embeddings = []
        self.save_examples()
        logger.info("Cleared all examples")
