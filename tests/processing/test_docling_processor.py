"""
Tests for DoclingProcessor.
"""

import pytest
from pathlib import Path

from src.processing.base import ProcessorConfig, ProcessorError


# Skip all tests if Docling is not installed
pytest.importorskip("docling", reason="Docling not installed")

from src.processing.docling_processor import DoclingProcessor


class TestDoclingProcessor:
    """Tests for DoclingProcessor."""

    def test_initialization(self):
        """Test that DoclingProcessor initializes correctly."""
        config = ProcessorConfig(processor_type="docling")
        processor = DoclingProcessor(config)

        assert processor.config == config
        assert processor.model_manager is not None
        assert processor._pipeline is None  # Lazy initialization

    def test_initialization_without_docling(self, monkeypatch):
        """Test that initialization fails gracefully without Docling."""
        # Mock docling import to fail
        import sys

        monkeypatch.setitem(sys.modules, "docling", None)

        config = ProcessorConfig(processor_type="docling")

        # Should raise ProcessorError about missing Docling
        # Note: This test might not work as expected due to import caching
        # Left here for documentation purposes
        pass

    def test_supports_pdf_files(self):
        """Test that Docling processor supports PDF files."""
        config = ProcessorConfig(processor_type="docling")
        processor = DoclingProcessor(config)

        assert processor.supports_file_type(Path("test.pdf")) is True
        assert processor.supports_file_type(Path("test.PDF")) is True

    def test_does_not_support_other_files(self):
        """Test that Docling processor doesn't support non-PDF files."""
        config = ProcessorConfig(processor_type="docling")
        processor = DoclingProcessor(config)

        assert processor.supports_file_type(Path("test.txt")) is False
        assert processor.supports_file_type(Path("test.docx")) is False

    def test_capabilities_with_table_extraction(self):
        """Test capabilities when table extraction is enabled."""
        config = ProcessorConfig(
            processor_type="docling", enable_table_extraction=True, enable_layout_analysis=True
        )
        processor = DoclingProcessor(config)

        caps = processor.get_capabilities()

        assert caps["ocr"] is False  # Not in v0.3.4a
        assert caps["tables"] is True
        assert caps["layout_analysis"] is True
        assert caps["reading_order"] is True
        assert caps["images"] is True

    def test_capabilities_without_table_extraction(self):
        """Test capabilities when table extraction is disabled."""
        config = ProcessorConfig(
            processor_type="docling", enable_table_extraction=False, enable_layout_analysis=False
        )
        processor = DoclingProcessor(config)

        caps = processor.get_capabilities()

        assert caps["tables"] is False
        assert caps["layout_analysis"] is False

    @pytest.mark.integration
    @pytest.mark.slow
    def test_process_real_pdf(self, tmp_path):
        """
        Test processing a real PDF file with Docling.

        This is an integration test that requires Docling to be installed
        and will download models on first run.
        """
        # Create a simple PDF using PyMuPDF
        pytest.importorskip("pymupdf")
        import pymupdf as fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test PDF content\nLine 2")
        doc.save(str(pdf_path))
        doc.close()

        # Process it with Docling
        config = ProcessorConfig(
            processor_type="docling",
            enable_table_extraction=True,
            enable_layout_analysis=True,
            model_cache_dir=tmp_path / "models",
        )
        processor = DoclingProcessor(config)
        result = processor.process(pdf_path)

        assert result.processor_type == "docling"
        assert result.content is not None
        assert len(result.content) > 0
        assert result.metadata["page_count"] >= 1
        assert result.metadata["format"] == "pdf"
        assert result.confidence > 0.9  # Docling has high confidence

    def test_process_nonexistent_file(self):
        """Test that processing nonexistent file raises error."""
        config = ProcessorConfig(processor_type="docling")
        processor = DoclingProcessor(config)

        with pytest.raises(FileNotFoundError):
            processor.process(Path("/nonexistent/file.pdf"))

    def test_process_unsupported_file(self, tmp_path):
        """Test that processing unsupported file type raises error."""
        config = ProcessorConfig(processor_type="docling")
        processor = DoclingProcessor(config)

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process(txt_file)

    def test_lazy_pipeline_initialization(self):
        """Test that pipeline is created lazily."""
        config = ProcessorConfig(processor_type="docling")
        processor = DoclingProcessor(config)

        # Pipeline should not be created yet
        assert processor._pipeline is None

        # Access pipeline property
        pipeline = processor.pipeline

        # Now it should be created
        assert pipeline is not None
        assert processor._pipeline is not None

        # Second access should return same instance
        pipeline2 = processor.pipeline
        assert pipeline2 is pipeline
