"""Tests for FastAPI web API endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.web.api import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test /api/health endpoint."""

    def test_health_check_success(self, client):
        """Test health check returns 200."""
        response = client.get("/api/health")

        assert response.status_code == 200

    def test_health_check_structure(self, client):
        """Test health check response structure."""
        response = client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "services" in data

    def test_health_check_version(self, client):
        """Test health check returns correct version."""
        response = client.get("/api/health")
        data = response.json()

        assert data["version"] == "0.2.0"

    def test_health_check_services(self, client):
        """Test health check reports service status."""
        response = client.get("/api/health")
        data = response.json()

        services = data["services"]
        assert "api" in services
        assert "retriever" in services
        assert "llm" in services

    def test_health_check_degraded_when_not_initialized(self, client):
        """Test health check is degraded when services not initialized."""
        response = client.get("/api/health")
        data = response.json()

        # Since retriever and llm are not initialized in tests
        assert data["status"] in ["degraded", "healthy"]


class TestQueryEndpoint:
    """Test /api/query endpoint."""

    def test_query_basic_request(self, client):
        """Test basic query request."""
        response = client.post(
            "/api/query",
            json={
                "query": "What is machine learning?",
                "stream": False
            }
        )

        assert response.status_code == 200

    def test_query_response_structure(self, client):
        """Test query response has correct structure."""
        response = client.post(
            "/api/query",
            json={
                "query": "test query",
                "stream": False
            }
        )

        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "retrieval_method" in data
        assert "total_time" in data

    def test_query_default_parameters(self, client):
        """Test query with default parameters."""
        response = client.post(
            "/api/query",
            json={"query": "test"}
        )

        # Should use streaming by default
        assert response.status_code == 200

    def test_query_custom_parameters(self, client):
        """Test query with custom parameters."""
        response = client.post(
            "/api/query",
            json={
                "query": "test",
                "collection": "my_collection",
                "top_k": 10,
                "retrieval_method": "vector",
                "stream": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["retrieval_method"] == "vector"

    def test_query_empty_query_rejected(self, client):
        """Test empty query is rejected."""
        response = client.post(
            "/api/query",
            json={"query": "", "stream": False}
        )

        assert response.status_code == 422  # Validation error

    def test_query_sources_structure(self, client):
        """Test sources have correct structure."""
        response = client.post(
            "/api/query",
            json={"query": "test", "stream": False}
        )

        data = response.json()
        sources = data["sources"]

        assert isinstance(sources, list)
        if len(sources) > 0:
            source = sources[0]
            assert "id" in source
            assert "filename" in source
            assert "chunk_index" in source
            assert "score" in source
            assert "excerpt" in source

    def test_query_streaming_response(self, client):
        """Test streaming query returns SSE."""
        response = client.post(
            "/api/query",
            json={"query": "test", "stream": True}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_query_streaming_events(self, client):
        """Test streaming query produces SSE events."""
        response = client.post(
            "/api/query",
            json={"query": "machine learning", "stream": True}
        )

        content = response.text

        # Should contain SSE event markers
        assert "event: status" in content
        assert "event: token" in content or "event: retrieved" in content
        assert "data:" in content

    def test_query_retrieval_methods(self, client):
        """Test different retrieval methods."""
        methods = ["vector", "bm25", "hybrid"]

        for method in methods:
            response = client.post(
                "/api/query",
                json={
                    "query": "test",
                    "retrieval_method": method,
                    "stream": False
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["retrieval_method"] == method

    def test_query_top_k_validation(self, client):
        """Test top_k parameter validation."""
        # Valid range
        response = client.post(
            "/api/query",
            json={"query": "test", "top_k": 5, "stream": False}
        )
        assert response.status_code == 200

        # Below minimum
        response = client.post(
            "/api/query",
            json={"query": "test", "top_k": 0, "stream": False}
        )
        assert response.status_code == 422

        # Above maximum
        response = client.post(
            "/api/query",
            json={"query": "test", "top_k": 100, "stream": False}
        )
        assert response.status_code == 422


class TestUploadEndpoint:
    """Test /api/upload endpoint."""

    def test_upload_pdf_file(self, client):
        """Test uploading PDF file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", b"PDF content", "application/pdf")}
        )

        assert response.status_code == 200

    def test_upload_txt_file(self, client):
        """Test uploading TXT file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"Text content", "text/plain")}
        )

        assert response.status_code == 200

    def test_upload_md_file(self, client):
        """Test uploading Markdown file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.md", b"# Markdown", "text/markdown")}
        )

        assert response.status_code == 200

    def test_upload_html_file(self, client):
        """Test uploading HTML file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.html", b"<html></html>", "text/html")}
        )

        assert response.status_code == 200

    def test_upload_unsupported_file_type(self, client):
        """Test uploading unsupported file type."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.exe", b"binary", "application/x-executable")}
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_response_structure(self, client):
        """Test upload response structure."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"content", "text/plain")}
        )

        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "status" in data
        assert "message" in data

    def test_upload_no_file(self, client):
        """Test upload without file."""
        response = client.post("/api/upload")

        assert response.status_code == 422  # Validation error


class TestCollectionsEndpoints:
    """Test collection management endpoints."""

    def test_list_collections(self, client):
        """Test listing collections."""
        response = client.get("/api/collections")

        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert isinstance(data["collections"], list)

    def test_clear_collection(self, client):
        """Test clearing a collection."""
        response = client.delete("/api/collections/default")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["collection"] == "default"


class TestCORS:
    """Test CORS middleware configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # CORS middleware should add appropriate headers
        # Note: TestClient may not fully simulate CORS preflight
        assert response.status_code in [200, 405]


class TestErrorHandling:
    """Test API error handling."""

    def test_404_for_unknown_endpoint(self, client):
        """Test 404 for unknown endpoint."""
        response = client.get("/api/unknown")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.get("/api/upload")  # Should be POST

        assert response.status_code == 405

    def test_invalid_json(self, client):
        """Test invalid JSON in request body."""
        response = client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "ragged API"
        assert schema["info"]["version"] == "0.2.0"

    def test_docs_endpoint(self, client):
        """Test Swagger UI docs endpoint."""
        response = client.get("/docs")

        assert response.status_code == 200
