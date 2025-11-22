"""Tests for serve CLI command.

v0.3.12: Test API server CLI integration.
"""

import pytest
from click.testing import CliRunner

from src.cli.commands.serve import serve


class TestServeCommand:
    """Test serve CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_serve_command_exists(self, runner):
        """Test serve command can be invoked."""
        result = runner.invoke(serve, ["--help"])
        assert result.exit_code == 0
        assert "Start the ragged REST API server" in result.output

    def test_serve_has_host_option(self, runner):
        """Test serve has --host option."""
        result = runner.invoke(serve, ["--help"])
        assert "--host" in result.output
        assert "Host to bind to" in result.output

    def test_serve_has_port_option(self, runner):
        """Test serve has --port option."""
        result = runner.invoke(serve, ["--help"])
        assert "--port" in result.output
        assert "Port to bind to" in result.output

    def test_serve_has_reload_option(self, runner):
        """Test serve has --reload option."""
        result = runner.invoke(serve, ["--help"])
        assert "--reload" in result.output
        assert "auto-reload" in result.output

    def test_serve_has_workers_option(self, runner):
        """Test serve has --workers option."""
        result = runner.invoke(serve, ["--help"])
        assert "--workers" in result.output
        assert "worker processes" in result.output

    def test_serve_has_log_level_option(self, runner):
        """Test serve has --log-level option."""
        result = runner.invoke(serve, ["--help"])
        assert "--log-level" in result.output
        assert "Log level" in result.output

    def test_serve_examples_in_help(self, runner):
        """Test serve help shows examples."""
        result = runner.invoke(serve, ["--help"])
        assert "Examples:" in result.output or "Example:" in result.output
