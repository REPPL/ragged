"""
Installation Security Module.

INSTALL-SEC: Security hardening for the installation process.

Provides:
- Dependency verification (checksums, signatures)
- Secure configuration defaults
- Secret generation and management
- Security audit automation
- Vulnerability scanning
"""

from ragged.install.security.verification import (
    verify_checksum,
    verify_gpg_signature,
    VerificationResult,
    VerificationStatus,
    verify_download,
    DownloadVerifier,
    compute_file_hash,
)
from ragged.install.security.checksums import (
    DependencyChecksum,
    DEPENDENCY_CHECKSUMS,
    get_checksum,
    get_current_platform,
    update_checksums,
    load_checksums,
)
from ragged.install.security.secrets import (
    generate_jwt_secret,
    generate_admin_password,
    generate_api_key,
    generate_encryption_key,
    generate_fernet_key,
    SecretStrength,
    SecretValidation,
    validate_secret_strength,
    calculate_entropy,
    SecretStore,
    redact_secret,
)
from ragged.install.security.secure_defaults import (
    SecureDefaults,
    SecurityLevel,
    SecurityWarning,
    apply_secure_defaults,
    validate_security_config,
    is_config_secure,
    generate_secure_config,
    format_security_warnings,
)
from ragged.install.security.permissions import (
    PermissionLevel,
    PermissionIssue,
    set_secure_permissions,
    verify_permissions,
    fix_permissions,
    get_permission_mode,
    ensure_secure_directory,
    format_permission_report,
)
from ragged.install.security.audit import (
    AuditCategory,
    AuditSeverity,
    AuditFinding,
    AuditResult,
    SecurityAuditor,
    run_security_audit,
    SystemHardeningAudit,
    NetworkSecurityAudit,
    format_audit_report,
    save_audit_log,
    calculate_security_score,
)
from ragged.install.security.vuln_scan import (
    VulnSeverity,
    Vulnerability,
    VulnScanResult,
    scan_python_dependencies,
    scan_docker_images,
    format_vuln_report,
    run_full_scan,
)


__all__ = [
    # Verification (INSTALL-SEC-001)
    "verify_checksum",
    "verify_gpg_signature",
    "VerificationResult",
    "VerificationStatus",
    "verify_download",
    "DownloadVerifier",
    "compute_file_hash",
    # Checksums (INSTALL-SEC-001)
    "DependencyChecksum",
    "DEPENDENCY_CHECKSUMS",
    "get_checksum",
    "get_current_platform",
    "update_checksums",
    "load_checksums",
    # Secrets (INSTALL-SEC-003)
    "generate_jwt_secret",
    "generate_admin_password",
    "generate_api_key",
    "generate_encryption_key",
    "generate_fernet_key",
    "SecretStrength",
    "SecretValidation",
    "validate_secret_strength",
    "calculate_entropy",
    "SecretStore",
    "redact_secret",
    # Secure Defaults (INSTALL-SEC-002)
    "SecureDefaults",
    "SecurityLevel",
    "SecurityWarning",
    "apply_secure_defaults",
    "validate_security_config",
    "is_config_secure",
    "generate_secure_config",
    "format_security_warnings",
    # Permissions (INSTALL-SEC-002)
    "PermissionLevel",
    "PermissionIssue",
    "set_secure_permissions",
    "verify_permissions",
    "fix_permissions",
    "get_permission_mode",
    "ensure_secure_directory",
    "format_permission_report",
    # Audit (INSTALL-SEC-004)
    "AuditCategory",
    "AuditSeverity",
    "AuditFinding",
    "AuditResult",
    "SecurityAuditor",
    "run_security_audit",
    "SystemHardeningAudit",
    "NetworkSecurityAudit",
    "format_audit_report",
    "save_audit_log",
    "calculate_security_score",
    # Vulnerability Scanning (INSTALL-SEC-005)
    "VulnSeverity",
    "Vulnerability",
    "VulnScanResult",
    "scan_python_dependencies",
    "scan_docker_images",
    "format_vuln_report",
    "run_full_scan",
]
