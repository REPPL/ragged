"""Tests for configuration validator.

v0.3.10: Test YAML config validation.
"""

import tempfile
from pathlib import Path

import pytest

from src.testing.config_validator import (
    ConfigValidator,
    ValidationError,
    ValidationIssue,
    ValidationResult,
    create_config_validator,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_init_valid(self):
        """Test initialisation of valid result."""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issues == 0

    def test_add_error(self):
        """Test adding error."""
        result = ValidationResult(valid=True)

        result.add_error("schema", "Test error", field="test.field")

        assert result.valid is False
        assert result.error_count == 1
        assert result.errors[0].level == "error"
        assert result.errors[0].category == "schema"
        assert result.errors[0].message == "Test error"
        assert result.errors[0].field == "test.field"

    def test_add_warning(self):
        """Test adding warning."""
        result = ValidationResult(valid=True)

        result.add_warning("semantic", "Test warning", field="test.field")

        assert result.valid is True  # Warnings don't invalidate
        assert result.warning_count == 1
        assert result.warnings[0].level == "warning"
        assert result.warnings[0].category == "semantic"

    def test_multiple_issues(self):
        """Test multiple errors and warnings."""
        result = ValidationResult(valid=True)

        result.add_error("schema", "Error 1")
        result.add_error("syntax", "Error 2")
        result.add_warning("semantic", "Warning 1")
        result.add_warning("security", "Warning 2")

        assert result.error_count == 2
        assert result.warning_count == 2
        assert result.total_issues == 4


class TestConfigValidatorInit:
    """Test ConfigValidator initialisation."""

    def test_init(self):
        """Test basic initialisation."""
        validator = ConfigValidator()

        assert validator is not None

    def test_create_config_validator(self):
        """Test convenience function."""
        validator = create_config_validator()

        assert isinstance(validator, ConfigValidator)


class TestYAMLSyntaxValidation:
    """Test YAML syntax validation."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return ConfigValidator()

    def test_validate_valid_yaml(self, validator, tmp_path):
        """Test validating valid YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 500
  chunk_overlap: 50
retrieval:
  top_k: 5
""")

        result = validator.validate(config_file)

        assert result.valid is True
        assert result.error_count == 0

    def test_validate_invalid_yaml(self, validator, tmp_path):
        """Test validating invalid YAML syntax."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 500
  invalid: {unclosed
""")

        result = validator.validate(config_file)

        assert result.valid is False
        assert result.error_count > 0
        assert any(e.category == "syntax" for e in result.errors)

    def test_validate_empty_file(self, validator, tmp_path):
        """Test validating empty file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any("empty" in e.message.lower() for e in result.errors)

    def test_validate_file_not_found(self, validator, tmp_path):
        """Test validating non-existent file."""
        config_file = tmp_path / "nonexistent.yaml"

        result = validator.validate(config_file)

        assert result.valid is False
        assert any("not found" in e.message.lower() for e in result.errors)

    def test_validate_not_dict(self, validator, tmp_path):
        """Test validating YAML that's not a dictionary."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("- item1\n- item2\n")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any("object" in e.message.lower() for e in result.errors)


class TestSchemaValidation:
    """Test schema validation."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return ConfigValidator()

    def test_validate_valid_schema(self, validator, tmp_path):
        """Test validating config with valid schema."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 500
  chunk_overlap: 50
  strategy: recursive
retrieval:
  top_k: 5
  method: hybrid
generation:
  model: llama3.2:latest
  temperature: 0.7
  max_tokens: 2048
""")

        result = validator.validate(config_file)

        assert result.valid is True
        assert not any(e.category == "schema" for e in result.errors)

    def test_validate_invalid_chunk_size(self, validator, tmp_path):
        """Test validating invalid chunk_size."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 50  # Too small (< 100)
""")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any(e.category == "schema" and "chunk_size" in e.message for e in result.errors)

    def test_validate_invalid_top_k(self, validator, tmp_path):
        """Test validating invalid top_k."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
retrieval:
  top_k: 0  # Too small (< 1)
""")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any(e.category == "schema" and "top_k" in e.message for e in result.errors)

    def test_validate_invalid_temperature(self, validator, tmp_path):
        """Test validating invalid temperature."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
generation:
  temperature: 3.0  # Too high (> 2.0)
""")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any(
            e.category == "schema" and "temperature" in e.message for e in result.errors
        )


class TestSemanticValidation:
    """Test semantic validation (best practices)."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return ConfigValidator()

    def test_high_top_k_warning(self, validator, tmp_path):
        """Test warning for high top_k."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
retrieval:
  top_k: 20
""")

        result = validator.validate(config_file)

        assert result.valid is True  # Warning, not error
        assert result.warning_count > 0
        assert any(
            "top_k" in w.message and w.category == "semantic" for w in result.warnings
        )

    def test_large_chunk_size_warning(self, validator, tmp_path):
        """Test warning for large chunk_size."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 1800
""")

        result = validator.validate(config_file)

        assert result.warning_count > 0
        assert any(
            "chunk_size" in w.message and "large" in w.message.lower()
            for w in result.warnings
        )

    def test_small_chunk_size_warning(self, validator, tmp_path):
        """Test warning for small chunk_size."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 150
""")

        result = validator.validate(config_file)

        assert result.warning_count > 0
        assert any(
            "chunk_size" in w.message and "small" in w.message.lower()
            for w in result.warnings
        )

    def test_overlap_exceeds_chunk_size(self, validator, tmp_path):
        """Test error when overlap >= chunk_size."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 500
  chunk_overlap: 500
""")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any(
            "overlap" in e.message and e.category == "semantic" for e in result.errors
        )

    def test_high_overlap_warning(self, validator, tmp_path):
        """Test warning for high overlap (>50% of chunk_size)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
chunking:
  chunk_size: 500
  chunk_overlap: 300
""")

        result = validator.validate(config_file)

        assert result.warning_count > 0
        assert any("overlap" in w.message and w.category == "semantic" for w in result.warnings)

    def test_high_temperature_warning(self, validator, tmp_path):
        """Test warning for high temperature."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
generation:
  temperature: 1.8
""")

        result = validator.validate(config_file)

        assert result.warning_count > 0
        assert any(
            "temperature" in w.message and "high" in w.message.lower()
            for w in result.warnings
        )

    def test_low_temperature_warning(self, validator, tmp_path):
        """Test warning for very low temperature."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
generation:
  temperature: 0.05
""")

        result = validator.validate(config_file)

        assert result.warning_count > 0
        assert any(
            "temperature" in w.message and "low" in w.message.lower()
            for w in result.warnings
        )


class TestSecurityValidation:
    """Test security validation."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return ConfigValidator()

    def test_detect_api_key_openai_style(self, validator, tmp_path):
        """Test detection of OpenAI-style API key."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
generation:
  api_key: sk-abcdefghijklmnopqrstuvwxyz123456
""")

        result = validator.validate(config_file)

        assert result.valid is False
        assert any(
            "api key" in e.message.lower() and e.category == "security"
            for e in result.errors
        )

    def test_no_api_key_detected(self, validator, tmp_path):
        """Test no false positive for API key detection."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
generation:
  model: gpt-3.5-turbo
  temperature: 0.7
""")

        result = validator.validate(config_file)

        assert not any(e.category == "security" for e in result.errors)


class TestValidateString:
    """Test string validation (no file)."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return ConfigValidator()

    def test_validate_valid_string(self, validator):
        """Test validating valid YAML string."""
        config_string = """
chunking:
  chunk_size: 500
retrieval:
  top_k: 5
"""

        result = validator.validate_string(config_string)

        assert result.valid is True

    def test_validate_invalid_string(self, validator):
        """Test validating invalid YAML string."""
        config_string = """
chunking:
  chunk_size: 50  # Too small
"""

        result = validator.validate_string(config_string)

        assert result.valid is False

    def test_validate_empty_string(self, validator):
        """Test validating empty string."""
        result = validator.validate_string("")

        assert result.valid is False
        assert any("empty" in e.message.lower() for e in result.errors)

    def test_validate_string_api_key(self, validator):
        """Test API key detection in string."""
        config_string = """
api_key: sk-test1234567890abcdefgh
"""

        result = validator.validate_string(config_string)

        assert result.valid is False
        assert any(
            "api key" in e.message.lower() and e.category == "security"
            for e in result.errors
        )
