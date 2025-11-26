"""
Docker Installer.

PREREQ-002: Automated Docker installation for macOS, Linux, and Windows.
Supports Docker Desktop and Docker Engine installation methods.
"""

import logging
import time
from pathlib import Path

from ragged.install.detection.base import Platform
from ragged.install.detection.docker import DockerDetector
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


# Docker download URLs
DOCKER_DESKTOP_MACOS_INTEL = (
    "https://desktop.docker.com/mac/main/amd64/Docker.dmg"
)
DOCKER_DESKTOP_MACOS_ARM = (
    "https://desktop.docker.com/mac/main/arm64/Docker.dmg"
)
DOCKER_DESKTOP_WINDOWS = (
    "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
)
DOCKER_INSTALL_SCRIPT = "https://get.docker.com"


class DockerInstaller(BaseInstaller):
    """
    Installer for Docker.

    Installation methods by platform:
    - macOS: Docker Desktop via DMG or Homebrew
    - Linux: Docker Engine via official script
    - Windows: Docker Desktop via installer
    """

    def _create_detector(self) -> DockerDetector:
        """Create Docker detector."""
        return DockerDetector()

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
                name="install_docker",
                description="Installing Docker Desktop",
                action=self._install_docker_macos,
                rollback=self._rollback_docker_macos,
            ),
            InstallationStep(
                name="start_docker",
                description="Starting Docker Desktop",
                action=self._start_docker_macos,
            ),
            InstallationStep(
                name="wait_for_daemon",
                description="Waiting for Docker daemon",
                action=self._wait_for_daemon,
            ),
        ]

    def _linux_steps(self) -> list[InstallationStep]:
        """Installation steps for Linux."""
        return [
            InstallationStep(
                name="detect_distro",
                description="Detecting Linux distribution",
                action=self._detect_linux_distro,
            ),
            InstallationStep(
                name="install_docker",
                description="Installing Docker Engine",
                action=self._install_docker_linux,
                rollback=self._rollback_docker_linux,
            ),
            InstallationStep(
                name="configure_user",
                description="Adding user to docker group",
                action=self._configure_docker_user,
            ),
            InstallationStep(
                name="start_docker",
                description="Starting Docker service",
                action=self._start_docker_linux,
            ),
            InstallationStep(
                name="wait_for_daemon",
                description="Waiting for Docker daemon",
                action=self._wait_for_daemon,
            ),
        ]

    def _windows_steps(self) -> list[InstallationStep]:
        """Installation steps for Windows."""
        return [
            InstallationStep(
                name="check_wsl",
                description="Checking WSL 2 status",
                action=self._check_wsl,
            ),
            InstallationStep(
                name="download_installer",
                description="Downloading Docker Desktop installer",
                action=self._download_docker_windows,
            ),
            InstallationStep(
                name="install_docker",
                description="Installing Docker Desktop",
                action=self._install_docker_windows,
                rollback=self._rollback_docker_windows,
            ),
            InstallationStep(
                name="wait_for_daemon",
                description="Waiting for Docker daemon",
                action=self._wait_for_daemon,
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
        return True  # Always succeed, just determines method

    def _install_docker_macos(self) -> bool:
        """Install Docker on macOS."""
        if self._use_homebrew:
            return self._install_docker_homebrew()
        return self._install_docker_dmg()

    def _install_docker_homebrew(self) -> bool:
        """Install Docker via Homebrew."""
        code, stdout, stderr = run_with_progress(
            ["brew", "install", "--cask", "docker"],
            "Installing Docker Desktop via Homebrew",
            timeout=600.0,
        )

        if code != 0:
            logger.error(f"Homebrew installation failed: {stderr}")
            return False

        return True

    def _install_docker_dmg(self) -> bool:
        """Install Docker via DMG download."""
        import platform

        # Determine architecture
        arch = platform.machine()
        url = DOCKER_DESKTOP_MACOS_ARM if arch == "arm64" else DOCKER_DESKTOP_MACOS_INTEL

        # Download DMG
        dmg_path = download_file(url)

        # Mount DMG
        mount_point = get_temp_dir() / "docker_mount"
        mount_point.mkdir(exist_ok=True)

        code, _, _ = run_with_progress(
            ["hdiutil", "attach", str(dmg_path), "-mountpoint", str(mount_point)],
            "Mounting Docker Desktop DMG",
        )

        if code != 0:
            return False

        try:
            # Copy to Applications
            app_path = mount_point / "Docker.app"
            if app_path.exists():
                code, _, _ = run_with_progress(
                    ["cp", "-R", str(app_path), "/Applications/"],
                    "Installing Docker.app",
                )
                if code != 0:
                    return False
        finally:
            # Unmount
            run_with_progress(
                ["hdiutil", "detach", str(mount_point)],
                "Unmounting DMG",
            )

        return True

    def _rollback_docker_macos(self) -> None:
        """Rollback Docker installation on macOS."""
        if self._use_homebrew:
            run_with_progress(
                ["brew", "uninstall", "--cask", "docker"],
                "Rolling back Docker installation",
            )
        else:
            run_with_progress(
                ["rm", "-rf", "/Applications/Docker.app"],
                "Removing Docker.app",
            )

    def _start_docker_macos(self) -> bool:
        """Start Docker Desktop on macOS."""
        code, _, _ = run_with_progress(
            ["open", "-a", "Docker"],
            "Starting Docker Desktop",
        )
        return code == 0

    # Linux installation methods

    def _detect_linux_distro(self) -> bool:
        """Detect Linux distribution."""
        self._linux_distro = "unknown"
        self._linux_version = "unknown"

        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        self._linux_distro = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        self._linux_version = line.split("=")[1].strip().strip('"')
        except FileNotFoundError:
            pass

        logger.info(f"Detected: {self._linux_distro} {self._linux_version}")
        return True

    def _install_docker_linux(self) -> bool:
        """Install Docker on Linux."""
        # Download and run official installation script
        script_path = download_file(DOCKER_INSTALL_SCRIPT, dest=get_temp_dir() / "get-docker.sh")

        code, stdout, stderr = run_with_sudo(
            ["sh", str(script_path)],
            "Running Docker installation script",
            timeout=600.0,
        )

        if code != 0:
            logger.error(f"Docker installation failed: {stderr}")
            return False

        return True

    def _rollback_docker_linux(self) -> None:
        """Rollback Docker installation on Linux."""
        if self._linux_distro in ("ubuntu", "debian"):
            run_with_sudo(
                ["apt-get", "remove", "-y", "docker-ce", "docker-ce-cli", "containerd.io"],
                "Removing Docker packages",
            )
        elif self._linux_distro in ("fedora", "rhel", "centos"):
            run_with_sudo(
                ["dnf", "remove", "-y", "docker-ce", "docker-ce-cli", "containerd.io"],
                "Removing Docker packages",
            )

    def _configure_docker_user(self) -> bool:
        """Add current user to docker group."""
        import os
        import pwd

        username = pwd.getpwuid(os.getuid()).pw_name

        code, _, _ = run_with_sudo(
            ["usermod", "-aG", "docker", username],
            f"Adding {username} to docker group",
        )

        if code != 0:
            logger.warning("Failed to add user to docker group")
            # Not a fatal error - user can still use sudo

        return True

    def _start_docker_linux(self) -> bool:
        """Start Docker service on Linux."""
        # Enable and start systemd service
        run_with_sudo(
            ["systemctl", "enable", "docker"],
            "Enabling Docker service",
        )

        code, _, _ = run_with_sudo(
            ["systemctl", "start", "docker"],
            "Starting Docker service",
        )

        return code == 0

    # Windows installation methods

    def _check_wsl(self) -> bool:
        """Check WSL 2 status on Windows."""
        code, stdout, _ = run_with_progress(
            ["wsl", "--status"],
            "Checking WSL status",
            timeout=30.0,
        )

        self._wsl_available = code == 0 and "WSL 2" in stdout
        return True  # Always succeed, just records status

    def _download_docker_windows(self) -> bool:
        """Download Docker Desktop installer for Windows."""
        self._installer_path = download_file(
            DOCKER_DESKTOP_WINDOWS,
            dest=get_temp_dir() / "DockerDesktopInstaller.exe",
        )
        return self._installer_path.exists()

    def _install_docker_windows(self) -> bool:
        """Install Docker Desktop on Windows."""
        # Run installer with silent flags
        code, _, stderr = run_with_progress(
            [
                str(self._installer_path),
                "install",
                "--quiet",
                "--accept-license",
            ],
            "Installing Docker Desktop",
            timeout=600.0,
        )

        if code != 0:
            logger.error(f"Docker installation failed: {stderr}")
            return False

        return True

    def _rollback_docker_windows(self) -> None:
        """Rollback Docker installation on Windows."""
        uninstaller = Path(r"C:\Program Files\Docker\Docker\Docker Desktop Installer.exe")
        if uninstaller.exists():
            run_with_progress(
                [str(uninstaller), "uninstall", "--quiet"],
                "Uninstalling Docker Desktop",
            )

    # Common methods

    def _wait_for_daemon(self) -> bool:
        """Wait for Docker daemon to be ready."""
        logger.info("Waiting for Docker daemon to start...")

        # Wait up to 60 seconds for daemon
        for _ in range(60):
            code, _, _ = run_with_progress(
                ["docker", "info"],
                "Checking Docker daemon",
                timeout=10.0,
            )
            if code == 0:
                return True
            time.sleep(1)

        logger.error("Docker daemon did not start within 60 seconds")
        return False
