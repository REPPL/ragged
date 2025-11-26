"""
Base Detector Abstract Class.

Provides the foundation for all prerequisite detectors with common
functionality for platform detection and result caching.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import platform
import subprocess
import shutil
from typing import Any


class Platform(Enum):
    """Supported operating system platforms."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class DetectionStatus(Enum):
    """Status of dependency detection."""

    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    PARTIALLY_INSTALLED = "partially_installed"
    ERROR = "error"


@dataclass
class DetectionResult:
    """
    Result of prerequisite detection.

    Attributes:
        status: Overall detection status.
        installed: Whether the dependency is installed.
        version: Version string if detected, None otherwise.
        path: Installation path if found, None otherwise.
        issues: List of issues or warnings detected.
        details: Additional detection details.
        platform: Platform where detection occurred.
    """

    status: DetectionStatus
    installed: bool
    version: str | None = None
    path: str | None = None
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    platform: Platform = Platform.UNKNOWN

    def is_ready(self) -> bool:
        """Check if prerequisite is ready for use (installed without critical issues)."""
        return self.installed and self.status == DetectionStatus.INSTALLED

    def has_issues(self) -> bool:
        """Check if there are any issues detected."""
        return len(self.issues) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for serialisation."""
        return {
            "status": self.status.value,
            "installed": self.installed,
            "version": self.version,
            "path": self.path,
            "issues": self.issues,
            "details": self.details,
            "platform": self.platform.value,
        }


class BaseDetector(ABC):
    """
    Abstract base class for prerequisite detectors.

    Provides common functionality for platform detection, command execution,
    and result caching. Subclasses implement specific detection logic.
    """

    def __init__(self) -> None:
        """Initialise detector with platform detection."""
        self._platform = self._detect_platform()
        self._cached_result: DetectionResult | None = None

    @staticmethod
    @lru_cache(maxsize=1)
    def _detect_platform() -> Platform:
        """
        Detect the current operating system platform.

        Returns:
            Platform enum value for the current OS.
        """
        system = platform.system().lower()
        if system == "darwin":
            return Platform.MACOS
        elif system == "windows":
            return Platform.WINDOWS
        elif system == "linux":
            return Platform.LINUX
        return Platform.UNKNOWN

    @property
    def platform(self) -> Platform:
        """Get the current platform."""
        return self._platform

    def detect(self, force_refresh: bool = False) -> DetectionResult:
        """
        Perform prerequisite detection.

        Args:
            force_refresh: If True, bypass cache and re-detect.

        Returns:
            DetectionResult with detection outcome.
        """
        if self._cached_result is not None and not force_refresh:
            return self._cached_result

        try:
            result = self._do_detect()
            result.platform = self._platform
            self._cached_result = result
            return result
        except Exception as e:
            return DetectionResult(
                status=DetectionStatus.ERROR,
                installed=False,
                issues=[f"Detection error: {e!s}"],
                platform=self._platform,
            )

    @abstractmethod
    def _do_detect(self) -> DetectionResult:
        """
        Implement actual detection logic.

        Subclasses must implement this method to perform
        prerequisite-specific detection.

        Returns:
            DetectionResult with detection outcome.
        """
        ...

    def run_command(
        self,
        command: list[str],
        timeout: float = 10.0,
        capture_output: bool = True,
    ) -> tuple[int, str, str]:
        """
        Execute a shell command safely.

        Args:
            command: Command and arguments as list.
            timeout: Maximum execution time in seconds.
            capture_output: Whether to capture stdout/stderr.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            result = subprocess.run(
                command,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=False,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", f"Command not found: {command[0]}"
        except Exception as e:
            return -1, "", str(e)

    def find_executable(self, name: str) -> str | None:
        """
        Find an executable on the system PATH.

        Args:
            name: Name of the executable to find.

        Returns:
            Full path to executable if found, None otherwise.
        """
        return shutil.which(name)

    def check_path_exists(self, path: str) -> bool:
        """
        Check if a filesystem path exists.

        Args:
            path: Path to check.

        Returns:
            True if path exists, False otherwise.
        """
        from pathlib import Path

        return Path(path).exists()

    def get_platform_paths(self, paths: dict[Platform, list[str]]) -> list[str]:
        """
        Get platform-specific paths.

        Args:
            paths: Dictionary mapping platforms to path lists.

        Returns:
            List of paths for the current platform.
        """
        return paths.get(self._platform, [])

    def parse_version(self, version_string: str) -> tuple[int, ...] | None:
        """
        Parse a version string into tuple of integers.

        Args:
            version_string: Version string like "24.0.5" or "v3.11.4".

        Returns:
            Tuple of version parts or None if parsing fails.
        """
        import re

        # Remove common prefixes
        cleaned = re.sub(r"^[vV]?", "", version_string)

        # Extract numeric version parts
        match = re.search(r"(\d+(?:\.\d+)*)", cleaned)
        if match:
            try:
                return tuple(int(x) for x in match.group(1).split("."))
            except ValueError:
                return None
        return None

    def version_satisfies(
        self,
        version: str,
        minimum: str,
        maximum: str | None = None,
    ) -> bool:
        """
        Check if a version satisfies minimum/maximum constraints.

        Args:
            version: Version string to check.
            minimum: Minimum required version.
            maximum: Maximum allowed version (optional).

        Returns:
            True if version is within constraints.
        """
        parsed = self.parse_version(version)
        min_parsed = self.parse_version(minimum)

        if parsed is None or min_parsed is None:
            return False

        if parsed < min_parsed:
            return False

        if maximum is not None:
            max_parsed = self.parse_version(maximum)
            if max_parsed is not None and parsed > max_parsed:
                return False

        return True
