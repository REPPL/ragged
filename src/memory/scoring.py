"""Scoring utilities for personalised ranking (v0.4.8).

Provides helper functions for calculating various scoring components used in
personalised retrieval ranking.
"""

import math
from datetime import datetime
from typing import List, Tuple


def normalize_distance_to_similarity(distance: float) -> float:
    """Convert distance score to similarity score.

    Vector stores typically return distance (lower = better).
    Convert to similarity (higher = better) for intuitive ranking.

    Args:
        distance: Distance score from vector search

    Returns:
        Similarity score in range [0.0, 1.0]
    """
    return 1.0 / (1.0 + distance)


def apply_time_decay(
    timestamp: datetime,
    current_time: datetime,
    decay_rate: float = 0.05,
) -> float:
    """Apply exponential time decay to a score.

    Older items receive lower scores based on exponential decay function.

    Args:
        timestamp: Original timestamp
        current_time: Current time for comparison
        decay_rate: Decay rate per day (default: 0.05 = ~7 day half-life)

    Returns:
        Decayed score in range [0.0, 1.0]

    Examples:
        >>> from datetime import timedelta
        >>> now = datetime.now()
        >>> yesterday = now - timedelta(days=1)
        >>> score = apply_time_decay(yesterday, now, decay_rate=0.05)
        >>> 0.9 < score < 1.0  # Slight decay after 1 day
        True
    """
    days_ago = (current_time - timestamp).days
    if days_ago < 0:
        days_ago = 0  # Handle future timestamps gracefully

    # Exponential decay: e^(-rate * days)
    return math.exp(-decay_rate * days_ago)


def calculate_logarithmic_boost(
    count: int,
    base: float = 2.0,
    scale: float = 10.0,
) -> float:
    """Calculate logarithmic boost for frequency/count values.

    Prevents high-frequency items from dominating, applies diminishing returns.

    Args:
        count: Frequency or count value
        base: Logarithm base (default: 2.0)
        scale: Scaling factor (default: 10.0)

    Returns:
        Boost score in range [0.0, 1.0]

    Examples:
        >>> calculate_logarithmic_boost(1)  # First occurrence
        0.1
        >>> calculate_logarithmic_boost(10)  # 10 occurrences
        0.33...
        >>> calculate_logarithmic_boost(100)  # 100 occurrences
        0.66...
    """
    if count <= 0:
        return 0.0

    boost = math.log(count + 1, base) / scale
    return min(boost, 1.0)  # Cap at 1.0


def combine_scores_weighted(
    scores: List[Tuple[float, float]],
) -> float:
    """Combine multiple scores with weights.

    Args:
        scores: List of (score, weight) tuples

    Returns:
        Weighted combination of scores

    Raises:
        ValueError: If weights don't sum to approximately 1.0

    Examples:
        >>> combine_scores_weighted([(0.8, 0.5), (0.6, 0.3), (0.4, 0.2)])
        0.7
    """
    if not scores:
        return 0.0

    # Validate weights sum to ~1.0
    total_weight = sum(weight for _, weight in scores)
    if not 0.99 <= total_weight <= 1.01:
        raise ValueError(
            f"Weights must sum to 1.0, got {total_weight:.3f}"
        )

    # Calculate weighted sum
    weighted_sum = sum(score * weight for score, weight in scores)
    return weighted_sum


def interpolate_scores(
    score1: float,
    score2: float,
    alpha: float,
) -> float:
    """Interpolate between two scores.

    Linear interpolation: (1-α) * score1 + α * score2

    Args:
        score1: First score
        score2: Second score
        alpha: Interpolation weight (0.0-1.0)

    Returns:
        Interpolated score

    Raises:
        ValueError: If alpha not in [0.0, 1.0]

    Examples:
        >>> interpolate_scores(0.5, 1.0, alpha=0.0)  # All score1
        0.5
        >>> interpolate_scores(0.5, 1.0, alpha=1.0)  # All score2
        1.0
        >>> interpolate_scores(0.5, 1.0, alpha=0.5)  # Midpoint
        0.75
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must be in [0.0, 1.0], got {alpha}")

    return (1.0 - alpha) * score1 + alpha * score2


def calculate_confidence_weighted_boost(
    relevance: float,
    confidence: float,
    recency: float,
) -> float:
    """Calculate boost weighted by confidence and recency.

    Combines relevance with confidence and recency to determine final boost.
    Used for topic-based boosting in personalised ranking.

    Args:
        relevance: Base relevance score (0.0-1.0)
        confidence: Confidence in the relevance (0.0-1.0)
        recency: Recency score with time decay (0.0-1.0)

    Returns:
        Weighted boost score (0.0-1.0)

    Examples:
        >>> calculate_confidence_weighted_boost(0.9, 0.8, 1.0)  # High all
        0.72
        >>> calculate_confidence_weighted_boost(0.9, 0.8, 0.5)  # Old interest
        0.36
    """
    # Multiply relevance by confidence and recency
    # This ensures low confidence or old interests have less impact
    return relevance * confidence * recency


def normalize_scores(scores: List[float]) -> List[float]:
    """Normalise a list of scores to [0.0, 1.0] range.

    Maps min score to 0.0 and max score to 1.0.

    Args:
        scores: List of scores to normalise

    Returns:
        Normalised scores

    Examples:
        >>> normalize_scores([1.0, 2.0, 3.0])
        [0.0, 0.5, 1.0]
        >>> normalize_scores([5.0, 5.0, 5.0])  # All same
        [1.0, 1.0, 1.0]
    """
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    # Handle case where all scores are the same
    if max_score == min_score:
        return [1.0] * len(scores)

    # Min-max normalisation
    range_score = max_score - min_score
    return [(s - min_score) / range_score for s in scores]


def calculate_rank_change(
    original_rank: int,
    new_rank: int,
) -> Tuple[int, str]:
    """Calculate rank change and direction.

    Args:
        original_rank: Original ranking position (0-indexed)
        new_rank: New ranking position (0-indexed)

    Returns:
        Tuple of (change_magnitude, direction) where direction is "up", "down", or "same"

    Examples:
        >>> calculate_rank_change(5, 2)  # Moved up
        (3, 'up')
        >>> calculate_rank_change(2, 5)  # Moved down
        (3, 'down')
        >>> calculate_rank_change(3, 3)  # No change
        (0, 'same')
    """
    change = original_rank - new_rank

    if change > 0:
        return (change, "up")
    elif change < 0:
        return (abs(change), "down")
    else:
        return (0, "same")
