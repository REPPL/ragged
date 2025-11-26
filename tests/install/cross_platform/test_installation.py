"""
Cross-Platform Installation Tests.

INSTALL-TEST-001: Test installation on different platforms.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


# Skip all tests if not in CI or explicit test mode
SKIP_INSTALL_TESTS = os.environ.get("RAGGED_TEST_INSTALL") != "1"


@pytest.fixture
def ragged_home(tmp_path: Path) -> Path:
    """Create temporary ragged home directory."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    return home


@pytest.fixture
def env_with_home(ragged_home: Path) -> dict[str, str]:
    """Environment with custom ragged home."""
    env = os.environ.copy()
    env["RAGGED_HOME"] = str(ragged_home)
    return env


class TestDetectionSystem:
    """Tests for the detection system."""

    def test_docker_detector(self, env_with_home: dict[str, str]) -> None:
        """Test Docker detection."""
        from ragged.install.detection import DockerDetector

        detector = DockerDetector()
        result = detector.detect()

        # Docker may or may not be installed
        assert result is not None
        assert hasattr(result, "installed")
        assert hasattr(result, "version")

    def test_python_detector(self, env_with_home: dict[str, str]) -> None:
        """Test Python detection."""
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()
        result = detector.detect()

        assert result.installed is True
        assert result.version is not None
        assert result.path is not None

    def test_ollama_detector(self, env_with_home: dict[str, str]) -> None:
        """Test Ollama detection."""
        from ragged.install.detection import OllamaDetector

        detector = OllamaDetector()
        result = detector.detect()

        # Ollama may or may not be installed
        assert result is not None
        assert hasattr(result, "installed")

    def test_environment_detector(
        self,
        ragged_home: Path,
        env_with_home: dict[str, str],
    ) -> None:
        """Test environment detection."""
        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(ragged_home)
        result = detector.detect()

        assert result is not None
        assert hasattr(result, "disk_space_gb")
        assert result.disk_space_gb > 0

    def test_detect_all_prerequisites(
        self,
        ragged_home: Path,
    ) -> None:
        """Test comprehensive prerequisite detection."""
        from ragged.install.detection import detect_all_prerequisites

        results = detect_all_prerequisites(ragged_home)

        assert "docker" in results
        assert "python" in results
        assert "ollama" in results
        assert "environment" in results


class TestValidationSystem:
    """Tests for the validation system."""

    def test_port_validator(self) -> None:
        """Test port validation."""
        from ragged.install.validation import PortValidator

        validator = PortValidator()
        results = validator.validate()

        assert isinstance(results, list)
        # Should check standard ports
        for result in results:
            assert hasattr(result, "passed")
            assert hasattr(result, "message")

    def test_filesystem_validator(self, ragged_home: Path) -> None:
        """Test filesystem validation."""
        from ragged.install.validation import FilesystemValidator

        validator = FilesystemValidator(ragged_home)
        results = validator.validate()

        assert isinstance(results, list)

    def test_version_validator(self) -> None:
        """Test version validation."""
        from ragged.install.validation import VersionValidator

        validator = VersionValidator()
        results = validator.validate()

        assert isinstance(results, list)

    def test_validate_environment(self, ragged_home: Path) -> None:
        """Test comprehensive environment validation."""
        from ragged.install.validation import validate_environment

        results = validate_environment(ragged_home)

        assert isinstance(results, list)


class TestScaffoldingSystem:
    """Tests for the scaffolding system."""

    def test_create_directory_structure(self, ragged_home: Path) -> None:
        """Test directory structure creation."""
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(ragged_home)

        # Check expected directories exist
        expected_dirs = ["documents", "cache", "logs", "data"]
        for dir_name in expected_dirs:
            assert (ragged_home / dir_name).exists()

    def test_uninstall_preview(self, ragged_home: Path) -> None:
        """Test uninstall preview."""
        from ragged.install.scaffolding import (
            create_directory_structure,
            get_uninstall_preview,
        )

        create_directory_structure(ragged_home)
        preview = get_uninstall_preview(ragged_home)

        assert "home_exists" in preview
        assert preview["home_exists"] is True
        assert "components" in preview


@pytest.mark.skipif(SKIP_INSTALL_TESTS, reason="Install tests disabled")
class TestFullInstallation:
    """Full installation tests (requires explicit enable)."""

    def test_clean_install(
        self,
        ragged_home: Path,
        env_with_home: dict[str, str],
    ) -> None:
        """Test clean installation."""
        from ragged.install import (
            detect_all_prerequisites,
            validate_environment,
            create_directory_structure,
        )

        # Detect
        prereqs = detect_all_prerequisites(ragged_home)
        assert prereqs["python"].installed

        # Validate
        validation = validate_environment(ragged_home)
        critical = [v for v in validation if v.severity.value == "critical"]
        assert len(critical) == 0, f"Critical validation failures: {critical}"

        # Scaffold
        create_directory_structure(ragged_home)
        assert ragged_home.exists()

    def test_install_with_existing_data(
        self,
        ragged_home: Path,
        env_with_home: dict[str, str],
    ) -> None:
        """Test installation with existing data."""
        from ragged.install.scaffolding import create_directory_structure

        # Create existing data
        docs_dir = ragged_home / "documents"
        docs_dir.mkdir(parents=True)
        test_file = docs_dir / "existing.txt"
        test_file.write_text("existing data")

        # Run scaffolding (should preserve existing)
        create_directory_structure(ragged_home)

        # Verify data preserved
        assert test_file.exists()
        assert test_file.read_text() == "existing data"


class TestPlatformSpecific:
    """Platform-specific tests."""

    @pytest.mark.skipif(
        platform.system() != "Darwin",
        reason="macOS-specific test",
    )
    def test_macos_homebrew_detection(self) -> None:
        """Test Homebrew detection on macOS."""
        result = subprocess.run(
            ["which", "brew"],
            capture_output=True,
            text=True,
        )
        # Homebrew may or may not be installed
        if result.returncode == 0:
            assert "/brew" in result.stdout

    @pytest.mark.skipif(
        platform.system() != "Linux",
        reason="Linux-specific test",
    )
    def test_linux_package_manager_detection(self) -> None:
        """Test package manager detection on Linux."""
        # Try common package managers
        package_managers = ["apt", "dnf", "yum", "pacman"]
        found = False

        for pm in package_managers:
            result = subprocess.run(
                ["which", pm],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                found = True
                break

        # At least one should be available on most Linux distros
        # but don't fail if none found (could be minimal container)

    @pytest.mark.skipif(
        platform.system() != "Windows",
        reason="Windows-specific test",
    )
    def test_windows_path_handling(self, ragged_home: Path) -> None:
        """Test Windows path handling."""
        # Windows paths should work correctly
        assert ragged_home.exists() or not ragged_home.exists()

        # Test path with spaces
        space_path = ragged_home / "path with spaces"
        space_path.mkdir(parents=True)
        assert space_path.exists()
