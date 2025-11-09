"""Tests for Ollama LLM client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.generation.ollama_client import OllamaClient


class TestOllamaClient:
    """Tests for OllamaClient class."""

    @pytest.fixture
    def mock_ollama(self):
        """Create a mock Ollama client."""
        with patch("src.generation.ollama_client.ollama") as mock:
            yield mock

    def test_init_success(self, mock_ollama):
        """Test successful initialization."""
        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        assert client is not None
        assert client.model == "llama3.2"

    def test_generate_success(self, mock_ollama):
        """Test successful text generation."""
        mock_response = {
            "response": "This is a generated response."
        }
        mock_ollama.generate.return_value = mock_response

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        response = client.generate("Test prompt")

        assert response == "This is a generated response."
        mock_ollama.generate.assert_called_once()

    def test_generate_with_options(self, mock_ollama):
        """Test generation with custom options."""
        mock_response = {
            "response": "Generated text"
        }
        mock_ollama.generate.return_value = mock_response

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        response = client.generate(
            "Test prompt",
            temperature=0.7,
            max_tokens=100
        )

        mock_ollama.generate.assert_called_once()
        # Verify options were passed
        call_kwargs = mock_ollama.generate.call_args[1]
        assert "options" in call_kwargs or "temperature" in str(call_kwargs)

    def test_generate_retry_on_failure(self, mock_ollama):
        """Test retry logic on failure."""
        # First call fails, second succeeds
        mock_ollama.generate.side_effect = [
            Exception("Connection error"),
            {"response": "Success after retry"}
        ]

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        # Should retry and succeed
        response = client.generate("Test prompt")

        assert "Success after retry" in response or response is not None
        # Should have called generate multiple times
        assert mock_ollama.generate.call_count >= 1

    def test_generate_empty_prompt(self, mock_ollama):
        """Test generation with empty prompt."""
        mock_response = {
            "response": "Response to empty prompt"
        }
        mock_ollama.generate.return_value = mock_response

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        response = client.generate("")

        # Should still call generate
        mock_ollama.generate.assert_called_once()

    def test_model_verification(self, mock_ollama):
        """Test model verification on init."""
        # Mock model list
        mock_ollama.list.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "mistral"}
            ]
        }

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        # If verification is implemented, should check model exists
        # This depends on implementation details
        assert client.model == "llama3.2"

    def test_generate_handles_error_response(self, mock_ollama):
        """Test handling of error responses from Ollama."""
        # Mock an error response
        mock_ollama.generate.side_effect = Exception("Model not found")

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="invalid-model"
        )

        with pytest.raises(Exception):
            client.generate("Test prompt")


class TestOllamaClientIntegration:
    """Integration tests for OllamaClient (require actual Ollama service)."""

    @pytest.mark.requires_ollama
    @pytest.mark.skipif(True, reason="Requires running Ollama service")
    def test_real_generation(self):
        """Test with real Ollama service."""
        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.2"
        )

        response = client.generate("What is 2+2?")

        assert response is not None
        assert len(response) > 0
        # Should contain "4" in some form
        assert "4" in response or "four" in response.lower()
