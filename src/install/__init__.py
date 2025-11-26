"""
ragged Installation System.

v0.8.0 - Installation Foundation & Prerequisites System

This module provides comprehensive installation management for ragged:
- Prerequisite detection (Docker, Python, Ollama)
- Automated dependency installation
- Environment validation
- Configuration management
- Installation scaffolding
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
]
