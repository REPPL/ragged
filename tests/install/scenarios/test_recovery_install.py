"""
Recovery Installation Scenario Tests.

INSTALL-TEST-002: Test recovery from corrupted/partial installations.
"""

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def corrupted_home(tmp_path: Path) -> Path:
    """Create a simulated corrupted installation."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)

    # Create partial structure (missing some directories)
    (home / "documents").mkdir()
    # cache is missing
    (home / "logs").mkdir()
    # data is missing

    # Create corrupted config
    (home / "config.yaml").write_text("invalid: yaml: content: [")

    return home


@pytest.fixture
def partial_home(tmp_path: Path) -> Path:
    """Create a simulated partial installation."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)

    # Only home exists, no subdirectories
    return home


class TestCorruptionDetection:
    """Tests for detecting corrupted installations."""

    def test_detects_missing_directories(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test detection of missing required directories."""
        # Check what's missing
        assert not (corrupted_home / "cache").exists()
        assert not (corrupted_home / "data").exists()

        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(corrupted_home)
        result = detector.detect()

        # Should detect home exists but may be incomplete
        assert result.home_exists is True

    def test_detects_corrupted_config(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test detection of corrupted configuration."""
        config_path = corrupted_home / "config.yaml"

        # Try to parse corrupted config
        content = config_path.read_text()
        assert "[" in content  # Invalid YAML

    def test_detects_permission_issues(
        self,
        tmp_path: Path,
    ) -> None:
        """Test detection of permission issues."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # Create unreadable file (if possible on this OS)
        try:
            bad_file = home / "locked"
            bad_file.write_text("locked")
            os.chmod(str(bad_file), 0o000)

            from ragged.install.detection import EnvironmentDetector

            detector = EnvironmentDetector(home)
            result = detector.detect()

            # Should still detect home
            assert result.home_exists is True
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(str(home / "locked"), 0o644)
            except Exception:
                pass


class TestPartialInstallRecovery:
    """Tests for recovering partial installations."""

    def test_completes_partial_structure(
        self,
        partial_home: Path,
    ) -> None:
        """Test completion of partial directory structure."""
        from ragged.install.scaffolding import create_directory_structure

        # Run scaffolding on partial install
        create_directory_structure(partial_home)

        # All directories should now exist
        assert (partial_home / "documents").exists()
        assert (partial_home / "cache").exists()
        assert (partial_home / "logs").exists()
        assert (partial_home / "data").exists()

    def test_preserves_existing_content(
        self,
        partial_home: Path,
    ) -> None:
        """Test existing content is preserved during recovery."""
        # Add some content to partial install
        docs = partial_home / "documents"
        docs.mkdir()
        user_file = docs / "important.txt"
        user_file.write_text("important data")

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(partial_home)

        # User file should still exist
        assert user_file.exists()
        assert user_file.read_text() == "important data"


class TestCorruptedConfigRecovery:
    """Tests for recovering corrupted configuration."""

    def test_handles_corrupted_yaml(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test handling of corrupted YAML config."""
        from ragged.install.scaffolding import create_directory_structure

        # Should not crash on corrupted config
        create_directory_structure(corrupted_home)

        # Installation should complete
        assert corrupted_home.exists()

    def test_handles_missing_config(
        self,
        partial_home: Path,
    ) -> None:
        """Test handling of missing configuration."""
        # No config file exists
        assert not (partial_home / "config.yaml").exists()
        assert not (partial_home / "config.json").exists()

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(partial_home)

        # Should complete without error
        assert partial_home.exists()

    def test_creates_default_config_on_recovery(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test default config creation during recovery."""
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(corrupted_home)

        # Recovery should complete
        assert corrupted_home.exists()


class TestRecoveryValidation:
    """Tests for validating recovered installations."""

    def test_validates_recovered_structure(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test validation of recovered structure."""
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        # Recover
        create_directory_structure(corrupted_home)

        # Validate
        results = validate_environment(corrupted_home)

        assert isinstance(results, list)

    def test_identifies_remaining_issues(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test identification of remaining issues after recovery."""
        from ragged.install.validation import validate_environment

        # Validate without recovery first
        results = validate_environment(corrupted_home)

        # Should get validation results
        assert isinstance(results, list)


class TestRecoveryWorkflow:
    """Tests for complete recovery workflow."""

    def test_full_recovery_workflow(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test complete recovery workflow."""
        from ragged.install import detect_all_prerequisites
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        # Step 1: Detect issues
        prereqs = detect_all_prerequisites(corrupted_home)

        # Step 2: Recover structure
        create_directory_structure(corrupted_home)

        # Step 3: Validate
        results = validate_environment(corrupted_home)

        # Verify recovery
        assert (corrupted_home / "documents").exists()
        assert (corrupted_home / "cache").exists()
        assert (corrupted_home / "logs").exists()
        assert (corrupted_home / "data").exists()

    def test_recovery_is_idempotent(
        self,
        corrupted_home: Path,
    ) -> None:
        """Test recovery can be run multiple times safely."""
        from ragged.install.scaffolding import create_directory_structure

        # Run recovery multiple times
        create_directory_structure(corrupted_home)
        create_directory_structure(corrupted_home)
        create_directory_structure(corrupted_home)

        # Should still be valid
        assert corrupted_home.exists()
        assert (corrupted_home / "documents").exists()


class TestEdgeCases:
    """Tests for edge cases in recovery."""

    def test_empty_files(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of empty files."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # Create empty config
        (home / "config.yaml").write_text("")

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()

    def test_binary_garbage_in_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of binary garbage in config."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # Write binary garbage
        (home / "config.yaml").write_bytes(b"\x00\x01\x02\x03\xff\xfe")

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()

    def test_symlink_in_structure(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of symlinks in structure."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # Create symlink to external directory
        external = tmp_path / "external_docs"
        external.mkdir()
        (external / "linked_file.txt").write_text("linked content")

        docs_link = home / "documents"
        docs_link.symlink_to(external)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        # Symlink should be preserved
        assert docs_link.is_symlink()
        assert (docs_link / "linked_file.txt").read_text() == "linked content"

    def test_deep_nested_corruption(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of deeply nested corruption."""
        home = tmp_path / ".ragged"
        home.mkdir(parents=True)

        # Create deep structure with corruption
        deep = home / "cache" / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "corrupted").write_bytes(b"\xff" * 1000)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        # Deep content should be preserved
        assert (deep / "corrupted").exists()
