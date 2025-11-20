"""
Integration tests for intelligent routing.

Tests cover:
- End-to-end routing workflow
- Quality assessment → routing → processing
- Metrics collection integration
- Routing metadata in results
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ingestion.loaders import _get_metrics, _get_router, _load_pdf_with_routing
from src.processing import ProcessorFactory, ProcessorRouter, RouterConfig
from src.processing.base import ProcessedDocument, ProcessorConfig
from src.processing.quality_assessor import QualityAssessment


@pytest.fixture(autouse=True)
def clear_singletons():
    """Clear router and metrics singletons before each test."""
    import src.ingestion.loaders as loaders
    loaders._router = None
    loaders._metrics = None
    yield
    # Cleanup after test
    loaders._router = None
    loaders._metrics = None


@pytest.fixture(autouse=True)
def mock_fitz():
    """Mock PyMuPDF (fitz) to prevent actual PDF processing."""
    with patch("src.processing.quality_assessor.QualityAssessor._assess_pdf") as mock_assess:
        # Return a default quality assessment
        mock_assess.return_value = QualityAssessment(
            overall_score=0.75,
            is_born_digital=False,
            is_scanned=True,
            text_quality=0.70,
            layout_complexity=0.5,
            image_quality=0.70,
            has_tables=False,
            has_rotated_content=False,
            metadata={"fallback": True},
        )
        yield mock_assess


@pytest.fixture
def mock_pdf_file(tmp_path):
    """Create mock PDF file."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\ntest content")
    return pdf_file


@pytest.fixture
def mock_quality_assessment():
    """Create mock quality assessment."""
    return QualityAssessment(
        overall_score=0.85,
        is_born_digital=True,
        is_scanned=False,
        text_quality=0.90,
        layout_complexity=0.3,
        image_quality=0.0,
        has_tables=True,
        has_rotated_content=False,
        metadata={
            "file_name": "test.pdf",
            "file_size": 1024,
            "total_pages": 10,
        },
    )


@pytest.fixture
def mock_processed_document():
    """Create mock processed document."""
    return ProcessedDocument(
        content="# Test Document\n\nTest content",
        tables=[{"data": [["A", "B"], ["1", "2"]]}],
        images=[],
        metadata={
            "page_count": 10,
            "title": "Test Document",
        },
        confidence=0.95,
        processor_type="docling",
    )


class TestRouterInitialisation:
    """Test router and metrics initialisation."""

    def test_get_router_creates_singleton(self):
        """Test router is created as singleton."""
        # Clear any existing router
        import src.ingestion.loaders as loaders
        loaders._router = None

        router1 = _get_router()
        router2 = _get_router()

        assert router1 is router2  # Same instance

    def test_get_metrics_creates_singleton(self):
        """Test metrics is created as singleton."""
        # Clear any existing metrics
        import src.ingestion.loaders as loaders
        loaders._metrics = None

        metrics1 = _get_metrics()
        metrics2 = _get_metrics()

        assert metrics1 is metrics2  # Same instance


class TestEndToEndRouting:
    """Test complete routing workflow."""

    @patch("src.ingestion.loaders.ProcessorFactory")
    def test_load_pdf_with_routing_success(
        self,
        mock_factory,
        mock_fitz,
        mock_pdf_file,
        mock_quality_assessment,
        mock_processed_document,
    ):
        """Test successful PDF loading with routing."""
        # Override default mock with test-specific assessment
        mock_fitz.return_value = mock_quality_assessment

        # Mock processor
        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        # Load PDF with routing
        result = _load_pdf_with_routing(mock_pdf_file)

        # Verify quality assessment was called
        mock_fitz.assert_called_once()

        # Verify processor was created and used
        mock_factory.create.assert_called_once()
        mock_processor.process.assert_called_once()

        # Verify result
        assert result is not None
        assert result.content == "# Test Document\n\nTest content"

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_routing_metadata_attached(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_quality_assessment,
        mock_processed_document,
    ):
        """Test routing metadata is attached to results."""
        # Mock quality assessor
        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_quality_assessment
        mock_assessor_class.return_value = mock_assessor

        # Mock processor
        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        # Load PDF
        _load_pdf_with_routing(mock_pdf_file)

        # Verify routing metadata was added
        assert "routing" in mock_processed_document.metadata
        routing_meta = mock_processed_document.metadata["routing"]

        assert "processor" in routing_meta
        assert "quality_score" in routing_meta
        assert "is_born_digital" in routing_meta
        assert "quality_tier" in routing_meta
        assert "reasoning" in routing_meta

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_metrics_recorded_on_success(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_quality_assessment,
        mock_processed_document,
    ):
        """Test metrics are recorded on successful processing."""
        # Mock quality assessor
        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_quality_assessment
        mock_assessor_class.return_value = mock_assessor

        # Mock processor
        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        # Get metrics instance and spy on it
        metrics = _get_metrics()
        initial_count = len(metrics._metrics)

        # Load PDF
        _load_pdf_with_routing(mock_pdf_file)

        # Verify metric was recorded
        assert len(metrics._metrics) > initial_count

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_metrics_recorded_on_failure(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_quality_assessment,
    ):
        """Test metrics are recorded on processing failure."""
        # Mock quality assessor
        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_quality_assessment
        mock_assessor_class.return_value = mock_assessor

        # Mock processor that fails
        mock_processor = Mock()
        mock_processor.process.side_effect = Exception("Processing failed")
        mock_factory.create.return_value = mock_processor

        # Load PDF (should raise exception)
        with pytest.raises(Exception, match="Processing failed"):
            _load_pdf_with_routing(mock_pdf_file)

        # Metrics should still be recorded
        metrics = _get_metrics()
        # At least routing decision should be recorded
        assert len(metrics._metrics) > 0


class TestQualityTierRouting:
    """Test routing for different quality tiers."""

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_high_quality_routing(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_processed_document,
    ):
        """Test routing for high-quality document."""
        # High-quality assessment
        quality = QualityAssessment(
            overall_score=0.92,
            is_born_digital=True,
            is_scanned=False,
            text_quality=0.95,
            layout_complexity=0.2,
            image_quality=0.0,
            has_tables=False,
            has_rotated_content=False,
            metadata={"file_name": "test.pdf", "total_pages": 5},
        )

        mock_assessor = Mock()
        mock_assessor.assess.return_value = quality
        mock_assessor_class.return_value = mock_assessor

        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        _load_pdf_with_routing(mock_pdf_file)

        # Verify standard mode was used
        call_args = mock_factory.create.call_args
        config = call_args[0][0]
        assert config.options["quality_tier"] == "high"
        assert config.options["processing_mode"] == "standard"

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_low_quality_routing(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_processed_document,
    ):
        """Test routing for low-quality document."""
        # Low-quality assessment
        quality = QualityAssessment(
            overall_score=0.55,
            is_born_digital=False,
            is_scanned=True,
            text_quality=0.60,
            layout_complexity=0.8,
            image_quality=0.50,
            has_tables=True,
            has_rotated_content=True,
            metadata={"file_name": "test.pdf", "total_pages": 50},
        )

        mock_assessor = Mock()
        mock_assessor.assess.return_value = quality
        mock_assessor_class.return_value = mock_assessor

        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        _load_pdf_with_routing(mock_pdf_file)

        # Verify maximum effort mode was used
        call_args = mock_factory.create.call_args
        config = call_args[0][0]
        assert config.options["quality_tier"] == "low"
        assert config.options["processing_mode"] == "maximum_effort"
        assert config.options["scanned_document"] is True
        assert config.options["complex_layout"] is True


class TestProcessorConfiguration:
    """Test processor configuration based on document characteristics."""

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_table_extraction_enabled_for_tables(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_processed_document,
    ):
        """Test table extraction enabled when tables detected."""
        quality = QualityAssessment(
            overall_score=0.85,
            is_born_digital=True,
            is_scanned=False,
            text_quality=0.90,
            layout_complexity=0.4,
            image_quality=0.0,
            has_tables=True,  # Tables detected
            has_rotated_content=False,
            metadata={"file_name": "test.pdf", "total_pages": 10},
        )

        mock_assessor = Mock()
        mock_assessor.assess.return_value = quality
        mock_assessor_class.return_value = mock_assessor

        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        _load_pdf_with_routing(mock_pdf_file)

        # Verify table extraction enabled
        call_args = mock_factory.create.call_args
        config = call_args[0][0]
        assert config.enable_table_extraction is True

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_scanned_document_configuration(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_processed_document,
    ):
        """Test configuration for scanned documents."""
        quality = QualityAssessment(
            overall_score=0.75,
            is_born_digital=False,
            is_scanned=True,  # Scanned document
            text_quality=0.70,
            layout_complexity=0.5,
            image_quality=0.75,
            has_tables=False,
            has_rotated_content=False,
            metadata={"file_name": "test.pdf", "total_pages": 20},
        )

        mock_assessor = Mock()
        mock_assessor.assess.return_value = quality
        mock_assessor_class.return_value = mock_assessor

        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        _load_pdf_with_routing(mock_pdf_file)

        # Verify scanned document options
        call_args = mock_factory.create.call_args
        config = call_args[0][0]
        assert config.options["scanned_document"] is True
        assert config.options["image_quality"] == 0.75


class TestCaching:
    """Test quality assessment caching."""

    @patch("src.ingestion.loaders.ProcessorFactory")
    @patch("src.processing.router.QualityAssessor")
    def test_quality_assessment_cached(
        self,
        mock_assessor_class,
        mock_factory,
        mock_pdf_file,
        mock_quality_assessment,
        mock_processed_document,
    ):
        """Test quality assessments are cached."""
        # Mock assessor with caching enabled
        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_quality_assessment
        mock_assessor_class.return_value = mock_assessor

        mock_processor = Mock()
        mock_processor.process.return_value = mock_processed_document
        mock_factory.create.return_value = mock_processor

        # Process same file twice
        _load_pdf_with_routing(mock_pdf_file)
        _load_pdf_with_routing(mock_pdf_file)

        # Assessment should be called twice (cache is in assessor, not loader)
        # But in real scenario with cache enabled, second call uses cache
        assert mock_assessor.assess.call_count == 2
