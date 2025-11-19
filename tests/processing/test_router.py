"""
Tests for processor routing module.

Tests cover:
- Processor selection based on quality
- Configuration adjustment
- Routing explanation
- Fallback options
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.processing.base import ProcessorConfig
from src.processing.quality_assessor import QualityAssessment
from src.processing.router import ProcessingRoute, ProcessorRouter, RouterConfig


@pytest.fixture
def router_config():
    """Create router configuration."""
    return RouterConfig(
        high_quality_threshold=0.85,
        low_quality_threshold=0.70,
        prefer_docling=True,
        fast_quality_assessment=True,
    )


@pytest.fixture
def router(router_config):
    """Create processor router."""
    return ProcessorRouter(router_config)


@pytest.fixture
def high_quality_assessment():
    """Create high-quality assessment."""
    return QualityAssessment(
        overall_score=0.90,
        is_born_digital=True,
        is_scanned=False,
        text_quality=0.95,
        layout_complexity=0.2,
        image_quality=0.0,
        has_tables=False,
        has_rotated_content=False,
        metadata={"file_name": "test.pdf", "total_pages": 10},
    )


@pytest.fixture
def medium_quality_assessment():
    """Create medium-quality assessment."""
    return QualityAssessment(
        overall_score=0.75,
        is_born_digital=False,
        is_scanned=True,
        text_quality=0.75,
        layout_complexity=0.5,
        image_quality=0.70,
        has_tables=True,
        has_rotated_content=False,
        metadata={"file_name": "test.pdf", "total_pages": 20},
    )


@pytest.fixture
def low_quality_assessment():
    """Create low-quality assessment."""
    return QualityAssessment(
        overall_score=0.60,
        is_born_digital=False,
        is_scanned=True,
        text_quality=0.60,
        layout_complexity=0.8,
        image_quality=0.55,
        has_tables=True,
        has_rotated_content=True,
        metadata={"file_name": "test.pdf", "total_pages": 50},
    )


class TestRouterConfig:
    """Test RouterConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RouterConfig()

        assert config.high_quality_threshold == 0.85
        assert config.low_quality_threshold == 0.70
        assert config.prefer_docling is True
        assert config.enable_paddleocr_fallback is False
        assert config.fast_quality_assessment is True
        assert config.cache_quality_assessments is True


class TestProcessingRoute:
    """Test ProcessingRoute dataclass."""

    def test_route_creation(self, high_quality_assessment):
        """Test processing route creation."""
        config = ProcessorConfig(processor_type="docling")

        route = ProcessingRoute(
            processor="docling",
            config=config,
            quality=high_quality_assessment,
            reasoning="Test reasoning",
            estimated_time=5.0,
            fallback_options=["legacy"],
        )

        assert route.processor == "docling"
        assert route.config.processor_type == "docling"
        assert route.quality.overall_score == 0.90
        assert route.reasoning == "Test reasoning"
        assert route.estimated_time == 5.0
        assert "legacy" in route.fallback_options


class TestProcessorRouter:
    """Test ProcessorRouter class."""

    def test_init(self, router_config):
        """Test router initialisation."""
        router = ProcessorRouter(router_config)

        assert router.config == router_config
        assert router.assessor is not None
        assert router.assessor.fast_mode is True

    def test_init_default_config(self):
        """Test router initialisation with default config."""
        router = ProcessorRouter()

        assert router.config.high_quality_threshold == 0.85
        assert router.config.low_quality_threshold == 0.70

    def test_register_processor(self, router):
        """Test processor registration."""
        mock_processor = Mock()

        router.register_processor("docling", mock_processor)

        assert "docling" in router._processors
        assert router._processors["docling"] == mock_processor

    def test_select_processor_prefers_docling(self, router, high_quality_assessment):
        """Test processor selection prefers Docling."""
        processor = router._select_processor(high_quality_assessment)
        assert processor == "docling"

    def test_configure_processor_high_quality(self, router, high_quality_assessment):
        """Test processor configuration for high-quality document."""
        config = router._configure_processor(high_quality_assessment)

        assert config.processor_type == "docling"
        assert config.enable_layout_analysis is True
        assert config.enable_table_extraction is False  # No tables
        assert config.options["quality_tier"] == "high"
        assert config.options["processing_mode"] == "standard"

    def test_configure_processor_medium_quality(self, router, medium_quality_assessment):
        """Test processor configuration for medium-quality document."""
        config = router._configure_processor(medium_quality_assessment)

        assert config.options["quality_tier"] == "medium"
        assert config.options["processing_mode"] == "aggressive"
        assert config.enable_table_extraction is True  # Has tables
        assert config.options["scanned_document"] is True

    def test_configure_processor_low_quality(self, router, low_quality_assessment):
        """Test processor configuration for low-quality document."""
        config = router._configure_processor(low_quality_assessment)

        assert config.options["quality_tier"] == "low"
        assert config.options["processing_mode"] == "maximum_effort"
        assert config.options["scanned_document"] is True
        assert config.options["complex_layout"] is True  # High complexity
        assert config.options["has_rotated_content"] is True

    def test_explain_routing_born_digital(self, router, high_quality_assessment):
        """Test routing explanation for born-digital document."""
        config = router._configure_processor(high_quality_assessment)
        reasoning = router._explain_routing(high_quality_assessment, "docling", config)

        assert "born-digital" in reasoning.lower()
        assert "high quality" in reasoning.lower()
        assert "docling" in reasoning.lower()

    def test_explain_routing_scanned_complex(self, router, low_quality_assessment):
        """Test routing explanation for scanned complex document."""
        config = router._configure_processor(low_quality_assessment)
        reasoning = router._explain_routing(low_quality_assessment, "docling", config)

        assert "scanned" in reasoning.lower()
        assert "low quality" in reasoning.lower()
        assert "complex layout" in reasoning.lower()
        assert "contains tables" in reasoning.lower()
        assert "rotated content" in reasoning.lower()

    def test_estimate_processing_time_simple(self, router, high_quality_assessment):
        """Test processing time estimation for simple document."""
        time_estimate = router._estimate_processing_time(high_quality_assessment)

        # 10 pages * 1.0s base = 10s
        assert time_estimate > 0
        assert time_estimate < 20  # Should be reasonable

    def test_estimate_processing_time_complex(self, router, low_quality_assessment):
        """Test processing time estimation for complex document."""
        time_estimate = router._estimate_processing_time(low_quality_assessment)

        # 50 pages * adjustments for quality, complexity, tables
        assert time_estimate > 50  # More than simple 1s/page

    def test_determine_fallbacks_docling(self, router):
        """Test fallback determination for Docling."""
        fallbacks = router._determine_fallbacks("docling")
        assert fallbacks == ["legacy"]

    def test_determine_fallbacks_legacy(self, router):
        """Test fallback determination for legacy."""
        fallbacks = router._determine_fallbacks("legacy")
        assert fallbacks == []

    def test_route_high_quality(self, router, high_quality_assessment, tmp_path):
        """Test routing for high-quality document."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        # Mock quality assessment
        with patch.object(router.assessor, "assess", return_value=high_quality_assessment):
            route = router.route(test_file)

            assert isinstance(route, ProcessingRoute)
            assert route.processor == "docling"
            assert route.quality.overall_score == 0.90
            assert route.config.options["quality_tier"] == "high"
            assert len(route.reasoning) > 0
            assert route.estimated_time > 0

    def test_route_low_quality(self, router, low_quality_assessment, tmp_path):
        """Test routing for low-quality document."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        with patch.object(router.assessor, "assess", return_value=low_quality_assessment):
            route = router.route(test_file)

            assert route.processor == "docling"
            assert route.config.options["quality_tier"] == "low"
            assert route.config.options["processing_mode"] == "maximum_effort"

    def test_get_available_processors(self, router):
        """Test getting available processors."""
        mock_processor1 = Mock()
        mock_processor2 = Mock()

        router.register_processor("docling", mock_processor1)
        router.register_processor("legacy", mock_processor2)

        processors = router.get_available_processors()

        assert "docling" in processors
        assert "legacy" in processors
        assert len(processors) == 2

    def test_clear_cache(self, router):
        """Test cache clearing."""
        with patch.object(router.assessor, "clear_cache") as mock_clear:
            router.clear_cache()
            mock_clear.assert_called_once()


class TestIntegration:
    """Integration tests for routing."""

    @patch("src.processing.router.QualityAssessor")
    def test_full_routing_workflow(self, mock_assessor_class, tmp_path):
        """Test complete routing workflow."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        # Create quality assessment
        quality = QualityAssessment(
            overall_score=0.78,
            is_born_digital=False,
            is_scanned=True,
            text_quality=0.75,
            layout_complexity=0.6,
            image_quality=0.70,
            has_tables=True,
            has_rotated_content=False,
            metadata={
                "file_name": "test.pdf",
                "file_size": 1024,
                "total_pages": 15,
            },
        )

        # Mock assessor
        mock_assessor = Mock()
        mock_assessor.assess.return_value = quality
        mock_assessor_class.return_value = mock_assessor

        # Create router and route
        config = RouterConfig(
            high_quality_threshold=0.85,
            low_quality_threshold=0.70,
        )
        router = ProcessorRouter(config)
        route = router.route(test_file)

        # Verify routing decision
        assert route.processor == "docling"
        assert route.quality == quality
        assert route.config.options["quality_tier"] == "medium"
        assert route.config.enable_table_extraction is True
        assert "scanned" in route.reasoning.lower()
        assert route.estimated_time > 0
        assert "legacy" in route.fallback_options
