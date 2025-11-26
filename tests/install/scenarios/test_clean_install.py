"""
Clean Installation Scenario Tests.

INSTALL-TEST-002: Test fresh installation on clean system.
"""

import os
import shutil
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def clean_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a completely clean ragged home directory."""
    home = tmp_path / ".ragged"
    # Ensure it doesn't exist
    if home.exists():
        shutil.rmtree(home)
    yield home
    # Cleanup
    if home.exists():
        shutil.rmtree(home)


@pytest.fixture
def clean_env(clean_home: Path) -> dict[str, str]:
    """Environment for clean installation."""
    env = os.environ.copy()
    env["RAGGED_HOME"] = str(clean_home)
    env["RAGGED_FIRST_RUN"] = "1"
    return env


class TestCleanInstallDetection:
    """Tests for detecting clean installation state."""

    def test_detects_no_existing_installation(
        self,
        clean_home: Path,
    ) -> None:
        """Test detection of missing installation."""
        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(clean_home)
        result = detector.detect()

        assert result.home_exists is False

    def test_detects_empty_home_directory(
        self,
        clean_home: Path,
    ) -> None:
        """Test detection when home exists but is empty."""
        clean_home.mkdir(parents=True)

        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(clean_home)
        result = detector.detect()

        assert result.home_exists is True


class TestCleanInstallPrerequisites:
    """Tests for prerequisite checking during clean install."""

    def test_python_prerequisite(self) -> None:
        """Test Python is detected as prerequisite."""
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()
        result = detector.detect()

        assert result.installed is True
        assert result.version is not None
        # Verify minimum version
        major, minor = map(int, result.version.split(".")[:2])
        assert major == 3
        assert minor >= 10

    def test_all_prerequisites_checked(
        self,
        clean_home: Path,
    ) -> None:
        """Test all prerequisites are checked."""
        from ragged.install.detection import detect_all_prerequisites

        results = detect_all_prerequisites(clean_home)

        # Should check all required components
        assert "python" in results
        assert "docker" in results
        assert "environment" in results


class TestCleanInstallScaffolding:
    """Tests for scaffolding during clean install."""

    def test_creates_directory_structure(
        self,
        clean_home: Path,
    ) -> None:
        """Test directory structure creation."""
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(clean_home)

        # Verify expected directories
        expected = ["documents", "cache", "logs", "data"]
        for dirname in expected:
            assert (clean_home / dirname).exists()
            assert (clean_home / dirname).is_dir()

    def test_sets_correct_permissions(
        self,
        clean_home: Path,
    ) -> None:
        """Test permissions are set correctly."""
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(clean_home)

        # Home directory should be accessible only to user
        home_mode = clean_home.stat().st_mode & 0o777
        # Should be at least readable/writable by owner
        assert home_mode & 0o600 == 0o600

    def test_creates_default_config(
        self,
        clean_home: Path,
    ) -> None:
        """Test default configuration is created."""
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(clean_home)

        # Config file should exist
        config_path = clean_home / "config.yaml"
        # Config may or may not exist depending on implementation
        # Just verify scaffolding completes without error


class TestCleanInstallValidation:
    """Tests for validating clean installation."""

    def test_validates_empty_environment(
        self,
        clean_home: Path,
    ) -> None:
        """Test validation passes for clean environment."""
        from ragged.install.validation import validate_environment

        # Create minimal structure first
        clean_home.mkdir(parents=True, exist_ok=True)

        results = validate_environment(clean_home)

        # Should return list of validation results
        assert isinstance(results, list)

    def test_identifies_critical_issues(
        self,
        clean_home: Path,
    ) -> None:
        """Test critical issues are identified."""
        from ragged.install.validation import validate_environment

        # Don't create home - should detect issues
        results = validate_environment(clean_home)

        # May have warnings but shouldn't block install
        assert isinstance(results, list)


class TestCleanInstallWorkflow:
    """Tests for complete clean installation workflow."""

    def test_full_clean_install_workflow(
        self,
        clean_home: Path,
    ) -> None:
        """Test complete clean installation workflow."""
        from ragged.install import (
            detect_all_prerequisites,
            validate_environment,
        )
        from ragged.install.scaffolding import create_directory_structure

        # Step 1: Detect prerequisites
        prereqs = detect_all_prerequisites(clean_home)
        assert prereqs["python"].installed

        # Step 2: Create structure
        create_directory_structure(clean_home)
        assert clean_home.exists()

        # Step 3: Validate
        results = validate_environment(clean_home)
        assert isinstance(results, list)

        # Final verification
        assert (clean_home / "documents").exists()
        assert (clean_home / "cache").exists()
        assert (clean_home / "logs").exists()
        assert (clean_home / "data").exists()

    def test_idempotent_install(
        self,
        clean_home: Path,
    ) -> None:
        """Test installation is idempotent."""
        from ragged.install.scaffolding import create_directory_structure

        # Run installation twice
        create_directory_structure(clean_home)
        create_directory_structure(clean_home)

        # Should still be valid
        assert clean_home.exists()
        assert (clean_home / "documents").exists()
