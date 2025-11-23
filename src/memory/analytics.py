"""Analytics for interest profiles and personalisation effectiveness (v0.4.8).

Provides insights into interest profile quality and personalisation impact.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ragged.memory.profile import InterestProfile, ProfileManager
from ragged.memory.topics import TopicExtractor
from ragged.retrieval.retriever import RetrievedChunk
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileStatistics:
    """Statistics about an interest profile.

    Attributes:
        persona: Persona name
        total_topics: Total number of tracked topics
        high_confidence_topics: Topics with confidence > 0.7
        recent_activity_days: Days with activity in last period
        profile_age_days: Age of profile in days
        top_topics: List of (topic, confidence, frequency) tuples
        topic_distribution: Distribution of topics by confidence range
    """
    persona: str
    total_topics: int
    high_confidence_topics: int
    recent_activity_days: int
    profile_age_days: int
    top_topics: List[Tuple[str, float, int]]  # (topic, confidence, frequency)
    topic_distribution: Dict[str, int]  # confidence_range -> count


@dataclass
class PersonalisationImpact:
    """Impact metrics for personalisation.

    Attributes:
        queries_analysed: Number of queries analysed
        avg_relevance_improvement: Average relevance improvement (%)
        queries_benefiting: Percentage of queries that benefited
        top_impactful_topics: Topics with strongest personalisation impact
        rank_changes: Statistics on rank changes (promoted, demoted, unchanged)
    """
    queries_analysed: int
    avg_relevance_improvement: float
    queries_benefiting: float
    top_impactful_topics: List[Tuple[str, float]]  # (topic, impact_score)
    rank_changes: Dict[str, int]  # "promoted"/"demoted"/"unchanged" -> count


class ProfileAnalytics:
    """Analytics engine for interest profiles.

    Provides insights into profile quality, topic distribution, and
    personalisation effectiveness.

    Example:
        >>> analytics = ProfileAnalytics(profile_manager)
        >>> stats = analytics.get_profile_statistics("researcher")
        >>> print(f"Topics: {stats.total_topics}, High conf: {stats.high_confidence_topics}")
    """

    def __init__(self, profile_manager: ProfileManager):
        """Initialise analytics engine.

        Args:
            profile_manager: Manager for interest profiles
        """
        self.profile_manager = profile_manager
        logger.info("ProfileAnalytics initialised")

    def get_profile_statistics(
        self,
        persona: str,
        recent_days: int = 7,
    ) -> ProfileStatistics:
        """Get comprehensive statistics for a profile.

        Args:
            persona: Persona name
            recent_days: Consider activity in last N days as "recent"

        Returns:
            ProfileStatistics with comprehensive profile insights

        Raises:
            ValueError: If persona not found
        """
        profile = self.profile_manager.get_profile(persona)
        if profile is None:
            raise ValueError(f"Profile not found for persona '{persona}'")

        # Calculate statistics
        total_topics = len(profile.topics)
        high_confidence = sum(
            1 for interest in profile.topics.values() if interest.confidence > 0.7
        )

        # Recent activity
        recent_cutoff = datetime.now() - timedelta(days=recent_days)
        recent_activity_days = len(set(
            interest.last_seen.date()
            for interest in profile.topics.values()
            if interest.last_seen > recent_cutoff
        ))

        # Profile age
        if profile.topics:
            oldest = min(interest.first_seen for interest in profile.topics.values())
            profile_age = (datetime.now() - oldest).days
        else:
            profile_age = 0

        # Top topics (by confidence)
        top_topics = sorted(
            [
                (topic, interest.confidence, interest.frequency)
                for topic, interest in profile.topics.items()
            ],
            key=lambda x: x[1],  # Sort by confidence
            reverse=True
        )[:10]  # Top 10

        # Topic distribution by confidence ranges
        distribution = {
            "0.0-0.3": 0,
            "0.3-0.5": 0,
            "0.5-0.7": 0,
            "0.7-0.9": 0,
            "0.9-1.0": 0,
        }
        for interest in profile.topics.values():
            conf = interest.confidence
            if conf < 0.3:
                distribution["0.0-0.3"] += 1
            elif conf < 0.5:
                distribution["0.3-0.5"] += 1
            elif conf < 0.7:
                distribution["0.5-0.7"] += 1
            elif conf < 0.9:
                distribution["0.7-0.9"] += 1
            else:
                distribution["0.9-1.0"] += 1

        return ProfileStatistics(
            persona=persona,
            total_topics=total_topics,
            high_confidence_topics=high_confidence,
            recent_activity_days=recent_activity_days,
            profile_age_days=profile_age,
            top_topics=top_topics,
            topic_distribution=distribution,
        )

    def compare_ranking(
        self,
        base_results: List[RetrievedChunk],
        personalised_results: List[RetrievedChunk],
    ) -> Dict[str, any]:
        """Compare base vs personalised ranking.

        Analyses differences between standard and personalised ranking
        to measure personalisation impact.

        Args:
            base_results: Results from standard retrieval
            personalised_results: Results from personalised retrieval

        Returns:
            Dictionary with comparison metrics:
            - overlap: Number of documents in both result sets
            - promoted: Documents that moved up in ranking
            - demoted: Documents that moved down in ranking
            - new_docs: Documents only in personalised results
            - removed_docs: Documents only in base results
            - avg_rank_change: Average rank change magnitude

        Example:
            >>> comparison = analytics.compare_ranking(base_results, personalised_results)
            >>> print(f"Promoted: {len(comparison['promoted'])}")
        """
        # Create rank mappings
        base_ranks = {chunk.chunk_id: i for i, chunk in enumerate(base_results)}
        personalised_ranks = {chunk.chunk_id: i for i, chunk in enumerate(personalised_results)}

        # Find overlap
        base_ids = set(base_ranks.keys())
        pers_ids = set(personalised_ranks.keys())
        overlap = base_ids & pers_ids

        # Analyse rank changes
        promoted = []
        demoted = []
        rank_changes = []

        for chunk_id in overlap:
            base_rank = base_ranks[chunk_id]
            pers_rank = personalised_ranks[chunk_id]
            change = base_rank - pers_rank  # Positive = promoted

            if change > 0:
                promoted.append((chunk_id, change))
            elif change < 0:
                demoted.append((chunk_id, abs(change)))

            rank_changes.append(abs(change))

        # New and removed documents
        new_docs = list(pers_ids - base_ids)
        removed_docs = list(base_ids - pers_ids)

        # Average rank change
        avg_change = sum(rank_changes) / len(rank_changes) if rank_changes else 0.0

        return {
            "overlap": len(overlap),
            "promoted": promoted,
            "demoted": demoted,
            "new_docs": new_docs,
            "removed_docs": removed_docs,
            "avg_rank_change": avg_change,
        }

    def calculate_topic_impact(
        self,
        persona: str,
        top_n: int = 10,
    ) -> List[Tuple[str, float]]:
        """Calculate which topics have strongest personalisation impact.

        Impact score based on:
        - Topic confidence
        - Topic frequency
        - Number of related documents

        Args:
            persona: Persona name
            top_n: Number of top topics to return

        Returns:
            List of (topic, impact_score) tuples, sorted by impact

        Raises:
            ValueError: If persona not found
        """
        profile = self.profile_manager.get_profile(persona)
        if profile is None:
            raise ValueError(f"Profile not found for persona '{persona}'")

        # Calculate impact scores
        topic_impacts = []
        for topic, interest in profile.topics.items():
            # Impact = confidence * log(frequency) * log(doc_count)
            import math
            freq_score = math.log2(interest.frequency + 1)
            doc_score = math.log2(len(interest.related_documents) + 1)
            impact = interest.confidence * freq_score * doc_score

            topic_impacts.append((topic, impact))

        # Sort by impact and return top-N
        topic_impacts.sort(key=lambda x: x[1], reverse=True)
        return topic_impacts[:top_n]

    def get_profile_health_score(self, persona: str) -> float:
        """Calculate overall health score for profile.

        Health score (0.0-1.0) based on:
        - Number of topics (more is better, up to a point)
        - Confidence distribution (balanced is better)
        - Recent activity (active is better)
        - Profile age (mature is better)

        Args:
            persona: Persona name

        Returns:
            Health score in range [0.0, 1.0]

        Raises:
            ValueError: If persona not found
        """
        stats = self.get_profile_statistics(persona)

        # Topic count score (0.0-0.3)
        # Optimal: 20-50 topics
        if stats.total_topics == 0:
            topic_score = 0.0
        elif stats.total_topics < 10:
            topic_score = stats.total_topics / 10 * 0.3
        elif stats.total_topics <= 50:
            topic_score = 0.3
        else:
            # Penalty for too many topics (noise)
            topic_score = max(0.1, 0.3 - (stats.total_topics - 50) / 200)

        # Confidence distribution score (0.0-0.3)
        # Good: Most topics in 0.5-0.9 range
        high_conf = stats.topic_distribution["0.7-0.9"] + stats.topic_distribution["0.9-1.0"]
        if stats.total_topics > 0:
            high_conf_ratio = high_conf / stats.total_topics
            confidence_score = min(high_conf_ratio, 0.5) * 0.6  # Max 0.3
        else:
            confidence_score = 0.0

        # Recent activity score (0.0-0.2)
        # Good: Activity in last 7 days
        activity_score = min(stats.recent_activity_days / 7, 1.0) * 0.2

        # Profile age score (0.0-0.2)
        # Good: At least 7 days old (more data)
        age_score = min(stats.profile_age_days / 30, 1.0) * 0.2

        total_score = topic_score + confidence_score + activity_score + age_score

        logger.debug(
            f"Health score for {persona}: {total_score:.3f} "
            f"(topics={topic_score:.3f}, conf={confidence_score:.3f}, "
            f"activity={activity_score:.3f}, age={age_score:.3f})"
        )

        return total_score

    def generate_profile_report(self, persona: str) -> str:
        """Generate human-readable profile report.

        Args:
            persona: Persona name

        Returns:
            Formatted report string

        Raises:
            ValueError: If persona not found
        """
        stats = self.get_profile_statistics(persona)
        health = self.get_profile_health_score(persona)
        impact = self.calculate_topic_impact(persona, top_n=5)

        report = f"""
Interest Profile Report: {persona}
{'=' * 60}

Profile Health: {health:.2f}/1.00 ({self._health_label(health)})

Statistics:
- Total Topics: {stats.total_topics}
- High Confidence Topics (>0.7): {stats.high_confidence_topics}
- Recent Activity (7d): {stats.recent_activity_days} days
- Profile Age: {stats.profile_age_days} days

Topic Distribution:
"""
        for range_name, count in stats.topic_distribution.items():
            percentage = (count / stats.total_topics * 100) if stats.total_topics > 0 else 0
            report += f"  {range_name}: {count:3d} ({percentage:5.1f}%)\n"

        report += "\nTop Topics (by confidence):\n"
        for i, (topic, conf, freq) in enumerate(stats.top_topics[:5], 1):
            report += f"  {i}. {topic:20s} (conf: {conf:.2f}, freq: {freq:3d})\n"

        report += "\nMost Impactful Topics (for personalisation):\n"
        for i, (topic, impact) in enumerate(impact, 1):
            report += f"  {i}. {topic:20s} (impact: {impact:.3f})\n"

        return report

    def _health_label(self, score: float) -> str:
        """Convert health score to label.

        Args:
            score: Health score (0.0-1.0)

        Returns:
            Health label (Poor, Fair, Good, Excellent)
        """
        if score < 0.3:
            return "Poor"
        elif score < 0.5:
            return "Fair"
        elif score < 0.7:
            return "Good"
        else:
            return "Excellent"
