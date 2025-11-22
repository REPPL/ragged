"""Metadata serialisation for ChromaDB compatibility.

ChromaDB only accepts str, int, float, bool for metadata values.
This module provides utilities to serialise/deserialise complex types
like lists, dicts, Path objects, and datetimes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


def serialize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Serialise metadata for ChromaDB storage.

    Converts complex types to ChromaDB-compatible simple types:
    - Path → str
    - datetime → ISO format str
    - list/dict → JSON str (with special prefix)
    - None → removed
    - str/int/float/bool → unchanged

    Args:
        metadata: Metadata dictionary with potentially complex types

    Returns:
        Serialised metadata with only str/int/float/bool values

    Example:
        >>> metadata = {
        ...     "path": Path("/data/file.pdf"),
        ...     "tags": ["ML", "AI"],
        ...     "config": {"model": "llama2"},
        ...     "count": 5,
        ...     "active": True,
        ...     "missing": None
        ... }
        >>> serialize_metadata(metadata)
        {
            "path": "/data/file.pdf",
            "tags": "__json__:[\"ML\", \"AI\"]",
            "config": "__json__:{\"model\": \"llama2\"}",
            "count": 5,
            "active": True
        }
    """
    serialized: dict[str, Any] = {}

    for key, value in metadata.items():
        # Skip None values
        if value is None:
            continue

        # Path objects → string
        if isinstance(value, Path):
            serialized[key] = str(value)

        # datetime → ISO format string
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()

        # Lists and dicts → JSON string with special prefix
        elif isinstance(value, (list, dict)):
            json_str = json.dumps(value, ensure_ascii=False)
            serialized[key] = f"__json__:{json_str}"

        # Simple types → unchanged
        elif isinstance(value, (str, int, float, bool)):
            serialized[key] = value

        # Unknown types → string representation with warning
        else:
            logger.warning(
                f"Unknown metadata type for key '{key}': {type(value).__name__}. "
                f"Converting to string."
            )
            serialized[key] = str(value)

    return serialized


def deserialize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Deserialise metadata from ChromaDB storage.

    Converts serialised values back to original types:
    - "__json__:..." → list/dict (parsed from JSON)
    - Other values → unchanged

    Args:
        metadata: Serialised metadata from ChromaDB

    Returns:
        Deserialised metadata with original types restored

    Raises:
        ValueError: If JSON is too large or deeply nested (security protection)

    Example:
        >>> metadata = {
        ...     "path": "/data/file.pdf",
        ...     "tags": "__json__:[\"ML\", \"AI\"]",
        ...     "config": "__json__:{\"model\": \"llama2\"}",
        ...     "count": 5
        ... }
        >>> deserialize_metadata(metadata)
        {
            "path": "/data/file.pdf",
            "tags": ["ML", "AI"],
            "config": {"model": "llama2"},
            "count": 5
        }
    """
    # SECURITY FIX (CRITICAL-1): Limits to prevent JSON DoS attacks
    MAX_JSON_SIZE = 100_000  # 100KB per JSON field
    MAX_NESTING_DEPTH = 10  # Maximum object/array nesting

    deserialized = {}

    for key, value in metadata.items():
        # JSON-serialised values → parse back to original type
        if isinstance(value, str) and value.startswith("__json__:"):
            json_str = value[len("__json__:"):]

            # SECURITY FIX (CRITICAL-1): Validate JSON size before parsing
            if len(json_str) > MAX_JSON_SIZE:
                logger.error(
                    f"JSON field '{key}' exceeds size limit ({len(json_str)} > {MAX_JSON_SIZE}). "
                    f"Potential DoS attack detected."
                )
                raise ValueError(
                    f"JSON field '{key}' exceeds maximum size ({MAX_JSON_SIZE} bytes)"
                )

            try:
                parsed_value = json.loads(json_str)

                # SECURITY FIX (CRITICAL-1): Validate nesting depth
                if not _is_safe_json_depth(parsed_value, MAX_NESTING_DEPTH):
                    logger.error(
                        f"JSON field '{key}' exceeds nesting depth limit ({MAX_NESTING_DEPTH}). "
                        f"Potential DoS attack detected."
                    )
                    raise ValueError(
                        f"JSON field '{key}' exceeds maximum nesting depth ({MAX_NESTING_DEPTH})"
                    )

                deserialized[key] = parsed_value

            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to deserialise JSON for key '{key}': {e}. "
                    f"Keeping as string."
                )
                deserialized[key] = value

        # All other values → unchanged
        else:
            deserialized[key] = value

    return deserialized


def _is_safe_json_depth(obj: Any, max_depth: int, current_depth: int = 0) -> bool:
    """
    Check if JSON object/array nesting depth is within safe limits.

    SECURITY FIX (CRITICAL-1): Prevents deeply nested JSON from causing parser DoS.

    Args:
        obj: Object to check (dict, list, or primitive)
        max_depth: Maximum allowed nesting depth
        current_depth: Current recursion depth

    Returns:
        True if depth is safe, False otherwise

    Example:
        >>> _is_safe_json_depth({"a": {"b": {"c": "value"}}}, max_depth=3)
        True
        >>> _is_safe_json_depth({"a": {"b": {"c": {"d": "value"}}}}, max_depth=3)
        False
    """
    if current_depth > max_depth:
        return False

    if isinstance(obj, dict):
        return all(
            _is_safe_json_depth(value, max_depth, current_depth + 1)
            for value in obj.values()
        )
    elif isinstance(obj, list):
        return all(
            _is_safe_json_depth(item, max_depth, current_depth + 1) for item in obj
        )
    else:
        # Primitive types (str, int, float, bool, None) are safe
        return True


def serialize_batch_metadata(metadatas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialise a batch of metadata dictionaries.

    Args:
        metadatas: List of metadata dictionaries

    Returns:
        List of serialised metadata dictionaries
    """
    return [serialize_metadata(m) for m in metadatas]


def deserialize_batch_metadata(metadatas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deserialise a batch of metadata dictionaries.

    Args:
        metadatas: List of serialised metadata dictionaries

    Returns:
        List of deserialised metadata dictionaries
    """
    return [deserialize_metadata(m) for m in metadatas]
