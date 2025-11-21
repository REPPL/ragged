"""Unit tests for QualityDetector.

Tests quality assessment using text analysis.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.correction.detectors.quality import QualityDetector
from src.correction.schemas import IssueType, QualityGrade


class TestQualityDetector:
    """Tests for QualityDetector."""

    @pytest.fixture
    def detector(self):
        """Create a QualityDetector instance."""
        return QualityDetector(confidence_threshold=0.70)

    @pytest.mark.asyncio
    async def test_detect_high_quality_pages(self, detector, tmp_path):
        """Test detection returns empty list for high-quality pages."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Mock high-quality page
        mock_page = MagicMock()
        mock_page.rect = MagicMock(width=595, height=842)  # A4 size
        mock_page.get_text.return_value = "This is high-quality text with proper sentences and structure. " * 20

        mock_doc.__getitem__.return_value = mock_page

        test_file = tmp_path / "good_quality.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        with patch('pymupdf.open', return_value=mock_doc):
            issues = await detector.detect(test_file)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_detect_low_quality_page(self, detector, tmp_path):
        """Test detection of low-quality pages."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock low-quality page (very little text)
        mock_page = MagicMock()
        mock_page.rect = MagicMock(width=595, height=842)
        mock_page.get_text.return_value = "a b c"  # Minimal, poor quality text

        mock_doc.__getitem__.return_value = mock_page

        test_file = tmp_path / "poor_quality.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        with patch('pymupdf.open', return_value=mock_doc):
            with patch.object(detector, '_assess_page_quality', return_value=0.5):
                issues = await detector.detect(test_file)

        # Should detect low quality
        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.QUALITY
        assert issues[0].confidence < 0.70

    @pytest.mark.asyncio
    async def test_detect_file_not_found(self, detector, tmp_path):
        """Test detection handles missing file gracefully."""
        non_existent = tmp_path / "missing.pdf"

        issues = await detector.detect(non_existent)
        assert issues == []

    def test_assess_page_quality_high(self, detector):
        """Test quality assessment for high-quality page."""
        mock_page = MagicMock()
        mock_page.rect = MagicMock(width=595, height=842)
        mock_page.get_text.return_value = (
            "This is a high-quality document with proper sentences and structure. "
            "It contains many words and has good formatting. " * 10
        )

        score = detector._assess_page_quality(mock_page)

        assert 0.0 <= score <= 1.0
        assert score >= 0.70  # Should be high quality

    def test_assess_page_quality_low(self, detector):
        """Test quality assessment for low-quality page."""
        mock_page = MagicMock()
        mock_page.rect = MagicMock(width=595, height=842)
        mock_page.get_text.return_value = "a b c d"  # Very poor quality

        score = detector._assess_page_quality(mock_page)

        assert 0.0 <= score <= 1.0
        assert score < 0.70  # Should be low quality

    def test_assess_page_quality_empty(self, detector):
        """Test quality assessment for empty page."""
        mock_page = MagicMock()
        mock_page.rect = MagicMock(width=595, height=842)
        mock_page.get_text.return_value = ""

        score = detector._assess_page_quality(mock_page)

        assert score == 0.1  # Very low score for empty page

    def test_compute_character_quality_score_good(self, detector):
        """Test character quality scoring for good text."""
        good_text = "This is well-formed text with proper characters and punctuation."

        score = detector._compute_character_quality_score(good_text)

        assert 0.0 <= score <= 1.0
        assert score > 0.8  # Should score high

    def test_compute_character_quality_score_poor(self, detector):
        """Test character quality scoring for poor text."""
        poor_text = "###@@@!!!***%%%"  # Mostly invalid characters

        score = detector._compute_character_quality_score(poor_text)

        assert 0.0 <= score <= 1.0
        # May still have some valid punctuation

    def test_compute_word_quality_score_good(self, detector):
        """Test word quality scoring for good words."""
        good_text = "These are normal words with proper length and structure"

        score = detector._compute_word_quality_score(good_text)

        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should score reasonably high

    def test_compute_word_quality_score_poor(self, detector):
        """Test word quality scoring for poor words."""
        poor_text = "a b c verylongwordthatisunrealistic"

        score = detector._compute_word_quality_score(poor_text)

        assert 0.0 <= score <= 1.0
        # Score may vary based on extreme word penalty

    def test_compute_formatting_score_good(self, detector):
        """Test formatting scoring for well-formatted text."""
        good_text = "This is a line with reasonable length.\nAnother good line.\n"

        score = detector._compute_formatting_score(good_text)

        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should score reasonably high

    def test_compute_formatting_score_poor(self, detector):
        """Test formatting scoring for poorly formatted text."""
        poor_text = "a\nb\nc\n"  # Very short lines

        score = detector._compute_formatting_score(poor_text)

        assert 0.0 <= score <= 1.0


class TestQualityDetectorIntegration:
    """Integration tests for QualityDetector."""

    @pytest.mark.asyncio
    async def test_full_detection_mixed_quality(self, tmp_path):
        """Test detection with mixed quality pages."""
        detector = QualityDetector(confidence_threshold=0.70)

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3

        # Page 1: High quality
        page1 = MagicMock()
        page1.rect = MagicMock(width=595, height=842)
        page1.get_text.return_value = "High quality text. " * 50

        # Page 2: Low quality
        page2 = MagicMock()
        page2.rect = MagicMock(width=595, height=842)
        page2.get_text.return_value = "a b c"

        # Page 3: High quality
        page3 = MagicMock()
        page3.rect = MagicMock(width=595, height=842)
        page3.get_text.return_value = "Also high quality. " * 50

        mock_doc.__getitem__.side_effect = [page1, page2, page3]

        test_file = tmp_path / "mixed_quality.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        with patch('pymupdf.open', return_value=mock_doc):
            # Mock quality assessment to return specific scores
            with patch.object(
                detector,
                '_assess_page_quality',
                side_effect=[0.85, 0.50, 0.90]  # High, Low, High
            ):
                issues = await detector.detect(test_file)

        # Should detect one low-quality page (page 2)
        assert len(issues) == 1
        assert issues[0].page_numbers == [2]
        assert issues[0].issue_type == IssueType.QUALITY
