"""
Intelligent processor routing based on document quality assessment.

This module implements routing logic that selects the optimal document
processor and configuration based on quality assessment results. It enables
adaptive processing strategies that match document characteristics.

v0.3.4b: Intelligent Routing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from src.processing.base import BaseProcessor, ProcessorConfig
from src.processing.quality_assessor import QualityAssessment, QualityAssessor
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RouterConfig:
    """
    Configuration for processor routing.

    Attributes:
        high_quality_threshold: Quality score threshold for high-quality docs (0.85)
        low_quality_threshold: Quality score threshold for low-quality docs (0.70)
        prefer_docling: Prefer Docling processor when available
        enable_paddleocr_fallback: Enable PaddleOCR fallback (v0.3.4c feature)
        fast_quality_assessment: Use fast quality assessment mode
        cache_quality_assessments: Cache quality assessment results
        collect_metrics: Enable metrics collection
        metrics_retention_days: Days to retain metrics data
    """

    high_quality_threshold: float = 0.85
    low_quality_threshold: float = 0.70
    prefer_docling: bool = True
    enable_paddleocr_fallback: bool = False  # Future v0.3.4c
    fast_quality_assessment: bool = True
    cache_quality_assessments: bool = True
    collect_metrics: bool = True
    metrics_retention_days: int = 30


@dataclass
class ProcessingRoute:
    """
    Processing route decision with configuration and reasoning.

    This dataclass encapsulates the routing decision including which
    processor to use, how to configure it, and why.

    Attributes:
        processor: Name of processor to use ('docling', 'legacy', etc.)
        config: Processor configuration
        quality: Quality assessment that informed the decision
        reasoning: Human-readable explanation of routing decision
        estimated_time: Estimated processing time in seconds
        fallback_options: Alternative processors if primary fails
    """

    processor: str
    config: ProcessorConfig
    quality: QualityAssessment
    reasoning: str
    estimated_time: float = 0.0
    fallback_options: List[str] = field(default_factory=list)


class ProcessorRouter:
    """
    Route documents to optimal processors based on quality assessment.

    This router analyses document quality and characteristics to determine
    the best processing strategy. It selects appropriate processors and
    configures them based on quality scores, document type, and complexity.

    Example:
        >>> config = RouterConfig(
        ...     high_quality_threshold=0.85,
        ...     fast_quality_assessment=True
        ... )
        >>> router = ProcessorRouter(config)
        >>> router.register_processor("docling", docling_processor)
        >>> route = router.route(Path("document.pdf"))
        >>> print(f"Using {route.processor}: {route.reasoning}")
    """

    def __init__(self, config: Optional[RouterConfig] = None):
        """
        Initialise processor router.

        Args:
            config: Router configuration (defaults to RouterConfig())
        """
        self.config = config or RouterConfig()
        self._processors: Dict[str, BaseProcessor] = {}

        # Initialise quality assessor
        self.assessor = QualityAssessor(
            fast_mode=self.config.fast_quality_assessment,
            cache_enabled=self.config.cache_quality_assessments,
        )

        logger.debug(
            f"Processor router initialised: "
            f"high_threshold={self.config.high_quality_threshold}, "
            f"low_threshold={self.config.low_quality_threshold}"
        )

    def register_processor(self, name: str, processor: BaseProcessor) -> None:
        """
        Register a processor for routing.

        Args:
            name: Processor name (e.g., 'docling', 'legacy')
            processor: Processor instance
        """
        self._processors[name] = processor
        logger.debug(f"Registered processor: {name}")

    def route(self, file_path: Path) -> ProcessingRoute:
        """
        Determine optimal processing route for document.

        This method:
        1. Assesses document quality
        2. Selects appropriate processor
        3. Configures processor for document characteristics
        4. Provides reasoning for the decision

        Args:
            file_path: Path to document file

        Returns:
            Processing route with processor, config, and reasoning

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If no suitable processor available
        """
        logger.debug(f"Routing document: {file_path.name}")

        # Step 1: Assess quality
        quality = self.assessor.assess(file_path)

        # Step 2: Select processor
        processor_name = self._select_processor(quality)

        # Step 3: Configure processor
        processor_config = self._configure_processor(quality)

        # Step 4: Generate reasoning
        reasoning = self._explain_routing(quality, processor_name, processor_config)

        # Step 5: Estimate processing time
        estimated_time = self._estimate_processing_time(quality)

        # Step 6: Determine fallback options
        fallback_options = self._determine_fallbacks(processor_name)

        route = ProcessingRoute(
            processor=processor_name,
            config=processor_config,
            quality=quality,
            reasoning=reasoning,
            estimated_time=estimated_time,
            fallback_options=fallback_options,
        )

        logger.info(
            f"Routing decision: {processor_name} "
            f"(quality={quality.overall_score:.2f}, "
            f"born_digital={quality.is_born_digital})"
        )
        logger.debug(f"Routing reasoning: {reasoning}")

        return route

    def _select_processor(self, quality: QualityAssessment) -> str:
        """
        Select processor based on quality assessment.

        v0.3.4b: Always use Docling (PaddleOCR in v0.3.4c)

        Args:
            quality: Quality assessment

        Returns:
            Processor name
        """
        # v0.3.4b: Docling for all documents
        # Future v0.3.4c: Route to PaddleOCR for low-quality scanned docs

        if self.config.prefer_docling:
            return "docling"

        # Fallback to legacy if Docling not preferred
        return "legacy"

    def _configure_processor(self, quality: QualityAssessment) -> ProcessorConfig:
        """
        Configure processor based on quality assessment.

        Adjusts configuration parameters based on:
        - Quality score (high/medium/low)
        - Document type (born-digital vs scanned)
        - Complexity (tables, rotated content, etc.)

        Args:
            quality: Quality assessment

        Returns:
            Processor configuration optimised for document
        """
        # Base configuration
        config = ProcessorConfig(
            processor_type="docling",
            enable_table_extraction=quality.has_tables,
            enable_layout_analysis=True,
        )

        # Adjust based on quality tier
        if quality.overall_score >= self.config.high_quality_threshold:
            # High quality: standard processing
            config.options = {
                "processing_mode": "standard",
                "quality_tier": "high",
            }

        elif quality.overall_score >= self.config.low_quality_threshold:
            # Medium quality: more aggressive processing
            config.options = {
                "processing_mode": "aggressive",
                "quality_tier": "medium",
            }

        else:
            # Low quality: maximum effort
            config.options = {
                "processing_mode": "maximum_effort",
                "quality_tier": "low",
            }

        # Adjust for scanned documents
        if quality.is_scanned:
            config.options["scanned_document"] = True
            config.options["image_quality"] = quality.image_quality

        # Adjust for complex layouts
        if quality.layout_complexity > 0.7:
            config.options["complex_layout"] = True
            config.enable_layout_analysis = True

        # Adjust for rotated content
        if quality.has_rotated_content:
            config.options["has_rotated_content"] = True

        logger.debug(
            f"Configured processor: "
            f"quality_tier={config.options.get('quality_tier', 'unknown')}, "
            f"mode={config.options.get('processing_mode', 'standard')}"
        )

        return config

    def _explain_routing(
        self,
        quality: QualityAssessment,
        processor_name: str,
        config: ProcessorConfig,
    ) -> str:
        """
        Generate human-readable explanation of routing decision.

        Args:
            quality: Quality assessment
            processor_name: Selected processor
            config: Processor configuration

        Returns:
            Reasoning explanation
        """
        parts = []

        # Document type
        if quality.is_born_digital:
            parts.append("born-digital document")
        else:
            parts.append("scanned document")

        # Quality tier
        quality_tier = config.options.get("quality_tier", "unknown")
        parts.append(f"{quality_tier} quality ({quality.overall_score:.2f})")

        # Complexity
        if quality.layout_complexity > 0.7:
            parts.append("complex layout")
        if quality.has_tables:
            parts.append("contains tables")
        if quality.has_rotated_content:
            parts.append("has rotated content")

        # Processor selection
        mode = config.options.get("processing_mode", "standard")
        parts.append(f"using {processor_name} with {mode} mode")

        return "Detected " + ", ".join(parts) + "."

    def _estimate_processing_time(self, quality: QualityAssessment) -> float:
        """
        Estimate processing time based on document characteristics.

        Args:
            quality: Quality assessment

        Returns:
            Estimated time in seconds
        """
        # Base time per page
        base_time_per_page = 1.0  # seconds

        # Adjust for quality
        if quality.overall_score < self.config.low_quality_threshold:
            base_time_per_page *= 1.5  # Low quality takes longer

        # Adjust for complexity
        if quality.layout_complexity > 0.7:
            base_time_per_page *= 1.2

        if quality.has_tables:
            base_time_per_page *= 1.3

        # Calculate total
        total_pages = quality.metadata.get("total_pages", 1)
        estimated_time = base_time_per_page * total_pages

        return estimated_time

    def _determine_fallbacks(self, primary_processor: str) -> List[str]:
        """
        Determine fallback processors if primary fails.

        Args:
            primary_processor: Primary processor name

        Returns:
            List of fallback processor names
        """
        # v0.3.4b: Simple fallback chain
        if primary_processor == "docling":
            return ["legacy"]
        elif primary_processor == "legacy":
            return []
        else:
            return ["docling", "legacy"]

    def get_available_processors(self) -> List[str]:
        """
        Get list of registered processors.

        Returns:
            List of processor names
        """
        return list(self._processors.keys())

    def clear_cache(self) -> None:
        """Clear quality assessment cache."""
        self.assessor.clear_cache()
        logger.debug("Router cache cleared")
