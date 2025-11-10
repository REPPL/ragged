"""Tests for BM25 keyword-based retrieval."""

import pytest
from src.retrieval.bm25 import BM25Retriever


@pytest.fixture
def sample_docs():
    """Sample documents for testing."""
    return [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language for data science",
        "Natural language processing enables computers to understand text",
        "Deep learning uses neural networks with multiple layers",
    ]


@pytest.fixture
def sample_doc_ids():
    """Sample document IDs."""
    return ["doc1", "doc2", "doc3", "doc4", "doc5"]


@pytest.fixture
def sample_metadatas():
    """Sample metadata for documents."""
    return [
        {"source_file": "file1.txt", "chunk_index": 0},
        {"source_file": "file2.txt", "chunk_index": 0},
        {"source_file": "file3.txt", "chunk_index": 0},
        {"source_file": "file4.txt", "chunk_index": 0},
        {"source_file": "file5.txt", "chunk_index": 0},
    ]


@pytest.fixture
def retriever(sample_docs, sample_doc_ids, sample_metadatas):
    """Initialized BM25 retriever with sample documents."""
    retriever = BM25Retriever()
    retriever.index_documents(sample_docs, sample_doc_ids, sample_metadatas)
    return retriever


class TestBM25Initialization:
    """Test BM25Retriever initialization."""

    def test_init_empty(self):
        """Test initializing empty retriever."""
        retriever = BM25Retriever()
        assert retriever.index is None
        assert retriever.documents == []
        assert retriever.doc_ids == []
        assert retriever.metadatas == []

    def test_count_empty(self):
        """Test count on empty retriever."""
        retriever = BM25Retriever()
        assert retriever.count() == 0


class TestBM25Indexing:
    """Test BM25 document indexing."""

    def test_index_documents(self, sample_docs, sample_doc_ids, sample_metadatas):
        """Test indexing documents."""
        retriever = BM25Retriever()
        retriever.index_documents(sample_docs, sample_doc_ids, sample_metadatas)

        assert retriever.index is not None
        assert len(retriever.documents) == 5
        assert len(retriever.doc_ids) == 5
        assert len(retriever.metadatas) == 5
        assert retriever.count() == 5

    def test_index_without_metadata(self, sample_docs, sample_doc_ids):
        """Test indexing without metadata."""
        retriever = BM25Retriever()
        retriever.index_documents(sample_docs, sample_doc_ids)

        assert len(retriever.metadatas) == 5
        assert all(m == {} for m in retriever.metadatas)

    def test_index_length_mismatch(self):
        """Test indexing with mismatched lengths raises ValueError."""
        retriever = BM25Retriever()

        with pytest.raises(ValueError, match="must have same length"):
            retriever.index_documents(
                ["doc1", "doc2"],
                ["id1"],  # Wrong length
            )

    def test_index_empty_documents(self):
        """Test indexing empty document list."""
        retriever = BM25Retriever()
        retriever.index_documents([], [])

        assert retriever.index is None
        assert retriever.count() == 0


class TestBM25Search:
    """Test BM25 search functionality."""

    def test_search_basic(self, retriever):
        """Test basic search returns results."""
        results = retriever.search("machine learning", top_k=3)

        assert len(results) > 0
        assert len(results) <= 3

        # Check result format
        for doc_id, content, score, metadata in results:
            assert isinstance(doc_id, str)
            assert isinstance(content, str)
            assert isinstance(score, float)
            assert isinstance(metadata, dict)

    def test_search_relevance(self, retriever):
        """Test search returns relevant results."""
        results = retriever.search("machine learning", top_k=5)

        # Top result should contain query terms
        top_doc_id, top_content, top_score, _ = results[0]
        assert "machine learning" in top_content.lower()
        assert top_doc_id == "doc2"

    def test_search_scores_descending(self, retriever):
        """Test search results are sorted by score descending."""
        results = retriever.search("python programming", top_k=5)

        scores = [score for _, _, score, _ in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_top_k_limits_results(self, retriever):
        """Test top_k parameter limits results."""
        results = retriever.search("the", top_k=2)
        assert len(results) <= 2

    def test_search_empty_query(self, retriever):
        """Test empty query returns empty results."""
        results = retriever.search("", top_k=5)
        assert len(results) == 0

    def test_search_no_matches(self, retriever):
        """Test query with no matches returns empty results."""
        results = retriever.search("xyzabc123nonexistent", top_k=5)
        # Should return empty list or very low scores
        assert len(results) == 0 or all(score < 0.1 for _, _, score, _ in results)

    def test_search_before_indexing(self):
        """Test search before indexing raises RuntimeError."""
        retriever = BM25Retriever()

        with pytest.raises(RuntimeError, match="No documents indexed"):
            retriever.search("test query", top_k=5)


class TestBM25TopKIndices:
    """Test get_top_k_indices method."""

    def test_get_top_k_indices(self, retriever):
        """Test getting top-k document indices."""
        indices = retriever.get_top_k_indices("machine learning", top_k=3)

        assert len(indices) <= 3
        assert all(isinstance(i, int) for i in indices)
        assert all(0 <= i < retriever.count() for i in indices)

    def test_get_top_k_indices_before_indexing(self):
        """Test get_top_k_indices before indexing raises RuntimeError."""
        retriever = BM25Retriever()

        with pytest.raises(RuntimeError, match="No documents indexed"):
            retriever.get_top_k_indices("test", top_k=5)


class TestBM25Clear:
    """Test clearing BM25 index."""

    def test_clear(self, retriever):
        """Test clearing retriever."""
        assert retriever.count() == 5

        retriever.clear()

        assert retriever.index is None
        assert retriever.documents == []
        assert retriever.doc_ids == []
        assert retriever.metadatas == []
        assert retriever.count() == 0

    def test_clear_empty(self):
        """Test clearing empty retriever."""
        retriever = BM25Retriever()
        retriever.clear()  # Should not raise error
        assert retriever.count() == 0
