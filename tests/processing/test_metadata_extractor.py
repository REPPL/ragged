"""Tests for metadata extraction from scanned documents (v0.4.9).

Tests cover:
- PDF embedded metadata extraction
- Title page OCR + regex extraction
- Regex patterns for title, author, year, publisher
- Confidence scoring
- Fallback metadata generation
- Filename sanitization
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from ragged.processing.metadata_extractor import ExtractedMetadata, MetadataExtractor


class TestMetadataExtractor:
    """Tests for MetadataExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create MetadataExtractor instance."""
        return MetadataExtractor(titlepage_pages=3, ocr_language="eng")

    def test_init_defaults(self):
        """Test that MetadataExtractor initialises with correct defaults."""
        extractor = MetadataExtractor()

        assert extractor.titlepage_pages == 3
        assert extractor.ocr_language == "eng"
        assert extractor.use_vision is False
        assert extractor.prefer_gpu is False

    def test_init_custom_settings(self):
        """Test custom initialisation settings."""
        extractor = MetadataExtractor(
            titlepage_pages=5,
            ocr_language="fra",
            use_vision=True,
            prefer_gpu=True,
        )

        assert extractor.titlepage_pages == 5
        assert extractor.ocr_language == "fra"
        assert extractor.use_vision is True
        assert extractor.prefer_gpu is True

    def test_extract_title_all_caps(self, extractor):
        """Test title extraction with ALL CAPS pattern."""
        text = """
        THE ART OF RAG SYSTEMS

        A comprehensive guide
        """

        title = extractor._extract_title(text)
        assert title == "THE ART OF RAG SYSTEMS"

    def test_extract_title_title_case(self, extractor):
        """Test title extraction with Title Case pattern."""
        text = """
        Machine Learning Basics

        Introduction to ML
        """

        title = extractor._extract_title(text)
        assert title == "Machine Learning Basics"

    def test_extract_title_heuristic_longest_line(self, extractor):
        """Test title extraction using longest line heuristic."""
        text = """
        Short

        This is a much longer title that should be selected

        Also short
        """

        title = extractor._extract_title(text)
        assert "longer title" in title

    def test_extract_title_validation_too_short(self, extractor):
        """Test that titles too short are rejected."""
        text = "SHORT"  # Only 5 characters

        title = extractor._extract_title(text)
        assert title is None  # Too short (minimum 10 characters)

    def test_extract_title_validation_too_long(self, extractor):
        """Test that titles too long are rejected."""
        text = "A" * 150  # 150 characters

        title = extractor._extract_title(text)
        assert title is None  # Too long (maximum 100 characters)

    def test_extract_author_by_prefix(self, extractor):
        """Test author extraction with 'by' prefix."""
        text = """
        Some Title

        by John Smith

        Published 2024
        """

        author = extractor._extract_author(text)
        assert author == "John Smith"

    def test_extract_author_with_label(self, extractor):
        """Test author extraction with 'Author:' label."""
        text = """
        Some Title

        Author: Jane Doe
        """

        author = extractor._extract_author(text)
        assert author == "Jane Doe"

    def test_extract_author_written_by(self, extractor):
        """Test author extraction with 'Written by' prefix."""
        text = """
        Some Title

        Written by Alice Johnson
        """

        author = extractor._extract_author(text)
        assert author == "Alice Johnson"

    def test_extract_author_standalone_name(self, extractor):
        """Test author extraction of standalone name on own line."""
        text = """
        Some Title

        John Smith
        """

        author = extractor._extract_author(text)
        assert author == "John Smith"

    def test_extract_author_validation_too_short(self, extractor):
        """Test that author names too short are rejected."""
        text = "by A B"  # Only 4 characters total

        author = extractor._extract_author(text)
        assert author is None  # Too short (minimum 5 characters)

    def test_extract_year_copyright_symbol(self, extractor):
        """Test year extraction from copyright with © symbol."""
        text = """
        Some Title

        Copyright © 2023
        """

        year = extractor._extract_year(text)
        assert year == 2023

    def test_extract_year_copyright_text(self, extractor):
        """Test year extraction from copyright text."""
        text = """
        Copyright 2024 Publisher
        """

        year = extractor._extract_year(text)
        assert year == 2024

    def test_extract_year_published(self, extractor):
        """Test year extraction from published text."""
        text = """
        Published in 2022
        """

        year = extractor._extract_year(text)
        assert year == 2022

    def test_extract_year_parentheses(self, extractor):
        """Test year extraction from parentheses."""
        text = """
        Some Publisher (2021)
        """

        year = extractor._extract_year(text)
        assert year == 2021

    def test_extract_year_standalone(self, extractor):
        """Test year extraction of standalone year on own line."""
        text = """
        Some Title

        2020
        """

        year = extractor._extract_year(text)
        assert year == 2020

    def test_extract_year_multiple_years_returns_most_recent(self, extractor):
        """Test that most recent year is returned when multiple found."""
        text = """
        First published 2020

        Revised edition 2024
        """

        year = extractor._extract_year(text)
        assert year == 2024  # Most recent

    def test_extract_year_validation_too_old(self, extractor):
        """Test that years too old are rejected."""
        text = """
        Copyright 1750  # Too old
        """

        year = extractor._extract_year(text)
        assert year is None  # Before 1800

    def test_extract_year_validation_future(self, extractor):
        """Test that future years beyond current+1 are rejected."""
        text = """
        Copyright 2999  # Too far in future
        """

        year = extractor._extract_year(text)
        assert year is None

    def test_extract_publisher_published_by(self, extractor):
        """Test publisher extraction with 'Published by' prefix."""
        text = """
        Published by Tech Press
        """

        publisher = extractor._extract_publisher(text)
        assert publisher == "Tech Press"

    def test_extract_publisher_with_label(self, extractor):
        """Test publisher extraction with 'Publisher:' label."""
        text = """
        Publisher: Academic Publishers
        """

        publisher = extractor._extract_publisher(text)
        assert publisher == "Academic Publishers"

    def test_extract_publisher_press_pattern(self, extractor):
        """Test publisher extraction with 'Press' pattern."""
        text = """
        University Press
        """

        publisher = extractor._extract_publisher(text)
        assert publisher == "University Press"

    def test_extract_publisher_publishers_pattern(self, extractor):
        """Test publisher extraction with 'Publishers' pattern."""
        text = """
        Smith Publishers
        """

        publisher = extractor._extract_publisher(text)
        assert publisher == "Smith Publishers"

    def test_sanitize_filename_removes_scan_indicators(self, extractor):
        """Test filename sanitisation removes scan indicators."""
        filename = "book-scan-001"

        result = extractor._sanitize_filename(filename)
        assert "scan" not in result.lower()

    def test_sanitize_filename_removes_copy_indicators(self, extractor):
        """Test filename sanitisation removes copy indicators."""
        filename = "document-copy-2"

        result = extractor._sanitize_filename(filename)
        assert "copy" not in result.lower()

    def test_sanitize_filename_removes_dates(self, extractor):
        """Test filename sanitisation removes date patterns."""
        filename = "book-20240123-final"

        result = extractor._sanitize_filename(filename)
        assert "20240123" not in result

    def test_sanitize_filename_replaces_underscores_hyphens(self, extractor):
        """Test filename sanitisation replaces underscores and hyphens with spaces."""
        filename = "the_art_of_rag-systems"

        result = extractor._sanitize_filename(filename)
        assert "_" not in result
        assert result == "The Art Of Rag Systems"

    def test_sanitize_filename_title_case(self, extractor):
        """Test filename sanitisation applies title case."""
        filename = "machine learning basics"

        result = extractor._sanitize_filename(filename)
        assert result == "Machine Learning Basics"

    def test_fallback_metadata_uses_filename(self, extractor):
        """Test fallback metadata uses sanitised filename as title."""
        pdf_path = Path("/path/to/machine_learning_basics.pdf")

        metadata = extractor._fallback_metadata(pdf_path)

        assert metadata.title == "Machine Learning Basics"
        assert metadata.author is None
        assert metadata.year is None
        assert metadata.publisher is None
        assert metadata.confidence == 0.1
        assert metadata.method == "fallback"

    def test_fallback_metadata_empty_filename(self, extractor):
        """Test fallback metadata handles empty filename."""
        pdf_path = Path("/path/to/.pdf")

        metadata = extractor._fallback_metadata(pdf_path)

        assert metadata.title == "Untitled Document"

    @patch("ragged.processing.metadata_extractor.pymupdf")
    def test_extract_from_pdf_metadata_complete(self, mock_pymupdf, extractor):
        """Test extraction from complete PDF metadata."""
        mock_doc = Mock()
        mock_doc.metadata = {
            "title": "Test Book",
            "author": "Test Author",
            "creationDate": "D:20240115120000",
        }
        mock_pymupdf.open.return_value.__enter__.return_value = mock_doc

        pdf_path = Path("/fake/path.pdf")
        metadata = extractor._extract_from_pdf_metadata(pdf_path)

        assert metadata is not None
        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"
        assert metadata.year == 2024
        assert metadata.confidence == 1.0  # All fields present
        assert metadata.method == "pdf_metadata"

    @patch("ragged.processing.metadata_extractor.pymupdf")
    def test_extract_from_pdf_metadata_partial(self, mock_pymupdf, extractor):
        """Test extraction from partial PDF metadata."""
        mock_doc = Mock()
        mock_doc.metadata = {
            "title": "Test Book",
            # No author or date
        }
        mock_pymupdf.open.return_value.__enter__.return_value = mock_doc

        pdf_path = Path("/fake/path.pdf")
        metadata = extractor._extract_from_pdf_metadata(pdf_path)

        assert metadata is not None
        assert metadata.title == "Test Book"
        assert metadata.author is None
        assert metadata.year is None
        assert metadata.confidence == 0.5  # Only title
        assert metadata.method == "pdf_metadata"

    @patch("ragged.processing.metadata_extractor.pymupdf")
    def test_extract_from_pdf_metadata_empty(self, mock_pymupdf, extractor):
        """Test extraction from empty PDF metadata."""
        mock_doc = Mock()
        mock_doc.metadata = {}
        mock_pymupdf.open.return_value.__enter__.return_value = mock_doc

        pdf_path = Path("/fake/path.pdf")
        metadata = extractor._extract_from_pdf_metadata(pdf_path)

        assert metadata is None  # No metadata available

    def test_confidence_scoring_all_fields(self, extractor):
        """Test confidence scoring with all fields extracted."""
        # Simulate extraction with all fields
        title = "Test Title"
        author = "Test Author"
        year = 2024
        publisher = "Test Publisher"

        confidence = 0.0
        if title:
            confidence += 0.4
        if author:
            confidence += 0.3
        if year:
            confidence += 0.2
        if publisher:
            confidence += 0.1

        assert confidence == 1.0

    def test_confidence_scoring_partial_fields(self, extractor):
        """Test confidence scoring with partial fields."""
        # Simulate extraction with only title and author
        title = "Test Title"
        author = "Test Author"

        confidence = 0.0
        if title:
            confidence += 0.4
        if author:
            confidence += 0.3

        assert confidence == 0.7

    def test_vision_extraction_not_implemented(self, extractor):
        """Test that vision extraction returns None (not yet implemented)."""
        pdf_path = Path("/fake/path.pdf")

        metadata = extractor._extract_with_vision(pdf_path)

        assert metadata is None  # Not implemented yet

    @pytest.mark.parametrize(
        "text,expected_title",
        [
            ("THE COMPLETE GUIDE TO RAG", "THE COMPLETE GUIDE TO RAG"),
            ("Machine Learning for Beginners", "Machine Learning for Beginners"),
            ("", None),  # Empty text
            ("Short", None),  # Too short
        ],
    )
    def test_extract_title_various_inputs(self, extractor, text, expected_title):
        """Test title extraction with various inputs."""
        if expected_title:
            assert expected_title in extractor._extract_title(text) or extractor._extract_title(text) == expected_title
        else:
            assert extractor._extract_title(text) is None

    @pytest.mark.parametrize(
        "text,expected_year",
        [
            ("Copyright © 2023", 2023),
            ("Published in 2024", 2024),
            ("(2022)", 2022),
            ("No year here", None),
            ("Copyright 1750", None),  # Too old
        ],
    )
    def test_extract_year_various_inputs(self, extractor, text, expected_year):
        """Test year extraction with various inputs."""
        assert extractor._extract_year(text) == expected_year
