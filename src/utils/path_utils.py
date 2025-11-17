"""Path handling utilities for secure file operations.

Provides validated path operations to prevent security vulnerabilities
like directory traversal and ensure consistent path handling.
"""

import os
from pathlib import Path
from typing import List, Optional, Union

from src.exceptions import InvalidPathError, ResourceNotFoundError


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize a path to absolute, resolved form.

    Resolves symlinks, removes redundant separators, and converts to absolute path.

    Args:
        path: Path to normalize

    Returns:
        Normalized absolute Path object

    Example:
        >>> normalize_path("./docs/../src/main.py")
        PosixPath('/app/src/main.py')
    """
    return Path(path).expanduser().resolve()


def validate_path_exists(path: Union[str, Path], must_be_file: bool = False, must_be_dir: bool = False) -> Path:
    """Validate that a path exists and optionally check its type.

    Args:
        path: Path to validate
        must_be_file: If True, raise error if not a file
        must_be_dir: If True, raise error if not a directory

    Returns:
        Normalized path

    Raises:
        ResourceNotFoundError: If path doesn't exist or type mismatch
        InvalidPathError: If both must_be_file and must_be_dir are True
    """
    if must_be_file and must_be_dir:
        raise InvalidPathError(
            "Cannot require both file and directory",
            {"must_be_file": True, "must_be_dir": True}
        )

    normalized = normalize_path(path)

    if not normalized.exists():
        raise ResourceNotFoundError(
            f"Path does not exist: {normalized}",
            {"path": str(normalized)}
        )

    if must_be_file and not normalized.is_file():
        raise ResourceNotFoundError(
            f"Path is not a file: {normalized}",
            {"path": str(normalized), "expected": "file"}
        )

    if must_be_dir and not normalized.is_dir():
        raise ResourceNotFoundError(
            f"Path is not a directory: {normalized}",
            {"path": str(normalized), "expected": "directory"}
        )

    return normalized


def safe_join(base: Union[str, Path], *paths: Union[str, Path]) -> Path:
    """Safely join paths and validate result is within base directory.

    Prevents directory traversal attacks by ensuring the result
    stays within the base directory.

    Args:
        base: Base directory path
        *paths: Path components to join

    Returns:
        Joined and validated path

    Raises:
        InvalidPathError: If result path is outside base directory

    Example:
        >>> safe_join("/data", "documents", "file.txt")
        PosixPath('/data/documents/file.txt')

        >>> safe_join("/data", "../etc/passwd")
        # Raises InvalidPathError
    """
    base_norm = normalize_path(base)
    joined = base_norm.joinpath(*paths)
    result = normalize_path(joined)

    # Check if result is within base directory
    try:
        result.relative_to(base_norm)
    except ValueError:
        raise InvalidPathError(
            f"Path traversal attempt: result outside base directory",
            {
                "base": str(base_norm),
                "result": str(result),
                "paths": [str(p) for p in paths]
            }
        )

    return result


def validate_file_extension(path: Union[str, Path], allowed_extensions: List[str]) -> Path:
    """Validate that a file has an allowed extension.

    Args:
        path: Path to validate
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.txt'])

    Returns:
        Normalized path

    Raises:
        InvalidPathError: If extension not allowed
    """
    normalized = normalize_path(path)
    ext = normalized.suffix.lower()

    # Normalize extensions to lowercase
    allowed = [e.lower() if e.startswith('.') else f".{e.lower()}" for e in allowed_extensions]

    if ext not in allowed:
        raise InvalidPathError(
            f"File extension not allowed: {ext}",
            {
                "path": str(normalized),
                "extension": ext,
                "allowed": allowed
            }
        )

    return normalized


def ensure_directory(path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path
        parents: Create parent directories if needed
        exist_ok: Don't raise error if directory already exists

    Returns:
        Normalized directory path

    Raises:
        InvalidPathError: If creation fails or path exists as non-directory
    """
    normalized = normalize_path(path)

    if normalized.exists() and not normalized.is_dir():
        raise InvalidPathError(
            f"Path exists but is not a directory: {normalized}",
            {"path": str(normalized)}
        )

    try:
        normalized.mkdir(parents=parents, exist_ok=exist_ok)
    except (OSError, PermissionError) as e:
        raise InvalidPathError(
            f"Failed to create directory: {normalized}",
            {"path": str(normalized), "error": str(e)}
        ) from e

    return normalized


def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """Get relative path from base to path.

    Args:
        path: Target path
        base: Base directory

    Returns:
        Relative path

    Raises:
        InvalidPathError: If path is not relative to base
    """
    path_norm = normalize_path(path)
    base_norm = normalize_path(base)

    try:
        return path_norm.relative_to(base_norm)
    except ValueError:
        raise InvalidPathError(
            f"Path is not relative to base",
            {
                "path": str(path_norm),
                "base": str(base_norm)
            }
        )


def validate_directory_not_empty(path: Union[str, Path]) -> Path:
    """Validate that a directory exists and is not empty.

    Args:
        path: Directory path to check

    Returns:
        Normalized directory path

    Raises:
        ResourceNotFoundError: If directory doesn't exist or is empty
    """
    normalized = validate_path_exists(path, must_be_dir=True)

    # Check if directory has any files
    if not any(normalized.iterdir()):
        raise ResourceNotFoundError(
            f"Directory is empty: {normalized}",
            {"path": str(normalized)}
        )

    return normalized


def is_hidden_path(path: Union[str, Path]) -> bool:
    """Check if a path or any of its parents are hidden.

    Hidden paths start with '.' (Unix convention).

    Args:
        path: Path to check

    Returns:
        True if path or any parent is hidden

    Example:
        >>> is_hidden_path(".hidden/file.txt")
        True
        >>> is_hidden_path("docs/.git/config")
        True
        >>> is_hidden_path("docs/README.md")
        False
    """
    normalized = normalize_path(path)

    # Check if file/dir itself is hidden
    if normalized.name.startswith('.') and normalized.name not in {'.', '..'}:
        return True

    # Check parents
    for parent in normalized.parents:
        if parent.name.startswith('.') and parent.name not in {'.', '..'}:
            return True

    return False


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize a filename by removing/replacing invalid characters.

    Removes or replaces characters that are invalid in filenames
    across different operating systems.

    Args:
        filename: Filename to sanitize
        replacement: Character to use for replacement

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("my/file:name.txt")
        "my_file_name.txt"
    """
    # Invalid characters for Windows/Unix
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, replacement)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Don't allow empty names
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def get_file_size_mb(path: Union[str, Path]) -> float:
    """Get file size in megabytes.

    Args:
        path: File path

    Returns:
        Size in MB

    Raises:
        ResourceNotFoundError: If file doesn't exist
    """
    normalized = validate_path_exists(path, must_be_file=True)
    size_bytes = normalized.stat().st_size
    return size_bytes / (1024 * 1024)


def get_directory_size_mb(path: Union[str, Path]) -> float:
    """Get total size of directory contents in megabytes.

    Recursively sums all file sizes in directory.

    Args:
        path: Directory path

    Returns:
        Total size in MB

    Raises:
        ResourceNotFoundError: If directory doesn't exist
    """
    normalized = validate_path_exists(path, must_be_dir=True)

    total_size = 0
    for item in normalized.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size

    return total_size / (1024 * 1024)
