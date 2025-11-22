"""
Base processor interface and data models for document processing.

This module defines the abstract interface that all document processors must
implement, along with standardised data models for configuration and output.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProcessedDocument:
    """
    Standardised output format from all document processors.

    This format ensures consistent output regardless of which processor
    (legacy, Docling, etc.) is used for document processing.
    """

    content: str
    """Markdown-formatted text extracted from the document."""

    tables: list[dict[str, Any]] = field(default_factory=list)
    """
    Extracted tables with structure preserved.

    Each table is represented as a dictionary with:
    - 'data': List[List[str]] - Table cells in row-major order
    - 'headers': List[str] - Column headers (if detected)
    - 'page': int - Page number where table appears
    - 'confidence': float - Extraction confidence (0-1)
    """

    images: list[dict[str, Any]] = field(default_factory=list)
    """
    Extracted images with metadata.

    Each image is represented as a dictionary with:
    - 'data': bytes - Image binary data
    - 'format': str - Image format (png, jpg, etc.)
    - 'caption': Optional[str] - Image caption if detected
    - 'page': int - Page number where image appears
    """

    metadata: dict[str, Any] = field(default_factory=dict)
    """
    Processing metadata including:
    - 'page_count': int - Total number of pages
    - 'title': Optional[str] - Document title
    - 'author': Optional[str] - Document author
    - 'processing_time': float - Time taken to process (seconds)
    - 'warnings': List[str] - Any processing warnings
    """

    confidence: float = 1.0
    """Overall confidence score for the extraction (0-1)."""

    processor_type: str = "unknown"
    """Name of the processor used (e.g., 'docling', 'legacy')."""


@dataclass
class ProcessorConfig:
    """
    Configuration for document processors.

    This configuration is passed to all processors to control their behaviour.
    Different processors may use different subsets of these options.
    """

    processor_type: str = "docling"
    """
    Type of processor to use.

    Options:
    - 'docling': Use Docling for advanced document processing
    - 'legacy': Use legacy pymupdf processor
    """

    enable_table_extraction: bool = True
    """Whether to extract and preserve table structure."""

    enable_layout_analysis: bool = True
    """Whether to perform layout analysis (requires Docling)."""

    enable_ocr: bool = False
    """Whether to perform OCR on scanned documents (future feature)."""

    model_cache_dir: Path | None = None
    """Directory for caching ML models (Docling models, etc.)."""

    batch_size: int = 1
    """Number of pages to process in a batch."""

    options: dict[str, Any] = field(default_factory=dict)
    """Processor-specific options as key-value pairs."""


class ProcessorError(Exception):
    """Exception raised when document processing fails."""

    pass


class BaseProcessor(ABC):
    """
    Abstract base class for document processors.

    All document processors (legacy pymupdf, Docling, future PaddleOCR, etc.)
    must implement this interface to ensure consistent behaviour and easy
    substitution.
    """

    def __init__(self, config: ProcessorConfig):
        """
        Initialise the processor with configuration.

        Args:
            config: Processor configuration
        """
        self.config = config

    @abstractmethod
    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process a document and return structured content.

        This is the main method that all processors must implement.
        It should extract text, tables, images, and metadata from
        the document and return them in a standardised format.

        Args:
            file_path: Path to the document file

        Returns:
            ProcessedDocument with extracted content

        Raises:
            ProcessorError: If document cannot be processed
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        pass

    @abstractmethod
    def supports_file_type(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the given file type.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this processor supports the file type, False otherwise
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> dict[str, bool]:
        """
        Return the capabilities of this processor.

        This allows the system to choose the most appropriate processor
        for a given task based on required capabilities.

        Returns:
            Dictionary mapping capability names to boolean values:
            - 'ocr': Can perform OCR on scanned documents
            - 'tables': Can extract table structure
            - 'layout_analysis': Can analyse document layout
            - 'reading_order': Can preserve reading order
            - 'images': Can extract images
        """
        pass

    def validate_file(self, file_path: Path) -> None:
        """
        Validate that the file exists and is readable.

        Args:
            file_path: Path to validate

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            ValueError: If file type is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        if not file_path.stat().st_size:
            raise ValueError(f"File is empty: {file_path}")

        if not self.supports_file_type(file_path):
            raise ValueError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Processor '{self.config.processor_type}' cannot handle this format."
            )
