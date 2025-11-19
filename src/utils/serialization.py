"""Safe serialization utilities to replace pickle.

This module provides secure JSON-based serialization for ragged's data persistence needs.
Unlike pickle, JSON serialization cannot execute arbitrary code, eliminating a critical
security vulnerability (VULN-001: Arbitrary Code Execution via Pickle).

Key Design Principles:
- No arbitrary code execution (unlike pickle)
- Type-safe serialization/deserialization
- Support for common Python types (dict, list, str, int, float, bool, None)
- Migration utilities for legacy pickle files
- Comprehensive error handling

Security: This module addresses CRITICAL-001 from the baseline security audit.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt


class SafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy arrays and other non-standard types.

    Supports:
    - numpy arrays (converted to lists)
    - numpy scalar types (converted to Python primitives)
    - Path objects (converted to strings)

    Raises:
        TypeError: If object type is not serializable
    """

    def default(self, obj: Any) -> Any:
        """Convert non-JSON-serializable objects to serializable equivalents.

        Args:
            obj: Object to encode

        Returns:
            Serializable representation of the object

        Raises:
            TypeError: If object cannot be serialized
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


def save_json(data: Any, filepath: Path) -> None:
    """Save data to JSON file with safe serialization.

    Args:
        data: Data to serialize (must be JSON-compatible or have SafeJSONEncoder support)
        filepath: Path to save JSON file

    Raises:
        OSError: If file cannot be written
        TypeError: If data cannot be serialized

    Security: This replaces pickle.dump() to prevent arbitrary code execution
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=SafeJSONEncoder, indent=2)


def load_json(filepath: Path) -> Any:
    """Load data from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Deserialized data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        OSError: If file cannot be read

    Security: This replaces pickle.load() to prevent arbitrary code execution
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bm25_index(
    corpus_processed: list[list[str]],
    idf: dict[str, float],
    doc_len: list[int],
    avgdl: float,
    filepath: Path,
) -> None:
    """Save BM25 index data to JSON file.

    This replaces pickle serialization for BM25 checkpoints in incremental_index.py.

    Args:
        corpus_processed: Tokenized corpus (list of token lists)
        idf: Inverse document frequency mapping (word -> IDF score)
        doc_len: Document lengths (number of tokens per document)
        avgdl: Average document length
        filepath: Path to save checkpoint

    Raises:
        OSError: If file cannot be written

    Security: Addresses CRITICAL-001 (pickle vulnerability in incremental_index.py:341)
    """
    data = {
        "version": "1.0",  # For future migration compatibility
        "corpus_processed": corpus_processed,
        "idf": idf,
        "doc_len": doc_len,
        "avgdl": avgdl,
    }
    save_json(data, filepath)


def load_bm25_index(filepath: Path) -> tuple[list[list[str]], dict[str, float], list[int], float]:
    """Load BM25 index data from JSON file.

    Args:
        filepath: Path to BM25 checkpoint file

    Returns:
        Tuple of (corpus_processed, idf, doc_len, avgdl)

    Raises:
        FileNotFoundError: If checkpoint file doesn't exist
        KeyError: If checkpoint is missing required fields
        ValueError: If checkpoint version is incompatible

    Security: Replaces pickle.load() for BM25 checkpoints
    """
    data = load_json(filepath)

    # Version check for future compatibility
    version = data.get("version", "1.0")
    if version != "1.0":
        raise ValueError(f"Unsupported BM25 checkpoint version: {version}")

    return (
        data["corpus_processed"],
        data["idf"],
        data["doc_len"],
        data["avgdl"],
    )


def save_cache_entry(key: str, value: Any, metadata: dict[str, Any], filepath: Path) -> None:
    """Save cache entry to JSON file.

    This replaces pickle serialization for L2 disk cache in multi_tier_cache.py.

    Args:
        key: Cache key
        value: Cached value (typically embeddings or retrieved chunks)
        metadata: Cache metadata (timestamp, hit count, etc.)
        filepath: Path to save cache entry

    Raises:
        OSError: If file cannot be written
        TypeError: If value contains non-serializable data

    Security: Addresses CRITICAL-001 (pickle vulnerability in multi_tier_cache.py:12)
    """
    data = {
        "version": "1.0",
        "key": key,
        "value": value,
        "metadata": metadata,
    }
    save_json(data, filepath)


def load_cache_entry(filepath: Path) -> tuple[str, Any, dict[str, Any]]:
    """Load cache entry from JSON file.

    Args:
        filepath: Path to cache entry file

    Returns:
        Tuple of (key, value, metadata)

    Raises:
        FileNotFoundError: If cache file doesn't exist
        KeyError: If cache entry is missing required fields
        ValueError: If cache version is incompatible
    """
    data = load_json(filepath)

    version = data.get("version", "1.0")
    if version != "1.0":
        raise ValueError(f"Unsupported cache entry version: {version}")

    return (
        data["key"],
        data["value"],
        data["metadata"],
    )


def migrate_pickle_to_json(
    pickle_path: Path,
    json_path: Path,
    migration_type: str = "bm25",
) -> bool:
    """Migrate legacy pickle file to secure JSON format.

    This utility helps transition from pickle-based persistence to JSON-based.
    Only use this for trusted pickle files created by previous versions of ragged.

    WARNING: This function uses pickle.load() and should only be run on trusted files.
    Never use this on pickle files from untrusted sources.

    Args:
        pickle_path: Path to legacy .pkl file
        json_path: Path to save migrated .json file
        migration_type: Type of data being migrated ("bm25" or "cache")

    Returns:
        True if migration successful, False otherwise

    Raises:
        ValueError: If migration_type is not supported
        FileNotFoundError: If pickle file doesn't exist

    Security Warning: Uses pickle.load() - only for trusted legacy files
    """
    import pickle  # Import locally to avoid exposing pickle globally

    if migration_type not in ("bm25", "cache"):
        raise ValueError(f"Unsupported migration type: {migration_type}")

    if not pickle_path.exists():
        raise FileNotFoundError(f"Pickle file not found: {pickle_path}")

    try:
        # Load legacy pickle file (SECURITY: Only for trusted ragged-generated files)
        with open(pickle_path, "rb") as f:
            data = pickle.load(f)  # noqa: S301 (only for migration of trusted files)

        # Save as JSON based on migration type
        if migration_type == "bm25":
            # Assume pickle contains tuple (corpus_processed, idf, doc_len, avgdl)
            corpus_processed, idf, doc_len, avgdl = data
            save_bm25_index(corpus_processed, idf, doc_len, avgdl, json_path)
        elif migration_type == "cache":
            # Assume pickle contains dict with key, value, metadata
            save_cache_entry(
                data["key"],
                data["value"],
                data.get("metadata", {}),
                json_path,
            )

        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        return False


def numpy_array_to_list(arr: npt.NDArray[Any]) -> list[Any]:
    """Convert numpy array to Python list for JSON serialization.

    Args:
        arr: Numpy array to convert

    Returns:
        Python list representation
    """
    return arr.tolist()


def list_to_numpy_array(lst: list[Any], dtype: Any = np.float32) -> npt.NDArray[Any]:
    """Convert Python list to numpy array after JSON deserialization.

    Args:
        lst: Python list to convert
        dtype: Numpy data type for array elements

    Returns:
        Numpy array
    """
    return np.array(lst, dtype=dtype)
