"""
Docker Detector.

PREREQ-001: Detects Docker installation, daemon status, and Docker Compose.
Supports Docker Desktop (macOS, Windows) and Docker Engine (Linux).
"""

import os
import re
from pathlib import Path

from ragged.install.detection.base import (
    BaseDetector,
    DetectionResult,
    DetectionStatus,
    Platform,
)


# Minimum supported versions
MIN_DOCKER_VERSION = "20.10"
MIN_COMPOSE_VERSION = "2.0"


class DockerDetector(BaseDetector):
    """
    Detector for Docker and Docker Compose.

    Detects:
    - Docker binary location
    - Docker daemon status
    - Docker version
    - Docker Compose (v1 or v2)
    - Installation method (Docker Desktop vs Engine)
    """

    def _do_detect(self) -> DetectionResult:
        """Perform Docker detection."""
        issues: list[str] = []
        details: dict[str, object] = {}

        # Step 1: Find Docker binary
        docker_path = self._find_docker_binary()
        if docker_path is None:
            return DetectionResult(
                status=DetectionStatus.NOT_INSTALLED,
                installed=False,
                issues=["Docker is not installed or not in PATH"],
                details={"installation_method": None},
            )

        details["binary_path"] = docker_path

        # Step 2: Check Docker version
        version = self._get_docker_version()
        if version is None:
            issues.append("Could not determine Docker version")
        else:
            details["docker_version"] = version
            if not self.version_satisfies(version, MIN_DOCKER_VERSION):
                issues.append(
                    f"Docker version {version} is below minimum {MIN_DOCKER_VERSION}"
                )

        # Step 3: Check Docker daemon status
        daemon_running = self._is_daemon_running()
        details["daemon_running"] = daemon_running
        if not daemon_running:
            issues.append("Docker daemon is not running")

        # Step 4: Check Docker Compose
        compose_info = self._detect_docker_compose()
        details["compose"] = compose_info
        if not compose_info.get("installed"):
            issues.append("Docker Compose is not installed")
        elif compose_info.get("version"):
            compose_version = compose_info["version"]
            if not self.version_satisfies(str(compose_version), MIN_COMPOSE_VERSION):
                issues.append(
                    f"Docker Compose version {compose_version} is below minimum {MIN_COMPOSE_VERSION}"
                )

        # Step 5: Detect installation method
        installation_method = self._detect_installation_method()
        details["installation_method"] = installation_method

        # Determine overall status
        if not daemon_running:
            status = DetectionStatus.PARTIALLY_INSTALLED
        elif issues:
            status = DetectionStatus.PARTIALLY_INSTALLED
        else:
            status = DetectionStatus.INSTALLED

        return DetectionResult(
            status=status,
            installed=True,
            version=version,
            path=docker_path,
            issues=issues,
            details=details,
        )

    def _find_docker_binary(self) -> str | None:
        """Find Docker binary on the system."""
        # First try PATH
        path = self.find_executable("docker")
        if path:
            return path

        # Platform-specific locations
        platform_paths: dict[Platform, list[str]] = {
            Platform.MACOS: [
                "/usr/local/bin/docker",
                "/opt/homebrew/bin/docker",
                "/Applications/Docker.app/Contents/Resources/bin/docker",
            ],
            Platform.LINUX: [
                "/usr/bin/docker",
                "/usr/local/bin/docker",
                "/snap/bin/docker",
            ],
            Platform.WINDOWS: [
                r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            ],
        }

        for candidate in self.get_platform_paths(platform_paths):
            if self.check_path_exists(candidate):
                return candidate

        return None

    def _get_docker_version(self) -> str | None:
        """Get Docker version string."""
        code, stdout, _ = self.run_command(["docker", "--version"])
        if code != 0:
            return None

        # Parse "Docker version 24.0.5, build ..."
        match = re.search(r"Docker version (\d+\.\d+(?:\.\d+)?)", stdout)
        if match:
            return match.group(1)
        return None

    def _is_daemon_running(self) -> bool:
        """Check if Docker daemon is running."""
        code, _, _ = self.run_command(["docker", "info"], timeout=15.0)
        return code == 0

    def _detect_docker_compose(self) -> dict[str, object]:
        """Detect Docker Compose installation."""
        result: dict[str, object] = {"installed": False, "version": None, "type": None}

        # Try Docker Compose v2 (docker compose)
        code, stdout, _ = self.run_command(["docker", "compose", "version"])
        if code == 0:
            match = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", stdout)
            if match:
                result["installed"] = True
                result["version"] = match.group(1)
                result["type"] = "v2"
                return result

        # Try Docker Compose v1 (docker-compose)
        code, stdout, _ = self.run_command(["docker-compose", "--version"])
        if code == 0:
            match = re.search(r"version v?(\d+\.\d+(?:\.\d+)?)", stdout)
            if match:
                result["installed"] = True
                result["version"] = match.group(1)
                result["type"] = "v1"
                return result

        return result

    def _detect_installation_method(self) -> str:
        """Detect how Docker was installed."""
        if self.platform == Platform.MACOS:
            # Check for Docker Desktop
            if Path("/Applications/Docker.app").exists():
                return "docker_desktop"
            # Check for Homebrew
            code, stdout, _ = self.run_command(["brew", "list", "--cask", "docker"])
            if code == 0:
                return "homebrew_cask"
            code, stdout, _ = self.run_command(["brew", "list", "docker"])
            if code == 0:
                return "homebrew"
            return "unknown"

        elif self.platform == Platform.LINUX:
            # Check for snap
            if Path("/snap/bin/docker").exists():
                return "snap"
            # Check for apt
            code, _, _ = self.run_command(["dpkg", "-s", "docker-ce"])
            if code == 0:
                return "apt"
            # Check for dnf/yum
            code, _, _ = self.run_command(["rpm", "-q", "docker-ce"])
            if code == 0:
                return "rpm"
            return "script"

        elif self.platform == Platform.WINDOWS:
            # Check for Docker Desktop
            if Path(r"C:\Program Files\Docker\Docker").exists():
                return "docker_desktop"
            # Check for WSL
            code, _, _ = self.run_command(["wsl", "--status"])
            if code == 0:
                return "wsl"
            return "unknown"

        return "unknown"

    def get_docker_info(self) -> dict[str, object] | None:
        """Get detailed Docker system information."""
        code, stdout, _ = self.run_command(["docker", "info", "--format", "{{json .}}"])
        if code != 0:
            return None

        import json

        try:
            return dict(json.loads(stdout))
        except json.JSONDecodeError:
            return None

    def get_storage_driver(self) -> str | None:
        """Get Docker storage driver."""
        info = self.get_docker_info()
        if info:
            return str(info.get("Driver", "unknown"))
        return None

    def get_docker_root(self) -> str | None:
        """Get Docker root directory."""
        info = self.get_docker_info()
        if info:
            return str(info.get("DockerRootDir", ""))
        return None
