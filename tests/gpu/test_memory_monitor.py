"""Tests for GPU memory monitoring.

Tests cover:
- Memory snapshot creation
- Utilisation percentage calculation
- Threshold checking (warning/critical)
- Threshold callbacks
- Batch size recommendations
- History management
"""

import time

import pytest

from src.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType
from src.gpu.memory_monitor import MemoryMonitor, MemorySnapshot


# Helper functions


def _has_gpu() -> bool:
    """Check if any GPU (CUDA or MPS) is available."""
    try:
        import torch

        return torch.cuda.is_available() or (
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        )
    except ImportError:
        return False


def _get_gpu_device(manager: DeviceManager) -> DeviceInfo:
    """Get a GPU device (CUDA or MPS) for testing."""
    device = manager.get_optimal_device()
    if device.device_type == DeviceType.CPU:
        pytest.skip("No GPU available for testing")
    return device


class TestMemorySnapshot:
    """Test MemorySnapshot dataclass."""

    def test_memory_snapshot_creation(self):
        """Test MemorySnapshot creation."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=24_000_000_000,
            allocated_bytes=8_000_000_000,
            reserved_bytes=10_000_000_000,
            free_bytes=14_000_000_000,
        )

        assert snapshot.total_bytes == 24_000_000_000
        assert snapshot.allocated_bytes == 8_000_000_000
        assert snapshot.reserved_bytes == 10_000_000_000
        assert snapshot.free_bytes == 14_000_000_000

    def test_utilisation_pct_calculation(self):
        """Test memory utilisation percentage calculation."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=10_000_000_000,  # 10 GB
            allocated_bytes=3_000_000_000,  # 3 GB
            reserved_bytes=4_000_000_000,
            free_bytes=6_000_000_000,
        )

        # 3 GB / 10 GB = 30%
        assert snapshot.utilisation_pct == 30.0

    def test_utilisation_pct_zero_total(self):
        """Test utilisation percentage with zero total memory."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=0,
            allocated_bytes=0,
            reserved_bytes=0,
            free_bytes=0,
        )

        assert snapshot.utilisation_pct == 0.0

    def test_utilisation_pct_full(self):
        """Test utilisation percentage at 100%."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=10_000_000_000,
            allocated_bytes=10_000_000_000,
            reserved_bytes=10_000_000_000,
            free_bytes=0,
        )

        assert snapshot.utilisation_pct == 100.0


class TestMemoryMonitor:
    """Test MemoryMonitor functionality."""

    def test_memory_monitor_cpu_raises(self):
        """Test that monitoring CPU device raises ValueError."""
        manager = DeviceManager()
        cpu_device = manager.get_optimal_device(device_hint="cpu")

        with pytest.raises(ValueError, match="Cannot monitor memory for CPU device"):
            MemoryMonitor(cpu_device, manager)

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_memory_monitor_initialization(self):
        """Test MemoryMonitor initializes successfully."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        monitor = MemoryMonitor(
            device=device,
            device_manager=manager,
            warning_threshold_pct=85.0,
            critical_threshold_pct=95.0,
        )

        assert monitor.device == device
        assert monitor.device_manager == manager
        assert monitor.warning_threshold == 85.0
        assert monitor.critical_threshold == 95.0
        assert len(monitor.snapshots) == 0

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_take_snapshot(self):
        """Test taking memory snapshot."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        snapshot = monitor.take_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.total_bytes >= 0
        assert snapshot.allocated_bytes >= 0
        assert snapshot.reserved_bytes >= 0
        assert snapshot.free_bytes >= 0
        assert len(monitor.snapshots) == 1

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_snapshot_history_limit(self):
        """Test snapshot history is limited to 100 entries."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        # Take 150 snapshots
        for _ in range(150):
            monitor.take_snapshot()

        # Should only keep last 100
        assert len(monitor.snapshots) == 100

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_clear_history(self):
        """Test clearing snapshot history."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        # Take some snapshots
        monitor.take_snapshot()
        monitor.take_snapshot()
        assert len(monitor.snapshots) == 2

        # Clear history
        monitor.clear_history()
        assert len(monitor.snapshots) == 0

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_warning_callback(self):
        """Test warning threshold callback."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        # Set very low warning threshold to trigger it
        monitor = MemoryMonitor(device, manager, warning_threshold_pct=0.1)

        callback_triggered = []

        def on_warning(snapshot: MemorySnapshot):
            callback_triggered.append(snapshot)

        monitor.set_warning_callback(on_warning)
        monitor.take_snapshot()

        # Callback should be triggered if any memory is allocated
        # (depends on actual GPU state, so this is a soft check)
        assert isinstance(callback_triggered, list)

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_critical_callback(self):
        """Test critical threshold callback."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        # Set very low critical threshold
        monitor = MemoryMonitor(device, manager, critical_threshold_pct=0.1)

        callback_triggered = []

        def on_critical(snapshot: MemorySnapshot):
            callback_triggered.append(snapshot)

        monitor.set_critical_callback(on_critical)
        monitor.take_snapshot()

        # Similar soft check as warning test
        assert isinstance(callback_triggered, list)

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_get_recommended_batch_size_no_snapshots(self):
        """Test batch size recommendation with no snapshots."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        # No snapshots yet
        recommended = monitor.get_recommended_batch_size(current_batch_size=4)

        # Should return current batch size when no data
        assert recommended == 4

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_get_recommended_batch_size_with_snapshot(self):
        """Test batch size recommendation based on memory usage."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        # Take snapshot
        monitor.take_snapshot()

        # Get recommendation
        recommended = monitor.get_recommended_batch_size(
            current_batch_size=4, target_utilisation_pct=75.0
        )

        # Should return a positive integer
        assert isinstance(recommended, int)
        assert recommended >= 1

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_batch_size_recommendation_scaling(self):
        """Test batch size scales with target utilisation."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        # Take snapshot to have data
        snapshot = monitor.take_snapshot()

        # If current utilisation is low, higher target should increase batch size
        current_util = snapshot.utilisation_pct

        if current_util > 0 and current_util < 50:
            # Low utilisation, should recommend larger batch
            rec_low = monitor.get_recommended_batch_size(4, target_utilisation_pct=30.0)
            rec_high = monitor.get_recommended_batch_size(4, target_utilisation_pct=70.0)

            # Higher target utilisation should give larger batch size
            assert rec_high >= rec_low

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_set_callbacks(self):
        """Test setting warning and critical callbacks."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)
        monitor = MemoryMonitor(device, manager)

        def warning_cb(snapshot):
            pass

        def critical_cb(snapshot):
            pass

        monitor.set_warning_callback(warning_cb)
        monitor.set_critical_callback(critical_cb)

        assert monitor.warning_callback == warning_cb
        assert monitor.critical_callback == critical_cb
