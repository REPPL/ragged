"""
Installation Scaffolding System.

PREREQ-005: Creates directory structure, sets up Docker services,
runs initial setup, verifies installation, and provides uninstall capability.
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
from ragged.install.scaffolding.uninstall import uninstall_ragged


__all__ = [
    "create_directory_structure",
    "setup_docker_services",
    "DockerServiceManager",
    "run_initial_setup",
    "verify_installation",
    "VerificationResult",
    "uninstall_ragged",
]
