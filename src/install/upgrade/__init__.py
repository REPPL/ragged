"""
Upgrade System.

REFINE-004: Upgrade and migration paths for ragged versions.
"""

from ragged.install.upgrade.upgrade import (
    Upgrader,
    UpgradeStrategy,
    UpgradeResult,
    upgrade_ragged,
    check_for_updates,
)
from ragged.install.upgrade.migrations import (
    Migration,
    MigrationRunner,
    run_migrations,
)


__all__ = [
    # Upgrade
    "Upgrader",
    "UpgradeStrategy",
    "UpgradeResult",
    "upgrade_ragged",
    "check_for_updates",
    # Migrations
    "Migration",
    "MigrationRunner",
    "run_migrations",
]
