"""
Path validation for security (v0.5.7 HIGH-5).

Prevents path traversal attacks by validating user-provided paths:
- Blocks relative paths with .. (parent directory)
- Blocks absolute paths outside allowed directories
- Sanitizes symbolic links
- Validates path components

Security: Prevents malicious paths from accessing sensitive files.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class PathTraversalError(ValueError):
    """Raised when path traversal attack detected.

    v0.5.7 HIGH-5: CLI input validation
    Used to reject malicious paths before file operations.
    """

    pass


class PathValidator:
    """
    Validate file paths for security.

    v0.5.7 HIGH-5: Prevents path traversal attacks

    Checks:
    - Blocks paths with .. (parent directory traversal)
    - Blocks paths starting with / (absolute paths)
    - Blocks paths with null bytes
    - Validates resolved path is within allowed base directory

    Example:
        >>> validator = PathValidator(allowed_base=Path.home() / ".ragged")
        >>> validator.validate(Path("cache/models"))  # OK
        >>> validator.validate(Path("../etc/passwd"))  # Raises PathTraversalError
    """

    def __init__(
        self,
        allowed_base: Path | None = None,
        allow_absolute: bool = False,
        allow_symlinks: bool = False,
    ) -> None:
        """
        Initialise path validator with security rules.

        Args:
            allowed_base: Base directory that paths must be within (None = no restriction)
            allow_absolute: Allow absolute paths (default: False for security)
            allow_symlinks: Allow symbolic links (default: False for security)

        Security (v0.5.7 HIGH-5):
        - allowed_base enforces sandboxing
        - allow_absolute=False prevents /etc/passwd attacks
        - allow_symlinks=False prevents symlink attacks

        Example:
            >>> # Strict validation (recommended for user input)
            >>> validator = PathValidator(
            ...     allowed_base=Path.home() / ".ragged",
            ...     allow_absolute=False,
            ...     allow_symlinks=False
            ... )
            >>> # Relaxed validation (for trusted paths)
            >>> validator = PathValidator(allow_absolute=True, allow_symlinks=True)
        """
        self.allowed_base = allowed_base.resolve() if allowed_base else None
        self.allow_absolute = allow_absolute
        self.allow_symlinks = allow_symlinks

        logger.debug(
            f"PathValidator initialised: "
            f"base={self.allowed_base}, "
            f"allow_absolute={allow_absolute}, "
            f"allow_symlinks={allow_symlinks}"
        )

    def validate(self, path: Path | str, create_if_missing: bool = False) -> Path:
        """
        Validate path for security.

        Args:
            path: Path to validate (string or Path object)
            create_if_missing: Create directory if it doesn't exist (default: False)

        Returns:
            Validated Path object (resolved and sanitized)

        Raises:
            PathTraversalError: If path fails security checks
            TypeError: If path is not Path or str

        Security (v0.5.7 HIGH-5):
        - Blocks .. parent directory traversal
        - Blocks null bytes
        - Enforces allowed_base sandboxing
        - Checks for symlink attacks

        Example:
            >>> validator = PathValidator(allowed_base=Path("/safe/dir"))
            >>> safe_path = validator.validate("cache/models")
            >>> # Returns: /safe/dir/cache/models
            >>> validator.validate("../etc/passwd")
            PathTraversalError: Path traversal detected
        """
        # Type check
        if not isinstance(path, (Path, str)):
            raise TypeError(f"Expected Path or str, got {type(path)}")

        # Convert to Path
        if isinstance(path, str):
            path = Path(path)

        # Security check 1: Block null bytes
        path_str = str(path)
        if "\x00" in path_str:
            raise PathTraversalError(
                "Null byte detected in path (security violation)"
            )

        # Security check 2: Block parent directory traversal in path components
        for part in path.parts:
            if part == "..":
                raise PathTraversalError(
                    f"Parent directory traversal detected: {path}. "
                    f"Use absolute paths or paths relative to allowed base."
                )

        # Security check 3: Block absolute paths (if not allowed)
        if not self.allow_absolute and path.is_absolute():
            raise PathTraversalError(
                f"Absolute path not allowed: {path}. "
                f"Use relative paths within allowed base directory."
            )

        # Resolve path (follows symlinks and makes absolute)
        if self.allowed_base:
            # Make relative to allowed_base
            if not path.is_absolute():
                resolved_path = (self.allowed_base / path).resolve()
            else:
                resolved_path = path.resolve()
        else:
            resolved_path = path.resolve()

        # Security check 4: Verify within allowed base
        if self.allowed_base:
            try:
                # Check if resolved path is within allowed_base
                resolved_path.relative_to(self.allowed_base)
            except ValueError:
                raise PathTraversalError(
                    f"Path {path} resolves outside allowed base directory. "
                    f"Resolved: {resolved_path}, Allowed base: {self.allowed_base}"
                )

        # Security check 5: Block symlinks (if not allowed)
        if not self.allow_symlinks and resolved_path.exists():
            # Check if any component in the path is a symlink
            current = resolved_path
            while current != current.parent:
                if current.is_symlink():
                    raise PathTraversalError(
                        f"Symbolic link detected in path: {path} -> {resolved_path}. "
                        f"Symlinks not allowed for security."
                    )
                current = current.parent

        # Create directory if requested and doesn't exist
        if create_if_missing and not resolved_path.exists():
            try:
                resolved_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {resolved_path}")
            except (PermissionError, OSError) as e:
                raise PathTraversalError(
                    f"Cannot create directory {resolved_path}: {e}"
                ) from e

        logger.debug(f"Path validated: {path} -> {resolved_path}")
        return resolved_path

    def validate_batch(
        self, paths: list[Path | str], create_if_missing: bool = False
    ) -> list[Path]:
        """
        Validate multiple paths.

        Args:
            paths: List of paths to validate
            create_if_missing: Create directories if they don't exist

        Returns:
            List of validated Path objects

        Raises:
            PathTraversalError: If any path fails validation

        Example:
            >>> validator = PathValidator(allowed_base=Path("/safe"))
            >>> safe_paths = validator.validate_batch([
            ...     "cache/models",
            ...     "data/uploads",
            ...     "logs"
            ... ])
        """
        validated = []
        for i, path in enumerate(paths):
            try:
                validated_path = self.validate(path, create_if_missing)
                validated.append(validated_path)
            except PathTraversalError as e:
                raise PathTraversalError(
                    f"Path {i} in batch failed validation: {e}"
                ) from e

        return validated


# Convenience functions
def validate_path(
    path: Path | str,
    allowed_base: Path | None = None,
    allow_absolute: bool = False,
    create_if_missing: bool = False,
) -> Path:
    """
    Validate path for security (convenience function).

    v0.5.7 HIGH-5: CLI input validation

    Args:
        path: Path to validate
        allowed_base: Base directory for sandboxing
        allow_absolute: Allow absolute paths
        create_if_missing: Create directory if missing

    Returns:
        Validated Path object

    Raises:
        PathTraversalError: If path fails security checks

    Example:
        >>> from ragged.validation import validate_path
        >>> safe_path = validate_path(
        ...     "cache/models",
        ...     allowed_base=Path.home() / ".ragged"
        ... )
    """
    validator = PathValidator(
        allowed_base=allowed_base,
        allow_absolute=allow_absolute,
        allow_symlinks=False,
    )
    return validator.validate(path, create_if_missing)


def validate_cli_path(path: str | None, create_if_missing: bool = False) -> Path | None:
    """
    Validate CLI path argument with default security settings.

    v0.5.7 HIGH-5: CLI input validation

    Designed for CLI arguments like --cache-dir, --output-dir, etc.
    Uses secure defaults: no absolute paths, no symlinks.

    Args:
        path: CLI path argument (None if not provided)
        create_if_missing: Create directory if missing

    Returns:
        Validated Path or None if input was None

    Raises:
        PathTraversalError: If path fails security checks

    Security:
    - Blocks parent directory traversal (..)
    - Blocks absolute paths (use config for absolute paths)
    - Blocks symbolic links
    - Paths are relative to current working directory

    Example:
        >>> # In CLI command:
        >>> @click.option("--cache-dir")
        >>> def download(cache_dir: str | None):
        ...     safe_cache_dir = validate_cli_path(cache_dir, create_if_missing=True)
        ...     if safe_cache_dir:
        ...         print(f"Using cache: {safe_cache_dir}")
    """
    if path is None:
        return None

    # Use current working directory as allowed base
    cwd = Path.cwd()

    validator = PathValidator(
        allowed_base=cwd,
        allow_absolute=False,  # Force relative paths for security
        allow_symlinks=False,  # Block symlinks for security
    )

    return validator.validate(path, create_if_missing)
