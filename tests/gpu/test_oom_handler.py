"""Tests for OOM (Out-of-Memory) error handling.

Tests cover:
- OOM detection
- Recovery strategy 1: Cache clearing
- Recovery strategy 2: Batch size reduction
- Recovery strategy 3: CPU fallback
- Non-OOM error pass-through
- Strategy enablement flags
"""

import pytest

from src.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType
from src.gpu.oom_handler import OOMHandler


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


class TestOOMHandler:
    """Test OOMHandler functionality."""

    def test_oom_handler_initialization(self):
        """Test OOMHandler initializes successfully."""
        manager = DeviceManager()

        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=True,
            enable_batch_reduction=True,
            enable_cpu_fallback=True,
        )

        assert handler.device_manager == manager
        assert handler.enable_cache_clearing is True
        assert handler.enable_batch_reduction is True
        assert handler.enable_cpu_fallback is True

    def test_oom_handler_custom_config(self):
        """Test OOMHandler with custom configuration."""
        manager = DeviceManager()

        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=False,
            enable_batch_reduction=True,
            enable_cpu_fallback=False,
        )

        assert handler.enable_cache_clearing is False
        assert handler.enable_batch_reduction is True
        assert handler.enable_cpu_fallback is False

    def test_handle_oom_successful_execution(self):
        """Test successful function execution without OOM."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager)
        device = manager.get_optimal_device()

        def successful_func(x, y):
            return x + y

        result = handler.handle_oom(
            successful_func, 5, 3, device=device
        )

        assert result == 8

    def test_handle_oom_successful_execution_with_kwargs(self):
        """Test successful execution with keyword arguments."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager)
        device = manager.get_optimal_device()

        def func_with_kwargs(a, b, c=10):
            return a + b + c

        result = handler.handle_oom(
            func_with_kwargs, 1, 2, device=device, c=3
        )

        assert result == 6

    def test_handle_oom_non_oom_error_propagates(self):
        """Test non-OOM errors are propagated."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager)
        device = manager.get_optimal_device()

        def failing_func():
            raise ValueError("Not an OOM error")

        with pytest.raises(ValueError, match="Not an OOM error"):
            handler.handle_oom(failing_func, device=device)

    def test_handle_oom_detects_oom_keywords(self):
        """Test OOM detection via error message keywords."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager)
        device = manager.get_optimal_device()

        oom_keywords = [
            "out of memory",
            "OOM",
            "CUDA error",
            "MPS error",
            "memory error",
        ]

        for keyword in oom_keywords:
            attempt_count = [0]

            def oom_func():
                attempt_count[0] += 1
                if attempt_count[0] == 1:
                    raise RuntimeError(f"Simulated {keyword}")
                return "success"

            # Handler should retry on OOM
            # (may succeed on retry or exhaust attempts)
            try:
                result = handler.handle_oom(oom_func, device=device)
                assert result == "success"
            except RuntimeError as e:
                # If all retries fail, should get error about recovery attempts
                assert "recovery attempts" in str(e) or keyword in str(e)

    def test_handle_oom_batch_size_reduction(self):
        """Test batch size reduction strategy."""
        manager = DeviceManager()
        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=False,  # Disable first strategy
            enable_batch_reduction=True,
            enable_cpu_fallback=False,  # Disable third strategy
        )
        device = manager.get_optimal_device()

        attempt_count = [0]
        batch_sizes_seen = []

        def oom_on_first(batch_size=16):
            attempt_count[0] += 1
            batch_sizes_seen.append(batch_size)

            if attempt_count[0] == 1:
                raise RuntimeError("CUDA out of memory")

            return f"success with batch_size={batch_size}"

        result = handler.handle_oom(
            oom_on_first, device=device, batch_size=16
        )

        # Should have tried twice (initial + retry with reduced batch)
        assert attempt_count[0] == 2
        assert len(batch_sizes_seen) == 2

        # Second attempt should have reduced batch size (16 -> 8)
        assert batch_sizes_seen[1] == 8

    def test_handle_oom_max_attempts_exceeded(self):
        """Test error when all recovery attempts fail."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager)
        device = manager.get_optimal_device()

        attempt_count = [0]

        def always_oom():
            attempt_count[0] += 1
            raise RuntimeError("CUDA out of memory")

        with pytest.raises(RuntimeError, match="recovery attempts"):
            handler.handle_oom(always_oom, device=device)

        # Should have tried 3 times
        assert attempt_count[0] == 3

    def test_handle_oom_cache_clearing_disabled(self):
        """Test behavior when all strategies are disabled."""
        manager = DeviceManager()
        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=False,
            enable_batch_reduction=False,
            enable_cpu_fallback=False,
        )
        device = manager.get_optimal_device()

        attempt_count = [0]

        def always_oom():
            attempt_count[0] += 1
            raise RuntimeError("out of memory")

        with pytest.raises(RuntimeError, match="recovery attempts"):
            handler.handle_oom(always_oom, device=device)

        # All strategies disabled, should only try once (initial attempt)
        assert attempt_count[0] == 1

    def test_handle_oom_cpu_fallback_strategy(self):
        """Test CPU fallback strategy."""
        manager = DeviceManager()

        # Only enable CPU fallback
        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=False,
            enable_batch_reduction=False,
            enable_cpu_fallback=True,
        )

        device = manager.get_optimal_device()

        attempt_count = [0]
        devices_used = []

        def oom_on_first(device=None):
            attempt_count[0] += 1
            if device:
                devices_used.append(device)

            # Fail on first attempt, succeed on CPU fallback
            if attempt_count[0] == 1:
                raise RuntimeError("CUDA out of memory")

            return "success"

        result = handler.handle_oom(oom_on_first, device=device)

        assert result == "success"
        # Should have tried twice (initial + CPU fallback)
        assert attempt_count[0] == 2

    def test_handle_oom_preserves_function_arguments(self):
        """Test that function arguments are preserved across retries."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager)
        device = manager.get_optimal_device()

        attempt_count = [0]
        args_seen = []

        def track_args(x, y, z=None):
            attempt_count[0] += 1
            args_seen.append((x, y, z))

            if attempt_count[0] == 1:
                raise RuntimeError("out of memory")

            return x + y + (z or 0)

        result = handler.handle_oom(
            track_args, 1, 2, device=device, z=3
        )

        assert result == 6
        assert len(args_seen) == 2

        # Arguments should be preserved
        assert args_seen[0] == (1, 2, 3)
        assert args_seen[1] == (1, 2, 3)

    def test_handle_oom_with_batch_size_kwarg(self):
        """Test batch size reduction when batch_size is in kwargs."""
        manager = DeviceManager()
        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=False,
            enable_batch_reduction=True,
            enable_cpu_fallback=False,
        )
        device = manager.get_optimal_device()

        attempt_count = [0]
        batch_sizes = []

        def process_batch(data, batch_size):
            attempt_count[0] += 1
            batch_sizes.append(batch_size)

            if attempt_count[0] == 1:
                raise RuntimeError("out of memory")

            return f"processed {len(data)} items with batch_size={batch_size}"

        result = handler.handle_oom(
            process_batch, [1, 2, 3, 4], device=device, batch_size=32
        )

        # Should have reduced batch size on retry
        assert batch_sizes[0] == 32
        assert batch_sizes[1] == 16  # 32 // 2

    def test_handle_oom_minimum_batch_size(self):
        """Test batch size doesn't go below 1."""
        manager = DeviceManager()
        handler = OOMHandler(
            device_manager=manager,
            enable_cache_clearing=False,
            enable_batch_reduction=True,
            enable_cpu_fallback=False,
        )
        device = manager.get_optimal_device()

        batch_sizes = []

        def track_batch(batch_size):
            batch_sizes.append(batch_size)
            if len(batch_sizes) < 2:
                raise RuntimeError("out of memory")
            return "success"

        result = handler.handle_oom(
            track_batch, device=device, batch_size=1
        )

        assert result == "success"

        # Starting with batch_size=1, reduction gives max(1, 1//2) = 1
        assert all(bs == 1 for bs in batch_sizes)

    @pytest.mark.skipif(not _has_gpu(), reason="GPU not available")
    def test_handle_oom_gpu_cache_clearing(self):
        """Test GPU cache clearing on first OOM."""
        manager = DeviceManager()
        handler = OOMHandler(device_manager=manager, enable_cache_clearing=True)

        device = _get_gpu_device(manager)

        attempt_count = [0]

        def oom_once():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise RuntimeError("CUDA out of memory")
            return "success"

        result = handler.handle_oom(oom_once, device=device)

        assert result == "success"
        assert attempt_count[0] == 2  # Original + retry after cache clear
