"""
System Hardening Audit.

INSTALL-SEC-004: System hardening security checks.
"""

import logging
import os
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from ragged.install.security.audit.framework import (
    AuditCategory,
    AuditCheck,
    AuditFinding,
    AuditSeverity,
)

logger = logging.getLogger(__name__)


def check_firewall_status() -> AuditFinding | None:
    """
    Check if firewall is enabled.

    Returns:
        AuditFinding if issue found.
    """
    system = platform.system().lower()

    try:
        if system == "darwin":
            # macOS: Check firewall status
            result = subprocess.run(
                ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "disabled" in result.stdout.lower():
                return AuditFinding(
                    category=AuditCategory.SYSTEM_HARDENING,
                    severity=AuditSeverity.MEDIUM,
                    title="Firewall disabled",
                    message="macOS firewall is disabled",
                    recommendation="Enable firewall for network protection",
                    fix_command="sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on",
                )

        elif system == "linux":
            # Linux: Check ufw or firewalld
            # Try ufw first
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                if "inactive" in result.stdout.lower():
                    return AuditFinding(
                        category=AuditCategory.SYSTEM_HARDENING,
                        severity=AuditSeverity.MEDIUM,
                        title="Firewall disabled",
                        message="UFW firewall is inactive",
                        recommendation="Enable firewall for network protection",
                        fix_command="sudo ufw enable",
                    )
            else:
                # Try firewalld
                result = subprocess.run(
                    ["systemctl", "is-active", "firewalld"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout.strip() != "active":
                    return AuditFinding(
                        category=AuditCategory.SYSTEM_HARDENING,
                        severity=AuditSeverity.MEDIUM,
                        title="Firewall not running",
                        message="Neither UFW nor firewalld is active",
                        recommendation="Enable a firewall for network protection",
                        fix_command="sudo systemctl start firewalld",
                    )

        elif system == "windows":
            # Windows: Check Windows Firewall
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "off" in result.stdout.lower():
                return AuditFinding(
                    category=AuditCategory.SYSTEM_HARDENING,
                    severity=AuditSeverity.MEDIUM,
                    title="Firewall disabled",
                    message="Windows Firewall is disabled",
                    recommendation="Enable Windows Firewall",
                    fix_command="netsh advfirewall set allprofiles state on",
                )

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.debug(f"Firewall check error: {e}")

    return None


def check_selinux_status() -> AuditFinding | None:
    """
    Check SELinux status (Linux only).

    Returns:
        AuditFinding if issue found.
    """
    if platform.system().lower() != "linux":
        return None

    try:
        result = subprocess.run(
            ["getenforce"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            status = result.stdout.strip().lower()
            if status == "disabled":
                return AuditFinding(
                    category=AuditCategory.SYSTEM_HARDENING,
                    severity=AuditSeverity.LOW,
                    title="SELinux disabled",
                    message="SELinux is disabled (may be intentional)",
                    recommendation="Consider enabling SELinux for enhanced security",
                    fix_command="sudo setenforce 1",
                    details={"status": status},
                )

    except FileNotFoundError:
        # SELinux not installed (common on non-RHEL distros)
        pass
    except subprocess.SubprocessError as e:
        logger.debug(f"SELinux check error: {e}")

    return None


def check_system_updates() -> AuditFinding | None:
    """
    Check if system has been updated recently.

    Returns:
        AuditFinding if updates are stale.
    """
    system = platform.system().lower()
    max_days = 30

    try:
        if system == "darwin":
            # macOS: Check last software update
            result = subprocess.run(
                ["softwareupdate", "--history"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Parse output for last update date
            # This is a simplified check
            if result.returncode != 0:
                return None

        elif system == "linux":
            # Linux: Check /var/lib/apt/periodic/update-stamp or similar
            apt_stamp = Path("/var/lib/apt/periodic/update-stamp")
            if apt_stamp.exists():
                mtime = datetime.fromtimestamp(apt_stamp.stat().st_mtime)
                if datetime.now() - mtime > timedelta(days=max_days):
                    return AuditFinding(
                        category=AuditCategory.SYSTEM_HARDENING,
                        severity=AuditSeverity.LOW,
                        title="System updates stale",
                        message=f"Last update check was more than {max_days} days ago",
                        recommendation="Run system updates regularly",
                        fix_command="sudo apt update && sudo apt upgrade",
                        details={"last_update": mtime.isoformat()},
                    )

            # Check yum/dnf
            yum_history = Path("/var/log/yum.log")
            dnf_history = Path("/var/log/dnf.log")

            for log_file in [dnf_history, yum_history]:
                if log_file.exists():
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if datetime.now() - mtime > timedelta(days=max_days):
                        return AuditFinding(
                            category=AuditCategory.SYSTEM_HARDENING,
                            severity=AuditSeverity.LOW,
                            title="System updates stale",
                            message=f"Last update was more than {max_days} days ago",
                            recommendation="Run system updates regularly",
                            fix_command="sudo dnf upgrade" if log_file == dnf_history else "sudo yum update",
                        )

    except Exception as e:
        logger.debug(f"Update check error: {e}")

    return None


def check_root_usage() -> AuditFinding | None:
    """
    Check if running as root.

    Returns:
        AuditFinding if running as root.
    """
    if platform.system().lower() == "windows":
        # Check for admin on Windows
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if is_admin:
                return AuditFinding(
                    category=AuditCategory.USER_PERMISSIONS,
                    severity=AuditSeverity.MEDIUM,
                    title="Running as administrator",
                    message="Installation is running with administrator privileges",
                    recommendation="Consider running as regular user if possible",
                )
        except Exception:
            pass
        return None

    # Unix: Check UID
    if os.getuid() == 0:
        return AuditFinding(
            category=AuditCategory.USER_PERMISSIONS,
            severity=AuditSeverity.MEDIUM,
            title="Running as root",
            message="Installation is running as root user",
            recommendation="Consider running as regular user for better security isolation",
            details={"uid": 0, "euid": os.geteuid()},
        )

    return None


def check_sudo_passwordless() -> AuditFinding | None:
    """
    Check if sudo is passwordless (potential security issue).

    Returns:
        AuditFinding if sudo is passwordless.
    """
    if platform.system().lower() == "windows":
        return None

    try:
        # Try running sudo with -n (non-interactive)
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5,
        )

        if result.returncode == 0:
            return AuditFinding(
                category=AuditCategory.USER_PERMISSIONS,
                severity=AuditSeverity.LOW,
                title="Passwordless sudo",
                message="Sudo does not require password (may be intentional)",
                recommendation="Consider requiring password for sudo commands",
            )

    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return None


class SystemHardeningAudit(AuditCheck):
    """System hardening audit check."""

    name = "system_hardening"
    category = AuditCategory.SYSTEM_HARDENING

    def run(self) -> list[AuditFinding]:
        """Run system hardening checks."""
        findings: list[AuditFinding] = []

        # Run individual checks
        checks = [
            check_firewall_status,
            check_selinux_status,
            check_system_updates,
            check_root_usage,
            check_sudo_passwordless,
        ]

        for check in checks:
            try:
                finding = check()
                if finding:
                    findings.append(finding)
            except Exception as e:
                logger.debug(f"Check {check.__name__} failed: {e}")

        return findings
