"""
Service Checker.

WIZARD-005: Check status of ragged services.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import logging
import subprocess


logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status."""

    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Information about a service."""

    name: str
    status: ServiceStatus
    message: str = ""
    url: str | None = None
    pid: int | None = None
    uptime: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class ServiceChecker:
    """
    Service status checker.

    Checks the status of all ragged-related services.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise service checker.

        Args:
            ragged_home: Path to ragged home directory.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )

    def check_all(self) -> list[ServiceInfo]:
        """Check all services."""
        services = []

        services.append(self._check_docker())
        services.append(self._check_ollama())
        services.append(self._check_chromadb())
        services.append(self._check_ragged_api())
        services.append(self._check_ragged_webui())

        return services

    def _check_docker(self) -> ServiceInfo:
        """Check Docker daemon status."""
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return ServiceInfo(
                    name="Docker",
                    status=ServiceStatus.RUNNING,
                    message=f"Version {version}",
                    details={"version": version},
                )

            return ServiceInfo(
                name="Docker",
                status=ServiceStatus.STOPPED,
                message="Docker daemon not running",
            )

        except FileNotFoundError:
            return ServiceInfo(
                name="Docker",
                status=ServiceStatus.NOT_INSTALLED,
                message="Docker not installed",
            )
        except subprocess.TimeoutExpired:
            return ServiceInfo(
                name="Docker",
                status=ServiceStatus.UNKNOWN,
                message="Docker check timed out",
            )

    def _check_ollama(self) -> ServiceInfo:
        """Check Ollama service status."""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:11434/api/version",
                timeout=5.0,
            )

            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")

                return ServiceInfo(
                    name="Ollama",
                    status=ServiceStatus.RUNNING,
                    message=f"Version {version}",
                    url="http://localhost:11434",
                    details={"version": version},
                )

            return ServiceInfo(
                name="Ollama",
                status=ServiceStatus.ERROR,
                message=f"Unexpected status: {response.status_code}",
            )

        except httpx.ConnectError:
            # Check if ollama binary exists
            try:
                result = subprocess.run(
                    ["which", "ollama"],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return ServiceInfo(
                        name="Ollama",
                        status=ServiceStatus.STOPPED,
                        message="Installed but not running",
                    )
            except Exception:
                pass

            return ServiceInfo(
                name="Ollama",
                status=ServiceStatus.STOPPED,
                message="Not running",
            )
        except Exception as e:
            return ServiceInfo(
                name="Ollama",
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )

    def _check_chromadb(self) -> ServiceInfo:
        """Check ChromaDB service status."""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:8001/api/v1/heartbeat",
                timeout=5.0,
            )

            if response.status_code == 200:
                return ServiceInfo(
                    name="ChromaDB",
                    status=ServiceStatus.RUNNING,
                    message="Running on port 8001",
                    url="http://localhost:8001",
                )

            return ServiceInfo(
                name="ChromaDB",
                status=ServiceStatus.ERROR,
                message=f"Unexpected status: {response.status_code}",
            )

        except httpx.ConnectError:
            # Check if using Docker
            try:
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=chromadb", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0 and result.stdout.strip():
                    status_str = result.stdout.strip()
                    if "Up" in status_str:
                        return ServiceInfo(
                            name="ChromaDB",
                            status=ServiceStatus.STARTING,
                            message=f"Container: {status_str}",
                        )

            except Exception:
                pass

            # Check for local storage
            local_path = self.ragged_home / "data" / "chromadb"
            if local_path.exists():
                return ServiceInfo(
                    name="ChromaDB",
                    status=ServiceStatus.RUNNING,
                    message="Using local storage",
                    details={"mode": "local"},
                )

            return ServiceInfo(
                name="ChromaDB",
                status=ServiceStatus.STOPPED,
                message="Not running",
            )
        except Exception as e:
            return ServiceInfo(
                name="ChromaDB",
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )

    def _check_ragged_api(self) -> ServiceInfo:
        """Check ragged API server status."""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:8000/health",
                timeout=5.0,
            )

            if response.status_code == 200:
                return ServiceInfo(
                    name="ragged API",
                    status=ServiceStatus.RUNNING,
                    message="Running on port 8000",
                    url="http://localhost:8000",
                )

            return ServiceInfo(
                name="ragged API",
                status=ServiceStatus.ERROR,
                message=f"Unexpected status: {response.status_code}",
            )

        except httpx.ConnectError:
            return ServiceInfo(
                name="ragged API",
                status=ServiceStatus.STOPPED,
                message="Not running",
            )
        except Exception as e:
            return ServiceInfo(
                name="ragged API",
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )

    def _check_ragged_webui(self) -> ServiceInfo:
        """Check ragged WebUI status."""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:5173/",
                timeout=5.0,
                follow_redirects=True,
            )

            if response.status_code == 200:
                return ServiceInfo(
                    name="ragged WebUI",
                    status=ServiceStatus.RUNNING,
                    message="Running on port 5173",
                    url="http://localhost:5173",
                )

            return ServiceInfo(
                name="ragged WebUI",
                status=ServiceStatus.ERROR,
                message=f"Unexpected status: {response.status_code}",
            )

        except httpx.ConnectError:
            return ServiceInfo(
                name="ragged WebUI",
                status=ServiceStatus.STOPPED,
                message="Not running",
            )
        except Exception as e:
            return ServiceInfo(
                name="ragged WebUI",
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )


def check_all_services(
    ragged_home: Path | None = None,
) -> list[ServiceInfo]:
    """
    Check all services.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        List of service information.
    """
    checker = ServiceChecker(ragged_home)
    return checker.check_all()
