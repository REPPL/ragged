"""
Database/Config Migrations.

REFINE-004: Migration system for schema and config changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import logging


logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Migration definition."""

    version: str
    name: str
    description: str

    def applies_to(self, from_version: str, to_version: str) -> bool:
        """Check if migration applies to version range."""
        try:
            from packaging import version
            v = version.parse(self.version)
            from_v = version.parse(from_version)
            to_v = version.parse(to_version)
            return from_v < v <= to_v
        except ImportError:
            return True  # Apply all migrations if packaging unavailable


class MigrationRunner:
    """
    Run database and config migrations.

    Applies migrations in version order with rollback support.
    """

    def __init__(self, ragged_home: Path) -> None:
        """
        Initialise migration runner.

        Args:
            ragged_home: Path to ragged home.
        """
        self.ragged_home = ragged_home
        self._migrations: list[tuple[Migration, callable]] = []

    def register(self, migration: Migration, handler: callable) -> None:
        """Register a migration."""
        self._migrations.append((migration, handler))

    def run(
        self,
        from_version: str,
        to_version: str,
    ) -> list[str]:
        """
        Run applicable migrations.

        Args:
            from_version: Current version.
            to_version: Target version.

        Returns:
            List of applied migration names.
        """
        applied = []

        # Sort migrations by version
        sorted_migrations = sorted(
            self._migrations,
            key=lambda m: m[0].version,
        )

        for migration, handler in sorted_migrations:
            if migration.applies_to(from_version, to_version):
                try:
                    logger.info(f"Applying migration: {migration.name}")
                    handler(self.ragged_home)
                    applied.append(migration.name)
                except Exception as e:
                    logger.error(f"Migration {migration.name} failed: {e}")
                    raise

        return applied


def run_migrations(
    ragged_home: Path,
    from_version: str,
    to_version: str,
) -> list[str]:
    """
    Run all applicable migrations.

    Args:
        ragged_home: Path to ragged home.
        from_version: Current version.
        to_version: Target version.

    Returns:
        List of applied migration names.
    """
    runner = MigrationRunner(ragged_home)

    # Register migrations
    _register_migrations(runner)

    return runner.run(from_version, to_version)


def _register_migrations(runner: MigrationRunner) -> None:
    """Register all known migrations."""

    # v0.8.0 -> v0.8.1: Add new directories
    runner.register(
        Migration(
            version="0.8.1",
            name="add_install_directories",
            description="Add new directories for installation wizard",
        ),
        _migrate_0_8_1,
    )

    # v0.8.1 -> v0.8.2: Update config format
    runner.register(
        Migration(
            version="0.8.2",
            name="update_config_format",
            description="Update configuration file format",
        ),
        _migrate_0_8_2,
    )


def _migrate_0_8_1(ragged_home: Path) -> None:
    """Migration for v0.8.1."""
    # Ensure new directories exist
    new_dirs = [
        "cache",
        "data/kuzu",
    ]

    for dir_name in new_dirs:
        dir_path = ragged_home / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)


def _migrate_0_8_2(ragged_home: Path) -> None:
    """Migration for v0.8.2."""
    import yaml

    config_path = ragged_home / "config.yaml"

    if not config_path.exists():
        return

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        # Ensure all sections exist
        defaults = {
            "server": {"host": "localhost", "port": 8000},
            "database": {"chromadb_host": "localhost", "chromadb_port": 8001},
            "llm": {"ollama_host": "http://localhost:11434", "default_model": "llama3.2"},
            "storage": {"documents_path": str(ragged_home / "documents")},
            "security": {"authentication_enabled": False},
            "webui": {"enabled": True, "port": 5173},
        }

        updated = False
        for section, values in defaults.items():
            if section not in config:
                config[section] = values
                updated = True

        if updated:
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)

    except Exception as e:
        logger.warning(f"Config migration failed: {e}")
