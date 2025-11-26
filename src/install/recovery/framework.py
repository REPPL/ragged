"""
Recovery Framework.

REFINE-002: Core framework for automated recovery including
pipeline, strategies, and rollback capability.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import logging
import shutil
import time


logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Types of recovery actions."""

    RESTART = "restart"
    REPAIR = "repair"
    RECREATE = "recreate"
    CLEAR = "clear"
    FIX_PERMISSIONS = "fix_permissions"
    REGENERATE = "regenerate"
    KILL_PROCESS = "kill_process"
    DOWNLOAD = "download"


class RecoveryStatus(Enum):
    """Status of recovery attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"
    NEEDS_CONFIRMATION = "needs_confirmation"


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""

    action: RecoveryAction
    status: RecoveryStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    rollback_performed: bool = False
    requires_reboot: bool = False
    requires_logout: bool = False


class RecoveryStrategy(ABC):
    """Abstract base class for recovery strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the recovery strategy."""
        ...

    @property
    @abstractmethod
    def action(self) -> RecoveryAction:
        """Type of recovery action."""
        ...

    @property
    def is_destructive(self) -> bool:
        """Whether this action can cause data loss."""
        return False

    @property
    def requires_confirmation(self) -> bool:
        """Whether user confirmation is needed."""
        return self.is_destructive

    @abstractmethod
    def can_recover(self, context: dict[str, Any]) -> bool:
        """
        Check if this strategy can handle the issue.

        Args:
            context: Recovery context.

        Returns:
            True if strategy is applicable.
        """
        ...

    @abstractmethod
    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """
        Attempt recovery.

        Args:
            context: Recovery context.

        Returns:
            Recovery result.
        """
        ...

    def rollback(self, context: dict[str, Any]) -> bool:
        """
        Rollback recovery attempt.

        Args:
            context: Recovery context.

        Returns:
            True if rollback successful.
        """
        return False


class RecoveryPipeline:
    """
    Recovery pipeline for automated issue resolution.

    Manages recovery strategies, execution, and rollback.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise recovery pipeline.

        Args:
            ragged_home: Path to ragged home directory.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self._strategies: list[RecoveryStrategy] = []
        self._results: list[RecoveryResult] = []
        self._backups: dict[str, Path] = {}
        self._callbacks: list[Callable[[RecoveryResult], None]] = []

    def register(self, strategy: RecoveryStrategy) -> None:
        """Register a recovery strategy."""
        self._strategies.append(strategy)

    def add_callback(self, callback: Callable[[RecoveryResult], None]) -> None:
        """Add a result callback."""
        self._callbacks.append(callback)

    def run(
        self,
        context: dict[str, Any] | None = None,
        auto_fix: bool = False,
        confirm_callback: Callable[[str], bool] | None = None,
    ) -> list[RecoveryResult]:
        """
        Run recovery strategies.

        Args:
            context: Recovery context.
            auto_fix: Auto-apply non-destructive fixes.
            confirm_callback: Callback for user confirmation.

        Returns:
            List of recovery results.
        """
        self._results = []

        if context is None:
            context = self._build_context()

        # Create backup before recovery
        self._create_backup()

        for strategy in self._strategies:
            if not strategy.can_recover(context):
                continue

            # Check if confirmation needed
            if strategy.requires_confirmation:
                if not auto_fix:
                    if confirm_callback is None:
                        self._results.append(RecoveryResult(
                            action=strategy.action,
                            status=RecoveryStatus.NEEDS_CONFIRMATION,
                            message=f"Recovery requires confirmation: {strategy.name}",
                        ))
                        continue

                    if not confirm_callback(f"Apply {strategy.name}?"):
                        self._results.append(RecoveryResult(
                            action=strategy.action,
                            status=RecoveryStatus.SKIPPED,
                            message=f"Skipped by user: {strategy.name}",
                        ))
                        continue

            # Run recovery
            start = time.perf_counter()
            try:
                result = strategy.recover(context)
                result.duration_ms = (time.perf_counter() - start) * 1000

                # Rollback if failed and strategy supports it
                if result.status == RecoveryStatus.FAILED:
                    if strategy.rollback(context):
                        result.rollback_performed = True
                        result.status = RecoveryStatus.ROLLED_BACK

                self._results.append(result)
                self._notify(result)

            except Exception as e:
                logger.exception(f"Recovery strategy {strategy.name} failed")
                result = RecoveryResult(
                    action=strategy.action,
                    status=RecoveryStatus.FAILED,
                    message=f"Exception: {e}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )
                self._results.append(result)
                self._notify(result)

        return self._results

    def _build_context(self) -> dict[str, Any]:
        """Build recovery context."""
        import platform

        return {
            "ragged_home": self.ragged_home,
            "platform": platform.system(),
            "backups": self._backups,
        }

    def _create_backup(self) -> None:
        """Create backup of critical files before recovery."""
        backup_dir = self.ragged_home / ".recovery_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup config
        config_path = self.ragged_home / "config.yaml"
        if config_path.exists():
            backup_path = backup_dir / f"config.yaml.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(config_path, backup_path)
            self._backups["config"] = backup_path

        # Backup .env
        env_path = self.ragged_home / ".env"
        if env_path.exists():
            backup_path = backup_dir / f".env.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(env_path, backup_path)
            self._backups["env"] = backup_path

    def _notify(self, result: RecoveryResult) -> None:
        """Notify callbacks of result."""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.warning(f"Callback error: {e}")

    @property
    def results(self) -> list[RecoveryResult]:
        """Get all results."""
        return self._results

    @property
    def successful_recoveries(self) -> list[RecoveryResult]:
        """Get successful recoveries."""
        return [r for r in self._results if r.status == RecoveryStatus.SUCCESS]

    @property
    def failed_recoveries(self) -> list[RecoveryResult]:
        """Get failed recoveries."""
        return [r for r in self._results if r.status == RecoveryStatus.FAILED]

    @property
    def all_succeeded(self) -> bool:
        """Check if all recoveries succeeded."""
        return len(self.failed_recoveries) == 0


def run_recovery(
    ragged_home: Path | None = None,
    auto_fix: bool = False,
    confirm_callback: Callable[[str], bool] | None = None,
) -> list[RecoveryResult]:
    """
    Run all recovery strategies.

    Args:
        ragged_home: Path to ragged home directory.
        auto_fix: Auto-apply non-destructive fixes.
        confirm_callback: Callback for user confirmation.

    Returns:
        List of recovery results.
    """
    from ragged.install.recovery.services import (
        RestartServiceStrategy,
        RepairDatabaseStrategy,
    )
    from ragged.install.recovery.filesystem import (
        FixPermissionsStrategy,
        RecreateDirectoriesStrategy,
        ClearCacheStrategy,
    )
    from ragged.install.recovery.configuration import (
        RepairConfigStrategy,
        RegenerateSecretsStrategy,
    )

    pipeline = RecoveryPipeline(ragged_home)

    # Register all strategies
    pipeline.register(FixPermissionsStrategy())
    pipeline.register(RecreateDirectoriesStrategy())
    pipeline.register(ClearCacheStrategy())
    pipeline.register(RepairConfigStrategy())
    pipeline.register(RegenerateSecretsStrategy())
    pipeline.register(RestartServiceStrategy())
    pipeline.register(RepairDatabaseStrategy())

    return pipeline.run(auto_fix=auto_fix, confirm_callback=confirm_callback)
