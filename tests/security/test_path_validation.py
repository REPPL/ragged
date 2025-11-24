"""
Tests for path traversal validation (v0.5.7 HIGH-5).

Security Feature: Path traversal attack prevention
Reference: docs/development/roadmap/version/v0.5.7/README.md
"""
import tempfile
from pathlib import Path

import pytest

from ragged.validation.path_validator import (
    PathTraversalError,
    PathValidator,
    validate_cli_path,
    validate_path,
)


@pytest.fixture
def safe_base_dir():
    """Create temporary safe base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def validator(safe_base_dir):
    """Create validator with safe base directory."""
    return PathValidator(
        allowed_base=safe_base_dir,
        allow_absolute=False,
        allow_symlinks=False,
    )


class TestPathValidator:
    """Test path traversal validation."""

    def test_validator_initialization(self, safe_base_dir):
        """Test validator initializes with correct settings."""
        validator = PathValidator(
            allowed_base=safe_base_dir,
            allow_absolute=False,
            allow_symlinks=False,
        )

        assert validator.allowed_base == safe_base_dir.resolve()
        assert validator.allow_absolute is False
        assert validator.allow_symlinks is False

    def test_validate_safe_relative_path(self, validator, safe_base_dir):
        """Test that safe relative paths pass validation."""
        # Safe relative path
        safe_path = Path("cache/models")

        # Should not raise
        validated = validator.validate(safe_path)

        # Should resolve within base (use resolved base for macOS /private/var compatibility)
        assert str(validated).startswith(str(safe_base_dir.resolve()))
        assert "cache/models" in str(validated)

    def test_validate_parent_traversal_blocked(self, validator):
        """Test that parent directory traversal is blocked."""
        # Attempt path traversal with ..
        malicious_path = Path("../etc/passwd")

        with pytest.raises(PathTraversalError) as exc_info:
            validator.validate(malicious_path)

        assert "parent directory traversal" in str(exc_info.value).lower()

    def test_validate_multiple_parent_traversal_blocked(self, validator):
        """Test that multiple .. are blocked."""
        malicious_path = Path("../../etc/passwd")

        with pytest.raises(PathTraversalError):
            validator.validate(malicious_path)

    def test_validate_hidden_parent_traversal_blocked(self, validator):
        """Test that hidden parent traversal is blocked."""
        # Path that tries to escape via ..
        malicious_path = Path("safe/../../etc/passwd")

        with pytest.raises(PathTraversalError):
            validator.validate(malicious_path)

    def test_validate_absolute_path_blocked_when_not_allowed(self, validator):
        """Test that absolute paths are blocked when not allowed."""
        absolute_path = Path("/etc/passwd")

        with pytest.raises(PathTraversalError) as exc_info:
            validator.validate(absolute_path)

        assert "absolute path not allowed" in str(exc_info.value).lower()

    def test_validate_absolute_path_allowed_when_configured(self, safe_base_dir):
        """Test that absolute paths are allowed when configured."""
        permissive_validator = PathValidator(
            allowed_base=None,
            allow_absolute=True,
            allow_symlinks=False,
        )

        absolute_path = safe_base_dir / "test.txt"

        # Should not raise
        validated = permissive_validator.validate(absolute_path)
        assert validated.is_absolute()

    def test_validate_null_byte_blocked(self, validator):
        """Test that null bytes in paths are blocked."""
        malicious_path = "cache/models\x00.txt"

        with pytest.raises(PathTraversalError) as exc_info:
            validator.validate(malicious_path)

        assert "null byte" in str(exc_info.value).lower()

    def test_validate_creates_directory_when_requested(self, validator, safe_base_dir):
        """Test that validate creates missing directory when requested."""
        new_dir = Path("new/cache/directory")

        validated = validator.validate(new_dir, create_if_missing=True)

        # Directory should now exist
        assert validated.exists()
        assert validated.is_dir()

    def test_validate_path_outside_base_rejected(self, safe_base_dir):
        """Test that paths resolving outside base are rejected."""
        validator = PathValidator(
            allowed_base=safe_base_dir / "allowed",
            allow_absolute=False,
            allow_symlinks=False,
        )

        # This path resolves outside allowed base
        malicious_path = Path("../..")

        with pytest.raises(PathTraversalError) as exc_info:
            validator.validate(malicious_path)

        # Accept either "parent directory traversal" (caught early) or "outside allowed base"
        error_msg = str(exc_info.value).lower()
        assert "parent directory traversal" in error_msg or "outside allowed base" in error_msg

    def test_validate_symlink_blocked_when_not_allowed(self, validator, safe_base_dir):
        """Test that symbolic links are blocked when not allowed."""
        # Create actual file
        actual_file = safe_base_dir / "actual.txt"
        actual_file.write_text("test")

        # Create symlink
        symlink = safe_base_dir / "link.txt"
        symlink.symlink_to(actual_file)

        with pytest.raises(PathTraversalError) as exc_info:
            validator.validate(Path("link.txt"))

        assert "symbolic link" in str(exc_info.value).lower()

    def test_validate_symlink_allowed_when_configured(self, safe_base_dir):
        """Test that symlinks are allowed when configured."""
        permissive_validator = PathValidator(
            allowed_base=safe_base_dir,
            allow_absolute=False,
            allow_symlinks=True,
        )

        # Create actual file
        actual_file = safe_base_dir / "actual.txt"
        actual_file.write_text("test")

        # Create symlink
        symlink = safe_base_dir / "link.txt"
        symlink.symlink_to(actual_file)

        # Should not raise
        validated = permissive_validator.validate(Path("link.txt"))
        assert validated.exists()

    def test_validate_batch_all_pass(self, validator):
        """Test batch validation when all paths pass."""
        paths = [
            Path("cache/model1"),
            Path("cache/model2"),
            Path("data/uploads"),
        ]

        # Should not raise
        validated = validator.validate_batch(paths)
        assert len(validated) == 3

    def test_validate_batch_one_fails(self, validator):
        """Test batch validation fails if any path fails."""
        paths = [
            Path("cache/model1"),
            Path("../etc/passwd"),  # Malicious
            Path("data/uploads"),
        ]

        with pytest.raises(PathTraversalError) as exc_info:
            validator.validate_batch(paths)

        assert "path 1" in str(exc_info.value).lower()

    def test_validate_non_path_type_raises_error(self, validator):
        """Test that non-Path/str types raise TypeError."""
        invalid_input = 12345

        with pytest.raises(TypeError):
            validator.validate(invalid_input)


class TestConvenienceFunctions:
    """Test convenience functions for path validation."""

    def test_validate_path_convenience_function(self, safe_base_dir):
        """Test validate_path convenience function."""
        safe_path = "cache/models"

        validated = validate_path(
            safe_path,
            allowed_base=safe_base_dir,
            allow_absolute=False,
        )

        assert str(validated).startswith(str(safe_base_dir.resolve()))

    def test_validate_path_rejects_traversal(self, safe_base_dir):
        """Test convenience function rejects path traversal."""
        malicious_path = "../etc/passwd"

        with pytest.raises(PathTraversalError):
            validate_path(
                malicious_path,
                allowed_base=safe_base_dir,
                allow_absolute=False,
            )

    def test_validate_cli_path_with_none_returns_none(self):
        """Test validate_cli_path returns None for None input."""
        result = validate_cli_path(None)
        assert result is None

    def test_validate_cli_path_validates_safe_path(self):
        """Test validate_cli_path validates safe relative paths."""
        # Use a path relative to cwd
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create safe path
                safe_path = "cache/models"
                validated = validate_cli_path(safe_path, create_if_missing=True)

                assert validated.exists()
                assert str(validated).startswith(str(Path(tmpdir).resolve()))

            finally:
                os.chdir(original_cwd)

    def test_validate_cli_path_blocks_traversal(self):
        """Test validate_cli_path blocks path traversal."""
        malicious_path = "../../../etc/passwd"

        with pytest.raises(PathTraversalError):
            validate_cli_path(malicious_path)

    def test_validate_cli_path_blocks_absolute_paths(self):
        """Test validate_cli_path blocks absolute paths."""
        absolute_path = "/etc/passwd"

        with pytest.raises(PathTraversalError):
            validate_cli_path(absolute_path)


class TestSecurityCompliance:
    """Test security compliance features."""

    def test_prevents_etc_passwd_attack(self, validator):
        """Test that /etc/passwd attack is prevented.

        Security (v0.5.7 HIGH-5): Classic path traversal attack.
        """
        # Absolute path attack
        with pytest.raises(PathTraversalError):
            validator.validate("/etc/passwd")

        # Relative path traversal attack
        with pytest.raises(PathTraversalError):
            validator.validate("../../../../etc/passwd")

    def test_prevents_hidden_traversal_via_resolution(self, validator, safe_base_dir):
        """Test that traversal hidden in path resolution is caught."""
        # Even if a path doesn't have .. in it initially,
        # if it resolves outside allowed_base, it should be rejected

        # Create a validator with a nested allowed base
        nested_validator = PathValidator(
            allowed_base=safe_base_dir / "allowed" / "subdir",
            allow_absolute=False,
            allow_symlinks=False,
        )

        # Try to escape via a path that resolves outside
        with pytest.raises(PathTraversalError):
            nested_validator.validate("../../outside")

    def test_prevents_symlink_attack(self, validator, safe_base_dir):
        """Test that symlink attacks are prevented.

        Security (v0.5.7 HIGH-5): Symlinks can bypass path restrictions.
        """
        # Create symlink to sensitive location
        symlink_path = safe_base_dir / "innocent_link"
        # Symlink to parent directory (outside allowed base conceptually)
        symlink_path.symlink_to(safe_base_dir.parent)

        # Should be blocked
        with pytest.raises(PathTraversalError):
            validator.validate("innocent_link")

    def test_null_byte_injection_prevented(self, validator):
        """Test that null byte injection is prevented.

        Security (v0.5.7 HIGH-5): Null bytes can truncate paths in some languages.
        """
        malicious_paths = [
            "cache\x00malicious",
            "safe/path\x00/etc/passwd",
            "\x00etc/passwd",
        ]

        for path in malicious_paths:
            with pytest.raises(PathTraversalError):
                validator.validate(path)


class TestCLIIntegrationScenarios:
    """Test realistic CLI integration scenarios."""

    def test_cli_cache_dir_validation(self):
        """Test validating CLI --cache-dir argument."""
        # Simulate CLI usage: ragged gpu download --cache-dir ./models
        cache_dir_arg = "./models"

        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                validated = validate_cli_path(cache_dir_arg, create_if_missing=True)

                assert validated.exists()
                assert validated.is_dir()
                assert str(validated).startswith(str(Path(tmpdir).resolve()))

            finally:
                os.chdir(original_cwd)

    def test_cli_rejects_malicious_cache_dir(self):
        """Test CLI rejects malicious --cache-dir arguments."""
        malicious_args = [
            "../../../etc",
            "/etc/passwd",
            "safe/../../../etc",
        ]

        for arg in malicious_args:
            with pytest.raises(PathTraversalError):
                validate_cli_path(arg)

    def test_cli_output_dir_validation(self):
        """Test validating CLI --output-dir argument."""
        output_dir_arg = "output/results"

        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                validated = validate_cli_path(output_dir_arg, create_if_missing=True)

                assert validated.exists()
                assert "output/results" in str(validated) or "output" in str(validated)

            finally:
                os.chdir(original_cwd)
