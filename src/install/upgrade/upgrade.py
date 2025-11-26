"""
Upgrade Logic.

REFINE-004: Core upgrade functionality for ragged versions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import logging
import shutil
import subprocess


logger = logging.getLogger(__name__)


class UpgradeStrategy(Enum):
    """Upgrade strategies."""

    IN_PLACE = "in_place"
    CLEAN_INSTALL = "clean_install"
    SIDE_BY_SIDE = "side_by_side"


class UpgradeStatus(Enum):
    """Status of upgrade."""

    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


@dataclass
class VersionInfo:
    """Version information."""

    version: str
    release_date: str | None = None
    release_notes: str | None = None
    download_url: str | None = None


@dataclass
class UpgradeResult:
    """Result of upgrade attempt."""

    status: UpgradeStatus
    from_version: str
    to_version: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    migrations_applied: list[str] = field(default_factory=list)
    backup_path: Path | None = None
    requires_restart: bool = False


class Upgrader:
    """
    Upgrade manager for ragged.

    Handles version detection, backup, upgrade, and rollback.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise upgrader.

        Args:
            ragged_home: Path to ragged home.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )

    def get_current_version(self) -> str:
        """Get currently installed version."""
        try:
            result = subprocess.run(
                ["pip", "show", "ragged"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":")[1].strip()

        except Exception as e:
            logger.warning(f"Failed to get current version: {e}")

        return "unknown"

    def check_for_updates(self) -> VersionInfo | None:
        """Check for available updates."""
        try:
            result = subprocess.run(
                ["pip", "index", "versions", "ragged"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Parse available versions
                # Format: ragged (X.Y.Z)
                import re
                match = re.search(r"ragged \(([^)]+)\)", result.stdout)
                if match:
                    latest = match.group(1)
                    current = self.get_current_version()

                    if self._compare_versions(latest, current) > 0:
                        return VersionInfo(version=latest)

        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")

        return None

    def upgrade(
        self,
        target_version: str | None = None,
        strategy: UpgradeStrategy = UpgradeStrategy.IN_PLACE,
        dry_run: bool = False,
    ) -> UpgradeResult:
        """
        Upgrade ragged to specified version.

        Args:
            target_version: Target version (latest if None).
            strategy: Upgrade strategy to use.
            dry_run: If True, only show what would be done.

        Returns:
            Upgrade result.
        """
        current = self.get_current_version()

        # Determine target version
        if target_version is None:
            update_info = self.check_for_updates()
            if update_info:
                target_version = update_info.version
            else:
                return UpgradeResult(
                    status=UpgradeStatus.CANCELLED,
                    from_version=current,
                    to_version=current,
                    message="Already at latest version",
                )

        # Check if upgrade needed
        if self._compare_versions(target_version, current) <= 0:
            return UpgradeResult(
                status=UpgradeStatus.CANCELLED,
                from_version=current,
                to_version=target_version,
                message=f"Already at version {current} (target: {target_version})",
            )

        if dry_run:
            return UpgradeResult(
                status=UpgradeStatus.SUCCESS,
                from_version=current,
                to_version=target_version,
                message=f"[DRY RUN] Would upgrade from {current} to {target_version}",
            )

        # Create backup
        backup_path = self._create_backup()

        try:
            # Pre-upgrade checks
            if not self._pre_upgrade_checks():
                return UpgradeResult(
                    status=UpgradeStatus.FAILED,
                    from_version=current,
                    to_version=target_version,
                    message="Pre-upgrade checks failed",
                    backup_path=backup_path,
                )

            # Perform upgrade
            if strategy == UpgradeStrategy.IN_PLACE:
                result = self._upgrade_in_place(target_version)
            elif strategy == UpgradeStrategy.CLEAN_INSTALL:
                result = self._upgrade_clean(target_version)
            else:
                return UpgradeResult(
                    status=UpgradeStatus.FAILED,
                    from_version=current,
                    to_version=target_version,
                    message=f"Unsupported strategy: {strategy}",
                    backup_path=backup_path,
                )

            if not result:
                raise RuntimeError("Upgrade failed")

            # Run migrations
            migrations = self._run_migrations(current, target_version)

            # Verify upgrade
            new_version = self.get_current_version()
            if new_version != target_version:
                raise RuntimeError(f"Version mismatch: expected {target_version}, got {new_version}")

            return UpgradeResult(
                status=UpgradeStatus.SUCCESS,
                from_version=current,
                to_version=target_version,
                message=f"Successfully upgraded from {current} to {target_version}",
                migrations_applied=migrations,
                backup_path=backup_path,
                requires_restart=True,
            )

        except Exception as e:
            logger.exception("Upgrade failed")

            # Rollback
            if backup_path and backup_path.exists():
                self._rollback(backup_path)

                return UpgradeResult(
                    status=UpgradeStatus.ROLLED_BACK,
                    from_version=current,
                    to_version=target_version,
                    message=f"Upgrade failed, rolled back: {e}",
                    backup_path=backup_path,
                )

            return UpgradeResult(
                status=UpgradeStatus.FAILED,
                from_version=current,
                to_version=target_version,
                message=f"Upgrade failed: {e}",
            )

    def _create_backup(self) -> Path:
        """Create backup before upgrade."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.ragged_home.parent / f".ragged_backup_{timestamp}"

        logger.info(f"Creating backup at {backup_path}")
        shutil.copytree(self.ragged_home, backup_path)

        return backup_path

    def _pre_upgrade_checks(self) -> bool:
        """Run pre-upgrade checks."""
        # Check disk space
        import shutil as sh
        usage = sh.disk_usage(self.ragged_home)
        free_gb = usage.free / (1024**3)

        if free_gb < 1:
            logger.error("Insufficient disk space for upgrade")
            return False

        return True

    def _upgrade_in_place(self, version: str) -> bool:
        """Upgrade using pip."""
        try:
            result = subprocess.run(
                ["pip", "install", "--upgrade", f"ragged=={version}"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"pip upgrade failed: {e}")
            return False

    def _upgrade_clean(self, version: str) -> bool:
        """Clean install upgrade."""
        try:
            # Uninstall current
            subprocess.run(
                ["pip", "uninstall", "-y", "ragged"],
                capture_output=True,
                timeout=60,
            )

            # Install new version
            result = subprocess.run(
                ["pip", "install", f"ragged=={version}"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Clean upgrade failed: {e}")
            return False

    def _run_migrations(self, from_version: str, to_version: str) -> list[str]:
        """Run database/config migrations."""
        from ragged.install.upgrade.migrations import run_migrations

        return run_migrations(
            self.ragged_home,
            from_version,
            to_version,
        )

    def _rollback(self, backup_path: Path) -> None:
        """Rollback to backup."""
        logger.info(f"Rolling back from {backup_path}")

        if self.ragged_home.exists():
            shutil.rmtree(self.ragged_home)

        shutil.copytree(backup_path, self.ragged_home)

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare version strings."""
        try:
            from packaging import version
            return (version.parse(v1) > version.parse(v2)) - (version.parse(v1) < version.parse(v2))
        except ImportError:
            # Simple comparison
            p1 = [int(x) for x in v1.split(".")]
            p2 = [int(x) for x in v2.split(".")]
            return (p1 > p2) - (p1 < p2)


def upgrade_ragged(
    target_version: str | None = None,
    strategy: UpgradeStrategy = UpgradeStrategy.IN_PLACE,
    dry_run: bool = False,
    ragged_home: Path | None = None,
) -> UpgradeResult:
    """
    Upgrade ragged to specified version.

    Args:
        target_version: Target version (latest if None).
        strategy: Upgrade strategy.
        dry_run: Only show what would be done.
        ragged_home: Path to ragged home.

    Returns:
        Upgrade result.
    """
    upgrader = Upgrader(ragged_home)
    return upgrader.upgrade(target_version, strategy, dry_run)


def check_for_updates(
    ragged_home: Path | None = None,
) -> VersionInfo | None:
    """
    Check for available updates.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        Version info if update available.
    """
    upgrader = Upgrader(ragged_home)
    return upgrader.check_for_updates()
