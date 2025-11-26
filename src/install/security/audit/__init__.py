"""
Security Audit Module.

INSTALL-SEC-004: Pre-install security audit automation.
"""

from ragged.install.security.audit.framework import (
    AuditCategory,
    AuditSeverity,
    AuditFinding,
    AuditResult,
    SecurityAuditor,
    run_security_audit,
)
from ragged.install.security.audit.system import (
    check_firewall_status,
    check_selinux_status,
    check_system_updates,
    check_root_usage,
    SystemHardeningAudit,
)
from ragged.install.security.audit.network import (
    check_open_ports,
    check_exposed_services,
    check_firewall_rules,
    NetworkSecurityAudit,
)
from ragged.install.security.audit.report import (
    format_audit_report,
    save_audit_log,
    calculate_security_score,
)


__all__ = [
    # Framework
    "AuditCategory",
    "AuditSeverity",
    "AuditFinding",
    "AuditResult",
    "SecurityAuditor",
    "run_security_audit",
    # System
    "check_firewall_status",
    "check_selinux_status",
    "check_system_updates",
    "check_root_usage",
    "SystemHardeningAudit",
    # Network
    "check_open_ports",
    "check_exposed_services",
    "check_firewall_rules",
    "NetworkSecurityAudit",
    # Report
    "format_audit_report",
    "save_audit_log",
    "calculate_security_score",
]
