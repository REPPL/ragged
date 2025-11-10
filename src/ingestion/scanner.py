"""Directory scanner for batch document ingestion.

Recursively finds supported documents in directories while
respecting ignore patterns and security constraints.
"""

import fnmatch
from pathlib import Path
from typing import List, Optional, Set

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Supported document extensions
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}

# Default patterns to ignore (similar to .gitignore)
DEFAULT_IGNORE_PATTERNS = {
    ".*",  # Hidden files/folders (starts with dot)
    "__pycache__",
    "node_modules",
    ".git",
    ".venv*",
    "venv*",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "Thumbs.db",
}


class DocumentScanner:
    """Scans directories for supported documents."""

    def __init__(
        self,
        follow_symlinks: bool = False,
        max_depth: Optional[int] = None,
        ignore_patterns: Optional[Set[str]] = None,
    ):
        """Initialize document scanner.

        Args:
            follow_symlinks: Whether to follow symbolic links
            max_depth: Maximum directory depth (None for unlimited)
            ignore_patterns: Set of patterns to ignore (fnmatch style)
        """
        self.follow_symlinks = follow_symlinks
        self.max_depth = max_depth
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS

    def scan(self, path: Path) -> List[Path]:
        """
        Recursively scan directory for supported documents.

        If path is a file, returns it as a single-item list.
        If path is a directory, recursively finds all supported documents.

        Args:
            path: File or directory path to scan

        Returns:
            Sorted list of absolute paths to documents

        Raises:
            ValueError: If path is neither a file nor directory
        """
        path = path.resolve()  # Convert to absolute path

        if path.is_file():
            # Single file - check if supported
            if self._is_supported_format(path):
                return [path]
            else:
                logger.warning(f"Unsupported file format: {path}")
                return []

        if not path.is_dir():
            raise ValueError(f"Path is not a file or directory: {path}")

        # Directory - scan recursively
        documents = []
        self._scan_recursive(path, depth=0, results=documents)

        # Return sorted for deterministic order
        return sorted(documents)

    def _scan_recursive(
        self, dir_path: Path, depth: int, results: List[Path]
    ) -> None:
        """Recursive directory traversal.

        Args:
            dir_path: Directory to scan
            depth: Current recursion depth
            results: List to append found documents to
        """
        # Check depth limit
        if self.max_depth is not None and depth > self.max_depth:
            logger.debug(f"Max depth reached at {dir_path}")
            return

        try:
            for entry in dir_path.iterdir():
                # Skip ignored paths
                if self._should_ignore(entry):
                    logger.debug(f"Ignoring: {entry.name}")
                    continue

                # Handle directories
                if entry.is_dir(follow_symlinks=self.follow_symlinks):
                    self._scan_recursive(entry, depth + 1, results)

                # Handle files
                elif entry.is_file(follow_symlinks=self.follow_symlinks):
                    if self._is_supported_format(entry):
                        results.append(entry.resolve())

        except PermissionError:
            logger.warning(f"Permission denied: {dir_path}")
        except Exception as e:
            logger.error(f"Error scanning {dir_path}: {e}")

    def _should_ignore(self, path: Path) -> bool:
        """Check if path matches any ignore patterns.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored
        """
        name = path.name

        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True

        return False

    def _is_supported_format(self, path: Path) -> bool:
        """Check if file extension is supported.

        Args:
            path: File path to check

        Returns:
            True if file format is supported
        """
        return path.suffix.lower() in SUPPORTED_EXTENSIONS
