"""
Ollama Detector.

PREREQ-001: Detects Ollama installation, service status, and installed models.
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


# Minimum supported version (Ollama had rapid development, be lenient)
MIN_OLLAMA_VERSION = "0.1.0"


class OllamaDetector(BaseDetector):
    """
    Detector for Ollama installation.

    Detects:
    - Ollama binary location
    - Ollama version
    - Service status (running on port 11434)
    - Installed models
    - Storage location and size
    """

    def _do_detect(self) -> DetectionResult:
        """Perform Ollama detection."""
        issues: list[str] = []
        details: dict[str, object] = {}

        # Step 1: Find Ollama binary
        ollama_path = self._find_ollama_binary()
        if ollama_path is None:
            return DetectionResult(
                status=DetectionStatus.NOT_INSTALLED,
                installed=False,
                issues=["Ollama is not installed or not in PATH"],
            )

        details["binary_path"] = ollama_path

        # Step 2: Get Ollama version
        version = self._get_ollama_version()
        if version is None:
            issues.append("Could not determine Ollama version")
        else:
            details["ollama_version"] = version
            if not self.version_satisfies(version, MIN_OLLAMA_VERSION):
                issues.append(
                    f"Ollama version {version} is below minimum {MIN_OLLAMA_VERSION}"
                )

        # Step 3: Check service status
        service_running = self._is_service_running()
        details["service_running"] = service_running
        if not service_running:
            issues.append("Ollama service is not running (port 11434)")

        # Step 4: Get installed models
        models = self._get_installed_models()
        details["models"] = models
        details["model_count"] = len(models)

        if not models:
            issues.append("No Ollama models installed")

        # Step 5: Get storage information
        storage = self._get_storage_info()
        details["storage"] = storage

        # Step 6: Detect API availability
        api_info = self._check_api_availability()
        details["api"] = api_info

        # Determine overall status
        if not service_running:
            status = DetectionStatus.PARTIALLY_INSTALLED
        elif issues:
            status = DetectionStatus.PARTIALLY_INSTALLED
        else:
            status = DetectionStatus.INSTALLED

        return DetectionResult(
            status=status,
            installed=True,
            version=version,
            path=ollama_path,
            issues=issues,
            details=details,
        )

    def _find_ollama_binary(self) -> str | None:
        """Find Ollama binary on the system."""
        # First try PATH
        path = self.find_executable("ollama")
        if path:
            return path

        # Platform-specific locations
        platform_paths: dict[Platform, list[str]] = {
            Platform.MACOS: [
                "/usr/local/bin/ollama",
                "/opt/homebrew/bin/ollama",
            ],
            Platform.LINUX: [
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
                str(Path.home() / ".ollama" / "bin" / "ollama"),
            ],
            Platform.WINDOWS: [
                str(
                    Path.home()
                    / "AppData"
                    / "Local"
                    / "Programs"
                    / "Ollama"
                    / "ollama.exe"
                ),
                r"C:\Program Files\Ollama\ollama.exe",
            ],
        }

        for candidate in self.get_platform_paths(platform_paths):
            if self.check_path_exists(candidate):
                return candidate

        return None

    def _get_ollama_version(self) -> str | None:
        """Get Ollama version string."""
        code, stdout, _ = self.run_command(["ollama", "--version"])
        if code != 0:
            return None

        # Parse "ollama version is 0.1.32" or "ollama version 0.1.32"
        match = re.search(r"ollama version\s*(?:is\s*)?(\d+\.\d+(?:\.\d+)?)", stdout)
        if match:
            return match.group(1)

        # Some versions just output the version number
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", stdout)
        if match:
            return match.group(1)

        return None

    def _is_service_running(self) -> bool:
        """Check if Ollama service is running."""
        # Try to connect to the API
        import socket

        try:
            with socket.create_connection(("localhost", 11434), timeout=5):
                return True
        except (socket.error, socket.timeout):
            pass

        # Alternative: try ollama list command
        code, _, _ = self.run_command(["ollama", "list"], timeout=10.0)
        return code == 0

    def _get_installed_models(self) -> list[dict[str, str]]:
        """Get list of installed Ollama models."""
        code, stdout, _ = self.run_command(["ollama", "list"], timeout=30.0)
        if code != 0:
            return []

        models: list[dict[str, str]] = []
        lines = stdout.strip().split("\n")

        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue

            # Parse "NAME                    ID              SIZE      MODIFIED"
            parts = line.split()
            if len(parts) >= 3:
                model: dict[str, str] = {
                    "name": parts[0],
                    "id": parts[1] if len(parts) > 1 else "",
                    "size": parts[2] if len(parts) > 2 else "",
                }
                models.append(model)

        return models

    def _get_storage_info(self) -> dict[str, object]:
        """Get Ollama storage information."""
        result: dict[str, object] = {
            "path": None,
            "size_bytes": 0,
            "model_count": 0,
        }

        # Default model storage locations
        platform_paths: dict[Platform, str] = {
            Platform.MACOS: str(Path.home() / ".ollama" / "models"),
            Platform.LINUX: str(Path.home() / ".ollama" / "models"),
            Platform.WINDOWS: str(
                Path.home() / ".ollama" / "models"
            ),
        }

        storage_path = platform_paths.get(self.platform)
        if storage_path and self.check_path_exists(storage_path):
            result["path"] = storage_path

            # Calculate total size
            total_size = 0
            try:
                for entry in Path(storage_path).rglob("*"):
                    if entry.is_file():
                        total_size += entry.stat().st_size
                result["size_bytes"] = total_size
                result["size_gb"] = round(total_size / (1024**3), 2)
            except (OSError, PermissionError):
                pass

        return result

    def _check_api_availability(self) -> dict[str, object]:
        """Check Ollama API availability."""
        result: dict[str, object] = {
            "available": False,
            "host": "localhost",
            "port": 11434,
            "url": "http://localhost:11434",
        }

        # Check if OLLAMA_HOST is set
        ollama_host = os.environ.get("OLLAMA_HOST")
        if ollama_host:
            result["url"] = ollama_host
            # Parse host/port from URL
            if ":" in ollama_host:
                parts = ollama_host.replace("http://", "").replace("https://", "").split(":")
                if len(parts) >= 2:
                    result["host"] = parts[0]
                    try:
                        result["port"] = int(parts[1].split("/")[0])
                    except ValueError:
                        pass

        # Try to connect to API
        try:
            import urllib.request
            import urllib.error

            url = f"{result['url']}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    result["available"] = True
        except (urllib.error.URLError, TimeoutError, OSError):
            # API not available but service might still be running
            pass

        return result

    def get_model_info(self, model_name: str) -> dict[str, object] | None:
        """Get detailed information about a specific model."""
        code, stdout, _ = self.run_command(["ollama", "show", model_name])
        if code != 0:
            return None

        result: dict[str, object] = {"name": model_name, "info": stdout}
        return result

    def pull_model(self, model_name: str, timeout: float = 600.0) -> bool:
        """Pull an Ollama model (for use during installation)."""
        code, _, _ = self.run_command(
            ["ollama", "pull", model_name],
            timeout=timeout,
        )
        return code == 0

    def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        models = self._get_installed_models()
        model_names = [m["name"] for m in models]

        # Check exact match
        if model_name in model_names:
            return True

        # Check with common tag patterns
        for name in model_names:
            if name.startswith(model_name):
                return True
            # Handle "llama3.2:3b" matching "llama3.2"
            base_name = name.split(":")[0]
            if base_name == model_name:
                return True

        return False
