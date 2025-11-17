"""
Integration tests for multi-format document loading.

Tests loading and processing of PDF, TXT, MD, HTML formats through the pipeline.
"""

import pytest
from pathlib import Path
from src.ingestion.loaders import load_document
from src.chunking.splitters import RecursiveCharacterTextSplitter, chunk_document
from src.config.settings import get_settings


class TestMultiFormatIngestion:
    """Test document loading across multiple formats."""

    @pytest.fixture
    def settings(self):
        """Get settings for tests."""
        return get_settings()

    @pytest.fixture
    def sample_txt(self, tmp_path):
        """Create sample TXT file."""
        content = "This is a plain text document about machine learning."
        file_path = tmp_path / "sample.txt"
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def sample_markdown(self, tmp_path):
        """Create sample Markdown file."""
        content = """# Machine Learning Guide

## Introduction
Machine learning is a subset of AI.

## Deep Learning
Deep learning uses neural networks.
"""
        file_path = tmp_path / "sample.md"
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def sample_html(self, tmp_path):
        """Create sample HTML file."""
        content = """<!DOCTYPE html>
<html>
<head><title>AI Guide</title></head>
<body>
<h1>Artificial Intelligence</h1>
<p>AI is the simulation of human intelligence in machines.</p>
<p>Machine learning is a key component of AI.</p>
</body>
</html>
"""
        file_path = tmp_path / "sample.html"
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create sample PDF file."""
        try:
            import fitz  # pymupdf
        except ImportError:
            pytest.skip("pymupdf not available")

        # Create a simple PDF with pymupdf
        file_path = tmp_path / "sample.pdf"
        doc = fitz.open()  # Create new PDF
        page = doc.new_page()  # Add a page

        # Add text to the page
        text = """Machine Learning Research Paper

Introduction
This document demonstrates PDF loading and processing capabilities.
Machine learning is transforming how we process and analyse data.

Methods
We utilise various machine learning algorithms for data analysis.
The research methodology includes both supervised and unsupervised learning.

Results
Our experiments show significant improvements in accuracy and performance.
"""
        # Insert text at position (50, 50) with font size 12
        page.insert_text((50, 50), text, fontsize=12)

        # Save the PDF
        doc.save(str(file_path))
        doc.close()

        return file_path

    @pytest.mark.integration
    def test_txt_loading_and_chunking(self, sample_txt, settings):
        """Test TXT file through full pipeline."""
        # Load
        document = load_document(sample_txt)
        assert document is not None
        assert "machine learning" in document.content.lower()
        assert document.metadata.file_path.name == "sample.txt"
        assert document.metadata.format == "txt"

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        document = chunk_document(document, splitter)
        assert len(document.chunks) >= 1
        assert all(chunk.metadata.document_path.name == "sample.txt" for chunk in document.chunks)

    @pytest.mark.integration
    def test_markdown_loading_and_chunking(self, sample_markdown, settings):
        """Test Markdown file through full pipeline."""
        # Load
        document = load_document(sample_markdown)
        assert document is not None
        assert "machine learning" in document.content.lower()
        assert document.metadata.file_path.name == "sample.md"
        assert document.metadata.format == "md"

        # Should preserve structure
        assert "Introduction" in document.content or "introduction" in document.content.lower()

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        document = chunk_document(document, splitter)
        assert len(document.chunks) >= 1

    @pytest.mark.integration
    def test_html_loading_and_chunking(self, sample_html, settings):
        """Test HTML file through full pipeline."""
        # Load
        document = load_document(sample_html)
        assert document is not None
        assert document.metadata.file_path.name == "sample.html"
        assert document.metadata.format == "html"

        # Should extract text content
        content_lower = document.content.lower()
        assert "artificial intelligence" in content_lower or "ai" in content_lower

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        document = chunk_document(document, splitter)
        assert len(document.chunks) >= 1

    @pytest.mark.integration
    def test_all_formats_produce_consistent_chunks(self, tmp_path, settings):
        """Test that all formats produce valid chunk structure."""

        formats = {
            "txt": "This is a test document with some content about AI and machine learning.",
            "md": "# Test\n\nThis is a test document with some content about AI and machine learning.",
            "html": "<html><body><p>This is a test document with some content about AI and machine learning.</p></body></html>",
        }

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        for ext, content in formats.items():
            file_path = tmp_path / f"test.{ext}"
            file_path.write_text(content)

            # Load and chunk
            document = load_document(file_path)
            document = chunk_document(document, splitter)

            # All formats should produce valid chunks
            assert len(document.chunks) >= 1
            for chunk in document.chunks:
                assert chunk.chunk_id is not None
                assert len(chunk.text) > 0
                assert chunk.metadata.document_path.name == f"test.{ext}"
                assert chunk.metadata.chunk_position >= 0

    @pytest.mark.integration
    def test_pdf_loading_and_chunking(self, sample_pdf, settings):
        """Test PDF file through full pipeline."""
        # Load
        document = load_document(sample_pdf)
        assert document is not None
        assert "machine learning" in document.content.lower()
        assert document.metadata.file_path.name == "sample.pdf"
        assert document.metadata.format == "pdf"

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        document = chunk_document(document, splitter)
        assert len(document.chunks) >= 1
        # Chunks should have document_path in metadata
        assert all(chunk.metadata.document_path.name == "sample.pdf" for chunk in document.chunks)

    @pytest.mark.integration
    def test_format_autodetection(self, sample_txt, sample_markdown, sample_html):
        """Test that format is correctly auto-detected."""

        # TXT
        doc_txt = load_document(sample_txt)
        assert doc_txt.metadata.format == "txt"

        # Markdown
        doc_md = load_document(sample_markdown)
        assert doc_md.metadata.format == "md"

        # HTML
        doc_html = load_document(sample_html)
        assert doc_html.metadata.format == "html"

    @pytest.mark.integration
    def test_metadata_preservation_across_formats(self, sample_txt, sample_markdown, sample_html):
        """Test that metadata is correctly preserved for all formats."""

        files = [sample_txt, sample_markdown, sample_html]

        for file_path in files:
            document = load_document(file_path)

            # All should have required metadata
            assert document.metadata.file_path is not None
            assert document.metadata.format is not None
            assert document.metadata.file_size > 0
            assert document.metadata.file_hash is not None
            assert document.metadata.created_at is not None

    @pytest.mark.integration
    def test_large_document_chunking(self, tmp_path, settings):
        """Test chunking of a larger document."""

        # Create a large text file
        large_content = "\n\n".join([
            f"This is paragraph {i} about machine learning and artificial intelligence. "
            f"It contains some information about neural networks and deep learning. "
            f"This paragraph also discusses natural language processing and computer vision."
            for i in range(50)
        ])

        file_path = tmp_path / "large_doc.txt"
        file_path.write_text(large_content)

        # Load and chunk
        document = load_document(file_path)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        document = chunk_document(document, splitter)

        # Should produce multiple chunks
        assert len(document.chunks) > 1

        # Chunks should have proper indices
        for i, chunk in enumerate(document.chunks):
            assert chunk.metadata.chunk_position == i

        # All chunks should reference same source
        assert all(chunk.metadata.document_path.name == "large_doc.txt" for chunk in document.chunks)

    @pytest.mark.integration
    def test_error_handling_invalid_file(self, tmp_path):
        """Test graceful error handling for invalid files."""

        # Non-existent file
        with pytest.raises((FileNotFoundError, ValueError)):
            load_document(tmp_path / "nonexistent.txt")

        # Empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        # Should handle gracefully (may return document with empty content or raise)
        try:
            doc = load_document(empty_file)
            # If it succeeds, content should be empty or minimal
            assert len(doc.content.strip()) == 0
        except ValueError:
            # Or it may raise ValueError for empty content
            pass
