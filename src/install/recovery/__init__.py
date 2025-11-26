"""
Recovery System.

REFINE-002: Automated recovery strategies for common installation
and runtime failures.
"""

from ragged.install.recovery.framework import (
    RecoveryPipeline,
    RecoveryAction,
    RecoveryResult,
    RecoveryStrategy,
    run_recovery,
)
from ragged.install.recovery.services import (
    ServiceRecovery,
    restart_service,
    repair_corrupted_database,
)
from ragged.install.recovery.filesystem import (
    FilesystemRecovery,
    fix_permissions,
    recreate_directories,
    clear_cache,
)
from ragged.install.recovery.configuration import (
    ConfigurationRecovery,
    repair_config,
    regenerate_secrets,
)
from ragged.install.recovery.report import (
    RecoveryReport,
    format_recovery_report,
)


__all__ = [
    # Framework
    "RecoveryPipeline",
    "RecoveryAction",
    "RecoveryResult",
    "RecoveryStrategy",
    "run_recovery",
    # Services
    "ServiceRecovery",
    "restart_service",
    "repair_corrupted_database",
    # Filesystem
    "FilesystemRecovery",
    "fix_permissions",
    "recreate_directories",
    "clear_cache",
    # Configuration
    "ConfigurationRecovery",
    "repair_config",
    "regenerate_secrets",
    # Reports
    "RecoveryReport",
    "format_recovery_report",
]
