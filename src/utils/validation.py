"""Enhanced validation patterns for input sanitization.

SECURITY FIX (MEDIUM-2): Centralized validation to prevent injection and malformed input.

Provides reusable validation functions for:
- File paths and names
- URLs and domains
- Email addresses
- Numeric ranges
- String patterns
- Collection sizes
"""

import re
import os
from pathlib import Path
from typing import Any, List, Optional, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


# SECURITY FIX (MEDIUM-2): Pattern definitions for common validations
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Safe filename: alphanumeric, dash, underscore, dot
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

# Safe path component: no traversal attempts
SAFE_PATH_COMPONENT_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

# Version string: semantic versioning
VERSION_PATTERN = re.compile(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$')

# Plugin name: namespace.plugin_name
PLUGIN_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$')


def validate_string(
    value: Any,
    min_length: int = 0,
    max_length: int = 10000,
    pattern: Optional[re.Pattern] = None,
    field_name: str = "String"
) -> str:
    """Validate string value.

    SECURITY FIX (MEDIUM-2): Validates string length and pattern.

    Args:
        value: Value to validate
        min_length: Minimum length
        max_length: Maximum length
        pattern: Optional regex pattern to match
        field_name: Field name for error messages

    Returns:
        Validated string

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")

    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")

    if len(value) > max_length:
        raise ValidationError(f"{field_name} must not exceed {max_length} characters")

    if pattern and not pattern.match(value):
        raise ValidationError(f"{field_name} does not match required pattern")

    # Check for null bytes
    if '\x00' in value:
        raise ValidationError(f"{field_name} contains null bytes")

    return value


def validate_integer(
    value: Any,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    field_name: str = "Integer"
) -> int:
    """Validate integer value.

    SECURITY FIX (MEDIUM-2): Validates integer range.

    Args:
        value: Value to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        field_name: Field name for error messages

    Returns:
        Validated integer

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{field_name} must be an integer, got {type(value).__name__}")

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}")

    return value


def validate_float(
    value: Any,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    field_name: str = "Float"
) -> float:
    """Validate float value.

    SECURITY FIX (MEDIUM-2): Validates float range.

    Args:
        value: Value to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        field_name: Field name for error messages

    Returns:
        Validated float

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a number, got {type(value).__name__}")

    value = float(value)

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}")

    return value


def validate_list(
    value: Any,
    min_length: int = 0,
    max_length: int = 1000,
    item_type: Optional[type] = None,
    field_name: str = "List"
) -> List:
    """Validate list value.

    SECURITY FIX (MEDIUM-2): Validates list size and item types.

    Args:
        value: Value to validate
        min_length: Minimum number of items
        max_length: Maximum number of items
        item_type: Optional type for list items
        field_name: Field name for error messages

    Returns:
        Validated list

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list, got {type(value).__name__}")

    if len(value) < min_length:
        raise ValidationError(f"{field_name} must have at least {min_length} items")

    if len(value) > max_length:
        raise ValidationError(f"{field_name} must not exceed {max_length} items")

    if item_type is not None:
        for i, item in enumerate(value):
            if not isinstance(item, item_type):
                raise ValidationError(
                    f"{field_name}[{i}] must be {item_type.__name__}, "
                    f"got {type(item).__name__}"
                )

    return value


def validate_email(value: str, field_name: str = "Email") -> str:
    """Validate email address.

    SECURITY FIX (MEDIUM-2): Basic email validation.

    Args:
        value: Email address to validate
        field_name: Field name for error messages

    Returns:
        Validated email address

    Raises:
        ValidationError: If email is invalid
    """
    value = validate_string(value, min_length=3, max_length=254, field_name=field_name)

    if not EMAIL_PATTERN.match(value):
        raise ValidationError(f"{field_name} is not a valid email address")

    return value.lower()


def validate_url(
    value: str,
    allowed_schemes: Optional[List[str]] = None,
    field_name: str = "URL"
) -> str:
    """Validate URL.

    SECURITY FIX (MEDIUM-2): URL validation with scheme checking.

    Args:
        value: URL to validate
        allowed_schemes: Allowed URL schemes (default: http, https)
        field_name: Field name for error messages

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    value = validate_string(value, min_length=1, max_length=2000, field_name=field_name)

    try:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"{field_name} is not a valid URL")

        if parsed.scheme not in allowed_schemes:
            raise ValidationError(
                f"{field_name} scheme must be one of {allowed_schemes}, "
                f"got '{parsed.scheme}'"
            )

        return value
    except Exception as e:
        raise ValidationError(f"{field_name} is not a valid URL: {e}")


def validate_path(
    value: Union[str, Path],
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
    allow_absolute: bool = True,
    allow_relative: bool = True,
    field_name: str = "Path"
) -> Path:
    """Validate file system path.

    SECURITY FIX (MEDIUM-2): Path validation with existence and type checks.

    Args:
        value: Path to validate
        must_exist: Path must exist
        must_be_file: Path must be a file
        must_be_dir: Path must be a directory
        allow_absolute: Allow absolute paths
        allow_relative: Allow relative paths
        field_name: Field name for error messages

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path is invalid
    """
    if isinstance(value, str):
        value = Path(value)
    elif not isinstance(value, Path):
        raise ValidationError(f"{field_name} must be a string or Path, got {type(value).__name__}")

    # Check absolute/relative
    if value.is_absolute() and not allow_absolute:
        raise ValidationError(f"{field_name} must be a relative path")

    if not value.is_absolute() and not allow_relative:
        raise ValidationError(f"{field_name} must be an absolute path")

    # Check for path traversal
    try:
        resolved = value.resolve()
    except Exception as e:
        raise ValidationError(f"{field_name} cannot be resolved: {e}")

    # Check existence
    if must_exist and not resolved.exists():
        raise ValidationError(f"{field_name} does not exist: {value}")

    # Check type
    if must_be_file and resolved.exists() and not resolved.is_file():
        raise ValidationError(f"{field_name} must be a file: {value}")

    if must_be_dir and resolved.exists() and not resolved.is_dir():
        raise ValidationError(f"{field_name} must be a directory: {value}")

    return resolved


def validate_filename(value: str, field_name: str = "Filename") -> str:
    """Validate filename.

    SECURITY FIX (MEDIUM-2): Filename validation to prevent path traversal.

    Args:
        value: Filename to validate
        field_name: Field name for error messages

    Returns:
        Validated filename

    Raises:
        ValidationError: If filename is invalid
    """
    value = validate_string(value, min_length=1, max_length=255, field_name=field_name)

    # Check for path separators (traversal attempt)
    if os.sep in value or '/' in value or '\\' in value:
        raise ValidationError(f"{field_name} must not contain path separators")

    # Check for hidden files/special names
    if value.startswith('.') or value in ('.', '..'):
        raise ValidationError(f"{field_name} must not be a hidden or special file")

    # Check against safe pattern
    if not SAFE_FILENAME_PATTERN.match(value):
        raise ValidationError(
            f"{field_name} contains invalid characters. "
            "Only alphanumeric, dash, underscore, and dot allowed."
        )

    return value


def validate_version(value: str, field_name: str = "Version") -> str:
    """Validate semantic version string.

    SECURITY FIX (MEDIUM-2): Version string validation.

    Args:
        value: Version string to validate (e.g., "1.2.3", "1.0.0-beta")
        field_name: Field name for error messages

    Returns:
        Validated version string

    Raises:
        ValidationError: If version is invalid
    """
    value = validate_string(value, min_length=5, max_length=50, field_name=field_name)

    if not VERSION_PATTERN.match(value):
        raise ValidationError(
            f"{field_name} must follow semantic versioning (e.g., 1.2.3 or 1.2.3-beta)"
        )

    return value


def validate_plugin_name(value: str, field_name: str = "Plugin name") -> str:
    """Validate plugin name.

    SECURITY FIX (MEDIUM-2): Plugin name validation.

    Args:
        value: Plugin name to validate (e.g., "embedder.custom_embedder")
        field_name: Field name for error messages

    Returns:
        Validated plugin name

    Raises:
        ValidationError: If plugin name is invalid
    """
    value = validate_string(value, min_length=3, max_length=100, field_name=field_name)

    if not PLUGIN_NAME_PATTERN.match(value):
        raise ValidationError(
            f"{field_name} must follow format 'type.name' (lowercase, alphanumeric, underscore)"
        )

    return value


def validate_enum(
    value: Any,
    allowed_values: List[Any],
    field_name: str = "Value"
) -> Any:
    """Validate value is in allowed set.

    SECURITY FIX (MEDIUM-2): Enum/choice validation.

    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Field name for error messages

    Returns:
        Validated value

    Raises:
        ValidationError: If value not in allowed set
    """
    if value not in allowed_values:
        raise ValidationError(
            f"{field_name} must be one of {allowed_values}, got '{value}'"
        )

    return value
