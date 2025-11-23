"""GPU memory monitoring and threshold management.

This module provides memory snapshot tracking, threshold-based callbacks,
and batch size recommendations based on observed GPU memory usage.

v0.5.2: GPU memory monitoring (VISION-004 Phase 2)
"""

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """
    GPU memory snapshot at a point in time.

    Attributes:
        timestamp: Unix timestamp of snapshot
        total_bytes: Total device memory
        allocated_bytes: Currently allocated memory
        reserved_bytes: Reserved by framework
        free_bytes: Available for allocation

    Example:
        >>> snapshot = MemorySnapshot(
        ...     timestamp=time.time(),
        ...     total_bytes=24_000_000_000,
        ...     allocated_bytes=8_000_000_000,
        ...     reserved_bytes=10_000_000_000,
        ...     free_bytes=14_000_000_000
        ... )
        >>> snapshot.utilisation_pct
        33.33
    """

    timestamp: float
    total_bytes: int
    allocated_bytes: int
    reserved_bytes: int
    free_bytes: int

    @property
    def utilisation_pct(self) -> float:
        """Calculate memory utilisation percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.allocated_bytes / self.total_bytes) * 100


class MemoryMonitor:
    """
    Monitor GPU memory usage and detect OOM conditions.

    Features:
    - Periodic memory snapshots
    - OOM prediction (approaching memory limit)
    - Callback hooks for memory events
    - Memory usage history tracking
    - Batch size recommendations

    Example:
        >>> manager = DeviceManager()
        >>> device = manager.get_optimal_device(device_hint="cuda")
        >>> monitor = MemoryMonitor(device, manager)
        >>> snapshot = monitor.take_snapshot()
        >>> print(f"Utilisation: {snapshot.utilisation_pct:.1f}%")
        Utilisation: 35.2%
        >>> recommended = monitor.get_recommended_batch_size(4)
        >>> print(f"Recommended batch size: {recommended}")
        Recommended batch size: 8
    """

    def __init__(
        self,
        device: DeviceInfo,
        device_manager: DeviceManager,
        warning_threshold_pct: float = 85.0,
        critical_threshold_pct: float = 95.0,
    ) -> None:
        """
        Initialise memory monitor.

        Args:
            device: Device to monitor
            device_manager: Device manager for memory queries
            warning_threshold_pct: Percentage for warning threshold (default: 85%)
            critical_threshold_pct: Percentage for critical threshold (default: 95%)

        Raises:
            ValueError: If device is CPU (cannot monitor CPU memory)

        Example:
            >>> manager = DeviceManager()
            >>> device = manager.get_optimal_device()
            >>> monitor = MemoryMonitor(device, manager, warning_threshold_pct=80.0)
        """
        if device.device_type == DeviceType.CPU:
            raise ValueError("Cannot monitor memory for CPU device")

        self.device = device
        self.device_manager = device_manager
        self.warning_threshold = warning_threshold_pct
        self.critical_threshold = critical_threshold_pct

        self.snapshots: list[MemorySnapshot] = []
        self.warning_callback: Optional[Callable[[MemorySnapshot], None]] = None
        self.critical_callback: Optional[Callable[[MemorySnapshot], None]] = None

        logger.info(
            f"Initialised MemoryMonitor for {device} "
            f"(warn={warning_threshold_pct}%, crit={critical_threshold_pct}%)"
        )

    def take_snapshot(self) -> MemorySnapshot:
        """
        Take memory snapshot.

        Returns:
            MemorySnapshot with current memory stats

        Example:
            >>> monitor = MemoryMonitor(device, manager)
            >>> snapshot = monitor.take_snapshot()
            >>> print(f"Free: {snapshot.free_bytes / 1e9:.1f}GB")
            Free: 18.5GB
        """
        memory_info = self.device_manager.get_device_memory_info(self.device)

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=memory_info["total"],
            allocated_bytes=memory_info["allocated"],
            reserved_bytes=memory_info["reserved"],
            free_bytes=memory_info["free"],
        )

        # Store snapshot
        self.snapshots.append(snapshot)

        # Limit history to last 100 snapshots
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]

        # Check thresholds
        self._check_thresholds(snapshot)

        return snapshot

    def _check_thresholds(self, snapshot: MemorySnapshot) -> None:
        """
        Check if memory usage exceeds thresholds.

        Args:
            snapshot: Memory snapshot to check
        """
        utilisation = snapshot.utilisation_pct

        if utilisation >= self.critical_threshold:
            logger.error(
                f"CRITICAL: Memory utilisation at {utilisation:.1f}% on {self.device}"
            )
            if self.critical_callback:
                self.critical_callback(snapshot)

        elif utilisation >= self.warning_threshold:
            logger.warning(
                f"WARNING: Memory utilisation at {utilisation:.1f}% on {self.device}"
            )
            if self.warning_callback:
                self.warning_callback(snapshot)

    def get_recommended_batch_size(
        self, current_batch_size: int, target_utilisation_pct: float = 75.0
    ) -> int:
        """
        Calculate recommended batch size based on memory usage.

        Args:
            current_batch_size: Current batch size being used
            target_utilisation_pct: Target memory utilisation (default: 75%)

        Returns:
            Recommended batch size (may be smaller or larger)

        Example:
            >>> monitor = MemoryMonitor(device, manager)
            >>> monitor.take_snapshot()  # Capture current usage
            >>> recommended = monitor.get_recommended_batch_size(4, target_utilisation_pct=70.0)
            >>> print(f"Adjust batch size: 4 → {recommended}")
            Adjust batch size: 4 → 6
        """
        if not self.snapshots:
            return current_batch_size

        latest = self.snapshots[-1]
        current_util = latest.utilisation_pct

        if current_util == 0:
            return current_batch_size

        # Scale batch size proportionally
        scale_factor = target_utilisation_pct / current_util
        recommended = int(current_batch_size * scale_factor)

        # Ensure minimum batch size of 1
        recommended = max(1, recommended)

        if recommended != current_batch_size:
            logger.info(
                f"Recommended batch size: {recommended} "
                f"(current: {current_batch_size}, util: {current_util:.1f}%)"
            )

        return recommended

    def clear_history(self) -> None:
        """
        Clear snapshot history.

        Example:
            >>> monitor = MemoryMonitor(device, manager)
            >>> monitor.take_snapshot()
            >>> len(monitor.snapshots)
            1
            >>> monitor.clear_history()
            >>> len(monitor.snapshots)
            0
        """
        self.snapshots.clear()
        logger.debug("Cleared memory snapshot history")

    def set_warning_callback(self, callback: Callable[[MemorySnapshot], None]) -> None:
        """
        Set callback for warning threshold.

        Args:
            callback: Function to call when warning threshold exceeded

        Example:
            >>> def on_warning(snapshot):
            ...     print(f"Warning: {snapshot.utilisation_pct:.1f}% utilisation")
            >>> monitor.set_warning_callback(on_warning)
        """
        self.warning_callback = callback

    def set_critical_callback(self, callback: Callable[[MemorySnapshot], None]) -> None:
        """
        Set callback for critical threshold.

        Args:
            callback: Function to call when critical threshold exceeded

        Example:
            >>> def on_critical(snapshot):
            ...     print(f"CRITICAL: {snapshot.utilisation_pct:.1f}% utilisation!")
            ...     # Take emergency action (reduce batch size, clear cache, etc.)
            >>> monitor.set_critical_callback(on_critical)
        """
        self.critical_callback = callback
