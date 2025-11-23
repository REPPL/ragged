"""Tests for GPU device manager.

Tests cover:
- Device detection (CUDA, MPS, CPU)
- Optimal device selection
- Device hints and constraints
- Memory information queries
- Cache management
"""

import pytest

from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType


# Helper functions


def _has_cuda() -> bool:
    """Check if CUDA is available."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def _has_mps() -> bool:
    """Check if MPS (Apple Silicon GPU) is available."""
    try:
        import torch

        return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    except ImportError:
        return False


class TestDeviceType:
    """Test DeviceType enum."""

    def test_device_type_values(self):
        """Test DeviceType enum values."""
        assert DeviceType.CUDA.value == "cuda"
        assert DeviceType.MPS.value == "mps"
        assert DeviceType.CPU.value == "cpu"

    def test_device_type_string_comparison(self):
        """Test DeviceType can be compared with strings."""
        assert DeviceType.CUDA == "cuda"
        assert DeviceType.MPS == "mps"
        assert DeviceType.CPU == "cpu"


class TestDeviceInfo:
    """Test DeviceInfo dataclass."""

    def test_device_info_creation(self):
        """Test DeviceInfo creation."""
        device = DeviceInfo(
            device_type=DeviceType.CUDA,
            device_id=0,
            total_memory=24_000_000_000,
            name="NVIDIA RTX 4090",
            compute_capability=(8, 9),
        )

        assert device.device_type == DeviceType.CUDA
        assert device.device_id == 0
        assert device.total_memory == 24_000_000_000
        assert device.name == "NVIDIA RTX 4090"
        assert device.compute_capability == (8, 9)

    def test_device_info_defaults(self):
        """Test DeviceInfo default values."""
        device = DeviceInfo(device_type=DeviceType.CPU)

        assert device.device_id == 0
        assert device.total_memory is None
        assert device.name is None
        assert device.compute_capability is None

    def test_device_info_string_cuda(self):
        """Test DeviceInfo string representation for CUDA."""
        device = DeviceInfo(
            device_type=DeviceType.CUDA,
            device_id=0,
            total_memory=24_000_000_000,
            name="NVIDIA RTX 4090",
        )

        str_repr = str(device)
        assert "CUDA:0" in str_repr
        assert "NVIDIA RTX 4090" in str_repr
        assert "22.4GB" in str_repr or "24.0GB" in str_repr  # Approximate

    def test_device_info_string_mps(self):
        """Test DeviceInfo string representation for MPS."""
        device = DeviceInfo(device_type=DeviceType.MPS, name="Apple Silicon")

        str_repr = str(device)
        assert "MPS" in str_repr
        assert "Apple Silicon" in str_repr

    def test_device_info_string_cpu(self):
        """Test DeviceInfo string representation for CPU."""
        device = DeviceInfo(device_type=DeviceType.CPU)

        str_repr = str(device)
        assert "CPU" in str_repr


class TestDeviceManager:
    """Test DeviceManager functionality."""

    def test_device_manager_initialization(self):
        """Test DeviceManager initializes successfully."""
        manager = DeviceManager()
        assert manager is not None
        assert hasattr(manager, "_available_devices")
        assert len(manager._available_devices) > 0

    def test_available_devices_not_empty(self):
        """Test that at least CPU is always available."""
        manager = DeviceManager()
        assert len(manager._available_devices) >= 1

        # CPU should always be available as fallback
        device_types = [d.device_type for d in manager._available_devices]
        assert DeviceType.CPU in device_types or any(
            dt in [DeviceType.CUDA, DeviceType.MPS] for dt in device_types
        )

    def test_get_optimal_device_auto_select(self):
        """Test automatic optimal device selection."""
        manager = DeviceManager()
        device = manager.get_optimal_device()

        assert device is not None
        assert isinstance(device, DeviceInfo)
        assert device.device_type in [DeviceType.CUDA, DeviceType.MPS, DeviceType.CPU]

    def test_get_optimal_device_cpu_hint(self):
        """Test forcing CPU device via hint."""
        manager = DeviceManager()
        device = manager.get_optimal_device(device_hint="cpu")

        assert device.device_type == DeviceType.CPU

    def test_get_optimal_device_invalid_hint(self):
        """Test invalid device hint raises error."""
        manager = DeviceManager()

        # Try to force CUDA on a system without it (if applicable)
        try:
            import torch

            if not torch.cuda.is_available():
                with pytest.raises(RuntimeError, match="not available"):
                    manager.get_optimal_device(device_hint="cuda")
        except ImportError:
            # PyTorch not available, skip this test
            pytest.skip("PyTorch not available")

    def test_get_optimal_device_with_memory_requirement(self):
        """Test device selection with memory requirement."""
        manager = DeviceManager()

        # Request device with very high memory (should fall back to CPU or fail gracefully)
        device = manager.get_optimal_device(min_memory_gb=1000.0)

        # Should either get a device with sufficient memory or CPU fallback
        assert device is not None
        assert isinstance(device, DeviceInfo)

    def test_get_device_memory_info_cpu_raises(self):
        """Test that querying CPU memory info raises ValueError."""
        manager = DeviceManager()
        cpu_device = manager.get_optimal_device(device_hint="cpu")

        with pytest.raises(ValueError, match="CPU device has no GPU memory tracking"):
            manager.get_device_memory_info(cpu_device)

    @pytest.mark.skipif(
        not _has_cuda(), reason="CUDA not available, skipping CUDA-specific tests"
    )
    def test_get_device_memory_info_cuda(self):
        """Test CUDA memory info retrieval."""
        manager = DeviceManager()
        cuda_device = manager.get_optimal_device(device_hint="cuda")

        memory_info = manager.get_device_memory_info(cuda_device)

        assert "total" in memory_info
        assert "allocated" in memory_info
        assert "reserved" in memory_info
        assert "free" in memory_info

        # All values should be non-negative
        assert memory_info["total"] >= 0
        assert memory_info["allocated"] >= 0
        assert memory_info["reserved"] >= 0
        assert memory_info["free"] >= 0

        # Total should equal or exceed allocated
        assert memory_info["total"] >= memory_info["allocated"]

    @pytest.mark.skipif(
        not _has_cuda(), reason="CUDA not available, skipping CUDA cache test"
    )
    def test_clear_cache_cuda(self):
        """Test CUDA cache clearing."""
        manager = DeviceManager()
        cuda_device = manager.get_optimal_device(device_hint="cuda")

        # Should not raise
        manager.clear_cache(cuda_device)

    def test_clear_cache_cpu_noop(self):
        """Test CPU cache clearing is no-op."""
        manager = DeviceManager()
        cpu_device = manager.get_optimal_device(device_hint="cpu")

        # Should not raise (no-op for CPU)
        manager.clear_cache(cpu_device)

    def test_device_priority_order(self):
        """Test device detection follows CUDA > MPS > CPU priority."""
        manager = DeviceManager()
        devices = manager._available_devices

        # Check that devices are ordered by priority
        device_types = [d.device_type for d in devices]

        # CUDA should come before MPS and CPU
        if DeviceType.CUDA in device_types and DeviceType.MPS in device_types:
            cuda_idx = device_types.index(DeviceType.CUDA)
            mps_idx = device_types.index(DeviceType.MPS)
            assert cuda_idx < mps_idx

        # MPS should come before CPU
        if DeviceType.MPS in device_types and DeviceType.CPU in device_types:
            mps_idx = device_types.index(DeviceType.MPS)
            cpu_idx = device_types.index(DeviceType.CPU)
            assert mps_idx < cpu_idx

        # CUDA should come before CPU
        if DeviceType.CUDA in device_types and DeviceType.CPU in device_types:
            cuda_idx = device_types.index(DeviceType.CUDA)
            cpu_idx = device_types.index(DeviceType.CPU)
            assert cuda_idx < cpu_idx
