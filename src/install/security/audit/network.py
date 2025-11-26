"""
Network Security Audit.

INSTALL-SEC-004: Network security checks.
"""

import logging
import platform
import socket
import subprocess
from typing import Any

from ragged.install.security.audit.framework import (
    AuditCategory,
    AuditCheck,
    AuditFinding,
    AuditSeverity,
)

logger = logging.getLogger(__name__)

# Ports that ragged uses
RAGGED_PORTS = [8000, 5173, 8001, 11434]

# Sensitive ports to check for exposure
SENSITIVE_PORTS = {
    22: "SSH",
    23: "Telnet",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    27017: "MongoDB",
    2375: "Docker (unencrypted)",
    2376: "Docker (TLS)",
}


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a port is available.

    Args:
        port: Port number.
        host: Host to check.

    Returns:
        True if available, False if in use.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0
    except Exception:
        return True  # Assume available on error


def check_open_ports() -> list[AuditFinding]:
    """
    Check for open sensitive ports.

    Returns:
        List of findings for exposed ports.
    """
    findings: list[AuditFinding] = []

    for port, service in SENSITIVE_PORTS.items():
        if not check_port_available(port, "0.0.0.0"):
            # Port is listening on all interfaces
            severity = AuditSeverity.MEDIUM
            if port == 2375:  # Docker unencrypted is critical
                severity = AuditSeverity.HIGH

            findings.append(AuditFinding(
                category=AuditCategory.NETWORK_SECURITY,
                severity=severity,
                title=f"{service} exposed",
                message=f"Port {port} ({service}) appears to be listening",
                recommendation=f"Ensure {service} is properly secured or restricted to localhost",
                details={"port": port, "service": service},
            ))

    return findings


def check_exposed_services() -> list[AuditFinding]:
    """
    Check for services that should not be publicly accessible.

    Returns:
        List of findings for exposed services.
    """
    findings: list[AuditFinding] = []

    # Check Docker daemon exposure
    if not check_port_available(2375, "0.0.0.0"):
        findings.append(AuditFinding(
            category=AuditCategory.NETWORK_SECURITY,
            severity=AuditSeverity.CRITICAL,
            title="Docker daemon exposed",
            message="Docker daemon is accessible on port 2375 (unencrypted)",
            recommendation="Disable Docker TCP socket or use TLS authentication",
            fix_command='Edit /etc/docker/daemon.json to remove "hosts": ["tcp://0.0.0.0:2375"]',
        ))

    # Check if Redis is exposed without authentication
    if not check_port_available(6379, "0.0.0.0"):
        findings.append(AuditFinding(
            category=AuditCategory.NETWORK_SECURITY,
            severity=AuditSeverity.HIGH,
            title="Redis exposed",
            message="Redis is accessible on port 6379",
            recommendation="Restrict Redis to localhost or enable authentication",
            fix_command="Add 'bind 127.0.0.1' and 'requirepass' to redis.conf",
        ))

    return findings


def check_firewall_rules() -> list[AuditFinding]:
    """
    Check firewall rules for ragged ports.

    Returns:
        List of findings for firewall issues.
    """
    findings: list[AuditFinding] = []
    system = platform.system().lower()

    # Check if ragged ports are open externally
    for port in RAGGED_PORTS:
        if not check_port_available(port, "0.0.0.0"):
            findings.append(AuditFinding(
                category=AuditCategory.NETWORK_SECURITY,
                severity=AuditSeverity.LOW,
                title=f"Port {port} in use",
                message=f"Port {port} is currently in use (may conflict with ragged)",
                recommendation=f"Ensure port {port} is available for ragged",
                details={"port": port},
            ))

    return findings


def check_dns_configuration() -> AuditFinding | None:
    """
    Check DNS configuration for security issues.

    Returns:
        AuditFinding if issue found.
    """
    try:
        # Check if localhost resolves correctly
        ip = socket.gethostbyname("localhost")
        if ip not in ("127.0.0.1", "::1"):
            return AuditFinding(
                category=AuditCategory.NETWORK_SECURITY,
                severity=AuditSeverity.MEDIUM,
                title="Localhost resolution issue",
                message=f"localhost resolves to {ip} instead of 127.0.0.1",
                recommendation="Check /etc/hosts and DNS configuration",
            )

    except socket.gaierror:
        return AuditFinding(
            category=AuditCategory.NETWORK_SECURITY,
            severity=AuditSeverity.MEDIUM,
            title="DNS resolution failed",
            message="Cannot resolve 'localhost'",
            recommendation="Check /etc/hosts and DNS configuration",
        )

    return None


def get_network_interfaces() -> list[dict[str, Any]]:
    """
    Get network interface information.

    Returns:
        List of interface info dictionaries.
    """
    interfaces: list[dict[str, Any]] = []

    try:
        import psutil

        net_if = psutil.net_if_addrs()
        for name, addrs in net_if.items():
            iface = {"name": name, "addresses": []}
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    iface["addresses"].append({
                        "type": "IPv4",
                        "address": addr.address,
                    })
            if iface["addresses"]:
                interfaces.append(iface)

    except ImportError:
        # psutil not available, use basic method
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            interfaces.append({
                "name": "default",
                "addresses": [{"type": "IPv4", "address": ip}],
            })
        except Exception:
            pass

    return interfaces


class NetworkSecurityAudit(AuditCheck):
    """Network security audit check."""

    name = "network_security"
    category = AuditCategory.NETWORK_SECURITY

    def run(self) -> list[AuditFinding]:
        """Run network security checks."""
        findings: list[AuditFinding] = []

        # Run individual checks
        findings.extend(check_open_ports())
        findings.extend(check_exposed_services())
        findings.extend(check_firewall_rules())

        dns_finding = check_dns_configuration()
        if dns_finding:
            findings.append(dns_finding)

        return findings
