"""Tests for Document Library API endpoints.

Tests cover:
- Document listing with filtering and pagination
- Document retrieval and preview
- Document metadata updates
- Document deletion (single and bulk)
- Tag and type listing

v0.9.0: Initial implementation
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from ragged.web.api import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store with test data."""
    mock = Mock()

    # Sample test data
    test_data = {
        "ids": [
            "doc1_0", "doc1_1", "doc1_2",  # Document 1 has 3 chunks
            "doc2_0", "doc2_1",  # Document 2 has 2 chunks
            "doc3_0",  # Document 3 has 1 chunk
        ],
        "documents": [
            "Chunk 0 of document 1",
            "Chunk 1 of document 1",
            "Chunk 2 of document 1",
            "Chunk 0 of document 2",
            "Chunk 1 of document 2",
            "Chunk 0 of document 3",
        ],
        "metadatas": [
            {
                "filename": "report.pdf",
                "file_type": "pdf",
                "chunk_index": 0,
                "tags": ["work", "quarterly"],
                "collection": "default",
                "created_at": "2025-01-15T10:00:00",
            },
            {
                "filename": "report.pdf",
                "file_type": "pdf",
                "chunk_index": 1,
                "tags": ["work", "quarterly"],
                "collection": "default",
                "created_at": "2025-01-15T10:00:00",
            },
            {
                "filename": "report.pdf",
                "file_type": "pdf",
                "chunk_index": 2,
                "tags": ["work", "quarterly"],
                "collection": "default",
                "created_at": "2025-01-15T10:00:00",
            },
            {
                "filename": "notes.md",
                "file_type": "md",
                "chunk_index": 0,
                "tags": ["personal"],
                "collection": "default",
                "created_at": "2025-01-20T14:30:00",
            },
            {
                "filename": "notes.md",
                "file_type": "md",
                "chunk_index": 1,
                "tags": ["personal"],
                "collection": "default",
                "created_at": "2025-01-20T14:30:00",
            },
            {
                "filename": "article.txt",
                "file_type": "txt",
                "chunk_index": 0,
                "tags": ["reading"],
                "collection": "default",
                "created_at": "2025-01-25T09:15:00",
            },
        ],
        "total": 6,
    }

    mock.list.return_value = test_data
    mock.count.return_value = 6
    mock.delete.return_value = None
    mock.update_metadata.return_value = None

    return mock


class TestDocumentListEndpoint:
    """Test GET /api/documents endpoint."""

    def test_list_documents_basic(self, client, mock_vector_store):
        """Test basic document listing."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents")

            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "has_more" in data

        finally:
            api._vector_store = original

    def test_list_documents_groups_chunks(self, client, mock_vector_store):
        """Test that chunks are grouped by document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents")

            assert response.status_code == 200
            data = response.json()

            # Should have 3 documents, not 6 chunks
            assert data["total"] == 3

            # Check document structure
            for doc in data["documents"]:
                assert "id" in doc
                assert "metadata" in doc
                assert "status" in doc
                assert "filename" in doc["metadata"]
                assert "chunk_count" in doc["metadata"]

        finally:
            api._vector_store = original

    def test_list_documents_pagination(self, client, mock_vector_store):
        """Test pagination parameters."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            # Test with limit and offset
            response = client.get("/api/documents?limit=2&offset=1")

            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 2
            assert data["offset"] == 1

        finally:
            api._vector_store = original

    def test_list_documents_filter_by_type(self, client, mock_vector_store):
        """Test filtering by file type."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents?file_type=pdf")

            assert response.status_code == 200
            # Verify filter was applied (mock was called)
            mock_vector_store.list.assert_called()

        finally:
            api._vector_store = original

    def test_list_documents_filter_by_search(self, client, mock_vector_store):
        """Test search by filename."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents?search=report")

            assert response.status_code == 200
            data = response.json()

            # Should only return documents with "report" in filename
            for doc in data["documents"]:
                assert "report" in doc["metadata"]["filename"].lower()

        finally:
            api._vector_store = original

    def test_list_documents_without_vector_store(self, client):
        """Test listing when vector store is not initialised."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = None

            response = client.get("/api/documents")

            assert response.status_code == 503
            assert "not initialised" in response.json()["detail"].lower()

        finally:
            api._vector_store = original

    def test_list_documents_limit_validation(self, client, mock_vector_store):
        """Test limit parameter validation."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            # Valid limit
            response = client.get("/api/documents?limit=50")
            assert response.status_code == 200

            # Limit too high
            response = client.get("/api/documents?limit=500")
            assert response.status_code == 422

            # Limit too low
            response = client.get("/api/documents?limit=0")
            assert response.status_code == 422

        finally:
            api._vector_store = original


class TestDocumentDetailEndpoint:
    """Test GET /api/documents/{id} endpoint."""

    def test_get_document_success(self, client, mock_vector_store):
        """Test getting a single document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/doc1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "doc1"
            assert "metadata" in data
            assert data["metadata"]["filename"] == "report.pdf"
            assert data["metadata"]["chunk_count"] == 3

        finally:
            api._vector_store = original

    def test_get_document_not_found(self, client, mock_vector_store):
        """Test getting a non-existent document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/nonexistent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

        finally:
            api._vector_store = original


class TestDocumentPreviewEndpoint:
    """Test GET /api/documents/{id}/preview endpoint."""

    def test_get_preview_success(self, client, mock_vector_store):
        """Test getting document preview."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/doc1/preview")

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "filename" in data
            assert "preview" in data
            assert "total_length" in data
            assert "truncated" in data

        finally:
            api._vector_store = original

    def test_get_preview_custom_length(self, client, mock_vector_store):
        """Test custom preview length."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/doc1/preview?max_length=500")

            assert response.status_code == 200
            data = response.json()
            assert len(data["preview"]) <= 500

        finally:
            api._vector_store = original

    def test_get_preview_not_found(self, client, mock_vector_store):
        """Test preview for non-existent document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/nonexistent/preview")

            assert response.status_code == 404

        finally:
            api._vector_store = original


class TestDocumentChunksEndpoint:
    """Test GET /api/documents/{id}/chunks endpoint."""

    def test_get_chunks_success(self, client, mock_vector_store):
        """Test getting document chunks."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/doc1/chunks")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 3  # doc1 has 3 chunks

            # Check chunk structure
            for chunk in data:
                assert "id" in chunk
                assert "document_id" in chunk
                assert "chunk_index" in chunk
                assert "content" in chunk
                assert chunk["document_id"] == "doc1"

        finally:
            api._vector_store = original

    def test_get_chunks_sorted_by_index(self, client, mock_vector_store):
        """Test chunks are sorted by index."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/doc1/chunks")

            assert response.status_code == 200
            data = response.json()

            # Verify sorting
            indices = [chunk["chunk_index"] for chunk in data]
            assert indices == sorted(indices)

        finally:
            api._vector_store = original

    def test_get_chunks_not_found(self, client, mock_vector_store):
        """Test chunks for non-existent document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/nonexistent/chunks")

            assert response.status_code == 404

        finally:
            api._vector_store = original


class TestDocumentUpdateEndpoint:
    """Test PATCH /api/documents/{id} endpoint."""

    def test_update_document_tags(self, client, mock_vector_store):
        """Test updating document tags."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.patch(
                "/api/documents/doc1",
                json={"tags": ["new", "tags"]}
            )

            assert response.status_code == 200
            mock_vector_store.update_metadata.assert_called()

        finally:
            api._vector_store = original

    def test_update_document_custom_metadata(self, client, mock_vector_store):
        """Test updating custom metadata."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.patch(
                "/api/documents/doc1",
                json={"custom": {"priority": "high", "reviewed": True}}
            )

            assert response.status_code == 200
            mock_vector_store.update_metadata.assert_called()

        finally:
            api._vector_store = original

    def test_update_document_not_found(self, client, mock_vector_store):
        """Test updating non-existent document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.patch(
                "/api/documents/nonexistent",
                json={"tags": ["test"]}
            )

            assert response.status_code == 404

        finally:
            api._vector_store = original


class TestDocumentDeleteEndpoint:
    """Test DELETE /api/documents/{id} endpoint."""

    def test_delete_document_success(self, client, mock_vector_store):
        """Test deleting a document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.delete("/api/documents/doc1")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] == 1
            assert "doc1" in data["ids"]
            mock_vector_store.delete.assert_called()

        finally:
            api._vector_store = original

    def test_delete_document_not_found(self, client, mock_vector_store):
        """Test deleting non-existent document."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.delete("/api/documents/nonexistent")

            assert response.status_code == 404

        finally:
            api._vector_store = original


class TestBulkDeleteEndpoint:
    """Test DELETE /api/documents (bulk) endpoint."""

    def test_bulk_delete_success(self, client, mock_vector_store):
        """Test bulk deleting documents."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.request(
                "DELETE",
                "/api/documents",
                json={"ids": ["doc1", "doc2"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] == 2
            mock_vector_store.delete.assert_called()

        finally:
            api._vector_store = original

    def test_bulk_delete_partial_match(self, client, mock_vector_store):
        """Test bulk delete with some non-existent IDs."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.request(
                "DELETE",
                "/api/documents",
                json={"ids": ["doc1", "nonexistent"]}
            )

            assert response.status_code == 200
            data = response.json()
            # Only one document should be deleted
            assert data["deleted"] == 1

        finally:
            api._vector_store = original

    def test_bulk_delete_empty_ids(self, client, mock_vector_store):
        """Test bulk delete with empty IDs list."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.request(
                "DELETE",
                "/api/documents",
                json={"ids": []}
            )

            assert response.status_code == 422  # Validation error

        finally:
            api._vector_store = original

    def test_bulk_delete_too_many_ids(self, client, mock_vector_store):
        """Test bulk delete with too many IDs."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            # Create list of 101 IDs (over limit of 100)
            ids = [f"doc{i}" for i in range(101)]

            response = client.request(
                "DELETE",
                "/api/documents",
                json={"ids": ids}
            )

            assert response.status_code == 422  # Validation error

        finally:
            api._vector_store = original


class TestTagsEndpoint:
    """Test GET /api/documents/tags endpoint."""

    def test_list_tags_success(self, client, mock_vector_store):
        """Test listing all tags."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/tags")

            assert response.status_code == 200
            data = response.json()
            assert "tags" in data
            assert "count" in data
            assert isinstance(data["tags"], list)
            # Should have: work, quarterly, personal, reading
            assert data["count"] == 4

        finally:
            api._vector_store = original

    def test_list_tags_sorted(self, client, mock_vector_store):
        """Test tags are sorted alphabetically."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/tags")

            assert response.status_code == 200
            data = response.json()
            assert data["tags"] == sorted(data["tags"])

        finally:
            api._vector_store = original


class TestTypesEndpoint:
    """Test GET /api/documents/types endpoint."""

    def test_list_types_success(self, client, mock_vector_store):
        """Test listing all document types."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/types")

            assert response.status_code == 200
            data = response.json()
            assert "types" in data
            assert "count" in data
            assert isinstance(data["types"], list)
            # Should have: pdf, md, txt
            assert data["count"] == 3

        finally:
            api._vector_store = original

    def test_list_types_sorted(self, client, mock_vector_store):
        """Test types are sorted alphabetically."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            response = client.get("/api/documents/types")

            assert response.status_code == 200
            data = response.json()
            assert data["types"] == sorted(data["types"])

        finally:
            api._vector_store = original


class TestDocumentAPIOpenAPI:
    """Test OpenAPI schema includes document endpoints."""

    def test_openapi_includes_documents_tag(self, client):
        """Test OpenAPI schema includes documents tag."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Check tags include documents
        tags = [tag["name"] for tag in schema.get("tags", [])]
        assert "documents" in tags or any(
            "documents" in path for path in schema.get("paths", {})
        )

    def test_openapi_documents_paths(self, client):
        """Test OpenAPI schema includes all document paths."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        # Check all document endpoints are documented
        assert "/api/documents" in paths
        assert "/api/documents/tags" in paths
        assert "/api/documents/types" in paths
        assert "/api/documents/{document_id}" in paths
        assert "/api/documents/{document_id}/preview" in paths
        assert "/api/documents/{document_id}/chunks" in paths


class TestDocumentAPIErrorHandling:
    """Test error handling in document API."""

    def test_invalid_document_id_format(self, client, mock_vector_store):
        """Test with invalid document ID."""
        from ragged.web import api

        original = api._vector_store
        try:
            api._vector_store = mock_vector_store

            # Empty ID should still work (treated as not found)
            response = client.get("/api/documents//preview")

            # Either 404 or 307 redirect is acceptable
            assert response.status_code in [404, 307]

        finally:
            api._vector_store = original

    def test_vector_store_error_handling(self, client):
        """Test error handling when vector store raises exception."""
        from ragged.web import api

        mock = Mock()
        mock.list.side_effect = Exception("Database connection failed")

        original = api._vector_store
        try:
            api._vector_store = mock

            response = client.get("/api/documents")

            assert response.status_code == 500
            assert "error" in response.json()["detail"].lower()

        finally:
            api._vector_store = original
