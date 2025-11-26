"""
Service Recovery.

REFINE-002: Recovery strategies for service failures.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from ragged.install.recovery.framework import (
    RecoveryAction,
    RecoveryResult,
    RecoveryStatus,
    RecoveryStrategy,
)


logger = logging.getLogger(__name__)


class RestartServiceStrategy(RecoveryStrategy):
    """Restart crashed services."""

    @property
    def name(self) -> str:
        return "restart_services"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.RESTART

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if any services need restarting."""
        # Check for Docker services
        ragged_home = context.get("ragged_home")
        if ragged_home:
            compose_file = ragged_home / "docker-compose.yml"
            if compose_file.exists():
                # Check if services are down
                try:
                    result = subprocess.run(
                        ["docker", "compose", "-f", str(compose_file), "ps", "-q"],
                        capture_output=True,
                        timeout=10,
                    )
                    # If no containers running but compose file exists
                    return result.returncode == 0 and not result.stdout.strip()
                except Exception:
                    pass

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Restart services."""
        ragged_home = context.get("ragged_home")
        compose_file = ragged_home / "docker-compose.yml"

        try:
            # Stop any existing
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "down"],
                capture_output=True,
                timeout=30,
            )

            # Start services
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Wait for health
                time.sleep(5)

                return RecoveryResult(
                    action=self.action,
                    status=RecoveryStatus.SUCCESS,
                    message="Services restarted successfully",
                )
            else:
                return RecoveryResult(
                    action=self.action,
                    status=RecoveryStatus.FAILED,
                    message=f"Failed to start services: {result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message="Service restart timed out",
            )
        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Service restart failed: {e}",
            )


class RepairDatabaseStrategy(RecoveryStrategy):
    """Repair corrupted database."""

    @property
    def name(self) -> str:
        return "repair_database"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.REPAIR

    @property
    def is_destructive(self) -> bool:
        return True  # May reset database

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if database needs repair."""
        ragged_home = context.get("ragged_home")
        if ragged_home:
            chromadb_path = ragged_home / "data" / "chromadb"
            if chromadb_path.exists():
                # Check for corruption indicators
                lock_file = chromadb_path / "chroma.sqlite3-journal"
                if lock_file.exists():
                    return True

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Repair database."""
        ragged_home = context.get("ragged_home")
        chromadb_path = ragged_home / "data" / "chromadb"

        try:
            import shutil
            from datetime import datetime

            # Backup current database
            backup_path = ragged_home / "data" / f"chromadb.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copytree(chromadb_path, backup_path)

            # Remove lock files
            for lock_file in chromadb_path.glob("*.journal"):
                lock_file.unlink()

            for lock_file in chromadb_path.glob("*.wal"):
                lock_file.unlink()

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message="Database repaired",
                details={"backup": str(backup_path)},
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Database repair failed: {e}",
            )


class ServiceRecovery:
    """Utility class for service recovery."""

    @staticmethod
    def restart_docker_service(
        service_name: str,
        compose_file: Path,
    ) -> bool:
        """Restart a specific Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "restart", service_name],
                capture_output=True,
                timeout=60,
                check=True,
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to restart {service_name}: {e}")
            return False

    @staticmethod
    def wait_for_health(
        url: str,
        timeout: int = 30,
        interval: float = 1.0,
    ) -> bool:
        """Wait for service to become healthy."""
        import httpx

        start = time.time()
        while time.time() - start < timeout:
            try:
                response = httpx.get(url, timeout=5.0)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(interval)

        return False


def restart_service(
    service_name: str,
    ragged_home: Path | None = None,
) -> bool:
    """
    Restart a specific service.

    Args:
        service_name: Name of service to restart.
        ragged_home: Path to ragged home.

    Returns:
        True if restart successful.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    compose_file = ragged_home / "docker-compose.yml"
    if compose_file.exists():
        return ServiceRecovery.restart_docker_service(service_name, compose_file)

    return False


def repair_corrupted_database(
    ragged_home: Path | None = None,
) -> bool:
    """
    Repair corrupted ChromaDB database.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        True if repair successful.
    """
    strategy = RepairDatabaseStrategy()
    context = {"ragged_home": ragged_home or Path.home() / ".ragged"}

    if strategy.can_recover(context):
        result = strategy.recover(context)
        return result.status == RecoveryStatus.SUCCESS

    return False
