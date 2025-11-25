"""Tests for plugin sandbox resource limit enforcement.

v0.6.2 SECURITY-005: Verify that sandbox resource limits are actually enforced
with real test plugins that attempt to violate limits.

These tests use executable test plugins in tests/plugins/ to verify:
- Memory limits prevent excessive allocation
- CPU limits trigger SIGXCPU
- Network isolation blocks connections (Linux only)
- Process limits prevent fork bombs
- Filesystem restrictions are enforced
"""

import sys
from pathlib import Path

import pytest

from ragged.plugins.sandbox import (
    PluginSandbox,
    SandboxConfig,
    SandboxResult,
)

# Path to test plugins
PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


class TestMemoryLimitEnforcement:
    """Test that memory limits are actually enforced."""

    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="Memory limits (RLIMIT_AS) not reliably enforced on macOS"
    )
    def test_memory_limit_enforced(self):
        """Verify that memory_hog plugin is killed when exceeding limit."""
        # Configure sandbox with 100MB memory limit
        config = SandboxConfig(
            max_memory_mb=100,
            max_cpu_seconds=30,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("memory_hog_test", config=config)

        # Execute memory hog plugin (attempts to allocate 1GB)
        plugin_path = str(PLUGINS_DIR / "memory_hog.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # Memory hog should be killed by SIGKILL (OOM)
        assert result.result == SandboxResult.MEMORY_LIMIT, (
            f"Expected MEMORY_LIMIT but got {result.result}. "
            f"Exit code: {result.exit_code}, Error: {result.error}"
        )

        # Should have allocated some memory before being killed
        assert result.output is not None
        assert "Allocated:" in result.output

    def test_memory_within_limit_succeeds(self):
        """Verify that plugins within memory limit can execute successfully."""
        # Configure sandbox with generous 500MB limit
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("memory_normal_test", config=config)

        # Execute a simple plugin that doesn't exceed limits
        plugin_path = str(PLUGINS_DIR / "simple_success.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        assert result.result == SandboxResult.SUCCESS
        assert result.exit_code == 0
        assert "Hello" in result.output


class TestCPULimitEnforcement:
    """Test that CPU time limits are actually enforced."""

    def test_cpu_limit_enforced(self):
        """Verify that cpu_burner plugin receives SIGXCPU when exceeding limit."""
        # Configure sandbox with 5 second CPU limit
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=5,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("cpu_burner_test", config=config)

        # Execute CPU burner plugin (attempts to use 60s CPU time)
        plugin_path = str(PLUGINS_DIR / "cpu_burner.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # CPU burner should be killed by SIGXCPU
        assert result.result == SandboxResult.TIMEOUT, (
            f"Expected TIMEOUT (SIGXCPU) but got {result.result}. "
            f"Exit code: {result.exit_code}, Error: {result.error}"
        )

        # Output may be empty if killed before any output was flushed
        # Just verify it was killed by timeout (which we already checked above)

    def test_cpu_within_limit_succeeds(self):
        """Verify that plugins within CPU limit can execute successfully."""
        # Configure sandbox with reasonable 10 second CPU limit
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=10,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("cpu_normal_test", config=config)

        # Execute a simple fast plugin
        plugin_path = str(PLUGINS_DIR / "simple_success.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        assert result.result == SandboxResult.SUCCESS
        assert result.exit_code == 0


class TestNetworkIsolationEnforcement:
    """Test that network isolation is enforced (Linux only)."""

    @pytest.mark.skipif(
        sys.platform != "linux",
        reason="Network isolation only enforced on Linux"
    )
    def test_network_isolation_enforced_linux(self):
        """Verify that network_accessor plugin cannot access network on Linux."""
        # Configure sandbox with network blocking
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            block_network=True,
            execution_timeout_seconds=60,
        )

        sandbox = PluginSandbox("network_accessor_test", config=config)

        # Execute network accessor plugin
        plugin_path = str(PLUGINS_DIR / "network_accessor.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # On Linux with proper capabilities, all network access should be blocked
        # The plugin exits with 0 if all operations were blocked (expected)
        assert result.exit_code == 0, (
            f"Network operations should have been blocked. "
            f"Exit code: {result.exit_code}, Output: {result.output}"
        )

        # Verify that operations were actually blocked
        assert result.output is not None
        assert "BLOCKED:" in result.output or "All network operations properly blocked" in result.output

    @pytest.mark.skipif(
        sys.platform == "linux",
        reason="Test non-Linux platform behavior"
    )
    def test_network_isolation_platform_dependent(self):
        """Verify network_accessor behavior on non-Linux platforms."""
        # Configure sandbox with network blocking
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            block_network=True,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("network_accessor_test", config=config)

        # Execute network accessor plugin
        plugin_path = str(PLUGINS_DIR / "network_accessor.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # On non-Linux platforms, network blocking may not be enforced
        # Just verify the plugin executed without crashing
        assert result.result in [SandboxResult.SUCCESS, SandboxResult.CRASHED]

        # Log platform-specific behavior for documentation
        if result.exit_code == 1:
            print(f"Platform {sys.platform}: Some network operations succeeded (expected)")
        else:
            print(f"Platform {sys.platform}: Network operations blocked")


class TestProcessLimitEnforcement:
    """Test that process limits prevent fork bombs."""

    def test_fork_bomb_prevented(self):
        """Verify that fork_bomb plugin cannot spawn excessive processes."""
        # Configure sandbox with strict 1 process limit
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("fork_bomb_test", config=config)

        # Execute fork bomb plugin
        plugin_path = str(PLUGINS_DIR / "fork_bomb.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # Fork bomb should be prevented from spawning processes
        # It may exit with 0 (if no spawns succeeded) or crash
        assert result.result in [SandboxResult.SUCCESS, SandboxResult.CRASHED], (
            f"Expected SUCCESS or CRASHED but got {result.result}"
        )

        # Verify that process spawning was blocked
        if result.output:
            # Should have "BLOCKED:" messages or successful enforcement message
            assert ("BLOCKED:" in result.output or
                    "Process limit properly enforced" in result.output or
                    "spawned 0 processes" in result.output), (
                f"Process spawning should have been blocked. Output: {result.output}"
            )

    def test_process_limit_allows_main_process(self):
        """Verify that the main process itself can execute within limits."""
        # Configure sandbox with 1 process limit (the main process)
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("process_normal_test", config=config)

        # Execute a simple plugin without spawning
        plugin_path = str(PLUGINS_DIR / "simple_success.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        assert result.result == SandboxResult.SUCCESS
        assert result.exit_code == 0


class TestFilesystemRestrictionEnforcement:
    """Test that filesystem restrictions are enforced."""

    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="Filesystem restrictions require Linux namespaces or sandbox-exec on macOS"
    )
    def test_filesystem_restrictions_enforced(self):
        """Verify that file_accessor plugin cannot access restricted paths."""
        # Configure sandbox without explicit allowed paths
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("file_accessor_test", config=config)

        # Execute file accessor plugin
        plugin_path = str(PLUGINS_DIR / "file_accessor.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # File accessor should report proper enforcement (exit code 0)
        # or permission errors (various exit codes)
        assert result.result in [SandboxResult.SUCCESS, SandboxResult.CRASHED]

        # Verify filesystem access was appropriately restricted
        if result.output:
            # Should have successful temp access but blocked system access
            assert "allowed_temp: SUCCEEDED" in result.output or "SUCCESS: Temp file access" in result.output

            # Unauthorized accesses should be blocked
            assert ("BLOCKED:" in result.output or
                    "Filesystem restrictions properly enforced" in result.output)

    def test_filesystem_allows_temp_access(self):
        """Verify that plugins can access allowed temporary directories."""
        # Configure sandbox
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=30,
            max_processes=1,
            execution_timeout_seconds=60,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("filesystem_normal_test", config=config)

        # Execute simple plugin that should succeed
        plugin_path = str(PLUGINS_DIR / "simple_success.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        assert result.result == SandboxResult.SUCCESS
        assert result.exit_code == 0


class TestExecutionTimeout:
    """Test that execution timeout is enforced."""

    def test_execution_timeout_enforced(self):
        """Verify that long-running plugins are killed by timeout."""
        # Configure sandbox with very short 2 second timeout
        config = SandboxConfig(
            max_memory_mb=500,
            max_cpu_seconds=60,  # High CPU limit
            max_processes=1,
            execution_timeout_seconds=2,  # But short wall-clock timeout
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("timeout_test", config=config)

        # Execute sleeper plugin that sleeps for 10 seconds
        plugin_path = str(PLUGINS_DIR / "sleeper.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # Should timeout
        assert result.result == SandboxResult.TIMEOUT
        assert result.duration_ms >= 2000  # At least 2 seconds
        assert result.output is None or "Should not print" not in result.output


class TestSandboxConfiguration:
    """Test sandbox configuration edge cases."""

    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="Zero memory limit not enforced on macOS"
    )
    def test_zero_memory_limit_rejected(self):
        """Verify that invalid configuration is handled."""
        # Test creating sandbox with invalid config
        config = SandboxConfig(
            max_memory_mb=0,  # Invalid
            max_cpu_seconds=10,
            max_processes=1,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("invalid_config_test", config=config)

        # Should fail to execute with invalid limits
        plugin_path = str(PLUGINS_DIR / "simple_success.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        # May crash or fail depending on OS
        assert result.result in [SandboxResult.CRASHED, SandboxResult.MEMORY_LIMIT]

    def test_high_limits_allow_execution(self):
        """Verify that generous limits allow normal execution."""
        # Configure sandbox with very high limits
        config = SandboxConfig(
            max_memory_mb=2000,
            max_cpu_seconds=60,
            max_processes=10,
            execution_timeout_seconds=120,
            additional_allowed_dirs=[PLUGINS_DIR],
        )

        sandbox = PluginSandbox("high_limits_test", config=config)

        # Execute a normal plugin
        plugin_path = str(PLUGINS_DIR / "simple_success.py")
        result = sandbox.execute(
            plugin_path,
            [],
        )

        assert result.result == SandboxResult.SUCCESS
        assert result.exit_code == 0


# Platform-specific documentation tests
def test_sandbox_capabilities_documented():
    """Verify that sandbox capabilities are documented per platform."""
    # This test ensures documentation exists
    docs_path = Path(__file__).parent.parent.parent / "docs" / "development" / "plugins"
    assert docs_path.exists(), "Plugin documentation directory should exist"

    # Check for sandbox.md
    sandbox_doc = docs_path / "sandbox.md"
    if sandbox_doc.exists():
        content = sandbox_doc.read_text()

        # Should document platform-specific capabilities
        assert "Linux" in content or "linux" in content
        assert "network" in content.lower()
        assert "memory" in content.lower()
        assert "CPU" in content or "cpu" in content

        print("Sandbox capabilities documented in docs/development/plugins/sandbox.md")
    else:
        pytest.skip("Sandbox documentation not yet created")
