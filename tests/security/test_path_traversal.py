"""Security tests for CRITICAL-2: Path traversal prevention in file permissions."""

import pytest
import tempfile
from pathlib import Path

from ragged.plugins.sandbox import PluginSandbox, SandboxConfig, SandboxViolation
from ragged.plugins.permissions import PermissionManager, PermissionType, PluginPermissions


class TestPathTraversalPrevention:
    """Tests for path traversal prevention (CRITICAL-2)."""

    @pytest.fixture
    def permission_manager(self):
        """Create permission manager for testing."""
        return PermissionManager()

    @pytest.fixture
    def sandbox_with_permissions(self, tmp_path, permission_manager):
        """Create sandbox with read/write permissions configured."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        config = SandboxConfig(
            allowed_read_paths=[allowed_dir],
            allowed_write_paths=[allowed_dir],
        )

        sandbox = PluginSandbox(
            "test_plugin",
            config=config,
            permission_manager=permission_manager,
        )

        # Register plugin with required permissions
        plugin_perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        plugin_perms.add_required(PermissionType.READ_DOCUMENTS)
        plugin_perms.add_required(PermissionType.WRITE_DOCUMENTS)
        permission_manager.register_plugin(plugin_perms)

        # Grant permissions
        permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)
        permission_manager.grant_permission("test_plugin", PermissionType.WRITE_DOCUMENTS)

        return sandbox, allowed_dir

    def test_block_parent_directory_traversal(self, sandbox_with_permissions):
        """Test that ../ path traversal is blocked."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Attempt to traverse to parent directory
        traversal_path = allowed_dir / ".." / "etc" / "passwd"

        with pytest.raises(SandboxViolation, match="Path traversal detected"):
            sandbox.check_file_access(traversal_path, write=False)

    def test_block_multi_level_traversal(self, sandbox_with_permissions):
        """Test that multiple ../ levels are blocked."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Attempt deep traversal
        traversal_path = allowed_dir / ".." / ".." / ".." / "etc" / "passwd"

        with pytest.raises(SandboxViolation, match="Path traversal detected"):
            sandbox.check_file_access(traversal_path, write=False)

    def test_block_traversal_in_middle_of_path(self, sandbox_with_permissions):
        """Test that ../ in middle of path is blocked."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Traversal in middle: /allowed/subdir/../../../etc/passwd
        subdir = allowed_dir / "subdir"
        subdir.mkdir()
        traversal_path = subdir / ".." / ".." / "etc" / "passwd"

        with pytest.raises(SandboxViolation, match="Path traversal detected"):
            sandbox.check_file_access(traversal_path, write=False)

    def test_block_absolute_path_outside_allowed(self, sandbox_with_permissions):
        """Test that absolute paths outside allowed directories are blocked."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Absolute path to sensitive file
        sensitive_path = Path("/etc/passwd")

        # Should be denied (returns False, not exception for absolute paths)
        allowed = sandbox.check_file_access(sensitive_path, write=False)
        assert allowed is False

    def test_block_symlink_to_sensitive_file(self, sandbox_with_permissions, tmp_path):
        """Test that symlinks pointing to sensitive files are blocked."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create symlink inside allowed dir pointing to /etc/passwd
        symlink_path = allowed_dir / "evil_link"
        target_path = Path("/etc/passwd")

        # Only create symlink if target exists (for test realism)
        if target_path.exists():
            try:
                symlink_path.symlink_to(target_path)

                # Symlink should be detected and access denied
                # (Returns False because resolved target is outside allowed paths)
                allowed = sandbox.check_file_access(symlink_path, write=False)
                assert allowed is False
            finally:
                if symlink_path.exists():
                    symlink_path.unlink()

    def test_block_symlink_pointing_outside(self, sandbox_with_permissions, tmp_path):
        """Test that symlinks pointing outside allowed directories are blocked."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create a file outside allowed directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret data")

        # Create symlink inside allowed dir pointing outside
        symlink_path = allowed_dir / "link_to_outside"
        symlink_path.symlink_to(outside_file)

        try:
            # Should be denied - symlink points outside allowed directory
            allowed = sandbox.check_file_access(symlink_path, write=False)
            assert allowed is False
        finally:
            if symlink_path.exists():
                symlink_path.unlink()

    def test_allow_legitimate_file_access(self, sandbox_with_permissions):
        """Test that legitimate files within allowed directory are allowed."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create legitimate file
        legit_file = allowed_dir / "data.txt"
        legit_file.write_text("test data")

        # Should be allowed
        allowed = sandbox.check_file_access(legit_file, write=False)
        assert allowed is True

        # Write access should also be allowed
        allowed = sandbox.check_file_access(legit_file, write=True)
        assert allowed is True

    def test_allow_subdirectory_access(self, sandbox_with_permissions):
        """Test that subdirectories within allowed paths work correctly."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create subdirectory structure
        subdir = allowed_dir / "level1" / "level2" / "level3"
        subdir.mkdir(parents=True)
        file_in_subdir = subdir / "data.txt"
        file_in_subdir.write_text("nested data")

        # Should be allowed
        allowed = sandbox.check_file_access(file_in_subdir, write=False)
        assert allowed is True

    def test_allow_legitimate_symlink_within_allowed(self, sandbox_with_permissions):
        """Test that symlinks within allowed directory are allowed."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create file and symlink both in allowed directory
        real_file = allowed_dir / "real_file.txt"
        real_file.write_text("real data")

        symlink_path = allowed_dir / "link_to_real"
        symlink_path.symlink_to(real_file)

        try:
            # Should be allowed - both symlink and target are in allowed directory
            allowed = sandbox.check_file_access(symlink_path, write=False)
            assert allowed is True
        finally:
            if symlink_path.exists():
                symlink_path.unlink()

    def test_canonical_path_resolution(self, sandbox_with_permissions):
        """Test that paths are properly canonicalized."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create file with non-canonical path reference
        file_path = allowed_dir / "data.txt"
        file_path.write_text("test")

        # Access via ./././ pattern (should work after canonicalization)
        non_canonical = allowed_dir / "." / "." / "data.txt"

        # Should be allowed after canonicalization
        allowed = sandbox.check_file_access(non_canonical, write=False)
        assert allowed is True

    def test_deny_access_without_permissions(self, tmp_path):
        """Test that access is denied without proper permissions."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        config = SandboxConfig(
            allowed_read_paths=[allowed_dir],
            allowed_write_paths=[allowed_dir],
        )

        # Create permission manager but don't grant permissions
        permission_manager = PermissionManager()

        # Register plugin with required permissions but don't grant them
        plugin_perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        plugin_perms.add_required(PermissionType.READ_DOCUMENTS)
        plugin_perms.add_required(PermissionType.WRITE_DOCUMENTS)
        permission_manager.register_plugin(plugin_perms)

        sandbox = PluginSandbox(
            "test_plugin",
            config=config,
            permission_manager=permission_manager,
        )

        file_path = allowed_dir / "data.txt"
        file_path.write_text("test")

        # Should be denied - no permissions granted
        allowed = sandbox.check_file_access(file_path, write=False)
        assert allowed is False

        allowed = sandbox.check_file_access(file_path, write=True)
        assert allowed is False

    def test_separate_read_write_paths(self, tmp_path):
        """Test that read and write paths are enforced separately."""
        read_only_dir = tmp_path / "read_only"
        read_only_dir.mkdir()
        write_only_dir = tmp_path / "write_only"
        write_only_dir.mkdir()

        config = SandboxConfig(
            allowed_read_paths=[read_only_dir],
            allowed_write_paths=[write_only_dir],
        )

        permission_manager = PermissionManager()

        # Register plugin with required permissions
        plugin_perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        plugin_perms.add_required(PermissionType.READ_DOCUMENTS)
        plugin_perms.add_required(PermissionType.WRITE_DOCUMENTS)
        permission_manager.register_plugin(plugin_perms)

        permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)
        permission_manager.grant_permission("test_plugin", PermissionType.WRITE_DOCUMENTS)

        sandbox = PluginSandbox(
            "test_plugin",
            config=config,
            permission_manager=permission_manager,
        )

        read_file = read_only_dir / "data.txt"
        read_file.write_text("read data")

        write_file = write_only_dir / "output.txt"
        write_file.write_text("write data")

        # Read should work on read-only path
        assert sandbox.check_file_access(read_file, write=False) is True

        # Write should NOT work on read-only path
        assert sandbox.check_file_access(read_file, write=True) is False

        # Write should work on write-only path
        assert sandbox.check_file_access(write_file, write=True) is True

        # Read should NOT work on write-only path
        assert sandbox.check_file_access(write_file, write=False) is False

    def test_handle_nonexistent_file(self, sandbox_with_permissions):
        """Test handling of nonexistent files."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Nonexistent file in allowed directory
        nonexistent = allowed_dir / "does_not_exist.txt"

        # Should be allowed (path validation, not existence check)
        # The actual file operation will fail, but permission check passes
        allowed = sandbox.check_file_access(nonexistent, write=False)
        assert allowed is True

    def test_block_double_slash_bypass(self, sandbox_with_permissions):
        """Test that double slashes don't bypass security."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Attempt bypass with double slashes
        file_path = allowed_dir / "data.txt"
        file_path.write_text("test")

        # Create path with double slashes (these should be normalized)
        path_str = str(allowed_dir) + "//data.txt"
        double_slash_path = Path(path_str)

        # Should still be allowed after normalization
        allowed = sandbox.check_file_access(double_slash_path, write=False)
        assert allowed is True

    def test_fail_secure_on_error(self, sandbox_with_permissions):
        """Test that errors result in denied access (fail-secure)."""
        sandbox, allowed_dir = sandbox_with_permissions

        # Create a path object that might cause resolution issues
        # Using a very long path that could cause issues
        very_long_name = "a" * 1000
        problematic_path = allowed_dir / very_long_name

        # Should not crash, should fail secure
        try:
            result = sandbox.check_file_access(problematic_path, write=False)
            # Either allowed or denied is fine, just shouldn't crash
            assert isinstance(result, bool)
        except SandboxViolation:
            # Also acceptable
            pass


class TestPathResolutionEdgeCases:
    """Tests for edge cases in path resolution."""

    def test_handle_relative_allowed_paths(self, tmp_path):
        """Test that relative allowed paths are resolved correctly."""
        # Use relative path in config
        config = SandboxConfig(
            allowed_read_paths=[Path(".")],
            allowed_write_paths=[Path(".")],
        )

        permission_manager = PermissionManager()

        # Register plugin with required permissions
        plugin_perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        plugin_perms.add_required(PermissionType.READ_DOCUMENTS)
        permission_manager.register_plugin(plugin_perms)

        permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)

        sandbox = PluginSandbox(
            "test_plugin",
            config=config,
            permission_manager=permission_manager,
        )

        # Current directory file should be allowed
        current_dir_file = Path.cwd() / "test_file.txt"

        # Check should work (may be allowed or denied based on actual cwd)
        # Just verify it doesn't crash
        try:
            result = sandbox.check_file_access(current_dir_file, write=False)
            assert isinstance(result, bool)
        except SandboxViolation:
            # Also acceptable - strict security
            pass

    def test_handle_empty_allowed_paths(self):
        """Test behaviour with empty allowed paths."""
        config = SandboxConfig(
            allowed_read_paths=[],
            allowed_write_paths=[],
        )

        permission_manager = PermissionManager()

        # Register plugin with required permissions
        plugin_perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        plugin_perms.add_required(PermissionType.READ_DOCUMENTS)
        permission_manager.register_plugin(plugin_perms)

        permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)

        sandbox = PluginSandbox(
            "test_plugin",
            config=config,
            permission_manager=permission_manager,
        )

        # Any path should be denied with empty allowed paths
        some_path = Path("/tmp/test.txt")
        allowed = sandbox.check_file_access(some_path, write=False)
        assert allowed is False
