"""Tests for contextual chunking."""

import pytest
from pathlib import Path
from datetime import datetime
import hashlib
from src.chunking.contextual import (
    ContextualChunk,
    ContextualChunker,
    ContextCompressor
)
from src.ingestion.models import Document, DocumentMetadata


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    content = """# Introduction

This is the introduction section of the document.

# Methods

This section describes the methodology used in the research.

The experiments were conducted over several months.

# Results

The results show significant findings.
"""
    file_hash = hashlib.sha256(content.encode()).hexdigest()

    return Document(
        document_id="doc1",
        content=content,
        metadata=DocumentMetadata(
            file_path=Path("/path/to/research_paper.pdf"),
            file_size=len(content),
            file_hash=file_hash,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            format="pdf"
        )
    )


class TestContextualChunk:
    """Test ContextualChunk dataclass."""

    def test_to_enriched_text_with_section(self):
        """Test enriched text with document and section context."""
        chunk = ContextualChunk(
            content="This is the content.",
            document_context="From: test.pdf",
            section_context="Section: Introduction",
            chunk_index=0,
            total_chunks=3
        )

        enriched = chunk.to_enriched_text()

        assert "[From: test.pdf]" in enriched
        assert "[Section: Introduction]" in enriched
        assert "This is the content." in enriched

    def test_to_enriched_text_without_section(self):
        """Test enriched text without section context."""
        chunk = ContextualChunk(
            content="Content here.",
            document_context="From: doc.txt",
            section_context=None,
            chunk_index=1,
            total_chunks=2
        )

        enriched = chunk.to_enriched_text()

        assert "[From: doc.txt]" in enriched
        assert "Section:" not in enriched
        assert "Content here." in enriched

    def test_to_metadata(self):
        """Test metadata extraction."""
        chunk = ContextualChunk(
            content="Text",
            document_context="From: file.md",
            section_context="Section: Methods",
            chunk_index=2,
            total_chunks=5
        )

        metadata = chunk.to_metadata()

        assert metadata["document_context"] == "From: file.md"
        assert metadata["section_context"] == "Section: Methods"
        assert metadata["chunk_index"] == 2
        assert metadata["total_chunks"] == 5


class TestContextualChunker:
    """Test ContextualChunker."""

    def test_init(self):
        """Test chunker initialization."""
        chunker = ContextualChunker(
            chunk_size=500,
            chunk_overlap=50,
            add_document_context=True,
            add_section_context=True
        )

        assert chunker.add_document_context is True
        assert chunker.add_section_context is True

    def test_chunk_document(self, sample_document):
        """Test document chunking."""
        chunker = ContextualChunker(chunk_size=200, chunk_overlap=20)

        chunks = chunker.chunk_document(sample_document)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.chunk_id.startswith("doc1_chunk_")
            assert hasattr(chunk, 'text')
            assert chunk.metadata.document_id == "doc1"

    def test_document_context_added(self, sample_document):
        """Test document context is added to chunks."""
        chunker = ContextualChunker(
            chunk_size=300,
            add_document_context=True,
            add_section_context=False
        )

        chunks = chunker.chunk_document(sample_document)

        # Check first chunk has document context
        first_chunk = chunks[0]
        assert "[From: research_paper.pdf" in first_chunk.text

    def test_section_context_detected(self):
        """Test section context detection from markdown headers."""
        content = "# Introduction\n\nThis is intro text.\n\n# Methods\n\nMethod details here."
        file_hash = hashlib.sha256(content.encode()).hexdigest()

        doc = Document(
            document_id="doc2",
            content=content,
            metadata=DocumentMetadata(
                file_path=Path("paper.md"),
                file_size=len(content),
                file_hash=file_hash,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                format="md"
            )
        )

        chunker = ContextualChunker(
            chunk_size=200,
            chunk_overlap=20,
            add_section_context=True
        )

        chunks = chunker.chunk_document(doc)

        # At least one chunk should have section context
        section_contexts = [
            chunk.metadata.get("section_context")
            for chunk in chunks
            if chunk.metadata.get("section_context")
        ]

        assert len(section_contexts) > 0

    def test_extract_section_markdown_header(self):
        """Test section extraction from markdown headers."""
        chunker = ContextualChunker()

        text = "# Introduction\n\nThis is the intro."
        section = chunker._extract_section_context(text)

        assert section == "Section: Introduction"

    def test_extract_section_caps_header(self):
        """Test section extraction from all-caps headers."""
        chunker = ContextualChunker()

        text = "INTRODUCTION\n\nContent here."
        section = chunker._extract_section_context(text)

        assert section == "Section: Introduction"

    def test_extract_section_numbered(self):
        """Test section extraction from numbered sections."""
        chunker = ContextualChunker()

        text = "1.1 Background\n\nSome text."
        section = chunker._extract_section_context(text)

        assert section == "Section: Background"

    def test_extract_section_none(self):
        """Test section extraction returns None when no header."""
        chunker = ContextualChunker()

        text = "Just plain text without any headers."
        section = chunker._extract_section_context(text)

        assert section is None

    def test_get_document_context(self):
        """Test document context extraction."""
        content = "Content"
        file_hash = hashlib.sha256(content.encode()).hexdigest()

        doc = Document(
            document_id="doc3",
            content=content,
            metadata=DocumentMetadata(
                file_path=Path("/path/to/test_file.pdf"),
                file_size=len(content),
                file_hash=file_hash,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                format="pdf"
            )
        )

        chunker = ContextualChunker(add_document_context=True)
        context = chunker._get_document_context(doc)

        assert "test_file.pdf" in context
        assert "pdf" in context

    def test_document_context_disabled(self):
        """Test chunking with document context disabled."""
        content = "Test content here."
        file_hash = hashlib.sha256(content.encode()).hexdigest()

        doc = Document(
            document_id="doc4",
            content=content,
            metadata=DocumentMetadata(
                file_path=Path("file.txt"),
                file_size=len(content),
                file_hash=file_hash,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                format="txt"
            )
        )

        chunker = ContextualChunker(
            add_document_context=False,
            add_section_context=False
        )

        context = chunker._get_document_context(doc)
        assert context == ""


class TestContextCompressor:
    """Test ContextCompressor."""

    @pytest.fixture
    def sample_chunks(self):
        """Sample chunks for compression."""
        from src.ingestion.models import Chunk, ChunkMetadata

        return [
            Chunk(
                chunk_id="chunk1",
                text="Content from first document.",
                tokens=5,
                position=0,
                document_id="doc1",
                metadata=ChunkMetadata(
                    document_id="doc1",
                    document_path=Path("doc1.pdf"),
                    chunk_position=0,
                    total_chunks=1,
                    overlap_with_previous=0,
                    overlap_with_next=0
                )
            ),
            Chunk(
                chunk_id="chunk2",
                text="Content from second document.",
                tokens=5,
                position=0,
                document_id="doc2",
                metadata=ChunkMetadata(
                    document_id="doc2",
                    document_path=Path("doc2.txt"),
                    chunk_position=0,
                    total_chunks=1,
                    overlap_with_previous=0,
                    overlap_with_next=0
                )
            )
        ]

    def test_init(self):
        """Test compressor initialization."""
        compressor = ContextCompressor(max_tokens=1000)
        assert compressor.max_tokens == 1000

    def test_compress_empty_chunks(self):
        """Test compressing empty chunk list."""
        compressor = ContextCompressor()
        result = compressor.compress([], "test query")

        assert result == ""

    def test_compress_chunks(self, sample_chunks):
        """Test compressing chunks."""
        compressor = ContextCompressor()
        result = compressor.compress(sample_chunks, "test query")

        assert "Content from first document" in result
        assert "Content from second document" in result
        assert "Source 1: doc1.pdf" in result
        assert "Source 2: doc2.txt" in result

    def test_compress_with_query_focus(self, sample_chunks):
        """Test query-focused compression."""
        compressor = ContextCompressor()
        result = compressor.compress_with_query_focus(
            sample_chunks,
            "test query"
        )

        assert len(result) > 0
        assert "Content from first document" in result
