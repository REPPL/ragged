"""
Document processing module for ragged.

This module provides a plugin-based architecture for processing documents
with various processors (legacy pymupdf, Docling, future PaddleOCR, etc.).

Usage:
    from src.processing import ProcessorFactory, ProcessorConfig

    config = ProcessorConfig(processor_type="docling")
    processor = ProcessorFactory.create(config)
    result = processor.process(Path("document.pdf"))
"""

from src.processing.base import (
    BaseProcessor,
    ProcessedDocument,
    ProcessorConfig,
    ProcessorError,
)
from src.processing.factory import ProcessorFactory

__all__ = [
    "BaseProcessor",
    "ProcessedDocument",
    "ProcessorConfig",
    "ProcessorError",
    "ProcessorFactory",
]
