"""Personalised ranking for retrieval results (v0.4.8).

Re-ranks retrieval results using user interest profiles to improve relevance
based on learned behaviour patterns.

Privacy: All personalisation happens locally, no external API calls.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from ragged.memory.profile import ProfileManager, InterestProfile
from ragged.memory.topics import TopicExtractor
from ragged.retrieval.retriever import RetrievedChunk
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PersonalisationConfig:
    """Configuration for personalised ranking.

    Attributes:
        enabled: Enable personalised ranking
        alpha: Personalisation weight (0.0-1.0, 0=no personalisation, 1=full)
        retrieve_multiplier: Retrieve k*multiplier candidates for reranking
        min_confidence_threshold: Minimum confidence for topic boosting
        topic_relevance_weight: Weight for topic relevance boost (0.0-1.0)
        historical_access_weight: Weight for historical access boost (0.0-1.0)
        co_occurrence_weight: Weight for co-occurrence boost (0.0-1.0)
        time_decay_rate: Decay rate per day for historical access (0.0-1.0)
    """
    enabled: bool = True
    alpha: float = 0.3
    retrieve_multiplier: int = 2
    min_confidence_threshold: float = 0.3
    topic_relevance_weight: float = 0.5
    historical_access_weight: float = 0.3
    co_occurrence_weight: float = 0.2
    time_decay_rate: float = 0.05

    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError(f"alpha must be 0.0-1.0, got {self.alpha}")
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            raise ValueError(
                f"min_confidence_threshold must be 0.0-1.0, got {self.min_confidence_threshold}"
            )
        weights_sum = (
            self.topic_relevance_weight +
            self.historical_access_weight +
            self.co_occurrence_weight
        )
        if not 0.99 <= weights_sum <= 1.01:  # Allow small floating point error
            raise ValueError(
                f"Boost weights must sum to 1.0, got {weights_sum:.3f}"
            )


class PersonalisedRanker:
    """Re-rank retrieval results based on user interest profile.

    Applies learned user interests to boost document relevance scores.
    Uses 3-factor personalisation:
    1. Topic relevance: Document topics match user interests
    2. Historical access: Document previously accessed
    3. Co-occurrence: Topics frequently seen together

    Example:
        >>> ranker = PersonalisedRanker(profile_manager, extractor)
        >>> results = retriever.retrieve(query, k=20)
        >>> personalised = ranker.rerank(results, query, persona="researcher", k=10)
    """

    def __init__(
        self,
        profile_manager: ProfileManager,
        topic_extractor: TopicExtractor,
        config: Optional[PersonalisationConfig] = None,
    ):
        """Initialise personalised ranker.

        Args:
            profile_manager: Manager for interest profiles
            topic_extractor: Topic extraction engine
            config: Personalisation configuration
        """
        self.profile_manager = profile_manager
        self.extractor = topic_extractor
        self.config = config or PersonalisationConfig()

        # Cache for document access history (doc_id -> last_access_time)
        self._access_history: dict[str, datetime] = {}

        logger.info(
            f"PersonalisedRanker initialised (alpha={self.config.alpha}, "
            f"multiplier={self.config.retrieve_multiplier})"
        )

    def rerank(
        self,
        results: List[RetrievedChunk],
        query: str,
        persona: str,
        k: int,
    ) -> List[RetrievedChunk]:
        """Re-rank results using personalisation.

        Args:
            results: Initial retrieval results (should be k*multiplier)
            query: User query
            persona: Current persona
            k: Number of final results to return

        Returns:
            Top-k personalised results ordered by combined score

        Raises:
            ValueError: If persona not found or invalid parameters
        """
        if not results:
            return []

        if not self.config.enabled:
            logger.debug("Personalisation disabled, returning original results")
            return results[:k]

        # Get interest profile
        profile = self.profile_manager.get_profile(persona)
        if profile is None:
            logger.warning(f"No profile found for persona '{persona}', using base ranking")
            return results[:k]

        # Extract query topics
        query_topics = self.extractor.extract_topics(query)
        logger.debug(f"Extracted {len(query_topics)} topics from query")

        # Score each document
        scored_results = []
        for chunk in results:
            base_score = self._normalize_score(chunk.score)
            personalisation_score = self._calculate_personalisation(
                chunk, query_topics, profile
            )
            final_score = self._combine_scores(base_score, personalisation_score)

            scored_results.append((chunk, final_score, personalisation_score))

        # Sort by final score (descending) and return top-k
        scored_results.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            f"Reranked {len(results)} results to {k}, "
            f"avg boost: {sum(x[2] for x in scored_results[:k])/k:.3f}"
        )

        return [chunk for chunk, _, _ in scored_results[:k]]

    def _calculate_personalisation(
        self,
        chunk: RetrievedChunk,
        query_topics: List,
        profile: InterestProfile,
    ) -> float:
        """Calculate personalisation score for document chunk.

        Combines three factors:
        1. Topic relevance: Chunk topics match user interests
        2. Historical access: Chunk previously accessed
        3. Co-occurrence: Related to query topics

        Args:
            chunk: Retrieved chunk to score
            query_topics: Topics extracted from query
            profile: User interest profile

        Returns:
            Personalisation score (0.0-1.0+, can exceed 1.0 for high interest)
        """
        # Extract document topics from chunk metadata
        doc_topics = self._extract_chunk_topics(chunk)

        # 1. Topic relevance boost
        topic_boost = self._calculate_topic_boost(doc_topics, profile)

        # 2. Historical access boost
        history_boost = self._calculate_history_boost(chunk, profile)

        # 3. Co-occurrence boost
        cooccurrence_boost = self._calculate_cooccurrence_boost(
            doc_topics, query_topics, profile
        )

        # Combine with configured weights
        personalisation_score = (
            topic_boost * self.config.topic_relevance_weight +
            history_boost * self.config.historical_access_weight +
            cooccurrence_boost * self.config.co_occurrence_weight
        )

        logger.debug(
            f"Personalisation: topic={topic_boost:.3f}, "
            f"history={history_boost:.3f}, cooccur={cooccurrence_boost:.3f}, "
            f"total={personalisation_score:.3f}"
        )

        return personalisation_score

    def _calculate_topic_boost(
        self,
        doc_topics: List[str],
        profile: InterestProfile,
    ) -> float:
        """Calculate topic relevance boost.

        Boosts documents whose topics match user interests, weighted by
        interest confidence and recency.

        Args:
            doc_topics: Topics from document
            profile: User interest profile

        Returns:
            Topic boost score (0.0-1.0+)
        """
        if not doc_topics or not profile.topics:
            return 0.0

        topic_boost = 0.0
        for doc_topic in doc_topics:
            # Normalise topic name for matching
            normalised = doc_topic.lower().strip()

            if normalised in profile.topics:
                interest = profile.topics[normalised]

                # Only boost if confidence meets threshold
                if interest.confidence >= self.config.min_confidence_threshold:
                    # Weight by confidence and recency
                    boost = interest.confidence * interest.recency
                    topic_boost += boost

        # Normalise by number of topics (prevent accumulation)
        if doc_topics:
            topic_boost = min(topic_boost / len(doc_topics), 1.0)

        return topic_boost

    def _calculate_history_boost(
        self,
        chunk: RetrievedChunk,
        profile: InterestProfile,
    ) -> float:
        """Calculate historical access boost.

        Boosts documents that user has accessed before, with time decay.

        Args:
            chunk: Retrieved chunk
            profile: User interest profile

        Returns:
            History boost score (0.0-1.0)
        """
        # Check if document in access history
        doc_id = chunk.document_id
        if doc_id not in self._access_history:
            return 0.0

        # Apply time decay
        last_access = self._access_history[doc_id]
        days_ago = (datetime.now() - last_access).days

        # Exponential decay: e^(-rate * days)
        import math
        decay = math.exp(-self.config.time_decay_rate * days_ago)

        return decay

    def _calculate_cooccurrence_boost(
        self,
        doc_topics: List[str],
        query_topics: List,
        profile: InterestProfile,
    ) -> float:
        """Calculate co-occurrence boost.

        Boosts documents with topics that frequently co-occur with query topics
        in user's interest profile.

        Args:
            doc_topics: Topics from document
            query_topics: Topics from query
            profile: User interest profile

        Returns:
            Co-occurrence boost score (0.0-1.0)
        """
        if not doc_topics or not query_topics or not profile.topics:
            return 0.0

        cooccurrence_boost = 0.0

        for query_topic in query_topics:
            normalised_query = query_topic.name.lower().strip()

            if normalised_query in profile.topics:
                interest = profile.topics[normalised_query]

                # Check if document topics co-occur with query topic
                for doc_topic in doc_topics:
                    normalised_doc = doc_topic.lower().strip()

                    if normalised_doc in interest.co_occurring_topics:
                        # Boost based on co-occurrence count
                        count = interest.co_occurring_topics[normalised_doc]
                        # Normalise: log scale to prevent dominance
                        import math
                        boost = min(math.log2(count + 1) / 10, 0.1)
                        cooccurrence_boost += boost

        return min(cooccurrence_boost, 1.0)

    def _extract_chunk_topics(self, chunk: RetrievedChunk) -> List[str]:
        """Extract topics from chunk.

        Extracts topics from:
        1. Chunk text (first 200 chars for performance)
        2. Document path/filename
        3. Metadata (if available)

        Args:
            chunk: Retrieved chunk

        Returns:
            List of topic strings (normalised to lowercase)
        """
        topics = []

        # Extract from chunk text (sample for performance)
        text_sample = chunk.text[:200]
        extracted = self.extractor.extract_topics(text_sample)
        topics.extend([t.name.lower() for t in extracted])

        # Extract from document path
        path_topics = self.extractor.extract_from_document(chunk.document_path)
        topics.extend([t.name.lower() for t in path_topics])

        # Deduplicate
        return list(set(topics))

    def _normalize_score(self, score: float) -> float:
        """Normalise retrieval score to 0.0-1.0 range.

        Vector stores return distance (lower is better), convert to similarity.

        Args:
            score: Original score (distance)

        Returns:
            Normalised similarity score (0.0-1.0, higher is better)
        """
        # Assume score is distance (0 = perfect match, higher = less similar)
        # Convert to similarity: 1 / (1 + distance)
        return 1.0 / (1.0 + score)

    def _combine_scores(
        self,
        base_score: float,
        personalisation_score: float,
    ) -> float:
        """Combine base retrieval score with personalisation.

        Uses weighted combination controlled by alpha parameter.

        Args:
            base_score: Similarity score from retrieval (0.0-1.0)
            personalisation_score: Personalisation boost (0.0-1.0+)

        Returns:
            Combined score
        """
        alpha = self.config.alpha
        return (1 - alpha) * base_score + alpha * personalisation_score

    def record_access(self, document_id: str, access_time: Optional[datetime] = None):
        """Record document access for historical boosting.

        Args:
            document_id: Document identifier
            access_time: Access timestamp (defaults to now)
        """
        self._access_history[document_id] = access_time or datetime.now()

    def clear_access_history(self):
        """Clear document access history."""
        self._access_history.clear()
        logger.info("Access history cleared")
