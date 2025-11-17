"""
Document loaders for various file formats.

This module provides loaders for PDF, TXT, Markdown, and HTML files
with security validation and error handling.
"""

import mimetypes
from pathlib import Path
from typing import Optional, Tuple

from src.ingestion.models import Document
from src.utils.logging import get_logger
from src.utils.security import (
    SecurityError,
    validate_file_path,
    validate_file_size,
    validate_mime_type,
)

logger = get_logger(__name__)


def load_document(
    file_path: Path,
    format: Optional[str] = None,
) -> Document:
    """
    Load a document from file, auto-detecting format if not specified.

    Args:
        file_path: Path to document file
        format: Optional format override ('pdf', 'txt', 'md', 'html')

    Returns:
        Document instance

    Raises:
        ValueError: If format not supported
        SecurityError: If file fails security checks
        FileNotFoundError: If file doesn't exist
    """
    # Validate security
    file_path = validate_file_path(file_path)
    validate_file_size(file_path)

    # Detect format
    if format is None:
        format = _detect_format(file_path)

    logger.info(f"Loading document: {file_path} (format: {format})")

    # Load based on format
    loaders = {
        "pdf": load_pdf,
        "txt": load_txt,
        "md": load_markdown,
        "html": load_html,
    }

    loader = loaders.get(format.lower())
    if loader is None:
        raise ValueError(f"Unsupported format: {format}. Supported: {list(loaders.keys())}")

    return loader(file_path)


def _detect_format(file_path: Path) -> str:
    """
    Detect document format from extension and MIME type.

    Args:
        file_path: Path to file

    Returns:
        Detected format string
    """
    # Get extension
    ext = file_path.suffix.lower().lstrip(".")

    # Map common extensions
    ext_map = {
        "pdf": "pdf",
        "txt": "txt",
        "md": "md",
        "markdown": "md",
        "html": "html",
        "htm": "html",
    }

    detected = ext_map.get(ext)
    if detected:
        return detected

    # Try MIME type
    mime_type = mimetypes.guess_type(str(file_path))[0]
    if mime_type:
        if "pdf" in mime_type:
            return "pdf"
        elif "html" in mime_type:
            return "html"
        elif "text" in mime_type:
            return "txt"

    # Default to txt
    logger.warning(f"Could not detect format for {file_path}, defaulting to txt")
    return "txt"


def load_pdf(file_path: Path) -> Document:
    """
    Load PDF using PyMuPDF4LLM.

    Args:
        file_path: Path to PDF file

    Returns:
        Document instance
    """
    try:
        import pymupdf4llm
        import pymupdf as fitz
    except ImportError:
        raise ImportError("pymupdf and pymupdf4llm required for PDF support: pip install pymupdf pymupdf4llm")

    logger.debug(f"Extracting text from PDF: {file_path}")

    # Get metadata first to know page count
    doc = fitz.open(file_path)
    metadata = doc.metadata or {}
    page_count = len(doc)
    doc.close()

    # Extract text page by page with page markers for citation tracking
    pages_text = []
    for page_num in range(page_count):
        # Extract markdown for this page only
        page_md = pymupdf4llm.to_markdown(str(file_path), pages=[page_num])
        # Add page marker before the page content
        pages_text.append(f"<!-- PAGE {page_num + 1} -->\n{page_md}")

    # Join all pages with double newlines
    md_text = "\n\n".join(pages_text)

    title = metadata.get("title") or file_path.stem
    author = metadata.get("author")

    logger.info(f"Loaded PDF: {page_count} pages, {len(md_text)} characters")

    return Document.from_file(
        file_path=file_path,
        content=md_text,
        format="pdf",
        title=title,
        author=author,
        page_count=page_count,
    )


def load_txt(file_path: Path) -> Document:
    """
    Load plain text file with encoding detection.

    Args:
        file_path: Path to text file

    Returns:
        Document instance
    """
    try:
        # Try UTF-8 first
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fall back to encoding detection
        try:
            import chardet
        except ImportError:
            raise ImportError("chardet required for non-UTF-8 files: pip install chardet")

        logger.debug(f"UTF-8 failed, detecting encoding for {file_path}")
        raw = file_path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding", "utf-8")
        confidence = detected.get("confidence", 0)

        logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")

        try:
            content = raw.decode(encoding)
        except (UnicodeDecodeError, TypeError):
            # Last resort: latin-1 (never fails)
            content = raw.decode("latin-1")

    logger.info(f"Loaded text file: {len(content)} characters")

    return Document.from_file(
        file_path=file_path,
        content=content,
        format="txt",
        title=file_path.stem,
    )


def load_markdown(file_path: Path) -> Document:
    """
    Load Markdown file.

    Args:
        file_path: Path to markdown file

    Returns:
        Document instance
    """
    content = file_path.read_text(encoding="utf-8")

    # Try to extract title from frontmatter or first heading
    title = file_path.stem
    lines = content.split("\n")

    for line in lines[:10]:  # Check first 10 lines
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    logger.info(f"Loaded markdown: {len(content)} characters")

    return Document.from_file(
        file_path=file_path,
        content=content,
        format="md",
        title=title,
    )


def load_html(file_path: Path) -> Document:
    """
    Load HTML using Trafilatura for content extraction.

    Args:
        file_path: Path to HTML file

    Returns:
        Document instance
    """
    try:
        import trafilatura
    except ImportError:
        raise ImportError("trafilatura required for HTML support: pip install trafilatura")

    html = file_path.read_text(encoding="utf-8")

    # Extract main content
    text = trafilatura.extract(
        html,
        include_links=False,
        include_images=False,
        include_tables=True,
    )

    if not text:
        # Fallback: use BeautifulSoup for basic extraction
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 required: pip install beautifulsoup4")

        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n", strip=True)

    # Try to get title
    title = file_path.stem
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
    except (AttributeError, TypeError) as e:
        # HTML parsing failed or title extraction failed
        logger.debug(f"Could not extract title from HTML: {e}")
        # Fall back to filename as title

    logger.info(f"Loaded HTML: {len(text or '')} characters")

    return Document.from_file(
        file_path=file_path,
        content=text or "",
        format="html",
        title=title,
    )
