"""Device detection and management for GPU/CPU computation.

This module provides automatic device detection (CUDA > MPS > CPU),
device availability checking, and memory querying for optimal resource usage.

v0.5.2: Initial GPU device management (VISION-004 Phase 1)
"""

import logging
import platform
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Supported device types for computation."""

    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


@dataclass
class DeviceInfo:
    """
    Device information for computation.

    Attributes:
        device_type: Type of device (CUDA, MPS, CPU)
        device_id: Device ID (for multi-GPU systems)
        total_memory: Total memory in bytes (None for CPU)
        name: Device name (e.g., "NVIDIA RTX 4090")
        compute_capability: CUDA compute capability (None for non-CUDA)

    Example:
        >>> device = DeviceInfo(
        ...     device_type=DeviceType.CUDA,
        ...     device_id=0,
        ...     total_memory=24_000_000_000,
        ...     name="NVIDIA RTX 4090"
        ... )
        >>> str(device)
        'CUDA:0 (NVIDIA RTX 4090, 22.4GB)'
    """

    device_type: DeviceType
    device_id: int = 0
    total_memory: Optional[int] = None
    name: Optional[str] = None
    compute_capability: Optional[tuple[int, int]] = None

    def __str__(self) -> str:
        """Human-readable device description."""
        if self.device_type == DeviceType.CPU:
            proc = platform.processor() or "Unknown"
            return f"CPU ({proc})"
        elif self.device_type == DeviceType.CUDA:
            mem_gb = self.total_memory / (1024**3) if self.total_memory else 0
            return f"CUDA:{self.device_id} ({self.name}, {mem_gb:.1f}GB)"
        elif self.device_type == DeviceType.MPS:
            return "MPS (Apple Silicon)"
        else:
            return str(self.device_type)


class DeviceManager:
    """
    Manage device detection and selection for GPU/CPU computation.

    Handles:
    - Automatic device detection (CUDA > MPS > CPU priority)
    - Device availability checking
    - Multi-GPU selection
    - Device capability queries
    - Memory information retrieval

    Example:
        >>> manager = DeviceManager()
        >>> device = manager.get_optimal_device()
        >>> print(f"Selected: {device}")
        Selected: CUDA:0 (NVIDIA RTX 4090, 24.0GB)
        >>> memory = manager.get_device_memory_info(device)
        >>> print(f"Free: {memory['free'] / 1e9:.1f}GB")
        Free: 18.5GB
    """

    def __init__(self) -> None:
        """Initialise device manager and detect available devices."""
        self._torch_available = self._check_torch_available()
        self._available_devices = self._detect_available_devices()

        logger.info(
            f"DeviceManager initialised. "
            f"Available devices: {[str(d) for d in self._available_devices]}"
        )

    @property
    def available_devices(self) -> list[DeviceInfo]:
        """
        Get list of available compute devices.

        Returns:
            List of detected devices

        Example:
            >>> manager = DeviceManager()
            >>> devices = manager.available_devices
            >>> len(devices)
            2
        """
        return self._available_devices

    def _check_torch_available(self) -> bool:
        """
        Check if PyTorch is available.

        Returns:
            True if torch can be imported, False otherwise
        """
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            logger.warning("PyTorch not available. CPU-only mode.")
            return False

    def _detect_available_devices(self) -> list[DeviceInfo]:
        """
        Detect all available compute devices.

        Returns:
            List of DeviceInfo objects (sorted by preference: CUDA > MPS > CPU)

        Example:
            >>> manager = DeviceManager()
            >>> devices = manager._detect_available_devices()
            >>> [d.device_type for d in devices]
            [<DeviceType.CUDA: 'cuda'>, <DeviceType.CPU: 'cpu'>]
        """
        devices: list[DeviceInfo] = []

        if not self._torch_available:
            # CPU-only fallback
            devices.append(DeviceInfo(device_type=DeviceType.CPU))
            return devices

        import torch

        # Check for CUDA devices
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)

                devices.append(
                    DeviceInfo(
                        device_type=DeviceType.CUDA,
                        device_id=i,
                        total_memory=props.total_memory,
                        name=props.name,
                        compute_capability=(props.major, props.minor),
                    )
                )

                logger.info(
                    f"Detected CUDA device {i}: {props.name} "
                    f"({props.total_memory / (1024**3):.1f}GB)"
                )

        # Check for Apple Silicon MPS
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            devices.append(DeviceInfo(device_type=DeviceType.MPS, name="Apple Silicon"))
            logger.info("Detected MPS device (Apple Silicon)")

        # CPU is always available as fallback
        devices.append(DeviceInfo(device_type=DeviceType.CPU))
        if not any(d.device_type in [DeviceType.CUDA, DeviceType.MPS] for d in devices[:-1]):
            logger.info("Using CPU device (no GPU available)")
        else:
            logger.debug("CPU device available as fallback")

        return devices

    def get_optimal_device(
        self, device_hint: Optional[str] = None, min_memory_gb: Optional[float] = None
    ) -> DeviceInfo:
        """
        Get optimal device for computation.

        Args:
            device_hint: User-specified device ("cuda", "mps", "cpu", "cuda:1")
            min_memory_gb: Minimum required memory in GB (for GPU selection)

        Returns:
            DeviceInfo for selected device

        Raises:
            RuntimeError: If device_hint specified but unavailable

        Example:
            >>> manager = DeviceManager()
            >>> # Auto-select best device
            >>> device = manager.get_optimal_device()
            >>> # Force CPU
            >>> cpu_device = manager.get_optimal_device(device_hint="cpu")
            >>> # Require 8GB+ GPU
            >>> gpu_device = manager.get_optimal_device(min_memory_gb=8.0)
        """
        if device_hint:
            # Parse device hint
            device_type_str = device_hint.split(":")[0]
            device_id = 0

            if ":" in device_hint:
                device_id = int(device_hint.split(":")[1])

            # Find matching device
            for device in self._available_devices:
                if device.device_type.value == device_type_str:
                    if device.device_type == DeviceType.CUDA and device.device_id != device_id:
                        continue

                    # Check memory requirement
                    if min_memory_gb and device.total_memory:
                        required_bytes = min_memory_gb * (1024**3)
                        if device.total_memory < required_bytes:
                            logger.warning(
                                f"Device {device} has insufficient memory "
                                f"({device.total_memory / (1024**3):.1f}GB < "
                                f"{min_memory_gb}GB). Skipping."
                            )
                            continue

                    logger.info(f"Selected device: {device} (user-specified)")
                    return device

            # Device hint specified but not found
            raise RuntimeError(
                f"Device '{device_hint}' specified but not available. "
                f"Available devices: {[str(d) for d in self._available_devices]}"
            )

        # Auto-select optimal device
        for device in self._available_devices:
            # Check memory requirement if specified
            if min_memory_gb and device.total_memory:
                required_bytes = min_memory_gb * (1024**3)
                if device.total_memory < required_bytes:
                    continue

            logger.info(f"Auto-selected device: {device}")
            return device

        # Fallback to first available (should always be at least CPU)
        fallback = self._available_devices[0]
        logger.warning(f"No device meets requirements. Using fallback: {fallback}")
        return fallback

    def get_device_memory_info(self, device: DeviceInfo) -> dict[str, int]:
        """
        Get memory information for device.

        Args:
            device: Device to query

        Returns:
            Dictionary with memory stats:
            {
                "total": int,      # Total memory in bytes
                "allocated": int,  # Currently allocated
                "reserved": int,   # Reserved by PyTorch
                "free": int        # Available for allocation
            }

        Raises:
            ValueError: If device is CPU (no memory tracking)

        Example:
            >>> manager = DeviceManager()
            >>> device = manager.get_optimal_device(device_hint="cuda")
            >>> memory = manager.get_device_memory_info(device)
            >>> print(f"Free: {memory['free'] / 1e9:.1f}GB")
            Free: 18.5GB
        """
        if device.device_type == DeviceType.CPU:
            raise ValueError("CPU device has no GPU memory tracking")

        if not self._torch_available:
            return {"total": 0, "allocated": 0, "reserved": 0, "free": 0}

        import torch

        if device.device_type == DeviceType.CUDA:
            torch.cuda.set_device(device.device_id)

            total = torch.cuda.get_device_properties(device.device_id).total_memory
            reserved = torch.cuda.memory_reserved(device.device_id)
            allocated = torch.cuda.memory_allocated(device.device_id)
            free = total - reserved

            return {"total": total, "allocated": allocated, "reserved": reserved, "free": free}

        elif device.device_type == DeviceType.MPS:
            # MPS doesn't expose memory stats via PyTorch
            # Return placeholder (future: query via Metal API)
            logger.debug("MPS memory tracking not available via PyTorch")
            return {"total": 0, "allocated": 0, "reserved": 0, "free": 0}

        else:
            raise ValueError(f"Unsupported device type: {device.device_type}")

    def clear_cache(self, device: DeviceInfo) -> None:
        """
        Clear cached memory for device.

        Args:
            device: Device to clear cache for

        Example:
            >>> manager = DeviceManager()
            >>> device = manager.get_optimal_device()
            >>> manager.clear_cache(device)  # Free up cached memory
        """
        if device.device_type == DeviceType.CPU:
            return  # No cache to clear

        if not self._torch_available:
            return

        import torch

        if device.device_type == DeviceType.CUDA:
            torch.cuda.empty_cache()
            logger.info(f"Cleared CUDA cache for device {device.device_id}")

        elif device.device_type == DeviceType.MPS:
            # MPS cache clearing
            if hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()
                logger.info("Cleared MPS cache")
