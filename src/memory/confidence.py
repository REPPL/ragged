"""Confidence calculation for interest profiles (v0.4.7).

Calculates interest confidence scores based on multiple factors.

Confidence Formula:
    confidence = weighted_average([
        (frequency_score, 0.35),   # How often topic appears
        (recency_score, 0.30),     # Time decay
        (consistency_score, 0.20), # Regular vs sporadic
        (depth_score, 0.15)        # Related documents
    ])

Privacy: All calculations performed locally, no external dependencies.
"""

import math
from datetime import datetime, timedelta
from typing import List

from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class ConfidenceCalculator:
    """Calculate interest confidence scores for topics.

    Confidence represents how confident we are that a user is interested
    in a topic, based on frequency, recency, consistency, and depth.
    """

    def __init__(
        self,
        frequency_weight: float = 0.35,
        recency_weight: float = 0.30,
        consistency_weight: float = 0.20,
        depth_weight: float = 0.15,
    ):
        """Initialize confidence calculator.

        Args:
            frequency_weight: Weight for frequency score (default: 0.35)
            recency_weight: Weight for recency score (default: 0.30)
            consistency_weight: Weight for consistency score (default: 0.20)
            depth_weight: Weight for depth score (default: 0.15)
        """
        # Validate weights sum to 1.0
        total_weight = frequency_weight + recency_weight + consistency_weight + depth_weight
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.frequency_weight = frequency_weight
        self.recency_weight = recency_weight
        self.consistency_weight = consistency_weight
        self.depth_weight = depth_weight

        logger.debug(
            f"ConfidenceCalculator initialized: "
            f"freq={frequency_weight}, rec={recency_weight}, "
            f"cons={consistency_weight}, depth={depth_weight}"
        )

    def calculate_confidence(
        self,
        frequency: int,
        last_seen: datetime,
        first_seen: datetime,
        related_documents: List[str],
        timestamps: List[datetime] | None = None,
    ) -> float:
        """Calculate overall interest confidence.

        Args:
            frequency: How many times topic appeared
            last_seen: Most recent occurrence
            first_seen: First occurrence
            related_documents: Document IDs related to topic
            timestamps: Optional list of all occurrence timestamps (for consistency)

        Returns:
            Confidence score (0.0-1.0)

        Example:
            >>> calc = ConfidenceCalculator()
            >>> conf = calc.calculate_confidence(
            ...     frequency=24,
            ...     last_seen=datetime.now(),
            ...     first_seen=datetime.now() - timedelta(days=30),
            ...     related_documents=["doc1", "doc2"],
            ... )
            >>> 0.0 <= conf <= 1.0
            True
        """
        freq_score = self.calculate_frequency_score(frequency)
        rec_score = self.calculate_recency_score(last_seen)
        cons_score = self.calculate_consistency_score(
            first_seen, last_seen, frequency, timestamps
        )
        depth_score = self.calculate_depth_score(related_documents)

        confidence = (
            freq_score * self.frequency_weight
            + rec_score * self.recency_weight
            + cons_score * self.consistency_weight
            + depth_score * self.depth_weight
        )

        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        logger.debug(
            f"Confidence: {confidence:.3f} "
            f"(freq={freq_score:.2f}, rec={rec_score:.2f}, "
            f"cons={cons_score:.2f}, depth={depth_score:.2f})"
        )

        return confidence

    def calculate_frequency_score(self, frequency: int, max_frequency: int = 10) -> float:
        """Calculate frequency score (0.0-1.0).

        Higher frequency = higher score, with diminishing returns.

        Args:
            frequency: Number of occurrences
            max_frequency: Frequency for score of 1.0 (default: 10)

        Returns:
            Frequency score (0.0-1.0)

        Example:
            >>> calc = ConfidenceCalculator()
            >>> calc.calculate_frequency_score(1)
            0.1
            >>> calc.calculate_frequency_score(10)
            1.0
        """
        score = min(frequency / max_frequency, 1.0)
        return score

    def calculate_recency_score(
        self,
        last_seen: datetime,
        decay_rate: float = 0.1,
        decay_days: int = 30,
    ) -> float:
        """Calculate recency score with exponential time decay (0.0-1.0).

        Recent occurrences score higher, older ones decay exponentially.

        Args:
            last_seen: Most recent occurrence timestamp
            decay_rate: Decay rate per period (default: 0.1 = 10% decay)
            decay_days: Days per decay period (default: 30)

        Returns:
            Recency score (0.0-1.0)

        Example:
            >>> calc = ConfidenceCalculator()
            >>> # Just seen
            >>> calc.calculate_recency_score(datetime.now())
            1.0
            >>> # 30 days ago
            >>> calc.calculate_recency_score(datetime.now() - timedelta(days=30))
            0.9...
        """
        days_since = (datetime.now() - last_seen).days
        periods_passed = days_since / decay_days

        # Exponential decay: score = e^(-decay_rate * periods)
        score = math.exp(-decay_rate * periods_passed)

        return score

    def calculate_consistency_score(
        self,
        first_seen: datetime,
        last_seen: datetime,
        frequency: int,
        timestamps: List[datetime] | None = None,
    ) -> float:
        """Calculate consistency score (0.0-1.0).

        Regular, evenly-spaced interest scores higher than sporadic bursts.

        Args:
            first_seen: First occurrence
            last_seen: Most recent occurrence
            frequency: Total occurrences
            timestamps: Optional list of all timestamps (for variance calculation)

        Returns:
            Consistency score (0.0-1.0)

        Example:
            >>> calc = ConfidenceCalculator()
            >>> # Regular interest over 30 days
            >>> score = calc.calculate_consistency_score(
            ...     first_seen=datetime.now() - timedelta(days=30),
            ...     last_seen=datetime.now(),
            ...     frequency=30,
            ... )
            >>> score > 0.5
            True
        """
        if frequency == 1:
            # Single occurrence = low consistency (could be one-time query)
            return 0.3

        # Calculate expected interval (if evenly distributed)
        time_span_days = (last_seen - first_seen).days + 1  # +1 to avoid division by zero
        expected_interval_days = time_span_days / frequency if frequency > 1 else time_span_days

        if timestamps and len(timestamps) >= 2:
            # Calculate actual variance in intervals
            intervals = []
            sorted_timestamps = sorted(timestamps)
            for i in range(1, len(sorted_timestamps)):
                interval = (sorted_timestamps[i] - sorted_timestamps[i - 1]).days
                intervals.append(interval)

            # Calculate coefficient of variation (CV)
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                if mean_interval > 0:
                    variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                    std_dev = math.sqrt(variance)
                    cv = std_dev / mean_interval  # Coefficient of variation

                    # Lower CV = more consistent = higher score
                    # CV of 0 (perfectly regular) = score 1.0
                    # CV of 1 (high variance) = score ~0.37
                    # CV of 2+ (very sporadic) = score ~0.13
                    score = math.exp(-cv)
                    return score

        # Fallback: estimate consistency from frequency and time span
        # More frequent over longer period = likely more consistent
        if time_span_days > 0:
            daily_frequency = frequency / time_span_days
            # Normalize: 1+ occurrence per day = very consistent (score ~1.0)
            # 1 occurrence per month (~0.033/day) = less consistent (score ~0.7)
            score = 1.0 - math.exp(-daily_frequency * 30)  # Scale by 30 days
            return score

        return 0.5  # Neutral score if can't calculate

    def calculate_depth_score(
        self,
        related_documents: List[str],
        max_documents: int = 50,
    ) -> float:
        """Calculate depth score based on related documents (0.0-1.0).

        More documents accessed = deeper interest.

        Args:
            related_documents: List of document IDs
            max_documents: Number of docs for score of 1.0 (default: 50)

        Returns:
            Depth score (0.0-1.0)

        Example:
            >>> calc = ConfidenceCalculator()
            >>> calc.calculate_depth_score([])
            0.0
            >>> calc.calculate_depth_score(["doc1", "doc2", "doc3"])
            0.06
            >>> calc.calculate_depth_score(["doc" + str(i) for i in range(50)])
            1.0
        """
        num_docs = len(related_documents)
        score = min(num_docs / max_documents, 1.0)
        return score


def update_topic_confidence(
    topic_interest,
    calculator: ConfidenceCalculator | None = None,
    timestamps: List[datetime] | None = None,
) -> None:
    """Update confidence score for a TopicInterest.

    Modifies the topic_interest in-place.

    Args:
        topic_interest: TopicInterest instance to update
        calculator: Optional custom ConfidenceCalculator (uses default if None)
        timestamps: Optional list of all occurrence timestamps

    Example:
        >>> from ragged.memory.profile import TopicInterest
        >>> from datetime import datetime, timedelta
        >>> topic = TopicInterest(
        ...     topic="RAG",
        ...     frequency=24,
        ...     last_seen=datetime.now(),
        ...     first_seen=datetime.now() - timedelta(days=30),
        ...     related_documents=["doc1", "doc2"],
        ... )
        >>> update_topic_confidence(topic)
        >>> 0.0 <= topic.confidence <= 1.0
        True
    """
    if calculator is None:
        calculator = ConfidenceCalculator()

    topic_interest.confidence = calculator.calculate_confidence(
        frequency=topic_interest.frequency,
        last_seen=topic_interest.last_seen,
        first_seen=topic_interest.first_seen,
        related_documents=topic_interest.related_documents,
        timestamps=timestamps,
    )
