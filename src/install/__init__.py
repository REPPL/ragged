"""
ragged Installation System.

v0.8.0 - Installation Foundation & Prerequisites System
v0.8.1 - Interactive Installation Wizard
v0.8.2 - Post-Launch Refinements & Error Recovery

This module provides comprehensive installation management for ragged:
- Prerequisite detection (Docker, Python, Ollama)
- Automated dependency installation
- Environment validation
- Configuration management
- Installation scaffolding
- Interactive installation wizard
- One-command bootstrap scripts
- Progress tracking
- Post-install verification
- Error diagnostics (v0.8.2)
- Automated recovery (v0.8.2)
- Health monitoring (v0.8.2)
- Upgrade & migrations (v0.8.2)
"""

from ragged.install.detection import (
    DetectionResult,
    BaseDetector,
    DockerDetector,
    PythonDetector,
    OllamaDetector,
    EnvironmentDetector,
    detect_all_prerequisites,
)
from ragged.install.installers import (
    InstallationResult,
    BaseInstaller,
    DockerInstaller,
    PythonInstaller,
    OllamaInstaller,
    install_missing_dependencies,
)
from ragged.install.validation import (
    ValidationResult,
    ValidationSeverity,
    PortValidator,
    FilesystemValidator,
    VersionValidator,
    SystemValidator,
    validate_environment,
    generate_validation_report,
)
from ragged.install.scaffolding import (
    create_directory_structure,
    setup_docker_services,
    run_initial_setup,
    verify_installation,
    uninstall_ragged,
    UninstallResult,
    UninstallMode,
    interactive_uninstall,
    get_uninstall_preview,
)
from ragged.install.scripts import (
    generate_bootstrap_script,
    BootstrapOptions,
)
from ragged.install.progress import (
    ProgressTracker,
    InstallationPhase,
    PhaseStatus,
    ProgressDisplay,
    create_progress_display,
)
from ragged.install.config_wizard import (
    ConfigWizard,
    ConfigWizardOptions,
    generate_config_from_dict,
    quick_configure,
)
from ragged.install.post_install import (
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
    run_health_checks,
    ServiceChecker,
    ServiceStatus,
    check_all_services,
    PostInstallSetup,
    run_post_install_setup,
    Doctor,
    DiagnosticResult,
    run_doctor,
)
# v0.8.2 - Diagnostics
from ragged.install.diagnostics import (
    DiagnosticCategory,
    DiagnosticSeverity,
    DiagnosticIssue,
    DiagnosticPipeline,
    run_diagnostics,
    generate_diagnostic_report,
    create_support_bundle,
)
# v0.8.2 - Recovery
from ragged.install.recovery import (
    RecoveryAction,
    RecoveryResult,
    RecoveryStrategy,
    RecoveryPipeline,
    auto_recover,
    format_recovery_report,
)
# v0.8.2 - Health Monitoring
from ragged.install.health import (
    HealthLevel,
    CheckCategory,
    HealthCheckSuite,
    ServiceHealth,
    HealthMonitor,
    MonitoringConfig,
    HealthDashboard,
    start_monitoring,
    stop_monitoring,
    display_health_dashboard,
)
# v0.8.2 - Upgrade & Migrations
from ragged.install.upgrade import (
    Upgrader,
    UpgradeStrategy,
    UpgradeResult,
    upgrade_ragged,
    check_for_updates,
    Migration,
    MigrationRunner,
    run_migrations,
)

__all__ = [
    # Detection
    "DetectionResult",
    "BaseDetector",
    "DockerDetector",
    "PythonDetector",
    "OllamaDetector",
    "EnvironmentDetector",
    "detect_all_prerequisites",
    # Installers
    "InstallationResult",
    "BaseInstaller",
    "DockerInstaller",
    "PythonInstaller",
    "OllamaInstaller",
    "install_missing_dependencies",
    # Validation
    "ValidationResult",
    "ValidationSeverity",
    "PortValidator",
    "FilesystemValidator",
    "VersionValidator",
    "SystemValidator",
    "validate_environment",
    "generate_validation_report",
    # Scaffolding
    "create_directory_structure",
    "setup_docker_services",
    "run_initial_setup",
    "verify_installation",
    "uninstall_ragged",
    "UninstallResult",
    "UninstallMode",
    "interactive_uninstall",
    "get_uninstall_preview",
    # Scripts (v0.8.1)
    "generate_bootstrap_script",
    "BootstrapOptions",
    # Progress (v0.8.1)
    "ProgressTracker",
    "InstallationPhase",
    "PhaseStatus",
    "ProgressDisplay",
    "create_progress_display",
    # Config Wizard (v0.8.1)
    "ConfigWizard",
    "ConfigWizardOptions",
    "generate_config_from_dict",
    "quick_configure",
    # Post-Install (v0.8.1)
    "HealthCheck",
    "HealthCheckResult",
    "HealthStatus",
    "run_health_checks",
    "ServiceChecker",
    "ServiceStatus",
    "check_all_services",
    "PostInstallSetup",
    "run_post_install_setup",
    "Doctor",
    "DiagnosticResult",
    "run_doctor",
    # Diagnostics (v0.8.2)
    "DiagnosticCategory",
    "DiagnosticSeverity",
    "DiagnosticIssue",
    "DiagnosticPipeline",
    "run_diagnostics",
    "generate_diagnostic_report",
    "create_support_bundle",
    # Recovery (v0.8.2)
    "RecoveryAction",
    "RecoveryResult",
    "RecoveryStrategy",
    "RecoveryPipeline",
    "auto_recover",
    "format_recovery_report",
    # Health Monitoring (v0.8.2)
    "HealthLevel",
    "CheckCategory",
    "HealthCheckSuite",
    "ServiceHealth",
    "HealthMonitor",
    "MonitoringConfig",
    "HealthDashboard",
    "start_monitoring",
    "stop_monitoring",
    "display_health_dashboard",
    # Upgrade & Migrations (v0.8.2)
    "Upgrader",
    "UpgradeStrategy",
    "UpgradeResult",
    "upgrade_ragged",
    "check_for_updates",
    "Migration",
    "MigrationRunner",
    "run_migrations",
]
