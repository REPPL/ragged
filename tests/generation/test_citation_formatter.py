"""Tests for IEEE-style citation formatting."""

import pytest
from pathlib import Path
from src.generation.citation_formatter import (
    extract_citation_numbers,
    format_ieee_reference,
    format_reference_list,
    format_response_with_references,
    # v0.3.7c: Enhanced citations
    extract_quote_from_chunk,
    format_enhanced_citation,
    format_enhanced_reference_list,
    format_response_with_enhanced_citations,
    deduplicate_citations,
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


# v0.3.7c: Enhanced citation tests
class TestEnhancedCitations:
    """Tests for enhanced citation formatting with quotes and confidence."""

    def test_extract_quote_short_content(self):
        """Test quote extraction from short content."""
        chunk = RetrievedChunk(
            text="Machine learning is AI.",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={}
        )

        quote = extract_quote_from_chunk(chunk, max_length=200)

        assert quote == '"Machine learning is AI."'

    def test_extract_quote_long_content(self):
        """Test quote extraction with truncation."""
        long_text = "Machine learning is a subset of artificial intelligence " * 10
        chunk = RetrievedChunk(
            text=long_text,
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={}
        )

        quote = extract_quote_from_chunk(chunk, max_length=100)

        assert quote.startswith('"Machine learning')
        assert quote.endswith('..."')
        assert len(quote) <= 110  # Slightly more than max_length due to ellipsis

    def test_extract_quote_empty_content(self):
        """Test quote extraction from empty chunk."""
        chunk = RetrievedChunk(
            text="",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={}
        )

        quote = extract_quote_from_chunk(chunk)

        assert quote is None

    def test_extract_quote_word_boundary(self):
        """Test that truncation respects word boundaries."""
        chunk = RetrievedChunk(
            text="The quick brown fox jumps over the lazy dog. " * 10,
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={}
        )

        quote = extract_quote_from_chunk(chunk, max_length=50)

        # Should not cut words in half
        assert not quote[:-4].endswith("ju")  # Not "ju..." from "jumps"
        assert quote.endswith('..."')

    def test_format_enhanced_citation_basic(self):
        """Test basic enhanced citation formatting."""
        chunk = RetrievedChunk(
            text="Machine learning is a subset of AI.",
            score=0.95,
            chunk_id="doc1_ch001",
            document_id="doc1",
            document_path="/path/to/ml_paper.pdf",
            chunk_position=0,
            metadata={"page_number": 42, "confidence": 0.95}
        )

        citation = format_enhanced_citation(
            citation_num=1,
            chunk=chunk,
            include_quote=True,
            include_confidence=True,
            include_chunk_id=False
        )

        assert "[1] Source: ml_paper.pdf, Page 42, Confidence: 0.95" in citation
        assert '"Machine learning is a subset of AI."' in citation

    def test_format_enhanced_citation_with_chunk_id(self):
        """Test enhanced citation with chunk ID."""
        chunk = RetrievedChunk(
            text="Test content",
            score=0.95,
            chunk_id="doc1_ch007",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={"page_number": 10}
        )

        citation = format_enhanced_citation(
            citation_num=1,
            chunk=chunk,
            include_chunk_id=True
        )

        assert "Chunk ID: doc1_ch007" in citation

    def test_format_enhanced_citation_no_quote(self):
        """Test enhanced citation without quote."""
        chunk = RetrievedChunk(
            text="Some content",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={"page_number": 5, "confidence": 0.88}
        )

        citation = format_enhanced_citation(
            citation_num=1,
            chunk=chunk,
            include_quote=False,
            include_confidence=True
        )

        assert "[1] Source: doc.pdf, Page 5, Confidence: 0.88" in citation
        assert '"Some content"' not in citation

    def test_format_enhanced_citation_no_confidence(self):
        """Test enhanced citation without confidence score."""
        chunk = RetrievedChunk(
            text="Content",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.pdf",
            chunk_position=0,
            metadata={"page_number": 3}
        )

        citation = format_enhanced_citation(
            citation_num=1,
            chunk=chunk,
            include_confidence=False
        )

        assert "Confidence" not in citation
        assert "[1] Source: doc.pdf, Page 3" in citation

    def test_format_enhanced_citation_no_page(self):
        """Test enhanced citation without page number."""
        chunk = RetrievedChunk(
            text="Content",
            score=0.95,
            chunk_id="1",
            document_id="doc1",
            document_path="/path/to/doc.txt",
            chunk_position=0,
            metadata={"confidence": 0.92}
        )

        citation = format_enhanced_citation(
            citation_num=1,
            chunk=chunk,
            include_confidence=True
        )

        assert "[1] Source: doc.txt, Confidence: 0.92" in citation
        assert "Page" not in citation

    def test_format_enhanced_reference_list_basic(self):
        """Test enhanced reference list formatting."""
        chunks = [
            RetrievedChunk(
                text="ML is AI.",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/ml.pdf",
                chunk_position=0,
                metadata={"page_number": 3, "confidence": 0.95}
            ),
            RetrievedChunk(
                text="DL uses neural networks.",
                score=0.90,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/dl.pdf",
                chunk_position=0,
                metadata={"page_number": 42, "confidence": 0.88}
            ),
        ]

        references = format_enhanced_reference_list(
            chunks=chunks,
            include_quotes=True,
            include_confidence=True
        )

        assert "[1] Source: ml.pdf, Page 3, Confidence: 0.95" in references
        assert '"ML is AI."' in references
        assert "[2] Source: dl.pdf, Page 42, Confidence: 0.88" in references
        assert '"DL uses neural networks."' in references

    def test_format_enhanced_reference_list_with_filter(self):
        """Test enhanced reference list with cited_numbers filter."""
        chunks = [
            RetrievedChunk(
                text="Content 1",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc1.pdf",
                chunk_position=0,
                metadata={"confidence": 0.95}
            ),
            RetrievedChunk(
                text="Content 2",
                score=0.90,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/doc2.pdf",
                chunk_position=0,
                metadata={"confidence": 0.90}
            ),
            RetrievedChunk(
                text="Content 3",
                score=0.85,
                chunk_id="3",
                document_id="doc3",
                document_path="/path/to/doc3.pdf",
                chunk_position=0,
                metadata={"confidence": 0.85}
            ),
        ]

        # Only include citations 1 and 3
        references = format_enhanced_reference_list(
            chunks=chunks,
            cited_numbers=[1, 3]
        )

        assert "[1]" in references
        assert "[3]" in references
        assert "[2]" not in references

    def test_format_enhanced_reference_list_confidence_threshold(self):
        """Test filtering by confidence threshold."""
        chunks = [
            RetrievedChunk(
                text="High confidence",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc1.pdf",
                chunk_position=0,
                metadata={"confidence": 0.95}
            ),
            RetrievedChunk(
                text="Low confidence",
                score=0.40,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/doc2.pdf",
                chunk_position=0,
                metadata={"confidence": 0.25}
            ),
        ]

        # Filter out confidence < 0.5
        references = format_enhanced_reference_list(
            chunks=chunks,
            confidence_threshold=0.5
        )

        assert "doc1.pdf" in references
        assert "doc2.pdf" not in references

    def test_format_enhanced_reference_list_empty(self):
        """Test enhanced reference list with empty chunks."""
        references = format_enhanced_reference_list([])

        assert references == ""

    def test_format_response_with_enhanced_citations_basic(self):
        """Test formatting response with enhanced citations."""
        response_text = "Machine learning is AI [1]. Deep learning uses neural nets [2]."
        chunks = [
            RetrievedChunk(
                text="ML is a subset of AI that focuses on learning from data.",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/ml.pdf",
                chunk_position=0,
                metadata={"page_number": 3, "confidence": 0.95}
            ),
            RetrievedChunk(
                text="Deep learning uses neural networks with multiple layers.",
                score=0.90,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/dl.pdf",
                chunk_position=0,
                metadata={"page_number": 42, "confidence": 0.88}
            ),
        ]

        result = format_response_with_enhanced_citations(
            response_text=response_text,
            chunks=chunks,
            include_quotes=True,
            include_confidence=True
        )

        assert "Machine learning is AI [1]" in result
        assert "**References:**" in result
        assert "[1] Source: ml.pdf, Page 3, Confidence: 0.95" in result
        assert '"ML is a subset of AI' in result
        assert "[2] Source: dl.pdf, Page 42, Confidence: 0.88" in result

    def test_format_response_with_enhanced_citations_no_quotes(self):
        """Test enhanced response without quotes."""
        response_text = "Text [1]."
        chunks = [
            RetrievedChunk(
                text="Some content",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc.pdf",
                chunk_position=0,
                metadata={"confidence": 0.92}
            ),
        ]

        result = format_response_with_enhanced_citations(
            response_text=response_text,
            chunks=chunks,
            include_quotes=False,
            include_confidence=True
        )

        assert "[1] Source: doc.pdf, Confidence: 0.92" in result
        assert '"Some content"' not in result

    def test_format_response_with_enhanced_citations_threshold(self):
        """Test enhanced response with confidence threshold."""
        response_text = "Text [1] and [2]."
        chunks = [
            RetrievedChunk(
                text="High confidence content",
                score=0.95,
                chunk_id="1",
                document_id="doc1",
                document_path="/path/to/doc1.pdf",
                chunk_position=0,
                metadata={"confidence": 0.95}
            ),
            RetrievedChunk(
                text="Low confidence content",
                score=0.50,
                chunk_id="2",
                document_id="doc2",
                document_path="/path/to/doc2.pdf",
                chunk_position=0,
                metadata={"confidence": 0.25}
            ),
        ]

        result = format_response_with_enhanced_citations(
            response_text=response_text,
            chunks=chunks,
            confidence_threshold=0.5  # Filter out [2]
        )

        assert "doc1.pdf" in result
        assert "doc2.pdf" not in result

    def test_format_response_with_enhanced_citations_empty_chunks(self):
        """Test enhanced response with no chunks."""
        response_text = "Text with no sources."

        result = format_response_with_enhanced_citations(
            response_text=response_text,
            chunks=[]
        )

        assert result == response_text
        assert "References" not in result

    def test_deduplicate_citations_basic(self):
        """Test basic citation deduplication."""
        citations = [
            {"source": "paper.pdf", "page": 42, "quote": "First quote"},
            {"source": "paper.pdf", "page": 42, "quote": "Second quote"},
            {"source": "book.pdf", "page": 10, "quote": "Different source"},
        ]

        deduplicated = deduplicate_citations(citations)

        assert len(deduplicated) == 2
        assert deduplicated[0]["source"] == "paper.pdf"
        assert deduplicated[1]["source"] == "book.pdf"

    def test_deduplicate_citations_different_pages(self):
        """Test that same source with different pages is not deduplicated."""
        citations = [
            {"source": "paper.pdf", "page": 42},
            {"source": "paper.pdf", "page": 43},
            {"source": "paper.pdf", "page": 44},
        ]

        deduplicated = deduplicate_citations(citations)

        assert len(deduplicated) == 3

    def test_deduplicate_citations_no_page(self):
        """Test deduplication with None page numbers."""
        citations = [
            {"source": "doc.txt", "page": None, "quote": "First"},
            {"source": "doc.txt", "page": None, "quote": "Second"},
        ]

        deduplicated = deduplicate_citations(citations)

        # Should deduplicate based on (source, None) key
        assert len(deduplicated) == 1

    def test_deduplicate_citations_empty_list(self):
        """Test deduplication of empty list."""
        deduplicated = deduplicate_citations([])

        assert deduplicated == []

    def test_deduplicate_citations_preserves_order(self):
        """Test that deduplication preserves first occurrence order."""
        citations = [
            {"source": "a.pdf", "page": 1},
            {"source": "b.pdf", "page": 2},
            {"source": "a.pdf", "page": 1},  # Duplicate
            {"source": "c.pdf", "page": 3},
        ]

        deduplicated = deduplicate_citations(citations)

        assert len(deduplicated) == 3
        assert deduplicated[0]["source"] == "a.pdf"
        assert deduplicated[1]["source"] == "b.pdf"
        assert deduplicated[2]["source"] == "c.pdf"
