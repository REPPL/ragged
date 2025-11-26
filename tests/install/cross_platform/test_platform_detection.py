"""
Platform Detection Tests.

INSTALL-TEST-001: Test platform detection across operating systems.
"""

import platform
import sys

import pytest


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_system_detection(self) -> None:
        """Test that system is correctly detected."""
        system = platform.system().lower()
        assert system in ("darwin", "linux", "windows")

    def test_architecture_detection(self) -> None:
        """Test that architecture is correctly detected."""
        machine = platform.machine().lower()
        # Common architectures
        assert machine in ("x86_64", "amd64", "arm64", "aarch64", "i386", "i686")

    def test_python_version(self) -> None:
        """Test Python version meets requirements."""
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 10

    @pytest.mark.skipif(
        platform.system() != "Darwin",
        reason="macOS-specific test",
    )
    def test_macos_version(self) -> None:
        """Test macOS version detection."""
        mac_ver = platform.mac_ver()[0]
        assert mac_ver, "Could not detect macOS version"
        # macOS 11+ (Big Sur or later)
        major = int(mac_ver.split(".")[0])
        assert major >= 11, f"macOS {major} not supported (requires 11+)"

    @pytest.mark.skipif(
        platform.system() != "Linux",
        reason="Linux-specific test",
    )
    def test_linux_distribution(self) -> None:
        """Test Linux distribution detection."""
        # Try to detect distribution
        try:
            import distro
            dist_id = distro.id()
            assert dist_id, "Could not detect Linux distribution"
        except ImportError:
            # Fall back to platform
            info = platform.freedesktop_os_release()
            assert "ID" in info

    @pytest.mark.skipif(
        platform.system() != "Windows",
        reason="Windows-specific test",
    )
    def test_windows_version(self) -> None:
        """Test Windows version detection."""
        win_ver = platform.win32_ver()[0]
        assert win_ver, "Could not detect Windows version"
        # Windows 10 or 11
        assert win_ver in ("10", "11"), f"Windows {win_ver} not supported"


class TestPlatformCapabilities:
    """Tests for platform-specific capabilities."""

    def test_docker_available(self) -> None:
        """Test Docker availability detection."""
        import subprocess

        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Docker may or may not be installed
            if result.returncode == 0:
                assert "Docker" in result.stdout
        except FileNotFoundError:
            pytest.skip("Docker not installed")

    def test_python_venv_capability(self) -> None:
        """Test Python venv module availability."""
        import venv
        assert hasattr(venv, "create")

    def test_pip_available(self) -> None:
        """Test pip availability."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "pip" in result.stdout


class TestNetworkCapabilities:
    """Tests for network capabilities."""

    def test_localhost_resolution(self) -> None:
        """Test localhost resolves correctly."""
        import socket

        ip = socket.gethostbyname("localhost")
        assert ip in ("127.0.0.1", "::1")

    def test_port_availability_check(self) -> None:
        """Test port availability checking works."""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Port 0 = let OS assign available port
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            assert port > 0
        finally:
            sock.close()

    def test_https_connectivity(self) -> None:
        """Test HTTPS connectivity."""
        import urllib.request

        try:
            response = urllib.request.urlopen(
                "https://pypi.org/simple/",
                timeout=10,
            )
            assert response.status == 200
        except Exception:
            pytest.skip("No internet connectivity")


class TestFilesystemCapabilities:
    """Tests for filesystem capabilities."""

    def test_home_directory_writable(self) -> None:
        """Test home directory is writable."""
        from pathlib import Path
        import tempfile

        home = Path.home()
        test_file = home / f".ragged_test_{tempfile.mktemp()}"

        try:
            test_file.write_text("test")
            assert test_file.exists()
        finally:
            test_file.unlink(missing_ok=True)

    def test_temp_directory_available(self) -> None:
        """Test temp directory is available."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            assert tmpdir
            test_file = Path(tmpdir) / "test"
            test_file.write_text("test")
            assert test_file.exists()

    def test_disk_space_check(self) -> None:
        """Test disk space checking works."""
        import shutil
        from pathlib import Path

        home = Path.home()
        usage = shutil.disk_usage(home)

        assert usage.total > 0
        assert usage.free > 0
        # At least 1GB free
        free_gb = usage.free / (1024**3)
        assert free_gb > 1, f"Insufficient disk space: {free_gb:.1f}GB"
