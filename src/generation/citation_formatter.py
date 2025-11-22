"""
IEEE-style citation formatting for RAG responses.

Provides functions to format retrieved chunks as numbered citations
with a formatted reference list in IEEE style.

v0.3.7c: Enhanced citations with quotes, confidence scores, and chunk IDs.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.retrieval.retriever import RetrievedChunk


def extract_citation_numbers(text: str) -> List[int]:
    """
    Extract citation numbers from text (e.g., [1], [2], [3]).

    Args:
        text: Text containing citations in [N] format

    Returns:
        List of citation numbers found in the text (sorted, deduplicated)
    """
    # Match patterns like [1], [2], [3]
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, text)

    # Convert to integers, sort, and deduplicate
    citation_nums = sorted(set(int(num) for num in matches))

    return citation_nums


def format_ieee_reference(
    title: str,
    page: Optional[int] = None,
    page_range: Optional[str] = None,
    file_path: str = ""
) -> str:
    """
    Format a single reference in IEEE style.

    Args:
        title: Document title (typically filename)
        page: Single page number (if available)
        page_range: Page range string like "5-7" (if available)
        file_path: Full file path (optional, for display)

    Returns:
        Formatted IEEE reference string

    Examples:
        format_ieee_reference("document.pdf", page=5)
        # Returns: "document.pdf, p. 5"

        format_ieee_reference("report.pdf", page_range="10-12")
        # Returns: "report.pdf, pp. 10-12"
    """
    # Start with the title/filename
    reference = title

    # Add page information if available
    if page_range:
        reference += f", pp. {page_range}"
    elif page is not None:
        reference += f", p. {page}"

    return reference


def format_reference_list(
    chunks: List[RetrievedChunk],
    cited_numbers: Optional[List[int]] = None
) -> str:
    """
    Format a list of chunks as IEEE-style numbered references.

    Args:
        chunks: List of retrieved chunks to format as references
        cited_numbers: Optional list of citation numbers actually used in text.
                      If provided, only these references will be included.

    Returns:
        Formatted reference list string

    Example:
        [1] document.pdf, p. 5
        [2] report.txt
        [3] notes.md, pp. 10-12
    """
    if not chunks:
        return ""

    references = []

    for i, chunk in enumerate(chunks, start=1):
        # Skip if we have cited_numbers and this one wasn't cited
        if cited_numbers is not None and i not in cited_numbers:
            continue

        # Extract metadata
        doc_path = chunk.document_path or "Unknown"
        filename = Path(doc_path).name if doc_path != "Unknown" else "Unknown"

        page = chunk.metadata.get("page_number") if chunk.metadata else None
        page_range = chunk.metadata.get("page_range") if chunk.metadata else None

        # Format the reference
        reference = format_ieee_reference(
            title=filename,
            page=page,
            page_range=page_range,
            file_path=doc_path
        )

        references.append(f"[{i}] {reference}")

    return "\n".join(references)


def format_response_with_references(
    response_text: str,
    chunks: List[RetrievedChunk],
    show_file_path: bool = True,
    include_unused_refs: bool = False
) -> str:
    """
    Format a response with inline citations and a reference list.

    Args:
        response_text: The generated response text (may contain [N] citations)
        chunks: List of retrieved chunks used for generation
        show_file_path: Whether to include full file paths in references
        include_unused_refs: Whether to include references not cited in text

    Returns:
        Formatted response with inline citations and reference list

    Example:
        Input response_text: "Machine learning is AI [1]. Deep learning uses neural nets [2]."
        Output:
            Machine learning is AI [1]. Deep learning uses neural nets [2].

            References:
            [1] ml_guide.pdf, p. 3
            [2] dl_book.pdf, p. 42
    """
    if not chunks:
        return response_text

    # Extract which citation numbers are actually used in the text
    cited_numbers = extract_citation_numbers(response_text) if not include_unused_refs else None

    # Format the reference list
    references = format_reference_list(chunks, cited_numbers)

    if not references:
        return response_text

    # Combine response with references
    formatted = f"{response_text}\n\n**References:**\n{references}"

    return formatted


# v0.3.7c: Enhanced citation functions

def extract_quote_from_chunk(
    chunk: RetrievedChunk,
    max_length: int = 200,
    context_words: int = 5
) -> Optional[str]:
    """
    Extract a representative quote from a chunk.

    Args:
        chunk: Retrieved chunk to extract quote from
        max_length: Maximum quote length in characters
        context_words: Number of words for context on each side

    Returns:
        Extracted quote string, or None if chunk has no content

    Example:
        >>> chunk = RetrievedChunk(text="Machine learning is...")
        >>> extract_quote_from_chunk(chunk, max_length=50)
        '"Machine learning is a subset of artificial..."'
    """
    if not hasattr(chunk, 'text') or not chunk.text:
        return None

    content = chunk.text.strip()

    # If content is short enough, use it all
    if len(content) <= max_length:
        return f'"{content}"'

    # Otherwise, extract first part with ellipsis
    quote = content[:max_length].rsplit(' ', 1)[0]  # Break at word boundary
    return f'"{quote}..."'


def format_enhanced_citation(
    citation_num: int,
    chunk: RetrievedChunk,
    include_quote: bool = True,
    include_confidence: bool = True,
    include_chunk_id: bool = False
) -> str:
    """
    Format an enhanced citation with quote, confidence, and metadata.

    Args:
        citation_num: Citation number [N]
        chunk: Retrieved chunk
        include_quote: Whether to include direct quote
        include_confidence: Whether to include confidence score
        include_chunk_id: Whether to include chunk ID (for debugging)

    Returns:
        Enhanced citation string

    Example:
        [1] Source: paper.pdf, Page 42, Confidence: 0.95
        "Machine learning is a subset of artificial intelligence that focuses..."
        Chunk ID: doc1_ch007
    """
    lines = []

    # Extract metadata
    doc_path = chunk.document_path or "Unknown"
    filename = Path(doc_path).name if doc_path != "Unknown" else "Unknown"
    page = chunk.metadata.get("page_number") if chunk.metadata else None
    confidence = getattr(chunk, 'confidence', None) or chunk.metadata.get("confidence") if chunk.metadata else None

    # First line: Basic citation info
    citation_parts = [f"Source: {filename}"]

    if page is not None:
        citation_parts.append(f"Page {page}")

    if include_confidence and confidence is not None:
        citation_parts.append(f"Confidence: {confidence:.2f}")

    lines.append(f"[{citation_num}] {', '.join(citation_parts)}")

    # Quote (if requested and available)
    if include_quote:
        quote = extract_quote_from_chunk(chunk)
        if quote:
            lines.append(quote)

    # Chunk ID (if requested)
    if include_chunk_id and hasattr(chunk, 'chunk_id'):
        lines.append(f"Chunk ID: {chunk.chunk_id}")

    return "\n".join(lines)


def format_enhanced_reference_list(
    chunks: List[RetrievedChunk],
    cited_numbers: Optional[List[int]] = None,
    include_quotes: bool = True,
    include_confidence: bool = True,
    confidence_threshold: float = 0.0
) -> str:
    """
    Format enhanced reference list with quotes and confidence scores.

    Args:
        chunks: List of retrieved chunks
        cited_numbers: Optional list of actually cited numbers
        include_quotes: Whether to include direct quotes
        include_confidence: Whether to show confidence scores
        confidence_threshold: Minimum confidence to include (0.0-1.0)

    Returns:
        Formatted enhanced reference list

    Example:
        [1] Source: paper.pdf, Page 42, Confidence: 0.95
        "Machine learning is a subset of artificial intelligence..."

        [2] Source: book.pdf, Page 15, Confidence: 0.88
        "Neural networks are computational models inspired by..."
    """
    if not chunks:
        return ""

    references = []

    for i, chunk in enumerate(chunks, start=1):
        # Skip if not cited
        if cited_numbers is not None and i not in cited_numbers:
            continue

        # Skip if below confidence threshold
        confidence = getattr(chunk, 'confidence', None) or chunk.metadata.get("confidence") if chunk.metadata else None
        if confidence is not None and confidence < confidence_threshold:
            continue

        # Format enhanced citation
        citation = format_enhanced_citation(
            citation_num=i,
            chunk=chunk,
            include_quote=include_quotes,
            include_confidence=include_confidence
        )

        references.append(citation)

    return "\n\n".join(references)


def format_response_with_enhanced_citations(
    response_text: str,
    chunks: List[RetrievedChunk],
    include_quotes: bool = True,
    include_confidence: bool = True,
    confidence_threshold: float = 0.3,
    include_unused_refs: bool = False
) -> str:
    """
    Format response with enhanced citations including quotes and confidence.

    Args:
        response_text: Generated response with [N] citations
        chunks: Retrieved chunks used
        include_quotes: Whether to include direct quotes from sources
        include_confidence: Whether to show confidence scores
        confidence_threshold: Minimum confidence to include citation
        include_unused_refs: Whether to include uncited references

    Returns:
        Formatted response with enhanced reference list

    Example:
        Machine learning is defined as... [1]

        References:
        [1] Source: ml_guide.pdf, Page 3, Confidence: 0.95
        "Machine learning is a subset of artificial intelligence..."
    """
    if not chunks:
        return response_text

    # Extract cited numbers
    cited_numbers = extract_citation_numbers(response_text) if not include_unused_refs else None

    # Format enhanced references
    references = format_enhanced_reference_list(
        chunks=chunks,
        cited_numbers=cited_numbers,
        include_quotes=include_quotes,
        include_confidence=include_confidence,
        confidence_threshold=confidence_threshold
    )

    if not references:
        return response_text

    # Combine
    formatted = f"{response_text}\n\n**References:**\n{references}"

    return formatted


def deduplicate_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate citations based on source and page.

    Args:
        citations: List of citation dictionaries with 'source' and 'page' keys

    Returns:
        Deduplicated list of citations

    Example:
        >>> citations = [
        ...     {"source": "paper.pdf", "page": 42, "quote": "ML is..."},
        ...     {"source": "paper.pdf", "page": 42, "quote": "Machine learning..."},
        ...     {"source": "book.pdf", "page": 10, "quote": "AI is..."}
        ... ]
        >>> deduplicated = deduplicate_citations(citations)
        >>> len(deduplicated)
        2
    """
    seen = set()
    deduplicated = []

    for citation in citations:
        key = (citation.get('source'), citation.get('page'))

        if key not in seen:
            seen.add(key)
            deduplicated.append(citation)

    return deduplicated
