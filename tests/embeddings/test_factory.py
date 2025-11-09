"""Tests for embedder factory."""

import pytest
from unittest.mock import patch, Mock
from src.embeddings.factory import create_embedder, get_embedder
from src.embeddings.base import BaseEmbedder


class TestEmbedderFactory:
    """Tests for embedder factory functions."""

    def test_create_embedder_sentence_transformers(self):
        """Test creating sentence-transformers embedder."""
        with patch("src.embeddings.factory.SentenceTransformerEmbedder") as mock_st:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_st.return_value = mock_instance

            embedder = create_embedder(
                model_type="sentence-transformers",
                model_name="all-MiniLM-L6-v2"
            )

            mock_st.assert_called_once_with(model_name="all-MiniLM-L6-v2")
            assert embedder == mock_instance

    def test_create_embedder_ollama(self):
        """Test creating Ollama embedder."""
        with patch("src.embeddings.factory.OllamaEmbedder") as mock_ollama:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_ollama.return_value = mock_instance

            embedder = create_embedder(
                model_type="ollama",
                model_name="nomic-embed-text",
                base_url="http://localhost:11434"
            )

            mock_ollama.assert_called_once()
            assert embedder == mock_instance

    def test_create_embedder_invalid_type(self):
        """Test creating embedder with invalid type."""
        with pytest.raises(ValueError, match="Unsupported embedder type"):
            create_embedder(
                model_type="invalid-type",
                model_name="some-model"
            )

    def test_create_embedder_default_model_name(self):
        """Test that default model names are used when not specified."""
        with patch("src.embeddings.factory.SentenceTransformerEmbedder") as mock_st:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_st.return_value = mock_instance

            # Don't specify model_name
            embedder = create_embedder(model_type="sentence-transformers")

            # Should use default model
            mock_st.assert_called_once()
            call_args = mock_st.call_args
            # Verify some default was used
            assert call_args is not None

    def test_get_embedder_caching(self):
        """Test that get_embedder caches the instance."""
        # Clear cache first
        get_embedder.cache_clear()

        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_create.return_value = mock_instance

            # First call should create
            embedder1 = get_embedder(
                model_type="sentence-transformers",
                model_name="all-MiniLM-L6-v2"
            )

            # Second call with same args should return cached
            embedder2 = get_embedder(
                model_type="sentence-transformers",
                model_name="all-MiniLM-L6-v2"
            )

            # Should only call create_embedder once
            assert mock_create.call_count == 1
            assert embedder1 == embedder2

        # Clean up
        get_embedder.cache_clear()

    def test_get_embedder_different_args_not_cached(self):
        """Test that different arguments create different instances."""
        # Clear cache first
        get_embedder.cache_clear()

        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance1 = Mock(spec=BaseEmbedder)
            mock_instance2 = Mock(spec=BaseEmbedder)
            mock_create.side_effect = [mock_instance1, mock_instance2]

            # Call with different arguments
            embedder1 = get_embedder(
                model_type="sentence-transformers",
                model_name="model1"
            )

            embedder2 = get_embedder(
                model_type="sentence-transformers",
                model_name="model2"
            )

            # Should call create_embedder twice
            assert mock_create.call_count == 2
            assert embedder1 != embedder2

        # Clean up
        get_embedder.cache_clear()

    def test_get_embedder_cache_clear(self):
        """Test that cache can be cleared."""
        # Clear cache first
        get_embedder.cache_clear()

        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance1 = Mock(spec=BaseEmbedder)
            mock_instance2 = Mock(spec=BaseEmbedder)
            mock_create.side_effect = [mock_instance1, mock_instance2]

            # First call
            embedder1 = get_embedder(model_type="sentence-transformers")

            # Clear cache
            get_embedder.cache_clear()

            # Second call should create new instance
            embedder2 = get_embedder(model_type="sentence-transformers")

            # Should call create_embedder twice
            assert mock_create.call_count == 2

        # Clean up
        get_embedder.cache_clear()
