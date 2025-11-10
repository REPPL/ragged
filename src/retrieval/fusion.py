"""Reciprocal Rank Fusion (RRF) for combining retrieval results."""

from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, Any, float, dict]]],
    k: int = 60,
) -> List[Tuple[str, Any, float, dict]]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion.

    RRF formula: score(d) = sum(1 / (k + rank(d))) across all rankings

    Args:
        rankings: List of ranked result lists, each containing
                  (doc_id, content, score, metadata) tuples
        k: RRF constant (default 60, standard in literature)

    Returns:
        Fused ranking as list of (doc_id, content, rrf_score, metadata) tuples,
        sorted by RRF score descending
    """
    if not rankings:
        return []

    # Remove empty rankings
    rankings = [r for r in rankings if r]

    if not rankings:
        return []

    # Calculate RRF scores
    rrf_scores: Dict[str, float] = {}
    doc_content: Dict[str, Any] = {}
    doc_metadata: Dict[str, dict] = {}

    for ranking in rankings:
        for rank, (doc_id, content, score, metadata) in enumerate(ranking, start=1):
            # RRF formula
            rrf_score = 1.0 / (k + rank)

            # Accumulate scores
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score

            # Store content and metadata (use first occurrence)
            if doc_id not in doc_content:
                doc_content[doc_id] = content
                doc_metadata[doc_id] = metadata

    # Sort by RRF score descending
    sorted_doc_ids = sorted(
        rrf_scores.keys(),
        key=lambda doc_id: rrf_scores[doc_id],
        reverse=True
    )

    # Build result list
    results = [
        (
            doc_id,
            doc_content[doc_id],
            rrf_scores[doc_id],
            doc_metadata[doc_id]
        )
        for doc_id in sorted_doc_ids
    ]

    logger.debug(
        f"RRF fusion: {len(rankings)} rankings -> {len(results)} unique documents"
    )

    return results


def weighted_fusion(
    rankings: List[List[Tuple[str, Any, float, dict]]],
    weights: List[float],
) -> List[Tuple[str, Any, float, dict]]:
    """Combine rankings using weighted score fusion.

    Simple weighted average of normalized scores.

    Args:
        rankings: List of ranked result lists
        weights: Weight for each ranking (must sum to 1.0)

    Returns:
        Fused ranking sorted by weighted score descending
    """
    if not rankings:
        return []

    if len(rankings) != len(weights):
        raise ValueError("Number of rankings must match number of weights")

    if abs(sum(weights) - 1.0) > 0.01:
        raise ValueError("Weights must sum to 1.0")

    # Normalize scores within each ranking
    normalized_rankings = []
    for ranking in rankings:
        if not ranking:
            normalized_rankings.append([])
            continue

        # Find max score for normalization
        max_score = max(score for _, _, score, _ in ranking)
        if max_score == 0:
            normalized_rankings.append(ranking)
            continue

        # Normalize to [0, 1]
        normalized = [
            (doc_id, content, score / max_score, metadata)
            for doc_id, content, score, metadata in ranking
        ]
        normalized_rankings.append(normalized)

    # Calculate weighted scores
    weighted_scores: Dict[str, float] = {}
    doc_content: Dict[str, Any] = {}
    doc_metadata: Dict[str, dict] = {}

    for ranking, weight in zip(normalized_rankings, weights):
        for doc_id, content, score, metadata in ranking:
            weighted_scores[doc_id] = weighted_scores.get(doc_id, 0.0) + (score * weight)

            if doc_id not in doc_content:
                doc_content[doc_id] = content
                doc_metadata[doc_id] = metadata

    # Sort by weighted score descending
    sorted_doc_ids = sorted(
        weighted_scores.keys(),
        key=lambda doc_id: weighted_scores[doc_id],
        reverse=True
    )

    results = [
        (doc_id, doc_content[doc_id], weighted_scores[doc_id], doc_metadata[doc_id])
        for doc_id in sorted_doc_ids
    ]

    logger.debug(
        f"Weighted fusion: {len(rankings)} rankings with weights {weights} "
        f"-> {len(results)} documents"
    )

    return results
