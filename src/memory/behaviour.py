"""Behaviour learning system (v0.4.7).

Learns from user interaction patterns and automatically updates interest profiles.

Privacy: All learning performed locally, no external API calls.
"""

from pathlib import Path
from typing import List, Optional

from ragged.memory.confidence import ConfidenceCalculator, update_topic_confidence
from ragged.memory.graph import KnowledgeGraph
from ragged.memory.interactions import Interaction
from ragged.memory.profile import InterestProfile, ProfileManager
from ragged.memory.topic_config import TopicExtractionConfig
from ragged.memory.topics import Topic, TopicExtractor
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class BehaviourLearner:
    """Learn from user behaviour patterns and update interest profiles.

    Automatically processes interactions to:
    - Extract topics from queries and documents
    - Update interest profiles
    - Calculate confidence scores
    - Detect co-occurring topics
    - Update knowledge graph (optional)
    """

    def __init__(
        self,
        profile_manager: ProfileManager,
        topic_config: Optional[TopicExtractionConfig] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        enable_graph_updates: bool = False,
    ):
        """Initialize behaviour learner.

        Args:
            profile_manager: ProfileManager for storing profiles
            topic_config: Topic extraction configuration (uses default if None)
            confidence_calculator: Confidence calculator (uses default if None)
            knowledge_graph: Optional knowledge graph for relationship tracking
            enable_graph_updates: Enable automatic graph updates (default: False)
        """
        self.profile_manager = profile_manager
        self.knowledge_graph = knowledge_graph
        self.enable_graph_updates = enable_graph_updates

        # Initialize topic extractor
        if topic_config is None:
            topic_config = TopicExtractionConfig()

        self.extractor = TopicExtractor(
            min_topic_length=topic_config.min_topic_length,
            max_topics_per_query=topic_config.max_topics_per_query,
            min_confidence=topic_config.confidence_threshold,
            stop_words=topic_config.stop_words,
            enable_phrases=topic_config.enable_phrases,
        )

        # Initialize confidence calculator
        self.confidence_calculator = (
            confidence_calculator if confidence_calculator else ConfidenceCalculator()
        )

        logger.debug(
            f"BehaviourLearner initialized: "
            f"graph_updates={enable_graph_updates}, "
            f"min_confidence={topic_config.confidence_threshold}"
        )

    def process_interaction(self, interaction: Interaction) -> InterestProfile:
        """Process interaction and update interest profile.

        Learning pipeline:
        1. Extract topics from query
        2. Extract topics from retrieved documents
        3. Update interest profile
        4. Detect co-occurring topics
        5. Update confidence scores
        6. Update knowledge graph (if enabled)
        7. Save profile

        Args:
            interaction: User interaction to process

        Returns:
            Updated InterestProfile

        Example:
            >>> from ragged.memory.interactions import Interaction
            >>> from ragged.memory.profile import ProfileManager
            >>> from pathlib import Path
            >>>
            >>> manager = ProfileManager(Path("profiles.db"))
            >>> learner = BehaviourLearner(manager)
            >>>
            >>> interaction = Interaction(
            ...     persona="researcher",
            ...     query="What are the latest RAG techniques?",
            ...     retrieved_doc_ids=["rag_paper_2023.pdf"],
            ... )
            >>>
            >>> profile = learner.process_interaction(interaction)
            >>> "rag" in profile.topics
            True
        """
        logger.debug(
            f"Processing interaction for persona '{interaction.persona}': "
            f"query='{interaction.query[:50]}...'"
        )

        # Step 1: Extract topics from query
        query_topics = self.extractor.extract_topics(interaction.query)

        # Step 2: Extract topics from retrieved documents
        doc_topics = []
        if interaction.retrieved_doc_ids:
            doc_topics = self.extractor.extract_from_documents(
                interaction.retrieved_doc_ids
            )

        # Combine all topics
        all_topics = query_topics + doc_topics

        logger.debug(
            f"Extracted {len(query_topics)} query topics, "
            f"{len(doc_topics)} document topics"
        )

        # Step 3: Update interest profile
        profile = self.profile_manager.get_profile(interaction.persona)

        # Get all topic names for co-occurrence detection
        topic_names = [t.name for t in all_topics]

        for topic in all_topics:
            # Update topic interest with co-occurring topics and documents
            profile.update_topic_interest(
                topic,
                doc_ids=interaction.retrieved_doc_ids,
                related_topics=[name for name in topic_names if name != topic.name],
            )

        # Step 4: Update confidence scores for all topics in profile
        for interest in profile.topics.values():
            update_topic_confidence(interest, self.confidence_calculator)

        # Step 5: Apply time decay (keeps recency scores current)
        profile.apply_time_decay()

        # Step 6: Update knowledge graph (if enabled)
        if self.enable_graph_updates and self.knowledge_graph:
            self._update_knowledge_graph(interaction.persona, all_topics, interaction.retrieved_doc_ids)

        # Step 7: Save updated profile
        self.profile_manager.save_profile(profile)

        logger.info(
            f"Updated profile for '{interaction.persona}': "
            f"{len(profile.topics)} topics tracked"
        )

        return profile

    def _update_knowledge_graph(
        self,
        persona: str,
        topics: List[Topic],
        doc_ids: List[str],
    ) -> None:
        """Update knowledge graph with topics and document relationships.

        Args:
            persona: Persona name
            topics: Extracted topics
            doc_ids: Retrieved document IDs
        """
        if not self.knowledge_graph:
            return

        # Add topics to graph
        for topic in topics:
            try:
                self.knowledge_graph.add_topic(persona, topic.name)
            except Exception as e:
                logger.warning(f"Failed to add topic '{topic.name}' to graph: {e}")

        # Link topics to documents
        for topic in topics:
            for doc_id in doc_ids:
                try:
                    self.knowledge_graph.link_topic_to_document(
                        persona, topic.name, doc_id
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to link topic '{topic.name}' to document '{doc_id}': {e}"
                    )

        logger.debug(
            f"Updated knowledge graph: {len(topics)} topics, "
            f"{len(doc_ids)} documents"
        )

    def process_batch(self, interactions: List[Interaction]) -> None:
        """Process multiple interactions in batch.

        More efficient than processing individually for bulk imports.

        Args:
            interactions: List of interactions to process

        Example:
            >>> interactions = [
            ...     Interaction(persona="user", query="What is RAG?"),
            ...     Interaction(persona="user", query="How does vector search work?"),
            ... ]
            >>> learner.process_batch(interactions)
        """
        logger.info(f"Processing batch of {len(interactions)} interactions")

        for interaction in interactions:
            try:
                self.process_interaction(interaction)
            except Exception as e:
                logger.error(
                    f"Failed to process interaction {interaction.id}: {e}"
                )

        logger.info(f"Batch processing complete: {len(interactions)} interactions")

    def get_persona_insights(self, persona: str) -> dict:
        """Get insights about persona's interests.

        Args:
            persona: Persona name

        Returns:
            Dictionary with insights:
                - top_topics: Top 10 topics by confidence
                - total_topics: Total topics tracked
                - profile_age_days: Days since profile creation
                - most_related_topics: Topics with most co-occurrences

        Example:
            >>> insights = learner.get_persona_insights("researcher")
            >>> insights["total_topics"]
            37
        """
        profile = self.profile_manager.get_profile(persona)

        # Get top topics
        top_topics = profile.get_top_topics(limit=10)

        # Calculate profile age
        from datetime import datetime

        profile_age = (datetime.now() - profile.created_at).days

        # Find topics with most co-occurrences
        topics_by_relations = sorted(
            profile.topics.values(),
            key=lambda t: len(t.co_occurring_topics),
            reverse=True,
        )[:10]

        return {
            "top_topics": [
                {
                    "topic": t.topic,
                    "confidence": t.confidence,
                    "frequency": t.frequency,
                    "last_seen": t.last_seen.isoformat(),
                }
                for t in top_topics
            ],
            "total_topics": len(profile.topics),
            "profile_age_days": profile_age,
            "most_related_topics": [
                {
                    "topic": t.topic,
                    "relations": len(t.co_occurring_topics),
                    "top_related": list(t.co_occurring_topics.keys())[:5],
                }
                for t in topics_by_relations
            ],
        }

    def forget_topic(self, persona: str, topic_name: str) -> bool:
        """Remove topic from persona's profile (GDPR right to erasure).

        Args:
            persona: Persona name
            topic_name: Topic to remove

        Returns:
            True if topic was removed, False if not found

        Example:
            >>> learner.forget_topic("researcher", "RAG")
            True
        """
        profile = self.profile_manager.get_profile(persona)

        removed = profile.remove_topic(topic_name)

        if removed:
            # Also remove from knowledge graph if enabled
            if self.enable_graph_updates and self.knowledge_graph:
                try:
                    # Remove topic from graph
                    # Note: KnowledgeGraph doesn't have a remove_topic method yet
                    # This would be added in a future enhancement
                    pass
                except Exception as e:
                    logger.warning(f"Failed to remove topic from graph: {e}")

            # Save updated profile
            self.profile_manager.save_profile(profile)

            logger.info(f"Removed topic '{topic_name}' from persona '{persona}'")

        return removed

    def reset_profile(self, persona: str) -> bool:
        """Reset persona's interest profile (GDPR right to erasure).

        Args:
            persona: Persona name

        Returns:
            True if profile was reset

        Example:
            >>> learner.reset_profile("researcher")
            True
        """
        deleted = self.profile_manager.delete_profile(persona)

        if deleted:
            logger.info(f"Reset profile for persona '{persona}'")

        return deleted

    def export_profile(self, persona: str) -> str:
        """Export persona's profile as JSON (GDPR data portability).

        Args:
            persona: Persona name

        Returns:
            JSON string of profile

        Example:
            >>> json_data = learner.export_profile("researcher")
            >>> "topics" in json_data
            True
        """
        profile = self.profile_manager.get_profile(persona)
        return profile.export_to_json()


def create_behaviour_learner(
    storage_dir: Path,
    topic_config: Optional[TopicExtractionConfig] = None,
    enable_graph: bool = False,
) -> BehaviourLearner:
    """Create behaviour learner with default configuration.

    Args:
        storage_dir: Directory for storing profiles and graph
        topic_config: Optional topic extraction configuration
        enable_graph: Enable knowledge graph integration

    Returns:
        Configured BehaviourLearner instance

    Example:
        >>> from pathlib import Path
        >>> learner = create_behaviour_learner(Path("~/.ragged/memory"))
    """
    storage_dir = Path(storage_dir).expanduser()
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Initialize profile manager
    profile_path = storage_dir / "profiles.db"
    profile_manager = ProfileManager(profile_path)

    # Initialize knowledge graph if enabled
    knowledge_graph = None
    if enable_graph:
        graph_path = storage_dir / "knowledge"
        knowledge_graph = KnowledgeGraph(graph_path)

    # Create learner
    learner = BehaviourLearner(
        profile_manager=profile_manager,
        topic_config=topic_config,
        knowledge_graph=knowledge_graph,
        enable_graph_updates=enable_graph,
    )

    logger.info(
        f"Created behaviour learner: storage={storage_dir}, graph={enable_graph}"
    )

    return learner
