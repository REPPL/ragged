"""
Document processing module for ragged.

This module provides a plugin-based architecture for processing documents
with various processors (legacy pymupdf, Docling, future PaddleOCR, etc.).

v0.3.4b: Added intelligent routing with quality assessment

Usage:
    from src.processing import ProcessorFactory, ProcessorConfig

    config = ProcessorConfig(processor_type="docling")
    processor = ProcessorFactory.create(config)
    result = processor.process(Path("document.pdf"))

    # With routing (v0.3.4b)
    from src.processing import ProcessorRouter, RouterConfig

    router = ProcessorRouter(RouterConfig())
    route = router.route(Path("document.pdf"))
"""

from src.processing.base import (
    BaseProcessor,
    ProcessedDocument,
    ProcessorConfig,
    ProcessorError,
)
from src.processing.factory import ProcessorFactory
from src.processing.metrics import MetricsSummary, ProcessingMetrics, RoutingMetric
from src.processing.quality_assessor import PageQuality, QualityAssessment, QualityAssessor
from src.processing.router import ProcessingRoute, ProcessorRouter, RouterConfig

__all__ = [
    "BaseProcessor",
    "ProcessedDocument",
    "ProcessorConfig",
    "ProcessorError",
    "ProcessorFactory",
    # v0.3.4b: Intelligent Routing
    "QualityAssessment",
    "QualityAssessor",
    "PageQuality",
    "ProcessingRoute",
    "ProcessorRouter",
    "RouterConfig",
    "ProcessingMetrics",
    "RoutingMetric",
    "MetricsSummary",
]
