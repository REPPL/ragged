"""
ragged Installation System.

v0.8.0 - Installation Foundation & Prerequisites System
v0.8.1 - Interactive Installation Wizard

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
]
