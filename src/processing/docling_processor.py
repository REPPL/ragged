"""
Docling-based document processor for state-of-the-art document processing.

This processor uses IBM Research's Docling framework for advanced document
processing with layout analysis, table extraction, and reading order preservation.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.processing.base import BaseProcessor, ProcessedDocument, ProcessorConfig, ProcessorError
from src.processing.model_manager import ModelManager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DoclingProcessor(BaseProcessor):
    """
    Advanced document processor using Docling framework.

    This processor leverages IBM Research's Docling for state-of-the-art
    document processing, achieving 30× faster processing and 97%+ table
    extraction accuracy compared to legacy approaches.

    Capabilities:
    - DocLayNet model for layout analysis
    - TableFormer for table structure extraction
    - Reading order preservation
    - Multi-column layout handling
    - Structured markdown output

    Performance:
    - 30× faster than Tesseract-based OCR
    - 97%+ table extraction accuracy
    - Proper reading order for complex layouts
    - Memory efficient (lazy model loading)

    Example:
        >>> config = ProcessorConfig(
        ...     processor_type="docling",
        ...     enable_layout_analysis=True,
        ...     enable_table_extraction=True
        ... )
        >>> processor = DoclingProcessor(config)
        >>> result = processor.process(Path("document.pdf"))
    """

    def __init__(self, config: ProcessorConfig):
        """
        Initialise the Docling processor.

        Args:
            config: Processor configuration

        Raises:
            ProcessorError: If Docling dependencies are not available
        """
        super().__init__(config)
        self._validate_dependencies()

        # Initialise model manager for lazy loading
        self.model_manager = ModelManager(config.model_cache_dir)

        # Pipeline is created lazily on first use
        self._pipeline: Optional[Any] = None

        logger.debug("Docling processor initialised")

    def _validate_dependencies(self) -> None:
        """
        Validate that Docling dependencies are available.

        Raises:
            ProcessorError: If Docling is not installed
        """
        try:
            import docling  # noqa: F401
            import docling_core  # noqa: F401
        except ImportError as e:
            raise ProcessorError(
                "Docling is required for this processor. "
                "Install with: pip install docling docling-core docling-parse"
            ) from e

    @property
    def pipeline(self) -> Any:
        """
        Get or create the Docling pipeline (lazy initialisation).

        The pipeline is created on first access to avoid loading models
        until they're actually needed.

        Returns:
            Configured Docling pipeline ready for processing

        Raises:
            ProcessorError: If pipeline creation fails
        """
        if self._pipeline is not None:
            return self._pipeline

        logger.info("Initialising Docling pipeline...")

        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            # Configure pipeline options
            pipeline_options = PdfPipelineOptions()

            # Enable table extraction if configured
            if self.config.enable_table_extraction:
                pipeline_options.do_table_structure = True
                logger.debug("Table extraction enabled")
            else:
                pipeline_options.do_table_structure = False

            # Configure document converter
            self._pipeline = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )

            logger.info("Docling pipeline initialised successfully")
            return self._pipeline

        except Exception as e:
            logger.error(f"Failed to initialise Docling pipeline: {e}")
            raise ProcessorError(f"Pipeline initialisation failed: {e}") from e

    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process a PDF document using Docling.

        This method uses Docling's advanced processing pipeline to extract
        text, tables, and metadata with proper layout analysis and reading
        order preservation.

        Args:
            file_path: Path to PDF file

        Returns:
            ProcessedDocument with extracted content and metadata

        Raises:
            ProcessorError: If processing fails
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        self.validate_file(file_path)
        start_time = time.time()
        warnings = []

        logger.debug(f"Processing PDF with Docling: {file_path}")

        # HIGH-002: Add processing timeout
        from src.config.settings import get_settings
        settings = get_settings()

        # Use processing timeout if configured
        timeout_seconds = getattr(settings, 'processing_timeout_seconds', 300)  # Default 5 minutes

        try:
            # Wrap processing in timeout using concurrent.futures
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

            def _do_processing():
                # Convert document using Docling
                result = self.pipeline.convert(str(file_path))
                return result

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_processing)
                try:
                    result = future.result(timeout=timeout_seconds)
                except FuturesTimeoutError:
                    raise ProcessorError(
                        f"Processing timeout after {timeout_seconds}s. "
                        f"Document may be too complex or corrupted."
                    )

            # Extract markdown content
            md_text = result.document.export_to_markdown()

            # Add page markers for citation tracking
            md_text_with_markers = self._add_page_markers(md_text, result)

            # Extract tables
            tables = self._extract_tables(result)

            # Extract images (if available)
            images = self._extract_images(result)

            # Extract metadata
            metadata = self._extract_metadata(result, file_path)

            # Calculate confidence score
            confidence = self._calculate_confidence(result)

            processing_time = time.time() - start_time
            page_count = metadata.get("page_count", 0)

            logger.info(
                f"Processed PDF with Docling: "
                f"{page_count} pages, {len(md_text_with_markers)} characters, "
                f"{len(tables)} tables extracted, "
                f"{processing_time:.2f}s"
            )

            metadata["processing_time"] = processing_time
            metadata["warnings"] = warnings

            return ProcessedDocument(
                content=md_text_with_markers,
                tables=tables,
                images=images,
                metadata=metadata,
                confidence=confidence,
                processor_type="docling",
            )

        except Exception as e:
            logger.error(f"Failed to process PDF with Docling: {e}")
            raise ProcessorError(f"Docling processing failed: {e}") from e

    def _add_page_markers(self, markdown: str, result: Any) -> str:
        """
        Add page markers to markdown for citation tracking.

        Args:
            markdown: Original markdown text
            result: Docling conversion result

        Returns:
            Markdown with page markers inserted
        """
        # For now, we'll try to infer page breaks from the document structure
        # This is a simplified implementation - Docling may provide better
        # page boundary information in the result object

        try:
            # Check if result has page information
            if hasattr(result, "document") and hasattr(result.document, "pages"):
                pages = result.document.pages
                page_count = len(pages)

                # Add page markers based on page count
                # This is a simple heuristic - split content roughly by page
                lines = markdown.split("\n")
                lines_per_page = max(1, len(lines) // page_count) if page_count > 0 else len(lines)

                marked_lines = []
                for i, line in enumerate(lines):
                    page_num = (i // lines_per_page) + 1
                    if i % lines_per_page == 0 and page_num <= page_count:
                        marked_lines.append(f"<!-- PAGE {page_num} -->")
                    marked_lines.append(line)

                return "\n".join(marked_lines)

        except Exception as e:
            logger.debug(f"Could not add page markers: {e}")

        # Fallback: return original markdown
        return markdown

    def _extract_tables(self, result: Any) -> List[Dict[str, Any]]:
        """
        Extract tables from Docling result.

        Args:
            result: Docling conversion result

        Returns:
            List of table dictionaries with structure preserved
        """
        tables = []

        try:
            if hasattr(result, "document") and hasattr(result.document, "tables"):
                for idx, table in enumerate(result.document.tables):
                    table_dict = {
                        "index": idx,
                        "data": self._table_to_rows(table),
                        "headers": self._extract_table_headers(table),
                        "page": getattr(table, "page", -1),
                        "confidence": getattr(table, "confidence", 1.0),
                    }
                    tables.append(table_dict)

                logger.debug(f"Extracted {len(tables)} tables")

        except Exception as e:
            logger.warning(f"Failed to extract tables: {e}")

        return tables

    def _table_to_rows(self, table: Any) -> List[List[str]]:
        """
        Convert Docling table to row-major list of lists.

        Args:
            table: Docling table object

        Returns:
            List of rows, each row is a list of cell values
        """
        try:
            # This is a simplified implementation
            # Actual implementation depends on Docling's table structure
            if hasattr(table, "to_list"):
                return table.to_list()
            elif hasattr(table, "data"):
                return table.data
            else:
                return []
        except Exception as e:
            logger.debug(f"Failed to convert table to rows: {e}")
            return []

    def _extract_table_headers(self, table: Any) -> List[str]:
        """
        Extract table headers if available.

        Args:
            table: Docling table object

        Returns:
            List of header strings
        """
        try:
            if hasattr(table, "headers"):
                return table.headers
            elif hasattr(table, "data") and len(table.data) > 0:
                # First row might be headers
                return table.data[0]
            else:
                return []
        except Exception as e:
            logger.debug(f"Failed to extract table headers: {e}")
            return []

    def _extract_images(self, result: Any) -> List[Dict[str, Any]]:
        """
        Extract images from Docling result.

        Args:
            result: Docling conversion result

        Returns:
            List of image dictionaries with metadata
        """
        images = []

        try:
            if hasattr(result, "document") and hasattr(result.document, "images"):
                for idx, image in enumerate(result.document.images):
                    image_dict = {
                        "index": idx,
                        "format": getattr(image, "format", "unknown"),
                        "caption": getattr(image, "caption", None),
                        "page": getattr(image, "page", -1),
                    }
                    # Don't include binary data by default (can be large)
                    # Only include reference/metadata
                    images.append(image_dict)

                logger.debug(f"Found {len(images)} images")

        except Exception as e:
            logger.debug(f"Failed to extract images: {e}")

        return images

    def _extract_metadata(self, result: Any, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from Docling result.

        Args:
            result: Docling conversion result
            file_path: Original file path

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "format": "pdf",
            "title": file_path.stem,
        }

        try:
            if hasattr(result, "document"):
                doc = result.document

                # Page count
                if hasattr(doc, "pages"):
                    metadata["page_count"] = len(doc.pages)

                # Document metadata
                if hasattr(doc, "metadata"):
                    doc_meta = doc.metadata
                    if hasattr(doc_meta, "title"):
                        metadata["title"] = doc_meta.title or file_path.stem
                    if hasattr(doc_meta, "author"):
                        metadata["author"] = doc_meta.author

        except Exception as e:
            logger.debug(f"Failed to extract some metadata: {e}")

        return metadata

    def _calculate_confidence(self, result: Any) -> float:
        """
        Calculate overall confidence score for the extraction.

        Args:
            result: Docling conversion result

        Returns:
            Confidence score between 0 and 1
        """
        # Default high confidence for Docling
        # In the future, this could aggregate confidence scores from
        # individual elements (tables, text blocks, etc.)
        return 0.95

    def validate_file(self, file_path: Path) -> None:
        """
        Validate file with Docling-specific security checks.

        Adds file size and MIME type validation to base validation.

        Args:
            file_path: Path to validate

        Raises:
            FileNotFoundError: If file doesn't exist
            SecurityError: If file fails security checks
            ValueError: If file type is not supported
        """
        # Call parent validation (existence, type, empty check)
        super().validate_file(file_path)

        # CRITICAL-001: Add file size validation
        from src.utils.security import validate_file_size, SecurityError
        from src.config.settings import get_settings

        settings = get_settings()
        try:
            validate_file_size(file_path, max_size_mb=settings.max_file_size_mb)
        except SecurityError as e:
            raise ValueError(f"File size validation failed: {e}") from e

        # HIGH-001: Add MIME type verification (magic bytes check)
        from src.utils.security import validate_mime_type

        try:
            mime_type = validate_mime_type(file_path, expected_types=["application/pdf"])
            logger.debug(f"Validated MIME type: {mime_type} for {file_path.name}")
        except SecurityError as e:
            raise ValueError(
                f"File does not appear to be a valid PDF (detected type issue). "
                f"Please ensure you're uploading an actual PDF file, not a renamed file."
            ) from e

    def supports_file_type(self, file_path: Path) -> bool:
        """
        Check if this processor supports the file type.

        Args:
            file_path: Path to file

        Returns:
            True if file is PDF, False otherwise
        """
        return file_path.suffix.lower() == ".pdf"

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get capabilities of the Docling processor.

        Returns:
            Dictionary of capabilities
        """
        return {
            "ocr": False,  # Not in v0.3.4a (requires v0.3.4c with PaddleOCR)
            "tables": self.config.enable_table_extraction,
            "layout_analysis": self.config.enable_layout_analysis,
            "reading_order": True,
            "images": True,
        }
