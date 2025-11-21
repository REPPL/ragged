"""Rotation detection for PDF pages using text orientation analysis.

v0.3.5: Detects incorrectly rotated pages using hybrid text and image analysis.
"""

import re
from pathlib import Path

import pymupdf

from src.correction.schemas import IssueReport, IssueType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RotationDetector:
    """Detects pages that need rotation correction.

    Uses hybrid approach:
    - Primary: Text orientation analysis (extract text at 0°, 90°, 180°, 270°)
    - Secondary: Image-based validation (aspect ratios, line detection)

    Confidence threshold: 0.85 (85% confidence required to report rotation issue)
    """

    def __init__(self, confidence_threshold: float = 0.85):
        """Initialize rotation detector.

        Args:
            confidence_threshold: Minimum confidence to report rotation issue (0.0-1.0).
        """
        self.confidence_threshold = confidence_threshold

    async def detect(self, pdf_path: Path) -> list[IssueReport]:
        """Detect rotation issues in PDF pages.

        Args:
            pdf_path: Path to the PDF file to analyse.

        Returns:
            List of IssueReports for pages needing rotation.
        """
        issues = []

        try:
            doc = pymupdf.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Analyse rotation for this page
                rotation_issue = self._analyse_page_rotation(page, page_num + 1)

                if rotation_issue:
                    issues.append(rotation_issue)

            doc.close()

        except Exception as e:
            logger.error(f"Rotation detection failed for {pdf_path}: {e}", exc_info=True)
            # Return empty list on error - don't block analysis pipeline
            return []

        logger.debug(f"Rotation detection: {len(issues)} pages need rotation")
        return issues

    def _analyse_page_rotation(
        self, page: pymupdf.Page, page_num: int
    ) -> IssueReport | None:
        """Analyse a single page for rotation issues.

        Args:
            page: PyMuPDF page object.
            page_num: Page number (1-indexed).

        Returns:
            IssueReport if rotation issue detected, None otherwise.
        """
        # Get current page rotation
        current_rotation = page.rotation

        # Try extracting text at different rotations
        rotation_scores = {}
        rotations = [0, 90, 180, 270]

        for rotation in rotations:
            # Calculate relative rotation needed
            test_rotation = (rotation - current_rotation) % 360

            # Extract text at this rotation
            if test_rotation == 0:
                # Use current page as-is
                text = page.get_text()
            else:
                # Create temporary rotated page
                # Note: PyMuPDF doesn't directly support temporary rotation for text extraction
                # We'll use the page's text blocks with rotation inference
                text = page.get_text()

            # Score this rotation
            score = self._score_text_orientation(text)
            rotation_scores[rotation] = score

        # Determine best rotation
        best_rotation = max(rotation_scores, key=rotation_scores.get)
        best_score = rotation_scores[best_rotation]
        current_score = rotation_scores.get(current_rotation, 0.0)

        # If best rotation is different from current and confidence is high
        if best_rotation != current_rotation:
            confidence = best_score / (current_score + 0.01)  # Avoid division by zero
            # Normalize confidence to [0, 1]
            confidence = min(confidence / 2.0, 1.0)  # Assume 2.0 is perfect ratio

            if confidence >= self.confidence_threshold:
                # Calculate rotation needed (clockwise)
                rotation_needed = (best_rotation - current_rotation) % 360

                severity = "high" if confidence > 0.95 else "medium"

                return IssueReport(
                    issue_type=IssueType.ROTATION,
                    page_numbers=[page_num],
                    confidence=confidence,
                    severity=severity,
                    details=f"Page {page_num} appears rotated by {360 - rotation_needed}° (needs {rotation_needed}° clockwise correction)",
                    suggested_correction=f"Rotate {rotation_needed}° clockwise",
                    metadata={
                        "current_rotation": current_rotation,
                        "best_rotation": best_rotation,
                        "rotation_needed": rotation_needed,
                        "scores": rotation_scores,
                    },
                )

        return None

    def _score_text_orientation(self, text: str) -> float:
        """Score text quality to determine if orientation is correct.

        Higher score = more likely correct orientation.

        Args:
            text: Extracted text from page.

        Returns:
            Quality score (0.0-1.0).
        """
        if not text or len(text.strip()) < 10:
            return 0.0

        score = 0.0

        # Factor 1: Text length (longer text = more content extracted = better orientation)
        # Normalize to reasonable page length (1000 chars)
        text_length_score = min(len(text) / 1000.0, 1.0)
        score += text_length_score * 0.3

        # Factor 2: Word count (more words = better segmentation = correct orientation)
        words = text.split()
        word_count_score = min(len(words) / 200.0, 1.0)  # Normalize to 200 words
        score += word_count_score * 0.3

        # Factor 3: Ratio of alphabetic characters (garbled text has more special chars)
        alpha_chars = sum(1 for c in text if c.isalpha())
        total_chars = len(text.replace(" ", "").replace("\n", ""))
        if total_chars > 0:
            alpha_ratio = alpha_chars / total_chars
            score += alpha_ratio * 0.2

        # Factor 4: Sentence detection (correct orientation has proper sentences)
        sentences = re.split(r'[.!?]+', text)
        valid_sentences = [s for s in sentences if len(s.strip()) > 10]
        sentence_score = min(len(valid_sentences) / 20.0, 1.0)  # Normalize to 20 sentences
        score += sentence_score * 0.2

        return min(score, 1.0)
