"""Tests for settings configuration."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config.settings import EmbeddingModel, Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_default_settings(self) -> None:
        """Test that default settings are loaded correctly."""
        settings = Settings()

        assert settings.environment == "development"
        assert settings.ollama_url == "http://localhost:11434"
        assert settings.chroma_url == "http://localhost:8001"
        assert settings.embedding_model == EmbeddingModel.SENTENCE_TRANSFORMERS
        assert settings.embedding_model_name == "all-MiniLM-L6-v2"
        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 100
        assert settings.retrieval_k == 5
        assert settings.llm_model == "llama3.2:3b"
        assert settings.log_level == "INFO"
        assert settings.data_dir == Path.home() / ".ragged"

    def test_env_file_loading(self, temp_env_file: Path) -> None:
        """Test loading settings from .env file."""
        # Create .env file with custom values
        temp_env_file.write_text(
            "RAGGED_ENVIRONMENT=production\n"
            "RAGGED_OLLAMA_URL=http://custom:11434\n"
            "RAGGED_CHROMA_URL=http://custom:8001\n"
            "RAGGED_CHUNK_SIZE=1000\n"
            "RAGGED_LOG_LEVEL=DEBUG\n"
        )

        settings = Settings(_env_file=str(temp_env_file))

        assert settings.environment == "production"
        assert settings.ollama_url == "http://custom:11434"
        assert settings.chroma_url == "http://custom:8001"
        assert settings.chunk_size == 1000
        assert settings.log_level == "DEBUG"

    def test_env_var_override(self, temp_env_file: Path) -> None:
        """Test that environment variables override .env file."""
        temp_env_file.write_text("RAGGED_ENVIRONMENT=development\n")

        os.environ["RAGGED_ENVIRONMENT"] = "testing"
        settings = Settings(_env_file=str(temp_env_file))

        assert settings.environment == "testing"

    def test_embedding_model_sentence_transformers(self) -> None:
        """Test sentence-transformers embedding model selection."""
        os.environ["RAGGED_EMBEDDING_MODEL"] = "sentence-transformers"
        settings = Settings()

        assert settings.embedding_model == EmbeddingModel.SENTENCE_TRANSFORMERS
        assert settings.embedding_model_name == "all-MiniLM-L6-v2"
        assert settings.embedding_dimensions == 384

    def test_embedding_model_ollama(self) -> None:
        """Test Ollama embedding model selection."""
        os.environ["RAGGED_EMBEDDING_MODEL"] = "ollama"
        settings = Settings()

        assert settings.embedding_model == EmbeddingModel.OLLAMA
        assert settings.embedding_model_name == "nomic-embed-text"
        assert settings.embedding_dimensions == 768

    def test_custom_embedding_model_name(self) -> None:
        """Test custom embedding model name."""
        os.environ["RAGGED_EMBEDDING_MODEL"] = "sentence-transformers"
        os.environ["RAGGED_EMBEDDING_MODEL_NAME"] = "custom-model"
        settings = Settings()

        assert settings.embedding_model_name == "custom-model"

    def test_chunk_size_validation(self) -> None:
        """Test chunk size must be positive."""
        os.environ["RAGGED_CHUNK_SIZE"] = "-100"

        with pytest.raises(ValidationError):
            Settings()

    def test_chunk_overlap_validation(self) -> None:
        """Test chunk overlap must be non-negative."""
        os.environ["RAGGED_CHUNK_OVERLAP"] = "-10"

        with pytest.raises(ValidationError):
            Settings()

    def test_chunk_overlap_less_than_size(self) -> None:
        """Test chunk overlap must be less than chunk size."""
        os.environ["RAGGED_CHUNK_SIZE"] = "100"
        os.environ["RAGGED_CHUNK_OVERLAP"] = "200"

        with pytest.raises(ValidationError):
            Settings()

    def test_retrieval_k_validation(self) -> None:
        """Test retrieval k must be positive."""
        os.environ["RAGGED_RETRIEVAL_K"] = "0"

        with pytest.raises(ValidationError):
            Settings()

    def test_max_file_size_validation(self) -> None:
        """Test max file size must be positive."""
        os.environ["RAGGED_MAX_FILE_SIZE_MB"] = "-10"

        with pytest.raises(ValidationError):
            Settings()

    def test_data_dir_creation(self, temp_dir: Path) -> None:
        """Test that data directory is created if it doesn't exist."""
        data_dir = temp_dir / "ragged_data"
        os.environ["RAGGED_DATA_DIR"] = str(data_dir)

        settings = Settings()

        assert settings.data_dir == data_dir
        # The model_post_init should create the directory
        assert data_dir.exists()

    def test_get_settings_singleton(self) -> None:
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_cache_clear(self) -> None:
        """Test that cache can be cleared."""
        settings1 = get_settings()

        os.environ["RAGGED_ENVIRONMENT"] = "testing"
        get_settings.cache_clear()
        settings2 = get_settings()

        assert settings1 is not settings2
        assert settings2.environment == "testing"

    def test_log_level_validation(self) -> None:
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            os.environ["RAGGED_LOG_LEVEL"] = level
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.log_level == level

    def test_invalid_log_level(self) -> None:
        """Test invalid log level raises error."""
        os.environ["RAGGED_LOG_LEVEL"] = "INVALID"
        get_settings.cache_clear()

        with pytest.raises(ValidationError):
            get_settings()
