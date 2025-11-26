"""
Doctor Command.

WIZARD-005: Diagnostic tool for troubleshooting ragged installations.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import logging
import subprocess


logger = logging.getLogger(__name__)


class DiagnosticLevel(Enum):
    """Diagnostic severity level."""

    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    level: DiagnosticLevel
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fix_command: str | None = None
    fix_available: bool = False


class Doctor:
    """
    Diagnostic tool for ragged.

    Runs comprehensive diagnostics and can auto-fix common issues.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise doctor.

        Args:
            ragged_home: Path to ragged home directory.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )

    def diagnose(self) -> list[DiagnosticResult]:
        """Run all diagnostics."""
        results = []

        # Installation checks
        results.extend(self._check_installation())

        # Service checks
        results.extend(self._check_services())

        # Configuration checks
        results.extend(self._check_configuration())

        # Resource checks
        results.extend(self._check_resources())

        # Network checks
        results.extend(self._check_network())

        return results

    def fix(self, results: list[DiagnosticResult]) -> list[tuple[str, bool, str]]:
        """
        Attempt to fix issues.

        Args:
            results: Diagnostic results to fix.

        Returns:
            List of (name, success, message) tuples.
        """
        fixes = []

        for result in results:
            if not result.fix_available or not result.fix_command:
                continue

            try:
                # Execute fix command
                proc = subprocess.run(
                    result.fix_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if proc.returncode == 0:
                    fixes.append((result.name, True, "Fixed successfully"))
                else:
                    fixes.append((result.name, False, proc.stderr or "Fix failed"))

            except subprocess.TimeoutExpired:
                fixes.append((result.name, False, "Fix timed out"))
            except Exception as e:
                fixes.append((result.name, False, str(e)))

        return fixes

    def _check_installation(self) -> list[DiagnosticResult]:
        """Check installation integrity."""
        results = []

        # Check ragged home exists
        if not self.ragged_home.exists():
            results.append(DiagnosticResult(
                name="ragged_home",
                level=DiagnosticLevel.CRITICAL,
                message=f"ragged home directory does not exist: {self.ragged_home}",
                fix_command=f"mkdir -p {self.ragged_home}",
                fix_available=True,
            ))
        else:
            results.append(DiagnosticResult(
                name="ragged_home",
                level=DiagnosticLevel.OK,
                message=f"ragged home: {self.ragged_home}",
            ))

        # Check required directories
        required_dirs = ["documents", "logs", "config", "data"]
        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = self.ragged_home / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            results.append(DiagnosticResult(
                name="directories",
                level=DiagnosticLevel.ERROR,
                message=f"Missing directories: {', '.join(missing_dirs)}",
                details={"missing": missing_dirs},
                fix_command=f"mkdir -p {' '.join(str(self.ragged_home / d) for d in missing_dirs)}",
                fix_available=True,
            ))
        else:
            results.append(DiagnosticResult(
                name="directories",
                level=DiagnosticLevel.OK,
                message="All required directories exist",
            ))

        # Check config file
        config_path = self.ragged_home / "config.yaml"
        if not config_path.exists():
            results.append(DiagnosticResult(
                name="config_file",
                level=DiagnosticLevel.ERROR,
                message="Configuration file missing",
                fix_command="ragged config --init",
                fix_available=True,
            ))
        else:
            # Validate config
            try:
                import yaml

                with open(config_path) as f:
                    yaml.safe_load(f)

                results.append(DiagnosticResult(
                    name="config_file",
                    level=DiagnosticLevel.OK,
                    message="Configuration file valid",
                ))
            except yaml.YAMLError as e:
                results.append(DiagnosticResult(
                    name="config_file",
                    level=DiagnosticLevel.ERROR,
                    message=f"Invalid YAML: {e}",
                ))

        # Check .env file
        env_path = self.ragged_home / ".env"
        if env_path.exists():
            mode = env_path.stat().st_mode & 0o777
            if mode > 0o600:
                results.append(DiagnosticResult(
                    name="env_permissions",
                    level=DiagnosticLevel.WARNING,
                    message=f".env has permissive permissions: {oct(mode)}",
                    fix_command=f"chmod 600 {env_path}",
                    fix_available=True,
                ))

        return results

    def _check_services(self) -> list[DiagnosticResult]:
        """Check service status."""
        results = []

        # Check Docker
        try:
            proc = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10,
            )
            if proc.returncode == 0:
                results.append(DiagnosticResult(
                    name="docker",
                    level=DiagnosticLevel.OK,
                    message="Docker is running",
                ))
            else:
                results.append(DiagnosticResult(
                    name="docker",
                    level=DiagnosticLevel.WARNING,
                    message="Docker daemon not running",
                    fix_command="open -a Docker" if self._is_macos() else "sudo systemctl start docker",
                    fix_available=True,
                ))
        except FileNotFoundError:
            results.append(DiagnosticResult(
                name="docker",
                level=DiagnosticLevel.INFO,
                message="Docker not installed (optional)",
            ))
        except subprocess.TimeoutExpired:
            results.append(DiagnosticResult(
                name="docker",
                level=DiagnosticLevel.WARNING,
                message="Docker check timed out",
            ))

        # Check Ollama
        try:
            import httpx

            response = httpx.get("http://localhost:11434/api/version", timeout=5.0)
            if response.status_code == 200:
                results.append(DiagnosticResult(
                    name="ollama",
                    level=DiagnosticLevel.OK,
                    message="Ollama is running",
                    details=response.json(),
                ))
            else:
                results.append(DiagnosticResult(
                    name="ollama",
                    level=DiagnosticLevel.ERROR,
                    message=f"Ollama error: {response.status_code}",
                ))
        except httpx.ConnectError:
            results.append(DiagnosticResult(
                name="ollama",
                level=DiagnosticLevel.ERROR,
                message="Ollama not running",
                fix_command="ollama serve &",
                fix_available=True,
            ))
        except Exception as e:
            results.append(DiagnosticResult(
                name="ollama",
                level=DiagnosticLevel.WARNING,
                message=f"Ollama check failed: {e}",
            ))

        return results

    def _check_configuration(self) -> list[DiagnosticResult]:
        """Check configuration validity."""
        results = []

        config_path = self.ragged_home / "config.yaml"
        if not config_path.exists():
            return results

        try:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            if not config:
                results.append(DiagnosticResult(
                    name="config_content",
                    level=DiagnosticLevel.ERROR,
                    message="Configuration file is empty",
                ))
                return results

            # Check required sections
            required_sections = ["server", "database", "llm"]
            missing = [s for s in required_sections if s not in config]

            if missing:
                results.append(DiagnosticResult(
                    name="config_sections",
                    level=DiagnosticLevel.WARNING,
                    message=f"Missing config sections: {', '.join(missing)}",
                ))
            else:
                results.append(DiagnosticResult(
                    name="config_sections",
                    level=DiagnosticLevel.OK,
                    message="All required config sections present",
                ))

            # Check port conflicts
            ports = []
            if "server" in config:
                ports.append(("API", config["server"].get("port", 8000)))
            if "webui" in config:
                ports.append(("WebUI", config["webui"].get("port", 5173)))
            if "database" in config:
                ports.append(("ChromaDB", config["database"].get("chromadb_port", 8001)))

            seen_ports = {}
            for name, port in ports:
                if port in seen_ports:
                    results.append(DiagnosticResult(
                        name="port_conflict",
                        level=DiagnosticLevel.ERROR,
                        message=f"Port {port} used by both {seen_ports[port]} and {name}",
                    ))
                seen_ports[port] = name

        except yaml.YAMLError as e:
            results.append(DiagnosticResult(
                name="config_yaml",
                level=DiagnosticLevel.ERROR,
                message=f"Invalid YAML: {e}",
            ))

        return results

    def _check_resources(self) -> list[DiagnosticResult]:
        """Check system resources."""
        results = []

        import shutil
        import psutil

        # Disk space
        try:
            usage = shutil.disk_usage(self.ragged_home)
            free_gb = usage.free / (1024**3)

            if free_gb < 1:
                results.append(DiagnosticResult(
                    name="disk_space",
                    level=DiagnosticLevel.CRITICAL,
                    message=f"Very low disk space: {free_gb:.1f}GB free",
                ))
            elif free_gb < 5:
                results.append(DiagnosticResult(
                    name="disk_space",
                    level=DiagnosticLevel.WARNING,
                    message=f"Low disk space: {free_gb:.1f}GB free",
                ))
            else:
                results.append(DiagnosticResult(
                    name="disk_space",
                    level=DiagnosticLevel.OK,
                    message=f"Disk space OK: {free_gb:.1f}GB free",
                ))
        except Exception as e:
            results.append(DiagnosticResult(
                name="disk_space",
                level=DiagnosticLevel.WARNING,
                message=f"Could not check disk: {e}",
            ))

        # Memory
        try:
            mem = psutil.virtual_memory()
            available_gb = mem.available / (1024**3)
            total_gb = mem.total / (1024**3)

            if available_gb < 2:
                results.append(DiagnosticResult(
                    name="memory",
                    level=DiagnosticLevel.WARNING,
                    message=f"Low memory: {available_gb:.1f}GB available of {total_gb:.1f}GB",
                ))
            else:
                results.append(DiagnosticResult(
                    name="memory",
                    level=DiagnosticLevel.OK,
                    message=f"Memory OK: {available_gb:.1f}GB available of {total_gb:.1f}GB",
                ))
        except Exception as e:
            results.append(DiagnosticResult(
                name="memory",
                level=DiagnosticLevel.INFO,
                message=f"Could not check memory: {e}",
            ))

        return results

    def _check_network(self) -> list[DiagnosticResult]:
        """Check network connectivity."""
        results = []

        import socket

        # Check localhost resolution
        try:
            socket.gethostbyname("localhost")
            results.append(DiagnosticResult(
                name="localhost",
                level=DiagnosticLevel.OK,
                message="localhost resolves correctly",
            ))
        except socket.gaierror:
            results.append(DiagnosticResult(
                name="localhost",
                level=DiagnosticLevel.ERROR,
                message="localhost does not resolve",
            ))

        # Check if key ports are available
        ports_to_check = [
            (8000, "API"),
            (5173, "WebUI"),
            (8001, "ChromaDB"),
            (11434, "Ollama"),
        ]

        for port, service in ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("127.0.0.1", port))
                sock.close()

                if result == 0:
                    results.append(DiagnosticResult(
                        name=f"port_{port}",
                        level=DiagnosticLevel.INFO,
                        message=f"Port {port} ({service}) is in use",
                    ))
            except Exception:
                pass

        return results

    def _is_macos(self) -> bool:
        """Check if running on macOS."""
        import platform

        return platform.system() == "Darwin"


def run_doctor(
    ragged_home: Path | None = None,
    fix: bool = False,
) -> tuple[list[DiagnosticResult], list[tuple[str, bool, str]]]:
    """
    Run doctor diagnostics.

    Args:
        ragged_home: Path to ragged home directory.
        fix: Whether to attempt fixes.

    Returns:
        Tuple of (diagnostics, fixes).
    """
    doctor = Doctor(ragged_home)
    diagnostics = doctor.diagnose()

    fixes = []
    if fix:
        # Only fix errors and warnings
        fixable = [
            d for d in diagnostics
            if d.fix_available and d.level in (
                DiagnosticLevel.ERROR,
                DiagnosticLevel.WARNING,
                DiagnosticLevel.CRITICAL,
            )
        ]
        fixes = doctor.fix(fixable)

    return diagnostics, fixes
