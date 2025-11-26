"""
Python Installer.

PREREQ-002: Automated Python installation for macOS, Linux, and Windows.
Supports official installers, Homebrew, and package managers.
"""

import logging
from pathlib import Path

from ragged.install.detection.base import Platform
from ragged.install.detection.python_detector import PythonDetector
from ragged.install.installers.base import (
    BaseInstaller,
    InstallationStep,
    InstallationError,
)
from ragged.install.installers.utils import (
    download_file,
    run_with_progress,
    run_with_sudo,
    get_temp_dir,
)


logger = logging.getLogger(__name__)


# Python download URLs (official releases)
PYTHON_VERSION = "3.12.0"
PYTHON_MACOS_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-macos11.pkg"
PYTHON_WINDOWS_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-amd64.exe"


class PythonInstaller(BaseInstaller):
    """
    Installer for Python.

    Installation methods by platform:
    - macOS: Homebrew or official pkg installer
    - Linux: System package manager (apt, dnf, etc.)
    - Windows: Official installer
    """

    def _create_detector(self) -> PythonDetector:
        """Create Python detector."""
        return PythonDetector()

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
                name="install_python",
                description="Installing Python 3.12",
                action=self._install_python_macos,
                rollback=self._rollback_python_macos,
            ),
            InstallationStep(
                name="verify_pip",
                description="Verifying pip installation",
                action=self._verify_pip,
            ),
            InstallationStep(
                name="verify_venv",
                description="Verifying venv module",
                action=self._verify_venv,
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
                name="install_python",
                description="Installing Python 3.12",
                action=self._install_python_linux,
                rollback=self._rollback_python_linux,
            ),
            InstallationStep(
                name="install_pip",
                description="Installing pip",
                action=self._install_pip_linux,
            ),
            InstallationStep(
                name="verify_venv",
                description="Verifying venv module",
                action=self._verify_venv,
            ),
        ]

    def _windows_steps(self) -> list[InstallationStep]:
        """Installation steps for Windows."""
        return [
            InstallationStep(
                name="download_installer",
                description="Downloading Python installer",
                action=self._download_python_windows,
            ),
            InstallationStep(
                name="install_python",
                description="Installing Python 3.12",
                action=self._install_python_windows,
                rollback=self._rollback_python_windows,
            ),
            InstallationStep(
                name="verify_pip",
                description="Verifying pip installation",
                action=self._verify_pip,
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

    def _install_python_macos(self) -> bool:
        """Install Python on macOS."""
        if self._use_homebrew:
            return self._install_python_homebrew()
        return self._install_python_pkg()

    def _install_python_homebrew(self) -> bool:
        """Install Python via Homebrew."""
        code, stdout, stderr = run_with_progress(
            ["brew", "install", "python@3.12"],
            "Installing Python 3.12 via Homebrew",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"Homebrew installation failed: {stderr}")
            return False

        # Ensure python3.12 is linked
        run_with_progress(
            ["brew", "link", "python@3.12", "--force"],
            "Linking Python 3.12",
        )

        return True

    def _install_python_pkg(self) -> bool:
        """Install Python via official pkg installer."""
        # Download pkg
        pkg_path = download_file(PYTHON_MACOS_URL)

        # Install pkg
        code, _, stderr = run_with_sudo(
            ["installer", "-pkg", str(pkg_path), "-target", "/"],
            "Installing Python pkg",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"pkg installation failed: {stderr}")
            return False

        return True

    def _rollback_python_macos(self) -> None:
        """Rollback Python installation on macOS."""
        if self._use_homebrew:
            run_with_progress(
                ["brew", "uninstall", "python@3.12"],
                "Rolling back Python installation",
            )

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

    def _install_python_linux(self) -> bool:
        """Install Python on Linux."""
        if self._linux_distro in ("ubuntu", "debian"):
            return self._install_python_apt()
        elif self._linux_distro in ("fedora",):
            return self._install_python_dnf()
        elif self._linux_distro in ("rhel", "centos", "rocky", "almalinux"):
            return self._install_python_dnf()
        elif self._linux_distro in ("arch", "manjaro"):
            return self._install_python_pacman()
        else:
            logger.warning(f"Unsupported distro: {self._linux_distro}")
            return self._install_python_from_source()

    def _install_python_apt(self) -> bool:
        """Install Python via apt (Debian/Ubuntu)."""
        # Add deadsnakes PPA for Python 3.12
        code, _, _ = run_with_sudo(
            ["add-apt-repository", "-y", "ppa:deadsnakes/ppa"],
            "Adding deadsnakes PPA",
        )

        run_with_sudo(
            ["apt-get", "update"],
            "Updating package list",
        )

        code, _, stderr = run_with_sudo(
            ["apt-get", "install", "-y", "python3.12", "python3.12-venv", "python3.12-dev"],
            "Installing Python 3.12",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"apt installation failed: {stderr}")
            return False

        return True

    def _install_python_dnf(self) -> bool:
        """Install Python via dnf (Fedora/RHEL)."""
        code, _, stderr = run_with_sudo(
            ["dnf", "install", "-y", "python3.12", "python3.12-pip", "python3.12-devel"],
            "Installing Python 3.12",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"dnf installation failed: {stderr}")
            return False

        return True

    def _install_python_pacman(self) -> bool:
        """Install Python via pacman (Arch)."""
        code, _, stderr = run_with_sudo(
            ["pacman", "-S", "--noconfirm", "python"],
            "Installing Python",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"pacman installation failed: {stderr}")
            return False

        return True

    def _install_python_from_source(self) -> bool:
        """Build Python from source (fallback)."""
        logger.info("Building Python from source...")

        # Download source
        source_url = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/Python-{PYTHON_VERSION}.tgz"
        source_path = download_file(source_url)

        # Extract
        build_dir = get_temp_dir() / "python_build"
        build_dir.mkdir(exist_ok=True)

        run_with_progress(
            ["tar", "-xzf", str(source_path), "-C", str(build_dir)],
            "Extracting Python source",
        )

        source_dir = build_dir / f"Python-{PYTHON_VERSION}"

        # Configure
        code, _, _ = run_with_progress(
            ["./configure", "--enable-optimizations", "--prefix=/usr/local"],
            "Configuring Python build",
            timeout=300.0,
            cwd=source_dir,
        )

        if code != 0:
            return False

        # Build
        code, _, _ = run_with_progress(
            ["make", "-j4"],
            "Building Python",
            timeout=900.0,
            cwd=source_dir,
        )

        if code != 0:
            return False

        # Install
        code, _, _ = run_with_sudo(
            ["make", "altinstall"],
            "Installing Python",
            timeout=300.0,
        )

        return code == 0

    def _install_pip_linux(self) -> bool:
        """Ensure pip is installed on Linux."""
        code, _, _ = run_with_progress(
            ["python3.12", "-m", "ensurepip", "--upgrade"],
            "Installing pip",
        )

        if code != 0:
            # Try alternative method
            run_with_sudo(
                ["apt-get", "install", "-y", "python3-pip"],
                "Installing pip via apt",
            )

        return True

    def _rollback_python_linux(self) -> None:
        """Rollback Python installation on Linux."""
        if self._linux_distro in ("ubuntu", "debian"):
            run_with_sudo(
                ["apt-get", "remove", "-y", "python3.12"],
                "Removing Python 3.12",
            )
        elif self._linux_distro in ("fedora", "rhel", "centos"):
            run_with_sudo(
                ["dnf", "remove", "-y", "python3.12"],
                "Removing Python 3.12",
            )

    # Windows installation methods

    def _download_python_windows(self) -> bool:
        """Download Python installer for Windows."""
        self._installer_path = download_file(
            PYTHON_WINDOWS_URL,
            dest=get_temp_dir() / f"python-{PYTHON_VERSION}-amd64.exe",
        )
        return self._installer_path.exists()

    def _install_python_windows(self) -> bool:
        """Install Python on Windows."""
        code, _, stderr = run_with_progress(
            [
                str(self._installer_path),
                "/quiet",
                "InstallAllUsers=1",
                "PrependPath=1",
                "Include_test=0",
            ],
            "Installing Python",
            timeout=300.0,
        )

        if code != 0:
            logger.error(f"Python installation failed: {stderr}")
            return False

        return True

    def _rollback_python_windows(self) -> None:
        """Rollback Python installation on Windows."""
        if hasattr(self, "_installer_path") and self._installer_path.exists():
            run_with_progress(
                [str(self._installer_path), "/uninstall", "/quiet"],
                "Uninstalling Python",
            )

    # Common verification methods

    def _verify_pip(self) -> bool:
        """Verify pip is working."""
        code, stdout, _ = run_with_progress(
            ["python3", "-m", "pip", "--version"],
            "Verifying pip",
        )

        if code != 0:
            # Try python3.12 explicitly
            code, stdout, _ = run_with_progress(
                ["python3.12", "-m", "pip", "--version"],
                "Verifying pip (python3.12)",
            )

        return code == 0

    def _verify_venv(self) -> bool:
        """Verify venv module is available."""
        code, _, _ = run_with_progress(
            ["python3", "-m", "venv", "--help"],
            "Verifying venv module",
        )

        if code != 0:
            code, _, _ = run_with_progress(
                ["python3.12", "-m", "venv", "--help"],
                "Verifying venv module (python3.12)",
            )

        return code == 0
