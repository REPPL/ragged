"""
Permission Diagnostics.

REFINE-001: Diagnostics for file permission issues,
ownership problems, and SELinux blocks.
"""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from ragged.install.diagnostics.framework import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticFix,
    DiagnosticResult,
    DiagnosticSeverity,
)


logger = logging.getLogger(__name__)


class FilePermissionChecker(Diagnostic):
    """Check file and directory permissions."""

    @property
    def name(self) -> str:
        return "file_permissions"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.PERMISSIONS

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []
        ragged_home = context.get("ragged_home", Path.home() / ".ragged")

        # Check ragged home permissions
        home_result = self._check_directory_permissions(ragged_home)
        if home_result:
            results.append(home_result)

        # Check for root-owned files
        root_result = self._check_root_ownership(ragged_home)
        if root_result:
            results.append(root_result)

        # Check .env file permissions
        env_result = self._check_env_permissions(ragged_home / ".env")
        if env_result:
            results.append(env_result)

        return results

    def _check_directory_permissions(
        self,
        path: Path,
    ) -> DiagnosticResult | None:
        """Check directory read/write permissions."""
        if not path.exists():
            return None

        # Check read access
        if not os.access(path, os.R_OK):
            return DiagnosticResult(
                name="home_read_access",
                category=DiagnosticCategory.PERMISSIONS,
                severity=DiagnosticSeverity.ERROR,
                message=f"Cannot read {path}",
                root_cause="Insufficient read permissions",
                fixes=[
                    DiagnosticFix(
                        description="Fix directory permissions",
                        command=f"chmod -R u+r {path}",
                        auto_fixable=True,
                    ),
                ],
            )

        # Check write access
        if not os.access(path, os.W_OK):
            return DiagnosticResult(
                name="home_write_access",
                category=DiagnosticCategory.PERMISSIONS,
                severity=DiagnosticSeverity.ERROR,
                message=f"Cannot write to {path}",
                root_cause="Insufficient write permissions",
                fixes=[
                    DiagnosticFix(
                        description="Fix directory permissions",
                        command=f"chmod -R u+w {path}",
                        auto_fixable=True,
                    ),
                ],
            )

        return None

    def _check_root_ownership(
        self,
        path: Path,
    ) -> DiagnosticResult | None:
        """Check for root-owned files (common mistake on Unix)."""
        if platform.system() == "Windows":
            return None

        if not path.exists():
            return None

        try:
            # Check if any files are owned by root
            root_files = []

            for item in path.rglob("*"):
                try:
                    stat = item.stat()
                    if stat.st_uid == 0:  # root
                        root_files.append(str(item))
                        if len(root_files) >= 5:  # Limit for display
                            break
                except OSError:
                    continue

            if root_files:
                return DiagnosticResult(
                    name="root_ownership",
                    category=DiagnosticCategory.PERMISSIONS,
                    severity=DiagnosticSeverity.ERROR,
                    message="Files owned by root found in ragged home",
                    root_cause="Files created with sudo or by root process",
                    details={"root_files": root_files},
                    fixes=[
                        DiagnosticFix(
                            description="Change ownership to current user",
                            command=f"sudo chown -R $USER:$USER {path}",
                            auto_fixable=True,
                            requires_sudo=True,
                        ),
                    ],
                )

        except Exception as e:
            logger.debug(f"Failed to check root ownership: {e}")

        return None

    def _check_env_permissions(
        self,
        path: Path,
    ) -> DiagnosticResult | None:
        """Check .env file has restrictive permissions."""
        if not path.exists():
            return None

        try:
            mode = path.stat().st_mode & 0o777

            if mode > 0o600:
                return DiagnosticResult(
                    name="env_permissions",
                    category=DiagnosticCategory.PERMISSIONS,
                    severity=DiagnosticSeverity.WARNING,
                    message=f".env file has permissive permissions: {oct(mode)}",
                    root_cause="Secrets may be readable by other users",
                    details={"current_mode": oct(mode), "recommended_mode": "0600"},
                    fixes=[
                        DiagnosticFix(
                            description="Restrict .env permissions",
                            command=f"chmod 600 {path}",
                            auto_fixable=True,
                        ),
                    ],
                )

        except OSError as e:
            logger.debug(f"Failed to check .env permissions: {e}")

        return None


class SELinuxDiagnostic(Diagnostic):
    """Diagnose SELinux issues on Linux."""

    @property
    def name(self) -> str:
        return "selinux"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.PERMISSIONS

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        if platform.system() != "Linux":
            return []

        results = []

        # Check SELinux status
        status_result = self._check_selinux_status()
        if status_result:
            results.append(status_result)

        # Check for recent denials
        denial_result = self._check_selinux_denials()
        if denial_result:
            results.append(denial_result)

        return results

    def _check_selinux_status(self) -> DiagnosticResult | None:
        """Check if SELinux is enforcing."""
        try:
            result = subprocess.run(
                ["getenforce"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                status = result.stdout.strip().lower()

                if status == "enforcing":
                    return DiagnosticResult(
                        name="selinux_enforcing",
                        category=DiagnosticCategory.PERMISSIONS,
                        severity=DiagnosticSeverity.INFO,
                        message="SELinux is enforcing",
                        details={"status": status},
                        fixes=[
                            DiagnosticFix(
                                description="Set SELinux to permissive (temporary)",
                                command="sudo setenforce 0",
                                auto_fixable=False,
                                requires_sudo=True,
                            ),
                        ],
                    )

        except FileNotFoundError:
            # SELinux not installed
            pass
        except Exception as e:
            logger.debug(f"Failed to check SELinux status: {e}")

        return None

    def _check_selinux_denials(self) -> DiagnosticResult | None:
        """Check for recent SELinux denials."""
        try:
            result = subprocess.run(
                ["ausearch", "-m", "avc", "-ts", "recent"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                # Check if any denials mention ragged
                denials = result.stdout.lower()
                if "ragged" in denials or "chromadb" in denials or "ollama" in denials:
                    return DiagnosticResult(
                        name="selinux_denials",
                        category=DiagnosticCategory.PERMISSIONS,
                        severity=DiagnosticSeverity.WARNING,
                        message="SELinux denials detected for ragged-related processes",
                        root_cause="SELinux policy blocking ragged operations",
                        fixes=[
                            DiagnosticFix(
                                description="Generate and apply SELinux policy",
                                command="sudo ausearch -c 'ragged' --raw | audit2allow -M ragged && sudo semodule -i ragged.pp",
                                auto_fixable=False,
                                requires_sudo=True,
                            ),
                        ],
                    )

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Failed to check SELinux denials: {e}")

        return None


class PermissionDiagnostic(Diagnostic):
    """Combined permission diagnostic."""

    @property
    def name(self) -> str:
        return "permissions"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.PERMISSIONS

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []

        file_checker = FilePermissionChecker()
        results.extend(file_checker.run(context))

        selinux_diag = SELinuxDiagnostic()
        results.extend(selinux_diag.run(context))

        return results
