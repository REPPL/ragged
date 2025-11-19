"""
Document loaders for various file formats.

This module provides loaders for PDF, TXT, Markdown, and HTML files
with security validation and error handling.

v0.3.4a: PDF loading now uses the new processor architecture (Docling or legacy).
"""

import mimetypes
from pathlib import Path
from typing import Optional, Tuple

from src.config.settings import get_settings
from src.ingestion.models import Document
from src.processing import ProcessorConfig, ProcessorFactory
from src.utils.logging import get_logger
from src.utils.security import (
    SecurityError,
    validate_file_path,
    validate_file_size,
    validate_mime_type,
)

logger = get_logger(__name__)
settings = get_settings()


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


def load_pdf(file_path: Path, processor_type: Optional[str] = None) -> Document:
    """
    Load PDF using the configured document processor.

    v0.3.4a: Now uses the new processor architecture with Docling or legacy pymupdf.

    Args:
        file_path: Path to PDF file
        processor_type: Override processor type ('docling' or 'legacy').
                       If None, uses settings.document_processor.

    Returns:
        Document instance

    Raises:
        ImportError: If required dependencies are missing
        ProcessorError: If document processing fails
    """
    logger.debug(f"Loading PDF: {file_path}")

    # Determine which processor to use
    if processor_type is None:
        processor_type = settings.document_processor

    # Create processor configuration
    config = ProcessorConfig(
        processor_type=processor_type,
        enable_table_extraction=settings.enable_table_extraction,
        enable_layout_analysis=settings.enable_layout_analysis,
        model_cache_dir=settings.data_dir / "models",
    )

    # Check if processor is available, fall back to legacy if needed
    if not ProcessorFactory.is_processor_available(processor_type):
        logger.warning(
            f"Processor '{processor_type}' not available. "
            f"Falling back to 'legacy' processor."
        )
        config.processor_type = "legacy"

    # Create processor and process document
    try:
        processor = ProcessorFactory.create(config)
        result = processor.process(file_path)

        logger.info(
            f"Processed PDF with {result.processor_type}: "
            f"{result.metadata.get('page_count', 0)} pages, "
            f"{len(result.content)} characters, "
            f"{len(result.tables)} tables extracted"
        )

        # Convert ProcessedDocument to Document
        return Document.from_file(
            file_path=file_path,
            content=result.content,
            format="pdf",
            title=result.metadata.get("title", file_path.stem),
            author=result.metadata.get("author"),
            page_count=result.metadata.get("page_count"),
        )

    except ImportError as e:
        # If Docling not installed, automatically fall back to legacy
        if "docling" in str(e).lower() and config.processor_type == "docling":
            logger.warning(
                "Docling not installed. Falling back to legacy processor. "
                "Install Docling with: pip install docling docling-core docling-parse"
            )
            config.processor_type = "legacy"
            processor = ProcessorFactory.create(config)
            result = processor.process(file_path)

            return Document.from_file(
                file_path=file_path,
                content=result.content,
                format="pdf",
                title=result.metadata.get("title", file_path.stem),
                author=result.metadata.get("author"),
                page_count=result.metadata.get("page_count"),
            )
        else:
            # Re-raise if it's a different import error
            raise


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
        encoding = detected.get("encoding") or "utf-8"
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
