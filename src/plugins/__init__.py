"""Plugin security and sandboxing framework for ragged.

This module provides the security foundation for ragged's plugin ecosystem,
implementing sandboxing, permissions, audit logging, and validation.

Version: 0.4.0
"""

from ragged.plugins.permissions import (
    PluginPermission,
    PluginPermissions,
    PermissionType,
    PermissionManager,
)
from ragged.plugins.sandbox import PluginSandbox, SandboxConfig, SandboxViolation
from ragged.plugins.audit import AuditLogger, AuditEvent, AuditEventType
from ragged.plugins.validation import PluginValidator, ValidationResult, ValidationSeverity
from ragged.plugins.consent import ConsentManager, ConsentStatus

__all__ = [
    # Permissions
    "PluginPermission",
    "PluginPermissions",
    "PermissionType",
    "PermissionManager",
    # Sandbox
    "PluginSandbox",
    "SandboxConfig",
    "SandboxViolation",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    # Validation
    "PluginValidator",
    "ValidationResult",
    "ValidationSeverity",
    # Consent
    "ConsentManager",
    "ConsentStatus",
]

__version__ = "0.4.0"
