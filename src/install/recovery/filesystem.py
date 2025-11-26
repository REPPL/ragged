"""
Filesystem Recovery.

REFINE-002: Recovery strategies for filesystem issues.
"""

import logging
import os
import shutil
import stat
from pathlib import Path
from typing import Any

from ragged.install.recovery.framework import (
    RecoveryAction,
    RecoveryResult,
    RecoveryStatus,
    RecoveryStrategy,
)


logger = logging.getLogger(__name__)


class FixPermissionsStrategy(RecoveryStrategy):
    """Fix file and directory permissions."""

    @property
    def name(self) -> str:
        return "fix_permissions"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.FIX_PERMISSIONS

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if permissions need fixing."""
        ragged_home = context.get("ragged_home")
        if ragged_home and ragged_home.exists():
            # Check if we don't have write access
            if not os.access(ragged_home, os.W_OK):
                return True

            # Check for root-owned files
            try:
                for item in ragged_home.rglob("*"):
                    if item.stat().st_uid == 0:
                        return True
            except Exception:
                pass

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Fix permissions."""
        ragged_home = context.get("ragged_home")
        fixed_count = 0

        try:
            # Get current user ID
            uid = os.getuid()
            gid = os.getgid()

            # Fix ownership
            for item in ragged_home.rglob("*"):
                try:
                    if item.stat().st_uid != uid:
                        os.chown(item, uid, gid)
                        fixed_count += 1
                except PermissionError:
                    # Need sudo for this
                    pass
                except OSError:
                    continue

            # Ensure directories are accessible
            for item in ragged_home.rglob("*"):
                if item.is_dir():
                    try:
                        current = item.stat().st_mode
                        item.chmod(current | stat.S_IRWXU)
                    except Exception:
                        continue

            # Restrict .env permissions
            env_path = ragged_home / ".env"
            if env_path.exists():
                env_path.chmod(0o600)

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message=f"Fixed permissions on {fixed_count} items",
                details={"fixed_count": fixed_count},
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Failed to fix permissions: {e}",
            )


class RecreateDirectoriesStrategy(RecoveryStrategy):
    """Recreate missing directories."""

    REQUIRED_DIRS = [
        "documents",
        "logs",
        "config",
        "data",
        "data/chromadb",
        "cache",
    ]

    @property
    def name(self) -> str:
        return "recreate_directories"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.RECREATE

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if directories need recreating."""
        ragged_home = context.get("ragged_home")
        if ragged_home:
            for dir_name in self.REQUIRED_DIRS:
                if not (ragged_home / dir_name).exists():
                    return True
        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Recreate directories."""
        ragged_home = context.get("ragged_home")
        created = []

        try:
            for dir_name in self.REQUIRED_DIRS:
                dir_path = ragged_home / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created.append(dir_name)

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message=f"Created {len(created)} directories",
                details={"created": created},
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Failed to create directories: {e}",
            )


class ClearCacheStrategy(RecoveryStrategy):
    """Clear corrupted cache files."""

    @property
    def name(self) -> str:
        return "clear_cache"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.CLEAR

    @property
    def is_destructive(self) -> bool:
        return True

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if cache should be cleared."""
        ragged_home = context.get("ragged_home")
        if ragged_home:
            cache_path = ragged_home / "cache"
            if cache_path.exists():
                # Check if cache is large or has corruption indicators
                try:
                    total_size = sum(f.stat().st_size for f in cache_path.rglob("*") if f.is_file())
                    if total_size > 1024**3:  # > 1GB
                        return True
                except Exception:
                    return True

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Clear cache."""
        ragged_home = context.get("ragged_home")
        cache_path = ragged_home / "cache"

        try:
            # Calculate size before clearing
            size_before = sum(f.stat().st_size for f in cache_path.rglob("*") if f.is_file())

            # Clear cache contents
            for item in cache_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message=f"Cleared {size_before / (1024**2):.1f}MB from cache",
                details={"bytes_cleared": size_before},
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Failed to clear cache: {e}",
            )


class FilesystemRecovery:
    """Utility class for filesystem recovery."""

    @staticmethod
    def ensure_directory(path: Path, permissions: int = 0o755) -> bool:
        """Ensure directory exists with correct permissions."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(permissions)
            return True
        except Exception as e:
            logger.warning(f"Failed to ensure directory {path}: {e}")
            return False

    @staticmethod
    def fix_ownership(path: Path, recursive: bool = False) -> int:
        """Fix ownership to current user."""
        fixed = 0
        uid = os.getuid()
        gid = os.getgid()

        items = [path]
        if recursive and path.is_dir():
            items.extend(path.rglob("*"))

        for item in items:
            try:
                if item.stat().st_uid != uid:
                    os.chown(item, uid, gid)
                    fixed += 1
            except Exception:
                continue

        return fixed


def fix_permissions(
    ragged_home: Path | None = None,
) -> bool:
    """
    Fix file permissions in ragged home.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        True if fix successful.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    strategy = FixPermissionsStrategy()
    context = {"ragged_home": ragged_home}

    if strategy.can_recover(context):
        result = strategy.recover(context)
        return result.status == RecoveryStatus.SUCCESS

    return True  # Nothing to fix


def recreate_directories(
    ragged_home: Path | None = None,
) -> bool:
    """
    Recreate missing directories.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        True if recreation successful.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    strategy = RecreateDirectoriesStrategy()
    context = {"ragged_home": ragged_home}

    result = strategy.recover(context)
    return result.status == RecoveryStatus.SUCCESS


def clear_cache(
    ragged_home: Path | None = None,
) -> bool:
    """
    Clear cache files.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        True if clear successful.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    strategy = ClearCacheStrategy()
    context = {"ragged_home": ragged_home}

    result = strategy.recover(context)
    return result.status == RecoveryStatus.SUCCESS
