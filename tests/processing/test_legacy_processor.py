"""
Tests for LegacyProcessor.
"""

import pytest
from pathlib import Path

from src.processing.base import ProcessorConfig, ProcessorError
from src.processing.legacy_processor import LegacyProcessor


class TestLegacyProcessor:
    """Tests for LegacyProcessor."""

    def test_initialization(self):
        """Test that LegacyProcessor initializes correctly."""
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)

        assert processor.config == config

    def test_supports_pdf_files(self):
        """Test that legacy processor supports PDF files."""
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)

        assert processor.supports_file_type(Path("test.pdf")) is True
        assert processor.supports_file_type(Path("test.PDF")) is True

    def test_does_not_support_other_files(self):
        """Test that legacy processor doesn't support non-PDF files."""
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)

        assert processor.supports_file_type(Path("test.txt")) is False
        assert processor.supports_file_type(Path("test.docx")) is False

    def test_capabilities(self):
        """Test that legacy processor reports correct capabilities."""
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)

        caps = processor.get_capabilities()

        assert caps["ocr"] is False
        assert caps["tables"] is False
        assert caps["layout_analysis"] is False
        assert caps["reading_order"] is False
        assert caps["images"] is False

    @pytest.mark.integration
    def test_process_real_pdf(self, tmp_path):
        """
        Test processing a real PDF file.

        This is an integration test that requires PyMuPDF to be installed.
        """
        pytest.importorskip("pymupdf")
        pytest.importorskip("pymupdf4llm")

        # Create a simple PDF using PyMuPDF
        import pymupdf as fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test PDF content\nLine 2")
        doc.save(str(pdf_path))
        doc.close()

        # Process it
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)
        result = processor.process(pdf_path)

        assert result.processor_type == "legacy"
        assert "Test PDF content" in result.content or "test.pdf" in result.content.lower()
        assert result.metadata["page_count"] == 1
        assert result.metadata["format"] == "pdf"
        assert result.confidence == 0.8

    def test_process_nonexistent_file(self):
        """Test that processing nonexistent file raises error."""
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)

        with pytest.raises(FileNotFoundError):
            processor.process(Path("/nonexistent/file.pdf"))

    def test_process_unsupported_file(self, tmp_path):
        """Test that processing unsupported file type raises error."""
        config = ProcessorConfig(processor_type="legacy")
        processor = LegacyProcessor(config)

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process(txt_file)
