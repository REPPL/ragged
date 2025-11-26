"""
Enhanced Health Checks.

REFINE-003: Granular health checks with multiple levels
and detailed status reporting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import logging
import time


logger = logging.getLogger(__name__)


class HealthLevel(Enum):
    """Health levels for services."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckCategory(Enum):
    """Categories of health checks."""

    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    RESOURCES = "resources"


@dataclass
class CheckResult:
    """Result of a single health check."""

    category: CheckCategory
    passed: bool
    message: str
    value: Any = None
    threshold: Any = None
    duration_ms: float = 0.0


@dataclass
class ServiceHealth:
    """Health status for a service."""

    name: str
    level: HealthLevel
    checks: list[CheckResult] = field(default_factory=list)
    url: str | None = None
    version: str | None = None
    uptime: str | None = None
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def connectivity_ok(self) -> bool:
        """Check if connectivity checks pass."""
        conn_checks = [c for c in self.checks if c.category == CheckCategory.CONNECTIVITY]
        return all(c.passed for c in conn_checks) if conn_checks else True

    @property
    def performance_ok(self) -> bool:
        """Check if performance checks pass."""
        perf_checks = [c for c in self.checks if c.category == CheckCategory.PERFORMANCE]
        return all(c.passed for c in perf_checks) if perf_checks else True

    @property
    def functionality_ok(self) -> bool:
        """Check if functionality checks pass."""
        func_checks = [c for c in self.checks if c.category == CheckCategory.FUNCTIONALITY]
        return all(c.passed for c in func_checks) if func_checks else True

    @property
    def resources_ok(self) -> bool:
        """Check if resource checks pass."""
        res_checks = [c for c in self.checks if c.category == CheckCategory.RESOURCES]
        return all(c.passed for c in res_checks) if res_checks else True


class HealthCheckSuite:
    """
    Suite of health checks for all services.

    Provides granular health status with multiple check categories.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise health check suite.

        Args:
            ragged_home: Path to ragged home directory.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )

    def check_all(self) -> list[ServiceHealth]:
        """Run all health checks."""
        services = []

        services.append(self._check_ollama())
        services.append(self._check_chromadb())
        services.append(self._check_ragged_api())
        services.append(self._check_ragged_storage())

        return services

    def _check_ollama(self) -> ServiceHealth:
        """Check Ollama health."""
        checks = []

        # Connectivity check
        start = time.perf_counter()
        try:
            import httpx

            response = httpx.get(
                "http://localhost:11434/api/version",
                timeout=5.0,
            )
            duration = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                checks.append(CheckResult(
                    category=CheckCategory.CONNECTIVITY,
                    passed=True,
                    message="Ollama reachable",
                    duration_ms=duration,
                ))

                # Performance check
                if duration < 200:
                    checks.append(CheckResult(
                        category=CheckCategory.PERFORMANCE,
                        passed=True,
                        message=f"Response time {duration:.0f}ms",
                        value=duration,
                        threshold=200,
                    ))
                else:
                    checks.append(CheckResult(
                        category=CheckCategory.PERFORMANCE,
                        passed=False,
                        message=f"Slow response {duration:.0f}ms (>200ms)",
                        value=duration,
                        threshold=200,
                    ))

                # Functionality check - list models
                models_response = httpx.get(
                    "http://localhost:11434/api/tags",
                    timeout=5.0,
                )
                if models_response.status_code == 200:
                    models = models_response.json().get("models", [])
                    checks.append(CheckResult(
                        category=CheckCategory.FUNCTIONALITY,
                        passed=len(models) > 0,
                        message=f"{len(models)} models available",
                        value=len(models),
                    ))

                version = response.json().get("version", "unknown")

                return ServiceHealth(
                    name="Ollama",
                    level=self._determine_level(checks),
                    checks=checks,
                    url="http://localhost:11434",
                    version=version,
                )

        except Exception as e:
            checks.append(CheckResult(
                category=CheckCategory.CONNECTIVITY,
                passed=False,
                message=f"Not reachable: {e}",
            ))

        return ServiceHealth(
            name="Ollama",
            level=HealthLevel.UNHEALTHY,
            checks=checks,
        )

    def _check_chromadb(self) -> ServiceHealth:
        """Check ChromaDB health."""
        checks = []

        # Check Docker-based ChromaDB
        start = time.perf_counter()
        try:
            import httpx

            response = httpx.get(
                "http://localhost:8001/api/v1/heartbeat",
                timeout=5.0,
            )
            duration = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                checks.append(CheckResult(
                    category=CheckCategory.CONNECTIVITY,
                    passed=True,
                    message="ChromaDB reachable",
                    duration_ms=duration,
                ))

                # Performance check
                checks.append(CheckResult(
                    category=CheckCategory.PERFORMANCE,
                    passed=duration < 200,
                    message=f"Response time {duration:.0f}ms",
                    value=duration,
                    threshold=200,
                ))

                return ServiceHealth(
                    name="ChromaDB",
                    level=self._determine_level(checks),
                    checks=checks,
                    url="http://localhost:8001",
                )

        except Exception:
            pass

        # Check local ChromaDB storage
        chromadb_path = self.ragged_home / "data" / "chromadb"
        if chromadb_path.exists():
            checks.append(CheckResult(
                category=CheckCategory.CONNECTIVITY,
                passed=True,
                message="Using local storage",
            ))

            # Check disk space
            import shutil
            usage = shutil.disk_usage(chromadb_path)
            free_gb = usage.free / (1024**3)
            checks.append(CheckResult(
                category=CheckCategory.RESOURCES,
                passed=free_gb > 1,
                message=f"{free_gb:.1f}GB free",
                value=free_gb,
                threshold=1,
            ))

            return ServiceHealth(
                name="ChromaDB",
                level=self._determine_level(checks),
                checks=checks,
            )

        checks.append(CheckResult(
            category=CheckCategory.CONNECTIVITY,
            passed=False,
            message="Not available",
        ))

        return ServiceHealth(
            name="ChromaDB",
            level=HealthLevel.UNHEALTHY,
            checks=checks,
        )

    def _check_ragged_api(self) -> ServiceHealth:
        """Check ragged API health."""
        checks = []

        start = time.perf_counter()
        try:
            import httpx

            response = httpx.get(
                "http://localhost:8000/health",
                timeout=5.0,
            )
            duration = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                checks.append(CheckResult(
                    category=CheckCategory.CONNECTIVITY,
                    passed=True,
                    message="API reachable",
                    duration_ms=duration,
                ))

                checks.append(CheckResult(
                    category=CheckCategory.PERFORMANCE,
                    passed=duration < 500,
                    message=f"Response time {duration:.0f}ms",
                    value=duration,
                    threshold=500,
                ))

                return ServiceHealth(
                    name="ragged API",
                    level=self._determine_level(checks),
                    checks=checks,
                    url="http://localhost:8000",
                )

        except Exception:
            checks.append(CheckResult(
                category=CheckCategory.CONNECTIVITY,
                passed=False,
                message="API not running",
            ))

        return ServiceHealth(
            name="ragged API",
            level=HealthLevel.UNHEALTHY,
            checks=checks,
        )

    def _check_ragged_storage(self) -> ServiceHealth:
        """Check ragged storage health."""
        checks = []

        # Check directories exist
        required_dirs = ["documents", "logs", "config", "data"]
        missing = [d for d in required_dirs if not (self.ragged_home / d).exists()]

        if missing:
            checks.append(CheckResult(
                category=CheckCategory.FUNCTIONALITY,
                passed=False,
                message=f"Missing directories: {', '.join(missing)}",
            ))
        else:
            checks.append(CheckResult(
                category=CheckCategory.FUNCTIONALITY,
                passed=True,
                message="All directories present",
            ))

        # Check disk space
        import shutil
        usage = shutil.disk_usage(self.ragged_home)
        free_gb = usage.free / (1024**3)
        checks.append(CheckResult(
            category=CheckCategory.RESOURCES,
            passed=free_gb > 2,
            message=f"{free_gb:.1f}GB free",
            value=free_gb,
            threshold=2,
        ))

        # Check config file
        config_path = self.ragged_home / "config.yaml"
        checks.append(CheckResult(
            category=CheckCategory.FUNCTIONALITY,
            passed=config_path.exists(),
            message="Config present" if config_path.exists() else "Config missing",
        ))

        return ServiceHealth(
            name="Storage",
            level=self._determine_level(checks),
            checks=checks,
        )

    def _determine_level(self, checks: list[CheckResult]) -> HealthLevel:
        """Determine overall health level from checks."""
        if not checks:
            return HealthLevel.UNKNOWN

        failed = [c for c in checks if not c.passed]

        if not failed:
            return HealthLevel.HEALTHY

        # Check if critical categories failed
        critical_failed = [
            c for c in failed
            if c.category in (CheckCategory.CONNECTIVITY, CheckCategory.FUNCTIONALITY)
        ]

        if critical_failed:
            return HealthLevel.UNHEALTHY

        return HealthLevel.DEGRADED


def run_health_suite(
    ragged_home: Path | None = None,
) -> list[ServiceHealth]:
    """
    Run complete health check suite.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        List of service health status.
    """
    suite = HealthCheckSuite(ragged_home)
    return suite.check_all()
