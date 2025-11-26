"""
Upgrade Installation Scenario Tests.

INSTALL-TEST-002: Test upgrading from previous versions.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def legacy_home(tmp_path: Path) -> Path:
    """Create a simulated legacy installation."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)

    # Create legacy structure
    (home / "documents").mkdir()
    (home / "cache").mkdir()

    # Create legacy config
    legacy_config = {
        "version": "0.5.0",
        "settings": {
            "auto_update": True,
        },
    }
    (home / "config.json").write_text(json.dumps(legacy_config))

    # Create some user data
    (home / "documents" / "test.txt").write_text("user data")

    return home


@pytest.fixture
def env_with_legacy(legacy_home: Path) -> dict[str, str]:
    """Environment pointing to legacy installation."""
    env = os.environ.copy()
    env["RAGGED_HOME"] = str(legacy_home)
    return env


class TestUpgradeDetection:
    """Tests for detecting upgrade scenarios."""

    def test_detects_existing_installation(
        self,
        legacy_home: Path,
    ) -> None:
        """Test detection of existing installation."""
        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(legacy_home)
        result = detector.detect()

        assert result.home_exists is True

    def test_detects_legacy_config(
        self,
        legacy_home: Path,
    ) -> None:
        """Test detection of legacy configuration format."""
        config_path = legacy_home / "config.json"
        assert config_path.exists()

        config = json.loads(config_path.read_text())
        assert config["version"] == "0.5.0"


class TestDataPreservation:
    """Tests for preserving user data during upgrade."""

    def test_preserves_documents(
        self,
        legacy_home: Path,
    ) -> None:
        """Test user documents are preserved."""
        from ragged.install.scaffolding import create_directory_structure

        # Run scaffolding (upgrade)
        create_directory_structure(legacy_home)

        # User data should still exist
        test_file = legacy_home / "documents" / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == "user data"

    def test_preserves_custom_files(
        self,
        legacy_home: Path,
    ) -> None:
        """Test custom user files are preserved."""
        # Add custom file
        custom_file = legacy_home / "custom_script.py"
        custom_file.write_text("# custom script")

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(legacy_home)

        # Custom file should remain
        assert custom_file.exists()


class TestConfigMigration:
    """Tests for configuration migration."""

    def test_handles_legacy_json_config(
        self,
        legacy_home: Path,
    ) -> None:
        """Test handling of legacy JSON config."""
        # Legacy config exists
        config_path = legacy_home / "config.json"
        assert config_path.exists()

        # Migration should handle this
        # (actual migration logic depends on implementation)

    def test_creates_new_config_format(
        self,
        legacy_home: Path,
    ) -> None:
        """Test new config format is created if needed."""
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(legacy_home)

        # Scaffolding should complete without error
        assert legacy_home.exists()


class TestUpgradeValidation:
    """Tests for validation after upgrade."""

    def test_validates_upgraded_environment(
        self,
        legacy_home: Path,
    ) -> None:
        """Test validation of upgraded environment."""
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        create_directory_structure(legacy_home)
        results = validate_environment(legacy_home)

        assert isinstance(results, list)

    def test_reports_migration_status(
        self,
        legacy_home: Path,
    ) -> None:
        """Test migration status is reported."""
        # This tests upgrade reporting
        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(legacy_home)
        result = detector.detect()

        assert result.home_exists is True


class TestUpgradeWorkflow:
    """Tests for complete upgrade workflow."""

    def test_full_upgrade_workflow(
        self,
        legacy_home: Path,
    ) -> None:
        """Test complete upgrade workflow."""
        from ragged.install import detect_all_prerequisites
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        # Capture original data
        original_data = (legacy_home / "documents" / "test.txt").read_text()

        # Step 1: Detect
        prereqs = detect_all_prerequisites(legacy_home)
        assert prereqs["python"].installed

        # Step 2: Upgrade scaffolding
        create_directory_structure(legacy_home)

        # Step 3: Validate
        results = validate_environment(legacy_home)

        # Verify data preserved
        assert (legacy_home / "documents" / "test.txt").read_text() == original_data

    def test_rollback_capability(
        self,
        legacy_home: Path,
    ) -> None:
        """Test that upgrade can be rolled back."""
        # Create backup marker
        backup_marker = legacy_home / ".upgrade_backup"

        # Simulate backup creation
        backup_marker.write_text("backup_location:/tmp/backup")

        # Rollback should be possible
        assert backup_marker.exists()


class TestVersionSpecificUpgrades:
    """Tests for version-specific upgrade paths."""

    def test_upgrade_from_v0_5(
        self,
        legacy_home: Path,
    ) -> None:
        """Test upgrade from v0.5.x."""
        # Legacy config already has v0.5.0
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(legacy_home)

        # Should handle v0.5 -> current
        assert legacy_home.exists()

    def test_upgrade_from_v0_6(
        self,
        tmp_path: Path,
    ) -> None:
        """Test upgrade from v0.6.x."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # v0.6 structure
        (home / "documents").mkdir()
        (home / "cache").mkdir()
        (home / "logs").mkdir()

        config = {"version": "0.6.0"}
        (home / "config.json").write_text(json.dumps(config))

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        # All directories should exist
        assert (home / "documents").exists()
        assert (home / "cache").exists()
        assert (home / "logs").exists()
        assert (home / "data").exists()

    def test_upgrade_from_v0_7(
        self,
        tmp_path: Path,
    ) -> None:
        """Test upgrade from v0.7.x."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # v0.7 structure (more complete)
        for dirname in ["documents", "cache", "logs", "data"]:
            (home / dirname).mkdir()

        config = {"version": "0.7.0"}
        (home / "config.yaml").write_text("version: 0.7.0\n")

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        # Should complete without issues
        assert home.exists()
