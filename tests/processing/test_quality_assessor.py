"""
Tests for quality assessment module.

Tests cover:
- Born-digital detection
- Image quality metrics
- Layout complexity analysis
- Per-page assessment
- Overall aggregation
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.processing.quality_assessor import (
    PageQuality,
    QualityAssessment,
    QualityAssessor,
)


@pytest.fixture
def mock_pymupdf():
    """Mock PyMuPDF for testing."""
    with patch("src.processing.quality_assessor.QualityAssessor._pymupdf") as mock:
        yield mock


@pytest.fixture
def mock_cv2():
    """Mock OpenCV for testing."""
    with patch("src.processing.quality_assessor.QualityAssessor._cv2") as mock_cv2, \
         patch("src.processing.quality_assessor.QualityAssessor._np") as mock_np:
        import numpy as np
        # Use real numpy for calculations
        mock_np.frombuffer = np.frombuffer
        mock_np.uint8 = np.uint8
        mock_np.std = np.std
        yield mock_cv2, mock_np


@pytest.fixture
def assessor():
    """Create quality assessor instance."""
    return QualityAssessor(fast_mode=True, cache_enabled=False)


@pytest.fixture
def mock_pdf_page():
    """Create mock PDF page."""
    page = Mock()
    page.number = 0
    page.rect = Mock(width=600, height=800)
    page.rect.width = 600
    page.rect.height = 800
    return page


class TestPageQuality:
    """Test PageQuality dataclass."""

    def test_overall_score_born_digital(self):
        """Test overall score calculation for born-digital page."""
        page = PageQuality(
            page_number=1,
            is_born_digital=True,
            text_quality=0.9,
            layout_complexity=0.3,
        )

        # Born-digital: 0.7 * text + 0.3 * (1 - 0.5*layout)
        expected = 0.7 * 0.9 + 0.3 * (1.0 - 0.5 * 0.3)
        assert abs(page.overall_score - expected) < 0.01

    def test_overall_score_scanned(self):
        """Test overall score calculation for scanned page."""
        page = PageQuality(
            page_number=1,
            is_scanned=True,
            text_quality=0.8,
            image_quality=0.7,
        )

        # Scanned: 0.5 * image + 0.5 * text
        expected = 0.5 * 0.7 + 0.5 * 0.8
        assert abs(page.overall_score - expected) < 0.01


class TestQualityAssessor:
    """Test QualityAssessor class."""

    def test_init(self):
        """Test assessor initialisation."""
        assessor = QualityAssessor(
            fast_mode=True,
            cache_enabled=True,
            max_pages_to_analyze=5,
        )

        assert assessor.fast_mode is True
        assert assessor.cache_enabled is True
        assert assessor.max_pages_to_analyze == 5

    def test_cache_key(self, assessor, tmp_path):
        """Test cache key generation."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        key1 = assessor._cache_key(test_file)
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash

        # Same file should have same key
        key2 = assessor._cache_key(test_file)
        assert key1 == key2

        # Different file should have different key
        test_file2 = tmp_path / "test2.pdf"
        test_file2.write_text("test2")
        key3 = assessor._cache_key(test_file2)
        assert key1 != key3

    def test_assess_nonexistent_file(self, assessor):
        """Test assessment of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            assessor.assess(Path("/nonexistent/file.pdf"))

    def test_assess_non_pdf(self, assessor, tmp_path):
        """Test assessment of non-PDF file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test")

        with pytest.raises(ValueError, match="Only PDF files supported"):
            assessor.assess(txt_file)

    def test_is_born_digital_true(self, assessor, mock_pdf_page):
        """Test born-digital detection for digital PDF."""
        # Mock born-digital indicators
        mock_pdf_page.get_fonts.return_value = [("Font1",)]  # Has fonts
        mock_pdf_page.get_text.return_value = "A" * 100  # Has text
        mock_pdf_page.get_images.return_value = []  # No images

        result = assessor._is_born_digital(mock_pdf_page)
        assert result is True

    def test_is_born_digital_false_scanned(self, assessor, mock_pdf_page):
        """Test born-digital detection for scanned PDF."""
        # Mock scanned indicators
        mock_pdf_page.get_fonts.return_value = []  # No fonts
        mock_pdf_page.get_text.return_value = "A" * 100  # Has text (OCR)

        # Mock full-page image
        img_rect = Mock(width=590, height=790)
        mock_pdf_page.get_images.return_value = [(1,)]
        mock_pdf_page.get_image_rects.return_value = [img_rect]

        result = assessor._is_born_digital(mock_pdf_page)
        assert result is False

    def test_assess_text_quality_born_digital(self, assessor, mock_pdf_page):
        """Test text quality assessment for born-digital page."""
        mock_pdf_page.get_text = Mock(side_effect=[
            "A" * 1000,  # First call returns text
            [{"text": "block"}],  # Second call returns blocks
        ])

        quality = assessor._assess_text_quality(mock_pdf_page, is_born_digital=True)
        assert quality >= 0.8  # High quality for born-digital

    def test_assess_text_quality_scanned(self, assessor, mock_pdf_page):
        """Test text quality assessment for scanned page."""
        # Good extraction
        mock_pdf_page.get_text.return_value = "A" * 1500
        quality = assessor._assess_text_quality(mock_pdf_page, is_born_digital=False)
        assert quality >= 0.8

        # Poor extraction
        mock_pdf_page.get_text.return_value = "A" * 50
        quality = assessor._assess_text_quality(mock_pdf_page, is_born_digital=False)
        assert quality < 0.7

    def test_assess_layout_complexity(self, assessor, mock_pdf_page):
        """Test layout complexity assessment."""
        # Simple layout: few blocks, no images
        blocks = [(10, 10, 100, 50, "text") for _ in range(3)]
        mock_pdf_page.get_text.return_value = blocks
        mock_pdf_page.get_images.return_value = []

        complexity = assessor._assess_layout_complexity(mock_pdf_page)
        assert 0.0 <= complexity <= 1.0
        assert complexity < 0.5  # Simple layout

        # Complex layout: many blocks, images
        blocks = [(i * 50, 10, i * 50 + 100, 50, "text") for i in range(20)]
        mock_pdf_page.get_text.return_value = blocks
        mock_pdf_page.get_images.return_value = [(1,), (2,), (3,)]

        complexity = assessor._assess_layout_complexity(mock_pdf_page)
        assert complexity > 0.5  # Complex layout

    def test_detect_tables(self, assessor, mock_pdf_page):
        """Test table detection."""
        # No tables
        mock_pdf_page.get_text.return_value = {"blocks": []}
        assert assessor._detect_tables(mock_pdf_page) is False

        # With table-like structure
        mock_pdf_page.get_text.return_value = {
            "blocks": [
                {
                    "lines": [{"text": "row1"}, {"text": "row2"}, {"text": "row3"}]
                }
            ]
        }
        assert assessor._detect_tables(mock_pdf_page) is True

    def test_detect_rotated_content(self, assessor, mock_pdf_page):
        """Test rotated content detection."""
        # No rotation
        mock_pdf_page.get_text.return_value = {
            "blocks": [
                {"lines": [{"dir": (1, 0)}]}
            ]
        }
        assert assessor._detect_rotated_content(mock_pdf_page) is False

        # With rotation
        mock_pdf_page.get_text.return_value = {
            "blocks": [
                {"lines": [{"dir": (0, 1)}]}  # Rotated
            ]
        }
        assert assessor._detect_rotated_content(mock_pdf_page) is True

    def test_aggregate_assessment_born_digital(self, assessor, tmp_path):
        """Test aggregation for born-digital document."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        page_scores = [
            PageQuality(
                page_number=1,
                is_born_digital=True,
                text_quality=0.9,
                layout_complexity=0.3,
            ),
            PageQuality(
                page_number=2,
                is_born_digital=True,
                text_quality=0.95,
                layout_complexity=0.2,
            ),
        ]

        assessment = assessor._aggregate_assessment(page_scores, 2, test_file)

        assert assessment.is_born_digital is True
        assert assessment.is_scanned is False
        assert 0.85 <= assessment.text_quality <= 1.0
        assert assessment.recommended_processor == "docling"

    def test_aggregate_assessment_scanned(self, assessor, tmp_path):
        """Test aggregation for scanned document."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        page_scores = [
            PageQuality(
                page_number=1,
                is_scanned=True,
                text_quality=0.7,
                image_quality=0.8,
            ),
        ]

        assessment = assessor._aggregate_assessment(page_scores, 1, test_file)

        assert assessment.is_scanned is True
        assert assessment.image_quality > 0.0

    def test_fallback_assessment(self, assessor, tmp_path):
        """Test fallback assessment on error."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        assessment = assessor._fallback_assessment(test_file, "Test error")

        assert assessment.overall_score == 0.7  # Conservative
        assert assessment.is_scanned is True  # Assume scanned
        assert assessment.confidence == 0.5  # Low confidence
        assert "Test error" in assessment.metadata["error"]

    def test_cache_functionality(self, tmp_path):
        """Test quality assessment caching."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        assessor = QualityAssessor(fast_mode=True, cache_enabled=True)

        # First call should assess
        with patch.object(assessor, "_assess_pdf") as mock_assess:
            mock_assess.return_value = QualityAssessment(
                overall_score=0.8,
                is_born_digital=True,
                is_scanned=False,
                text_quality=0.9,
                layout_complexity=0.3,
                image_quality=0.0,
                has_tables=False,
                has_rotated_content=False,
            )

            result1 = assessor.assess(test_file)
            assert mock_assess.call_count == 1

            # Second call should use cache
            result2 = assessor.assess(test_file)
            assert mock_assess.call_count == 1  # Not called again

            # Results should be identical
            assert result1.overall_score == result2.overall_score

    def test_clear_cache(self):
        """Test cache clearing."""
        assessor = QualityAssessor(cache_enabled=True)
        assessor._cache["test"] = Mock()

        assessor.clear_cache()
        assert len(assessor._cache) == 0


class TestIntegration:
    """Integration tests for quality assessment."""

    def test_full_assessment_workflow(self, tmp_path):
        """Test complete assessment workflow."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        # Mock PyMuPDF
        import fitz
        with patch("fitz.open") as mock_open:
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__len__.return_value = 2  # 2 pages

            # Mock page 1
            page1 = Mock()
            page1.number = 0
            page1.get_fonts.return_value = [("Font1",)]
            page1.get_text = Mock(side_effect=["A" * 1000, {"blocks": []}])
            page1.get_images.return_value = []
            page1.rect = Mock(width=600, height=800)

            # Mock page 2
            page2 = Mock()
            page2.number = 1
            page2.get_fonts.return_value = [("Font1",)]
            page2.get_text = Mock(side_effect=["B" * 1000, {"blocks": []}])
            page2.get_images.return_value = []
            page2.rect = Mock(width=600, height=800)

            mock_doc.__getitem__.side_effect = [page1, page2]
            mock_doc.close = Mock()
            mock_open.return_value = mock_doc

            # Run assessment
            assessor = QualityAssessor(fast_mode=False, cache_enabled=False)

            assessment = assessor.assess(test_file)

            # Verify result
            assert isinstance(assessment, QualityAssessment)
            assert 0.0 <= assessment.overall_score <= 1.0
            assert len(assessment.page_scores) == 2
            assert assessment.metadata["total_pages"] == 2
            assert assessment.metadata["pages_analysed"] == 2
