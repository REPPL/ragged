"""
Python Detector.

PREREQ-001: Detects Python installation, version, pip, and virtual environment capabilities.
Supports system Python, pyenv, conda, and other Python managers.
"""

import os
import re
import sys
from pathlib import Path

from ragged.install.detection.base import (
    BaseDetector,
    DetectionResult,
    DetectionStatus,
    Platform,
)


# Minimum supported version
MIN_PYTHON_VERSION = "3.10"
MAX_PYTHON_VERSION = "3.12"


class PythonDetector(BaseDetector):
    """
    Detector for Python installation.

    Detects:
    - Python binary location
    - Python version (minimum 3.10 required)
    - pip installation
    - Virtual environment capability
    - Active virtual environment
    - Python manager (pyenv, conda, system)
    """

    def _do_detect(self) -> DetectionResult:
        """Perform Python detection."""
        issues: list[str] = []
        details: dict[str, object] = {}

        # Step 1: Find Python binary
        python_path = self._find_python_binary()
        if python_path is None:
            return DetectionResult(
                status=DetectionStatus.NOT_INSTALLED,
                installed=False,
                issues=["Python 3.10+ is not installed or not in PATH"],
            )

        details["binary_path"] = python_path

        # Step 2: Get Python version
        version = self._get_python_version(python_path)
        if version is None:
            issues.append("Could not determine Python version")
        else:
            details["python_version"] = version
            if not self.version_satisfies(version, MIN_PYTHON_VERSION, MAX_PYTHON_VERSION):
                issues.append(
                    f"Python version {version} is outside supported range "
                    f"({MIN_PYTHON_VERSION}-{MAX_PYTHON_VERSION})"
                )

        # Step 3: Check pip installation
        pip_info = self._detect_pip(python_path)
        details["pip"] = pip_info
        if not pip_info.get("installed"):
            issues.append("pip is not installed")

        # Step 4: Check virtual environment capability
        venv_capable = self._check_venv_capability(python_path)
        details["venv_capable"] = venv_capable
        if not venv_capable:
            issues.append("Python venv module is not available")

        # Step 5: Detect active virtual environment
        venv_info = self._detect_virtual_environment()
        details["virtual_environment"] = venv_info

        # Step 6: Detect Python manager
        manager = self._detect_python_manager(python_path)
        details["python_manager"] = manager

        # Step 7: Get Python installation info
        install_info = self._get_installation_info(python_path)
        details["installation"] = install_info

        # Determine overall status
        if version and not self.version_satisfies(version, MIN_PYTHON_VERSION, MAX_PYTHON_VERSION):
            status = DetectionStatus.PARTIALLY_INSTALLED
        elif not pip_info.get("installed") or not venv_capable:
            status = DetectionStatus.PARTIALLY_INSTALLED
        elif issues:
            status = DetectionStatus.PARTIALLY_INSTALLED
        else:
            status = DetectionStatus.INSTALLED

        return DetectionResult(
            status=status,
            installed=True,
            version=version,
            path=python_path,
            issues=issues,
            details=details,
        )

    def _find_python_binary(self) -> str | None:
        """Find suitable Python binary."""
        # Candidates in order of preference
        candidates = ["python3.12", "python3.11", "python3.10", "python3", "python"]

        for candidate in candidates:
            path = self.find_executable(candidate)
            if path:
                # Verify it's Python 3.10+
                version = self._get_python_version(path)
                if version and self.version_satisfies(version, MIN_PYTHON_VERSION):
                    return path

        # Platform-specific fallback paths
        platform_paths: dict[Platform, list[str]] = {
            Platform.MACOS: [
                "/opt/homebrew/bin/python3",
                "/usr/local/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
            ],
            Platform.LINUX: [
                "/usr/bin/python3",
                "/usr/local/bin/python3",
            ],
            Platform.WINDOWS: [
                r"C:\Python312\python.exe",
                r"C:\Python311\python.exe",
                r"C:\Python310\python.exe",
            ],
        }

        for candidate in self.get_platform_paths(platform_paths):
            if self.check_path_exists(candidate):
                version = self._get_python_version(candidate)
                if version and self.version_satisfies(version, MIN_PYTHON_VERSION):
                    return candidate

        return None

    def _get_python_version(self, python_path: str) -> str | None:
        """Get Python version from binary."""
        code, stdout, _ = self.run_command([python_path, "--version"])
        if code != 0:
            return None

        # Parse "Python 3.11.4"
        match = re.search(r"Python (\d+\.\d+(?:\.\d+)?)", stdout)
        if match:
            return match.group(1)
        return None

    def _detect_pip(self, python_path: str) -> dict[str, object]:
        """Detect pip installation."""
        result: dict[str, object] = {"installed": False, "version": None, "path": None}

        code, stdout, _ = self.run_command([python_path, "-m", "pip", "--version"])
        if code != 0:
            return result

        result["installed"] = True

        # Parse "pip 23.3.1 from /path/to/pip (python 3.11)"
        version_match = re.search(r"pip (\d+\.\d+(?:\.\d+)?)", stdout)
        if version_match:
            result["version"] = version_match.group(1)

        path_match = re.search(r"from ([^\s]+)", stdout)
        if path_match:
            result["path"] = path_match.group(1)

        return result

    def _check_venv_capability(self, python_path: str) -> bool:
        """Check if Python can create virtual environments."""
        code, _, _ = self.run_command([python_path, "-m", "venv", "--help"])
        return code == 0

    def _detect_virtual_environment(self) -> dict[str, object]:
        """Detect if running in a virtual environment."""
        result: dict[str, object] = {"active": False, "path": None, "type": None}

        # Check VIRTUAL_ENV environment variable
        venv_path = os.environ.get("VIRTUAL_ENV")
        if venv_path:
            result["active"] = True
            result["path"] = venv_path
            result["type"] = "venv"
            return result

        # Check for conda environment
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if conda_prefix:
            result["active"] = True
            result["path"] = conda_prefix
            result["type"] = "conda"
            return result

        # Check sys.prefix vs sys.base_prefix
        if sys.prefix != sys.base_prefix:
            result["active"] = True
            result["path"] = sys.prefix
            result["type"] = "venv"

        return result

    def _detect_python_manager(self, python_path: str) -> str:
        """Detect how Python was installed/managed."""
        path_str = str(python_path).lower()

        if "pyenv" in path_str:
            return "pyenv"
        elif "conda" in path_str or "anaconda" in path_str or "miniconda" in path_str:
            return "conda"
        elif "homebrew" in path_str or "/opt/homebrew" in path_str:
            return "homebrew"
        elif "asdf" in path_str:
            return "asdf"

        # Check for pyenv shim
        code, stdout, _ = self.run_command(["pyenv", "version"])
        if code == 0:
            return "pyenv"

        # Platform-specific defaults
        if self.platform == Platform.MACOS:
            if "/Library/Frameworks" in path_str:
                return "official_installer"
            return "system"
        elif self.platform == Platform.LINUX:
            if "/usr/bin" in path_str:
                return "system"
            return "manual"
        elif self.platform == Platform.WINDOWS:
            if "WindowsApps" in path_str:
                return "microsoft_store"
            return "official_installer"

        return "unknown"

    def _get_installation_info(self, python_path: str) -> dict[str, object]:
        """Get detailed Python installation information."""
        result: dict[str, object] = {}

        # Get sys.prefix and sys.base_prefix
        code, stdout, _ = self.run_command(
            [python_path, "-c", "import sys; print(sys.prefix); print(sys.base_prefix)"]
        )
        if code == 0:
            lines = stdout.strip().split("\n")
            if len(lines) >= 2:
                result["prefix"] = lines[0]
                result["base_prefix"] = lines[1]

        # Get site-packages location
        code, stdout, _ = self.run_command(
            [python_path, "-c", "import site; print(site.getsitepackages()[0])"]
        )
        if code == 0:
            result["site_packages"] = stdout.strip()

        # Check if user can install packages
        code, stdout, _ = self.run_command(
            [python_path, "-c", "import sys; print(not sys.flags.no_user_site)"]
        )
        if code == 0:
            result["user_site_enabled"] = stdout.strip() == "True"

        return result

    def check_package_installed(self, package: str) -> bool:
        """Check if a Python package is installed."""
        python_path = self._find_python_binary()
        if not python_path:
            return False

        code, _, _ = self.run_command(
            [python_path, "-c", f"import {package}"]
        )
        return code == 0

    def get_installed_packages(self) -> list[dict[str, str]]:
        """Get list of installed packages."""
        python_path = self._find_python_binary()
        if not python_path:
            return []

        code, stdout, _ = self.run_command(
            [python_path, "-m", "pip", "list", "--format=json"]
        )
        if code != 0:
            return []

        import json

        try:
            packages: list[dict[str, str]] = json.loads(stdout)
            return packages
        except json.JSONDecodeError:
            return []
