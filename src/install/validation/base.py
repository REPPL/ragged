"""
Base Validator Abstract Class.

Provides the foundation for environment validators with common
result structures and severity levels.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(Enum):
    """Severity level of validation result."""

    INFO = "info"  # Informational, no action needed
    WARNING = "warning"  # Proceed with caution
    CRITICAL = "critical"  # Blocks installation


@dataclass
class ValidationResult:
    """
    Result of a single validation check.

    Attributes:
        name: Short identifier for the check.
        passed: Whether the check passed.
        severity: Severity level if failed.
        message: Human-readable description.
        details: Additional information.
        fix_suggestion: How to resolve the issue.
        category: Category for grouping results.
    """

    name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fix_suggestion: str | None = None
    category: str = "general"

    def is_blocking(self) -> bool:
        """Check if this result blocks installation."""
        return not self.passed and self.severity == ValidationSeverity.CRITICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "name": self.name,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "fix_suggestion": self.fix_suggestion,
            "category": self.category,
        }


class BaseValidator(ABC):
    """
    Abstract base class for environment validators.

    Subclasses implement specific validation checks.
    """

    @property
    @abstractmethod
    def category(self) -> str:
        """Return the category name for this validator."""
        ...

    @abstractmethod
    def validate(self) -> list[ValidationResult]:
        """
        Run all validation checks.

        Returns:
            List of validation results.
        """
        ...

    def create_result(
        self,
        name: str,
        passed: bool,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.WARNING,
        details: dict[str, Any] | None = None,
        fix_suggestion: str | None = None,
    ) -> ValidationResult:
        """
        Create a validation result with this validator's category.

        Args:
            name: Check name.
            passed: Whether check passed.
            message: Description message.
            severity: Severity if failed.
            details: Additional details.
            fix_suggestion: How to fix the issue.

        Returns:
            ValidationResult instance.
        """
        return ValidationResult(
            name=name,
            passed=passed,
            severity=severity if not passed else ValidationSeverity.INFO,
            message=message,
            details=details or {},
            fix_suggestion=fix_suggestion,
            category=self.category,
        )
