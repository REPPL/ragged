"""
Environment Validation System.

PREREQ-003: Validates environment readiness including ports, filesystem,
versions, and system resources before installation.
"""

from ragged.install.validation.base import (
    ValidationResult,
    ValidationSeverity,
    BaseValidator,
)
from ragged.install.validation.ports import PortValidator
from ragged.install.validation.filesystem import FilesystemValidator
from ragged.install.validation.versions import VersionValidator
from ragged.install.validation.system import SystemValidator
from ragged.install.validation.report import (
    generate_validation_report,
    ValidationReport,
)


def validate_environment() -> list[ValidationResult]:
    """
    Run all environment validations.

    Returns:
        List of validation results from all validators.
    """
    validators = [
        PortValidator(),
        FilesystemValidator(),
        VersionValidator(),
        SystemValidator(),
    ]

    results = []
    for validator in validators:
        results.extend(validator.validate())

    return results


__all__ = [
    "ValidationResult",
    "ValidationSeverity",
    "BaseValidator",
    "PortValidator",
    "FilesystemValidator",
    "VersionValidator",
    "SystemValidator",
    "validate_environment",
    "generate_validation_report",
    "ValidationReport",
]
