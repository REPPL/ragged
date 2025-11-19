"""Tests for confidence scoring module."""

import pytest
from unittest.mock import Mock

from src.generation.confidence import ConfidenceCalculator, ConfidenceScore


class TestConfidenceScore:
    """Tests for ConfidenceScore dataclass."""

    def test_to_str_very_high(self) -> None:
        """Test verbal description for very high confidence."""
        score = ConfidenceScore(
            retrieval_score=0.95,
            generation_score=0.92,
            citation_coverage=0.95,
            overall_confidence=0.94,
        )
        assert score.to_str() == "Very High"

    def test_to_str_high(self) -> None:
        """Test verbal description for high confidence."""
        score = ConfidenceScore(
            retrieval_score=0.80,
            generation_score=0.75,
            citation_coverage=0.78,
            overall_confidence=0.78,
        )
        assert score.to_str() == "High"

    def test_to_str_medium(self) -> None:
        """Test verbal description for medium confidence."""
        score = ConfidenceScore(
            retrieval_score=0.65,
            generation_score=0.60,
            citation_coverage=0.62,
            overall_confidence=0.62,
        )
        assert score.to_str() == "Medium"

    def test_to_str_low(self) -> None:
        """Test verbal description for low confidence."""
        score = ConfidenceScore(
            retrieval_score=0.45,
            generation_score=0.42,
            citation_coverage=0.40,
            overall_confidence=0.42,
        )
        assert score.to_str() == "Low"

    def test_to_str_very_low(self) -> None:
        """Test verbal description for very low confidence."""
        score = ConfidenceScore(
            retrieval_score=0.20,
            generation_score=0.15,
            citation_coverage=0.10,
            overall_confidence=0.15,
        )
        assert score.to_str() == "Very Low"

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        score = ConfidenceScore(
            retrieval_score=0.80,
            generation_score=0.75,
            citation_coverage=0.70,
            overall_confidence=0.76,
        )

        result_dict = score.to_dict()

        assert result_dict["retrieval_score"] == 0.80
        assert result_dict["generation_score"] == 0.75
        assert result_dict["citation_coverage"] == 0.70
        assert result_dict["overall_confidence"] == 0.76
        assert result_dict["level"] == "High"


class TestConfidenceCalculator:
    """Tests for ConfidenceCalculator class."""

    def test_initialisation_default_weights(self) -> None:
        """Test calculator initialisation with default weights."""
        calculator = ConfidenceCalculator()

        assert calculator.retrieval_weight == 0.4
        assert calculator.generation_weight == 0.3
        assert calculator.citation_weight == 0.3

    def test_initialisation_custom_weights(self) -> None:
        """Test calculator initialisation with custom weights."""
        calculator = ConfidenceCalculator(
            retrieval_weight=0.5,
            generation_weight=0.3,
            citation_weight=0.2,
        )

        assert calculator.retrieval_weight == 0.5
        assert calculator.generation_weight == 0.3
        assert calculator.citation_weight == 0.2

    def test_initialisation_invalid_weights(self) -> None:
        """Test validation of weights sum."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            ConfidenceCalculator(
                retrieval_weight=0.5,
                generation_weight=0.5,
                citation_weight=0.5,  # Sum > 1.0
            )

    def test_calculate_with_chunks(self) -> None:
        """Test confidence calculation with retrieved chunks."""
        # Mock chunks with scores
        chunk1 = Mock()
        chunk1.score = 0.85
        chunk2 = Mock()
        chunk2.score = 0.75
        chunk3 = Mock()
        chunk3.score = 0.65

        chunks = [chunk1, chunk2, chunk3]
        # Answer with citation markers
        answer = "This is a well-structured answer [Source: doc1.pdf] with multiple points. 1. First point. 2. Second point [Source: doc2.pdf]."
        citations = ["[Source: doc1.pdf]", "[Source: doc2.pdf]"]

        calculator = ConfidenceCalculator()
        confidence = calculator.calculate(
            retrieved_chunks=chunks,
            answer=answer,
            citations=citations,
        )

        # Retrieval score should be average: (0.85 + 0.75 + 0.65) / 3 = 0.75
        assert confidence.retrieval_score == 0.75
        # Overall should be weighted average
        assert 0 <= confidence.overall_confidence <= 1.0
        assert confidence.generation_score > 0
        assert confidence.citation_coverage > 0

    def test_calculate_no_chunks(self) -> None:
        """Test confidence calculation with no retrieved chunks."""
        answer = "This is an answer without retrieval."
        citations = []

        calculator = ConfidenceCalculator()
        confidence = calculator.calculate(
            retrieved_chunks=[],
            answer=answer,
            citations=citations,
        )

        assert confidence.retrieval_score == 0.0
        assert confidence.citation_coverage == 0.0
        # Generation score should still be calculated
        assert confidence.generation_score > 0

    def test_calculate_chunks_without_score_attribute(self) -> None:
        """Test handling chunks without score attribute."""
        chunk = Mock(spec=[])  # No score attribute
        chunks = [chunk]
        answer = "Test answer"
        citations = []

        calculator = ConfidenceCalculator()
        confidence = calculator.calculate(
            retrieved_chunks=chunks,
            answer=answer,
            citations=citations,
        )

        # Should default to 0.0 when chunks don't have scores
        assert confidence.retrieval_score == 0.0

    def test_estimate_generation_quality_good_answer(self) -> None:
        """Test generation quality estimation for good answer."""
        calculator = ConfidenceCalculator()

        # Good answer: structured, reasonable length, not repetitive
        answer = (
            "Here's a comprehensive answer:\n"
            "1. First key point about the topic\n"
            "2. Second important aspect to consider\n"
            "3. Third relevant detail\n"
            "This covers the main aspects comprehensively."
        )

        quality = calculator._estimate_generation_quality(answer)

        # Should score high: has structure, reasonable length, diverse vocabulary
        assert quality >= 0.8

    def test_estimate_generation_quality_poor_answer(self) -> None:
        """Test generation quality estimation for poor answer."""
        calculator = ConfidenceCalculator()

        # Poor answer: too short, no structure, repetitive
        answer = "short short short"

        quality = calculator._estimate_generation_quality(answer)

        # Should score low
        assert quality < 0.7

    def test_estimate_generation_quality_too_long(self) -> None:
        """Test generation quality for overly long answer."""
        calculator = ConfidenceCalculator()

        # Very long answer (over 2000 chars)
        answer = "word " * 500  # Creates ~2500 char string

        quality = calculator._estimate_generation_quality(answer)

        # Should lose points for unreasonable length
        assert quality < 0.8

    def test_calculate_citation_coverage_no_citations(self) -> None:
        """Test citation coverage with no citations."""
        calculator = ConfidenceCalculator()

        answer = "This answer has no citations at all."
        citations = []

        coverage = calculator._calculate_citation_coverage(answer, citations)

        assert coverage == 0.0

    def test_calculate_citation_coverage_with_citations(self) -> None:
        """Test citation coverage with citations."""
        calculator = ConfidenceCalculator()

        answer = (
            "This point is cited [Source: doc1.pdf]. "
            "Another point [Source: doc2.pdf]. "
            "And a third point [Source: doc3.pdf]."
        )
        citations = ["[Source: doc1.pdf]", "[Source: doc2.pdf]", "[Source: doc3.pdf]"]

        coverage = calculator._calculate_citation_coverage(answer, citations)

        # 3 citations * 50 words = 150 words cited
        # Answer has ~15 words, so coverage capped at 100%
        assert coverage == 1.0

    def test_calculate_citation_coverage_partial(self) -> None:
        """Test citation coverage with partial citing."""
        calculator = ConfidenceCalculator()

        # Long answer with only one citation
        answer = " ".join(["word"] * 100) + " [Source: doc.pdf]"
        citations = ["[Source: doc.pdf]"]

        coverage = calculator._calculate_citation_coverage(answer, citations)

        # 1 citation * 50 = 50 words cited out of 101 total
        assert 0.4 < coverage < 0.6

    def test_calculate_citation_coverage_empty_answer(self) -> None:
        """Test citation coverage with empty answer."""
        calculator = ConfidenceCalculator()

        answer = ""
        citations = []

        coverage = calculator._calculate_citation_coverage(answer, citations)

        assert coverage == 0.0

    def test_overall_confidence_calculation(self) -> None:
        """Test overall confidence is weighted average."""
        chunk = Mock()
        chunk.score = 0.8

        answer = "1. First point. 2. Second point."
        citations = ["[Source: doc.pdf]"]

        calculator = ConfidenceCalculator(
            retrieval_weight=0.5,
            generation_weight=0.3,
            citation_weight=0.2,
        )

        confidence = calculator.calculate(
            retrieved_chunks=[chunk],
            answer=answer,
            citations=citations,
        )

        # Verify it's a weighted average
        expected = (
            0.5 * confidence.retrieval_score +
            0.3 * confidence.generation_score +
            0.2 * confidence.citation_coverage
        )

        assert abs(confidence.overall_confidence - expected) < 0.001
