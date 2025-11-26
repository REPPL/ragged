"""
Security Audit Reporting.

INSTALL-SEC-004: Audit report generation and logging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ragged.install.security.audit.framework import (
    AuditCategory,
    AuditFinding,
    AuditResult,
    AuditSeverity,
)

logger = logging.getLogger(__name__)


def calculate_security_score(findings: list[AuditFinding]) -> int:
    """
    Calculate security score from findings.

    Args:
        findings: List of audit findings.

    Returns:
        Score from 0-100.
    """
    if not findings:
        return 100

    penalties = {
        AuditSeverity.CRITICAL: 30,
        AuditSeverity.HIGH: 15,
        AuditSeverity.MEDIUM: 5,
        AuditSeverity.LOW: 1,
    }

    total_penalty = sum(
        penalties.get(f.severity, 0)
        for f in findings
    )

    return max(0, 100 - total_penalty)


def format_audit_report(
    result: AuditResult,
    verbose: bool = False,
) -> str:
    """
    Format audit result as human-readable report.

    Args:
        result: Audit result to format.
        verbose: Include detailed information.

    Returns:
        Formatted report string.
    """
    lines: list[str] = []

    # Header
    lines.append("=" * 60)
    lines.append("  SECURITY AUDIT REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Score
    score_emoji = _get_score_emoji(result.score)
    lines.append(f"Security Score: {result.score}/100 {score_emoji}")
    lines.append(f"Status: {'PASSED' if result.passed else 'NEEDS ATTENTION'}")
    lines.append(f"Timestamp: {result.timestamp}")
    lines.append(f"Duration: {result.duration_seconds:.2f}s")
    lines.append("")

    # Summary by severity
    severity_counts = _count_by_severity(result.findings)
    lines.append("--- SUMMARY ---")
    for severity in AuditSeverity:
        count = severity_counts.get(severity, 0)
        icon = _get_severity_icon(severity)
        lines.append(f"  {icon} {severity.value.upper()}: {count}")
    lines.append("")

    # Findings by category
    if result.findings:
        lines.append("--- FINDINGS ---")
        lines.append("")

        # Sort by severity
        sorted_findings = sorted(
            result.findings,
            key=lambda f: list(AuditSeverity).index(f.severity),
        )

        for finding in sorted_findings:
            icon = _get_severity_icon(finding.severity)
            lines.append(f"{icon} [{finding.severity.value.upper()}] {finding.title}")
            lines.append(f"   {finding.message}")
            lines.append(f"   Recommendation: {finding.recommendation}")

            if finding.fix_command:
                lines.append(f"   Fix: {finding.fix_command}")

            if verbose and finding.details:
                lines.append(f"   Details: {json.dumps(finding.details)}")

            lines.append("")

    else:
        lines.append("--- NO ISSUES FOUND ---")
        lines.append("All security checks passed.")
        lines.append("")

    # Recommendations
    if result.has_critical_findings():
        lines.append("--- ACTION REQUIRED ---")
        lines.append("Critical issues must be resolved before proceeding.")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def _get_score_emoji(score: int) -> str:
    """Get emoji for score."""
    if score >= 90:
        return "(Excellent)"
    elif score >= 70:
        return "(Good)"
    elif score >= 50:
        return "(Fair)"
    else:
        return "(Needs Work)"


def _get_severity_icon(severity: AuditSeverity) -> str:
    """Get icon for severity level."""
    icons = {
        AuditSeverity.CRITICAL: "[!]",
        AuditSeverity.HIGH: "[H]",
        AuditSeverity.MEDIUM: "[M]",
        AuditSeverity.LOW: "[L]",
    }
    return icons.get(severity, "[?]")


def _count_by_severity(
    findings: list[AuditFinding],
) -> dict[AuditSeverity, int]:
    """Count findings by severity."""
    counts: dict[AuditSeverity, int] = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def save_audit_log(
    result: AuditResult,
    log_path: Path,
) -> None:
    """
    Save audit result to log file.

    Args:
        result: Audit result to save.
        log_path: Path to save log.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create log entry
    log_entry = {
        "timestamp": result.timestamp,
        "score": result.score,
        "passed": result.passed,
        "duration_seconds": result.duration_seconds,
        "categories_checked": [c.value for c in result.categories_checked],
        "findings": [
            {
                "category": f.category.value,
                "severity": f.severity.value,
                "title": f.title,
                "message": f.message,
                "recommendation": f.recommendation,
                "fix_command": f.fix_command,
                "details": f.details,
            }
            for f in result.findings
        ],
    }

    # Append to log file
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    logger.info(f"Audit log saved to {log_path}")


def export_audit_json(result: AuditResult) -> str:
    """
    Export audit result as JSON.

    Args:
        result: Audit result.

    Returns:
        JSON string.
    """
    data = {
        "timestamp": result.timestamp,
        "score": result.score,
        "passed": result.passed,
        "duration_seconds": result.duration_seconds,
        "categories_checked": [c.value for c in result.categories_checked],
        "findings": [
            {
                "category": f.category.value,
                "severity": f.severity.value,
                "title": f.title,
                "message": f.message,
                "recommendation": f.recommendation,
                "fix_command": f.fix_command,
                "details": f.details,
            }
            for f in result.findings
        ],
    }

    return json.dumps(data, indent=2)


def format_audit_markdown(result: AuditResult) -> str:
    """
    Format audit result as Markdown.

    Args:
        result: Audit result.

    Returns:
        Markdown string.
    """
    lines: list[str] = []

    lines.append("# Security Audit Report")
    lines.append("")
    lines.append(f"**Date:** {result.timestamp}")
    lines.append(f"**Score:** {result.score}/100")
    lines.append(f"**Status:** {'Passed' if result.passed else 'Needs Attention'}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")

    severity_counts = _count_by_severity(result.findings)
    for severity in AuditSeverity:
        count = severity_counts.get(severity, 0)
        lines.append(f"| {severity.value.upper()} | {count} |")

    lines.append("")

    # Findings
    if result.findings:
        lines.append("## Findings")
        lines.append("")

        for finding in result.findings:
            severity_badge = f"`{finding.severity.value.upper()}`"
            lines.append(f"### {severity_badge} {finding.title}")
            lines.append("")
            lines.append(finding.message)
            lines.append("")
            lines.append(f"**Recommendation:** {finding.recommendation}")

            if finding.fix_command:
                lines.append("")
                lines.append("**Fix:**")
                lines.append(f"```bash\n{finding.fix_command}\n```")

            lines.append("")

    else:
        lines.append("## No Issues Found")
        lines.append("")
        lines.append("All security checks passed successfully.")

    return "\n".join(lines)
