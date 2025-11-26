"""
Filesystem Validator.

PREREQ-003: Validates filesystem requirements including disk space,
permissions, and directory structure for ragged installation.
"""

import os
import shutil
from pathlib import Path
from typing import Any

from ragged.install.validation.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


# Disk space requirements (GB)
MIN_DISK_SPACE_GB = 2
RECOMMENDED_DISK_SPACE_GB = 10
WARN_DISK_SPACE_GB = 5


class FilesystemValidator(BaseValidator):
    """
    Validator for filesystem requirements.

    Checks:
    - Disk space availability
    - Write permissions for ragged directory
    - Directory ownership
    - Filesystem type compatibility
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise filesystem validator.

        Args:
            ragged_home: Path to ragged home directory. Defaults to ~/.ragged
        """
        self._ragged_home = ragged_home or (Path.home() / ".ragged")

    @property
    def category(self) -> str:
        """Return category name."""
        return "filesystem"

    def validate(self) -> list[ValidationResult]:
        """Run all filesystem validation checks."""
        results = []

        results.append(self._check_disk_space())
        results.append(self._check_write_permissions())
        results.append(self._check_directory_ownership())
        results.append(self._check_path_length())

        return results

    def _check_disk_space(self) -> ValidationResult:
        """Check available disk space."""
        try:
            usage = shutil.disk_usage(Path.home())
            available_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_percent = (usage.used / usage.total) * 100

            details: dict[str, Any] = {
                "available_gb": round(available_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 1),
                "path": str(Path.home()),
            }

            if available_gb < MIN_DISK_SPACE_GB:
                return self.create_result(
                    name="disk_space",
                    passed=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Insufficient disk space: {available_gb:.1f}GB available",
                    details=details,
                    fix_suggestion=(
                        f"Free up at least {MIN_DISK_SPACE_GB}GB of disk space. "
                        f"Currently only {available_gb:.1f}GB available."
                    ),
                )
            elif available_gb < WARN_DISK_SPACE_GB:
                return self.create_result(
                    name="disk_space",
                    passed=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Low disk space: {available_gb:.1f}GB available",
                    details=details,
                    fix_suggestion=(
                        f"Consider freeing disk space. {RECOMMENDED_DISK_SPACE_GB}GB+ recommended "
                        f"for models and documents."
                    ),
                )
            else:
                return self.create_result(
                    name="disk_space",
                    passed=True,
                    message=f"Disk space OK: {available_gb:.1f}GB available",
                    details=details,
                )

        except OSError as e:
            return self.create_result(
                name="disk_space",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Could not check disk space: {e}",
                fix_suggestion="Ensure you have at least 10GB free disk space.",
            )

    def _check_write_permissions(self) -> ValidationResult:
        """Check write permissions for ragged directory."""
        # Check if directory exists
        if self._ragged_home.exists():
            can_write = os.access(self._ragged_home, os.W_OK)

            if can_write:
                return self.create_result(
                    name="write_permissions",
                    passed=True,
                    message=f"Write access OK: {self._ragged_home}",
                    details={"path": str(self._ragged_home), "exists": True},
                )
            else:
                return self.create_result(
                    name="write_permissions",
                    passed=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Cannot write to: {self._ragged_home}",
                    details={"path": str(self._ragged_home), "exists": True},
                    fix_suggestion=(
                        f"Fix permissions: chmod u+w {self._ragged_home} or "
                        f"chown $USER {self._ragged_home}"
                    ),
                )
        else:
            # Directory doesn't exist - check if parent is writable
            parent = self._ragged_home.parent
            can_create = os.access(parent, os.W_OK)

            if can_create:
                return self.create_result(
                    name="write_permissions",
                    passed=True,
                    message=f"Can create directory: {self._ragged_home}",
                    details={"path": str(self._ragged_home), "exists": False},
                )
            else:
                return self.create_result(
                    name="write_permissions",
                    passed=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Cannot create directory: {self._ragged_home}",
                    details={"path": str(self._ragged_home), "exists": False},
                    fix_suggestion=(
                        f"Ensure write access to: {parent}. "
                        f"Or set RAGGED_HOME to a writable location."
                    ),
                )

    def _check_directory_ownership(self) -> ValidationResult:
        """Check that ragged directory is owned by current user."""
        if not self._ragged_home.exists():
            return self.create_result(
                name="directory_ownership",
                passed=True,
                message="Directory will be created with correct ownership",
                details={"path": str(self._ragged_home), "exists": False},
            )

        try:
            stat_info = self._ragged_home.stat()
            current_uid = os.getuid()
            owner_uid = stat_info.st_uid

            if owner_uid == current_uid:
                return self.create_result(
                    name="directory_ownership",
                    passed=True,
                    message=f"Directory ownership OK: {self._ragged_home}",
                    details={
                        "path": str(self._ragged_home),
                        "owner_uid": owner_uid,
                        "current_uid": current_uid,
                    },
                )
            else:
                # Check if owned by root
                if owner_uid == 0:
                    return self.create_result(
                        name="directory_ownership",
                        passed=False,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Directory owned by root: {self._ragged_home}",
                        details={
                            "path": str(self._ragged_home),
                            "owner_uid": owner_uid,
                            "current_uid": current_uid,
                        },
                        fix_suggestion=(
                            f"Change ownership: sudo chown -R $USER {self._ragged_home}"
                        ),
                    )
                else:
                    return self.create_result(
                        name="directory_ownership",
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Directory owned by different user: {self._ragged_home}",
                        details={
                            "path": str(self._ragged_home),
                            "owner_uid": owner_uid,
                            "current_uid": current_uid,
                        },
                        fix_suggestion=(
                            f"Change ownership: chown -R $USER {self._ragged_home}"
                        ),
                    )

        except (OSError, AttributeError) as e:
            return self.create_result(
                name="directory_ownership",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Could not check ownership: {e}",
            )

    def _check_path_length(self) -> ValidationResult:
        """Check that path length is within limits."""
        path_str = str(self._ragged_home)
        max_path_length = 260  # Windows MAX_PATH

        # On Windows, path length can be an issue
        if len(path_str) > max_path_length:
            return self.create_result(
                name="path_length",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Path too long ({len(path_str)} chars): {self._ragged_home}",
                details={
                    "path": path_str,
                    "length": len(path_str),
                    "max_length": max_path_length,
                },
                fix_suggestion=(
                    "Use a shorter installation path. "
                    "Set RAGGED_HOME to a shorter path."
                ),
            )

        return self.create_result(
            name="path_length",
            passed=True,
            message=f"Path length OK ({len(path_str)} chars)",
            details={"path": path_str, "length": len(path_str)},
        )

    def get_subdirectories(self) -> list[Path]:
        """Get list of ragged subdirectories that should exist."""
        return [
            self._ragged_home / "documents",
            self._ragged_home / "chromadb",
            self._ragged_home / "cache",
            self._ragged_home / "logs",
            self._ragged_home / "models",
            self._ragged_home / "backups",
        ]

    def estimate_required_space(
        self,
        num_documents: int = 100,
        model_size_gb: float = 5.0,
    ) -> float:
        """
        Estimate required disk space in GB.

        Args:
            num_documents: Expected number of documents.
            model_size_gb: Size of LLM models.

        Returns:
            Estimated disk space in GB.
        """
        # Base ragged installation
        base_gb = 0.5

        # Documents (estimate 10MB average)
        documents_gb = (num_documents * 10) / 1024

        # ChromaDB (roughly 2x document size for embeddings)
        chromadb_gb = documents_gb * 2

        # Models
        models_gb = model_size_gb

        # Cache and logs
        overhead_gb = 1.0

        return base_gb + documents_gb + chromadb_gb + models_gb + overhead_gb
