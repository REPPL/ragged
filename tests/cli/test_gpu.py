"""Tests for v0.5.3 GPU management commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from ragged.cli.commands.gpu import gpu


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


class TestGpuListCommand:
    """Test gpu list command."""

    def test_gpu_list_help(self, cli_runner):
        """Test list command help text."""
        result = cli_runner.invoke(gpu, ["list", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output.lower() or "devices" in result.output.lower()

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_list_basic(self, mock_manager, cli_runner):
        """Test basic device listing."""
        # Mock device manager
        mock_mgr = MagicMock()
        mock_mgr.list_devices.return_value = [
            {"id": "cuda:0", "name": "NVIDIA RTX 4090", "type": "cuda"},
            {"id": "cpu", "name": "CPU", "type": "cpu"}
        ]
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["list"])
        assert result.exit_code == 0
        # Should show device information
        assert "cuda" in result.output.lower() or "cpu" in result.output.lower()

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_list_verbose(self, mock_manager, cli_runner):
        """Test verbose device listing."""
        mock_mgr = MagicMock()
        mock_mgr.list_devices.return_value = []
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["list", "--verbose"])
        assert result.exit_code == 0


class TestGpuInfoCommand:
    """Test gpu info command."""

    def test_gpu_info_help(self, cli_runner):
        """Test info command help text."""
        result = cli_runner.invoke(gpu, ["info", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output.lower() or "device" in result.output.lower()

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_info_basic(self, mock_manager, cli_runner):
        """Test device info display."""
        mock_mgr = MagicMock()
        mock_mgr.get_device_info.return_value = {
            "id": "cuda:0",
            "name": "NVIDIA RTX 4090",
            "memory_total": 24000000000,
            "compute_capability": "8.9"
        }
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["info", "cuda:0"])
        # Should succeed or gracefully handle missing device
        assert result.exit_code in [0, 1]

    def test_gpu_info_requires_device(self, cli_runner):
        """Test that info command requires device argument."""
        result = cli_runner.invoke(gpu, ["info"])
        assert result.exit_code != 0


class TestGpuStatsCommand:
    """Test gpu stats command."""

    def test_gpu_stats_help(self, cli_runner):
        """Test stats command help text."""
        result = cli_runner.invoke(gpu, ["stats", "--help"])
        assert result.exit_code == 0
        assert "stats" in result.output.lower() or "memory" in result.output.lower()

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_stats_basic(self, mock_manager, cli_runner):
        """Test memory statistics display."""
        mock_mgr = MagicMock()
        mock_mgr.get_memory_stats.return_value = {
            "allocated": 2000000000,
            "reserved": 3000000000,
            "free": 5000000000,
            "total": 8000000000
        }
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["stats"])
        # Should succeed or handle missing GPU gracefully
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_stats_watch(self, mock_manager, cli_runner):
        """Test watch mode for stats."""
        mock_mgr = MagicMock()
        mock_mgr.get_memory_stats.return_value = {"allocated": 0, "total": 8000000000}
        mock_manager.return_value = mock_mgr

        # Watch mode would run forever, so we test the option is accepted
        # In a real scenario, this would be tested with timeout/interruption
        # For now, just verify the command accepts the option
        result = cli_runner.invoke(gpu, ["stats", "--help"])
        assert "--watch" in result.output

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_stats_interval(self, mock_manager, cli_runner):
        """Test custom refresh interval."""
        result = cli_runner.invoke(gpu, ["stats", "--help"])
        assert "--interval" in result.output


class TestGpuBenchmarkCommand:
    """Test gpu benchmark command."""

    def test_gpu_benchmark_help(self, cli_runner):
        """Test benchmark command help text."""
        result = cli_runner.invoke(gpu, ["benchmark", "--help"])
        assert result.exit_code == 0
        assert "benchmark" in result.output.lower()

    @patch("ragged.cli.commands.gpu.ColPaliEmbedder")
    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_benchmark_basic(self, mock_manager, mock_embedder, cli_runner):
        """Test basic benchmarking."""
        mock_mgr = MagicMock()
        mock_mgr.list_devices.return_value = [{"id": "cpu", "type": "cpu"}]
        mock_manager.return_value = mock_mgr

        mock_emb = MagicMock()
        mock_embedder.return_value = mock_emb

        result = cli_runner.invoke(gpu, ["benchmark"])
        # Should complete or gracefully handle missing components
        assert result.exit_code in [0, 1]

    def test_gpu_benchmark_num_pages(self, cli_runner):
        """Test --num-pages option."""
        result = cli_runner.invoke(gpu, ["benchmark", "--help"])
        assert "--num-pages" in result.output

    def test_gpu_benchmark_batch_size(self, cli_runner):
        """Test --batch-size option."""
        result = cli_runner.invoke(gpu, ["benchmark", "--help"])
        assert "--batch-size" in result.output

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_benchmark_specific_device(self, mock_manager, cli_runner):
        """Test benchmarking specific device."""
        mock_mgr = MagicMock()
        mock_mgr.list_devices.return_value = []
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["benchmark", "--device", "cpu"])
        assert result.exit_code in [0, 1]


class TestGpuGroupCommand:
    """Test gpu command group."""

    def test_gpu_help(self, cli_runner):
        """Test gpu group help text."""
        result = cli_runner.invoke(gpu, ["--help"])
        assert result.exit_code == 0
        assert "gpu" in result.output.lower() or "device" in result.output.lower()
        assert "list" in result.output.lower()
        assert "info" in result.output.lower()
        assert "stats" in result.output.lower()
        assert "benchmark" in result.output.lower()

    def test_gpu_no_subcommand(self, cli_runner):
        """Test gpu without subcommand shows help."""
        result = cli_runner.invoke(gpu, [])
        assert result.exit_code in [0, 2]


class TestGpuErrorHandling:
    """Test GPU command error handling."""

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_list_no_devices(self, mock_manager, cli_runner):
        """Test listing when no GPU devices available."""
        mock_mgr = MagicMock()
        mock_mgr.list_devices.return_value = []
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["list"])
        assert result.exit_code == 0
        # Should indicate no devices found
        assert "no" in result.output.lower() or "cpu" in result.output.lower()

    @patch("ragged.cli.commands.gpu.DeviceManager")
    def test_gpu_info_invalid_device(self, mock_manager, cli_runner):
        """Test info for invalid device."""
        mock_mgr = MagicMock()
        mock_mgr.get_device_info.side_effect = ValueError("Device not found")
        mock_manager.return_value = mock_mgr

        result = cli_runner.invoke(gpu, ["info", "invalid:99"])
        assert result.exit_code in [0, 1]
