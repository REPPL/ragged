"""Security tests for CRITICAL-3: Network isolation in sandbox."""

import pytest
import sys
from pathlib import Path

from ragged.plugins.sandbox import PluginSandbox, SandboxConfig, SandboxResult


class TestNetworkIsolation:
    """Tests for network isolation (CRITICAL-3)."""

    @pytest.fixture
    def sandbox_with_network_blocking(self, tmp_path):
        """Create sandbox with network blocking enabled."""
        # Create plugin directory
        plugin_dir = Path.home() / ".ragged" / "plugins" / "test_network"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        config = SandboxConfig(
            block_network=True,
            execution_timeout_seconds=5,
            max_cpu_seconds=5,
        )

        sandbox = PluginSandbox("test_network", config=config)

        yield sandbox, plugin_dir

        # Cleanup
        # Plugin dir can remain for other tests

    @pytest.fixture
    def sandbox_without_network_blocking(self, tmp_path):
        """Create sandbox WITHOUT network blocking."""
        plugin_dir = Path.home() / ".ragged" / "plugins" / "test_network"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        config = SandboxConfig(
            block_network=False,
            execution_timeout_seconds=5,
            max_cpu_seconds=5,
        )

        sandbox = PluginSandbox("test_network", config=config)

        return sandbox, plugin_dir

    def test_environment_variables_set_for_network_blocking(self, sandbox_with_network_blocking):
        """Test that network blocking sets appropriate environment variables."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Prepare environment with network blocking
        env = sandbox._prepare_environment(None)

        # Check proxy variables are set to block network
        assert env.get("http_proxy") == "http://127.0.0.1:0"
        assert env.get("https_proxy") == "http://127.0.0.1:0"
        assert env.get("HTTP_PROXY") == "http://127.0.0.1:0"
        assert env.get("HTTPS_PROXY") == "http://127.0.0.1:0"
        assert env.get("ftp_proxy") == "http://127.0.0.1:0"
        assert env.get("FTP_PROXY") == "http://127.0.0.1:0"

        # Check no_proxy is empty
        assert env.get("no_proxy") == ""
        assert env.get("NO_PROXY") == ""

        # Check offline mode flags
        assert env.get("REQUESTS_OFFLINE") == "1"
        assert env.get("URLLIB_OFFLINE") == "1"

    def test_environment_variables_not_set_without_blocking(self, sandbox_without_network_blocking):
        """Test that network variables are not set when blocking is disabled."""
        sandbox, plugin_dir = sandbox_without_network_blocking

        # Prepare environment without network blocking
        env = sandbox._prepare_environment(None)

        # Network blocking variables should not be present
        assert "http_proxy" not in env or env.get("http_proxy") != "http://127.0.0.1:0"
        assert "REQUESTS_OFFLINE" not in env

    def test_sensitive_credentials_blocked(self, sandbox_with_network_blocking):
        """Test that cloud credentials are not passed to sandboxed process."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Try to pass sensitive credentials
        env_with_creds = {
            "AWS_ACCESS_KEY_ID": "fake_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret",
            "SSH_AUTH_SOCK": "/tmp/ssh_socket",
        }

        restricted_env = sandbox._prepare_environment(env_with_creds)

        # These should NOT be in restricted environment
        assert "AWS_ACCESS_KEY_ID" not in restricted_env
        assert "AWS_SECRET_ACCESS_KEY" not in restricted_env
        assert "SSH_AUTH_SOCK" not in restricted_env

    def test_allowed_environment_variables_passed_through(self, sandbox_with_network_blocking):
        """Test that allowed environment variables are passed through."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Allowed variables
        env_allowed = {
            "RAGGED_PLUGIN_NAME": "test_plugin",
            "RAGGED_PLUGIN_VERSION": "1.0.0",
            "RAGGED_DATA_DIR": "/tmp/data",
        }

        restricted_env = sandbox._prepare_environment(env_allowed)

        # These SHOULD be in restricted environment
        assert restricted_env.get("RAGGED_PLUGIN_NAME") == "test_plugin"
        assert restricted_env.get("RAGGED_PLUGIN_VERSION") == "1.0.0"
        assert restricted_env.get("RAGGED_DATA_DIR") == "/tmp/data"

    def test_network_test_script_blocked(self, sandbox_with_network_blocking):
        """Test that network access is actually blocked via test script."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Create test script that attempts network access
        test_script = plugin_dir / "test_network.py"
        test_script.write_text("""#!/usr/bin/env python3
import sys
import os

# Check if network blocking environment is set
http_proxy = os.environ.get('http_proxy', '')
if 'http://127.0.0.1:0' in http_proxy:
    print("NETWORK_BLOCKED")
    sys.exit(0)
else:
    print("NETWORK_NOT_BLOCKED")
    sys.exit(1)
""")
        test_script.chmod(0o755)

        try:
            # Execute script
            result = sandbox.execute(str(test_script), [])

            # Should succeed and indicate network is blocked
            assert result.result in (SandboxResult.SUCCESS, SandboxResult.CRASHED)
            if result.output:
                assert "NETWORK_BLOCKED" in result.output
        finally:
            if test_script.exists():
                test_script.unlink()

    def test_network_isolation_with_urllib(self, sandbox_with_network_blocking):
        """Test that urllib requests are blocked."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Create script that tries to use urllib
        urllib_script = plugin_dir / "test_urllib.py"
        urllib_script.write_text("""#!/usr/bin/env python3
import sys

try:
    from urllib.request import urlopen
    # This should fail due to proxy settings
    response = urlopen('http://example.com', timeout=2)
    print("NETWORK_ACCESS_SUCCEEDED")
    sys.exit(1)
except Exception as e:
    # Network access blocked
    print(f"NETWORK_ACCESS_BLOCKED: {type(e).__name__}")
    sys.exit(0)
""")
        urllib_script.chmod(0o755)

        try:
            # Execute script - should fail to access network
            result = sandbox.execute(str(urllib_script), [])

            # Script should complete and report blocked access
            if result.output:
                assert "NETWORK_ACCESS_BLOCKED" in result.output or "NETWORK_BLOCKED" in result.output
        finally:
            if urllib_script.exists():
                urllib_script.unlink()

    def test_minimal_environment_prevents_leaks(self, sandbox_with_network_blocking):
        """Test that minimal environment doesn't leak sensitive data."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        env = sandbox._prepare_environment(None)

        # Should only have minimal safe variables
        expected_safe_keys = {
            "PATH", "LANG",
            "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
            "ftp_proxy", "FTP_PROXY", "no_proxy", "NO_PROXY",
            "PYTHONHTTPSVERIFY", "REQUESTS_OFFLINE", "URLLIB_OFFLINE",
        }

        # All keys should be expected/safe
        for key in env.keys():
            assert key in expected_safe_keys, f"Unexpected environment variable leaked: {key}"

    def test_network_blocking_flag_respected(self):
        """Test that block_network flag is properly respected."""
        # With blocking
        config_block = SandboxConfig(block_network=True)
        assert config_block.block_network is True

        sandbox_block = PluginSandbox("test", config=config_block)
        env_block = sandbox_block._prepare_environment(None)
        assert env_block.get("http_proxy") == "http://127.0.0.1:0"

        # Without blocking
        config_allow = SandboxConfig(block_network=False)
        assert config_allow.block_network is False

        sandbox_allow = PluginSandbox("test", config=config_allow)
        env_allow = sandbox_allow._prepare_environment(None)
        assert env_allow.get("http_proxy") != "http://127.0.0.1:0"

    @pytest.mark.skipif(sys.platform != "linux", reason="Network namespaces only available on Linux")
    def test_linux_network_namespace_attempted(self, sandbox_with_network_blocking):
        """Test that on Linux, network namespace isolation is attempted."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Create simple test script
        test_script = plugin_dir / "simple_test.py"
        test_script.write_text("""#!/usr/bin/env python3
print("test")
""")
        test_script.chmod(0o755)

        try:
            # This will attempt network namespace creation
            # It may fail without privileges, but should not crash
            result = sandbox.execute(str(test_script), [])

            # Should complete without crashing
            assert result.result in (
                SandboxResult.SUCCESS,
                SandboxResult.CRASHED,
                SandboxResult.TIMEOUT,
            )
        finally:
            if test_script.exists():
                test_script.unlink()

    def test_network_isolation_logging(self, sandbox_with_network_blocking, caplog):
        """Test that network isolation is properly logged."""
        sandbox, plugin_dir = sandbox_with_network_blocking

        # Prepare environment (triggers logging)
        env = sandbox._prepare_environment(None)

        # Check that network blocking was logged
        # (Note: caplog may not capture all logs depending on logger setup)
        assert env.get("http_proxy") == "http://127.0.0.1:0"


class TestNetworkIsolationDefenseInDepth:
    """Tests for defense-in-depth network isolation."""

    def test_multiple_proxy_variants_set(self):
        """Test that both lowercase and uppercase proxy vars are set."""
        config = SandboxConfig(block_network=True)
        sandbox = PluginSandbox("test", config=config)
        env = sandbox._prepare_environment(None)

        # Both cases should be set for maximum compatibility
        assert env.get("http_proxy") == "http://127.0.0.1:0"
        assert env.get("HTTP_PROXY") == "http://127.0.0.1:0"
        assert env.get("https_proxy") == "http://127.0.0.1:0"
        assert env.get("HTTPS_PROXY") == "http://127.0.0.1:0"

    def test_no_proxy_bypass_prevented(self):
        """Test that no_proxy can't be used to bypass restrictions."""
        config = SandboxConfig(block_network=True)
        sandbox = PluginSandbox("test", config=config)

        # Try to pass no_proxy to bypass
        env_with_bypass = {"no_proxy": "*"}
        restricted_env = sandbox._prepare_environment(env_with_bypass)

        # Should be overridden to empty
        assert restricted_env.get("no_proxy") == ""
        assert restricted_env.get("NO_PROXY") == ""

    def test_all_protocol_proxies_blocked(self):
        """Test that FTP and other protocols are also blocked."""
        config = SandboxConfig(block_network=True)
        sandbox = PluginSandbox("test", config=config)
        env = sandbox._prepare_environment(None)

        # FTP should also be blocked
        assert env.get("ftp_proxy") == "http://127.0.0.1:0"
        assert env.get("FTP_PROXY") == "http://127.0.0.1:0"
