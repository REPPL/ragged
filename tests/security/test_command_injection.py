"""Security tests for CRITICAL-1: Command injection prevention in sandbox."""

import pytest
import tempfile
from pathlib import Path

from ragged.plugins.sandbox import PluginSandbox, SandboxConfig, SandboxViolation


class TestCommandInjectionPrevention:
    """Tests for command injection prevention (CRITICAL-1)."""

    @pytest.fixture
    def sandbox(self):
        """Create sandbox for testing."""
        return PluginSandbox("test_plugin")

    @pytest.fixture
    def safe_plugin_dir(self, tmp_path):
        """Create a safe plugin directory with test executable."""
        plugin_dir = Path.home() / ".ragged" / "plugins" / "test_plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create a safe test script
        test_script = plugin_dir / "safe_script.py"
        test_script.write_text("#!/usr/bin/env python3\nprint('Hello from plugin')\n")
        test_script.chmod(0o755)

        yield plugin_dir

        # Cleanup
        if test_script.exists():
            test_script.unlink()

    def test_block_system_binaries(self, sandbox):
        """Test that system binaries are blocked."""
        dangerous_binaries = [
            "/bin/sh",
            "/bin/bash",
            "/usr/bin/python3",
            "/usr/bin/curl",
            "/bin/rm",
        ]

        for binary in dangerous_binaries:
            with pytest.raises(SandboxViolation, match="within allowed plugin directories"):
                sandbox.execute(binary, [])

    def test_block_command_injection_via_executable(self, sandbox):
        """Test that command injection via executable path is blocked."""
        injection_attempts = [
            "/bin/sh -c whoami",
            "$(whoami)",
            "`whoami`",
            "/bin/sh; whoami",
            "/bin/sh | whoami",
        ]

        for injection in injection_attempts:
            with pytest.raises(SandboxViolation):
                sandbox.execute(injection, [])

    def test_block_path_traversal_in_executable(self, sandbox):
        """Test that path traversal in executable is blocked."""
        traversal_attempts = [
            "../../../bin/sh",
            "../../etc/passwd",
            "./../../../usr/bin/python3",
        ]

        for traversal in traversal_attempts:
            with pytest.raises(SandboxViolation):
                sandbox.execute(traversal, [])

    def test_block_shell_metacharacters_in_args(self, sandbox, safe_plugin_dir):
        """Test that shell metacharacters in arguments are blocked."""
        safe_executable = str(safe_plugin_dir / "safe_script.py")

        dangerous_args = [
            ["; whoami"],
            ["| cat /etc/passwd"],
            ["&& rm -rf /"],
            ["$(whoami)"],
            ["`whoami`"],
            ["> /tmp/output"],
            ["< /etc/passwd"],
            ["( whoami )"],
        ]

        for args in dangerous_args:
            with pytest.raises(SandboxViolation, match="forbidden character"):
                sandbox.execute(safe_executable, args)

    def test_block_null_bytes_in_args(self, sandbox, safe_plugin_dir):
        """Test that null bytes in arguments are blocked."""
        safe_executable = str(safe_plugin_dir / "safe_script.py")

        with pytest.raises(SandboxViolation, match="null byte"):
            sandbox.execute(safe_executable, ["arg\x00injection"])

    def test_block_oversized_arguments(self, sandbox, safe_plugin_dir):
        """Test that overly long arguments are blocked."""
        safe_executable = str(safe_plugin_dir / "safe_script.py")

        huge_arg = "A" * 5000  # Exceeds 4096 byte limit

        with pytest.raises(SandboxViolation, match="too long"):
            sandbox.execute(safe_executable, [huge_arg])

    def test_block_nonexistent_executable(self, sandbox):
        """Test that nonexistent executables are blocked."""
        fake_path = Path.home() / ".ragged" / "plugins" / "nonexistent" / "fake.py"

        with pytest.raises(SandboxViolation, match="does not exist"):
            sandbox.execute(str(fake_path), [])

    def test_block_directory_as_executable(self, sandbox):
        """Test that directories cannot be executed."""
        plugin_dir = Path.home() / ".ragged" / "plugins" / "test_plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(SandboxViolation, match="not a regular file"):
            sandbox.execute(str(plugin_dir), [])

    def test_block_dangerous_symlinks(self, sandbox, safe_plugin_dir):
        """Test that symlinks pointing outside allowed directories are blocked."""
        # Create symlink to dangerous location
        symlink_path = safe_plugin_dir / "dangerous_link"
        try:
            symlink_path.symlink_to("/bin/sh")

            with pytest.raises(SandboxViolation, match="within allowed plugin directories"):
                sandbox.execute(str(symlink_path), [])
        finally:
            if symlink_path.exists():
                symlink_path.unlink()

    def test_allow_safe_executable(self, sandbox, safe_plugin_dir):
        """Test that safe executables within plugin directory are allowed."""
        safe_executable = str(safe_plugin_dir / "safe_script.py")

        # This should validate without raising exception
        # (execution may fail but validation should pass)
        try:
            result = sandbox.execute(safe_executable, ["arg1", "arg2"])
            # If it executes, that's fine
        except SandboxViolation:
            # Should not raise SandboxViolation for valid paths
            pytest.fail("Safe executable was incorrectly blocked")
        except Exception:
            # Other exceptions (like execution errors) are acceptable
            pass

    def test_allow_safe_arguments(self, sandbox, safe_plugin_dir):
        """Test that safe arguments are allowed."""
        safe_executable = str(safe_plugin_dir / "safe_script.py")

        safe_args = [
            ["--help"],
            ["--verbose"],
            ["input.txt"],
            ["--output=result.json"],
            ["-v", "-vv", "-vvv"],
        ]

        for args in safe_args:
            try:
                sandbox.execute(safe_executable, args)
            except SandboxViolation:
                pytest.fail(f"Safe arguments were incorrectly blocked: {args}")
            except Exception:
                # Other exceptions are acceptable
                pass

    def test_path_canonicalization(self, sandbox, safe_plugin_dir):
        """Test that paths are properly canonicalized."""
        # Create executable
        safe_script = safe_plugin_dir / "test.py"
        safe_script.write_text("#!/usr/bin/env python3\nprint('test')\n")
        safe_script.chmod(0o755)

        # Try with non-canonical path (should be accepted after resolution)
        non_canonical = safe_plugin_dir / "." / "test.py"

        try:
            sandbox.execute(str(non_canonical), [])
        except SandboxViolation:
            pytest.fail("Canonical path resolution failed")
        except Exception:
            # Other exceptions are acceptable
            pass
        finally:
            if safe_script.exists():
                safe_script.unlink()


class TestExecutableValidation:
    """Tests for executable path validation method."""

    def test_validate_executable_path_resolution(self):
        """Test that executable paths are resolved correctly."""
        sandbox = PluginSandbox("test")

        # Create test executable
        plugin_dir = Path.home() / ".ragged" / "plugins" / "test"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        test_exec = plugin_dir / "test.py"
        test_exec.write_text("#!/usr/bin/env python3\nprint('test')\n")
        test_exec.chmod(0o755)

        try:
            validated = sandbox._validate_executable_path(str(test_exec))
            assert Path(validated).is_absolute()
            assert Path(validated).exists()
        finally:
            if test_exec.exists():
                test_exec.unlink()

    def test_validate_arguments_rejects_metacharacters(self):
        """Test that argument validation rejects shell metacharacters."""
        sandbox = PluginSandbox("test")

        dangerous_args = [
            ["; echo pwned"],
            ["| cat /etc/passwd"],
            ["&& malicious"],
            ["$( injection )"],
            ["`backtick`"],
        ]

        for args in dangerous_args:
            with pytest.raises(SandboxViolation):
                sandbox._validate_arguments(args)

    def test_validate_arguments_accepts_safe_args(self):
        """Test that argument validation accepts safe arguments."""
        sandbox = PluginSandbox("test")

        safe_args = [
            ["--verbose"],
            ["--output", "file.txt"],
            ["input.json"],
            ["-vvv"],
        ]

        for args in safe_args:
            # Should not raise exception
            sandbox._validate_arguments(args)
