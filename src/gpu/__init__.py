"""GPU resource management for vision embeddings.

This module provides intelligent GPU/CPU device management, memory monitoring,
and adaptive batch sizing for ColPali vision embedding generation.

v0.5.2: GPU resource management (VISION-004)

Components:
- DeviceManager: Automatic device detection (CUDA > MPS > CPU priority)
- MemoryMonitor: GPU memory tracking with threshold callbacks
- OOMHandler: Automatic OOM recovery (cache → batch reduction → CPU fallback)
- AdaptiveBatchSizer: Memory-based batch size calculation

Example:
    >>> from ragged.gpu import DeviceManager, MemoryMonitor, AdaptiveBatchSizer
    >>> # Initialize device manager
    >>> manager = DeviceManager()
    >>> device = manager.get_optimal_device()
    >>> # Setup memory monitoring
    >>> monitor = MemoryMonitor(device, manager)
    >>> # Calculate optimal batch size
    >>> sizer = AdaptiveBatchSizer(device, monitor)
    >>> batch_size = sizer.calculate_batch_size(embedding_dim=768, sequence_length=1024)
"""

from ragged.gpu.batch_sizer import AdaptiveBatchSizer, BatchSizeConfig
from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType
from ragged.gpu.memory_monitor import MemoryMonitor, MemorySnapshot
from ragged.gpu.oom_handler import OOMHandler

__all__ = [
    "DeviceInfo",
    "DeviceManager",
    "DeviceType",
    "MemoryMonitor",
    "MemorySnapshot",
    "OOMHandler",
    "AdaptiveBatchSizer",
    "BatchSizeConfig",
]
