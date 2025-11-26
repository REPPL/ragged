"""
Installation Scaffolding System.

PREREQ-005: Creates directory structure, sets up Docker services,
runs initial setup, verifies installation, and provides uninstall capability.

REFINE-005: Enhanced uninstall with interactive mode and data export.
"""

from ragged.install.scaffolding.directories import create_directory_structure
from ragged.install.scaffolding.docker_setup import (
    setup_docker_services,
    DockerServiceManager,
)
from ragged.install.scaffolding.initial_setup import run_initial_setup
from ragged.install.scaffolding.verification import (
    verify_installation,
    VerificationResult,
)
from ragged.install.scaffolding.uninstall import (
    uninstall_ragged,
    UninstallResult,
    UninstallMode,
    UninstallWizard,
    interactive_uninstall,
    get_uninstall_preview,
    format_uninstall_report,
)


__all__ = [
    # Directories
    "create_directory_structure",
    # Docker
    "setup_docker_services",
    "DockerServiceManager",
    # Setup
    "run_initial_setup",
    # Verification
    "verify_installation",
    "VerificationResult",
    # Uninstall
    "uninstall_ragged",
    "UninstallResult",
    "UninstallMode",
    "UninstallWizard",
    "interactive_uninstall",
    "get_uninstall_preview",
    "format_uninstall_report",
]
