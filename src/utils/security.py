"""
Security utilities for input validation and sanitization.

This module provides security functions to prevent common vulnerabilities
like path traversal, file size attacks, and malicious content.
"""

import os
from pathlib import Path
from typing import Optional

from src.config.settings import get_settings


class SecurityError(Exception):
    """Raised when a security violation is detected."""

    pass


def validate_file_path(file_path: Path, allowed_base: Optional[Path] = None) -> Path:
    """
    Validate a file path to prevent path traversal attacks.

    Args:
        file_path: Path to validate
        allowed_base: Optional base directory that file must be within

    Returns:
        Resolved absolute path

    Raises:
        SecurityError: If path is invalid or outside allowed base
        FileNotFoundError: If file doesn't exist
    """
    # Resolve to absolute path
    try:
        resolved = file_path.resolve()
    except (OSError, RuntimeError) as e:
        raise SecurityError(f"Invalid file path: {e}") from e

    # Check file exists
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    # Check if it's a file (not a directory or symlink to directory)
    if not resolved.is_file():
        raise SecurityError(f"Path is not a regular file: {resolved}")

    # If allowed_base is specified, ensure file is within it
    if allowed_base is not None:
        allowed_base_resolved = allowed_base.resolve()
        try:
            resolved.relative_to(allowed_base_resolved)
        except ValueError:
            raise SecurityError(
                f"Path {resolved} is outside allowed directory {allowed_base_resolved}"
            )

    return resolved


def validate_file_size(file_path: Path, max_size_mb: Optional[int] = None) -> int:
    """
    Validate file size to prevent resource exhaustion.

    Args:
        file_path: Path to file
        max_size_mb: Maximum allowed size in MB (uses config default if None)

    Returns:
        File size in bytes

    Raises:
        SecurityError: If file exceeds size limit
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size

    # Get max size from config if not provided
    if max_size_mb is None:
        settings = get_settings()
        max_size_mb = settings.max_file_size_mb

    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        raise SecurityError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed "
            f"size ({max_size_mb} MB): {file_path}"
        )

    return file_size


def validate_mime_type(file_path: Path, expected_types: Optional[list[str]] = None) -> str:
    """
    Validate file MIME type based on content (magic bytes) not just extension.

    Args:
        file_path: Path to file
        expected_types: List of expected MIME types (e.g., ['application/pdf', 'text/plain'])
                        If None, returns detected type without validation.

    Returns:
        Detected MIME type

    Raises:
        SecurityError: If MIME type doesn't match expected types

    Note:
        This is a basic implementation. For production, consider using python-magic
        library for more robust MIME type detection.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read first few bytes to detect file type
    with open(file_path, "rb") as f:
        header = f.read(8)

    # Basic magic byte detection (simplified)
    mime_type = "application/octet-stream"  # Default

    if header.startswith(b"%PDF"):
        mime_type = "application/pdf"
    elif header.startswith(b"PK\x03\x04"):  # ZIP-based formats
        # Could be DOCX, but we'll treat as generic zip
        mime_type = "application/zip"
    elif header.startswith(b"\x89PNG"):
        mime_type = "image/png"
    elif header.startswith(b"\xFF\xD8\xFF"):
        mime_type = "image/jpeg"
    elif header[:2] in (b"<!", b"<?", b"<h", b"<H", b"<d", b"<D"):  # HTML markers
        mime_type = "text/html"
    else:
        # Try to detect text files
        try:
            f.seek(0)
            content = f.read(512)
            content.decode("utf-8")
            mime_type = "text/plain"
        except (UnicodeDecodeError, OSError):
            pass

    # Validate against expected types if provided
    if expected_types is not None:
        if mime_type not in expected_types:
            raise SecurityError(
                f"File type {mime_type} not in allowed types {expected_types}: {file_path}"
            )

    return mime_type


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename safe for filesystem operations

    Raises:
        SecurityError: If filename is invalid or empty after sanitization
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Remove null bytes and control characters
    filename = "".join(c for c in filename if c.isprintable() and c != "\0")

    # Remove path traversal attempts
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")

    # Limit length
    if len(filename) > max_length:
        # Preserve extension if possible
        name, ext = os.path.splitext(filename)
        max_name_len = max_length - len(ext)
        filename = name[:max_name_len] + ext

    # Ensure not empty
    if not filename:
        raise SecurityError("Filename is empty after sanitization")

    return filename


def is_safe_content(content: str, max_length: int = 100_000_000) -> bool:
    """
    Check if content is safe to process.

    Args:
        content: Content to check
        max_length: Maximum allowed content length

    Returns:
        True if content is safe

    Raises:
        SecurityError: If content exceeds length limit
    """
    if len(content) > max_length:
        raise SecurityError(
            f"Content length ({len(content)}) exceeds maximum ({max_length})"
        )

    return True
