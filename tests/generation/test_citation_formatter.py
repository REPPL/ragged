"""Tests for IEEE-style citation formatting."""

import pytest
from pathlib import Path
from src.generation.citation_formatter import (
    extract_citation_numbers,
    format_ieee_reference,
    format_reference_list,
    format_response_with_references,
)
from src.retrieval.retriever import RetrievedChunk


class TestExtractCitationNumbers:
    """Tests for extracting citation numbers from text."""

    def test_extract_single_citation(self):
        """Test extracting a single citation."""
        text = "Machine learning is a subset of AI [1]."

        citations = extract_citation_numbers(text)

        assert citations == [1]

    def test_extract_multiple_citations(self):
        """Test extracting multiple citations."""
        text = "ML is AI [1]. DL uses neural nets [2]. NLP processes text [3]."

        citations = extract_citation_numbers(text)

        assert citations == [1, 2, 3]

    def test_extract_unordered_citations(self):
        """Test that citations are returned sorted."""
        text = "Third [3], first [1], second [2]."

        citations = extract_citation_numbers(text)

        assert citations == [1, 2, 3]

    def test_extract_duplicate_citations(self):
        """Test that duplicate citations are deduplicated."""
        text = "First mention [1]. Second mention [1]. Third mention [1]."

        citations = extract_citation_numbers(text)

        assert citations == [1]

    def test_extract_no_citations(self):
        """Test extracting from text with no citations."""
        text = "This text has no citations."

        citations = extract_citation_numbers(text)

        assert citations == []

    def test_extract_mixed_numbers(self):
        """Test extraction with various numbers."""
        text = "Sources [1], [5], [10], [25], [100]."

        citations = extract_citation_numbers(text)

        assert citations == [1, 5, 10, 25, 100]

    def test_extract_multiline_text(self):
        """Test extraction from multiline text."""
        text = """First paragraph [1].

        Second paragraph [2].

        Third paragraph [3]."""

        citations = extract_citation_numbers(text)

        assert citations == [1, 2, 3]

    def test_extract_all_bracketed_numbers(self):
        """Test that all numbers in brackets are extracted."""
        text = "Array [0] and citation [1] and dict['key']."

        citations = extract_citation_numbers(text)

        # Extracts all [number] patterns - [0] and [1]
        # Note: dict['key'] is ignored as it's not a number
        assert citations == [0, 1]


class TestFormatIEEEReference:
    """Tests for formatting single IEEE references."""

    def test_format_title_only(self):
        """Test formatting reference with title only."""
        result = format_ieee_reference("document.pdf")

        assert result == "document.pdf"

    def test_format_with_single_page(self):
        """Test formatting reference with single page."""
        result = format_ieee_reference("document.pdf", page=5)

        assert result == "document.pdf, p. 5"

    def test_format_with_page_range(self):
        """Test formatting reference with page range."""
        result = format_ieee_reference("report.pdf", page_range="10-12")

        assert result == "report.pdf, pp. 10-12"

    def test_format_page_range_overrides_single_page(self):
        """Test that page_range takes precedence over page."""
        result = format_ieee_reference(
            "document.pdf",
            page=5,
            page_range="10-12"
        )

        # Page range should be used
        assert result == "document.pdf, pp. 10-12"

    def test_format_with_file_path(self):
        """Test formatting with full file path."""
        result = format_ieee_reference(
            "document.pdf",
            page=5,
            file_path="/path/to/document.pdf"
        )

        # File path doesn't affect output (optional parameter for future use)
        assert result == "document.pdf, p. 5"

    def test_format_various_filenames(self):
        """Test formatting with various filename types."""
        assert format_ieee_reference("notes.txt") == "notes.txt"
        assert format_ieee_reference("readme.md") == "readme.md"
        assert format_ieee_reference("page.html") == "page.html"

    def test_format_with_zero_page(self):
        """Test formatting with page 0 (should be treated as valid)."""
        result = format_ieee_reference("document.pdf", page=0)

        assert result == "document.pdf, p. 0"


class TestFormatReferenceList:
    """Tests for formatting lists of references."""

    def test_format_empty_list(self):
        """Test formatting empty chunk list."""
        result = format_reference_list([])

        assert result == ""

    def test_format_single_reference(self):
        """Test formatting single reference."""
        chunk = RetrievedChunk(
            text="Content here",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/document.pdf",
            chunk_position=0,
            metadata={"page_number": 5}
        )

        result = format_reference_list([chunk])

        assert result == "[1] document.pdf, p. 5"

    def test_format_multiple_references(self):
        """Test formatting multiple references."""
        chunks = [
            RetrievedChunk(
                text="Content 1",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc1.pdf",
                chunk_position=0,
                metadata={"page_number": 5}
            ),
            RetrievedChunk(
                text="Content 2",
                score=0.90,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/doc2.txt",
                chunk_position=0,
                metadata={}
            ),
            RetrievedChunk(
                text="Content 3",
                score=0.85,
                chunk_id="3",
                document_id="doc3",
                document_path="/path/to/doc3.md",
                chunk_position=0,
                metadata={"page_range": "10-12"}
            ),
        ]

        result = format_reference_list(chunks)

        expected = """[1] doc1.pdf, p. 5
[2] doc2.txt
[3] doc3.md, pp. 10-12"""

        assert result == expected

    def test_format_with_cited_numbers_filter(self):
        """Test formatting with cited_numbers filter."""
        chunks = [
            RetrievedChunk(
                text="Content 1",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc1.pdf",
                chunk_position=0,
                metadata={}
            ),
            RetrievedChunk(
                text="Content 2",
                score=0.90,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/doc2.txt",
                chunk_position=0,
                metadata={}
            ),
            RetrievedChunk(
                text="Content 3",
                score=0.85,
                chunk_id="3",
                document_id="doc3",
                document_path="/path/to/doc3.md",
                chunk_position=0,
                metadata={}
            ),
        ]

        # Only include citations 1 and 3
        result = format_reference_list(chunks, cited_numbers=[1, 3])

        expected = """[1] doc1.pdf
[3] doc3.md"""

        assert result == expected

    def test_format_with_unknown_document_path(self):
        """Test formatting when document_path is None."""
        chunk = RetrievedChunk(
            text="Content",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path=None,
            chunk_position=0,
            metadata={}
        )

        result = format_reference_list([chunk])

        assert result == "[1] Unknown"

    def test_format_with_none_metadata(self):
        """Test formatting when metadata is None."""
        chunk = RetrievedChunk(
            text="Content",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata=None
        )

        result = format_reference_list([chunk])

        assert result == "[1] doc.pdf"


class TestFormatResponseWithReferences:
    """Tests for formatting responses with inline citations and references."""

    def test_format_with_citations(self):
        """Test formatting response with citations."""
        response_text = "Machine learning is AI [1]. Deep learning uses neural nets [2]."
        chunks = [
            RetrievedChunk(
                text="ML definition",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/ml.pdf",
                chunk_position=0,
                metadata={"page_number": 3}
            ),
            RetrievedChunk(
                text="DL definition",
                score=0.90,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/dl.pdf",
                chunk_position=0,
                metadata={"page_number": 42}
            ),
        ]

        result = format_response_with_references(response_text, chunks)

        assert "Machine learning is AI [1]" in result
        assert "Deep learning uses neural nets [2]" in result
        assert "**References:**" in result
        assert "[1] ml.pdf, p. 3" in result
        assert "[2] dl.pdf, p. 42" in result

    def test_format_empty_chunks(self):
        """Test formatting with no chunks."""
        response_text = "This is a response with no sources."

        result = format_response_with_references(response_text, [])

        assert result == response_text
        assert "References" not in result

    def test_format_unused_references_excluded(self):
        """Test that unused references are excluded by default."""
        response_text = "Only citing source [1]."
        chunks = [
            RetrievedChunk(
                text="Cited content",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/cited.pdf",
                chunk_position=0,
                metadata={}
            ),
            RetrievedChunk(
                text="Uncited content",
                score=0.85,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/uncited.pdf",
                chunk_position=0,
                metadata={}
            ),
        ]

        result = format_response_with_references(response_text, chunks, include_unused_refs=False)

        assert "[1] cited.pdf" in result
        assert "uncited.pdf" not in result

    def test_format_unused_references_included(self):
        """Test that unused references can be included."""
        response_text = "Only citing source [1]."
        chunks = [
            RetrievedChunk(
                text="Cited content",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/cited.pdf",
                chunk_position=0,
                metadata={}
            ),
            RetrievedChunk(
                text="Uncited content",
                score=0.85,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/uncited.pdf",
                chunk_position=0,
                metadata={}
            ),
        ]

        result = format_response_with_references(response_text, chunks, include_unused_refs=True)

        assert "[1] cited.pdf" in result
        assert "[2] uncited.pdf" in result

    def test_format_no_citations_in_text(self):
        """Test formatting when text has no citation markers."""
        response_text = "This text has no citation markers."
        chunks = [
            RetrievedChunk(
                text="Content",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc.pdf",
                chunk_position=0,
                metadata={}
            ),
        ]

        result = format_response_with_references(response_text, chunks, include_unused_refs=False)

        # Should not include references section since no citations were used
        assert result == response_text
        assert "References" not in result

    def test_format_multiline_response(self):
        """Test formatting multiline response."""
        response_text = """First paragraph discusses ML [1].

Second paragraph discusses DL [2].

Third paragraph discusses NLP [3]."""

        chunks = [
            RetrievedChunk(
                text=f"Content {i}",
                score=0.95,
                chunk_id=str(i),
                document_id=f"doc{i}",
                document_path=f"/path/to/doc{i}.pdf",
                chunk_position=0,
                metadata={}
            )
            for i in range(1, 4)
        ]

        result = format_response_with_references(response_text, chunks)

        assert "First paragraph discusses ML [1]" in result
        assert "Second paragraph discusses DL [2]" in result
        assert "Third paragraph discusses NLP [3]" in result
        assert "**References:**" in result
        assert "[1] doc1.pdf" in result
        assert "[2] doc2.pdf" in result
        assert "[3] doc3.pdf" in result

    def test_format_show_file_path_parameter(self):
        """Test show_file_path parameter (currently unused but for future)."""
        response_text = "Text [1]."
        chunks = [
            RetrievedChunk(
                text="Content",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/long/path/to/document.pdf",
                chunk_position=0,
                metadata={}
            ),
        ]

        # Parameter exists but doesn't affect current implementation
        result1 = format_response_with_references(response_text, chunks, show_file_path=True)
        result2 = format_response_with_references(response_text, chunks, show_file_path=False)

        # Both should produce same output currently
        assert "document.pdf" in result1
        assert "document.pdf" in result2
