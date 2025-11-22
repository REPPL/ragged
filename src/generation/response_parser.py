"""
Parse LLM responses to extract answers and citations.

Handles parsing of generated text to extract structured information.
"""

import re
from dataclasses import dataclass


@dataclass
class GeneratedResponse:
    """Parsed response from LLM."""

    answer: str
    citations: list[str]
    raw_response: str

    def __repr__(self) -> str:
        """String representation."""
        return f"GeneratedResponse(citations={len(self.citations)})"


def parse_response(response_text: str) -> GeneratedResponse:
    """
    Parse LLM response to extract answer and citations.

    Args:
        response_text: Raw LLM response

    Returns:
        Parsed response with citations extracted

    Example:
        >>> text = "The answer is 42 [Source: guide.md]. Also see [Source: doc.pdf]."
        >>> response = parse_response(text)
        >>> response.citations
        ['guide.md', 'doc.pdf']
    """
    # Extract citations using regex
    pattern = r'\[Source:\s*([^\]]+)\]'
    citations = re.findall(pattern, response_text)

    # Get unique citations while preserving order
    seen = set()
    unique_citations = []
    for citation in citations:
        citation = citation.strip()
        if citation not in seen:
            seen.add(citation)
            unique_citations.append(citation)

    return GeneratedResponse(
        answer=response_text,
        citations=unique_citations,
        raw_response=response_text
    )


def extract_citations(text: str) -> list[str]:
    """
    Extract citations from text.

    Args:
        text: Text containing [Source: ...] citations

    Returns:
        List of unique citation strings

    Example:
        >>> text = "Answer [Source: file1.txt]. More info [Source: file2.pdf]."
        >>> extract_citations(text)
        ['file1.txt', 'file2.pdf']
    """
    response = parse_response(text)
    return response.citations


def format_response_for_cli(response: GeneratedResponse | str) -> str:
    """
    Format response for CLI display.

    Args:
        response: Parsed response or raw response text

    Returns:
        Formatted string for terminal output

    Example output:
        Answer:
        The system supports PDF, TXT, MD, and HTML files.

        Sources:
        - guide.md
        - documentation.pdf
    """
    # Handle both GeneratedResponse objects and raw strings
    if isinstance(response, str):
        response = parse_response(response)

    output = []

    # Add answer
    output.append("Answer:")
    output.append(response.answer)

    # Add citations if present
    if response.citations:
        output.append("\nSources:")
        for citation in response.citations:
            output.append(f"- {citation}")

    return "\n".join(output)
