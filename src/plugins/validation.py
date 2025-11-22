"""Plugin validation and security scanning.

Automated security checks for plugins before execution.

SECURITY FIX (HIGH-1): Added strict manifest validation
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import toml

logger = logging.getLogger(__name__)

# SECURITY FIX (HIGH-1): Security constraints for plugin manifests
MAX_PERMISSIONS = 5  # Maximum permissions a plugin can request
MAX_DEPENDENCIES = 10  # Maximum dependencies a plugin can declare
MAX_NAME_LENGTH = 50  # Maximum length for plugin name
MAX_VERSION_LENGTH = 20  # Maximum length for version string
MAX_DESCRIPTION_LENGTH = 500  # Maximum length for description
ALLOWED_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")  # Alphanumeric, underscore, hyphen, dot
ALLOWED_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$")  # Semantic versioning


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
    file: str | None = None
    line: int | None = None
    code: str | None = None


@dataclass
class ValidationResult:
    """Result of plugin validation."""

    passed: bool
    issues: list[ValidationIssue]
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
        issues: list[ValidationIssue] = []

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

    def _scan_file(self, file_path: Path) -> list[ValidationIssue]:
        """Scan a Python file for dangerous patterns.

        Args:
            file_path: Path to Python file

        Returns:
            List of validation issues found
        """
        issues: list[ValidationIssue] = []

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

    def _calculate_score(self, issues: list[ValidationIssue]) -> float:
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

    def validate_manifest(self, manifest_path: Path) -> ValidationResult:
        """Validate plugin manifest structure and content.

        SECURITY FIX (HIGH-1): Strict manifest validation

        Args:
            manifest_path: Path to plugin.toml manifest file

        Returns:
            ValidationResult with any issues found
        """
        issues: list[ValidationIssue] = []

        # Check manifest exists
        if not manifest_path.exists():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message="Plugin manifest (plugin.toml) not found",
                    file=str(manifest_path),
                )
            )
            return ValidationResult(passed=False, issues=issues, score=0.0)

        try:
            # Parse TOML
            manifest = toml.load(manifest_path)
        except Exception as e:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Failed to parse plugin.toml: {e}",
                    file=str(manifest_path),
                )
            )
            return ValidationResult(passed=False, issues=issues, score=0.0)

        # Validate required sections
        required_sections = ["plugin", "permissions"]
        for section in required_sections:
            if section not in manifest:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Missing required section [{section}] in manifest",
                        file=str(manifest_path),
                    )
                )

        # Validate [plugin] section
        if "plugin" in manifest:
            plugin_section = manifest["plugin"]

            # Required fields in [plugin]
            required_fields = ["name", "version", "type", "description", "author"]
            for field in required_fields:
                if field not in plugin_section:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Missing required field '{field}' in [plugin] section",
                            file=str(manifest_path),
                        )
                    )

            # Validate name
            name = plugin_section.get("name", "")
            if not ALLOWED_NAME_PATTERN.match(name):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Plugin name '{name}' contains invalid characters. "
                                "Only alphanumeric, underscore, hyphen, and dot allowed.",
                        file=str(manifest_path),
                    )
                )
            if len(name) > MAX_NAME_LENGTH:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Plugin name '{name}' exceeds maximum length of {MAX_NAME_LENGTH}",
                        file=str(manifest_path),
                    )
                )

            # Validate version
            version = plugin_section.get("version", "")
            if not ALLOWED_VERSION_PATTERN.match(version):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Plugin version '{version}' must follow semantic versioning (e.g., 1.0.0)",
                        file=str(manifest_path),
                    )
                )
            if len(version) > MAX_VERSION_LENGTH:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Plugin version exceeds maximum length of {MAX_VERSION_LENGTH}",
                        file=str(manifest_path),
                    )
                )

            # Validate description length
            description = plugin_section.get("description", "")
            if len(description) > MAX_DESCRIPTION_LENGTH:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Description exceeds recommended length of {MAX_DESCRIPTION_LENGTH}",
                        file=str(manifest_path),
                    )
                )

            # Validate plugin type
            plugin_type = plugin_section.get("type", "")
            valid_types = ["embedder", "retriever", "processor", "command"]
            if plugin_type not in valid_types:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid plugin type '{plugin_type}'. Must be one of: {valid_types}",
                        file=str(manifest_path),
                    )
                )

        # Validate [permissions] section
        if "permissions" in manifest:
            perms = manifest["permissions"]

            # Count total permissions
            required_perms = perms.get("required", [])
            optional_perms = perms.get("optional", [])
            total_perms = len(required_perms) + len(optional_perms)

            if total_perms > MAX_PERMISSIONS:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Plugin requests {total_perms} permissions, "
                                f"exceeding maximum of {MAX_PERMISSIONS}",
                        file=str(manifest_path),
                    )
                )

            # Validate permission format
            valid_permission_pattern = re.compile(r"^[a-z]+:[a-z_]+$")
            for perm in required_perms + optional_perms:
                if not valid_permission_pattern.match(perm):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Invalid permission format '{perm}'. "
                                    "Must be 'category:permission' (e.g., 'read:documents')",
                            file=str(manifest_path),
                        )
                    )

        # Validate [dependencies] section if present
        if "dependencies" in manifest:
            dependencies = manifest["dependencies"]

            if len(dependencies) > MAX_DEPENDENCIES:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Plugin declares {len(dependencies)} dependencies, "
                                f"exceeding recommended maximum of {MAX_DEPENDENCIES}",
                        file=str(manifest_path),
                    )
                )

            # Check dependency version pinning
            for dep_name, dep_spec in dependencies.items():
                if dep_spec == "*" or not dep_spec:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Dependency '{dep_name}' not version-pinned. "
                                    "Recommend specific version for security.",
                            file=str(manifest_path),
                        )
                    )

        # Calculate score
        score = self._calculate_score(issues)
        passed = not any(i.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.ERROR) for i in issues)

        return ValidationResult(passed=passed, issues=issues, score=score)

    def validate_permissions(self, requested: list[str], manifest: dict) -> ValidationResult:
        """Validate that requested permissions match manifest.

        Args:
            requested: List of requested permission strings
            manifest: Plugin manifest dictionary

        Returns:
            ValidationResult indicating if permissions are valid
        """
        issues: list[ValidationIssue] = []

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
