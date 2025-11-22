"""
Legacy document processor using PyMuPDF.

This processor maintains backwards compatibility with the existing pymupdf-based
document processing. It provides basic text extraction without advanced features
like layout analysis or table structure preservation.
"""

import time
from pathlib import Path

from src.processing.base import BaseProcessor, ProcessedDocument, ProcessorConfig, ProcessorError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LegacyProcessor(BaseProcessor):
    """
    Legacy processor using PyMuPDF for basic document processing.

    This processor provides backwards compatibility with the original ragged
    implementation. It uses pymupdf4llm for text extraction but doesn't
    perform advanced layout analysis or table structure preservation.

    Capabilities:
    - Basic text extraction from PDFs
    - Page-by-page processing
    - Metadata extraction
    - Page markers for citation tracking

    Limitations:
    - No layout analysis (multi-column documents may be scrambled)
    - No table structure preservation
    - No OCR for scanned documents
    - No reading order detection
    """

    def __init__(self, config: ProcessorConfig):
        """
        Initialise the legacy processor.

        Args:
            config: Processor configuration
        """
        super().__init__(config)
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """
        Validate that required dependencies are available.

        Raises:
            ProcessorError: If dependencies are missing
        """
        try:
            import pymupdf  # noqa: F401
            import pymupdf4llm  # noqa: F401
        except ImportError as e:
            raise ProcessorError(
                "PyMuPDF dependencies required for legacy processor. "
                "Install with: pip install pymupdf pymupdf4llm"
            ) from e

    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process a PDF document using PyMuPDF.

        This implementation mirrors the original load_pdf function from
        src/ingestion/loaders.py to ensure backwards compatibility.

        Args:
            file_path: Path to PDF file

        Returns:
            ProcessedDocument with extracted content

        Raises:
            ProcessorError: If processing fails
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        self.validate_file(file_path)
        start_time = time.time()
        warnings = []

        try:
            import pymupdf as fitz
            import pymupdf4llm
        except ImportError as e:
            raise ProcessorError(f"Failed to import PyMuPDF: {e}") from e

        logger.debug(f"Processing PDF with legacy processor: {file_path}")

        try:
            # Open document to get metadata and page count
            doc = fitz.open(file_path)
            metadata = doc.metadata or {}
            page_count = len(doc)
            doc.close()

            # Extract text page by page with page markers
            pages_text = []
            for page_num in range(page_count):
                try:
                    # Extract markdown for this page only
                    page_md = pymupdf4llm.to_markdown(str(file_path), pages=[page_num])
                    # Add page marker before the page content
                    pages_text.append(f"<!-- PAGE {page_num + 1} -->\n{page_md}")
                except Exception as e:
                    warning = f"Failed to extract page {page_num + 1}: {e}"
                    logger.warning(warning)
                    warnings.append(warning)
                    # Add placeholder for failed page
                    pages_text.append(f"<!-- PAGE {page_num + 1} -->\n[Page extraction failed]")

            # Join all pages with double newlines
            md_text = "\n\n".join(pages_text)

            # Extract metadata
            title = metadata.get("title") or file_path.stem
            author = metadata.get("author")

            processing_time = time.time() - start_time
            logger.info(
                f"Processed PDF with legacy processor: "
                f"{page_count} pages, {len(md_text)} characters, "
                f"{processing_time:.2f}s"
            )

            return ProcessedDocument(
                content=md_text,
                tables=[],  # Legacy processor doesn't extract tables
                images=[],  # Legacy processor doesn't extract images
                metadata={
                    "page_count": page_count,
                    "title": title,
                    "author": author,
                    "processing_time": processing_time,
                    "warnings": warnings,
                    "format": "pdf",
                },
                confidence=0.8,  # Lower confidence for legacy processing
                processor_type="legacy",
            )

        except Exception as e:
            logger.error(f"Failed to process PDF with legacy processor: {e}")
            raise ProcessorError(f"Legacy processor failed: {e}") from e

    def supports_file_type(self, file_path: Path) -> bool:
        """
        Check if this processor supports the file type.

        Args:
            file_path: Path to file

        Returns:
            True if file is PDF, False otherwise
        """
        return file_path.suffix.lower() == ".pdf"

    def get_capabilities(self) -> dict[str, bool]:
        """
        Get capabilities of the legacy processor.

        Returns:
            Dictionary of capabilities (all False except basic text extraction)
        """
        return {
            "ocr": False,
            "tables": False,  # Tables extracted as unstructured text
            "layout_analysis": False,
            "reading_order": False,
            "images": False,
        }
