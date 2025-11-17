"""Tests for embedder factory."""

import pytest
from unittest.mock import patch, Mock
from src.embeddings.factory import create_embedder, get_embedder
from src.embeddings.base import BaseEmbedder
from src.config.settings import EmbeddingModel


class TestEmbedderFactory:
    """Tests for embedder factory functions."""

    def test_create_embedder_sentence_transformers(self):
        """Test creating sentence-transformers embedder."""
        with patch("src.embeddings.factory.SentenceTransformerEmbedder") as mock_st:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_st.return_value = mock_instance

            embedder = create_embedder(
                model_type=EmbeddingModel.SENTENCE_TRANSFORMERS,
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
                model_type=EmbeddingModel.OLLAMA,
                model_name="nomic-embed-text"
            )

            mock_ollama.assert_called_once_with(model_name="nomic-embed-text")
            assert embedder == mock_instance

    def test_create_embedder_invalid_type(self):
        """Test creating embedder with invalid type."""
        # Create a mock invalid enum value
        class InvalidModel:
            value = "invalid-type"

        with pytest.raises(ValueError, match="Unsupported embedding model type"):
            create_embedder(
                model_type=InvalidModel(),  # type: ignore[arg-type]
                model_name="some-model"
            )

    def test_create_embedder_default_model_name(self):
        """Test that default model names are used when not specified."""
        with patch("src.embeddings.factory.SentenceTransformerEmbedder") as mock_st:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_st.return_value = mock_instance

            with patch("src.embeddings.factory.get_settings") as mock_settings:
                # Mock settings to return default model name
                mock_settings.return_value.embedding_model_name = "default-model"

                # Don't specify model_name
                embedder = create_embedder(model_type=EmbeddingModel.SENTENCE_TRANSFORMERS)

                # Should use default model from settings
                mock_st.assert_called_once_with(model_name="default-model")

    def test_get_embedder_returns_embedder(self):
        """Test that get_embedder returns an embedder instance."""
        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_create.return_value = mock_instance

            embedder = get_embedder()

            # Should call create_embedder
            mock_create.assert_called_once()
            assert embedder == mock_instance

    def test_get_embedder_uses_config(self):
        """Test that get_embedder uses configuration."""
        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_create.return_value = mock_instance

            # get_embedder() should call create_embedder with no args
            # which causes create_embedder to use settings
            embedder = get_embedder()

            # Should call create_embedder with no parameters
            mock_create.assert_called_once_with()
            assert embedder == mock_instance
