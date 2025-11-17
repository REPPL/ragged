"""Hashing utilities for content and data integrity.

Provides consistent SHA-256 hashing functions used throughout the codebase.
"""

import hashlib
from typing import Union


def hash_content(content: Union[str, bytes], encoding: str = "utf-8") -> str:
    """Generate SHA-256 hash of content.

    Args:
        content: Content to hash (string or bytes)
        encoding: Encoding to use if content is string (default: utf-8)

    Returns:
        Hexadecimal SHA-256 hash string

    Examples:
        >>> hash_content("hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'

        >>> hash_content(b"hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    if isinstance(content, str):
        content = content.encode(encoding)

    return hashlib.sha256(content).hexdigest()


def hash_file_content(content: str, sample_size: int = 1024) -> str:
    """Generate SHA-256 hash of file content using first and last samples.

    For large files, hashing only the beginning and end provides a good
    balance between uniqueness and performance.

    Args:
        content: Full file content as string
        sample_size: Number of bytes to sample from start and end (default: 1024)

    Returns:
        Hexadecimal SHA-256 hash string

    Examples:
        >>> content = "a" * 10000
        >>> hash_file_content(content, sample_size=100)
        # Returns hash of first 100 + last 100 bytes
    """
    content_bytes = content.encode("utf-8")

    if len(content_bytes) <= sample_size * 2:
        # File is small enough to hash entirely
        return hashlib.sha256(content_bytes).hexdigest()

    # Sample first and last portions
    first_sample = content_bytes[:sample_size]
    last_sample = content_bytes[-sample_size:]

    return hashlib.sha256(first_sample + last_sample).hexdigest()


def hash_query(query: str) -> str:
    """Generate cache key hash for query strings.

    Convenience function for hashing queries consistently across retrieval
    and caching systems.

    Args:
        query: Query string to hash

    Returns:
        Hexadecimal SHA-256 hash string

    Examples:
        >>> hash_query("what is machine learning?")
        # Returns consistent hash for caching
    """
    return hash_content(query)
