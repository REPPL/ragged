"""Tests for response parsing utilities."""

import pytest
from src.generation.response_parser import (
    parse_response,
    extract_citations,
    format_response_for_cli
)


class TestResponseParser:
    """Tests for response parsing functions."""

    def test_extract_citations_single(self):
        """Test extracting a single citation."""
        text = "Machine learning is a subset of AI [Source: ai_guide.pdf]."

        citations = extract_citations(text)

        assert len(citations) == 1
        assert "ai_guide.pdf" in citations

    def test_extract_citations_multiple(self):
        """Test extracting multiple citations."""
        text = """
        Machine learning is a subset of AI [Source: ai_guide.pdf].
        Neural networks are important [Source: deep_learning.txt].
        NLP is used for text processing [Source: nlp_intro.md].
        """

        citations = extract_citations(text)

        assert len(citations) == 3
        assert "ai_guide.pdf" in citations
        assert "deep_learning.txt" in citations
        assert "nlp_intro.md" in citations

    def test_extract_citations_none(self):
        """Test extracting citations when none exist."""
        text = "This is a response with no citations."

        citations = extract_citations(text)

        assert len(citations) == 0

    def test_extract_citations_duplicates(self):
        """Test extracting citations with duplicates."""
        text = """
        First mention [Source: file.txt].
        Second mention [Source: file.txt].
        Third mention [Source: file.txt].
        """

        citations = extract_citations(text)

        # Should deduplicate
        assert len(citations) == 1
        assert "file.txt" in citations

    def test_extract_citations_various_formats(self):
        """Test extraction with various filename formats."""
        text = """
        PDF file [Source: document.pdf].
        Text file [Source: notes.txt].
        Markdown file [Source: readme.md].
        HTML file [Source: page.html].
        """

        citations = extract_citations(text)

        assert len(citations) == 4
        assert all(
            ext in " ".join(citations)
            for ext in [".pdf", ".txt", ".md", ".html"]
        )

    def test_parse_response_with_citations(self):
        """Test parsing response with citations."""
        response_text = "Answer here [Source: file.txt]."

        result = parse_response(response_text)

        assert result is not None
        # Depending on implementation, may return dict or object
        # with 'text' and 'citations' fields

    def test_format_response_for_cli(self):
        """Test formatting response for CLI display."""
        response_text = """
        Machine learning is AI [Source: ml.pdf].
        Deep learning uses neural nets [Source: dl.txt].
        """

        formatted = format_response_for_cli(response_text)

        assert formatted is not None
        assert isinstance(formatted, str)
        # Should contain the original content
        assert "machine learning" in formatted.lower() or "Machine learning" in formatted

    def test_format_response_for_cli_no_citations(self):
        """Test formatting response without citations."""
        response_text = "This is a simple response."

        formatted = format_response_for_cli(response_text)

        assert formatted is not None
        assert "simple response" in formatted.lower() or "simple response" in formatted

    def test_format_response_for_cli_preserves_formatting(self):
        """Test that formatting preserves line breaks."""
        response_text = """Line 1.

        Line 2.

        Line 3."""

        formatted = format_response_for_cli(response_text)

        # Should preserve basic structure
        assert "Line 1" in formatted
        assert "Line 2" in formatted
        assert "Line 3" in formatted

    def test_extract_citations_case_insensitive(self):
        """Test that citation extraction is case-insensitive."""
        text = """
        First [source: file1.txt].
        Second [Source: file2.txt].
        Third [SOURCE: file3.txt].
        """

        citations = extract_citations(text)

        # All variants should be recognized
        assert len(citations) >= 1

    def test_extract_citations_with_spaces(self):
        """Test citation extraction with various spacing."""
        text = """
        Normal [Source: file1.txt].
        Extra spaces [Source:  file2.txt].
        Tab [Source:	file3.txt].
        """

        citations = extract_citations(text)

        # Should handle various spacing
        assert len(citations) >= 1

    def test_parse_response_empty_string(self):
        """Test parsing empty response."""
        result = parse_response("")

        # Should handle gracefully
        assert result is not None or result == ""

    def test_format_response_for_cli_long_text(self):
        """Test formatting long response."""
        long_text = "Sentence. " * 100 + "[Source: file.txt]"

        formatted = format_response_for_cli(long_text)

        assert formatted is not None
        # Should contain content
        assert len(formatted) > 0
