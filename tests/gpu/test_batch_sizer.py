"""Tests for adaptive batch sizing.

Tests cover:
- BatchSizeConfig validation
- Batch size calculation based on GPU memory
- Adaptive batch size adjustment
- Min/max clamping
- CPU vs GPU behavior
- Cached batch size retrieval
"""

import pytest

from src.gpu.batch_sizer import AdaptiveBatchSizer, BatchSizeConfig
from src.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType
from src.gpu.memory_monitor import MemoryMonitor


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


class TestBatchSizeConfig:
    """Test BatchSizeConfig dataclass."""

    def test_batch_size_config_defaults(self):
        """Test default configuration values."""
        config = BatchSizeConfig()

        assert config.min_batch_size == 1
        assert config.max_batch_size == 32
        assert config.target_memory_utilisation == 0.75
        assert config.safety_margin == 0.10

    def test_batch_size_config_custom(self):
        """Test custom configuration."""
        config = BatchSizeConfig(
            min_batch_size=2,
            max_batch_size=16,
            target_memory_utilisation=0.70,
            safety_margin=0.15,
        )

        assert config.min_batch_size == 2
        assert config.max_batch_size == 16
        assert config.target_memory_utilisation == 0.70
        assert config.safety_margin == 0.15


class TestAdaptiveBatchSizer:
    """Test AdaptiveBatchSizer functionality."""

    def test_batch_sizer_cpu_uses_max(self):
        """Test CPU device uses max batch size."""
        manager = DeviceManager()
        cpu_device = manager.get_optimal_device(device_hint="cpu")

        sizer = AdaptiveBatchSizer(device=cpu_device)
        batch_size = sizer.calculate_batch_size()

        # CPU should use max batch size (no memory constraints)
        assert batch_size == 32

    def test_batch_sizer_cpu_custom_max(self):
        """Test CPU with custom max batch size."""
        manager = DeviceManager()
        cpu_device = manager.get_optimal_device(device_hint="cpu")

        config = BatchSizeConfig(max_batch_size=64)
        sizer = AdaptiveBatchSizer(device=cpu_device, config=config)
        batch_size = sizer.calculate_batch_size()

        assert batch_size == 64

    def test_batch_sizer_unknown_memory_uses_min(self):
        """Test device with unknown memory uses conservative batch size."""
        # Create device with no total_memory set
        device = DeviceInfo(device_type=DeviceType.CUDA, total_memory=None)

        sizer = AdaptiveBatchSizer(device=device)
        batch_size = sizer.calculate_batch_size()

        # Unknown memory should use min batch size
        assert batch_size == 1

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_batch_sizer_gpu_calculation(self):
        """Test GPU batch size calculation."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        sizer = AdaptiveBatchSizer(device=device)
        batch_size = sizer.calculate_batch_size(
            embedding_dim=768, sequence_length=1024, bytes_per_element=4
        )

        # Should return a value between min and max
        assert 1 <= batch_size <= 32

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_batch_sizer_respects_min_max(self):
        """Test batch size is clamped to min/max."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        # Create config with tight constraints
        config = BatchSizeConfig(min_batch_size=4, max_batch_size=8)
        sizer = AdaptiveBatchSizer(device=device, config=config)

        batch_size = sizer.calculate_batch_size()

        # Should be within specified range
        assert 4 <= batch_size <= 8

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_batch_sizer_larger_embeddings_smaller_batch(self):
        """Test larger embeddings result in smaller batch sizes."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        sizer = AdaptiveBatchSizer(device=device)

        # Small embeddings
        batch_small = sizer.calculate_batch_size(
            embedding_dim=128, sequence_length=256, bytes_per_element=4
        )

        # Large embeddings
        batch_large = sizer.calculate_batch_size(
            embedding_dim=2048, sequence_length=2048, bytes_per_element=4
        )

        # Larger embeddings should give smaller batch size
        # (or equal if already at minimum)
        assert batch_large <= batch_small

    def test_batch_sizer_caches_result(self):
        """Test batch size calculation is cached."""
        manager = DeviceManager()
        device = manager.get_optimal_device()

        sizer = AdaptiveBatchSizer(device=device)

        # Initially no cached value
        assert sizer.get_cached_batch_size() is None

        # Calculate batch size
        batch_size = sizer.calculate_batch_size()

        # Should be cached now
        cached = sizer.get_cached_batch_size()
        assert cached == batch_size

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_adjust_batch_size_no_monitor(self):
        """Test batch size adjustment without memory monitor."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        sizer = AdaptiveBatchSizer(device=device, memory_monitor=None)
        adjusted = sizer.adjust_batch_size(current_batch_size=8)

        # Without monitor, should return same batch size
        assert adjusted == 8

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_adjust_batch_size_with_monitor(self):
        """Test batch size adjustment with memory monitor."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        # Create memory monitor
        monitor = MemoryMonitor(device, manager)
        monitor.take_snapshot()  # Capture current memory state

        sizer = AdaptiveBatchSizer(device=device, memory_monitor=monitor)

        # Adjust batch size
        adjusted = sizer.adjust_batch_size(current_batch_size=8)

        # Should return a valid batch size
        assert isinstance(adjusted, int)
        assert adjusted >= 1

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_adjust_batch_size_respects_min_max(self):
        """Test adjustment respects min/max constraints."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        monitor = MemoryMonitor(device, manager)
        monitor.take_snapshot()

        config = BatchSizeConfig(min_batch_size=2, max_batch_size=16)
        sizer = AdaptiveBatchSizer(device=device, memory_monitor=monitor, config=config)

        # Try to adjust from very small batch
        adjusted = sizer.adjust_batch_size(current_batch_size=1)
        assert 2 <= adjusted <= 16

    def test_batch_sizer_with_memory_monitor_integration(self):
        """Test integration between batch sizer and memory monitor."""
        manager = DeviceManager()

        # Get any device (even CPU for this integration test)
        device = manager.get_optimal_device()

        if device.device_type == DeviceType.CPU:
            # CPU can't have memory monitor, just test basic integration
            sizer = AdaptiveBatchSizer(device=device, memory_monitor=None)
            batch_size = sizer.calculate_batch_size()
            assert batch_size > 0
        else:
            # GPU device
            monitor = MemoryMonitor(device, manager)
            sizer = AdaptiveBatchSizer(device=device, memory_monitor=monitor)

            # Calculate initial batch size
            batch_size = sizer.calculate_batch_size()
            assert batch_size > 0

            # Take memory snapshot
            monitor.take_snapshot()

            # Adjust batch size
            adjusted = sizer.adjust_batch_size(batch_size)
            assert adjusted > 0

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_batch_sizer_different_precisions(self):
        """Test batch size calculation with different data types."""
        manager = DeviceManager()
        device = _get_gpu_device(manager)

        sizer = AdaptiveBatchSizer(device=device)

        # float32 (4 bytes)
        batch_fp32 = sizer.calculate_batch_size(
            embedding_dim=768, sequence_length=1024, bytes_per_element=4
        )

        # float16 (2 bytes) should allow larger batch
        batch_fp16 = sizer.calculate_batch_size(
            embedding_dim=768, sequence_length=1024, bytes_per_element=2
        )

        # Smaller data type should allow larger batch (or equal if at max)
        assert batch_fp16 >= batch_fp32
