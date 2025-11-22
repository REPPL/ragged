"""
Configuration validation for ragged.

v0.3.10: Validate YAML configs for syntax, schema, and security.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Configuration validation error."""

    pass


@dataclass
class ValidationIssue:
    """A single validation issue."""

    level: str  # 'error' or 'warning'
    category: str  # 'syntax', 'schema', 'semantic', 'security'
    message: str
    field: str | None = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return len(self.warnings)

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return self.error_count + self.warning_count

    def add_error(self, category: str, message: str, field: str | None = None):
        """Add an error."""
        self.errors.append(
            ValidationIssue(level="error", category=category, message=message, field=field)
        )
        self.valid = False

    def add_warning(self, category: str, message: str, field: str | None = None):
        """Add a warning."""
        self.warnings.append(
            ValidationIssue(level="warning", category=category, message=message, field=field)
        )


# Pydantic models for schema validation
class ChunkingConfig(BaseModel):
    """Chunking configuration schema."""

    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    strategy: str = Field(default="recursive")


class RetrievalConfig(BaseModel):
    """Retrieval configuration schema."""

    top_k: int = Field(default=5, ge=1, le=50)
    method: str = Field(default="hybrid")


class GenerationConfig(BaseModel):
    """Generation configuration schema."""

    model: str = Field(default="llama3.2:latest")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class RaggedConfig(BaseModel):
    """Full ragged configuration schema."""

    chunking: ChunkingConfig | None = None
    retrieval: RetrievalConfig | None = None
    generation: GenerationConfig | None = None


class ConfigValidator:
    """
    Validate ragged configuration files.

    Performs syntax, schema, semantic, and security validation.

    Example:
        >>> validator = ConfigValidator()
        >>> result = validator.validate(Path("config.yaml"))
        >>> if result.valid:
        ...     print("Config is valid")
        >>> else:
        ...     for error in result.errors:
        ...         print(f"Error: {error.message}")
    """

    def __init__(self):
        """Initialise validator."""
        logger.info("ConfigValidator initialised")

    def validate(self, config_path: Path) -> ValidationResult:
        """
        Validate configuration file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        # 1. Check file exists
        if not config_path.exists():
            result.add_error("syntax", f"Configuration file not found: {config_path}")
            return result

        # 2. Validate YAML syntax
        config_data = self._validate_yaml_syntax(config_path, result)
        if not config_data:
            return result  # Syntax errors prevent further validation

        # 3. Validate schema
        self._validate_schema(config_data, result)

        # 4. Validate semantics (best practices)
        self._validate_semantics(config_data, result)

        # 5. Validate security
        self._validate_security(config_path, config_data, result)

        logger.info(
            f"Validation complete: {result.error_count} errors, {result.warning_count} warnings"
        )
        return result

    def _validate_yaml_syntax(
        self, config_path: Path, result: ValidationResult
    ) -> dict[str, Any] | None:
        """
        Validate YAML syntax.

        Args:
            config_path: Path to YAML file
            result: ValidationResult to update

        Returns:
            Parsed config data or None if syntax error
        """
        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                result.add_error("syntax", "Configuration file is empty")
                return None

            if not isinstance(config_data, dict):
                result.add_error("syntax", "Configuration must be a YAML object (key-value pairs)")
                return None

            logger.debug("YAML syntax validation passed")
            return config_data

        except yaml.YAMLError as e:
            result.add_error("syntax", f"YAML syntax error: {e}")
            return None
        except Exception as e:
            result.add_error("syntax", f"Failed to read configuration: {e}")
            return None

    def _validate_schema(self, config_data: dict[str, Any], result: ValidationResult):
        """
        Validate configuration schema using Pydantic.

        Args:
            config_data: Parsed configuration data
            result: ValidationResult to update
        """
        try:
            # Validate with Pydantic model
            RaggedConfig(**config_data)
            logger.debug("Schema validation passed")

        except PydanticValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                result.add_error("schema", f"Field '{field}': {message}", field=field)

        except Exception as e:
            result.add_error("schema", f"Schema validation failed: {e}")

    def _validate_semantics(self, config_data: dict[str, Any], result: ValidationResult):
        """
        Validate semantic rules (best practices).

        Args:
            config_data: Parsed configuration data
            result: ValidationResult to update
        """
        # Check retrieval.top_k
        retrieval = config_data.get("retrieval", {})
        top_k = retrieval.get("top_k", 5)
        if top_k > 10:
            result.add_warning(
                "semantic",
                f"retrieval.top_k={top_k} is high (recommended: 5-10)",
                field="retrieval.top_k",
            )

        # Check chunking.chunk_size
        chunking = config_data.get("chunking", {})
        chunk_size = chunking.get("chunk_size", 500)
        if chunk_size > 1500:
            result.add_warning(
                "semantic",
                f"chunking.chunk_size={chunk_size} may be too large (recommended: 200-1000)",
                field="chunking.chunk_size",
            )
        elif chunk_size < 200:
            result.add_warning(
                "semantic",
                f"chunking.chunk_size={chunk_size} may be too small (recommended: 200-1000)",
                field="chunking.chunk_size",
            )

        # Check chunk_overlap vs chunk_size
        chunk_overlap = chunking.get("chunk_overlap", 50)
        if chunk_overlap >= chunk_size:
            result.add_error(
                "semantic",
                f"chunking.chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})",
                field="chunking.chunk_overlap",
            )
        elif chunk_overlap > chunk_size * 0.5:
            result.add_warning(
                "semantic",
                f"chunking.chunk_overlap ({chunk_overlap}) is >50% of chunk_size (recommended: 10-20%)",
                field="chunking.chunk_overlap",
            )

        # Check generation.temperature
        generation = config_data.get("generation", {})
        temperature = generation.get("temperature", 0.7)
        if temperature > 1.5:
            result.add_warning(
                "semantic",
                f"generation.temperature={temperature} is high (may produce inconsistent results)",
                field="generation.temperature",
            )
        elif temperature < 0.1:
            result.add_warning(
                "semantic",
                f"generation.temperature={temperature} is very low (may be too deterministic)",
                field="generation.temperature",
            )

        logger.debug("Semantic validation complete")

    def _validate_security(
        self, config_path: Path, config_data: dict[str, Any], result: ValidationResult
    ):
        """
        Validate security aspects.

        Args:
            config_path: Path to config file
            config_data: Parsed configuration data
            result: ValidationResult to update
        """
        # Check for hardcoded API keys in config
        config_str = yaml.dump(config_data)

        # Pattern for potential API keys
        api_key_patterns = [
            r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style
            r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9]{20,}",  # Generic api_key
        ]

        for pattern in api_key_patterns:
            if re.search(pattern, config_str):
                result.add_error(
                    "security",
                    "Potential hardcoded API key detected in configuration",
                )

        # Check file permissions (Unix only)
        if hasattr(os, "stat"):
            try:
                stat_info = config_path.stat()
                mode = stat_info.st_mode
                # Check if readable by others (0o004)
                if mode & 0o004:
                    result.add_warning(
                        "security",
                        f"Configuration file is world-readable (permissions: {oct(mode)[-3:]})",
                    )
            except Exception:
                pass  # Skip permission check if it fails

        logger.debug("Security validation complete")

    def validate_string(self, config_string: str) -> ValidationResult:
        """
        Validate configuration from string.

        Args:
            config_string: YAML configuration as string

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Parse YAML
        try:
            config_data = yaml.safe_load(config_string)

            if config_data is None:
                result.add_error("syntax", "Configuration is empty")
                return result

            if not isinstance(config_data, dict):
                result.add_error("syntax", "Configuration must be a YAML object")
                return result

        except yaml.YAMLError as e:
            result.add_error("syntax", f"YAML syntax error: {e}")
            return result

        # Validate schema
        self._validate_schema(config_data, result)

        # Validate semantics
        self._validate_semantics(config_data, result)

        # Security validation (no file path available)
        config_str = config_string
        if re.search(r"sk-[a-zA-Z0-9]{20,}", config_str):
            result.add_error(
                "security",
                "Potential hardcoded API key detected in configuration",
            )

        return result


# Convenience function
def create_config_validator() -> ConfigValidator:
    """
    Create a configuration validator.

    Returns:
        ConfigValidator instance

    Example:
        >>> validator = create_config_validator()
        >>> result = validator.validate(Path("config.yaml"))
    """
    return ConfigValidator()
