"""
Validation Report Generator.

PREREQ-003: Generates human-readable validation reports with
categorised results and fix suggestions.
"""

from dataclasses import dataclass, field
from typing import Any

from ragged.install.validation.base import (
    ValidationResult,
    ValidationSeverity,
)


@dataclass
class ValidationReport:
    """
    Comprehensive validation report.

    Attributes:
        results: All validation results.
        passed: Overall pass status.
        blocking_issues: Number of critical issues.
        warnings: Number of warning issues.
        total_checks: Total number of checks run.
        summary: Human-readable summary.
    """

    results: list[ValidationResult]
    passed: bool
    blocking_issues: int
    warnings: int
    total_checks: int
    summary: str
    categories: dict[str, list[ValidationResult]] = field(default_factory=dict)

    def can_proceed(self) -> bool:
        """Check if installation can proceed."""
        return self.blocking_issues == 0

    def get_fix_suggestions(self) -> list[str]:
        """Get all fix suggestions for failed checks."""
        suggestions = []
        for result in self.results:
            if not result.passed and result.fix_suggestion:
                suggestions.append(f"[{result.name}] {result.fix_suggestion}")
        return suggestions

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "passed": self.passed,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
            "total_checks": self.total_checks,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results],
            "categories": {
                cat: [r.to_dict() for r in results]
                for cat, results in self.categories.items()
            },
        }


def generate_validation_report(
    results: list[ValidationResult],
) -> ValidationReport:
    """
    Generate a comprehensive validation report.

    Args:
        results: List of validation results.

    Returns:
        ValidationReport with summary and categorised results.
    """
    # Categorise results
    categories: dict[str, list[ValidationResult]] = {}
    for result in results:
        if result.category not in categories:
            categories[result.category] = []
        categories[result.category].append(result)

    # Count issues
    blocking = sum(1 for r in results if r.is_blocking())
    warnings = sum(
        1 for r in results
        if not r.passed and r.severity == ValidationSeverity.WARNING
    )
    passed_count = sum(1 for r in results if r.passed)
    total = len(results)

    # Determine overall status
    overall_passed = blocking == 0

    # Generate summary
    summary = _generate_summary(
        passed_count,
        blocking,
        warnings,
        total,
        overall_passed,
    )

    return ValidationReport(
        results=results,
        passed=overall_passed,
        blocking_issues=blocking,
        warnings=warnings,
        total_checks=total,
        summary=summary,
        categories=categories,
    )


def _generate_summary(
    passed: int,
    blocking: int,
    warnings: int,
    total: int,
    overall_passed: bool,
) -> str:
    """Generate human-readable summary."""
    if overall_passed and warnings == 0:
        return (
            f"✅ All checks passed ({passed}/{total}). "
            "Environment is ready for ragged installation."
        )
    elif overall_passed:
        return (
            f"✅ Installation can proceed ({passed}/{total} passed). "
            f"⚠️  {warnings} warning(s) - review recommended."
        )
    else:
        return (
            f"❌ Installation blocked by {blocking} critical issue(s). "
            f"⚠️  {warnings} warning(s). "
            "Please resolve critical issues before proceeding."
        )


def format_validation_report(report: ValidationReport) -> str:
    """
    Format validation report as human-readable text.

    Args:
        report: ValidationReport to format.

    Returns:
        Formatted text report.
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("  RAGGED INSTALLATION VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    lines.append(report.summary)
    lines.append("")

    # Results by category
    for category, results in report.categories.items():
        lines.append(f"--- {category.upper()} ---")
        lines.append("")

        for result in results:
            status = "✅" if result.passed else ("❌" if result.is_blocking() else "⚠️")
            lines.append(f"{status} {result.message}")

            if not result.passed and result.fix_suggestion:
                lines.append(f"   Fix: {result.fix_suggestion}")

            if result.details:
                for key, value in result.details.items():
                    lines.append(f"   {key}: {value}")

        lines.append("")

    # Fix suggestions summary
    if not report.passed:
        lines.append("--- REQUIRED ACTIONS ---")
        lines.append("")
        for suggestion in report.get_fix_suggestions():
            lines.append(f"• {suggestion}")
        lines.append("")

    # Footer
    lines.append("=" * 60)

    if report.can_proceed():
        lines.append("  Ready to proceed with installation")
    else:
        lines.append("  Fix critical issues before proceeding")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_validation_report_json(report: ValidationReport) -> str:
    """
    Format validation report as JSON.

    Args:
        report: ValidationReport to format.

    Returns:
        JSON string.
    """
    import json

    return json.dumps(report.to_dict(), indent=2)


def format_validation_report_markdown(report: ValidationReport) -> str:
    """
    Format validation report as Markdown.

    Args:
        report: ValidationReport to format.

    Returns:
        Markdown string.
    """
    lines = []

    # Header
    lines.append("# Ragged Installation Validation Report")
    lines.append("")

    # Summary
    status_icon = "✅" if report.passed else "❌"
    lines.append(f"**Status:** {status_icon} {report.summary}")
    lines.append("")

    # Statistics
    lines.append("## Statistics")
    lines.append("")
    lines.append(f"- **Total Checks:** {report.total_checks}")
    lines.append(f"- **Passed:** {report.total_checks - report.blocking_issues - report.warnings}")
    lines.append(f"- **Warnings:** {report.warnings}")
    lines.append(f"- **Critical Issues:** {report.blocking_issues}")
    lines.append("")

    # Results by category
    lines.append("## Results")
    lines.append("")

    for category, results in report.categories.items():
        lines.append(f"### {category.title()}")
        lines.append("")

        lines.append("| Check | Status | Message |")
        lines.append("|-------|--------|---------|")

        for result in results:
            status = "✅" if result.passed else ("❌" if result.is_blocking() else "⚠️")
            message = result.message.replace("|", "\\|")
            lines.append(f"| {result.name} | {status} | {message} |")

        lines.append("")

    # Fix suggestions
    if not report.passed:
        lines.append("## Required Actions")
        lines.append("")

        for suggestion in report.get_fix_suggestions():
            lines.append(f"- {suggestion}")

        lines.append("")

    return "\n".join(lines)
