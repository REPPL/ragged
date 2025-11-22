"""Tests for vision-aware retriever."""

import pytest
import numpy as np
from PIL import Image
import chromadb

from src.retrieval.vision_retriever import VisionRetriever, RetrievalResult, RetrievalResponse
from src.retrieval.query_processor import MultiModalQueryProcessor, QueryType
from src.storage.dual_store import DualEmbeddingStore


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
def in_memory_client():
    """Create in-memory ChromaDB client."""
    return chromadb.Client()


@pytest.fixture
def dual_store(in_memory_client):
    """Create DualEmbeddingStore with in-memory client."""
    return DualEmbeddingStore(client=in_memory_client)


@pytest.fixture
def query_processor():
    """Create query processor with mock embedders."""
    return MultiModalQueryProcessor(
        text_embedder=MockTextEmbedder(), vision_embedder=MockVisionEmbedder()
    )


@pytest.fixture
def retriever(dual_store, query_processor):
    """Create VisionRetriever with test dependencies."""
    return VisionRetriever(store=dual_store, query_processor=query_processor)


@pytest.fixture
def sample_image():
    """Create sample PIL image for testing."""
    return Image.new("RGB", (100, 100), color="white")


@pytest.fixture
def populated_store(dual_store):
    """Create store with sample data."""
    # Add text embeddings
    for i in range(5):
        dual_store.add_text_embedding(
            document_id=f"doc{i}",
            chunk_id=f"chunk_{i}",
            chunk_index=i,
            embedding=np.random.rand(384),
            text_content=f"Sample text {i}",
        )

    # Add vision embeddings
    for i in range(3):
        dual_store.add_vision_embedding(
            document_id=f"doc{i}",
            page_number=i,
            embedding=np.random.rand(128),
            image_hash=f"hash_{i}",
            has_diagrams=(i % 2 == 0),  # Even pages have diagrams
            has_tables=(i % 2 == 1),  # Odd pages have tables
        )

    return dual_store


class TestRetrievalResult:
    """Test RetrievalResult dataclass."""

    def test_create_result(self):
        """Test creating retrieval result."""
        result = RetrievalResult(
            document_id="doc1",
            embedding_id="doc1_chunk_0_text",
            score=0.95,
            embedding_type="text",
            metadata={"document_id": "doc1"},
            rank=1,
        )

        assert result.document_id == "doc1"
        assert result.score == 0.95
        assert result.rank == 1


class TestRetrievalResponse:
    """Test RetrievalResponse dataclass."""

    def test_create_response(self):
        """Test creating retrieval response."""
        results = [
            RetrievalResult("doc1", "id1", 0.95, "text", {}, 1),
            RetrievalResult("doc2", "id2", 0.85, "text", {}, 2),
        ]

        response = RetrievalResponse(
            results=results,
            query_type=QueryType.TEXT_ONLY,
            total_results=2,
            execution_time_ms=150.5,
        )

        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.query_type == QueryType.TEXT_ONLY


class TestVisionRetrieverInit:
    """Test VisionRetriever initialisation."""

    def test_init_with_defaults(self):
        """Test initialisation with default components."""
        retriever = VisionRetriever()

        assert retriever.store is not None
        assert retriever.query_processor is not None
        assert retriever.default_text_weight == 0.5
        assert retriever.default_vision_weight == 0.5

    def test_init_with_custom_weights(self):
        """Test initialisation with custom weights."""
        retriever = VisionRetriever(default_text_weight=0.7, default_vision_weight=0.3)

        assert retriever.default_text_weight == 0.7
        assert retriever.default_vision_weight == 0.3


class TestVisionRetrieverTextQuery:
    """Test text-only queries."""

    def test_query_text(self):
        """Test basic text query."""
        retriever = VisionRetriever()
        response = retriever.query(text="test query", n_results=5)

        assert response.query_type == QueryType.TEXT_ONLY
        assert isinstance(response.results, list)
        assert response.execution_time_ms > 0

    def test_query_text_with_populated_store(self, populated_store, query_processor):
        """Test text query against populated store."""
        retriever = VisionRetriever(store=populated_store, query_processor=query_processor)
        response = retriever.query(text="test query", n_results=3)

        assert response.total_results <= 3
        if response.results:
            assert all(r.embedding_type == "text" for r in response.results)

    def test_query_text_convenience(self, retriever):
        """Test convenience method for text query."""
        response = retriever.query_text("test", n_results=5)

        assert response.query_type == QueryType.TEXT_ONLY
        assert response.total_results <= 5


class TestVisionRetrieverImageQuery:
    """Test image-only queries."""

    def test_query_image(self, retriever, sample_image):
        """Test basic image query."""
        response = retriever.query(image=sample_image, n_results=5)

        assert response.query_type == QueryType.IMAGE_ONLY
        assert isinstance(response.results, list)

    def test_query_image_with_populated_store(
        self, populated_store, query_processor, sample_image
    ):
        """Test image query against populated store."""
        retriever = VisionRetriever(store=populated_store, query_processor=query_processor)
        response = retriever.query(image=sample_image, n_results=3)

        assert response.total_results <= 3
        if response.results:
            assert all(r.embedding_type == "vision" for r in response.results)

    def test_query_image_convenience(self, retriever, sample_image):
        """Test convenience method for image query."""
        response = retriever.query_image(sample_image, n_results=5)

        assert response.query_type == QueryType.IMAGE_ONLY


class TestVisionRetrieverHybridQuery:
    """Test hybrid text+image queries."""

    def test_query_hybrid(self, retriever, sample_image):
        """Test basic hybrid query."""
        response = retriever.query(
            text="test", image=sample_image, n_results=5, text_weight=0.6, vision_weight=0.4
        )

        assert response.query_type == QueryType.HYBRID
        assert isinstance(response.results, list)

    def test_query_hybrid_convenience(self, retriever, sample_image):
        """Test convenience method for hybrid query."""
        response = retriever.query_hybrid(
            "test", sample_image, n_results=5, text_weight=0.7, vision_weight=0.3
        )

        assert response.query_type == QueryType.HYBRID

    def test_query_hybrid_default_weights(self, retriever, sample_image):
        """Test hybrid query uses default weights."""
        response = retriever.query(text="test", image=sample_image, n_results=5)

        # Should use default weights (0.5, 0.5)
        assert response.query_type == QueryType.HYBRID


class TestVisualBoosting:
    """Test visual content boosting."""

    def test_boost_diagrams(self, populated_store, query_processor):
        """Test diagram boosting."""
        retriever = VisionRetriever(store=populated_store, query_processor=query_processor)

        # Query without boosting
        response_no_boost = retriever.query(text="test", n_results=10, boost_diagrams=False)

        # Query with diagram boosting
        response_with_boost = retriever.query(text="test", n_results=10, boost_diagrams=True)

        # Both should return results
        assert isinstance(response_no_boost.results, list)
        assert isinstance(response_with_boost.results, list)

    def test_boost_tables(self, populated_store, query_processor):
        """Test table boosting."""
        retriever = VisionRetriever(store=populated_store, query_processor=query_processor)

        response = retriever.query(text="test", n_results=10, boost_tables=True)

        assert isinstance(response.results, list)


class TestErrorHandling:
    """Test error handling."""

    def test_query_no_input(self, retriever):
        """Test error when no input provided."""
        with pytest.raises(ValueError, match="At least one of text or image"):
            retriever.query()

    def test_query_image_without_vision_embedder(self, dual_store, sample_image):
        """Test error when vision embedder not available."""
        processor = MultiModalQueryProcessor(text_embedder=MockTextEmbedder(), vision_embedder=None)
        retriever = VisionRetriever(store=dual_store, query_processor=processor)

        with pytest.raises(RuntimeError, match="vision embedder not initialised"):
            retriever.query(image=sample_image)
