"""
Integration tests for the document processing system.

These tests verify that the entire processing pipeline works correctly,
from file loading through processing to final document output.
"""

import pytest
from pathlib import Path

from src.ingestion.loaders import load_pdf
from src.processing import ProcessorConfig, ProcessorFactory


class TestProcessingIntegration:
    """Integration tests for document processing."""

    @pytest.mark.integration
    def test_load_pdf_with_legacy_processor(self, tmp_path):
        """Test loading PDF with legacy processor through loaders.py."""
        pytest.importorskip("pymupdf")
        pytest.importorskip("pymupdf4llm")

        # Create a simple PDF
        import pymupdf as fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Integration test content")
        doc.save(str(pdf_path))
        doc.close()

        # Load using legacy processor
        document = load_pdf(pdf_path, processor_type="legacy")

        assert document is not None
        assert document.format == "pdf"
        assert document.file_path == pdf_path
        assert document.page_count == 1

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.skipif(
        not pytest.importorskip("docling", reason="Docling not installed"),
        reason="Requires Docling",
    )
    def test_load_pdf_with_docling_processor(self, tmp_path):
        """Test loading PDF with Docling processor through loaders.py."""
        pytest.importorskip("pymupdf")

        # Create a simple PDF
        import pymupdf as fitz

        pdf_path = tmp_path / "test_docling.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Docling integration test")
        doc.save(str(pdf_path))
        doc.close()

        # Load using Docling processor
        document = load_pdf(pdf_path, processor_type="docling")

        assert document is not None
        assert document.format == "pdf"
        assert document.file_path == pdf_path
        assert document.page_count >= 1

    @pytest.mark.integration
    def test_processor_fallback_mechanism(self, tmp_path):
        """Test that system falls back to legacy when Docling unavailable."""
        pytest.importorskip("pymupdf")
        pytest.importorskip("pymupdf4llm")

        # Create a simple PDF
        import pymupdf as fitz

        pdf_path = tmp_path / "fallback_test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Fallback test")
        doc.save(str(pdf_path))
        doc.close()

        # Try to load with a processor type
        # If Docling is not available, it should fall back to legacy
        document = load_pdf(pdf_path)

        assert document is not None
        assert document.format == "pdf"

    def test_processor_selection_via_config(self):
        """Test that processor can be selected via configuration."""
        # Test that factory respects configuration
        legacy_config = ProcessorConfig(processor_type="legacy")
        legacy_processor = ProcessorFactory.create(legacy_config)

        assert legacy_processor.config.processor_type == "legacy"

        # If Docling is available, test it too
        if ProcessorFactory.is_processor_available("docling"):
            docling_config = ProcessorConfig(processor_type="docling")
            docling_processor = ProcessorFactory.create(docling_config)

            assert docling_processor.config.processor_type == "docling"

    @pytest.mark.integration
    def test_processing_preserves_page_markers(self, tmp_path):
        """Test that page markers are preserved for citation tracking."""
        pytest.importorskip("pymupdf")
        pytest.importorskip("pymupdf4llm")

        # Create a multi-page PDF
        import pymupdf as fitz

        pdf_path = tmp_path / "multipage.pdf"
        doc = fitz.open()

        # Add 3 pages
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1} content")

        doc.save(str(pdf_path))
        doc.close()

        # Load with legacy processor
        document = load_pdf(pdf_path, processor_type="legacy")

        # Check for page markers
        assert "<!-- PAGE 1 -->" in document.content
        assert "<!-- PAGE 2 -->" in document.content
        assert "<!-- PAGE 3 -->" in document.content
