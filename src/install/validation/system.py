"""
System Requirements Validator.

PREREQ-003: Validates system requirements including RAM, CPU,
and OS version for ragged installation.
"""

import os
import platform
from typing import Any

from ragged.install.detection.base import Platform, BaseDetector
from ragged.install.validation.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


# System requirements
MIN_RAM_GB = 4
RECOMMENDED_RAM_GB = 8
OPTIMAL_RAM_GB = 16

MIN_CPU_CORES = 2
RECOMMENDED_CPU_CORES = 4

# Minimum OS versions
MIN_OS_VERSIONS = {
    Platform.MACOS: "11.0",  # Big Sur
    Platform.LINUX: "5.0",  # Kernel version
    Platform.WINDOWS: "10",  # Windows 10
}


class SystemValidator(BaseValidator):
    """
    Validator for system requirements.

    Checks:
    - Available RAM
    - CPU core count
    - OS version compatibility
    - Architecture compatibility
    """

    def __init__(self) -> None:
        """Initialise system validator."""
        self._platform = BaseDetector._detect_platform()

    @property
    def category(self) -> str:
        """Return category name."""
        return "system"

    def validate(self) -> list[ValidationResult]:
        """Run all system validation checks."""
        results = []

        results.append(self._check_ram())
        results.append(self._check_cpu())
        results.append(self._check_os_version())
        results.append(self._check_architecture())

        return results

    def _check_ram(self) -> ValidationResult:
        """Check system RAM."""
        ram_gb = self._get_system_ram_gb()

        details: dict[str, Any] = {
            "ram_gb": ram_gb,
            "minimum": MIN_RAM_GB,
            "recommended": RECOMMENDED_RAM_GB,
            "optimal": OPTIMAL_RAM_GB,
        }

        if ram_gb is None:
            return self.create_result(
                name="ram",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message="Could not determine system RAM",
                details=details,
                fix_suggestion=f"Ensure at least {RECOMMENDED_RAM_GB}GB RAM is available.",
            )

        if ram_gb < MIN_RAM_GB:
            return self.create_result(
                name="ram",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Insufficient RAM: {ram_gb:.1f}GB (minimum {MIN_RAM_GB}GB)",
                details=details,
                fix_suggestion=(
                    f"ragged requires at least {MIN_RAM_GB}GB RAM. "
                    f"Recommended: {RECOMMENDED_RAM_GB}GB+."
                ),
            )

        if ram_gb < RECOMMENDED_RAM_GB:
            return self.create_result(
                name="ram",
                passed=True,
                message=f"RAM: {ram_gb:.1f}GB (recommended: {RECOMMENDED_RAM_GB}GB+)",
                details=details,
            )

        if ram_gb < OPTIMAL_RAM_GB:
            return self.create_result(
                name="ram",
                passed=True,
                message=f"RAM: {ram_gb:.1f}GB OK (optimal: {OPTIMAL_RAM_GB}GB for large models)",
                details=details,
            )

        return self.create_result(
            name="ram",
            passed=True,
            message=f"RAM: {ram_gb:.1f}GB - excellent",
            details=details,
        )

    def _check_cpu(self) -> ValidationResult:
        """Check CPU core count."""
        cpu_count = os.cpu_count() or 1

        details: dict[str, Any] = {
            "cpu_cores": cpu_count,
            "minimum": MIN_CPU_CORES,
            "recommended": RECOMMENDED_CPU_CORES,
        }

        if cpu_count < MIN_CPU_CORES:
            return self.create_result(
                name="cpu",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Low CPU cores: {cpu_count} (minimum {MIN_CPU_CORES})",
                details=details,
                fix_suggestion=(
                    "Performance may be limited with fewer than "
                    f"{MIN_CPU_CORES} CPU cores."
                ),
            )

        if cpu_count < RECOMMENDED_CPU_CORES:
            return self.create_result(
                name="cpu",
                passed=True,
                message=f"CPU cores: {cpu_count} (recommended: {RECOMMENDED_CPU_CORES}+)",
                details=details,
            )

        return self.create_result(
            name="cpu",
            passed=True,
            message=f"CPU cores: {cpu_count} - OK",
            details=details,
        )

    def _check_os_version(self) -> ValidationResult:
        """Check OS version compatibility."""
        os_info = self._get_os_info()

        details: dict[str, Any] = {
            "os_name": os_info.get("name"),
            "os_version": os_info.get("version"),
            "platform": self._platform.value,
        }

        min_version = MIN_OS_VERSIONS.get(self._platform)

        if self._platform == Platform.MACOS:
            return self._check_macos_version(os_info, details, str(min_version))
        elif self._platform == Platform.LINUX:
            return self._check_linux_version(os_info, details, str(min_version))
        elif self._platform == Platform.WINDOWS:
            return self._check_windows_version(os_info, details, str(min_version))

        return self.create_result(
            name="os_version",
            passed=True,
            message=f"OS: {os_info.get('name', 'Unknown')} {os_info.get('version', '')}",
            details=details,
        )

    def _check_macos_version(
        self,
        os_info: dict[str, Any],
        details: dict[str, Any],
        min_version: str,
    ) -> ValidationResult:
        """Check macOS version."""
        version = os_info.get("version", "")
        details["minimum_version"] = min_version

        if version:
            try:
                major = int(version.split(".")[0])
                min_major = int(min_version.split(".")[0])

                if major < min_major:
                    return self.create_result(
                        name="os_version",
                        passed=False,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"macOS {version} below minimum {min_version}",
                        details=details,
                        fix_suggestion=f"Upgrade to macOS {min_version} (Big Sur) or later.",
                    )
            except (ValueError, IndexError):
                pass

        return self.create_result(
            name="os_version",
            passed=True,
            message=f"macOS {version} - OK",
            details=details,
        )

    def _check_linux_version(
        self,
        os_info: dict[str, Any],
        details: dict[str, Any],
        min_version: str,
    ) -> ValidationResult:
        """Check Linux kernel version."""
        kernel = os_info.get("kernel_version", "")
        distro = os_info.get("distro_name", "Linux")
        distro_version = os_info.get("distro_version", "")
        details["minimum_kernel"] = min_version
        details["distro"] = distro
        details["distro_version"] = distro_version

        # Check kernel version
        if kernel:
            try:
                major = int(kernel.split(".")[0])
                min_major = int(min_version.split(".")[0])

                if major < min_major:
                    return self.create_result(
                        name="os_version",
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Linux kernel {kernel} may be outdated",
                        details=details,
                        fix_suggestion="Consider updating your Linux distribution.",
                    )
            except (ValueError, IndexError):
                pass

        version_str = f"{distro} {distro_version}" if distro_version else distro
        return self.create_result(
            name="os_version",
            passed=True,
            message=f"{version_str} - OK",
            details=details,
        )

    def _check_windows_version(
        self,
        os_info: dict[str, Any],
        details: dict[str, Any],
        min_version: str,
    ) -> ValidationResult:
        """Check Windows version."""
        version = os_info.get("version", "")
        details["minimum_version"] = min_version

        # Windows version string like "10.0.19041"
        if version:
            try:
                major = int(version.split(".")[0])
                min_major = int(min_version)

                if major < min_major:
                    return self.create_result(
                        name="os_version",
                        passed=False,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Windows {major} below minimum Windows {min_version}",
                        details=details,
                        fix_suggestion=f"Upgrade to Windows {min_version} or later.",
                    )
            except (ValueError, IndexError):
                pass

        return self.create_result(
            name="os_version",
            passed=True,
            message=f"Windows {version} - OK",
            details=details,
        )

    def _check_architecture(self) -> ValidationResult:
        """Check CPU architecture compatibility."""
        machine = platform.machine().lower()

        details: dict[str, Any] = {
            "architecture": machine,
            "supported": ["x86_64", "amd64", "arm64", "aarch64"],
        }

        # Supported architectures
        supported = ["x86_64", "amd64", "arm64", "aarch64"]

        if machine in supported:
            return self.create_result(
                name="architecture",
                passed=True,
                message=f"Architecture: {machine} - supported",
                details=details,
            )

        # Check for ARM variations
        if machine.startswith("arm"):
            return self.create_result(
                name="architecture",
                passed=True,
                message=f"Architecture: {machine} - supported (ARM)",
                details=details,
            )

        return self.create_result(
            name="architecture",
            passed=False,
            severity=ValidationSeverity.WARNING,
            message=f"Architecture: {machine} - may not be fully supported",
            details=details,
            fix_suggestion="ragged is optimised for x86_64 and ARM64 architectures.",
        )

    def _get_system_ram_gb(self) -> float | None:
        """Get system RAM in GB."""
        try:
            import psutil

            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            pass

        # Fallback methods
        if self._platform == Platform.MACOS:
            try:
                import subprocess

                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0:
                    return int(result.stdout.strip()) / (1024**3)
            except (subprocess.TimeoutExpired, ValueError, OSError):
                pass

        elif self._platform == Platform.LINUX:
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_kb = int(line.split()[1])
                            return mem_kb / (1024**2)
            except (FileNotFoundError, ValueError, OSError):
                pass

        return None

    def _get_os_info(self) -> dict[str, Any]:
        """Get OS information."""
        info: dict[str, Any] = {
            "name": platform.system(),
            "version": platform.release(),
            "platform": platform.platform(),
        }

        if self._platform == Platform.MACOS:
            try:
                import subprocess

                result = subprocess.run(
                    ["sw_vers", "-productVersion"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0:
                    info["version"] = result.stdout.strip()
                    info["name"] = "macOS"
            except (subprocess.TimeoutExpired, OSError):
                pass

        elif self._platform == Platform.LINUX:
            info["kernel_version"] = platform.release()
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("NAME="):
                            info["distro_name"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("VERSION_ID="):
                            info["distro_version"] = line.split("=")[1].strip().strip('"')
            except (FileNotFoundError, OSError):
                pass

        elif self._platform == Platform.WINDOWS:
            info["version"] = platform.version()
            win_ver = platform.win32_ver()
            if win_ver:
                info["name"] = f"Windows {win_ver[0]}"

        return info
