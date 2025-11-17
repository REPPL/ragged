"""Few-shot example storage and retrieval for improved prompting.

Stores high-quality Q&A examples and retrieves relevant ones for few-shot learning.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import logging
import numpy as np

from src.config.constants import FALLBACK_EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


@dataclass
class FewShotExample:
    """A few-shot Q&A example."""

    query: str
    context: str  # Retrieved context that was used
    answer: str  # High-quality answer
    category: Optional[str] = None  # Category for organization
    tags: Optional[List[str]] = None  # Tags for filtering

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FewShotExample":
        """Create from dictionary."""
        return cls(**data)

    def to_prompt_format(self) -> str:
        """Format as few-shot prompt example.

        Returns:
            Formatted example for prompting
        """
        return f"""Example:
Query: {self.query}

Context:
{self.context}

Answer: {self.answer}
"""


class FewShotExampleStore:
    """Store and retrieve few-shot examples."""

    def __init__(self, storage_path: Optional[Path] = None, embedder: Any = None):
        """Initialize example store.

        Args:
            storage_path: Path to JSON file for persistence
            embedder: Optional embedder for semantic similarity search
        """
        self.storage_path = storage_path or Path("data/few_shot_examples.json")
        self.embedder = embedder
        self.examples: List[FewShotExample] = []
        self.example_embeddings: List[np.ndarray] = []  # Query embeddings for examples
        self._load_examples()

    def _load_examples(self) -> None:
        """Load examples from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
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
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
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
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
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

    def get_all_examples(self) -> List[FewShotExample]:
        """Get all examples.

        Returns:
            List of all examples
        """
        return self.examples

    def get_by_category(self, category: str) -> List[FewShotExample]:
        """Get examples by category.

        Args:
            category: Category name

        Returns:
            List of examples in category
        """
        return [ex for ex in self.examples if ex.category == category]

    def get_by_tags(self, tags: List[str]) -> List[FewShotExample]:
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
        category: Optional[str] = None
    ) -> List[FewShotExample]:
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
        candidates: List[FewShotExample],
        top_k: int,
        category: Optional[str] = None
    ) -> List[FewShotExample]:
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
        candidates: List[FewShotExample],
        top_k: int
    ) -> List[FewShotExample]:
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


def seed_default_examples(store: FewShotExampleStore) -> None:
    """Seed the store with default examples.

    Args:
        store: Example store to seed
    """
    # Example 1: Factual retrieval
    store.add_example(
        query="What is machine learning?",
        context="[Source 1: ml_intro.pdf]\nMachine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.",
        answer="Machine learning is a subset of artificial intelligence that allows systems to automatically learn and improve from experience without explicit programming. It involves developing algorithms that can access data and learn patterns from it to make predictions or decisions.",
        category="definition",
        tags=["AI", "machine learning", "basics"]
    )

    # Example 2: Comparative question
    store.add_example(
        query="What's the difference between supervised and unsupervised learning?",
        context="[Source 1: ml_types.pdf]\nSupervised learning uses labeled data where the correct output is known. The algorithm learns to map inputs to outputs. Common examples include classification and regression.\n\n[Source 2: ml_types.pdf]\nUnsupervised learning works with unlabeled data. The algorithm must find patterns and structure in the data without guidance. Clustering is a common unsupervised learning task.",
        answer="The key difference is in the training data:\n\nSupervised learning uses labeled data where correct answers are provided. The algorithm learns to predict outputs from inputs (e.g., classification, regression).\n\nUnsupervised learning works with unlabeled data. The algorithm must discover patterns and structure independently (e.g., clustering, dimensionality reduction).",
        category="comparison",
        tags=["machine learning", "supervised", "unsupervised"]
    )

    # Example 3: Process/How-to
    store.add_example(
        query="How does gradient descent work?",
        context="[Source 1: optimization.pdf]\nGradient descent is an optimization algorithm used to minimize a cost function. It works by iteratively moving in the direction of steepest descent, which is the negative gradient. The learning rate determines the step size of each iteration.",
        answer="Gradient descent minimizes a cost function through iterative steps:\n\n1. Calculate the gradient (slope) of the cost function\n2. Move in the opposite direction (negative gradient)\n3. The learning rate controls step size\n4. Repeat until convergence\n\nThis finds the minimum by following the steepest downward slope at each step.",
        category="process",
        tags=["optimization", "gradient descent", "algorithms"]
    )

    # Example 4: Technical concept
    store.add_example(
        query="What is overfitting in machine learning?",
        context="[Source 1: model_evaluation.pdf]\nOverfitting occurs when a model learns the training data too well, including noise and outliers. The model performs well on training data but poorly on new, unseen data. It essentially memorizes rather than generalizes.",
        answer="Overfitting happens when a model learns training data too well, including noise and random fluctuations. While it achieves high accuracy on training data, it fails to generalize to new data.\n\nThis is like memorizing answers instead of understanding concepts - the model performs poorly on unseen examples.",
        category="concept",
        tags=["machine learning", "overfitting", "model evaluation"]
    )

    # Example 5: When to use
    store.add_example(
        query="When should I use a decision tree vs neural network?",
        context="[Source 1: model_selection.pdf]\nDecision trees are interpretable, work well with structured data, and require less data. Neural networks excel with large datasets, unstructured data like images and text, but are less interpretable and require more computational resources.",
        answer="Choose based on your requirements:\n\nDecision Trees when you need:\n- Interpretability and explainability\n- Smaller structured datasets\n- Fast training\n- Simple deployment\n\nNeural Networks when you have:\n- Large amounts of data\n- Unstructured data (images, text, audio)\n- Complex patterns to learn\n- Computational resources available",
        category="selection",
        tags=["models", "decision trees", "neural networks"]
    )

    logger.info("Seeded 5 default few-shot examples")


def format_few_shot_prompt(
    query: str,
    context: str,
    examples: List[FewShotExample],
    max_examples: int = 3
) -> str:
    """Format a prompt with few-shot examples.

    Args:
        query: Current query
        context: Retrieved context for current query
        examples: Few-shot examples to include
        max_examples: Maximum number of examples to include

    Returns:
        Formatted prompt with examples
    """
    if not examples:
        # No examples - return basic prompt
        return f"""Context:
{context}

Question: {query}

Answer:"""

    # Include examples
    example_text = "\n\n".join(
        ex.to_prompt_format() for ex in examples[:max_examples]
    )

    prompt = f"""You are a helpful AI assistant. Answer questions based on the provided context.

Here are some examples of good answers:

{example_text}

Now answer this question:

Context:
{context}

Question: {query}

Answer:"""

    return prompt
