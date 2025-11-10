"""
IEEE-style citation formatting for RAG responses.

Provides functions to format retrieved chunks as numbered citations
with a formatted reference list in IEEE style.
"""

import re
from pathlib import Path
from typing import List, Optional

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
