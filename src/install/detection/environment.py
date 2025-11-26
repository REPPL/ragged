"""
Environment Detector.

PREREQ-001: Detects system environment including available ports, disk space,
filesystem permissions, OS version, and shell type.
"""

import os
import re
import socket
import shutil
from pathlib import Path

from ragged.install.detection.base import (
    BaseDetector,
    DetectionResult,
    DetectionStatus,
    Platform,
)


# Default ragged ports
RAGGED_PORTS = {
    "fastapi": 8000,
    "sveltekit": 5173,
    "chromadb": 8001,
    "ollama": 11434,
}

# Disk space requirements (in GB)
MIN_DISK_SPACE_GB = 2
RECOMMENDED_DISK_SPACE_GB = 10


class EnvironmentDetector(BaseDetector):
    """
    Detector for system environment.

    Detects:
    - Available ports for ragged services
    - Disk space availability
    - Filesystem permissions
    - Operating system and architecture
    - Shell type
    """

    def _do_detect(self) -> DetectionResult:
        """Perform environment detection."""
        issues: list[str] = []
        details: dict[str, object] = {}

        # Step 1: Check port availability
        port_info = self._check_ports()
        details["ports"] = port_info
        for port_name, info in port_info.items():
            if isinstance(info, dict) and not info.get("available", True):
                issues.append(
                    f"Port {info.get('port')} ({port_name}) is in use by: {info.get('process', 'unknown')}"
                )

        # Step 2: Check disk space
        disk_info = self._check_disk_space()
        details["disk"] = disk_info
        if isinstance(disk_info, dict):
            available_gb = disk_info.get("available_gb", 0)
            if available_gb < MIN_DISK_SPACE_GB:
                issues.append(
                    f"Insufficient disk space: {available_gb:.1f}GB available, "
                    f"minimum {MIN_DISK_SPACE_GB}GB required"
                )
            elif available_gb < RECOMMENDED_DISK_SPACE_GB:
                issues.append(
                    f"Low disk space: {available_gb:.1f}GB available, "
                    f"{RECOMMENDED_DISK_SPACE_GB}GB recommended"
                )

        # Step 3: Check filesystem permissions
        fs_info = self._check_filesystem_permissions()
        details["filesystem"] = fs_info
        if isinstance(fs_info, dict) and not fs_info.get("writable"):
            issues.append(f"Cannot write to ragged directory: {fs_info.get('path')}")

        # Step 4: Get OS information
        os_info = self._get_os_info()
        details["os"] = os_info

        # Step 5: Detect shell
        shell_info = self._detect_shell()
        details["shell"] = shell_info

        # Step 6: Check network connectivity
        network_info = self._check_network()
        details["network"] = network_info

        # Step 7: Get system resources
        system_info = self._get_system_resources()
        details["system"] = system_info

        # Check RAM recommendations
        if isinstance(system_info, dict):
            ram_gb = system_info.get("ram_gb", 0)
            if ram_gb < 4:
                issues.append(f"Low RAM: {ram_gb}GB detected, minimum 8GB recommended")
            elif ram_gb < 8:
                issues.append(
                    f"Limited RAM: {ram_gb}GB detected, 8-16GB recommended for optimal performance"
                )

        # Determine overall status
        critical_issues = [
            i
            for i in issues
            if "Insufficient disk" in i or "Cannot write" in i or "in use" in i
        ]

        if critical_issues:
            status = DetectionStatus.PARTIALLY_INSTALLED
        elif issues:
            status = DetectionStatus.PARTIALLY_INSTALLED
        else:
            status = DetectionStatus.INSTALLED

        return DetectionResult(
            status=status,
            installed=True,  # Environment is always "installed"
            issues=issues,
            details=details,
        )

    def _check_ports(self) -> dict[str, dict[str, object]]:
        """Check availability of ragged ports."""
        results: dict[str, dict[str, object]] = {}

        for name, port in RAGGED_PORTS.items():
            info: dict[str, object] = {
                "port": port,
                "available": True,
                "process": None,
            }

            # Try to bind to the port
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    info["available"] = True
            except OSError:
                info["available"] = False
                # Try to identify what's using the port
                info["process"] = self._identify_port_user(port)

            results[name] = info

        return results

    def _identify_port_user(self, port: int) -> str | None:
        """Identify what process is using a port."""
        if self.platform in (Platform.MACOS, Platform.LINUX):
            code, stdout, _ = self.run_command(
                ["lsof", "-i", f":{port}", "-t"],
                timeout=5.0,
            )
            if code == 0 and stdout.strip():
                pid = stdout.strip().split("\n")[0]
                # Get process name
                code2, name, _ = self.run_command(["ps", "-p", pid, "-o", "comm="])
                if code2 == 0:
                    return name.strip()
                return f"PID {pid}"

        elif self.platform == Platform.WINDOWS:
            code, stdout, _ = self.run_command(
                ["netstat", "-ano"],
                timeout=5.0,
            )
            if code == 0:
                for line in stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            return f"PID {parts[-1]}"

        return "unknown"

    def _check_disk_space(self) -> dict[str, object]:
        """Check available disk space."""
        result: dict[str, object] = {
            "path": str(Path.home()),
            "total_gb": 0,
            "used_gb": 0,
            "available_gb": 0,
            "percent_used": 0,
        }

        try:
            usage = shutil.disk_usage(Path.home())
            result["total_gb"] = round(usage.total / (1024**3), 2)
            result["used_gb"] = round(usage.used / (1024**3), 2)
            result["available_gb"] = round(usage.free / (1024**3), 2)
            result["percent_used"] = round((usage.used / usage.total) * 100, 1)
        except (OSError, PermissionError):
            pass

        return result

    def _check_filesystem_permissions(self) -> dict[str, object]:
        """Check filesystem permissions for ragged directory."""
        ragged_dir = Path.home() / ".ragged"
        result: dict[str, object] = {
            "path": str(ragged_dir),
            "exists": ragged_dir.exists(),
            "writable": False,
            "owner_match": False,
        }

        # Check if directory exists or can be created
        if ragged_dir.exists():
            result["writable"] = os.access(ragged_dir, os.W_OK)

            # Check ownership
            try:
                stat_info = ragged_dir.stat()
                result["owner_match"] = stat_info.st_uid == os.getuid()
            except (OSError, AttributeError):
                pass
        else:
            # Check if parent directory is writable
            result["writable"] = os.access(Path.home(), os.W_OK)

        return result

    def _get_os_info(self) -> dict[str, object]:
        """Get operating system information."""
        import platform as plat

        result: dict[str, object] = {
            "system": plat.system(),
            "release": plat.release(),
            "version": plat.version(),
            "machine": plat.machine(),
            "processor": plat.processor(),
            "platform": self.platform.value,
        }

        # Platform-specific version info
        if self.platform == Platform.MACOS:
            code, stdout, _ = self.run_command(["sw_vers", "-productVersion"])
            if code == 0:
                result["macos_version"] = stdout.strip()

        elif self.platform == Platform.LINUX:
            # Try to read /etc/os-release
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("NAME="):
                            result["distro_name"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("VERSION_ID="):
                            result["distro_version"] = line.split("=")[1].strip().strip('"')
            except (FileNotFoundError, PermissionError):
                pass

        elif self.platform == Platform.WINDOWS:
            result["windows_version"] = plat.win32_ver()[0]

        return result

    def _detect_shell(self) -> dict[str, object]:
        """Detect current shell."""
        result: dict[str, object] = {
            "shell": None,
            "path": None,
            "version": None,
        }

        # Check SHELL environment variable
        shell_path = os.environ.get("SHELL")
        if shell_path:
            result["path"] = shell_path
            result["shell"] = Path(shell_path).name

            # Get version
            code, stdout, _ = self.run_command([shell_path, "--version"])
            if code == 0:
                result["version"] = stdout.split("\n")[0]

        # On Windows, check for PowerShell or cmd
        if self.platform == Platform.WINDOWS:
            comspec = os.environ.get("ComSpec")
            if comspec:
                result["path"] = comspec
                result["shell"] = Path(comspec).name

        return result

    def _check_network(self) -> dict[str, object]:
        """Check network connectivity."""
        result: dict[str, object] = {
            "localhost_available": False,
            "internet_available": False,
        }

        # Check localhost
        try:
            with socket.create_connection(("localhost", 80), timeout=1):
                pass
        except (socket.error, socket.timeout):
            pass
        result["localhost_available"] = True  # localhost should always work

        # Check internet connectivity
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            result["internet_available"] = True
        except (socket.error, socket.timeout):
            result["internet_available"] = False

        return result

    def _get_system_resources(self) -> dict[str, object]:
        """Get system resource information."""
        result: dict[str, object] = {
            "cpu_count": os.cpu_count() or 1,
            "ram_gb": 0,
        }

        # Get RAM
        try:
            import psutil

            result["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
        except ImportError:
            # Fallback methods
            if self.platform == Platform.MACOS:
                code, stdout, _ = self.run_command(["sysctl", "-n", "hw.memsize"])
                if code == 0:
                    try:
                        result["ram_gb"] = round(int(stdout.strip()) / (1024**3), 1)
                    except ValueError:
                        pass

            elif self.platform == Platform.LINUX:
                try:
                    with open("/proc/meminfo") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                mem_kb = int(line.split()[1])
                                result["ram_gb"] = round(mem_kb / (1024**2), 1)
                                break
                except (FileNotFoundError, PermissionError, ValueError):
                    pass

        return result

    def get_available_port(self, start: int = 8000, end: int = 9000) -> int | None:
        """Find an available port in the given range."""
        for port in range(start, end):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue
        return None

    def get_ragged_home(self) -> Path:
        """Get ragged home directory path."""
        # Allow override via environment variable
        env_home = os.environ.get("RAGGED_HOME")
        if env_home:
            return Path(env_home)
        return Path.home() / ".ragged"
