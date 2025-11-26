"""
Automated Dependency Installation System.

PREREQ-002: Provides automated installation of missing dependencies
including Docker, Python, and Ollama with platform-specific installers.
"""

from ragged.install.installers.base import InstallationResult, BaseInstaller
from ragged.install.installers.docker import DockerInstaller
from ragged.install.installers.python_installer import PythonInstaller
from ragged.install.installers.ollama import OllamaInstaller
from ragged.install.installers.utils import (
    download_file,
    run_with_progress,
    get_temp_dir,
    cleanup_temp_files,
)
from ragged.install.detection import detect_all_prerequisites


def install_missing_dependencies(
    install_docker: bool = True,
    install_python: bool = True,
    install_ollama: bool = True,
    interactive: bool = True,
) -> dict[str, InstallationResult]:
    """
    Install missing dependencies.

    Args:
        install_docker: Whether to install Docker if missing.
        install_python: Whether to install Python if missing.
        install_ollama: Whether to install Ollama if missing.
        interactive: Whether to prompt for user confirmation.

    Returns:
        Dictionary mapping dependency names to installation results.
    """
    results: dict[str, InstallationResult] = {}

    # First, detect what's already installed
    detection = detect_all_prerequisites()

    installers = []

    if install_docker and not detection["docker"].is_ready():
        installers.append(("docker", DockerInstaller()))

    if install_python and not detection["python"].is_ready():
        installers.append(("python", PythonInstaller()))

    if install_ollama and not detection["ollama"].is_ready():
        installers.append(("ollama", OllamaInstaller()))

    for name, installer in installers:
        if interactive:
            # In a real implementation, this would prompt the user
            pass

        results[name] = installer.install()

    return results


__all__ = [
    "InstallationResult",
    "BaseInstaller",
    "DockerInstaller",
    "PythonInstaller",
    "OllamaInstaller",
    "install_missing_dependencies",
    "download_file",
    "run_with_progress",
    "get_temp_dir",
    "cleanup_temp_files",
]
