"""Document similarity analytics.

Provides similarity calculations, clustering, and network analysis
for document embeddings to enable knowledge exploration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarityEdge:
    """An edge in the similarity graph.

    Attributes:
        source_id: Source document ID
        target_id: Target document ID
        similarity: Cosine similarity score (0-1)
    """

    source_id: str
    target_id: str
    similarity: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source_id,
            "target": self.target_id,
            "similarity": self.similarity,
        }


@dataclass
class DocumentNode:
    """A node in the similarity graph.

    Attributes:
        id: Document ID
        title: Document title
        doc_type: Document type (pdf, markdown, code, etc.)
        size: Document size in characters
        cluster_id: Assigned cluster ID
        metadata: Additional metadata
    """

    id: str
    title: str
    doc_type: str = "unknown"
    size: int = 0
    cluster_id: int = -1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.doc_type,
            "size": self.size,
            "cluster_id": self.cluster_id,
            "metadata": self.metadata,
        }


@dataclass
class SimilarityCluster:
    """A cluster of similar documents.

    Attributes:
        cluster_id: Cluster identifier
        document_ids: List of document IDs in cluster
        centroid_id: ID of document closest to centroid
        keywords: Common keywords in cluster
        size: Number of documents
    """

    cluster_id: int
    document_ids: list[str]
    centroid_id: str = ""
    keywords: list[str] = field(default_factory=list)
    size: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "document_ids": self.document_ids,
            "centroid_id": self.centroid_id,
            "keywords": self.keywords,
            "size": self.size or len(self.document_ids),
        }


@dataclass
class SimilarityGraph:
    """Complete similarity graph with nodes, edges, and clusters.

    Attributes:
        nodes: Document nodes
        edges: Similarity edges
        clusters: Detected clusters
        threshold: Similarity threshold used
        computed_at: When graph was computed
    """

    nodes: list[DocumentNode]
    edges: list[SimilarityEdge]
    clusters: list[SimilarityCluster] = field(default_factory=list)
    threshold: float = 0.7
    computed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "clusters": [c.to_dict() for c in self.clusters],
            "threshold": self.threshold,
            "computed_at": self.computed_at.isoformat(),
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "cluster_count": len(self.clusters),
            },
        }


class SimilarityCalculator:
    """Calculates document similarity from embeddings.

    Uses cosine similarity to measure semantic relatedness between
    document embeddings.
    """

    def __init__(self, cache_ttl: int = 3600) -> None:
        """Initialise similarity calculator.

        Args:
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[datetime, Any]] = {}

    def cosine_similarity(
        self,
        vec_a: np.ndarray,
        vec_b: np.ndarray,
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec_a: First embedding vector
            vec_b: Second embedding vector

        Returns:
            Cosine similarity (0-1)
        """
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    def compute_similarity_matrix(
        self,
        embeddings: dict[str, np.ndarray],
    ) -> dict[tuple[str, str], float]:
        """Compute pairwise similarity matrix.

        Args:
            embeddings: Dictionary mapping document IDs to embeddings

        Returns:
            Dictionary mapping (doc_id_a, doc_id_b) to similarity score
        """
        doc_ids = list(embeddings.keys())
        n = len(doc_ids)
        similarities: dict[tuple[str, str], float] = {}

        for i in range(n):
            for j in range(i + 1, n):
                id_a = doc_ids[i]
                id_b = doc_ids[j]
                sim = self.cosine_similarity(embeddings[id_a], embeddings[id_b])
                similarities[(id_a, id_b)] = sim

        return similarities

    def build_similarity_graph(
        self,
        documents: list[dict[str, Any]],
        embeddings: dict[str, np.ndarray],
        threshold: float = 0.7,
    ) -> SimilarityGraph:
        """Build a similarity graph from documents and embeddings.

        Args:
            documents: List of document metadata dicts with id, title, type, size
            embeddings: Dictionary mapping document IDs to embeddings
            threshold: Minimum similarity to include edge

        Returns:
            SimilarityGraph with nodes and edges
        """
        # Create nodes
        nodes = []
        for doc in documents:
            doc_id = doc.get("id", "")
            if doc_id in embeddings:
                nodes.append(
                    DocumentNode(
                        id=doc_id,
                        title=doc.get("title", doc_id),
                        doc_type=doc.get("type", "unknown"),
                        size=doc.get("size", 0),
                        metadata=doc.get("metadata", {}),
                    )
                )

        # Compute similarities and create edges
        similarities = self.compute_similarity_matrix(embeddings)
        edges = []

        for (id_a, id_b), sim in similarities.items():
            if sim >= threshold:
                edges.append(SimilarityEdge(source_id=id_a, target_id=id_b, similarity=sim))

        return SimilarityGraph(nodes=nodes, edges=edges, threshold=threshold)

    def find_similar_documents(
        self,
        doc_id: str,
        embeddings: dict[str, np.ndarray],
        limit: int = 10,
        threshold: float = 0.5,
    ) -> list[tuple[str, float]]:
        """Find documents similar to a given document.

        Args:
            doc_id: Target document ID
            embeddings: Dictionary mapping document IDs to embeddings
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of (document_id, similarity) tuples, sorted by similarity
        """
        if doc_id not in embeddings:
            return []

        target_embedding = embeddings[doc_id]
        similarities = []

        for other_id, other_embedding in embeddings.items():
            if other_id == doc_id:
                continue

            sim = self.cosine_similarity(target_embedding, other_embedding)
            if sim >= threshold:
                similarities.append((other_id, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def find_duplicates(
        self,
        embeddings: dict[str, np.ndarray],
        threshold: float = 0.95,
    ) -> list[tuple[str, str, float]]:
        """Find potential duplicate documents.

        Args:
            embeddings: Dictionary mapping document IDs to embeddings
            threshold: Similarity threshold for duplicate detection

        Returns:
            List of (doc_id_a, doc_id_b, similarity) tuples for duplicates
        """
        similarities = self.compute_similarity_matrix(embeddings)
        duplicates = []

        for (id_a, id_b), sim in similarities.items():
            if sim >= threshold:
                duplicates.append((id_a, id_b, sim))

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def find_isolated_documents(
        self,
        embeddings: dict[str, np.ndarray],
        threshold: float = 0.5,
    ) -> list[str]:
        """Find documents with no similar matches.

        Args:
            embeddings: Dictionary mapping document IDs to embeddings
            threshold: Similarity threshold

        Returns:
            List of isolated document IDs
        """
        doc_ids = list(embeddings.keys())
        has_connection = {doc_id: False for doc_id in doc_ids}

        similarities = self.compute_similarity_matrix(embeddings)

        for (id_a, id_b), sim in similarities.items():
            if sim >= threshold:
                has_connection[id_a] = True
                has_connection[id_b] = True

        return [doc_id for doc_id, connected in has_connection.items() if not connected]


class ClusterDetector:
    """Detects clusters in document embeddings.

    Uses simple clustering algorithms to group similar documents.
    """

    def __init__(self, min_cluster_size: int = 2) -> None:
        """Initialise cluster detector.

        Args:
            min_cluster_size: Minimum documents per cluster
        """
        self.min_cluster_size = min_cluster_size

    def detect_clusters_simple(
        self,
        embeddings: dict[str, np.ndarray],
        threshold: float = 0.7,
    ) -> list[SimilarityCluster]:
        """Detect clusters using simple connected components.

        This is a lightweight alternative to full clustering algorithms
        that doesn't require scipy/sklearn.

        Args:
            embeddings: Dictionary mapping document IDs to embeddings
            threshold: Similarity threshold for grouping

        Returns:
            List of detected clusters
        """
        calculator = SimilarityCalculator()
        similarities = calculator.compute_similarity_matrix(embeddings)

        # Build adjacency list
        doc_ids = list(embeddings.keys())
        adjacency: dict[str, set[str]] = {doc_id: set() for doc_id in doc_ids}

        for (id_a, id_b), sim in similarities.items():
            if sim >= threshold:
                adjacency[id_a].add(id_b)
                adjacency[id_b].add(id_a)

        # Find connected components using BFS
        visited: set[str] = set()
        clusters: list[SimilarityCluster] = []
        cluster_id = 0

        for start_id in doc_ids:
            if start_id in visited:
                continue

            # BFS to find connected component
            component: list[str] = []
            queue = [start_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                component.append(current)

                for neighbour in adjacency[current]:
                    if neighbour not in visited:
                        queue.append(neighbour)

            # Only keep clusters meeting minimum size
            if len(component) >= self.min_cluster_size:
                # Find centroid (document with highest average similarity to others)
                centroid_id = self._find_centroid(component, embeddings, calculator)

                clusters.append(
                    SimilarityCluster(
                        cluster_id=cluster_id,
                        document_ids=component,
                        centroid_id=centroid_id,
                        size=len(component),
                    )
                )
                cluster_id += 1

        return clusters

    def _find_centroid(
        self,
        doc_ids: list[str],
        embeddings: dict[str, np.ndarray],
        calculator: SimilarityCalculator,
    ) -> str:
        """Find the centroid document (most similar to all others)."""
        if len(doc_ids) <= 1:
            return doc_ids[0] if doc_ids else ""

        best_id = doc_ids[0]
        best_avg_sim = 0.0

        for doc_id in doc_ids:
            total_sim = 0.0
            for other_id in doc_ids:
                if other_id != doc_id:
                    total_sim += calculator.cosine_similarity(
                        embeddings[doc_id], embeddings[other_id]
                    )

            avg_sim = total_sim / (len(doc_ids) - 1)
            if avg_sim > best_avg_sim:
                best_avg_sim = avg_sim
                best_id = doc_id

        return best_id

    def assign_clusters_to_graph(
        self,
        graph: SimilarityGraph,
        clusters: list[SimilarityCluster],
    ) -> SimilarityGraph:
        """Assign cluster IDs to nodes in a similarity graph."""
        # Build mapping from doc_id to cluster_id
        doc_to_cluster: dict[str, int] = {}
        for cluster in clusters:
            for doc_id in cluster.document_ids:
                doc_to_cluster[doc_id] = cluster.cluster_id

        # Update nodes
        for node in graph.nodes:
            node.cluster_id = doc_to_cluster.get(node.id, -1)

        graph.clusters = clusters
        return graph


class SimilarityAnalytics:
    """High-level similarity analytics interface.

    Combines similarity calculation, clustering, and insights
    for document similarity analysis.
    """

    def __init__(self) -> None:
        """Initialise similarity analytics."""
        self.calculator = SimilarityCalculator()
        self.cluster_detector = ClusterDetector()

    def analyze(
        self,
        documents: list[dict[str, Any]],
        embeddings: dict[str, np.ndarray],
        threshold: float = 0.7,
        detect_clusters: bool = True,
    ) -> dict[str, Any]:
        """Perform comprehensive similarity analysis.

        Args:
            documents: Document metadata
            embeddings: Document embeddings
            threshold: Similarity threshold
            detect_clusters: Whether to detect clusters

        Returns:
            Analysis results dictionary
        """
        # Build similarity graph
        graph = self.calculator.build_similarity_graph(
            documents, embeddings, threshold
        )

        # Detect clusters if requested
        if detect_clusters:
            clusters = self.cluster_detector.detect_clusters_simple(
                embeddings, threshold
            )
            graph = self.cluster_detector.assign_clusters_to_graph(graph, clusters)

        # Find duplicates and isolated documents
        duplicates = self.calculator.find_duplicates(embeddings, threshold=0.95)
        isolated = self.calculator.find_isolated_documents(embeddings, threshold)

        # Generate insights
        insights = self._generate_insights(graph, duplicates, isolated)

        return {
            "graph": graph.to_dict(),
            "duplicates": [
                {"doc_a": d[0], "doc_b": d[1], "similarity": d[2]}
                for d in duplicates
            ],
            "isolated_documents": isolated,
            "insights": insights,
        }

    def _generate_insights(
        self,
        graph: SimilarityGraph,
        duplicates: list[tuple[str, str, float]],
        isolated: list[str],
    ) -> list[str]:
        """Generate human-readable insights."""
        insights = []

        # Cluster insights
        if graph.clusters:
            insights.append(f"{len(graph.clusters)} document clusters identified")
            largest = max(graph.clusters, key=lambda c: c.size)
            insights.append(f"Largest cluster has {largest.size} documents")

        # Duplicate insights
        if duplicates:
            insights.append(
                f"{len(duplicates)} potential duplicate pairs found (>95% similar)"
            )

        # Isolated document insights
        if isolated:
            insights.append(
                f"{len(isolated)} documents have no similar matches"
            )

        # Network density
        if graph.nodes:
            max_edges = len(graph.nodes) * (len(graph.nodes) - 1) / 2
            density = len(graph.edges) / max_edges if max_edges > 0 else 0
            if density < 0.1:
                insights.append("Low network density - documents are quite diverse")
            elif density > 0.5:
                insights.append("High network density - documents are closely related")

        return insights


# Module-level convenience functions
_analytics: SimilarityAnalytics | None = None


def get_similarity_analytics() -> SimilarityAnalytics:
    """Get global similarity analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = SimilarityAnalytics()
    return _analytics
