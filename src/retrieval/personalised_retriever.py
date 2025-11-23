"""Personalised retrieval using interest profiles (v0.4.8).

Wraps standard retriever with personalised re-ranking based on user
interest profiles.
"""

from typing import Any, List, Optional

from ragged.memory.personalisation import PersonalisationConfig, PersonalisedRanker
from ragged.memory.profile import ProfileManager
from ragged.memory.topics import TopicExtractor
from ragged.retrieval.retriever import RetrievedChunk, Retriever
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class PersonalisedRetriever:
    """Retriever with personalised ranking.

    Enhances standard retrieval with user interest profile-based re-ranking.
    Retrieves k*multiplier candidates, then re-ranks using PersonalisedRanker
    to return top-k personalised results.

    Example:
        >>> from ragged.memory import ProfileManager, TopicExtractor
        >>> profile_manager = ProfileManager()
        >>> extractor = TopicExtractor()
        >>> retriever = PersonalisedRetriever(
        ...     profile_manager=profile_manager,
        ...     topic_extractor=extractor,
        ... )
        >>> results = retriever.retrieve(
        ...     query="What is RAG?",
        ...     k=10,
        ...     persona="researcher",
        ...     personalise=True,
        ... )
    """

    def __init__(
        self,
        profile_manager: ProfileManager,
        topic_extractor: TopicExtractor,
        base_retriever: Optional[Retriever] = None,
        config: Optional[PersonalisationConfig] = None,
    ):
        """Initialise personalised retriever.

        Args:
            profile_manager: Manager for interest profiles
            topic_extractor: Topic extraction engine
            base_retriever: Base retriever (creates default if None)
            config: Personalisation configuration
        """
        self.base_retriever = base_retriever or Retriever()
        self.ranker = PersonalisedRanker(
            profile_manager=profile_manager,
            topic_extractor=topic_extractor,
            config=config,
        )
        self.config = config or PersonalisationConfig()

        logger.info(
            f"PersonalisedRetriever initialised "
            f"(multiplier={self.config.retrieve_multiplier})"
        )

    def retrieve(
        self,
        query: str,
        k: int = 5,
        persona: str = "default",
        personalise: bool = True,
        filter_metadata: Optional[dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """Retrieve with optional personalisation.

        Workflow:
        1. Retrieve k*multiplier candidates using base retriever
        2. If personalisation enabled, re-rank using interest profile
        3. Return top-k results

        Args:
            query: User query
            k: Number of results to return
            persona: Current persona for profile lookup
            personalise: Enable personalised ranking
            filter_metadata: Optional metadata filter for base retrieval
            min_score: Optional minimum similarity score threshold

        Returns:
            Top-k results (personalised if enabled, otherwise standard)

        Example:
            >>> # Standard retrieval (no personalisation)
            >>> results = retriever.retrieve("machine learning", k=10, personalise=False)
            >>>
            >>> # Personalised retrieval
            >>> results = retriever.retrieve(
            ...     "machine learning",
            ...     k=10,
            ...     persona="researcher",
            ...     personalise=True,
            ... )
        """
        # Determine number of candidates to retrieve
        if personalise and self.config.enabled:
            retrieve_k = k * self.config.retrieve_multiplier
            logger.debug(
                f"Retrieving {retrieve_k} candidates for personalised reranking to {k}"
            )
        else:
            retrieve_k = k
            logger.debug(f"Retrieving {k} results (personalisation disabled)")

        # Retrieve candidates using base retriever
        candidates = self.base_retriever.retrieve(
            query=query,
            k=retrieve_k,
            filter_metadata=filter_metadata,
            min_score=min_score,
        )

        if not candidates:
            logger.warning("No candidates retrieved")
            return []

        # Apply personalised ranking if enabled
        if personalise and self.config.enabled:
            try:
                results = self.ranker.rerank(
                    results=candidates,
                    query=query,
                    persona=persona,
                    k=k,
                )
                logger.info(
                    f"Personalised ranking applied: {len(candidates)} -> {len(results)}"
                )
                return results
            except Exception as e:
                logger.error(
                    f"Personalised ranking failed: {e}. Falling back to base results."
                )
                return candidates[:k]
        else:
            # Return top-k base results
            return candidates[:k]

    def record_interaction(
        self,
        query: str,
        retrieved_docs: List[RetrievedChunk],
        persona: str = "default",
    ):
        """Record interaction for historical access boosting.

        Tracks which documents were retrieved for this query, enabling
        historical access boosting in future retrievals.

        Args:
            query: User query
            retrieved_docs: Documents that were retrieved
            persona: Current persona
        """
        # Record document access for historical boosting
        for doc in retrieved_docs:
            self.ranker.record_access(doc.document_id)

        logger.debug(
            f"Recorded access for {len(retrieved_docs)} documents (persona: {persona})"
        )

    def get_config(self) -> PersonalisationConfig:
        """Get current personalisation configuration.

        Returns:
            Current PersonalisationConfig
        """
        return self.config

    def update_config(self, **kwargs):
        """Update personalisation configuration.

        Args:
            **kwargs: Configuration parameters to update (e.g., alpha=0.5)

        Raises:
            ValueError: If invalid configuration parameter

        Example:
            >>> retriever.update_config(alpha=0.5, retrieve_multiplier=3)
        """
        # Update config attributes
        for key, value in kwargs.items():
            if not hasattr(self.config, key):
                raise ValueError(f"Invalid configuration parameter: {key}")
            setattr(self.config, key, value)

        # Validate updated config
        self.config.__post_init__()

        logger.info(f"Configuration updated: {kwargs}")

    def enable_personalisation(self):
        """Enable personalised ranking."""
        self.config.enabled = True
        logger.info("Personalised ranking enabled")

    def disable_personalisation(self):
        """Disable personalised ranking."""
        self.config.enabled = False
        logger.info("Personalised ranking disabled")


def create_personalised_retriever(
    persona_db_path: Optional[str] = None,
    base_retriever: Optional[Retriever] = None,
    config: Optional[PersonalisationConfig] = None,
) -> PersonalisedRetriever:
    """Factory function to create PersonalisedRetriever with default dependencies.

    Args:
        persona_db_path: Path to persona database (defaults to ~/.ragged/memory/)
        base_retriever: Base retriever (creates default if None)
        config: Personalisation configuration

    Returns:
        Configured PersonalisedRetriever instance

    Example:
        >>> retriever = create_personalised_retriever()
        >>> results = retriever.retrieve("machine learning", k=10, persona="researcher")
    """
    from pathlib import Path

    # Create profile manager
    if persona_db_path is None:
        persona_db_path = str(Path.home() / ".ragged" / "memory" / "profiles.db")

    profile_manager = ProfileManager(db_path=persona_db_path)

    # Create topic extractor
    topic_extractor = TopicExtractor()

    # Create personalised retriever
    return PersonalisedRetriever(
        profile_manager=profile_manager,
        topic_extractor=topic_extractor,
        base_retriever=base_retriever,
        config=config,
    )
