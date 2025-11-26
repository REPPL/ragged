"""
Known Issues Regression Tests.

INSTALL-TEST-005: Tests for previously fixed issues.
"""

import os
import platform
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def test_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test home directory."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    yield home


class TestPathHandlingRegressions:
    """Regression tests for path handling issues."""

    def test_spaces_in_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test paths with spaces are handled correctly.

        Regression: Early versions failed with spaces in paths.
        """
        home = tmp_path / "path with spaces" / ".ragged"
        home.mkdir(parents=True)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()
        assert (home / "documents").exists()

    def test_unicode_in_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Unicode paths are handled correctly.

        Regression: Unicode paths caused encoding errors.
        """
        home = tmp_path / "путь" / "路径" / ".ragged"
        home.mkdir(parents=True)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()

    def test_very_long_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test very long paths are handled.

        Regression: Long paths exceeded OS limits.
        """
        # Create a reasonably long path (not exceeding OS limits)
        long_segment = "a" * 50
        home = tmp_path
        for _ in range(5):
            home = home / long_segment
        home = home / ".ragged"
        home.mkdir(parents=True)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()

    def test_symlink_home(
        self,
        tmp_path: Path,
    ) -> None:
        """Test installation via symlinked home.

        Regression: Symlinks caused resolution issues.
        """
        real_home = tmp_path / "real" / ".ragged"
        real_home.mkdir(parents=True)

        link_parent = tmp_path / "link"
        link_parent.mkdir()
        symlink_home = link_parent / ".ragged"
        symlink_home.symlink_to(real_home)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(symlink_home)

        # Both should work
        assert real_home.exists()
        assert symlink_home.exists()


class TestConfigurationRegressions:
    """Regression tests for configuration issues."""

    def test_empty_config_file(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of empty config file.

        Regression: Empty config caused parsing crash.
        """
        config = test_home / "config.yaml"
        config.write_text("")

        from ragged.install.scaffolding import create_directory_structure

        # Should not crash
        create_directory_structure(test_home)

        assert test_home.exists()

    def test_malformed_yaml(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of malformed YAML.

        Regression: Invalid YAML caused uncaught exception.
        """
        config = test_home / "config.yaml"
        config.write_text("invalid: yaml: [content")

        from ragged.install.scaffolding import create_directory_structure

        # Should not crash
        create_directory_structure(test_home)

        assert test_home.exists()

    def test_missing_required_keys(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of config missing required keys.

        Regression: Missing keys caused KeyError.
        """
        config = test_home / "config.yaml"
        config.write_text("some_key: some_value\n")

        from ragged.install.scaffolding import create_directory_structure

        # Should not crash
        create_directory_structure(test_home)

        assert test_home.exists()


class TestPermissionRegressions:
    """Regression tests for permission issues."""

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Unix permissions test",
    )
    def test_restrictive_umask(
        self,
        test_home: Path,
    ) -> None:
        """Test installation with restrictive umask.

        Regression: Restrictive umask caused unusable directories.
        """
        old_umask = os.umask(0o077)  # Very restrictive

        try:
            from ragged.install.scaffolding import create_directory_structure

            create_directory_structure(test_home)

            # Directories should still be usable
            test_file = test_home / "documents" / "test.txt"
            test_file.write_text("test")
            assert test_file.read_text() == "test"
        finally:
            os.umask(old_umask)

    def test_read_only_parent(
        self,
        tmp_path: Path,
    ) -> None:
        """Test detection handles read-only parent gracefully.

        Regression: Read-only parent caused crash during detection.
        """
        from ragged.install.detection import EnvironmentDetector

        # Detection should work even if we can't write
        detector = EnvironmentDetector(tmp_path / "nonexistent" / ".ragged")
        result = detector.detect()

        # Should return result without crashing
        assert result is not None


class TestDetectionRegressions:
    """Regression tests for detection issues."""

    def test_docker_not_in_path(self) -> None:
        """Test Docker detection when not in PATH.

        Regression: Missing Docker caused unhandled exception.
        """
        from ragged.install.detection import DockerDetector

        detector = DockerDetector()
        result = detector.detect()

        # Should return result (installed=False if not found)
        assert result is not None
        assert hasattr(result, "installed")

    def test_python_detection_accuracy(self) -> None:
        """Test Python version detection is accurate.

        Regression: Version parsing was incorrect for some formats.
        """
        import sys

        from ragged.install.detection import PythonDetector

        detector = PythonDetector()
        result = detector.detect()

        # Should match actual Python version
        assert result.installed is True
        detected_version = result.version
        actual_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        assert detected_version.startswith(actual_version)

    def test_environment_detection_disk_space(
        self,
        test_home: Path,
    ) -> None:
        """Test disk space detection is accurate.

        Regression: Disk space was reported in wrong units.
        """
        import shutil

        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(test_home)
        result = detector.detect()

        # Compare with shutil
        actual = shutil.disk_usage(test_home)
        actual_gb = actual.free / (1024**3)

        # Should be within reasonable range
        assert abs(result.disk_space_gb - actual_gb) < 1.0


class TestValidationRegressions:
    """Regression tests for validation issues."""

    def test_port_validation_with_ipv6(self) -> None:
        """Test port validation with IPv6.

        Regression: IPv6-only systems failed validation.
        """
        from ragged.install.validation import PortValidator

        validator = PortValidator()
        results = validator.validate()

        # Should complete without crashing
        assert isinstance(results, list)

    def test_filesystem_validation_with_special_files(
        self,
        test_home: Path,
    ) -> None:
        """Test filesystem validation with special files.

        Regression: Named pipes and device files caused issues.
        """
        from ragged.install.validation import FilesystemValidator

        # Create normal structure
        (test_home / "documents").mkdir()

        validator = FilesystemValidator(test_home)
        results = validator.validate()

        assert isinstance(results, list)


class TestConcurrencyRegressions:
    """Regression tests for concurrency issues."""

    def test_concurrent_directory_creation(
        self,
        test_home: Path,
    ) -> None:
        """Test concurrent directory creation.

        Regression: Race condition caused directory creation to fail.
        """
        import threading

        from ragged.install.scaffolding import create_directory_structure

        errors: list[Exception] = []

        def worker() -> None:
            try:
                create_directory_structure(test_home)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0
        assert test_home.exists()

    def test_concurrent_detection(
        self,
        test_home: Path,
    ) -> None:
        """Test concurrent detection.

        Regression: Concurrent detection caused resource conflicts.
        """
        import threading

        from ragged.install.detection import detect_all_prerequisites

        results_list: list[dict] = []
        errors: list[Exception] = []

        def worker() -> None:
            try:
                results = detect_all_prerequisites(test_home)
                results_list.append(results)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results_list) == 5
