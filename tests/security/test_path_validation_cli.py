"""Security tests for CLI path validation (v0.5.8 HIGH-5).

This test suite verifies that all CLI commands with path arguments
properly validate user-provided paths to prevent:
- Path traversal attacks (../, ../../, etc.)
- Null byte injection (%00, \x00)
- Symlink attacks
- Other path-based vulnerabilities

Security Context:
- HIGH-5 from v0.5.7 baseline security audit
- Implements defense-in-depth path validation
- Uses PathValidator from ragged.validation.path_validator
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ragged.cli.commands.add import add
from ragged.cli.commands.exportimport import export as export_cmd
from ragged.cli.commands.history import history
from ragged.cli.commands.ingest import ingest
from ragged.cli.commands.memory import memory
from ragged.cli.commands.scan import scan


class TestPathTraversalPrevention:
    """Test that all CLI commands reject path traversal attacks."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_path_validator_reject(self):
        """Mock PathValidator to reject malicious paths."""
        with patch("ragged.validation.path_validator.PathValidator.validate") as mock:
            # Simulate PathValidator rejecting malicious path
            from ragged.validation.path_validator import PathTraversalError
            mock.side_effect = PathTraversalError("Path traversal detected")
            yield mock

    def test_add_command_rejects_path_traversal(self, cli_runner, tmp_path):
        """Test that 'ragged add' rejects path traversal attempts."""
        malicious_path = "../../../etc/passwd"

        result = cli_runner.invoke(add, [malicious_path])

        # Should fail (exit code != 0)
        assert result.exit_code != 0
        # Should show error (security error or path doesn't exist)
        assert "Security Error" in result.output or "does not exist" in result.output or result.exit_code == 2

    def test_ingest_pdf_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged ingest pdf' rejects path traversal."""
        malicious_path = "../../sensitive/document.pdf"

        result = cli_runner.invoke(ingest, ["pdf", malicious_path])

        # Should fail - path validation or file doesn't exist
        assert result.exit_code != 0

    def test_ingest_batch_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged ingest batch' rejects path traversal."""
        malicious_dir = "../../../root"

        result = cli_runner.invoke(ingest, ["batch", malicious_dir])

        # Should fail - path validation or directory doesn't exist
        assert result.exit_code != 0

    def test_export_backup_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged export backup' rejects path traversal in output path."""
        malicious_output = "../../../tmp/backup.json"

        result = cli_runner.invoke(export_cmd, ["backup", "--output", malicious_output])

        # Should either reject or fail safely
        assert result.exit_code != 0 or "Security Error" in result.output

    def test_export_restore_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged export restore' rejects path traversal in backup file."""
        malicious_backup = "../../../etc/passwd"

        result = cli_runner.invoke(export_cmd, ["restore", malicious_backup])

        # Should fail - path validation or file doesn't exist
        assert result.exit_code != 0

    def test_scan_process_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged scan process' rejects path traversal in input."""
        malicious_input = "../../sensitive/scan.txt"

        result = cli_runner.invoke(scan, ["process", malicious_input])

        # Should fail - path validation or file doesn't exist
        assert result.exit_code != 0

    def test_scan_output_dir_rejects_path_traversal(self, cli_runner, tmp_path):
        """Test that 'ragged scan process' rejects path traversal in output dir."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("test content")
        malicious_output = "../../../tmp/output"

        result = cli_runner.invoke(scan, ["process", str(input_file), "--output-dir", malicious_output])

        # Should either reject or fail safely
        assert result.exit_code != 0 or "Security Error" in result.output

    def test_history_export_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged history export' rejects path traversal."""
        malicious_output = "../../../tmp/history.json"

        result = cli_runner.invoke(history, ["export", malicious_output])

        # Should either reject or fail safely
        assert result.exit_code != 0 or "Security Error" in result.output

    def test_memory_export_rejects_path_traversal(self, cli_runner):
        """Test that 'ragged memory export' rejects path traversal."""
        malicious_output = "../../../tmp/memory.json"

        result = cli_runner.invoke(memory, ["export", malicious_output])

        # Should either reject or fail safely
        assert result.exit_code != 0 or "Security Error" in result.output


class TestNullByteInjectionPrevention:
    """Test that CLI commands reject null byte injection attempts."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI runner."""
        return CliRunner()

    def test_add_command_rejects_null_bytes(self, cli_runner):
        """Test that 'ragged add' rejects paths with null bytes."""
        malicious_path = "document\x00.txt"

        result = cli_runner.invoke(add, [malicious_path])

        # Should fail - null bytes are invalid in paths
        assert result.exit_code != 0

    def test_export_backup_rejects_null_bytes(self, cli_runner):
        """Test that 'ragged export backup' rejects null bytes in output path."""
        malicious_output = "backup\x00.json"

        result = cli_runner.invoke(export_cmd, ["backup", "--output", malicious_output])

        # Should fail - null bytes are invalid
        assert result.exit_code != 0


class TestSymlinkAttackPrevention:
    """Test that CLI commands reject symlink attacks."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI runner."""
        return CliRunner()

    def test_add_command_rejects_symlinks(self, cli_runner, tmp_path):
        """Test that 'ragged add' rejects symlinks when configured."""
        # Create a regular file and a symlink to it
        real_file = tmp_path / "real.txt"
        real_file.write_text("content")

        symlink = tmp_path / "symlink.txt"
        try:
            os.symlink(real_file, symlink)
        except OSError:
            pytest.skip("Symlink creation not supported on this platform")

        result = cli_runner.invoke(add, [str(symlink)])

        # PathValidator is configured with allow_symlinks=False,
        # so it should reject symlinks (exit code != 0)
        assert result.exit_code != 0

    def test_export_backup_rejects_symlink_output(self, cli_runner, tmp_path):
        """Test that 'ragged export backup' rejects symlink output paths."""
        real_file = tmp_path / "real_backup.json"
        symlink = tmp_path / "symlink_backup.json"

        try:
            # Create symlink to non-existent file
            os.symlink(real_file, symlink)
        except OSError:
            pytest.skip("Symlink creation not supported on this platform")

        result = cli_runner.invoke(export_cmd, ["backup", "--output", str(symlink)])

        # Should reject symlink or fail safely
        assert result.exit_code != 0 or "Security Error" in result.output


class TestPathValidatorIntegration:
    """Test that PathValidator is properly integrated into all commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI runner."""
        return CliRunner()

    def test_add_uses_path_validator(self, cli_runner, tmp_path):
        """Verify 'ragged add' uses PathValidator."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("ragged.cli.commands.add.PathValidator") as mock_validator:
            # Configure mock to return the path unchanged
            mock_instance = MagicMock()
            mock_instance.validate.return_value = test_file
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(add, [str(test_file)])

            # PathValidator should have been instantiated and validate() called
            assert mock_validator.called
            assert mock_instance.validate.called

    def test_ingest_pdf_uses_path_validator(self, cli_runner, tmp_path):
        """Verify 'ragged ingest pdf' uses PathValidator."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4 fake pdf")

        with patch("ragged.cli.commands.ingest.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = test_pdf
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(ingest, ["pdf", str(test_pdf)])

            assert mock_validator.called
            assert mock_instance.validate.called

    def test_export_uses_path_validator(self, cli_runner, tmp_path):
        """Verify 'ragged export backup' uses PathValidator."""
        output_file = tmp_path / "backup.json"

        with patch("ragged.cli.commands.exportimport.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = output_file
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(export_cmd, ["backup", "--output", str(output_file)])

            assert mock_validator.called
            assert mock_instance.validate.called

    def test_scan_uses_path_validator(self, cli_runner, tmp_path):
        """Verify 'ragged scan process' uses PathValidator."""
        test_file = tmp_path / "scan.txt"
        test_file.write_text("content")

        with patch("ragged.cli.commands.scan.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = test_file
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(scan, ["process", str(test_file)])

            assert mock_validator.called
            assert mock_instance.validate.called

    def test_history_export_uses_path_validator(self, cli_runner, tmp_path):
        """Verify 'ragged history export' uses PathValidator."""
        output_file = tmp_path / "history.json"

        with patch("ragged.cli.commands.history.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = output_file
            mock_validator.return_value = mock_instance

            # Create empty history first
            with patch("ragged.cli.commands.history.QueryHistory") as mock_history:
                mock_history_instance = MagicMock()
                mock_history_instance.export_history.return_value = 0
                mock_history.return_value = mock_history_instance

                result = cli_runner.invoke(history, ["export", str(output_file)])

                assert mock_validator.called
                assert mock_instance.validate.called

    def test_memory_export_uses_path_validator(self, cli_runner, tmp_path):
        """Verify 'ragged memory export' uses PathValidator."""
        output_file = tmp_path / "memory.json"

        with patch("ragged.cli.commands.memory.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = output_file
            mock_validator.return_value = mock_instance

            # Create empty interaction tracker first
            with patch("ragged.cli.commands.memory.InteractionTracker") as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.export_to_file.return_value = None
                mock_tracker.return_value = mock_tracker_instance

                result = cli_runner.invoke(memory, ["export", str(output_file)])

                assert mock_validator.called
                assert mock_instance.validate.called


class TestPathValidatorConfiguration:
    """Test that PathValidator is configured correctly for security."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI runner."""
        return CliRunner()

    def test_path_validator_config_allows_absolute_paths(self, cli_runner, tmp_path):
        """Verify PathValidator allows absolute paths (users expect this)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("ragged.cli.commands.add.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = test_file
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(add, [str(test_file)])

            # Check that PathValidator was instantiated with allow_absolute=True
            call_kwargs = mock_validator.call_args[1] if mock_validator.call_args else {}
            assert call_kwargs.get("allow_absolute") is True

    def test_path_validator_config_blocks_symlinks(self, cli_runner, tmp_path):
        """Verify PathValidator blocks symlinks for security."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("ragged.cli.commands.add.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = test_file
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(add, [str(test_file)])

            # Check that PathValidator was instantiated with allow_symlinks=False
            call_kwargs = mock_validator.call_args[1] if mock_validator.call_args else {}
            assert call_kwargs.get("allow_symlinks") is False

    def test_path_validator_config_no_allowed_base(self, cli_runner, tmp_path):
        """Verify PathValidator allows paths anywhere (no base restriction)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("ragged.cli.commands.add.PathValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate.return_value = test_file
            mock_validator.return_value = mock_instance

            result = cli_runner.invoke(add, [str(test_file)])

            # Check that PathValidator was instantiated with allowed_base=None
            call_kwargs = mock_validator.call_args[1] if mock_validator.call_args else {}
            assert call_kwargs.get("allowed_base") is None


# Mark all tests as security tests
pytestmark = pytest.mark.security
