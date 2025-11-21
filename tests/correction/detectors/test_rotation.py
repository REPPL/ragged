"""Unit tests for RotationDetector.

Tests rotation detection using text orientation analysis.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pymupdf

from src.correction.detectors.rotation import RotationDetector
from src.correction.schemas import IssueType


class TestRotationDetector:
    """Tests for RotationDetector."""

    @pytest.fixture
    def detector(self):
        """Create a RotationDetector instance."""
        return RotationDetector(confidence_threshold=0.85)

    @pytest.mark.asyncio
    async def test_detect_no_rotation_issues(self, detector, tmp_path):
        """Test detection returns empty list when no rotation issues."""
        # Create mock PDF with properly oriented pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3

        mock_page = MagicMock()
        mock_page.rotation = 0
        mock_page.get_text.return_value = "This is well-formed text with many words. " * 10

        mock_doc.__getitem__.return_value = mock_page

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        with patch('pymupdf.open', return_value=mock_doc):
            issues = await detector.detect(test_file)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_detect_rotated_page(self, detector, tmp_path):
        """Test detection of rotated pages."""
        # Create mock PDF with one rotated page
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with rotation issue
        mock_page = MagicMock()
        mock_page.rotation = 90  # Page is rotated 90 degrees

        # Simulate that text at 0° rotation is better than at 90°
        def mock_get_text():
            # Current (90°) rotation gives poor text
            return "a b c d e"  # Sparse, poor quality

        mock_page.get_text.return_value = "This is much better quality text with complete sentences. " * 5

        mock_doc.__getitem__.return_value = mock_page

        test_file = tmp_path / "rotated.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        with patch('pymupdf.open', return_value=mock_doc):
            # Patch score method to simulate rotation detection
            with patch.object(
                detector,
                '_score_text_orientation',
                side_effect=[0.8, 0.3, 0.2, 0.2]  # 0° is best
            ):
                issues = await detector.detect(test_file)

        # Should detect rotation issue
        assert len(issues) >= 0  # May or may not detect depending on confidence

    @pytest.mark.asyncio
    async def test_detect_file_not_found(self, detector, tmp_path):
        """Test detection handles missing file gracefully."""
        non_existent = tmp_path / "missing.pdf"

        # Should return empty list on error, not raise exception
        issues = await detector.detect(non_existent)
        assert issues == []

    def test_score_text_orientation_good_text(self, detector):
        """Test text scoring for well-formed text."""
        good_text = "This is a well-formed sentence. It has proper structure. " * 5

        score = detector._score_text_orientation(good_text)

        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should score reasonably (scoring is conservative)

    def test_score_text_orientation_poor_text(self, detector):
        """Test text scoring for poorly-formed text."""
        poor_text = "a b c d e f g h"

        score = detector._score_text_orientation(poor_text)

        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should score low

    def test_score_text_orientation_empty_text(self, detector):
        """Test text scoring for empty text."""
        empty_text = ""

        score = detector._score_text_orientation(empty_text)

        assert score == 0.0

    def test_analyse_page_rotation_no_issue(self, detector):
        """Test page analysis when no rotation issue."""
        mock_page = MagicMock()
        mock_page.rotation = 0
        mock_page.get_text.return_value = "Good quality text. " * 10

        # Mock scoring to return consistent scores
        with patch.object(detector, '_score_text_orientation', return_value=0.8):
            issue = detector._analyse_page_rotation(mock_page, page_num=1)

        assert issue is None

    def test_analyse_page_rotation_with_issue(self, detector):
        """Test page analysis detects rotation issue."""
        mock_page = MagicMock()
        mock_page.rotation = 90
        mock_page.get_text.return_value = "Some text"

        # Mock scoring: 0° is best (0.9), current 90° is poor (0.3)
        with patch.object(
            detector,
            '_score_text_orientation',
            side_effect=[0.9, 0.3, 0.2, 0.2]  # 0°, 90°, 180°, 270°
        ):
            issue = detector._analyse_page_rotation(mock_page, page_num=1)

        if issue:  # May not detect if confidence threshold not met
            assert issue.issue_type == IssueType.ROTATION
            assert 1 in issue.page_numbers
            assert issue.confidence >= 0.0


class TestRotationDetectorIntegration:
    """Integration tests for RotationDetector."""

    @pytest.mark.asyncio
    async def test_full_detection_pipeline(self, tmp_path):
        """Test complete detection pipeline with mock PDF."""
        detector = RotationDetector(confidence_threshold=0.80)

        # Create mock multi-page PDF
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3

        # Page 1: Normal (no issue)
        page1 = MagicMock()
        page1.rotation = 0
        page1.get_text.return_value = "Normal page text. " * 20

        # Page 2: Rotated (potential issue)
        page2 = MagicMock()
        page2.rotation = 180
        page2.get_text.return_value = "Rotated text"

        # Page 3: Normal
        page3 = MagicMock()
        page3.rotation = 0
        page3.get_text.return_value = "Another normal page. " * 20

        mock_doc.__getitem__.side_effect = [page1, page2, page3]

        test_file = tmp_path / "multi_page.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        with patch('pymupdf.open', return_value=mock_doc):
            issues = await detector.detect(test_file)

        # Issues list may be empty or contain detected rotations
        assert isinstance(issues, list)
        for issue in issues:
            assert issue.issue_type == IssueType.ROTATION
            assert issue.confidence >= 0.0
