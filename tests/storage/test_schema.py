"""Tests for dual embedding storage schema (v0.5.0)."""

import pytest
from datetime import datetime

from src.storage.schema import (
    EmbeddingType,
    TextMetadata,
    VisionMetadata,
    create_text_metadata,
    create_vision_metadata,
    generate_embedding_id,
    parse_embedding_id,
)


class TestEmbeddingType:
    """Test EmbeddingType enumeration."""

    def test_text_type(self):
        """Test TEXT enum value."""
        assert EmbeddingType.TEXT.value == "text"

    def test_vision_type(self):
        """Test VISION enum value."""
        assert EmbeddingType.VISION.value == "vision"

    def test_enum_comparison(self):
        """Test enum comparison."""
        assert EmbeddingType.TEXT != EmbeddingType.VISION
        assert EmbeddingType.TEXT == EmbeddingType.TEXT


class TestGenerateEmbeddingId:
    """Test embedding ID generation."""

    def test_text_embedding_id(self):
        """Test text embedding ID format."""
        doc_id = "abc123"
        index = 5
        result = generate_embedding_id(doc_id, EmbeddingType.TEXT, index)

        assert result == "abc123_chunk_5_text"

    def test_vision_embedding_id(self):
        """Test vision embedding ID format."""
        doc_id = "xyz789"
        index = 3
        result = generate_embedding_id(doc_id, EmbeddingType.VISION, index)

        assert result == "xyz789_page_3_vision"

    def test_text_embedding_id_zero_index(self):
        """Test text embedding ID with zero index."""
        result = generate_embedding_id("doc1", EmbeddingType.TEXT, 0)
        assert result == "doc1_chunk_0_text"

    def test_vision_embedding_id_large_index(self):
        """Test vision embedding ID with large index."""
        result = generate_embedding_id("doc1", EmbeddingType.VISION, 999)
        assert result == "doc1_page_999_vision"


class TestCreateTextMetadata:
    """Test text metadata creation."""

    def test_create_basic_text_metadata(self):
        """Test basic text metadata creation."""
        metadata = create_text_metadata(
            document_id="doc123",
            chunk_id="chunk_0",
            chunk_index=0,
            text_content="Sample text content",
        )

        assert isinstance(metadata, dict)
        assert metadata["document_id"] == "doc123"
        assert metadata["embedding_type"] == "text"
        assert metadata["chunk_id"] == "chunk_0"
        assert metadata["chunk_index"] == 0
        assert metadata["text_content"] == "Sample text content"
        assert metadata["char_count"] == len("Sample text content")
        assert metadata["page_number"] is None

    def test_create_text_metadata_with_page(self):
        """Test text metadata creation with page number."""
        metadata = create_text_metadata(
            document_id="doc456",
            chunk_id="chunk_5",
            chunk_index=5,
            text_content="Text on page 3",
            page_number=2,  # 0-indexed
        )

        assert metadata["page_number"] == 2

    def test_text_metadata_has_timestamp(self):
        """Test that text metadata includes created_at timestamp."""
        before = datetime.utcnow().isoformat()
        metadata = create_text_metadata(
            document_id="doc1", chunk_id="c1", chunk_index=0, text_content="test"
        )
        after = datetime.utcnow().isoformat()

        assert "created_at" in metadata
        assert before <= metadata["created_at"] <= after

    def test_text_metadata_char_count(self):
        """Test character count calculation."""
        text = "This has 24 characters."
        metadata = create_text_metadata(
            document_id="doc1", chunk_id="c1", chunk_index=0, text_content=text
        )

        assert metadata["char_count"] == len(text)


class TestCreateVisionMetadata:
    """Test vision metadata creation."""

    def test_create_basic_vision_metadata(self):
        """Test basic vision metadata creation."""
        metadata = create_vision_metadata(
            document_id="doc123",
            page_number=5,
            image_hash="abc123def456",
        )

        assert isinstance(metadata, dict)
        assert metadata["document_id"] == "doc123"
        assert metadata["embedding_type"] == "vision"
        assert metadata["page_number"] == 5
        assert metadata["image_hash"] == "abc123def456"
        assert metadata["has_diagrams"] is False
        assert metadata["has_tables"] is False
        assert metadata["layout_complexity"] == "simple"

    def test_create_vision_metadata_with_features(self):
        """Test vision metadata with diagram/table flags."""
        metadata = create_vision_metadata(
            document_id="doc456",
            page_number=3,
            image_hash="hash789",
            has_diagrams=True,
            has_tables=True,
            layout_complexity="complex",
        )

        assert metadata["has_diagrams"] is True
        assert metadata["has_tables"] is True
        assert metadata["layout_complexity"] == "complex"

    def test_vision_metadata_has_timestamp(self):
        """Test that vision metadata includes created_at timestamp."""
        before = datetime.utcnow().isoformat()
        metadata = create_vision_metadata(
            document_id="doc1", page_number=0, image_hash="hash123"
        )
        after = datetime.utcnow().isoformat()

        assert "created_at" in metadata
        assert before <= metadata["created_at"] <= after

    def test_vision_metadata_layout_options(self):
        """Test different layout complexity options."""
        for complexity in ["simple", "moderate", "complex"]:
            metadata = create_vision_metadata(
                document_id="doc1", page_number=0, image_hash="hash", layout_complexity=complexity
            )
            assert metadata["layout_complexity"] == complexity


class TestParseEmbeddingId:
    """Test embedding ID parsing."""

    def test_parse_text_embedding_id(self):
        """Test parsing text embedding ID."""
        embedding_id = "abc123_chunk_5_text"
        result = parse_embedding_id(embedding_id)

        assert result["document_id"] == "abc123"
        assert result["type"] == "text"
        assert result["index"] == 5

    def test_parse_vision_embedding_id(self):
        """Test parsing vision embedding ID."""
        embedding_id = "xyz789_page_3_vision"
        result = parse_embedding_id(embedding_id)

        assert result["document_id"] == "xyz789"
        assert result["type"] == "vision"
        assert result["index"] == 3

    def test_parse_complex_document_id(self):
        """Test parsing ID with underscores in document ID."""
        embedding_id = "doc_with_underscores_chunk_10_text"
        result = parse_embedding_id(embedding_id)

        assert result["document_id"] == "doc_with_underscores"
        assert result["type"] == "text"
        assert result["index"] == 10

    def test_parse_invalid_format(self):
        """Test parsing invalid ID format."""
        with pytest.raises(ValueError, match="Invalid embedding type"):
            parse_embedding_id("invalid_id")

    def test_parse_invalid_type(self):
        """Test parsing ID with invalid embedding type."""
        with pytest.raises(ValueError, match="Invalid embedding type"):
            parse_embedding_id("doc123_chunk_5_invalid")

    def test_parse_invalid_index(self):
        """Test parsing ID with non-numeric index."""
        with pytest.raises(ValueError, match="Invalid index"):
            parse_embedding_id("doc123_chunk_abc_text")

    def test_parse_zero_index(self):
        """Test parsing ID with zero index."""
        result = parse_embedding_id("doc1_chunk_0_text")
        assert result["index"] == 0

    def test_parse_large_index(self):
        """Test parsing ID with large index."""
        result = parse_embedding_id("doc1_page_9999_vision")
        assert result["index"] == 9999
