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
    deserialized = {}

    for key, value in metadata.items():
        # JSON-serialised values → parse back to original type
        if isinstance(value, str) and value.startswith("__json__:"):
            json_str = value[len("__json__:"):]
            try:
                deserialized[key] = json.loads(json_str)
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
