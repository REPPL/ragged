"""
Layered configuration management for ragged.

Provides a configuration system with proper precedence ordering:
1. Defaults (in code)
2. User config file (~/.config/ragged/config.yml)
3. CLI flags (handled by Click)
4. Environment variables (highest priority)
"""

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class RaggedConfig:
    """
    Ragged configuration with layered overrides.

    Priority: Defaults → User file → CLI flags → Environment variables
    """

    # Retrieval settings
    retrieval_method: str = "hybrid"
    top_k: int = 5
    bm25_weight: float = 0.3
    vector_weight: float = 0.7

    # Reranking settings
    enable_reranking: bool = True
    rerank_to: int = 3
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Query processing
    enable_query_decomposition: bool = False
    enable_hyde: bool = False
    enable_compression: bool = False

    # Generation settings
    llm_model: str = "llama3.2:latest"
    temperature: float = 0.7
    max_tokens: int = 512

    # Confidence thresholds
    confidence_threshold: float = 0.85

    # Current persona
    persona: str = "balanced"

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "RaggedConfig":
        """
        Load configuration with layered overrides.

        Args:
            config_path: Optional custom config file path

        Returns:
            RaggedConfig instance with merged settings
        """
        # Start with defaults
        config = cls()

        # Load user config file
        if config_path is None:
            config_path = Path.home() / ".config" / "ragged" / "config.yml"

        if config_path.exists():
            with open(config_path) as f:
                user_config = yaml.safe_load(f) or {}
                config._merge(user_config)

        # Apply environment variables (highest priority)
        config._apply_env_vars()

        return config

    def _merge(self, overrides: Dict[str, Any]) -> None:
        """
        Merge override dict into config.

        Args:
            overrides: Dictionary of config overrides
        """
        for key, value in overrides.items():
            if hasattr(self, key):
                # Preserve type
                current_type = type(getattr(self, key))
                try:
                    if current_type == bool and isinstance(value, str):
                        value = value.lower() in ["true", "1", "yes"]
                    elif current_type in (int, float) and not isinstance(value, current_type):
                        value = current_type(value)
                    setattr(self, key, value)
                except (ValueError, TypeError):
                    # Skip invalid conversions
                    pass

    def _apply_env_vars(self) -> None:
        """Apply environment variable overrides."""
        env_mapping = {
            "RAGGED_RETRIEVAL_METHOD": "retrieval_method",
            "RAGGED_TOP_K": ("top_k", int),
            "RAGGED_PERSONA": "persona",
            "RAGGED_LLM_MODEL": "llm_model",
            "RAGGED_TEMPERATURE": ("temperature", float),
            "RAGGED_ENABLE_RERANKING": ("enable_reranking", bool),
        }

        for env_var, attr in env_mapping.items():
            if env_var in os.environ:
                if isinstance(attr, tuple):
                    attr_name, converter = attr
                    try:
                        if converter == bool:
                            value = os.environ[env_var].lower() in ["true", "1", "yes"]
                        else:
                            value = converter(os.environ[env_var])
                        setattr(self, attr_name, value)
                    except (ValueError, TypeError):
                        # Skip invalid environment values
                        pass
                else:
                    setattr(self, attr, os.environ[env_var])

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of config
        """
        return asdict(self)

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save current config to file.

        Args:
            config_path: Optional custom path (default: ~/.config/ragged/config.yml)
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "ragged" / "config.yml"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)


class ConfigValidator:
    """Validate configuration values."""

    def validate(self, config: RaggedConfig) -> Tuple[bool, List[str]]:
        """
        Validate configuration.

        Args:
            config: Configuration to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate retrieval method
        if config.retrieval_method not in ["hybrid", "vector", "bm25"]:
            errors.append(f"Invalid retrieval_method: {config.retrieval_method}")

        # Validate weights
        if config.retrieval_method == "hybrid":
            if not (0 <= config.bm25_weight <= 1):
                errors.append(f"bm25_weight must be 0-1: {config.bm25_weight}")
            if not (0 <= config.vector_weight <= 1):
                errors.append(f"vector_weight must be 0-1: {config.vector_weight}")

        # Validate top_k
        if config.top_k < 1 or config.top_k > 100:
            errors.append(f"top_k must be 1-100: {config.top_k}")

        # Validate rerank_to
        if config.enable_reranking and config.rerank_to > config.top_k:
            errors.append(
                f"rerank_to ({config.rerank_to}) cannot exceed top_k ({config.top_k})"
            )

        # Validate persona
        valid_personas = ["accuracy", "speed", "balanced", "research", "quick-answer"]
        if config.persona not in valid_personas:
            errors.append(f"Invalid persona: {config.persona}")

        # Validate temperature
        if not (0 <= config.temperature <= 2.0):
            errors.append(f"temperature must be 0-2.0: {config.temperature}")

        # Validate confidence threshold
        if not (0 <= config.confidence_threshold <= 1.0):
            errors.append(
                f"confidence_threshold must be 0-1.0: {config.confidence_threshold}"
            )

        return (len(errors) == 0, errors)
