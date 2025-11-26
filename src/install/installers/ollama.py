"""
Ollama Installer.

PREREQ-002: Automated Ollama installation for macOS, Linux, and Windows.
"""

import logging
import time
from pathlib import Path

from ragged.install.detection.base import Platform
from ragged.install.detection.ollama import OllamaDetector
from ragged.install.installers.base import (
    BaseInstaller,
    InstallationStep,
    InstallationError,
)
from ragged.install.installers.utils import (
    download_file,
    run_with_progress,
    run_with_sudo,
    wait_for_service,
    get_temp_dir,
)


logger = logging.getLogger(__name__)


# Ollama URLs
OLLAMA_INSTALL_SCRIPT = "https://ollama.ai/install.sh"
OLLAMA_MACOS_URL = "https://ollama.com/download/Ollama-darwin.zip"
OLLAMA_WINDOWS_URL = "https://ollama.com/download/OllamaSetup.exe"

# Default model to pull
DEFAULT_MODEL = "llama3.2:3b"


class OllamaInstaller(BaseInstaller):
    """
    Installer for Ollama.

    Installation methods by platform:
    - macOS: Official installer script or Homebrew
    - Linux: Official installer script
    - Windows: Official installer executable
    """

    def __init__(self, default_model: str = DEFAULT_MODEL) -> None:
        """
        Initialise Ollama installer.

        Args:
            default_model: Default model to pull after installation.
        """
        super().__init__()
        self._default_model = default_model

    def _create_detector(self) -> OllamaDetector:
        """Create Ollama detector."""
        return OllamaDetector()

    def _setup_steps(self) -> list[InstallationStep]:
        """Set up installation steps based on platform."""
        if self.platform == Platform.MACOS:
            return self._macos_steps()
        elif self.platform == Platform.LINUX:
            return self._linux_steps()
        elif self.platform == Platform.WINDOWS:
            return self._windows_steps()
        else:
            raise InstallationError(f"Unsupported platform: {self.platform}")

    def _macos_steps(self) -> list[InstallationStep]:
        """Installation steps for macOS."""
        return [
            InstallationStep(
                name="check_homebrew",
                description="Checking for Homebrew",
                action=self._check_homebrew,
            ),
            InstallationStep(
                name="install_ollama",
                description="Installing Ollama",
                action=self._install_ollama_macos,
                rollback=self._rollback_ollama_macos,
            ),
            InstallationStep(
                name="start_service",
                description="Starting Ollama service",
                action=self._start_ollama,
            ),
            InstallationStep(
                name="wait_for_service",
                description="Waiting for Ollama service",
                action=self._wait_for_service,
            ),
            InstallationStep(
                name="pull_model",
                description=f"Pulling default model ({self._default_model})",
                action=self._pull_default_model,
            ),
        ]

    def _linux_steps(self) -> list[InstallationStep]:
        """Installation steps for Linux."""
        return [
            InstallationStep(
                name="download_script",
                description="Downloading Ollama installer",
                action=self._download_install_script,
            ),
            InstallationStep(
                name="install_ollama",
                description="Installing Ollama",
                action=self._install_ollama_linux,
                rollback=self._rollback_ollama_linux,
            ),
            InstallationStep(
                name="start_service",
                description="Starting Ollama service",
                action=self._start_ollama_linux,
            ),
            InstallationStep(
                name="wait_for_service",
                description="Waiting for Ollama service",
                action=self._wait_for_service,
            ),
            InstallationStep(
                name="pull_model",
                description=f"Pulling default model ({self._default_model})",
                action=self._pull_default_model,
            ),
        ]

    def _windows_steps(self) -> list[InstallationStep]:
        """Installation steps for Windows."""
        return [
            InstallationStep(
                name="download_installer",
                description="Downloading Ollama installer",
                action=self._download_ollama_windows,
            ),
            InstallationStep(
                name="install_ollama",
                description="Installing Ollama",
                action=self._install_ollama_windows,
                rollback=self._rollback_ollama_windows,
            ),
            InstallationStep(
                name="wait_for_service",
                description="Waiting for Ollama service",
                action=self._wait_for_service,
            ),
            InstallationStep(
                name="pull_model",
                description=f"Pulling default model ({self._default_model})",
                action=self._pull_default_model,
            ),
        ]

    # macOS installation methods

    def _check_homebrew(self) -> bool:
        """Check if Homebrew is available."""
        code, _, _ = run_with_progress(
            ["brew", "--version"],
            "Checking Homebrew",
            timeout=10.0,
        )
        self._use_homebrew = code == 0
        return True

    def _install_ollama_macos(self) -> bool:
        """Install Ollama on macOS."""
        if self._use_homebrew:
            return self._install_ollama_homebrew()
        return self._install_ollama_script()

    def _install_ollama_homebrew(self) -> bool:
        """Install Ollama via Homebrew."""
        code, stdout, stderr = run_with_progress(
            ["brew", "install", "ollama"],
            "Installing Ollama via Homebrew",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"Homebrew installation failed: {stderr}")
            return False

        return True

    def _install_ollama_script(self) -> bool:
        """Install Ollama via official script."""
        # Download and run install script
        script_path = download_file(
            OLLAMA_INSTALL_SCRIPT,
            dest=get_temp_dir() / "install_ollama.sh",
        )

        code, stdout, stderr = run_with_progress(
            ["sh", str(script_path)],
            "Running Ollama install script",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"Ollama installation failed: {stderr}")
            return False

        return True

    def _rollback_ollama_macos(self) -> None:
        """Rollback Ollama installation on macOS."""
        if self._use_homebrew:
            run_with_progress(
                ["brew", "uninstall", "ollama"],
                "Rolling back Ollama installation",
            )
        else:
            run_with_progress(
                ["rm", "-f", "/usr/local/bin/ollama"],
                "Removing Ollama binary",
            )

    def _start_ollama(self) -> bool:
        """Start Ollama service on macOS."""
        if self._use_homebrew:
            code, _, _ = run_with_progress(
                ["brew", "services", "start", "ollama"],
                "Starting Ollama service",
            )
            return code == 0

        # Start Ollama in background
        code, _, _ = run_with_progress(
            ["ollama", "serve"],
            "Starting Ollama server",
            timeout=5.0,  # Will timeout as it runs in foreground
        )

        # The command will "fail" because it doesn't return, but that's OK
        return True

    # Linux installation methods

    def _download_install_script(self) -> bool:
        """Download Ollama install script."""
        self._install_script = download_file(
            OLLAMA_INSTALL_SCRIPT,
            dest=get_temp_dir() / "install_ollama.sh",
        )
        return self._install_script.exists()

    def _install_ollama_linux(self) -> bool:
        """Install Ollama on Linux."""
        code, stdout, stderr = run_with_progress(
            ["sh", str(self._install_script)],
            "Running Ollama install script",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"Ollama installation failed: {stderr}")
            return False

        return True

    def _rollback_ollama_linux(self) -> None:
        """Rollback Ollama installation on Linux."""
        run_with_sudo(
            ["rm", "-f", "/usr/local/bin/ollama"],
            "Removing Ollama binary",
        )
        run_with_sudo(
            ["systemctl", "stop", "ollama"],
            "Stopping Ollama service",
        )
        run_with_sudo(
            ["systemctl", "disable", "ollama"],
            "Disabling Ollama service",
        )

    def _start_ollama_linux(self) -> bool:
        """Start Ollama service on Linux."""
        # Enable and start systemd service if available
        run_with_sudo(
            ["systemctl", "enable", "ollama"],
            "Enabling Ollama service",
        )

        code, _, _ = run_with_sudo(
            ["systemctl", "start", "ollama"],
            "Starting Ollama service",
        )

        if code == 0:
            return True

        # Fallback: start manually
        logger.info("Starting Ollama manually...")
        run_with_progress(
            ["nohup", "ollama", "serve", "&"],
            "Starting Ollama server",
            timeout=5.0,
        )

        return True

    # Windows installation methods

    def _download_ollama_windows(self) -> bool:
        """Download Ollama installer for Windows."""
        self._installer_path = download_file(
            OLLAMA_WINDOWS_URL,
            dest=get_temp_dir() / "OllamaSetup.exe",
        )
        return self._installer_path.exists()

    def _install_ollama_windows(self) -> bool:
        """Install Ollama on Windows."""
        code, _, stderr = run_with_progress(
            [str(self._installer_path), "/S"],  # Silent install
            "Installing Ollama",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"Ollama installation failed: {stderr}")
            return False

        return True

    def _rollback_ollama_windows(self) -> None:
        """Rollback Ollama installation on Windows."""
        uninstaller = Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "unins000.exe"
        if uninstaller.exists():
            run_with_progress(
                [str(uninstaller), "/S"],
                "Uninstalling Ollama",
            )

    # Common methods

    def _wait_for_service(self) -> bool:
        """Wait for Ollama service to be ready."""
        logger.info("Waiting for Ollama service...")

        # Wait for port 11434
        if wait_for_service("localhost", 11434, timeout=60.0):
            return True

        logger.error("Ollama service did not start within 60 seconds")
        return False

    def _pull_default_model(self) -> bool:
        """Pull the default model."""
        logger.info(f"Pulling model: {self._default_model}")

        code, stdout, stderr = run_with_progress(
            ["ollama", "pull", self._default_model],
            f"Pulling {self._default_model}",
            timeout=1800.0,  # 30 minutes for large models
        )

        if code != 0:
            logger.warning(f"Failed to pull model: {stderr}")
            # Not a fatal error - user can pull models later
            return True

        return True

    def set_default_model(self, model: str) -> None:
        """Set the default model to pull."""
        self._default_model = model
