"""Tests for multi-modal query processor."""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image

from src.retrieval.query_processor import (
    MultiModalQueryProcessor,
    QueryEmbeddings,
    QueryType,
)


class MockTextEmbedder:
    """Mock text embedder for testing."""

    def embed(self, text: str) -> np.ndarray:
        """Return mock 384-dim embedding."""
        return np.random.rand(384)


class MockVisionEmbedder:
    """Mock vision embedder for testing."""

    def embed_page(self, image: Image.Image) -> np.ndarray:
        """Return mock 128-dim embedding."""
        return np.random.rand(128)


@pytest.fixture
def mock_text_embedder():
    """Create mock text embedder."""
    return MockTextEmbedder()


@pytest.fixture
def mock_vision_embedder():
    """Create mock vision embedder."""
    return MockVisionEmbedder()


@pytest.fixture
def processor_text_only(mock_text_embedder):
    """Create processor with text embedder only."""
    return MultiModalQueryProcessor(text_embedder=mock_text_embedder, vision_embedder=None)


@pytest.fixture
def processor_full(mock_text_embedder, mock_vision_embedder):
    """Create processor with both embedders."""
    return MultiModalQueryProcessor(
        text_embedder=mock_text_embedder, vision_embedder=mock_vision_embedder
    )


@pytest.fixture
def sample_image():
    """Create sample PIL image for testing."""
    return Image.new("RGB", (100, 100), color="white")


class TestQueryType:
    """Test QueryType enumeration."""

    def test_query_types(self):
        """Test query type values."""
        assert QueryType.TEXT_ONLY == "text_only"
        assert QueryType.IMAGE_ONLY == "image_only"
        assert QueryType.HYBRID == "hybrid"


class TestQueryEmbeddings:
    """Test QueryEmbeddings dataclass."""

    def test_text_only_valid(self):
        """Test valid text-only query embeddings."""
        embeddings = QueryEmbeddings(
            query_type=QueryType.TEXT_ONLY,
            text_embedding=np.random.rand(384),
            text_query="test query",
        )

        assert embeddings.query_type == QueryType.TEXT_ONLY
        assert embeddings.text_embedding is not None
        assert embeddings.vision_embedding is None

    def test_text_only_invalid(self):
        """Test invalid text-only query embeddings."""
        with pytest.raises(ValueError, match="Text-only query requires text embedding"):
            QueryEmbeddings(query_type=QueryType.TEXT_ONLY)

    def test_image_only_valid(self):
        """Test valid image-only query embeddings."""
        embeddings = QueryEmbeddings(
            query_type=QueryType.IMAGE_ONLY,
            vision_embedding=np.random.rand(128),
        )

        assert embeddings.query_type == QueryType.IMAGE_ONLY
        assert embeddings.vision_embedding is not None
        assert embeddings.text_embedding is None

    def test_image_only_invalid(self):
        """Test invalid image-only query embeddings."""
        with pytest.raises(ValueError, match="Image-only query requires vision embedding"):
            QueryEmbeddings(query_type=QueryType.IMAGE_ONLY)

    def test_hybrid_valid(self):
        """Test valid hybrid query embeddings."""
        embeddings = QueryEmbeddings(
            query_type=QueryType.HYBRID,
            text_embedding=np.random.rand(384),
            vision_embedding=np.random.rand(128),
            text_query="test",
        )

        assert embeddings.query_type == QueryType.HYBRID
        assert embeddings.text_embedding is not None
        assert embeddings.vision_embedding is not None

    def test_hybrid_invalid(self):
        """Test invalid hybrid query embeddings."""
        with pytest.raises(ValueError, match="Hybrid query requires both"):
            QueryEmbeddings(
                query_type=QueryType.HYBRID, text_embedding=np.random.rand(384)
            )


class TestMultiModalQueryProcessor:
    """Test MultiModalQueryProcessor."""

    def test_init_with_embedders(self, mock_text_embedder, mock_vision_embedder):
        """Test initialisation with provided embedders."""
        processor = MultiModalQueryProcessor(
            text_embedder=mock_text_embedder, vision_embedder=mock_vision_embedder
        )

        assert processor.text_embedder is mock_text_embedder
        assert processor.vision_embedder is mock_vision_embedder

    def test_process_text_query(self, processor_text_only):
        """Test processing text-only query."""
        result = processor_text_only.process_query(text="test query")

        assert result.query_type == QueryType.TEXT_ONLY
        assert result.text_embedding is not None
        assert result.text_embedding.shape == (384,)
        assert result.vision_embedding is None
        assert result.text_query == "test query"

    def test_process_image_query(self, processor_full, sample_image):
        """Test processing image-only query."""
        result = processor_full.process_query(image=sample_image)

        assert result.query_type == QueryType.IMAGE_ONLY
        assert result.vision_embedding is not None
        assert result.vision_embedding.shape == (128,)
        assert result.text_embedding is None

    def test_process_hybrid_query(self, processor_full, sample_image):
        """Test processing hybrid query."""
        result = processor_full.process_query(text="test query", image=sample_image)

        assert result.query_type == QueryType.HYBRID
        assert result.text_embedding is not None
        assert result.vision_embedding is not None
        assert result.text_embedding.shape == (384,)
        assert result.vision_embedding.shape == (128,)
        assert result.text_query == "test query"

    def test_process_no_input(self, processor_text_only):
        """Test error when no input provided."""
        with pytest.raises(ValueError, match="At least one of text or image"):
            processor_text_only.process_query()

    def test_process_image_without_vision_embedder(self, processor_text_only, sample_image):
        """Test error when image query requested without vision embedder."""
        with pytest.raises(RuntimeError, match="vision embedder not initialised"):
            processor_text_only.process_query(image=sample_image)

    def test_process_text_convenience(self, processor_text_only):
        """Test convenience method for text query."""
        result = processor_text_only.process_text("test")

        assert result.query_type == QueryType.TEXT_ONLY
        assert result.text_embedding is not None

    def test_process_image_convenience(self, processor_full, sample_image):
        """Test convenience method for image query."""
        result = processor_full.process_image(sample_image)

        assert result.query_type == QueryType.IMAGE_ONLY
        assert result.vision_embedding is not None

    def test_process_hybrid_convenience(self, processor_full, sample_image):
        """Test convenience method for hybrid query."""
        result = processor_full.process_hybrid("test", sample_image)

        assert result.query_type == QueryType.HYBRID
        assert result.text_embedding is not None
        assert result.vision_embedding is not None
