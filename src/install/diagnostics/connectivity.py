"""
Connectivity Diagnostics.

REFINE-001: Diagnostics for port conflicts, network issues,
and firewall problems.
"""

import logging
import platform
import socket
import subprocess
from typing import Any

from ragged.install.diagnostics.framework import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticFix,
    DiagnosticResult,
    DiagnosticSeverity,
)


logger = logging.getLogger(__name__)


class PortConflictDetector(Diagnostic):
    """Detect port conflicts on required ports."""

    REQUIRED_PORTS = [
        (8000, "ragged API"),
        (5173, "WebUI"),
        (8001, "ChromaDB"),
        (11434, "Ollama"),
    ]

    @property
    def name(self) -> str:
        return "port_conflict"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.CONNECTIVITY

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []

        for port, service in self.REQUIRED_PORTS:
            result = self._check_port(port, service, context)
            if result:
                results.append(result)

        return results

    def _check_port(
        self,
        port: int,
        service: str,
        context: dict[str, Any],
    ) -> DiagnosticResult | None:
        """Check if a port is available."""
        # Try to bind to the port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result == 0:
                # Port is in use - find what's using it
                process_info = self._find_process_using_port(port)

                fixes = []
                if process_info.get("pid"):
                    pid = process_info["pid"]
                    fixes.append(DiagnosticFix(
                        description=f"Kill process {pid} using port {port}",
                        command=f"kill -9 {pid}",
                        auto_fixable=True,
                        requires_sudo=False,
                    ))

                fixes.append(DiagnosticFix(
                    description=f"Use alternative port for {service}",
                    command=f"# Edit config to use different port",
                    auto_fixable=False,
                ))

                return DiagnosticResult(
                    name=f"port_{port}_conflict",
                    category=DiagnosticCategory.CONNECTIVITY,
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Port {port} ({service}) is already in use",
                    root_cause=f"Process {process_info.get('name', 'unknown')} (PID: {process_info.get('pid', '?')}) is using port {port}",
                    details=process_info,
                    fixes=fixes,
                )

        except socket.error:
            # Port check failed - likely available
            pass

        return None

    def _find_process_using_port(self, port: int) -> dict[str, Any]:
        """Find process using a port."""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        parts = lines[1].split()
                        return {
                            "name": parts[0] if parts else "unknown",
                            "pid": int(parts[1]) if len(parts) > 1 else None,
                        }

            elif system == "Linux":
                result = subprocess.run(
                    ["ss", "-tlnp", f"sport = :{port}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout:
                    # Parse ss output
                    for line in result.stdout.split("\n"):
                        if f":{port}" in line:
                            # Extract PID from output
                            import re
                            match = re.search(r"pid=(\d+)", line)
                            if match:
                                pid = int(match.group(1))
                                return {"pid": pid, "name": "unknown"}

            elif system == "Windows":
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if f":{port}" in line and "LISTENING" in line:
                            parts = line.split()
                            if parts:
                                pid = int(parts[-1])
                                return {"pid": pid, "name": "unknown"}

        except Exception as e:
            logger.debug(f"Failed to find process on port {port}: {e}")

        return {"name": "unknown", "pid": None}


class NetworkDiagnostic(Diagnostic):
    """Diagnose network connectivity issues."""

    @property
    def name(self) -> str:
        return "network"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.CONNECTIVITY

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []

        # Check localhost resolution
        localhost_result = self._check_localhost()
        if localhost_result:
            results.append(localhost_result)

        # Check loopback interface
        loopback_result = self._check_loopback()
        if loopback_result:
            results.append(loopback_result)

        return results

    def _check_localhost(self) -> DiagnosticResult | None:
        """Check localhost resolution."""
        try:
            socket.gethostbyname("localhost")
            return None
        except socket.gaierror as e:
            return DiagnosticResult(
                name="localhost_resolution",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.CRITICAL,
                message="Cannot resolve 'localhost'",
                root_cause=f"DNS resolution failed: {e}",
                fixes=[
                    DiagnosticFix(
                        description="Add localhost to /etc/hosts",
                        command='echo "127.0.0.1 localhost" | sudo tee -a /etc/hosts',
                        auto_fixable=False,
                        requires_sudo=True,
                    ),
                ],
            )

    def _check_loopback(self) -> DiagnosticResult | None:
        """Check loopback interface."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.bind(("127.0.0.1", 0))
            sock.close()
            return None
        except socket.error as e:
            return DiagnosticResult(
                name="loopback_interface",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.CRITICAL,
                message="Loopback interface not working",
                root_cause=f"Cannot bind to 127.0.0.1: {e}",
                fixes=[
                    DiagnosticFix(
                        description="Check network interface configuration",
                        command="ifconfig lo0" if platform.system() == "Darwin" else "ip addr show lo",
                        auto_fixable=False,
                    ),
                ],
            )


class FirewallDiagnostic(Diagnostic):
    """Diagnose firewall issues."""

    @property
    def name(self) -> str:
        return "firewall"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.CONNECTIVITY

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []
        system = platform.system()

        if system == "Darwin":
            result = self._check_macos_firewall()
            if result:
                results.append(result)
        elif system == "Linux":
            result = self._check_linux_firewall()
            if result:
                results.append(result)

        return results

    def _check_macos_firewall(self) -> DiagnosticResult | None:
        """Check macOS firewall."""
        try:
            result = subprocess.run(
                ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if "enabled" in result.stdout.lower():
                return DiagnosticResult(
                    name="macos_firewall",
                    category=DiagnosticCategory.CONNECTIVITY,
                    severity=DiagnosticSeverity.INFO,
                    message="macOS firewall is enabled",
                    details={"state": "enabled"},
                    fixes=[
                        DiagnosticFix(
                            description="Allow ragged through firewall",
                            command="# Add ragged to firewall exceptions in System Preferences > Security",
                            auto_fixable=False,
                        ),
                    ],
                )

        except Exception:
            pass

        return None

    def _check_linux_firewall(self) -> DiagnosticResult | None:
        """Check Linux firewall (ufw or firewalld)."""
        # Check ufw
        try:
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "active" in result.stdout.lower():
                return DiagnosticResult(
                    name="ufw_firewall",
                    category=DiagnosticCategory.CONNECTIVITY,
                    severity=DiagnosticSeverity.INFO,
                    message="UFW firewall is active",
                    fixes=[
                        DiagnosticFix(
                            description="Allow ragged ports through UFW",
                            command="sudo ufw allow 8000/tcp && sudo ufw allow 5173/tcp && sudo ufw allow 8001/tcp",
                            auto_fixable=False,
                            requires_sudo=True,
                        ),
                    ],
                )
        except FileNotFoundError:
            pass

        # Check firewalld
        try:
            result = subprocess.run(
                ["firewall-cmd", "--state"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "running" in result.stdout.lower():
                return DiagnosticResult(
                    name="firewalld",
                    category=DiagnosticCategory.CONNECTIVITY,
                    severity=DiagnosticSeverity.INFO,
                    message="Firewalld is running",
                    fixes=[
                        DiagnosticFix(
                            description="Allow ragged ports through firewalld",
                            command="sudo firewall-cmd --add-port=8000/tcp --add-port=5173/tcp --add-port=8001/tcp --permanent && sudo firewall-cmd --reload",
                            auto_fixable=False,
                            requires_sudo=True,
                        ),
                    ],
                )
        except FileNotFoundError:
            pass

        return None


class ConnectivityDiagnostic(Diagnostic):
    """Combined connectivity diagnostic."""

    @property
    def name(self) -> str:
        return "connectivity"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.CONNECTIVITY

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []

        # Run all connectivity checks
        port_detector = PortConflictDetector()
        results.extend(port_detector.run(context))

        network_diag = NetworkDiagnostic()
        results.extend(network_diag.run(context))

        firewall_diag = FirewallDiagnostic()
        results.extend(firewall_diag.run(context))

        return results
