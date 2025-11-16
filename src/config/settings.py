"""
Configuration management for ragged using Pydantic Settings.

This module provides type-safe configuration with environment variable support
and validation.
"""

import functools
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingModel(str, Enum):
    """Supported embedding model types."""

    SENTENCE_TRANSFORMERS = "sentence-transformers"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables with the RAGGED_ prefix.
    For example, RAGGED_ENVIRONMENT=production will set environment to "production".
    """

    # Environment
    environment: Literal["development", "production", "testing"] = "development"

    # Service URLs
    ollama_url: str = "http://localhost:11434"
    chroma_url: str = "http://localhost:8001"

    # Embedding Model Configuration
    embedding_model: EmbeddingModel = EmbeddingModel.SENTENCE_TRANSFORMERS
    embedding_model_name: str = Field(default="")  # Set in validator
    embedding_dimensions: int = Field(default=0)  # Set in validator

    # Chunking Configuration
    chunk_size: int = Field(default=500, gt=0, description="Chunk size in tokens")
    chunk_overlap: int = Field(default=100, ge=0, description="Overlap between chunks in tokens")

    # Retrieval Configuration
    retrieval_k: int = Field(default=5, gt=0, description="Number of chunks to retrieve")
    retrieval_method: str = Field(
        default="hybrid",
        description="Retrieval method: 'vector', 'bm25', or 'hybrid'"
    )

    # Generation Configuration
    llm_model: str = Field(default="llama3.2:latest", description="Ollama model for generation")

    # Storage Configuration
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".ragged",
        description="Directory for storing data",
    )

    # Limits
    max_file_size_mb: int = Field(
        default=100, gt=0, description="Maximum file size in megabytes"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RAGGED_",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("embedding_model_name", mode="before")
    @classmethod
    def set_embedding_model_name(cls, v: str, info) -> str:
        """Set default embedding model name based on embedding model type."""
        if v:  # If explicitly set, use it
            return v

        # Get embedding_model from validation context
        embedding_model = info.data.get("embedding_model", EmbeddingModel.SENTENCE_TRANSFORMERS)

        if embedding_model == EmbeddingModel.SENTENCE_TRANSFORMERS:
            return "all-MiniLM-L6-v2"
        elif embedding_model == EmbeddingModel.OLLAMA:
            return "nomic-embed-text"
        else:
            return "all-MiniLM-L6-v2"  # Default fallback

    @field_validator("embedding_dimensions", mode="before")
    @classmethod
    def set_embedding_dimensions(cls, v: int, info) -> int:
        """Set embedding dimensions based on model."""
        if v and v > 0:  # If explicitly set and positive, use it
            return v

        embedding_model_name = info.data.get("embedding_model_name", "")
        embedding_model = info.data.get("embedding_model", EmbeddingModel.SENTENCE_TRANSFORMERS)

        # Common model dimension mappings
        model_dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "nomic-embed-text": 768,
        }

        # Try to get dimensions from model name
        if embedding_model_name in model_dimensions:
            return model_dimensions[embedding_model_name]

        # Otherwise, use defaults based on model type
        if embedding_model == EmbeddingModel.SENTENCE_TRANSFORMERS:
            return 384  # Default for all-MiniLM-L6-v2
        elif embedding_model == EmbeddingModel.OLLAMA:
            return 768  # Default for nomic-embed-text
        else:
            return 384  # Safe default

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "Settings":
        """Validate that chunk overlap is less than chunk size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        return self

    def model_post_init(self, __context) -> None:
        """Create data directory and load user config if available."""
        # Import here to avoid circular dependency
        from src.utils.logging import get_logger

        logger = get_logger(__name__)

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Check for user config file
        config_file = self.data_dir / "config.yml"
        if config_file.exists():
            try:
                import yaml
                import os

                with open(config_file, "r") as f:
                    user_config = yaml.safe_load(f) or {}

                # Override with user config (if not set by environment variable)
                if "llm_model" in user_config and not os.getenv("RAGGED_LLM_MODEL"):
                    self.llm_model = user_config["llm_model"]
                    logger.info(f"Loaded LLM model from user config: {self.llm_model}")

            except Exception as e:
                logger.warning(f"Failed to load user config: {e}")


@functools.lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns the same Settings instance on subsequent calls for efficiency.
    Use get_settings.cache_clear() to reset the cache.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()