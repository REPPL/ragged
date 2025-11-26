"""
Directory Structure Creation.

PREREQ-005: Creates the standard ragged directory structure with
proper permissions and documentation.
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Standard directory structure
DIRECTORY_STRUCTURE = {
    "documents": {
        "description": "Uploaded documents for indexing",
        "permissions": 0o755,
    },
    "chromadb": {
        "description": "ChromaDB vector database storage",
        "permissions": 0o755,
    },
    "cache": {
        "description": "Query cache and embeddings cache",
        "permissions": 0o755,
    },
    "logs": {
        "description": "Application logs",
        "permissions": 0o755,
    },
    "models": {
        "description": "Downloaded models (if local)",
        "permissions": 0o755,
    },
    "backups": {
        "description": "Database backups",
        "permissions": 0o755,
    },
}


def create_directory_structure(
    ragged_home: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Create the standard ragged directory structure.

    Args:
        ragged_home: Path to ragged home directory.
        dry_run: If True, only report what would be created.

    Returns:
        Dictionary with creation results.
    """
    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    result: dict[str, Any] = {
        "ragged_home": str(ragged_home),
        "created": [],
        "existing": [],
        "errors": [],
        "dry_run": dry_run,
    }

    logger.info(f"Creating directory structure at: {ragged_home}")

    # Create root directory
    if not ragged_home.exists():
        if not dry_run:
            try:
                ragged_home.mkdir(parents=True, mode=0o755)
                result["created"].append(str(ragged_home))
                logger.info(f"Created: {ragged_home}")
            except OSError as e:
                result["errors"].append(f"Failed to create {ragged_home}: {e}")
                logger.error(f"Failed to create {ragged_home}: {e}")
                return result
        else:
            result["created"].append(str(ragged_home))
    else:
        result["existing"].append(str(ragged_home))

    # Create subdirectories
    for dirname, info in DIRECTORY_STRUCTURE.items():
        dir_path = ragged_home / dirname
        permissions = info["permissions"]

        if not dir_path.exists():
            if not dry_run:
                try:
                    dir_path.mkdir(mode=permissions)
                    result["created"].append(str(dir_path))
                    logger.info(f"Created: {dir_path}")
                except OSError as e:
                    result["errors"].append(f"Failed to create {dir_path}: {e}")
                    logger.error(f"Failed to create {dir_path}: {e}")
            else:
                result["created"].append(str(dir_path))
        else:
            result["existing"].append(str(dir_path))
            # Ensure correct permissions on existing directories
            if not dry_run:
                try:
                    dir_path.chmod(permissions)
                except OSError:
                    pass

    # Create README in ragged home
    readme_path = ragged_home / "README.md"
    if not readme_path.exists() and not dry_run:
        _create_readme(readme_path)
        result["created"].append(str(readme_path))

    # Create .gitignore
    gitignore_path = ragged_home / ".gitignore"
    if not gitignore_path.exists() and not dry_run:
        _create_gitignore(gitignore_path)
        result["created"].append(str(gitignore_path))

    return result


def _create_readme(path: Path) -> None:
    """Create README explaining directory structure."""
    content = """# ragged Data Directory

This directory contains all ragged data and configuration.

## Directory Structure

```
~/.ragged/
├── config.yaml          # Main configuration file
├── .env                 # Environment variables and secrets
├── documents/           # Uploaded documents for indexing
├── chromadb/            # Vector database storage
├── cache/               # Query and embeddings cache
├── logs/                # Application logs
├── models/              # Downloaded models (if using local)
└── backups/             # Database backups
```

## Files

- **config.yaml**: Main configuration. Edit to customise ragged behaviour.
- **.env**: Secrets and environment variables. Never commit to version control.

## Data Safety

- **documents/**: Your uploaded documents. Back up regularly.
- **chromadb/**: Vector database. Can be regenerated from documents.
- **backups/**: Automatic backups stored here.

## Uninstalling

To uninstall ragged:
```bash
ragged uninstall
```

This will:
1. Stop all services
2. Remove Docker containers
3. Optionally delete this directory

## More Information

- Documentation: https://ragged.ai/docs
- Source: https://github.com/ragged/ragged
- Issues: https://github.com/ragged/ragged/issues
"""

    with open(path, "w") as f:
        f.write(content)

    logger.info(f"Created README: {path}")


def _create_gitignore(path: Path) -> None:
    """Create .gitignore for sensitive directories."""
    content = """# ragged data directory .gitignore
# This prevents accidental commits of sensitive data

# Environment files with secrets
.env
.env.local
.env.*.local

# Database files
chromadb/

# Logs
logs/
*.log

# Cache
cache/

# Backups
backups/

# Uploaded documents (may contain sensitive content)
documents/

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*.swo
*~
"""

    with open(path, "w") as f:
        f.write(content)

    logger.info(f"Created .gitignore: {path}")


def ensure_directory_permissions(ragged_home: Path) -> list[str]:
    """
    Ensure correct permissions on all directories.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        List of any permission errors.
    """
    errors = []

    # Root directory
    try:
        ragged_home.chmod(0o755)
    except OSError as e:
        errors.append(f"Could not set permissions on {ragged_home}: {e}")

    # .env file should be restrictive
    env_path = ragged_home / ".env"
    if env_path.exists():
        try:
            env_path.chmod(0o600)
        except OSError as e:
            errors.append(f"Could not set permissions on {env_path}: {e}")

    # Subdirectories
    for dirname, info in DIRECTORY_STRUCTURE.items():
        dir_path = ragged_home / dirname
        if dir_path.exists():
            try:
                dir_path.chmod(info["permissions"])
            except OSError as e:
                errors.append(f"Could not set permissions on {dir_path}: {e}")

    return errors


def get_directory_sizes(ragged_home: Path) -> dict[str, int]:
    """
    Get sizes of ragged directories.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        Dictionary mapping directory names to sizes in bytes.
    """
    sizes: dict[str, int] = {}

    for dirname in DIRECTORY_STRUCTURE:
        dir_path = ragged_home / dirname
        if dir_path.exists():
            total = 0
            try:
                for entry in dir_path.rglob("*"):
                    if entry.is_file():
                        total += entry.stat().st_size
            except (OSError, PermissionError):
                pass
            sizes[dirname] = total

    return sizes


def format_size(size_bytes: int) -> str:
    """Format size in human-readable form."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
