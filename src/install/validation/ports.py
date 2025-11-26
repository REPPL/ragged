"""
Port Availability Validator.

PREREQ-003: Validates that required ports are available for ragged services.
"""

import socket
import subprocess
from typing import Any

from ragged.install.detection.base import Platform, BaseDetector
from ragged.install.validation.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


# Required ports and their services
REQUIRED_PORTS = {
    8000: ("FastAPI Backend", "Backend API server"),
    5173: ("SvelteKit Dev", "Development WebUI server"),
    8001: ("ChromaDB", "Vector database"),
    11434: ("Ollama", "LLM inference server"),
}


class PortValidator(BaseValidator):
    """
    Validator for port availability.

    Checks that all required ports are available and identifies
    any processes using conflicting ports.
    """

    def __init__(self) -> None:
        """Initialise port validator."""
        self._platform = BaseDetector._detect_platform()

    @property
    def category(self) -> str:
        """Return category name."""
        return "ports"

    def validate(self) -> list[ValidationResult]:
        """Run all port validation checks."""
        results = []

        for port, (service, description) in REQUIRED_PORTS.items():
            result = self._check_port(port, service, description)
            results.append(result)

        return results

    def _check_port(
        self,
        port: int,
        service: str,
        description: str,
    ) -> ValidationResult:
        """Check if a specific port is available."""
        available = self._is_port_available(port)

        if available:
            return self.create_result(
                name=f"port_{port}",
                passed=True,
                message=f"Port {port} ({service}) is available",
                details={"port": port, "service": service},
            )

        # Port is in use - find out what's using it
        process_info = self._identify_port_user(port)

        return self.create_result(
            name=f"port_{port}",
            passed=False,
            severity=ValidationSeverity.CRITICAL,
            message=f"Port {port} ({service}) is in use",
            details={
                "port": port,
                "service": service,
                "description": description,
                "used_by": process_info,
            },
            fix_suggestion=self._get_fix_suggestion(port, process_info),
        )

    def _is_port_available(self, port: int) -> bool:
        """Check if port is available for binding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return True
        except OSError:
            return False

    def _identify_port_user(self, port: int) -> dict[str, Any]:
        """Identify what process is using a port."""
        result: dict[str, Any] = {
            "pid": None,
            "process_name": None,
            "command": None,
        }

        if self._platform in (Platform.MACOS, Platform.LINUX):
            result = self._identify_unix_port_user(port)
        elif self._platform == Platform.WINDOWS:
            result = self._identify_windows_port_user(port)

        return result

    def _identify_unix_port_user(self, port: int) -> dict[str, Any]:
        """Identify port user on Unix systems."""
        result: dict[str, Any] = {
            "pid": None,
            "process_name": None,
            "command": None,
        }

        try:
            # Use lsof to find process
            proc = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if proc.returncode == 0 and proc.stdout.strip():
                pid = proc.stdout.strip().split("\n")[0]
                result["pid"] = int(pid)

                # Get process name
                ps_proc = subprocess.run(
                    ["ps", "-p", pid, "-o", "comm="],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if ps_proc.returncode == 0:
                    result["process_name"] = ps_proc.stdout.strip()

                # Get full command
                cmd_proc = subprocess.run(
                    ["ps", "-p", pid, "-o", "args="],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if cmd_proc.returncode == 0:
                    result["command"] = cmd_proc.stdout.strip()

        except (subprocess.TimeoutExpired, OSError, ValueError):
            pass

        return result

    def _identify_windows_port_user(self, port: int) -> dict[str, Any]:
        """Identify port user on Windows."""
        result: dict[str, Any] = {
            "pid": None,
            "process_name": None,
            "command": None,
        }

        try:
            # Use netstat to find process
            proc = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if proc.returncode == 0:
                for line in proc.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            result["pid"] = int(pid)

                            # Get process name using tasklist
                            task_proc = subprocess.run(
                                [
                                    "tasklist",
                                    "/fi",
                                    f"PID eq {pid}",
                                    "/fo",
                                    "csv",
                                    "/nh",
                                ],
                                capture_output=True,
                                text=True,
                                timeout=5,
                                check=False,
                            )
                            if task_proc.returncode == 0:
                                parts_list = task_proc.stdout.strip().split(",")
                                if parts_list:
                                    result["process_name"] = parts_list[0].strip('"')
                            break

        except (subprocess.TimeoutExpired, OSError, ValueError):
            pass

        return result

    def _get_fix_suggestion(
        self,
        port: int,
        process_info: dict[str, Any],
    ) -> str:
        """Generate fix suggestion for port conflict."""
        pid = process_info.get("pid")
        name = process_info.get("process_name", "unknown")

        suggestions = []

        # Suggest stopping the conflicting process
        if pid:
            if self._platform in (Platform.MACOS, Platform.LINUX):
                suggestions.append(f"Stop the process: kill {pid}")
            else:
                suggestions.append(f"Stop the process: taskkill /PID {pid} /F")

        # Service-specific suggestions
        if name:
            name_lower = name.lower()
            if "docker" in name_lower:
                suggestions.append("Or stop Docker: docker-compose down")
            elif "ollama" in name_lower:
                suggestions.append("Or stop Ollama: ollama stop")
            elif "python" in name_lower or "uvicorn" in name_lower:
                suggestions.append("Or stop the Python server that's running")

        # Suggest using alternative port
        suggestions.append(f"Or configure ragged to use a different port instead of {port}")

        return "; ".join(suggestions)

    def find_alternative_port(
        self,
        preferred: int,
        search_range: int = 100,
    ) -> int | None:
        """
        Find an alternative available port near the preferred port.

        Args:
            preferred: Preferred port number.
            search_range: How many ports to check.

        Returns:
            Available port number or None if none found.
        """
        # First check the preferred port
        if self._is_port_available(preferred):
            return preferred

        # Search nearby ports
        for offset in range(1, search_range + 1):
            for candidate in [preferred + offset, preferred - offset]:
                if 1024 <= candidate <= 65535 and self._is_port_available(candidate):
                    return candidate

        return None
