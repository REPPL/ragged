"""Tests for Knowledge Graph API endpoints.

v0.9.0: Initial implementation
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_knowledge_graph() -> MagicMock:
    """Create a mock KnowledgeGraph for testing."""
    mock = MagicMock()

    # Default return values
    mock.get_user_interests.return_value = [
        {
            "topic": "machine learning",
            "interest_level": 0.8,
            "frequency": 15,
            "last_accessed": datetime.now(UTC),
        },
        {
            "topic": "python",
            "interest_level": 0.9,
            "frequency": 25,
            "last_accessed": datetime.now(UTC),
        },
    ]

    mock.get_accessed_documents.return_value = [
        {
            "doc_id": "doc_001",
            "title": "Introduction to ML",
            "access_count": 5,
            "last_accessed": datetime.now(UTC),
        },
        {
            "doc_id": "doc_002",
            "title": "Python Guide",
            "access_count": 10,
            "last_accessed": datetime.now(UTC),
        },
    ]

    mock.get_related_documents.return_value = [
        {
            "doc_id": "doc_001",
            "title": "Introduction to ML",
            "relevance": 0.95,
        },
        {
            "doc_id": "doc_003",
            "title": "Deep Learning Basics",
            "relevance": 0.85,
        },
    ]

    mock.export_graph.return_value = {
        "persona": "default",
        "export_timestamp": datetime.now(UTC).isoformat(),
        "interests": [{"topic": "ml", "interest_level": 0.8}],
        "documents": [{"doc_id": "doc_001", "title": "Test Doc"}],
        "topic_document_links": [{"topic": "ml", "doc_id": "doc_001", "relevance": 0.9}],
    }

    return mock


@pytest.fixture
def client(mock_knowledge_graph: MagicMock) -> TestClient:
    """Create a test client with mocked knowledge graph."""
    with patch("ragged.web.routers.graph._knowledge_graph", mock_knowledge_graph):
        with patch("ragged.web.routers.graph.get_knowledge_graph", return_value=mock_knowledge_graph):
            from ragged.web.api import app
            yield TestClient(app)


class TestGraphDataEndpoint:
    """Tests for GET /api/graph/data endpoint."""

    def test_get_graph_data_default_persona(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting graph data for default persona."""
        response = client.get("/api/graph/data")

        assert response.status_code == 200
        data = response.json()

        assert "nodes" in data
        assert "edges" in data
        assert "node_count" in data
        assert "edge_count" in data
        assert data["node_count"] >= 0
        assert data["edge_count"] >= 0

    def test_get_graph_data_custom_persona(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting graph data for custom persona."""
        response = client.get("/api/graph/data?persona=researcher")

        assert response.status_code == 200
        data = response.json()

        mock_knowledge_graph.get_user_interests.assert_called_with("researcher")

    def test_graph_data_contains_user_node(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that graph data includes user node."""
        response = client.get("/api/graph/data?persona=testuser")

        assert response.status_code == 200
        data = response.json()

        user_nodes = [n for n in data["nodes"] if n["type"] == "user"]
        assert len(user_nodes) == 1
        assert user_nodes[0]["id"] == "user_testuser"

    def test_graph_data_contains_topic_nodes(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that graph data includes topic nodes from interests."""
        response = client.get("/api/graph/data")

        assert response.status_code == 200
        data = response.json()

        topic_nodes = [n for n in data["nodes"] if n["type"] == "topic"]
        assert len(topic_nodes) >= 2  # Based on mock data

    def test_graph_data_contains_document_nodes(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that graph data includes document nodes."""
        response = client.get("/api/graph/data")

        assert response.status_code == 200
        data = response.json()

        doc_nodes = [n for n in data["nodes"] if n["type"] == "document"]
        assert len(doc_nodes) >= 1

    def test_graph_data_contains_edges(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that graph data includes relationship edges."""
        response = client.get("/api/graph/data")

        assert response.status_code == 200
        data = response.json()

        # Should have INTERESTED_IN edges
        interested_edges = [e for e in data["edges"] if e["type"] == "INTERESTED_IN"]
        assert len(interested_edges) >= 1

    def test_graph_data_error_handling(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test error handling when graph operations fail."""
        mock_knowledge_graph.get_user_interests.side_effect = Exception("Graph error")

        response = client.get("/api/graph/data")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


class TestInterestsEndpoint:
    """Tests for GET /api/graph/interests/{persona} endpoint."""

    def test_get_interests_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully getting interests for a persona."""
        response = client.get("/api/graph/interests/default")

        assert response.status_code == 200
        data = response.json()

        assert data["persona"] == "default"
        assert "interests" in data
        assert "count" in data
        assert len(data["interests"]) == data["count"]

    def test_get_interests_structure(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that interest response has correct structure."""
        response = client.get("/api/graph/interests/default")

        assert response.status_code == 200
        data = response.json()

        if data["interests"]:
            interest = data["interests"][0]
            assert "topic" in interest
            assert "interest_level" in interest
            assert "frequency" in interest
            assert "last_accessed" in interest

    def test_get_interests_empty(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting interests when none exist."""
        mock_knowledge_graph.get_user_interests.return_value = []

        response = client.get("/api/graph/interests/newuser")

        assert response.status_code == 200
        data = response.json()
        assert data["interests"] == []
        assert data["count"] == 0

    def test_get_interests_validation_error(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test validation error handling."""
        mock_knowledge_graph.get_user_interests.side_effect = ValueError("Invalid persona")

        response = client.get("/api/graph/interests/invalid")

        assert response.status_code == 400


class TestAddInterestEndpoint:
    """Tests for POST /api/graph/interests endpoint."""

    def test_add_interest_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully adding a topic interest."""
        response = client.post(
            "/api/graph/interests",
            json={
                "topic": "deep learning",
                "interest_level": 0.7,
                "persona": "researcher",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "deep learning" in data["message"]

        mock_knowledge_graph.add_topic_interest.assert_called_once_with(
            topic="deep learning",
            interest_level=0.7,
            persona="researcher",
        )

    def test_add_interest_default_level(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test adding interest with default interest level."""
        response = client.post(
            "/api/graph/interests",
            json={
                "topic": "nlp",
                "persona": "default",
            },
        )

        assert response.status_code == 200

        # Should use default interest_level of 0.5
        call_args = mock_knowledge_graph.add_topic_interest.call_args
        assert call_args.kwargs["interest_level"] == 0.5

    def test_add_interest_validation_error(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test validation when interest level is out of range."""
        response = client.post(
            "/api/graph/interests",
            json={
                "topic": "test",
                "interest_level": 1.5,  # Invalid: > 1.0
                "persona": "default",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_add_interest_empty_topic(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test validation when topic is empty."""
        response = client.post(
            "/api/graph/interests",
            json={
                "topic": "",
                "interest_level": 0.5,
                "persona": "default",
            },
        )

        assert response.status_code == 422


class TestAccessedDocumentsEndpoint:
    """Tests for GET /api/graph/documents/{persona} endpoint."""

    def test_get_accessed_documents_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully getting accessed documents."""
        response = client.get("/api/graph/documents/default")

        assert response.status_code == 200
        data = response.json()

        assert data["persona"] == "default"
        assert "documents" in data
        assert "count" in data
        assert len(data["documents"]) == data["count"]

    def test_get_accessed_documents_with_limit(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting accessed documents with custom limit."""
        response = client.get("/api/graph/documents/default?limit=10")

        assert response.status_code == 200
        mock_knowledge_graph.get_accessed_documents.assert_called_with("default", limit=10)

    def test_get_accessed_documents_structure(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that document response has correct structure."""
        response = client.get("/api/graph/documents/default")

        assert response.status_code == 200
        data = response.json()

        if data["documents"]:
            doc = data["documents"][0]
            assert "doc_id" in doc
            assert "title" in doc
            assert "access_count" in doc
            assert "last_accessed" in doc

    def test_get_accessed_documents_limit_validation(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test limit parameter validation."""
        # Limit too high
        response = client.get("/api/graph/documents/default?limit=1000")
        assert response.status_code == 422

        # Limit too low
        response = client.get("/api/graph/documents/default?limit=0")
        assert response.status_code == 422


class TestRecordAccessEndpoint:
    """Tests for POST /api/graph/access endpoint."""

    def test_record_access_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully recording document access."""
        response = client.post(
            "/api/graph/access",
            json={
                "doc_id": "doc_123",
                "title": "Test Document",
                "persona": "default",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "doc_123" in data["message"]

        mock_knowledge_graph.record_document_access.assert_called_once_with(
            doc_id="doc_123",
            title="Test Document",
            persona="default",
        )

    def test_record_access_minimal(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test recording access with minimal data."""
        response = client.post(
            "/api/graph/access",
            json={
                "doc_id": "doc_456",
                "persona": "default",
            },
        )

        assert response.status_code == 200

    def test_record_access_empty_doc_id(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test validation when doc_id is empty."""
        response = client.post(
            "/api/graph/access",
            json={
                "doc_id": "",
                "persona": "default",
            },
        )

        assert response.status_code == 422


class TestRelatedDocumentsEndpoint:
    """Tests for GET /api/graph/related/{topic} endpoint."""

    def test_get_related_documents_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully getting related documents."""
        response = client.get("/api/graph/related/machine%20learning")

        assert response.status_code == 200
        data = response.json()

        assert data["topic"] == "machine learning"
        assert "documents" in data
        assert "count" in data

    def test_get_related_documents_with_limit(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting related documents with custom limit."""
        response = client.get("/api/graph/related/python?limit=25")

        assert response.status_code == 200
        mock_knowledge_graph.get_related_documents.assert_called_with("python", limit=25)

    def test_get_related_documents_structure(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that related document response has correct structure."""
        response = client.get("/api/graph/related/test")

        assert response.status_code == 200
        data = response.json()

        if data["documents"]:
            doc = data["documents"][0]
            assert "doc_id" in doc
            assert "title" in doc
            assert "relevance" in doc

    def test_get_related_documents_empty(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting related documents when none exist."""
        mock_knowledge_graph.get_related_documents.return_value = []

        response = client.get("/api/graph/related/unknown")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["count"] == 0


class TestLinkTopicEndpoint:
    """Tests for POST /api/graph/link endpoint."""

    def test_link_topic_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully linking topic to document."""
        response = client.post(
            "/api/graph/link",
            json={
                "topic": "machine learning",
                "doc_id": "doc_001",
                "relevance": 0.9,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "machine learning" in data["message"]
        assert "doc_001" in data["message"]

        mock_knowledge_graph.link_topic_to_document.assert_called_once_with(
            topic="machine learning",
            doc_id="doc_001",
            relevance=0.9,
        )

    def test_link_topic_default_relevance(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test linking topic with default relevance."""
        response = client.post(
            "/api/graph/link",
            json={
                "topic": "python",
                "doc_id": "doc_002",
            },
        )

        assert response.status_code == 200

        # Should use default relevance of 0.5
        call_args = mock_knowledge_graph.link_topic_to_document.call_args
        assert call_args.kwargs["relevance"] == 0.5

    def test_link_topic_validation_error(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test validation when relevance is out of range."""
        response = client.post(
            "/api/graph/link",
            json={
                "topic": "test",
                "doc_id": "doc_001",
                "relevance": -0.5,  # Invalid: < 0.0
            },
        )

        assert response.status_code == 422


class TestGraphExportEndpoint:
    """Tests for GET /api/graph/export endpoint."""

    def test_export_graph_success(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test successfully exporting graph data."""
        response = client.get("/api/graph/export?persona=default")

        assert response.status_code == 200
        data = response.json()

        assert data["persona"] == "default"
        assert "export_timestamp" in data
        assert "interests" in data
        assert "documents" in data
        assert "topic_document_links" in data

    def test_export_graph_requires_persona(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that persona parameter is required."""
        response = client.get("/api/graph/export")

        assert response.status_code == 422

    def test_export_graph_validation_error(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test validation error handling."""
        mock_knowledge_graph.export_graph.side_effect = ValueError("Persona not found")

        response = client.get("/api/graph/export?persona=nonexistent")

        assert response.status_code == 400


class TestNeighborsEndpoint:
    """Tests for GET /api/graph/neighbors/{node_type}/{node_id} endpoint."""

    def test_get_user_neighbors(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting neighbors for a user node."""
        response = client.get("/api/graph/neighbors/user/default")

        assert response.status_code == 200
        data = response.json()

        assert data["node_id"] == "default"
        assert data["node_type"] == "user"
        assert "neighbors" in data
        assert "edges" in data
        assert "count" in data

    def test_get_topic_neighbors(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting neighbors for a topic node."""
        response = client.get("/api/graph/neighbors/topic/machine%20learning")

        assert response.status_code == 200
        data = response.json()

        assert data["node_type"] == "topic"
        mock_knowledge_graph.get_related_documents.assert_called()

    def test_get_document_neighbors(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test getting neighbors for a document node."""
        response = client.get("/api/graph/neighbors/document/doc_001")

        assert response.status_code == 200
        data = response.json()

        assert data["node_type"] == "document"
        # Documents have no outgoing edges in our schema
        assert data["count"] == 0

    def test_get_neighbors_invalid_type(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test error for invalid node type."""
        response = client.get("/api/graph/neighbors/invalid/test")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_get_neighbors_includes_edges(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that neighbors response includes edge information."""
        response = client.get("/api/graph/neighbors/user/default")

        assert response.status_code == 200
        data = response.json()

        # Should have edges connecting user to topics and documents
        if data["neighbors"]:
            assert len(data["edges"]) > 0
            edge = data["edges"][0]
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge


class TestGraphAPIOpenAPI:
    """Tests for Graph API OpenAPI documentation."""

    def test_openapi_schema_includes_graph_endpoints(
        self, client: TestClient
    ) -> None:
        """Test that OpenAPI schema includes all graph endpoints."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        paths = schema["paths"]
        assert "/api/graph/data" in paths
        assert "/api/graph/interests/{persona}" in paths
        assert "/api/graph/documents/{persona}" in paths
        assert "/api/graph/related/{topic}" in paths
        assert "/api/graph/interests" in paths
        assert "/api/graph/access" in paths
        assert "/api/graph/link" in paths
        assert "/api/graph/export" in paths
        assert "/api/graph/neighbors/{node_type}/{node_id}" in paths

    def test_openapi_schema_has_graph_tag(
        self, client: TestClient
    ) -> None:
        """Test that graph endpoints are tagged correctly."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Check that graph endpoints have the 'graph' tag
        graph_data_path = schema["paths"]["/api/graph/data"]["get"]
        assert "graph" in graph_data_path["tags"]


class TestGraphAPIErrorHandling:
    """Tests for Graph API error handling."""

    def test_graph_unavailable(self) -> None:
        """Test handling when knowledge graph initialisation fails."""
        with patch("ragged.web.routers.graph._knowledge_graph", None):
            with patch("ragged.web.routers.graph.KnowledgeGraph") as mock_cls:
                mock_cls.side_effect = Exception("Database unavailable")

                from ragged.web.api import app
                client = TestClient(app)

                response = client.get("/api/graph/data")

                assert response.status_code == 503
                assert "unavailable" in response.json()["detail"].lower()

    def test_internal_error_returns_500(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that internal errors return 500 status code."""
        mock_knowledge_graph.get_user_interests.side_effect = Exception(
            "Internal processing error"
        )

        response = client.get("/api/graph/data")

        assert response.status_code == 500
        # Error message should be included
        assert "error" in response.json()["detail"].lower()


class TestGraphAPIIntegration:
    """Integration tests for Graph API endpoints."""

    def test_full_workflow(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test a typical workflow: add interest, record access, link, export."""
        # 1. Add an interest
        response = client.post(
            "/api/graph/interests",
            json={
                "topic": "testing",
                "interest_level": 0.8,
                "persona": "developer",
            },
        )
        assert response.status_code == 200

        # 2. Record document access
        response = client.post(
            "/api/graph/access",
            json={
                "doc_id": "test_doc_001",
                "title": "Testing Best Practices",
                "persona": "developer",
            },
        )
        assert response.status_code == 200

        # 3. Link topic to document
        response = client.post(
            "/api/graph/link",
            json={
                "topic": "testing",
                "doc_id": "test_doc_001",
                "relevance": 0.95,
            },
        )
        assert response.status_code == 200

        # 4. Get graph data
        response = client.get("/api/graph/data?persona=developer")
        assert response.status_code == 200

        # 5. Export graph
        response = client.get("/api/graph/export?persona=developer")
        assert response.status_code == 200

    def test_concurrent_operations(
        self, client: TestClient, mock_knowledge_graph: MagicMock
    ) -> None:
        """Test that multiple operations can be performed."""
        # Add multiple interests
        for topic in ["python", "testing", "api"]:
            response = client.post(
                "/api/graph/interests",
                json={
                    "topic": topic,
                    "persona": "default",
                },
            )
            assert response.status_code == 200

        # Verify all were added
        assert mock_knowledge_graph.add_topic_interest.call_count == 3
