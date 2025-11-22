"""Tests for dual embedding storage (v0.5.0)."""

import pytest
import numpy as np
import chromadb
from chromadb.api import ClientAPI

from src.storage.dual_store import DualEmbeddingStore
from src.storage.schema import EmbeddingType


@pytest.fixture
def in_memory_client() -> ClientAPI:
    """Create in-memory ChromaDB client for testing."""
    return chromadb.Client()


@pytest.fixture
def dual_store(in_memory_client: ClientAPI) -> DualEmbeddingStore:
    """Create DualEmbeddingStore with in-memory client."""
    return DualEmbeddingStore(client=in_memory_client)


class TestInitialisation:
    """Test DualEmbeddingStore initialisation."""

    def test_init_with_client(self, in_memory_client: ClientAPI):
        """Test initialisation with existing client."""
        store = DualEmbeddingStore(client=in_memory_client)

        assert store.client is in_memory_client
        assert store.collection_name == "documents"
        assert store.text_collection is not None
        assert store.vision_collection is not None

    def test_init_creates_in_memory_client(self):
        """Test initialisation creates in-memory client by default."""
        store = DualEmbeddingStore()

        assert store.client is not None
        assert store.text_collection is not None
        assert store.vision_collection is not None

    def test_init_with_custom_collection_name(self, in_memory_client: ClientAPI):
        """Test initialisation with custom collection name."""
        store = DualEmbeddingStore(collection_name="custom_docs", client=in_memory_client)

        assert store.collection_name == "custom_docs"

    def test_collections_have_v05_schema(self, dual_store: DualEmbeddingStore):
        """Test that created collections have v0.5 schema metadata."""
        text_metadata = dual_store.text_collection.metadata
        vision_metadata = dual_store.vision_collection.metadata

        assert text_metadata is not None
        assert text_metadata.get("schema_version") == "v0.5"
        assert text_metadata.get("embedding_type") == "text"

        assert vision_metadata is not None
        assert vision_metadata.get("schema_version") == "v0.5"
        assert vision_metadata.get("embedding_type") == "vision"


class TestAddTextEmbedding:
    """Test adding text embeddings."""

    def test_add_basic_text_embedding(self, dual_store: DualEmbeddingStore):
        """Test adding basic text embedding."""
        embedding = np.random.rand(384)

        embedding_id = dual_store.add_text_embedding(
            document_id="doc123",
            chunk_id="chunk_0",
            chunk_index=0,
            embedding=embedding,
            text_content="Sample text",
        )

        assert embedding_id == "doc123_chunk_0_text"

        # Verify stored
        results = dual_store.text_collection.get(ids=[embedding_id])
        assert len(results["ids"]) == 1
        assert results["metadatas"][0]["embedding_type"] == "text"

    def test_add_text_embedding_with_page(self, dual_store: DualEmbeddingStore):
        """Test adding text embedding with page number."""
        embedding = np.random.rand(384)

        dual_store.add_text_embedding(
            document_id="doc123",
            chunk_id="chunk_5",
            chunk_index=5,
            embedding=embedding,
            text_content="Text on page 3",
            page_number=2,
        )

        results = dual_store.text_collection.get(ids=["doc123_chunk_5_text"])
        assert results["metadatas"][0]["page_number"] == 2

    def test_add_text_embedding_wrong_dimension(self, dual_store: DualEmbeddingStore):
        """Test adding text embedding with wrong dimension raises error."""
        wrong_embedding = np.random.rand(128)  # Should be 384

        with pytest.raises(ValueError, match="Text embedding must be 384-dimensional"):
            dual_store.add_text_embedding(
                document_id="doc1",
                chunk_id="c1",
                chunk_index=0,
                embedding=wrong_embedding,
                text_content="text",
            )

    def test_add_multiple_text_embeddings(self, dual_store: DualEmbeddingStore):
        """Test adding multiple text embeddings for same document."""
        for i in range(5):
            embedding = np.random.rand(384)
            dual_store.add_text_embedding(
                document_id="doc123",
                chunk_id=f"chunk_{i}",
                chunk_index=i,
                embedding=embedding,
                text_content=f"Chunk {i}",
            )

        results = dual_store.get_by_document("doc123", EmbeddingType.TEXT)
        assert len(results["ids"]) == 5


class TestAddVisionEmbedding:
    """Test adding vision embeddings."""

    def test_add_basic_vision_embedding(self, dual_store: DualEmbeddingStore):
        """Test adding basic vision embedding."""
        embedding = np.random.rand(128)

        embedding_id = dual_store.add_vision_embedding(
            document_id="doc123",
            page_number=0,
            embedding=embedding,
            image_hash="abc123",
        )

        assert embedding_id == "doc123_page_0_vision"

        # Verify stored
        results = dual_store.vision_collection.get(ids=[embedding_id])
        assert len(results["ids"]) == 1
        assert results["metadatas"][0]["embedding_type"] == "vision"

    def test_add_vision_embedding_with_features(self, dual_store: DualEmbeddingStore):
        """Test adding vision embedding with diagram/table flags."""
        embedding = np.random.rand(128)

        dual_store.add_vision_embedding(
            document_id="doc123",
            page_number=5,
            embedding=embedding,
            image_hash="hash789",
            has_diagrams=True,
            has_tables=True,
            layout_complexity="complex",
        )

        results = dual_store.vision_collection.get(ids=["doc123_page_5_vision"])
        metadata = results["metadatas"][0]

        assert metadata["has_diagrams"] is True
        assert metadata["has_tables"] is True
        assert metadata["layout_complexity"] == "complex"

    def test_add_vision_embedding_wrong_dimension(self, dual_store: DualEmbeddingStore):
        """Test adding vision embedding with wrong dimension raises error."""
        wrong_embedding = np.random.rand(384)  # Should be 128

        with pytest.raises(ValueError, match="Vision embedding must be 128-dimensional"):
            dual_store.add_vision_embedding(
                document_id="doc1", page_number=0, embedding=wrong_embedding, image_hash="hash"
            )

    def test_add_multiple_vision_embeddings(self, dual_store: DualEmbeddingStore):
        """Test adding multiple vision embeddings for same document."""
        for i in range(5):
            embedding = np.random.rand(128)
            dual_store.add_vision_embedding(
                document_id="doc123",
                page_number=i,
                embedding=embedding,
                image_hash=f"hash_{i}",
            )

        results = dual_store.get_by_document("doc123", EmbeddingType.VISION)
        assert len(results["ids"]) == 5


class TestQueryText:
    """Test text-only querying."""

    def test_query_text_basic(self, dual_store: DualEmbeddingStore):
        """Test basic text query."""
        # Add some text embeddings
        for i in range(5):
            embedding = np.random.rand(384)
            dual_store.add_text_embedding(
                document_id="doc1",
                chunk_id=f"c{i}",
                chunk_index=i,
                embedding=embedding,
                text_content=f"text {i}",
            )

        # Query
        query_emb = np.random.rand(384)
        results = dual_store.query_text(query_emb, k=3)

        assert len(results["ids"][0]) == 3
        assert all("_text" in id for id in results["ids"][0])

    def test_query_text_filters_vision(self, dual_store: DualEmbeddingStore):
        """Test that text query excludes vision embeddings."""
        # Add both types
        dual_store.add_text_embedding(
            "doc1", "c0", 0, np.random.rand(384), "text"
        )
        dual_store.add_vision_embedding(
            "doc1", 0, np.random.rand(128), "hash"
        )

        # Query text
        query_emb = np.random.rand(384)
        results = dual_store.query_text(query_emb, k=5)

        # Should only get text embeddings
        assert len(results["ids"][0]) == 1
        assert results["ids"][0][0].endswith("_text")

    def test_query_text_wrong_dimension(self, dual_store: DualEmbeddingStore):
        """Test text query with wrong dimension raises error."""
        wrong_query = np.random.rand(128)

        with pytest.raises(ValueError, match="Text query must be 384-dimensional"):
            dual_store.query_text(wrong_query)

    def test_query_text_with_filter(self, dual_store: DualEmbeddingStore):
        """Test text query with metadata filter."""
        # Add embeddings from different documents
        dual_store.add_text_embedding("doc1", "c0", 0, np.random.rand(384), "text 1")
        dual_store.add_text_embedding("doc2", "c0", 0, np.random.rand(384), "text 2")

        # Query with filter
        query_emb = np.random.rand(384)
        results = dual_store.query_text(query_emb, k=5, where_filter={"document_id": "doc1"})

        assert len(results["ids"][0]) == 1
        assert results["metadatas"][0][0]["document_id"] == "doc1"


class TestQueryVision:
    """Test vision-only querying."""

    def test_query_vision_basic(self, dual_store: DualEmbeddingStore):
        """Test basic vision query."""
        # Add some vision embeddings
        for i in range(5):
            embedding = np.random.rand(128)
            dual_store.add_vision_embedding(
                document_id="doc1",
                page_number=i,
                embedding=embedding,
                image_hash=f"hash_{i}",
            )

        # Query
        query_emb = np.random.rand(128)
        results = dual_store.query_vision(query_emb, k=3)

        assert len(results["ids"][0]) == 3
        assert all("_vision" in id for id in results["ids"][0])

    def test_query_vision_filters_text(self, dual_store: DualEmbeddingStore):
        """Test that vision query excludes text embeddings."""
        # Add both types
        dual_store.add_text_embedding("doc1", "c0", 0, np.random.rand(384), "text")
        dual_store.add_vision_embedding("doc1", 0, np.random.rand(128), "hash")

        # Query vision
        query_emb = np.random.rand(128)
        results = dual_store.query_vision(query_emb, k=5)

        # Should only get vision embeddings
        assert len(results["ids"][0]) == 1
        assert results["ids"][0][0].endswith("_vision")

    def test_query_vision_wrong_dimension(self, dual_store: DualEmbeddingStore):
        """Test vision query with wrong dimension raises error."""
        wrong_query = np.random.rand(384)

        with pytest.raises(ValueError, match="Vision query must be 128-dimensional"):
            dual_store.query_vision(wrong_query)


class TestQueryHybrid:
    """Test hybrid text+vision querying with RRF."""

    def test_query_hybrid_both_embeddings(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with both text and vision embeddings."""
        # Add both types
        for i in range(3):
            dual_store.add_text_embedding(
                f"doc{i}", f"c0", 0, np.random.rand(384), f"text {i}"
            )
            dual_store.add_vision_embedding(
                f"doc{i}", 0, np.random.rand(128), f"hash_{i}"
            )

        # Query hybrid
        text_emb = np.random.rand(384)
        vision_emb = np.random.rand(128)
        results = dual_store.query_hybrid(
            text_embedding=text_emb,
            vision_embedding=vision_emb,
            k=3,
        )

        # Should return merged results
        assert len(results["ids"][0]) <= 3
        assert "rrf_scores" in results

    def test_query_hybrid_text_only(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with only text embedding."""
        dual_store.add_text_embedding("doc1", "c0", 0, np.random.rand(384), "text")

        text_emb = np.random.rand(384)
        results = dual_store.query_hybrid(text_embedding=text_emb, k=5)

        assert len(results["ids"][0]) == 1
        assert "rrf_scores" in results

    def test_query_hybrid_vision_only(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with only vision embedding."""
        dual_store.add_vision_embedding("doc1", 0, np.random.rand(128), "hash")

        vision_emb = np.random.rand(128)
        results = dual_store.query_hybrid(vision_embedding=vision_emb, k=5)

        assert len(results["ids"][0]) == 1
        assert "rrf_scores" in results

    def test_query_hybrid_neither_raises_error(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with neither embedding raises error."""
        with pytest.raises(ValueError, match="At least one embedding"):
            dual_store.query_hybrid(k=5)

    def test_query_hybrid_weighted(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with custom weights."""
        dual_store.add_text_embedding("doc1", "c0", 0, np.random.rand(384), "text")
        dual_store.add_vision_embedding("doc1", 0, np.random.rand(128), "hash")

        text_emb = np.random.rand(384)
        vision_emb = np.random.rand(128)

        # Query with custom weights
        results = dual_store.query_hybrid(
            text_embedding=text_emb,
            vision_embedding=vision_emb,
            k=5,
            text_weight=0.7,
            vision_weight=0.3,
        )

        assert len(results["ids"][0]) >= 1

    def test_query_hybrid_negative_weight_raises_error(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with negative weight raises error."""
        with pytest.raises(ValueError, match="Weights must be non-negative"):
            dual_store.query_hybrid(
                text_embedding=np.random.rand(384),
                text_weight=-0.5,
                vision_weight=0.5,
            )

    def test_query_hybrid_zero_weights_raises_error(self, dual_store: DualEmbeddingStore):
        """Test hybrid query with all zero weights raises error."""
        with pytest.raises(ValueError, match="At least one weight must be positive"):
            dual_store.query_hybrid(
                text_embedding=np.random.rand(384),
                text_weight=0.0,
                vision_weight=0.0,
            )

    def test_query_hybrid_rrf_scoring(self, dual_store: DualEmbeddingStore):
        """Test that hybrid query produces RRF scores."""
        # Add multiple embeddings
        for i in range(5):
            dual_store.add_text_embedding(
                f"doc{i}", "c0", 0, np.random.rand(384), f"text {i}"
            )
            dual_store.add_vision_embedding(
                f"doc{i}", 0, np.random.rand(128), f"hash_{i}"
            )

        text_emb = np.random.rand(384)
        vision_emb = np.random.rand(128)
        results = dual_store.query_hybrid(
            text_embedding=text_emb,
            vision_embedding=vision_emb,
            k=3,
        )

        # Check RRF scores exist and are sorted
        rrf_scores = results["rrf_scores"][0]
        assert len(rrf_scores) == len(results["ids"][0])
        assert all(isinstance(score, float) for score in rrf_scores)
        assert rrf_scores == sorted(rrf_scores, reverse=True)  # Descending order


class TestGetByDocument:
    """Test document-based retrieval."""

    def test_get_by_document_both_types(self, dual_store: DualEmbeddingStore):
        """Test retrieving all embeddings for a document."""
        # Add both types
        dual_store.add_text_embedding("doc123", "c0", 0, np.random.rand(384), "text")
        dual_store.add_text_embedding("doc123", "c1", 1, np.random.rand(384), "text")
        dual_store.add_vision_embedding("doc123", 0, np.random.rand(128), "hash1")
        dual_store.add_vision_embedding("doc123", 1, np.random.rand(128), "hash2")

        results = dual_store.get_by_document("doc123")

        assert len(results["ids"]) == 4

    def test_get_by_document_text_only(self, dual_store: DualEmbeddingStore):
        """Test retrieving only text embeddings for a document."""
        dual_store.add_text_embedding("doc123", "c0", 0, np.random.rand(384), "text")
        dual_store.add_vision_embedding("doc123", 0, np.random.rand(128), "hash")

        results = dual_store.get_by_document("doc123", EmbeddingType.TEXT)

        assert len(results["ids"]) == 1
        assert results["ids"][0].endswith("_text")

    def test_get_by_document_vision_only(self, dual_store: DualEmbeddingStore):
        """Test retrieving only vision embeddings for a document."""
        dual_store.add_text_embedding("doc123", "c0", 0, np.random.rand(384), "text")
        dual_store.add_vision_embedding("doc123", 0, np.random.rand(128), "hash")

        results = dual_store.get_by_document("doc123", EmbeddingType.VISION)

        assert len(results["ids"]) == 1
        assert results["ids"][0].endswith("_vision")

    def test_get_by_document_nonexistent(self, dual_store: DualEmbeddingStore):
        """Test retrieving non-existent document returns empty."""
        results = dual_store.get_by_document("nonexistent")

        assert len(results["ids"]) == 0


class TestDeleteDocument:
    """Test document deletion."""

    def test_delete_document_removes_all(self, dual_store: DualEmbeddingStore):
        """Test deleting document removes all embeddings."""
        # Add both types
        dual_store.add_text_embedding("doc123", "c0", 0, np.random.rand(384), "text")
        dual_store.add_vision_embedding("doc123", 0, np.random.rand(128), "hash")

        count = dual_store.delete_document("doc123")

        assert count == 2

        # Verify deleted
        results = dual_store.get_by_document("doc123")
        assert len(results["ids"]) == 0

    def test_delete_document_preserves_others(self, dual_store: DualEmbeddingStore):
        """Test deleting document preserves other documents."""
        dual_store.add_text_embedding("doc1", "c0", 0, np.random.rand(384), "text 1")
        dual_store.add_text_embedding("doc2", "c0", 0, np.random.rand(384), "text 2")

        dual_store.delete_document("doc1")

        # doc2 should still exist
        results = dual_store.get_by_document("doc2")
        assert len(results["ids"]) == 1

    def test_delete_nonexistent_document(self, dual_store: DualEmbeddingStore):
        """Test deleting non-existent document returns 0."""
        count = dual_store.delete_document("nonexistent")

        assert count == 0
