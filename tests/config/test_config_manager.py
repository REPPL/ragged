"""Tests for configuration management system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.config.config_manager import RaggedConfig, ConfigValidator


class TestRaggedConfig:
    """Test RaggedConfig class."""

    def test_default_configuration(self):
        """Test that default configuration has expected values."""
        config = RaggedConfig()

        assert config.retrieval_method == "hybrid"
        assert config.top_k == 5
        assert config.bm25_weight == 0.3
        assert config.vector_weight == 0.7
        assert config.enable_reranking is True
        assert config.rerank_to == 3
        assert config.rerank_model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert config.enable_query_decomposition is False
        assert config.enable_hyde is False
        assert config.enable_compression is False
        assert config.llm_model == "llama3.2:latest"
        assert config.temperature == 0.7
        assert config.max_tokens == 512
        assert config.confidence_threshold == 0.85
        assert config.persona == "balanced"

    def test_load_from_nonexistent_file(self):
        """Test loading when config file doesn't exist uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.yml"
            config = RaggedConfig.load(config_path)

            # Should use defaults
            assert config.retrieval_method == "hybrid"
            assert config.top_k == 5
            assert config.persona == "balanced"

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"

            # Write test config
            test_config = {
                "retrieval_method": "vector",
                "top_k": 10,
                "enable_reranking": False,
                "temperature": 0.9,
                "persona": "speed",
            }

            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

            # Load and verify
            config = RaggedConfig.load(config_path)
            assert config.retrieval_method == "vector"
            assert config.top_k == 10
            assert config.enable_reranking is False
            assert config.temperature == 0.9
            assert config.persona == "speed"

            # Other values should be defaults
            assert config.bm25_weight == 0.3
            assert config.vector_weight == 0.7

    def test_environment_variable_overrides(self):
        """Test that environment variables override file config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"

            # Write config file
            test_config = {"top_k": 5, "retrieval_method": "hybrid"}
            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

            # Set environment variables
            with patch.dict(
                os.environ,
                {
                    "RAGGED_TOP_K": "15",
                    "RAGGED_RETRIEVAL_METHOD": "vector",
                    "RAGGED_TEMPERATURE": "0.8",
                    "RAGGED_ENABLE_RERANKING": "false",
                },
            ):
                config = RaggedConfig.load(config_path)

                # Environment variables should override
                assert config.top_k == 15
                assert config.retrieval_method == "vector"
                assert config.temperature == 0.8
                assert config.enable_reranking is False

    def test_type_conversion_from_yaml(self):
        """Test type conversion when loading from YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"

            # Write config with string values
            test_config = {
                "top_k": "10",
                "temperature": "0.9",
                "enable_reranking": "true",
            }

            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

            config = RaggedConfig.load(config_path)

            # Should convert to correct types
            assert isinstance(config.top_k, int)
            assert config.top_k == 10
            assert isinstance(config.temperature, float)
            assert config.temperature == 0.9
            assert isinstance(config.enable_reranking, bool)
            assert config.enable_reranking is True

    def test_boolean_conversion_variations(self):
        """Test boolean conversion from various string formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"

            # Test various boolean representations
            test_cases = [
                ("true", True),
                ("True", True),
                ("TRUE", True),
                ("1", True),
                ("yes", True),
                ("false", False),
                ("False", False),
                ("FALSE", False),
                ("0", False),
                ("no", False),
            ]

            for string_val, expected in test_cases:
                test_config = {"enable_reranking": string_val}
                with open(config_path, "w") as f:
                    yaml.dump(test_config, f)

                config = RaggedConfig.load(config_path)
                assert (
                    config.enable_reranking == expected
                ), f"Expected {string_val} to convert to {expected}"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = RaggedConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["retrieval_method"] == "hybrid"
        assert config_dict["top_k"] == 5
        assert config_dict["persona"] == "balanced"

    def test_save_configuration(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"

            config = RaggedConfig()
            config.top_k = 10
            config.temperature = 0.9
            config.persona = "accuracy"

            config.save(config_path)

            # Verify file was created
            assert config_path.exists()

            # Load and verify
            with open(config_path) as f:
                saved_config = yaml.safe_load(f)

            assert saved_config["top_k"] == 10
            assert saved_config["temperature"] == 0.9
            assert saved_config["persona"] == "accuracy"

    def test_save_creates_directory(self):
        """Test that save creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nested" / "dir" / "config.yml"

            config = RaggedConfig()
            config.save(config_path)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_merge_ignores_unknown_keys(self):
        """Test that merge ignores unknown configuration keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"

            test_config = {
                "top_k": 10,
                "unknown_key": "should_be_ignored",
                "another_unknown": 123,
            }

            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

            config = RaggedConfig.load(config_path)

            # Known key should be loaded
            assert config.top_k == 10

            # Unknown keys should not cause errors
            assert not hasattr(config, "unknown_key")
            assert not hasattr(config, "another_unknown")


class TestConfigValidator:
    """Test ConfigValidator class."""

    def test_validate_default_config(self):
        """Test that default configuration passes validation."""
        config = RaggedConfig()
        validator = ConfigValidator()

        is_valid, errors = validator.validate(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_retrieval_method(self):
        """Test validation of retrieval_method."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Valid methods
        for method in ["hybrid", "vector", "bm25"]:
            config.retrieval_method = method
            is_valid, errors = validator.validate(config)
            assert is_valid is True

        # Invalid method
        config.retrieval_method = "invalid_method"
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert len(errors) > 0
        assert "Invalid retrieval_method" in errors[0]

    def test_validate_weights(self):
        """Test validation of bm25 and vector weights."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Invalid bm25_weight (too high)
        config.bm25_weight = 1.5
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("bm25_weight" in error for error in errors)

        # Invalid bm25_weight (negative)
        config.bm25_weight = -0.1
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("bm25_weight" in error for error in errors)

        # Invalid vector_weight
        config.bm25_weight = 0.3  # Reset
        config.vector_weight = 1.2
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("vector_weight" in error for error in errors)

    def test_validate_top_k_range(self):
        """Test validation of top_k range."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Valid range (adjust rerank_to to match or disable reranking)
        for k in [1, 5, 50, 100]:
            config.top_k = k
            if config.enable_reranking:
                config.rerank_to = min(k, config.rerank_to)
            is_valid, _ = validator.validate(config)
            assert is_valid is True

        # Too low
        config.top_k = 0
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("top_k" in error for error in errors)

        # Too high
        config.top_k = 101
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("top_k" in error for error in errors)

    def test_validate_rerank_to_constraint(self):
        """Test validation that rerank_to cannot exceed top_k."""
        config = RaggedConfig()
        validator = ConfigValidator()

        config.enable_reranking = True
        config.top_k = 5
        config.rerank_to = 10

        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("rerank_to" in error and "top_k" in error for error in errors)

        # Valid case
        config.rerank_to = 3
        is_valid, _ = validator.validate(config)
        assert is_valid is True

    def test_validate_persona(self):
        """Test validation of persona names."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Valid personas
        valid_personas = ["accuracy", "speed", "balanced", "research", "quick-answer"]
        for persona in valid_personas:
            config.persona = persona
            is_valid, _ = validator.validate(config)
            assert is_valid is True, f"Persona {persona} should be valid"

        # Invalid persona
        config.persona = "invalid_persona"
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("Invalid persona" in error for error in errors)

    def test_validate_temperature_range(self):
        """Test validation of temperature range."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Valid range
        for temp in [0.0, 0.5, 1.0, 1.5, 2.0]:
            config.temperature = temp
            is_valid, _ = validator.validate(config)
            assert is_valid is True

        # Too low
        config.temperature = -0.1
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("temperature" in error for error in errors)

        # Too high
        config.temperature = 2.1
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("temperature" in error for error in errors)

    def test_validate_confidence_threshold(self):
        """Test validation of confidence threshold."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Valid range
        for threshold in [0.0, 0.5, 0.85, 1.0]:
            config.confidence_threshold = threshold
            is_valid, _ = validator.validate(config)
            assert is_valid is True

        # Too low
        config.confidence_threshold = -0.1
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("confidence_threshold" in error for error in errors)

        # Too high
        config.confidence_threshold = 1.1
        is_valid, errors = validator.validate(config)
        assert is_valid is False
        assert any("confidence_threshold" in error for error in errors)

    def test_validate_multiple_errors(self):
        """Test that validator returns all errors, not just first one."""
        config = RaggedConfig()
        validator = ConfigValidator()

        # Set multiple invalid values
        config.retrieval_method = "invalid"
        config.top_k = 0
        config.temperature = 3.0
        config.persona = "invalid_persona"

        is_valid, errors = validator.validate(config)

        assert is_valid is False
        assert len(errors) >= 4  # Should report all errors
        assert any("retrieval_method" in error for error in errors)
        assert any("top_k" in error for error in errors)
        assert any("temperature" in error for error in errors)
        assert any("persona" in error for error in errors)
