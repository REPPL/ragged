"""
Health Check.

WIZARD-005: Comprehensive health checks for ragged installation.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import logging
import subprocess


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fix_suggestion: str | None = None
    duration_ms: float = 0.0


@dataclass
class HealthCheck:
    """
    Health check executor.

    Runs various health checks on the ragged installation.
    """

    ragged_home: Path
    checks: list[Callable[["HealthCheck"], HealthCheckResult]] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        """Initialise default checks if not provided."""
        if not self.checks:
            self.checks = [
                self._check_directories,
                self._check_config,
                self._check_docker,
                self._check_ollama,
                self._check_chromadb,
                self._check_permissions,
                self._check_disk_space,
            ]

    def run_all(self) -> list[HealthCheckResult]:
        """Run all health checks."""
        import time

        results = []

        for check in self.checks:
            start = time.perf_counter()
            try:
                result = check(self)
                result.duration_ms = (time.perf_counter() - start) * 1000
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                result = HealthCheckResult(
                    name=check.__name__.replace("_check_", ""),
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {e}",
                )
            results.append(result)

        return results

    def overall_status(self, results: list[HealthCheckResult]) -> HealthStatus:
        """Determine overall health status."""
        statuses = [r.status for r in results]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def _check_directories(self, _: "HealthCheck") -> HealthCheckResult:
        """Check required directories exist."""
        required_dirs = [
            "documents",
            "logs",
            "config",
            "data",
        ]

        missing = []
        for dir_name in required_dirs:
            dir_path = self.ragged_home / dir_name
            if not dir_path.exists():
                missing.append(dir_name)

        if missing:
            return HealthCheckResult(
                name="directories",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing directories: {', '.join(missing)}",
                details={"missing": missing},
                fix_suggestion="Run 'ragged install' to create directories",
            )

        return HealthCheckResult(
            name="directories",
            status=HealthStatus.HEALTHY,
            message="All required directories exist",
            details={"checked": required_dirs},
        )

    def _check_config(self, _: "HealthCheck") -> HealthCheckResult:
        """Check configuration file exists and is valid."""
        config_path = self.ragged_home / "config.yaml"

        if not config_path.exists():
            return HealthCheckResult(
                name="config",
                status=HealthStatus.UNHEALTHY,
                message="Configuration file not found",
                fix_suggestion="Run 'ragged config --init' to create configuration",
            )

        try:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            if not config:
                return HealthCheckResult(
                    name="config",
                    status=HealthStatus.DEGRADED,
                    message="Configuration file is empty",
                    fix_suggestion="Run 'ragged config --init' to regenerate",
                )

            return HealthCheckResult(
                name="config",
                status=HealthStatus.HEALTHY,
                message="Configuration file is valid",
                details={"sections": list(config.keys())},
            )

        except yaml.YAMLError as e:
            return HealthCheckResult(
                name="config",
                status=HealthStatus.UNHEALTHY,
                message=f"Invalid YAML: {e}",
                fix_suggestion="Check configuration syntax or regenerate",
            )

    def _check_docker(self, _: "HealthCheck") -> HealthCheckResult:
        """Check Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return HealthCheckResult(
                    name="docker",
                    status=HealthStatus.DEGRADED,
                    message="Docker daemon not running",
                    fix_suggestion="Start Docker Desktop or Docker daemon",
                )

            return HealthCheckResult(
                name="docker",
                status=HealthStatus.HEALTHY,
                message="Docker is running",
            )

        except FileNotFoundError:
            return HealthCheckResult(
                name="docker",
                status=HealthStatus.DEGRADED,
                message="Docker not installed",
                details={"optional": True},
                fix_suggestion="Install Docker for containerised services",
            )
        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name="docker",
                status=HealthStatus.DEGRADED,
                message="Docker check timed out",
                fix_suggestion="Docker may be unresponsive - try restarting",
            )

    def _check_ollama(self, _: "HealthCheck") -> HealthCheckResult:
        """Check Ollama is available and running."""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:11434/api/tags",
                timeout=5.0,
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "unknown") for m in models]

                return HealthCheckResult(
                    name="ollama",
                    status=HealthStatus.HEALTHY,
                    message=f"Ollama running with {len(models)} models",
                    details={"models": model_names},
                )

            return HealthCheckResult(
                name="ollama",
                status=HealthStatus.DEGRADED,
                message=f"Ollama returned status {response.status_code}",
            )

        except httpx.ConnectError:
            return HealthCheckResult(
                name="ollama",
                status=HealthStatus.UNHEALTHY,
                message="Ollama not running",
                fix_suggestion="Run 'ollama serve' to start Ollama",
            )
        except Exception as e:
            return HealthCheckResult(
                name="ollama",
                status=HealthStatus.UNKNOWN,
                message=f"Ollama check failed: {e}",
            )

    def _check_chromadb(self, _: "HealthCheck") -> HealthCheckResult:
        """Check ChromaDB is available."""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:8001/api/v1/heartbeat",
                timeout=5.0,
            )

            if response.status_code == 200:
                return HealthCheckResult(
                    name="chromadb",
                    status=HealthStatus.HEALTHY,
                    message="ChromaDB is running",
                )

            return HealthCheckResult(
                name="chromadb",
                status=HealthStatus.DEGRADED,
                message=f"ChromaDB returned status {response.status_code}",
            )

        except httpx.ConnectError:
            # Check if using local ChromaDB
            chromadb_path = self.ragged_home / "data" / "chromadb"
            if chromadb_path.exists():
                return HealthCheckResult(
                    name="chromadb",
                    status=HealthStatus.HEALTHY,
                    message="Using local ChromaDB storage",
                    details={"mode": "local", "path": str(chromadb_path)},
                )

            return HealthCheckResult(
                name="chromadb",
                status=HealthStatus.UNHEALTHY,
                message="ChromaDB not available",
                fix_suggestion="Start ChromaDB container or configure local storage",
            )
        except Exception as e:
            return HealthCheckResult(
                name="chromadb",
                status=HealthStatus.UNKNOWN,
                message=f"ChromaDB check failed: {e}",
            )

    def _check_permissions(self, _: "HealthCheck") -> HealthCheckResult:
        """Check file permissions."""
        import os

        issues = []

        # Check home directory
        if not os.access(self.ragged_home, os.R_OK | os.W_OK):
            issues.append(f"No read/write access to {self.ragged_home}")

        # Check .env file permissions (should be restrictive)
        env_path = self.ragged_home / ".env"
        if env_path.exists():
            mode = env_path.stat().st_mode & 0o777
            if mode > 0o600:
                issues.append(f".env file has too permissive permissions: {oct(mode)}")

        if issues:
            return HealthCheckResult(
                name="permissions",
                status=HealthStatus.DEGRADED,
                message="; ".join(issues),
                fix_suggestion="Run 'ragged doctor --fix' to correct permissions",
            )

        return HealthCheckResult(
            name="permissions",
            status=HealthStatus.HEALTHY,
            message="File permissions are correct",
        )

    def _check_disk_space(self, _: "HealthCheck") -> HealthCheckResult:
        """Check available disk space."""
        import shutil

        try:
            usage = shutil.disk_usage(self.ragged_home)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_pct = (usage.used / usage.total) * 100

            details = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_pct, 1),
            }

            if free_gb < 1:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Very low disk space: {free_gb:.1f}GB free",
                    details=details,
                    fix_suggestion="Free up disk space or move ragged home",
                )
            elif free_gb < 5:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.DEGRADED,
                    message=f"Low disk space: {free_gb:.1f}GB free",
                    details=details,
                    fix_suggestion="Consider freeing up space",
                )

            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.HEALTHY,
                message=f"{free_gb:.1f}GB free of {total_gb:.1f}GB",
                details=details,
            )

        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check disk space: {e}",
            )


def run_health_checks(
    ragged_home: Path | None = None,
) -> tuple[HealthStatus, list[HealthCheckResult]]:
    """
    Run all health checks.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        Tuple of overall status and list of results.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    checker = HealthCheck(ragged_home=ragged_home)
    results = checker.run_all()
    status = checker.overall_status(results)

    return status, results
