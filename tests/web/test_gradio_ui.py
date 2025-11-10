"""Tests for Gradio web UI."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import gradio as gr
from src.web.gradio_ui import (
    check_api_health,
    format_sources,
    upload_document,
    get_collections,
    query_non_streaming,
    create_ui,
)


class TestAPIHealth:
    """Test API health check functionality."""

    @patch('src.web.gradio_ui.requests.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy", "version": "0.2.0"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = check_api_health()

        assert result["status"] == "healthy"
        assert result["version"] == "0.2.0"
        mock_get.assert_called_once()

    @patch('src.web.gradio_ui.requests.get')
    def test_health_check_failure(self, mock_get):
        """Test health check when API is down."""
        mock_get.side_effect = Exception("Connection refused")

        result = check_api_health()

        assert result["status"] == "unhealthy"
        assert "error" in result


class TestFormatSources:
    """Test source formatting functionality."""

    def test_format_sources_empty(self):
        """Test formatting empty sources list."""
        result = format_sources([])
        assert "No sources found" in result

    def test_format_sources_single(self):
        """Test formatting single source."""
        sources = [
            {
                "filename": "test.pdf",
                "score": 0.95,
                "excerpt": "This is a test excerpt",
                "chunk_index": 0
            }
        ]

        result = format_sources(sources)

        assert "test.pdf" in result
        assert "0.950" in result
        assert "This is a test excerpt" in result
        assert "## Sources" in result

    def test_format_sources_multiple(self):
        """Test formatting multiple sources."""
        sources = [
            {
                "filename": "doc1.txt",
                "score": 0.95,
                "excerpt": "First excerpt",
                "chunk_index": 0
            },
            {
                "filename": "doc2.pdf",
                "score": 0.85,
                "excerpt": "Second excerpt",
                "chunk_index": 1
            }
        ]

        result = format_sources(sources)

        assert "doc1.txt" in result
        assert "doc2.pdf" in result
        assert "First excerpt" in result
        assert "Second excerpt" in result
        assert result.count("###") == 2  # Two source headers

    def test_format_sources_missing_fields(self):
        """Test formatting sources with missing fields."""
        sources = [
            {
                "filename": "test.pdf"
                # Missing score, excerpt, chunk_index
            }
        ]

        result = format_sources(sources)

        # Should handle gracefully with defaults
        assert "test.pdf" in result
        assert "0.000" in result  # Default score


class TestUploadDocument:
    """Test document upload functionality."""

    def test_upload_no_file(self):
        """Test upload with no file selected."""
        result = upload_document(None)
        assert "No file selected" in result

    @patch('src.web.gradio_ui.requests.post')
    @patch('builtins.open', create=True)
    def test_upload_success(self, mock_open, mock_post):
        """Test successful file upload."""
        # Mock file object
        mock_file = Mock()
        mock_file.name = "/tmp/test.pdf"

        # Mock requests response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "message": "File uploaded successfully"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Mock file reading
        mock_open.return_value.__enter__.return_value = Mock()

        result = upload_document(mock_file)

        assert "✅" in result
        assert "successfully" in result.lower()

    @patch('src.web.gradio_ui.requests.post')
    @patch('builtins.open', create=True)
    def test_upload_failure(self, mock_open, mock_post):
        """Test upload failure."""
        mock_file = Mock()
        mock_file.name = "/tmp/test.pdf"

        mock_post.side_effect = Exception("Upload failed")
        mock_open.return_value.__enter__.return_value = Mock()

        result = upload_document(mock_file)

        assert "❌" in result
        assert "failed" in result.lower()


class TestGetCollections:
    """Test collection retrieval."""

    @patch('src.web.gradio_ui.requests.get')
    def test_get_collections_success(self, mock_get):
        """Test successful collection retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "collections": ["default", "papers", "docs"]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_collections()

        assert len(result) == 3
        assert "default" in result
        assert "papers" in result

    @patch('src.web.gradio_ui.requests.get')
    def test_get_collections_failure(self, mock_get):
        """Test collection retrieval when API fails."""
        mock_get.side_effect = Exception("API error")

        result = get_collections()

        # Should return default collection
        assert result == ["default"]


class TestQueryNonStreaming:
    """Test non-streaming query functionality."""

    @patch('src.web.gradio_ui.requests.post')
    def test_query_non_streaming_success(self, mock_post):
        """Test successful non-streaming query."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "answer": "This is the answer",
            "sources": [
                {
                    "filename": "test.pdf",
                    "score": 0.9,
                    "excerpt": "Relevant text",
                    "chunk_index": 0
                }
            ],
            "retrieval_method": "hybrid",
            "total_time": 0.5
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        history = []
        updated_history, sources = query_non_streaming(
            "What is AI?",
            history,
            collection="default",
            retrieval_method="hybrid",
            top_k=5
        )

        assert len(updated_history) == 1
        assert updated_history[0][0] == "What is AI?"
        assert "This is the answer" in updated_history[0][1]
        assert "test.pdf" in sources

    @patch('src.web.gradio_ui.requests.post')
    def test_query_non_streaming_empty_message(self, mock_post):
        """Test query with empty message."""
        history = []
        updated_history, sources = query_non_streaming("", history)

        assert len(updated_history) == 0
        assert sources == ""
        mock_post.assert_not_called()

    @patch('src.web.gradio_ui.requests.post')
    def test_query_non_streaming_error(self, mock_post):
        """Test query when API returns error."""
        mock_post.side_effect = Exception("API error")

        history = []
        updated_history, sources = query_non_streaming("test", history)

        assert len(updated_history) == 1
        assert "❌" in updated_history[0][1]
        assert "Error" in updated_history[0][1]


class TestCreateUI:
    """Test Gradio UI creation."""

    @patch('src.web.gradio_ui.check_api_health')
    @patch('src.web.gradio_ui.get_collections')
    def test_create_ui(self, mock_get_collections, mock_health):
        """Test UI creation."""
        mock_health.return_value = {"status": "healthy"}
        mock_get_collections.return_value = ["default"]

        app = create_ui()

        assert isinstance(app, gr.Blocks)

    @patch('src.web.gradio_ui.check_api_health')
    @patch('src.web.gradio_ui.get_collections')
    def test_create_ui_api_unhealthy(self, mock_get_collections, mock_health):
        """Test UI creation when API is unhealthy."""
        mock_health.return_value = {"status": "unhealthy"}
        mock_get_collections.return_value = ["default"]

        app = create_ui()

        # Should still create UI
        assert isinstance(app, gr.Blocks)


class TestUIConfiguration:
    """Test UI configuration options."""

    def test_api_base_url(self):
        """Test API base URL configuration."""
        from src.web.gradio_ui import API_BASE_URL, API_QUERY

        assert "localhost:8000" in API_BASE_URL
        assert API_QUERY.startswith(API_BASE_URL)

    def test_default_values(self):
        """Test default configuration values."""
        # These are tested through UI creation
        # Just verify they're sensible
        assert True  # Placeholder for configuration tests
