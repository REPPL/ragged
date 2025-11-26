"""
Recovery Reports.

REFINE-002: Generate reports for recovery attempts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ragged.install.recovery.framework import (
    RecoveryResult,
    RecoveryStatus,
)


@dataclass
class RecoveryReport:
    """Summary of recovery attempts."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    results: list[RecoveryResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def success_count(self) -> int:
        """Count of successful recoveries."""
        return sum(1 for r in self.results if r.status == RecoveryStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        """Count of failed recoveries."""
        return sum(1 for r in self.results if r.status == RecoveryStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        """Count of skipped recoveries."""
        return sum(1 for r in self.results if r.status == RecoveryStatus.SKIPPED)

    @property
    def all_succeeded(self) -> bool:
        """Check if all recoveries succeeded."""
        return self.failed_count == 0

    @property
    def requires_restart(self) -> bool:
        """Check if any recovery requires restart."""
        return any(r.requires_reboot or r.requires_logout for r in self.results)


def format_recovery_report(
    results: list[RecoveryResult],
) -> str:
    """
    Format recovery results as human-readable report.

    Args:
        results: Recovery results.

    Returns:
        Formatted report string.
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("  RECOVERY REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    success_count = sum(1 for r in results if r.status == RecoveryStatus.SUCCESS)
    failed_count = sum(1 for r in results if r.status == RecoveryStatus.FAILED)
    skipped_count = sum(1 for r in results if r.status == RecoveryStatus.SKIPPED)
    total_time = sum(r.duration_ms for r in results)

    if failed_count == 0:
        lines.append(f"Status: All {success_count} recoveries successful")
    else:
        lines.append(f"Status: {success_count} successful, {failed_count} failed, {skipped_count} skipped")

    lines.append(f"Total time: {total_time:.0f}ms")
    lines.append("")

    # Successful recoveries
    successful = [r for r in results if r.status == RecoveryStatus.SUCCESS]
    if successful:
        lines.append("--- SUCCESSFUL RECOVERIES ---")
        for result in successful:
            lines.append(f"  [OK] {result.action.value}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    lines.append(f"       {key}: {value}")
        lines.append("")

    # Failed recoveries
    failed = [r for r in results if r.status == RecoveryStatus.FAILED]
    if failed:
        lines.append("--- FAILED RECOVERIES ---")
        for result in failed:
            lines.append(f"  [X] {result.action.value}: {result.message}")
            if result.rollback_performed:
                lines.append("       (rollback performed)")
        lines.append("")

    # Skipped recoveries
    skipped = [r for r in results if r.status == RecoveryStatus.SKIPPED]
    if skipped:
        lines.append("--- SKIPPED ---")
        for result in skipped:
            lines.append(f"  [-] {result.action.value}: {result.message}")
        lines.append("")

    # Pending confirmation
    pending = [r for r in results if r.status == RecoveryStatus.NEEDS_CONFIRMATION]
    if pending:
        lines.append("--- PENDING CONFIRMATION ---")
        for result in pending:
            lines.append(f"  [?] {result.action.value}: {result.message}")
        lines.append("")
        lines.append("Run 'ragged doctor --fix' with confirmation to apply these fixes.")
        lines.append("")

    # Post-recovery actions
    requires_reboot = any(r.requires_reboot for r in results)
    requires_logout = any(r.requires_logout for r in results)

    if requires_reboot:
        lines.append("--- ACTION REQUIRED ---")
        lines.append("A system reboot is required to complete recovery.")
        lines.append("")
    elif requires_logout:
        lines.append("--- ACTION REQUIRED ---")
        lines.append("Log out and back in to complete recovery.")
        lines.append("")

    # Footer
    lines.append("=" * 60)

    return "\n".join(lines)


def format_recovery_summary(results: list[RecoveryResult]) -> str:
    """
    Format a brief recovery summary.

    Args:
        results: Recovery results.

    Returns:
        Brief summary string.
    """
    success_count = sum(1 for r in results if r.status == RecoveryStatus.SUCCESS)
    failed_count = sum(1 for r in results if r.status == RecoveryStatus.FAILED)

    if failed_count == 0:
        return f"Recovery complete: {success_count} issues fixed"
    else:
        return f"Recovery partial: {success_count} fixed, {failed_count} failed"
