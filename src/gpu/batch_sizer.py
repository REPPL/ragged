"""Adaptive batch size calculation for GPU memory optimization.

This module calculates optimal batch sizes based on available GPU memory
and adjusts batch sizes dynamically based on observed memory usage.

v0.5.2: Adaptive batch sizing (VISION-004 Phase 3)
"""

import logging
from dataclasses import dataclass
from typing import Optional

from src.gpu.device_manager import DeviceInfo, DeviceType
from src.gpu.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


@dataclass
class BatchSizeConfig:
    """
    Configuration for batch sizing.

    Attributes:
        min_batch_size: Minimum allowed batch size (default: 1)
        max_batch_size: Maximum allowed batch size (default: 32)
        target_memory_utilisation: Target memory utilisation as fraction (default: 0.75)
        safety_margin: Safety buffer as fraction (default: 0.10)

    Example:
        >>> config = BatchSizeConfig(
        ...     min_batch_size=1,
        ...     max_batch_size=16,
        ...     target_memory_utilisation=0.70,
        ...     safety_margin=0.15
        ... )
    """

    min_batch_size: int = 1
    max_batch_size: int = 32
    target_memory_utilisation: float = 0.75  # 75%
    safety_margin: float = 0.10  # 10% safety buffer


class AdaptiveBatchSizer:
    """
    Calculate optimal batch sizes based on GPU memory.

    Strategies:
    - Memory-based: Size batches to fit in available memory
    - Adaptive: Adjust based on observed memory usage
    - Performance-aware: Balance memory vs throughput

    Example:
        >>> manager = DeviceManager()
        >>> device = manager.get_optimal_device()
        >>> sizer = AdaptiveBatchSizer(device)
        >>> batch_size = sizer.calculate_batch_size(
        ...     embedding_dim=768,
        ...     sequence_length=1024
        ... )
        >>> print(f"Optimal batch size: {batch_size}")
        Optimal batch size: 8
    """

    def __init__(
        self,
        device: DeviceInfo,
        memory_monitor: Optional[MemoryMonitor] = None,
        config: Optional[BatchSizeConfig] = None,
    ) -> None:
        """
        Initialise adaptive batch sizer.

        Args:
            device: Compute device
            memory_monitor: Memory monitor for adaptive sizing (optional)
            config: Batch sizing configuration (optional, uses defaults if None)

        Example:
            >>> device = DeviceInfo(DeviceType.CUDA, total_memory=24_000_000_000)
            >>> monitor = MemoryMonitor(device, device_manager)
            >>> sizer = AdaptiveBatchSizer(device, monitor)
        """
        self.device = device
        self.memory_monitor = memory_monitor
        self.config = config or BatchSizeConfig()

        self._cached_batch_size: Optional[int] = None

        logger.info(
            f"Initialised AdaptiveBatchSizer for {device} "
            f"(min={self.config.min_batch_size}, "
            f"max={self.config.max_batch_size})"
        )

    def calculate_batch_size(
        self,
        embedding_dim: int = 768,
        sequence_length: int = 1024,
        bytes_per_element: int = 4,  # float32
    ) -> int:
        """
        Calculate optimal batch size for given parameters.

        Args:
            embedding_dim: Embedding dimensionality (default: 768)
            sequence_length: Sequence length (default: 1024)
            bytes_per_element: Bytes per tensor element (default: 4 for float32)

        Returns:
            Recommended batch size

        Example:
            >>> sizer = AdaptiveBatchSizer(cuda_device)
            >>> # For ColPali: 768-dim embeddings, 1024 sequence length
            >>> batch_size = sizer.calculate_batch_size(768, 1024)
            >>> print(f"Batch size: {batch_size}")
            Batch size: 8
        """
        if self.device.device_type == DeviceType.CPU:
            # CPU: Use max batch size (no memory constraints typically)
            logger.debug("CPU device: using max batch size")
            self._cached_batch_size = self.config.max_batch_size
            return self.config.max_batch_size

        if self.device.total_memory is None:
            # Unknown memory: Use conservative batch size
            logger.warning("Unknown GPU memory. Using conservative batch size.")
            self._cached_batch_size = self.config.min_batch_size
            return self.config.min_batch_size

        # Estimate memory per batch item
        # Formula: embedding_dim * sequence_length * bytes_per_element * overhead_factor
        # Overhead accounts for activations, gradients, optimizer state
        overhead_factor = 3.0

        bytes_per_item = embedding_dim * sequence_length * bytes_per_element * overhead_factor

        # Calculate available memory (with safety margin)
        available_memory = self.device.total_memory * (
            self.config.target_memory_utilisation - self.config.safety_margin
        )

        # Calculate batch size
        calculated_batch_size = int(available_memory // bytes_per_item)

        # Clamp to min/max
        batch_size = max(
            self.config.min_batch_size, min(calculated_batch_size, self.config.max_batch_size)
        )

        logger.info(
            f"Calculated batch size: {batch_size} "
            f"(available_memory={available_memory / (1024**3):.2f}GB, "
            f"bytes_per_item={bytes_per_item / (1024**2):.2f}MB)"
        )

        self._cached_batch_size = batch_size
        return batch_size

    def adjust_batch_size(self, current_batch_size: int) -> int:
        """
        Adjust batch size based on memory monitor feedback.

        Args:
            current_batch_size: Current batch size

        Returns:
            Adjusted batch size

        Example:
            >>> sizer = AdaptiveBatchSizer(device, memory_monitor)
            >>> # After processing a batch, adjust based on observed usage
            >>> new_batch_size = sizer.adjust_batch_size(current_batch_size=8)
            >>> print(f"Adjusted: 8 → {new_batch_size}")
            Adjusted: 8 → 12
        """
        if self.memory_monitor is None:
            return current_batch_size

        recommended = self.memory_monitor.get_recommended_batch_size(
            current_batch_size, target_utilisation_pct=self.config.target_memory_utilisation * 100
        )

        # Clamp to min/max
        adjusted = max(
            self.config.min_batch_size, min(recommended, self.config.max_batch_size)
        )

        if adjusted != current_batch_size:
            logger.info(f"Adjusted batch size: {current_batch_size} → {adjusted}")

        return adjusted

    def get_cached_batch_size(self) -> Optional[int]:
        """
        Get last calculated batch size.

        Returns:
            Cached batch size or None if calculate_batch_size() not called yet

        Example:
            >>> sizer = AdaptiveBatchSizer(device)
            >>> sizer.calculate_batch_size()
            8
            >>> sizer.get_cached_batch_size()
            8
        """
        return self._cached_batch_size
