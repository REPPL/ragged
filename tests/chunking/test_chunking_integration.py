"""Integration tests for v0.3.3 intelligent chunking strategies.

Tests the complete flow from configuration → factory → chunking → document model.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.chunking.factory import ChunkerFactory
from src.chunking.hierarchical_chunker import HierarchicalChunker
from src.chunking.semantic_chunker import SemanticChunker
from src.chunking.splitters.chunking import chunk_document
from src.chunking.splitters.recursive_splitter import RecursiveCharacterTextSplitter
from src.config.settings import Settings, get_settings
from src.ingestion.models import Document, DocumentMetadata


# Valid SHA256 hash for testing (64 hex chars)
TEST_HASH = "a" * 64
TEST_CONTENT_HASH = "b" * 64


class TestChunkerFactory:
    """Test ChunkerFactory creates correct chunker instances."""

    def test_create_fixed_chunker(self):
        """Test factory creates RecursiveCharacterTextSplitter for 'fixed' strategy."""
        chunker = ChunkerFactory.create_chunker("fixed")

        assert isinstance(chunker, RecursiveCharacterTextSplitter)
        assert chunker.chunk_size == get_settings().chunk_size
        assert chunker.chunk_overlap == get_settings().chunk_overlap

    def test_create_semantic_chunker(self):
        """Test factory creates SemanticChunker for 'semantic' strategy."""
        chunker = ChunkerFactory.create_chunker("semantic")

        assert isinstance(chunker, SemanticChunker)
        assert chunker.similarity_threshold == get_settings().semantic_similarity_threshold
        assert chunker.min_chunk_size == get_settings().semantic_min_chunk_size
        assert chunker.max_chunk_size == get_settings().semantic_max_chunk_size

    def test_create_hierarchical_chunker(self):
        """Test factory creates HierarchicalChunker for 'hierarchical' strategy."""
        chunker = ChunkerFactory.create_chunker("hierarchical")

        assert isinstance(chunker, HierarchicalChunker)
        assert chunker.parent_chunk_size == get_settings().hierarchical_parent_size
        assert chunker.child_chunk_size == get_settings().hierarchical_child_size
        assert chunker.parent_overlap == get_settings().hierarchical_parent_overlap
        assert chunker.child_overlap == get_settings().hierarchical_child_overlap

    def test_create_chunker_defaults_to_settings(self):
        """Test factory uses settings.chunking_strategy when strategy is None."""
        # Clear settings cache and create new settings with fixed strategy
        get_settings.cache_clear()

        # Default is "fixed"
        chunker = ChunkerFactory.create_chunker(strategy=None)

        assert isinstance(chunker, RecursiveCharacterTextSplitter)

        get_settings.cache_clear()

    def test_create_chunker_invalid_strategy(self):
        """Test factory raises ValueError for invalid strategy."""
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            ChunkerFactory.create_chunker("invalid_strategy")


class TestChunkDocumentIntegration:
    """Test chunk_document() function with different strategies."""

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        return Document(
            content="This is the first sentence. This is the second sentence. "
                   "This is the third sentence. This is the fourth sentence. "
                   "This is the fifth sentence. This is the sixth sentence.",
            metadata=DocumentMetadata(
                file_path=Path("/tmp/test.txt"),
                file_hash=TEST_HASH,
                content_hash=TEST_CONTENT_HASH,
                format="txt",
                file_size=1024,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
            ),
        )

    def test_chunk_document_with_fixed_strategy(self, sample_document):
        """Test chunk_document with fixed strategy."""
        document = chunk_document(sample_document, strategy="fixed")

        assert len(document.chunks) > 0
        assert all(chunk.metadata.document_id == document.document_id for chunk in document.chunks)
        assert all(chunk.document_id == document.document_id for chunk in document.chunks)

        # Check metadata
        for i, chunk in enumerate(document.chunks):
            assert chunk.metadata.chunk_position == i
            assert chunk.metadata.total_chunks == len(document.chunks)
            assert chunk.position == i

    def test_chunk_document_with_semantic_strategy(self, sample_document):
        """Test chunk_document with semantic strategy (using fallback)."""
        # Semantic chunker will use fallback since we don't have actual embeddings
        document = chunk_document(sample_document, strategy="semantic")

        assert len(document.chunks) > 0
        assert all(chunk.metadata.document_id == document.document_id for chunk in document.chunks)

        # Semantic chunker doesn't have chunk_overlap attribute
        for chunk in document.chunks:
            # First chunk has no overlap with previous
            if chunk.position == 0:
                assert chunk.metadata.overlap_with_previous == 0
            # Last chunk has no overlap with next
            if chunk.position == len(document.chunks) - 1:
                assert chunk.metadata.overlap_with_next == 0

    def test_chunk_document_with_hierarchical_strategy(self, sample_document):
        """Test chunk_document with hierarchical strategy."""
        document = chunk_document(sample_document, strategy="hierarchical")

        assert len(document.chunks) > 0
        assert all(chunk.metadata.document_id == document.document_id for chunk in document.chunks)

        # Hierarchical chunker returns child chunks
        # Check that chunks are properly created
        for chunk in document.chunks:
            assert chunk.text is not None
            assert len(chunk.text) > 0
            assert chunk.tokens > 0

    def test_chunk_document_with_custom_splitter(self, sample_document):
        """Test chunk_document with custom splitter (overrides strategy)."""
        custom_splitter = RecursiveCharacterTextSplitter(
            chunk_size=50,
            chunk_overlap=10,
        )

        document = chunk_document(
            sample_document,
            splitter=custom_splitter,
            strategy="semantic",  # Should be ignored
        )

        assert len(document.chunks) > 0
        # Should use custom splitter, not semantic strategy

    def test_chunk_document_preserves_metadata(self, sample_document):
        """Test that chunking preserves original document metadata."""
        document = chunk_document(sample_document, strategy="fixed")

        for chunk in document.chunks:
            assert chunk.metadata.file_hash == sample_document.metadata.file_hash
            assert chunk.metadata.content_hash == sample_document.metadata.content_hash
            assert chunk.metadata.document_path == sample_document.metadata.file_path

    def test_chunk_document_page_tracking_with_pdf(self):
        """Test page tracking with PDF document."""
        pdf_content = "<!-- PAGE 1 -->\nFirst page content.\n<!-- PAGE 2 -->\nSecond page content."

        pdf_document = Document(
            content=pdf_content,
            metadata=DocumentMetadata(
                file_path=Path("/tmp/test.pdf"),
                file_hash=TEST_HASH,
                content_hash=TEST_CONTENT_HASH,
                format="pdf",
                file_size=2048,
                page_count=2,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
            ),
        )

        document = chunk_document(pdf_document, strategy="fixed")

        assert len(document.chunks) > 0
        # Page tracking should work for PDFs
        # Some chunks should have page numbers
        page_numbers = [c.metadata.page_number for c in document.chunks]
        assert any(p is not None for p in page_numbers)

    def test_chunk_document_no_page_tracking_with_txt(self):
        """Test that TXT documents don't get page numbers."""
        txt_document = Document(
            content="Plain text content without pages.",
            metadata=DocumentMetadata(
                file_path=Path("/tmp/test.txt"),
                file_hash=TEST_HASH,
                content_hash=TEST_CONTENT_HASH,
                format="txt",
                file_size=512,
                page_count=None,  # TXT has no pages
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
            ),
        )

        document = chunk_document(txt_document, strategy="fixed")

        assert len(document.chunks) > 0
        # TXT documents should not have page numbers
        for chunk in document.chunks:
            assert chunk.metadata.page_number is None


class TestChunkingConfiguration:
    """Test chunking configuration via settings."""

    def test_default_chunking_strategy(self):
        """Test default chunking strategy is 'fixed'."""
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.chunking_strategy == "fixed"
        get_settings.cache_clear()

    def test_semantic_configuration_parameters(self):
        """Test semantic chunking configuration parameters."""
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.semantic_similarity_threshold == 0.75
        assert settings.semantic_min_chunk_size == 200
        assert settings.semantic_max_chunk_size == 1500
        get_settings.cache_clear()

    def test_hierarchical_configuration_parameters(self):
        """Test hierarchical chunking configuration parameters."""
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.hierarchical_parent_size == 2000
        assert settings.hierarchical_child_size == 500
        assert settings.hierarchical_parent_overlap == 200
        assert settings.hierarchical_child_overlap == 50
        get_settings.cache_clear()

    def test_invalid_chunking_strategy_validation(self, monkeypatch):
        """Test that invalid chunking_strategy raises ValidationError."""
        get_settings.cache_clear()

        # Try to set invalid strategy via environment variable
        monkeypatch.setenv("RAGGED_CHUNKING_STRATEGY", "invalid")

        with pytest.raises(ValueError, match="chunking_strategy must be one of"):
            Settings()

        get_settings.cache_clear()

    def test_valid_chunking_strategies(self, monkeypatch):
        """Test all valid chunking strategies."""
        get_settings.cache_clear()

        for strategy in ["fixed", "semantic", "hierarchical"]:
            get_settings.cache_clear()
            monkeypatch.setenv("RAGGED_CHUNKING_STRATEGY", strategy)

            settings = Settings()
            assert settings.chunking_strategy == strategy

        get_settings.cache_clear()


class TestSemanticChunkingWithMockedModel:
    """Test semantic chunking with mocked sentence transformer model."""

    def test_semantic_chunking_detects_topic_boundaries(self):
        """Test that semantic chunking with realistic model mocking."""
        # Create chunker and manually set up mocked model
        chunker = SemanticChunker(
            similarity_threshold=0.8,
            min_sentences_per_chunk=1,
            min_chunk_size=10,
        )

        # Create a mock model
        mock_model = MagicMock()

        # Create embeddings that show topic change
        def mock_encode(sentences, **kwargs):  # Accept kwargs for show_progress_bar etc.
            num_sentences = len(sentences)
            embeddings = []
            for i in range(num_sentences):
                if i < num_sentences // 2:
                    embeddings.append([1.0, 0.0, 0.0])  # First topic
                else:
                    embeddings.append([0.0, 0.0, 1.0])  # Different topic
            return np.array(embeddings)

        mock_model.encode = mock_encode
        chunker._model = mock_model  # Inject mock directly

        text = (
            "Machine learning is amazing. Neural networks are powerful. "
            "Deep learning has many applications. "
            "Cooking pasta is easy. Italian cuisine is delicious. "
            "Recipes can be simple."
        )

        chunks = chunker.split_text(text)

        # Should detect topic change (ML → Cooking)
        assert len(chunks) >= 2

    def test_semantic_chunking_end_to_end(self):
        """Test semantic chunking end-to-end with chunk_document."""
        document = Document(
            content=(
                "Artificial intelligence is transforming technology. "
                "Machine learning algorithms learn from data. "
                "Deep neural networks are very effective. "
                "Gardening requires patience and care. "
                "Plants need water and sunlight. "
                "Soil quality is important for growth."
            ),
            metadata=DocumentMetadata(
                file_path=Path("/tmp/test.txt"),
                file_hash=TEST_HASH,
                content_hash=TEST_CONTENT_HASH,
                format="txt",
                file_size=512,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
            ),
        )

        # Semantic chunking will use fallback split (no actual model loading in test)
        chunked_doc = chunk_document(document, strategy="semantic")

        assert len(chunked_doc.chunks) >= 1
        # Fallback creates chunks based on size, not topic detection


class TestHierarchicalChunkingIntegration:
    """Test hierarchical chunking integration."""

    def test_hierarchical_chunking_creates_parent_child_structure(self):
        """Test that hierarchical chunking creates proper parent-child structure."""
        chunker = HierarchicalChunker(
            parent_chunk_size=200,
            child_chunk_size=80,
            parent_overlap=20,
            child_overlap=10,
        )

        text = "This is a longer document. " * 30  # ~840 chars

        # split_text returns child chunks (strings)
        child_chunks = chunker.split_text(text)

        assert len(child_chunks) > 0
        # All should be strings (child chunk text)
        assert all(isinstance(c, str) for c in child_chunks)

    def test_hierarchical_chunking_with_document(self):
        """Test hierarchical chunking with chunk_document function."""
        document = Document(
            content="Paragraph one content. " * 40,  # ~920 chars
            metadata=DocumentMetadata(
                file_path=Path("/tmp/test.txt"),
                file_hash=TEST_HASH,
                content_hash=TEST_CONTENT_HASH,
                format="txt",
                file_size=1024,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
            ),
        )

        chunked_doc = chunk_document(document, strategy="hierarchical")

        assert len(chunked_doc.chunks) > 0

        # All chunks should have proper metadata
        for chunk in chunked_doc.chunks:
            assert chunk.metadata.document_id == document.document_id
            assert chunk.text is not None
            assert chunk.tokens > 0


class TestChunkingCLIIntegration:
    """Test CLI integration for chunking strategies.

    Note: These tests verify the CLI option exists and can be parsed.
    Full end-to-end CLI testing is done in integration tests with real files.
    """

    def test_cli_chunking_strategy_option_validation(self):
        """Test that chunking_strategy option has correct choices."""
        from src.cli.commands.add import add

        # Check that the command has the chunking_strategy option
        param_names = [p.name for p in add.params]
        assert "chunking_strategy" in param_names

        # Get the chunking_strategy parameter
        chunking_strategy_param = next(
            p for p in add.params if p.name == "chunking_strategy"
        )

        # Verify it's a Choice type with correct values
        assert hasattr(chunking_strategy_param.type, "choices")
        expected_choices = ["fixed", "semantic", "hierarchical"]
        actual_choices = list(chunking_strategy_param.type.choices)
        assert set(actual_choices) == set(expected_choices)
