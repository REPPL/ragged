"""Plugin validation and security scanning.

Automated security checks for plugins before execution.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Individual validation issue."""

    severity: ValidationSeverity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of plugin validation."""

    passed: bool
    issues: List[ValidationIssue]
    score: float = 0.0  # 0.0 to 1.0

    def has_critical(self) -> bool:
        """Check if there are any critical issues."""
        return any(i.severity == ValidationSeverity.CRITICAL for i in self.issues)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)


class PluginValidator:
    """Validates plugins for security and safety."""

    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        (r"eval\s*\(", "Use of eval() is dangerous", ValidationSeverity.CRITICAL),
        (r"exec\s*\(", "Use of exec() is dangerous", ValidationSeverity.CRITICAL),
        (r"__import__\s*\(", "Dynamic imports may be unsafe", ValidationSeverity.WARNING),
        (r"os\.system\s*\(", "Direct system calls are restricted", ValidationSeverity.ERROR),
        (r"subprocess\.(call|run|Popen)", "Subprocess usage requires review", ValidationSeverity.WARNING),
        (r"open\s*\([^)]*['\"]w", "File writes require write:documents permission", ValidationSeverity.WARNING),
        (r"requests\.(get|post|put|delete)", "Network access requires network:api permission", ValidationSeverity.WARNING),
        (r"urllib\.request", "Network access requires network:api permission", ValidationSeverity.WARNING),
        (r"socket\.", "Raw socket usage not allowed", ValidationSeverity.CRITICAL),
        (r"rm\s+-rf", "Dangerous shell commands detected", ValidationSeverity.CRITICAL),
    ]

    def __init__(self):
        """Initialise validator."""
        pass

    def validate_plugin(self, plugin_path: Path) -> ValidationResult:
        """Validate a plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []

        # Check plugin structure
        if not plugin_path.is_dir():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message="Plugin path is not a directory",
                    file=str(plugin_path),
                )
            )
            return ValidationResult(passed=False, issues=issues, score=0.0)

        # Check for plugin manifest
        manifest_path = plugin_path / "plugin.toml"
        if not manifest_path.exists():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Missing plugin.toml manifest",
                    file=str(plugin_path),
                )
            )

        # Scan Python files for dangerous patterns
        python_files = list(plugin_path.glob("**/*.py"))
        for py_file in python_files:
            file_issues = self._scan_file(py_file)
            issues.extend(file_issues)

        # Calculate score
        score = self._calculate_score(issues)

        # Determine if passed
        passed = not (any(i.severity == ValidationSeverity.CRITICAL for i in issues))

        return ValidationResult(passed=passed, issues=issues, score=score)

    def _scan_file(self, file_path: Path) -> List[ValidationIssue]:
        """Scan a Python file for dangerous patterns.

        Args:
            file_path: Path to Python file

        Returns:
            List of validation issues found
        """
        issues: List[ValidationIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for pattern, message, severity in self.DANGEROUS_PATTERNS:
                    if re.search(pattern, line):
                        issues.append(
                            ValidationIssue(
                                severity=severity,
                                message=message,
                                file=str(file_path),
                                line=line_num,
                                code=line.strip(),
                            )
                        )

        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Failed to scan file: {e}",
                    file=str(file_path),
                )
            )

        return issues

    def _calculate_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate validation score based on issues.

        Args:
            issues: List of validation issues

        Returns:
            Score from 0.0 (many critical issues) to 1.0 (no issues)
        """
        if not issues:
            return 1.0

        # Weight issues by severity
        weights = {
            ValidationSeverity.INFO: 0.01,
            ValidationSeverity.WARNING: 0.05,
            ValidationSeverity.ERROR: 0.15,
            ValidationSeverity.CRITICAL: 0.50,
        }

        penalty = sum(weights.get(issue.severity, 0.0) for issue in issues)
        score = max(0.0, 1.0 - penalty)

        return score

    def validate_permissions(self, requested: List[str], manifest: Dict) -> ValidationResult:
        """Validate that requested permissions match manifest.

        Args:
            requested: List of requested permission strings
            manifest: Plugin manifest dictionary

        Returns:
            ValidationResult indicating if permissions are valid
        """
        issues: List[ValidationIssue] = []

        # Check if manifest declares permissions
        if "permissions" not in manifest:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Manifest missing [permissions] section",
                )
            )
            return ValidationResult(passed=False, issues=issues, score=0.0)

        # Check if requested permissions are declared
        manifest_required = set(manifest.get("permissions", {}).get("required", []))
        manifest_optional = set(manifest.get("permissions", {}).get("optional", []))
        manifest_all = manifest_required | manifest_optional

        for perm in requested:
            if perm not in manifest_all:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Permission '{perm}' not declared in manifest",
                    )
                )

        passed = len(issues) == 0
        score = 1.0 if passed else 0.0

        return ValidationResult(passed=passed, issues=issues, score=score)
