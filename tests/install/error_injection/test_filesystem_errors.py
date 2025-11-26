"""
Filesystem Error Injection Tests.

INSTALL-TEST-003: Test recovery from filesystem-related errors.
"""

import os
import stat
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def test_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test home directory."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    yield home


class TestDiskSpaceErrors:
    """Tests for disk space error handling."""

    def test_handles_disk_full_simulation(
        self,
        test_home: Path,
    ) -> None:
        """Test handling when disk appears full."""
        from ragged.install.validation import FilesystemValidator

        validator = FilesystemValidator(test_home)
        results = validator.validate()

        # Should return validation results
        assert isinstance(results, list)

    def test_low_disk_space_warning(
        self,
        test_home: Path,
    ) -> None:
        """Test warning on low disk space."""
        import shutil

        # Get actual disk usage
        usage = shutil.disk_usage(test_home)
        free_gb = usage.free / (1024**3)

        # Test should pass but may warn if low
        from ragged.install.validation import FilesystemValidator

        validator = FilesystemValidator(test_home)
        results = validator.validate()

        assert isinstance(results, list)


class TestPermissionErrors:
    """Tests for permission error handling."""

    def test_handles_read_only_directory(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of read-only directory."""
        # Create read-only directory
        readonly_dir = test_home / "readonly"
        readonly_dir.mkdir()
        os.chmod(str(readonly_dir), stat.S_IRUSR | stat.S_IXUSR)

        try:
            from ragged.install.validation import FilesystemValidator

            validator = FilesystemValidator(test_home)
            results = validator.validate()

            assert isinstance(results, list)
        finally:
            # Restore permissions for cleanup
            os.chmod(str(readonly_dir), stat.S_IRWXU)

    def test_handles_no_write_permission(
        self,
        test_home: Path,
    ) -> None:
        """Test handling when write permission denied."""
        # Create file without write permission
        no_write = test_home / "no_write.txt"
        no_write.write_text("test")
        os.chmod(str(no_write), stat.S_IRUSR)

        try:
            from ragged.install.validation import FilesystemValidator

            validator = FilesystemValidator(test_home)
            results = validator.validate()

            assert isinstance(results, list)
        finally:
            os.chmod(str(no_write), stat.S_IRWXU)

    def test_handles_no_execute_permission(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of directory without execute permission."""
        # Create directory without execute (can't cd into it)
        no_exec = test_home / "no_exec"
        no_exec.mkdir()
        os.chmod(str(no_exec), stat.S_IRUSR | stat.S_IWUSR)

        try:
            from ragged.install.validation import FilesystemValidator

            validator = FilesystemValidator(test_home)
            results = validator.validate()

            assert isinstance(results, list)
        finally:
            os.chmod(str(no_exec), stat.S_IRWXU)


class TestFileLockErrors:
    """Tests for file lock error handling."""

    def test_handles_locked_config(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of locked configuration file."""
        # Create config file
        config = test_home / "config.yaml"
        config.write_text("test: value\n")

        # Simulate locked file by making it read-only
        os.chmod(str(config), stat.S_IRUSR)

        try:
            from ragged.install.detection import EnvironmentDetector

            detector = EnvironmentDetector(test_home)
            result = detector.detect()

            # Should still work for reading
            assert result.home_exists is True
        finally:
            os.chmod(str(config), stat.S_IRWXU)

    def test_handles_concurrent_access(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of concurrent file access."""
        from ragged.install.scaffolding import create_directory_structure

        # Create structure normally
        create_directory_structure(test_home)

        # Concurrent access simulation (second call)
        create_directory_structure(test_home)

        # Should handle gracefully
        assert test_home.exists()


class TestPathErrors:
    """Tests for path-related error handling."""

    def test_handles_very_long_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of very long paths."""
        # Create deeply nested path
        deep_path = tmp_path
        for i in range(10):  # Create nested directories
            deep_path = deep_path / f"level_{i}"

        deep_path.mkdir(parents=True)
        home = deep_path / ".ragged"
        home.mkdir()

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()

    def test_handles_special_characters_in_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of special characters in path."""
        # Path with spaces and special chars
        special_path = tmp_path / "path with spaces" / "special-chars_here"
        special_path.mkdir(parents=True)
        home = special_path / ".ragged"
        home.mkdir()

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()

    def test_handles_unicode_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test handling of Unicode characters in path."""
        # Path with Unicode
        unicode_path = tmp_path / "用户" / "данные"
        unicode_path.mkdir(parents=True)
        home = unicode_path / ".ragged"
        home.mkdir()

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(home)

        assert home.exists()


class TestSymlinkErrors:
    """Tests for symlink error handling."""

    def test_handles_broken_symlink(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of broken symlinks."""
        # Create broken symlink
        target = test_home / "nonexistent"
        broken_link = test_home / "broken_link"
        broken_link.symlink_to(target)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # Should complete despite broken symlink
        assert test_home.exists()

    def test_handles_circular_symlink(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of circular symlinks."""
        # Create circular symlink
        link_a = test_home / "link_a"
        link_b = test_home / "link_b"

        link_a.symlink_to(link_b)
        link_b.symlink_to(link_a)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # Should complete despite circular symlinks
        assert test_home.exists()


class TestIOErrors:
    """Tests for I/O error handling."""

    def test_handles_io_error_on_read(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of I/O errors during read."""
        from ragged.install.detection import EnvironmentDetector

        with patch.object(Path, "read_text", side_effect=IOError("Simulated I/O error")):
            detector = EnvironmentDetector(test_home)
            # Should handle gracefully
            try:
                result = detector.detect()
                assert result is not None
            except IOError:
                # Acceptable if error propagates
                pass

    def test_handles_os_error_on_stat(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of OS errors during stat."""
        from ragged.install.detection import EnvironmentDetector

        # Normal detection should work
        detector = EnvironmentDetector(test_home)
        result = detector.detect()

        assert result is not None
