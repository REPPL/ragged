"""
Answer confidence scoring implementation.

This module provides confidence scoring for generated answers based on
retrieval quality, generation quality, and citation coverage.

Confidence helps users understand answer reliability and identify cases
where the system might be uncertain or hallucinating.
"""

from dataclasses import dataclass
from typing import Any, List


@dataclass
class ConfidenceScore:
    """
    Confidence breakdown for an answer.

    Each component score ranges from 0.0 to 1.0.
    Overall confidence is weighted average of components.
    """

    retrieval_score: float  # 0-1: How relevant are retrieved chunks?
    generation_score: float  # 0-1: LLM confidence in answer
    citation_coverage: float  # 0-1: How much is cited?
    overall_confidence: float  # 0-1: Weighted average

    def to_str(self) -> str:
        """
        Human-readable confidence level.

        Returns:
            Verbal description of confidence level
        """
        if self.overall_confidence >= 0.9:
            return "Very High"
        elif self.overall_confidence >= 0.75:
            return "High"
        elif self.overall_confidence >= 0.6:
            return "Medium"
        elif self.overall_confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary with all scores and verbal level
        """
        return {
            "retrieval_score": self.retrieval_score,
            "generation_score": self.generation_score,
            "citation_coverage": self.citation_coverage,
            "overall_confidence": self.overall_confidence,
            "level": self.to_str(),
        }


class ConfidenceCalculator:
    """
    Calculate answer confidence scores.

    Confidence is based on three factors:
    1. Retrieval score: How similar are retrieved chunks to query?
    2. Generation score: Quality signals from answer (heuristic-based)
    3. Citation coverage: What percentage of answer is cited?

    Example:
        >>> calculator = ConfidenceCalculator()
        >>> confidence = calculator.calculate(
        ...     retrieved_chunks=[chunk1, chunk2],
        ...     answer="RAG combines retrieval and generation...",
        ...     citations=["[Source: doc1.pdf, page 5]"]
        ... )
        >>> print(f"Confidence: {confidence.to_str()}")
    """

    def __init__(
        self,
        retrieval_weight: float = 0.4,
        generation_weight: float = 0.3,
        citation_weight: float = 0.3,
    ) -> None:
        """
        Initialise calculator with weights.

        Args:
            retrieval_weight: Weight for retrieval score (default: 0.4)
            generation_weight: Weight for LLM confidence (default: 0.3)
            citation_weight: Weight for citation coverage (default: 0.3)

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        total_weight = retrieval_weight + generation_weight + citation_weight
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(
                f"Weights must sum to 1.0, got {total_weight:.3f}"
            )

        self.retrieval_weight = retrieval_weight
        self.generation_weight = generation_weight
        self.citation_weight = citation_weight

    def calculate(
        self,
        retrieved_chunks: List[Any],
        answer: str,
        citations: List[str],
    ) -> ConfidenceScore:
        """
        Calculate confidence for an answer.

        Args:
            retrieved_chunks: Retrieved chunks with scores (must have .score attribute)
            answer: Generated answer
            citations: Extracted citations

        Returns:
            ConfidenceScore with breakdown
        """
        # Retrieval score: Average of top-k chunk scores
        if retrieved_chunks and hasattr(retrieved_chunks[0], 'score'):
            retrieval_score = sum(
                c.score for c in retrieved_chunks
            ) / len(retrieved_chunks)
        else:
            retrieval_score = 0.0

        # Generation score: Placeholder (will use LLM logprobs in future)
        # For now, use heuristics: length, clarity, etc.
        generation_score = self._estimate_generation_quality(answer)

        # Citation coverage: Percentage of answer with citations
        citation_coverage = self._calculate_citation_coverage(
            answer, citations
        )

        # Overall confidence: Weighted average
        overall = (
            self.retrieval_weight * retrieval_score +
            self.generation_weight * generation_score +
            self.citation_weight * citation_coverage
        )

        return ConfidenceScore(
            retrieval_score=retrieval_score,
            generation_score=generation_score,
            citation_coverage=citation_coverage,
            overall_confidence=overall,
        )

    def _estimate_generation_quality(self, answer: str) -> float:
        """
        Estimate generation quality using heuristics.

        Future improvement: Use LLM logprobs when available.

        Current signals:
        - Has structure (bullets, numbers)
        - Reasonable length (not too short/long)
        - Not overly repetitive

        Args:
            answer: Generated answer text

        Returns:
            Quality score (0.0-1.0)
        """
        # Check for common quality signals
        has_structure = any(marker in answer for marker in ['1.', '2.', '-', '*'])
        reasonable_length = 50 <= len(answer) <= 2000

        words = answer.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            not_too_repetitive = unique_ratio > 0.5
        else:
            not_too_repetitive = False

        score = 0.5  # Neutral baseline

        if has_structure:
            score += 0.15
        if reasonable_length:
            score += 0.15
        if not_too_repetitive:
            score += 0.2

        return min(score, 1.0)

    def _calculate_citation_coverage(
        self,
        answer: str,
        citations: List[str],
    ) -> float:
        """
        Calculate what percentage of answer is cited.

        Uses rough estimate based on citation count and average
        words per citation. Future improvement: Track exact coverage
        using citation spans.

        Args:
            answer: Generated answer text
            citations: List of citation strings

        Returns:
            Citation coverage (0.0-1.0)
        """
        if not citations:
            return 0.0

        # Rough estimate: Count citation markers
        citation_count = answer.count('[Source:')
        words_per_citation = 50  # Assume each citation covers ~50 words

        total_words = len(answer.split())
        cited_words = min(citation_count * words_per_citation, total_words)

        return cited_words / total_words if total_words > 0 else 0.0
