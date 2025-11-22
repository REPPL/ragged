"""Plugin security and sandboxing framework for ragged.

This module provides the security foundation for ragged's plugin ecosystem,
implementing sandboxing, permissions, audit logging, and validation.

Version: 0.4.0
"""

from ragged.plugins.audit import AuditEvent, AuditEventType, AuditLogger
from ragged.plugins.consent import ConsentManager, ConsentStatus
from ragged.plugins.permissions import (
    PermissionManager,
    PermissionType,
    PluginPermission,
    PluginPermissions,
)
from ragged.plugins.sandbox import PluginSandbox, SandboxConfig, SandboxViolation
from ragged.plugins.validation import PluginValidator, ValidationResult, ValidationSeverity

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
