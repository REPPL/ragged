"""
Diagnostics System.

REFINE-001: Comprehensive error diagnostic system for identifying
root causes and providing actionable fix suggestions.
"""

from ragged.install.diagnostics.framework import (
    DiagnosticPipeline,
    DiagnosticCategory,
    DiagnosticResult,
    run_diagnostics,
)
from ragged.install.diagnostics.connectivity import (
    ConnectivityDiagnostic,
    PortConflictDetector,
    NetworkDiagnostic,
    FirewallDiagnostic,
)
from ragged.install.diagnostics.permissions import (
    PermissionDiagnostic,
    FilePermissionChecker,
    SELinuxDiagnostic,
)
from ragged.install.diagnostics.resources import (
    ResourceDiagnostic,
    DiskSpaceDiagnostic,
    MemoryDiagnostic,
)
from ragged.install.diagnostics.report import (
    DiagnosticReport,
    format_diagnostic_report,
    generate_support_bundle,
)


__all__ = [
    # Framework
    "DiagnosticPipeline",
    "DiagnosticCategory",
    "DiagnosticResult",
    "run_diagnostics",
    # Connectivity
    "ConnectivityDiagnostic",
    "PortConflictDetector",
    "NetworkDiagnostic",
    "FirewallDiagnostic",
    # Permissions
    "PermissionDiagnostic",
    "FilePermissionChecker",
    "SELinuxDiagnostic",
    # Resources
    "ResourceDiagnostic",
    "DiskSpaceDiagnostic",
    "MemoryDiagnostic",
    # Reports
    "DiagnosticReport",
    "format_diagnostic_report",
    "generate_support_bundle",
]
