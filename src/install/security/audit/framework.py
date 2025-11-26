"""
Security Audit Framework.

INSTALL-SEC-004: Core audit framework for pre-install security checks.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AuditCategory(Enum):
    """Audit check categories."""

    SYSTEM_HARDENING = "system_hardening"
    NETWORK_SECURITY = "network_security"
    FILESYSTEM_SECURITY = "filesystem_security"
    USER_PERMISSIONS = "user_permissions"
    DEPENDENCIES = "dependencies"


class AuditSeverity(Enum):
    """Severity of audit findings."""

    CRITICAL = "critical"  # Must fix before installation
    HIGH = "high"  # Should fix (warn but allow proceed)
    MEDIUM = "medium"  # Recommend fixing
    LOW = "low"  # Informational


@dataclass
class AuditFinding:
    """Individual audit finding."""

    category: AuditCategory
    severity: AuditSeverity
    title: str
    message: str
    recommendation: str
    fix_command: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditResult:
    """Result of security audit."""

    timestamp: str
    findings: list[AuditFinding] = field(default_factory=list)
    passed: bool = True
    score: int = 100  # 0-100
    categories_checked: list[AuditCategory] = field(default_factory=list)
    duration_seconds: float = 0.0

    def add_finding(self, finding: AuditFinding) -> None:
        """Add a finding to results."""
        self.findings.append(finding)
        if finding.severity in (AuditSeverity.CRITICAL, AuditSeverity.HIGH):
            self.passed = False

    def has_critical_findings(self) -> bool:
        """Check if there are critical findings."""
        return any(
            f.severity == AuditSeverity.CRITICAL
            for f in self.findings
        )

    def get_findings_by_severity(
        self,
        severity: AuditSeverity,
    ) -> list[AuditFinding]:
        """Get findings by severity level."""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_category(
        self,
        category: AuditCategory,
    ) -> list[AuditFinding]:
        """Get findings by category."""
        return [f for f in self.findings if f.category == category]


class AuditCheck(ABC):
    """Base class for audit checks."""

    name: str = "base_check"
    category: AuditCategory = AuditCategory.SYSTEM_HARDENING

    @abstractmethod
    def run(self) -> list[AuditFinding]:
        """
        Run the audit check.

        Returns:
            List of findings (empty if no issues).
        """
        pass


class SecurityAuditor:
    """
    Security auditor for pre-install checks.

    Runs a suite of security checks and produces audit report.
    """

    def __init__(self) -> None:
        """Initialise auditor."""
        self._checks: list[AuditCheck] = []
        self._callbacks: list[Callable[[str], None]] = []

    def register_check(self, check: AuditCheck) -> None:
        """Register an audit check."""
        self._checks.append(check)

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add progress callback."""
        self._callbacks.append(callback)

    def _notify(self, message: str) -> None:
        """Notify callbacks."""
        for callback in self._callbacks:
            try:
                callback(message)
            except Exception:
                pass

    def run_audit(
        self,
        categories: list[AuditCategory] | None = None,
    ) -> AuditResult:
        """
        Run security audit.

        Args:
            categories: Categories to audit (all if None).

        Returns:
            AuditResult with findings.
        """
        import time

        start_time = time.time()

        result = AuditResult(
            timestamp=datetime.now().isoformat(),
        )

        # Filter checks by category
        checks = self._checks
        if categories:
            checks = [c for c in checks if c.category in categories]
            result.categories_checked = categories
        else:
            result.categories_checked = list(AuditCategory)

        self._notify(f"Running {len(checks)} security checks...")

        for check in checks:
            try:
                self._notify(f"Checking: {check.name}")
                findings = check.run()

                for finding in findings:
                    result.add_finding(finding)

            except Exception as e:
                logger.exception(f"Audit check {check.name} failed: {e}")
                result.add_finding(AuditFinding(
                    category=check.category,
                    severity=AuditSeverity.LOW,
                    title=f"Check failed: {check.name}",
                    message=f"Audit check failed with error: {e}",
                    recommendation="Check may need manual review",
                ))

        # Calculate score
        result.score = _calculate_score(result.findings)
        result.duration_seconds = time.time() - start_time

        return result


def _calculate_score(findings: list[AuditFinding]) -> int:
    """
    Calculate security score from findings.

    Args:
        findings: List of audit findings.

    Returns:
        Score from 0-100.
    """
    if not findings:
        return 100

    # Penalty points per severity
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


def run_security_audit(
    categories: list[AuditCategory] | None = None,
    callback: Callable[[str], None] | None = None,
) -> AuditResult:
    """
    Run comprehensive security audit.

    Args:
        categories: Categories to audit.
        callback: Progress callback.

    Returns:
        AuditResult with findings.
    """
    from ragged.install.security.audit.system import SystemHardeningAudit
    from ragged.install.security.audit.network import NetworkSecurityAudit

    auditor = SecurityAuditor()

    # Register standard checks
    auditor.register_check(SystemHardeningAudit())
    auditor.register_check(NetworkSecurityAudit())

    if callback:
        auditor.add_callback(callback)

    return auditor.run_audit(categories)
