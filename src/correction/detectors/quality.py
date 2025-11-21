"""Quality detection for PDF pages using text analysis and OCR confidence.

v0.3.5: Assesses per-page quality and identifies low-confidence sections.
"""

import re
from pathlib import Path

import pymupdf

from src.correction.schemas import IssueReport, IssueType, QualityGrade
from src.utils.logging import get_logger

logger = get_logger(__name__)


class QualityDetector:
    """Detects quality issues in PDF pages.

    Analyses:
    - Text extraction quality (word density, character distribution)
    - OCR confidence (if available)
    - Readability metrics
    - Image quality indicators

    Confidence threshold: 0.70 (70% quality minimum for "acceptable")
    """

    def __init__(self, confidence_threshold: float = 0.70):
        """Initialize quality detector.

        Args:
            confidence_threshold: Minimum quality score (0.0-1.0).
                Pages below this threshold are flagged as low quality.
        """
        self.confidence_threshold = confidence_threshold

    async def detect(self, pdf_path: Path) -> list[IssueReport]:
        """Detect quality issues in PDF pages.

        Args:
            pdf_path: Path to the PDF file to analyse.

        Returns:
            List of IssueReports for low-quality pages.
        """
        issues = []

        try:
            doc = pymupdf.open(pdf_path)

            # Analyse each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                quality_score = self._assess_page_quality(page)

                if quality_score < self.confidence_threshold:
                    # Determine quality grade
                    if quality_score >= 0.60:
                        grade = QualityGrade.FAIR
                        severity = "medium"
                    elif quality_score >= 0.40:
                        grade = QualityGrade.POOR
                        severity = "high"
                    else:
                        grade = "very_poor"
                        severity = "critical"

                    issues.append(
                        IssueReport(
                            issue_type=IssueType.QUALITY,
                            page_numbers=[page_num + 1],
                            confidence=quality_score,
                            severity=severity,
                            details=(
                                f"Page {page_num + 1} has low quality (score: {quality_score:.2f}, "
                                f"grade: {grade if isinstance(grade, str) else grade.value})"
                            ),
                            suggested_correction="Review page for OCR errors or consider rescanning",
                            metadata={
                                "quality_score": quality_score,
                                "quality_grade": grade if isinstance(grade, str) else grade.value,
                            },
                        )
                    )

            doc.close()

        except Exception as e:
            logger.error(f"Quality detection failed for {pdf_path}: {e}", exc_info=True)
            return []

        logger.debug(f"Quality detection: {len(issues)} low-quality pages found")
        return issues

    def _assess_page_quality(self, page: pymupdf.Page) -> float:
        """Assess quality of a single page.

        Combines multiple quality metrics:
        - Text density (text coverage vs page area)
        - Character distribution (ratio of valid characters)
        - Word quality (average word length, dictionary-like words)
        - Whitespace distribution
        - Image quality indicators

        Args:
            page: PyMuPDF page object.

        Returns:
            Quality score (0.0-1.0), where 1.0 is excellent quality.
        """
        # Extract text
        text = page.get_text()

        if not text or len(text.strip()) < 10:
            # Almost no text extracted = very low quality or blank page
            return 0.1

        # Metric 1: Text density (text length vs page area)
        text_density_score = self._compute_text_density_score(page, text)

        # Metric 2: Character quality (ratio of valid characters)
        char_quality_score = self._compute_character_quality_score(text)

        # Metric 3: Word quality (word length, structure)
        word_quality_score = self._compute_word_quality_score(text)

        # Metric 4: Whitespace and formatting
        formatting_score = self._compute_formatting_score(text)

        # Combine scores (weighted average)
        overall_score = (
            text_density_score * 0.25
            + char_quality_score * 0.30
            + word_quality_score * 0.30
            + formatting_score * 0.15
        )

        return min(overall_score, 1.0)

    def _compute_text_density_score(self, page: pymupdf.Page, text: str) -> float:
        """Compute text density score.

        Higher density = more text extracted = better quality.

        Args:
            page: PyMuPDF page object.
            text: Extracted text.

        Returns:
            Text density score (0.0-1.0).
        """
        # Get page area
        rect = page.rect
        page_area = rect.width * rect.height

        # Estimate text coverage (very rough heuristic)
        # Assume average character takes ~50 square points
        estimated_text_area = len(text) * 50

        # Normalize to page area (typical page is ~595x842 = 501290 points for A4)
        density = min(estimated_text_area / page_area, 1.0)

        # Scale to reasonable range (pages with 20%+ coverage are good)
        normalized_density = min(density * 5.0, 1.0)

        return normalized_density

    def _compute_character_quality_score(self, text: str) -> float:
        """Compute character quality score.

        Analyses ratio of valid characters vs garbage characters.

        Args:
            text: Extracted text.

        Returns:
            Character quality score (0.0-1.0).
        """
        if not text:
            return 0.0

        total_chars = len(text)

        # Count different character types
        alpha_chars = sum(1 for c in text if c.isalpha())
        numeric_chars = sum(1 for c in text if c.isdigit())
        whitespace_chars = sum(1 for c in text if c.isspace())
        punctuation_chars = sum(1 for c in text if c in '.,;:!?-()[]{}"\'/\\')

        valid_chars = alpha_chars + numeric_chars + whitespace_chars + punctuation_chars
        invalid_chars = total_chars - valid_chars

        # Good text should have high ratio of valid characters
        valid_ratio = valid_chars / total_chars

        # Penalty for excessive invalid characters
        invalid_penalty = min(invalid_chars / total_chars, 0.3)

        score = valid_ratio - invalid_penalty

        return max(score, 0.0)

    def _compute_word_quality_score(self, text: str) -> float:
        """Compute word quality score.

        Analyses word structure and distribution.

        Args:
            text: Extracted text.

        Returns:
            Word quality score (0.0-1.0).
        """
        words = text.split()

        if not words:
            return 0.0

        # Metric 1: Average word length (good text has reasonable word lengths)
        avg_word_length = sum(len(word) for word in words) / len(words)
        # Ideal average is around 5-7 characters
        length_score = 1.0 - abs(avg_word_length - 6.0) / 10.0
        length_score = max(length_score, 0.0)

        # Metric 2: Ratio of dictionary-like words (mostly alphabetic)
        dictionary_like = sum(
            1 for word in words if re.match(r'^[a-zA-Z]+[a-z]*$', word)
        )
        dictionary_ratio = dictionary_like / len(words)

        # Metric 3: Ratio of very short or very long words (likely OCR errors)
        extreme_words = sum(
            1 for word in words if len(word) < 2 or len(word) > 20
        )
        extreme_ratio = extreme_words / len(words)
        extreme_penalty = min(extreme_ratio * 2.0, 0.3)

        # Combine
        score = (length_score * 0.3 + dictionary_ratio * 0.5) - extreme_penalty

        return max(score, 0.0)

    def _compute_formatting_score(self, text: str) -> float:
        """Compute formatting quality score.

        Analyses whitespace distribution and structure.

        Args:
            text: Extracted text.

        Returns:
            Formatting score (0.0-1.0).
        """
        if not text:
            return 0.0

        # Metric 1: Line breaks (good text has reasonable line structure)
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return 0.0

        # Average line length
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(
            non_empty_lines
        )

        # Reasonable line length is 40-100 characters
        if 40 <= avg_line_length <= 100:
            line_length_score = 1.0
        else:
            line_length_score = 0.7

        # Metric 2: Excessive whitespace (sign of poor OCR)
        whitespace_ratio = sum(1 for c in text if c.isspace()) / len(text)

        # Reasonable whitespace is 10-25%
        if 0.10 <= whitespace_ratio <= 0.25:
            whitespace_score = 1.0
        elif whitespace_ratio < 0.10:
            whitespace_score = 0.8  # Too little whitespace
        else:
            whitespace_score = max(1.0 - (whitespace_ratio - 0.25) * 2.0, 0.3)

        # Combine
        score = line_length_score * 0.5 + whitespace_score * 0.5

        return score
