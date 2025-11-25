"""Unit tests for similarity analytics module."""

import pytest
import numpy as np

from ragged.analytics.similarity import (
    SimilarityEdge,
    DocumentNode,
    SimilarityCluster,
    SimilarityGraph,
    SimilarityCalculator,
    ClusterDetector,
    SimilarityAnalytics,
)


class TestSimilarityEdge:
    """Tests for SimilarityEdge dataclass."""

    def test_create_edge(self):
        """Test creating a similarity edge."""
        edge = SimilarityEdge(
            source_id="doc1",
            target_id="doc2",
            similarity=0.85,
        )
        assert edge.source_id == "doc1"
        assert edge.target_id == "doc2"
        assert edge.similarity == 0.85

    def test_to_dict(self):
        """Test edge serialisation."""
        edge = SimilarityEdge("a", "b", 0.9)
        d = edge.to_dict()
        assert d["source"] == "a"
        assert d["target"] == "b"
        assert d["similarity"] == 0.9


class TestDocumentNode:
    """Tests for DocumentNode dataclass."""

    def test_create_node(self):
        """Test creating a document node."""
        node = DocumentNode(
            id="doc1",
            title="Test Document",
            doc_type="pdf",
            size=1000,
        )
        assert node.id == "doc1"
        assert node.title == "Test Document"
        assert node.doc_type == "pdf"
        assert node.cluster_id == -1

    def test_to_dict(self):
        """Test node serialisation."""
        node = DocumentNode("id1", "Title", "markdown", 500, cluster_id=2)
        d = node.to_dict()
        assert d["id"] == "id1"
        assert d["title"] == "Title"
        assert d["cluster_id"] == 2


class TestSimilarityCluster:
    """Tests for SimilarityCluster dataclass."""

    def test_create_cluster(self):
        """Test creating a cluster."""
        cluster = SimilarityCluster(
            cluster_id=0,
            document_ids=["doc1", "doc2", "doc3"],
            centroid_id="doc2",
        )
        assert cluster.cluster_id == 0
        assert len(cluster.document_ids) == 3
        assert cluster.centroid_id == "doc2"

    def test_to_dict(self):
        """Test cluster serialisation."""
        cluster = SimilarityCluster(1, ["a", "b"], "a", keywords=["python"])
        d = cluster.to_dict()
        assert d["cluster_id"] == 1
        assert d["size"] == 2
        assert d["keywords"] == ["python"]


class TestSimilarityGraph:
    """Tests for SimilarityGraph dataclass."""

    def test_create_graph(self):
        """Test creating a similarity graph."""
        nodes = [DocumentNode("1", "Doc 1"), DocumentNode("2", "Doc 2")]
        edges = [SimilarityEdge("1", "2", 0.8)]
        graph = SimilarityGraph(nodes=nodes, edges=edges, threshold=0.7)

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.threshold == 0.7

    def test_to_dict(self):
        """Test graph serialisation."""
        nodes = [DocumentNode("1", "Doc")]
        graph = SimilarityGraph(nodes=nodes, edges=[])
        d = graph.to_dict()

        assert "nodes" in d
        assert "edges" in d
        assert "stats" in d
        assert d["stats"]["node_count"] == 1


class TestSimilarityCalculator:
    """Tests for SimilarityCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create a similarity calculator."""
        return SimilarityCalculator()

    def test_cosine_similarity_identical(self, calculator):
        """Test cosine similarity with identical vectors."""
        vec = np.array([1.0, 2.0, 3.0])
        sim = calculator.cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self, calculator):
        """Test cosine similarity with orthogonal vectors."""
        vec_a = np.array([1.0, 0.0])
        vec_b = np.array([0.0, 1.0])
        sim = calculator.cosine_similarity(vec_a, vec_b)
        assert abs(sim) < 0.001

    def test_cosine_similarity_opposite(self, calculator):
        """Test cosine similarity with opposite vectors."""
        vec_a = np.array([1.0, 2.0])
        vec_b = np.array([-1.0, -2.0])
        sim = calculator.cosine_similarity(vec_a, vec_b)
        assert abs(sim + 1.0) < 0.001

    def test_cosine_similarity_zero_vector(self, calculator):
        """Test cosine similarity with zero vector."""
        vec_a = np.array([1.0, 2.0])
        vec_b = np.array([0.0, 0.0])
        sim = calculator.cosine_similarity(vec_a, vec_b)
        assert sim == 0.0

    def test_compute_similarity_matrix(self, calculator):
        """Test computing pairwise similarity matrix."""
        embeddings = {
            "doc1": np.array([1.0, 0.0, 0.0]),
            "doc2": np.array([1.0, 0.1, 0.0]),
            "doc3": np.array([0.0, 1.0, 0.0]),
        }
        matrix = calculator.compute_similarity_matrix(embeddings)

        # Should have 3 pairs
        assert len(matrix) == 3
        # doc1 and doc2 should be similar
        assert matrix[("doc1", "doc2")] > 0.9
        # doc1 and doc3 should be orthogonal
        assert matrix[("doc1", "doc3")] < 0.1

    def test_build_similarity_graph(self, calculator):
        """Test building similarity graph."""
        documents = [
            {"id": "doc1", "title": "Doc 1", "type": "pdf", "size": 100},
            {"id": "doc2", "title": "Doc 2", "type": "md", "size": 200},
            {"id": "doc3", "title": "Doc 3", "type": "py", "size": 150},
        ]
        embeddings = {
            "doc1": np.array([1.0, 0.0]),
            "doc2": np.array([0.9, 0.1]),
            "doc3": np.array([0.0, 1.0]),
        }

        graph = calculator.build_similarity_graph(documents, embeddings, threshold=0.8)

        assert len(graph.nodes) == 3
        assert graph.threshold == 0.8
        # doc1 and doc2 should be connected
        assert any(
            (e.source_id == "doc1" and e.target_id == "doc2") or
            (e.source_id == "doc2" and e.target_id == "doc1")
            for e in graph.edges
        )

    def test_find_similar_documents(self, calculator):
        """Test finding similar documents."""
        embeddings = {
            "doc1": np.array([1.0, 0.0]),
            "doc2": np.array([0.9, 0.1]),
            "doc3": np.array([0.8, 0.2]),
            "doc4": np.array([0.0, 1.0]),
        }

        similar = calculator.find_similar_documents("doc1", embeddings, limit=2)
        assert len(similar) == 2
        # doc2 should be most similar to doc1
        assert similar[0][0] == "doc2"

    def test_find_duplicates(self, calculator):
        """Test finding duplicate documents."""
        embeddings = {
            "doc1": np.array([1.0, 0.0, 0.0]),
            "doc2": np.array([1.0, 0.01, 0.0]),  # Near duplicate
            "doc3": np.array([0.0, 1.0, 0.0]),
        }

        duplicates = calculator.find_duplicates(embeddings, threshold=0.99)
        assert len(duplicates) == 1
        assert duplicates[0][0] == "doc1"
        assert duplicates[0][1] == "doc2"

    def test_find_isolated_documents(self, calculator):
        """Test finding isolated documents."""
        embeddings = {
            "doc1": np.array([1.0, 0.0]),
            "doc2": np.array([0.9, 0.1]),
            "isolated": np.array([0.0, 1.0]),  # Different from others
        }

        isolated = calculator.find_isolated_documents(embeddings, threshold=0.8)
        assert "isolated" in isolated


class TestClusterDetector:
    """Tests for ClusterDetector."""

    @pytest.fixture
    def detector(self):
        """Create a cluster detector."""
        return ClusterDetector(min_cluster_size=2)

    def test_detect_clusters_simple(self, detector):
        """Test detecting clusters."""
        # Two clusters: (doc1, doc2) and (doc3, doc4)
        embeddings = {
            "doc1": np.array([1.0, 0.0]),
            "doc2": np.array([0.9, 0.1]),
            "doc3": np.array([0.0, 1.0]),
            "doc4": np.array([0.1, 0.9]),
        }

        clusters = detector.detect_clusters_simple(embeddings, threshold=0.8)

        assert len(clusters) == 2
        # Check cluster membership
        all_docs = set()
        for cluster in clusters:
            all_docs.update(cluster.document_ids)
        assert all_docs == {"doc1", "doc2", "doc3", "doc4"}

    def test_detect_clusters_with_outlier(self, detector):
        """Test that outliers are not in clusters."""
        embeddings = {
            "doc1": np.array([1.0, 0.0]),
            "doc2": np.array([0.9, 0.1]),
            "outlier": np.array([0.5, 0.5]),  # Different from both groups
        }

        clusters = detector.detect_clusters_simple(embeddings, threshold=0.8)

        # Only doc1 and doc2 should form a cluster
        assert len(clusters) == 1
        assert set(clusters[0].document_ids) == {"doc1", "doc2"}

    def test_assign_clusters_to_graph(self, detector):
        """Test assigning clusters to graph nodes."""
        nodes = [
            DocumentNode("doc1", "Doc 1"),
            DocumentNode("doc2", "Doc 2"),
            DocumentNode("doc3", "Doc 3"),
        ]
        graph = SimilarityGraph(nodes=nodes, edges=[])
        clusters = [
            SimilarityCluster(0, ["doc1", "doc2"]),
            SimilarityCluster(1, ["doc3"]),
        ]

        result = detector.assign_clusters_to_graph(graph, clusters)

        # Check nodes have cluster IDs
        node_clusters = {n.id: n.cluster_id for n in result.nodes}
        assert node_clusters["doc1"] == 0
        assert node_clusters["doc2"] == 0


class TestSimilarityAnalytics:
    """Tests for SimilarityAnalytics."""

    @pytest.fixture
    def analytics(self):
        """Create similarity analytics instance."""
        return SimilarityAnalytics()

    def test_analyze(self, analytics):
        """Test comprehensive analysis."""
        documents = [
            {"id": "doc1", "title": "Python Guide"},
            {"id": "doc2", "title": "Python Tutorial"},
            {"id": "doc3", "title": "JavaScript Basics"},
        ]
        embeddings = {
            "doc1": np.array([1.0, 0.0, 0.0]),
            "doc2": np.array([0.95, 0.05, 0.0]),
            "doc3": np.array([0.0, 0.0, 1.0]),
        }

        result = analytics.analyze(documents, embeddings, threshold=0.7)

        assert "graph" in result
        assert "duplicates" in result
        assert "isolated_documents" in result
        assert "insights" in result

        # doc3 should be isolated
        assert "doc3" in result["isolated_documents"]

    def test_analyze_generates_insights(self, analytics):
        """Test that analysis generates insights."""
        documents = [{"id": f"doc{i}", "title": f"Doc {i}"} for i in range(5)]
        # Create two clusters
        embeddings = {
            "doc0": np.array([1.0, 0.0]),
            "doc1": np.array([0.9, 0.1]),
            "doc2": np.array([0.0, 1.0]),
            "doc3": np.array([0.1, 0.9]),
            "doc4": np.array([0.5, 0.5]),  # Outlier
        }

        result = analytics.analyze(documents, embeddings, threshold=0.8)

        assert len(result["insights"]) > 0
        # Should mention clusters
        assert any("cluster" in i.lower() for i in result["insights"])
