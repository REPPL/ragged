# VISION-004: GPU Resource Management

**Feature:** Intelligent GPU/CPU Fallback and Resource Monitoring
**Category:** Infrastructure
**Estimated Effort:** 18-24 hours
**Dependencies:** VISION-001 (ColPali Integration)
**Status:** Planned

---

## Overview

Implement robust GPU resource management for vision embedding generation, ensuring ragged gracefully handles diverse hardware environments (NVIDIA CUDA, Apple Silicon MPS, CPU-only). This feature provides intelligent device detection, automatic fallback, memory monitoring, and resource-aware batch sizing.

**Key Requirements:**
1. **Automatic Device Detection:** Detect CUDA > MPS > CPU in order of preference
2. **Graceful Fallback:** Seamlessly fall back to CPU if GPU unavailable or OOM
3. **Memory Monitoring:** Track GPU memory usage and prevent OOM crashes
4. **Adaptive Batch Sizing:** Adjust batch sizes based on available memory
5. **Model Lifecycle:** Efficient model loading/unloading for memory conservation

---

## Architecture

### Device Priority

```
User Specified Device?
├─ YES → Use specified device
│  ├─ Device available? → Use it
│  └─ Device unavailable → Error (explicit choice failed)
│
└─ NO → Auto-detect
   ├─ CUDA available? → Use CUDA
   ├─ MPS available? → Use MPS
   └─ Default → CPU
```

### Memory Management

```
Model Loading Request
    ↓
[Memory Check]
    ├─ Available memory >= required? → Load model
    └─ Insufficient memory
        ├─ Unload idle models → Retry
        └─ Still insufficient → Fallback to CPU
    ↓
[Batch Processing]
    ├─ Monitor memory during processing
    ├─ Detect OOM conditions
    └─ Reduce batch size if needed
    ↓
[Cleanup]
    └─ Unload model after idle timeout
```

---

## Implementation Plan

### Phase 1: Device Detection and Selection (4-6 hours)

#### Session 1.1: Device Manager (4-6h)

**Task:** Implement device detection and selection logic

**Implementation:**

```python
# src/gpu/device_manager.py

from enum import Enum
from typing import Optional, Dict
from dataclasses import dataclass
import platform
from loguru import logger


class DeviceType(str, Enum):
    """Supported device types."""
    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


@dataclass
class DeviceInfo:
    """
    Device information.

    Attributes:
        device_type: Type of device (CUDA, MPS, CPU)
        device_id: Device ID (for multi-GPU systems)
        total_memory: Total memory in bytes (None for CPU)
        name: Device name (e.g., "NVIDIA RTX 4090")
        compute_capability: CUDA compute capability (None for non-CUDA)
    """
    device_type: DeviceType
    device_id: int = 0
    total_memory: Optional[int] = None
    name: Optional[str] = None
    compute_capability: Optional[tuple] = None

    def __str__(self) -> str:
        """Human-readable device description."""
        if self.device_type == DeviceType.CPU:
            return f"CPU ({platform.processor()})"
        elif self.device_type == DeviceType.CUDA:
            mem_gb = self.total_memory / (1024**3) if self.total_memory else 0
            return f"CUDA:{self.device_id} ({self.name}, {mem_gb:.1f}GB)"
        elif self.device_type == DeviceType.MPS:
            return f"MPS (Apple Silicon)"
        else:
            return str(self.device_type)


class DeviceManager:
    """
    Manage device detection and selection for GPU/CPU computation.

    Handles:
    - Automatic device detection (CUDA > MPS > CPU)
    - Device availability checking
    - Multi-GPU selection
    - Device capability queries
    """

    def __init__(self):
        """Initialise device manager."""
        self._torch_available = self._check_torch_available()
        self._available_devices = self._detect_available_devices()

        logger.info(
            f"DeviceManager initialised. "
            f"Available devices: {[str(d) for d in self._available_devices]}"
        )

    def _check_torch_available(self) -> bool:
        """Check if PyTorch is available."""
        try:
            import torch
            return True
        except ImportError:
            logger.warning("PyTorch not available. CPU-only mode.")
            return False

    def _detect_available_devices(self) -> list[DeviceInfo]:
        """
        Detect all available compute devices.

        Returns:
            List of DeviceInfo objects (sorted by preference: CUDA > MPS > CPU)
        """
        devices = []

        if not self._torch_available:
            # CPU-only fallback
            devices.append(DeviceInfo(device_type=DeviceType.CPU))
            return devices

        import torch

        # Check for CUDA devices
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)

                devices.append(DeviceInfo(
                    device_type=DeviceType.CUDA,
                    device_id=i,
                    total_memory=props.total_memory,
                    name=props.name,
                    compute_capability=(props.major, props.minor)
                ))

                logger.info(
                    f"Detected CUDA device {i}: {props.name} "
                    f"({props.total_memory / (1024**3):.1f}GB)"
                )

        # Check for Apple Silicon MPS
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            devices.append(DeviceInfo(
                device_type=DeviceType.MPS,
                name="Apple Silicon"
            ))
            logger.info("Detected MPS device (Apple Silicon)")

        # CPU fallback
        if not devices:
            devices.append(DeviceInfo(device_type=DeviceType.CPU))
            logger.info("Using CPU device (no GPU available)")

        return devices

    def get_optimal_device(
        self,
        device_hint: Optional[str] = None,
        min_memory_gb: Optional[float] = None
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
                    if device.device_type == DeviceType.CUDA and \
                       device.device_id != device_id:
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
        logger.warning(
            f"No device meets requirements. Using fallback: {fallback}"
        )
        return fallback

    def get_device_memory_info(
        self,
        device: DeviceInfo
    ) -> Dict[str, int]:
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

            return {
                "total": total,
                "allocated": allocated,
                "reserved": reserved,
                "free": free
            }

        elif device.device_type == DeviceType.MPS:
            # MPS doesn't expose memory stats via PyTorch
            # Return placeholder (future: query via Metal API)
            return {
                "total": 0,
                "allocated": 0,
                "reserved": 0,
                "free": 0
            }

        else:
            raise ValueError(f"Unsupported device type: {device.device_type}")

    def clear_cache(self, device: DeviceInfo):
        """
        Clear cached memory for device.

        Args:
            device: Device to clear cache for
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
```

**Deliverables:**
- `src/gpu/device_manager.py` (~300 lines)
- Device detection and selection logic
- Memory querying for CUDA devices
- Cache management

**Time:** 4-6 hours

---

### Phase 2: Memory Monitoring and OOM Handling (6-8 hours)

#### Session 2.1: Memory Monitor (3-4h)

**Task:** Implement GPU memory monitoring and OOM detection

**Implementation:**

```python
# src/gpu/memory_monitor.py

from typing import Optional, Callable
from dataclasses import dataclass
import time
from loguru import logger

from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType


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
        utilisation_pct: Percentage of memory utilised
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
    """

    def __init__(
        self,
        device: DeviceInfo,
        device_manager: DeviceManager,
        warning_threshold_pct: float = 85.0,
        critical_threshold_pct: float = 95.0
    ):
        """
        Initialise memory monitor.

        Args:
            device: Device to monitor
            device_manager: Device manager for memory queries
            warning_threshold_pct: Percentage for warning threshold
            critical_threshold_pct: Percentage for critical threshold
        """
        if device.device_type == DeviceType.CPU:
            raise ValueError("Cannot monitor memory for CPU device")

        self.device = device
        self.device_manager = device_manager
        self.warning_threshold = warning_threshold_pct
        self.critical_threshold = critical_threshold_pct

        self.snapshots: list[MemorySnapshot] = []
        self.warning_callback: Optional[Callable] = None
        self.critical_callback: Optional[Callable] = None

        logger.info(
            f"Initialised MemoryMonitor for {device} "
            f"(warn={warning_threshold_pct}%, crit={critical_threshold_pct}%)"
        )

    def take_snapshot(self) -> MemorySnapshot:
        """
        Take memory snapshot.

        Returns:
            MemorySnapshot with current memory stats
        """
        memory_info = self.device_manager.get_device_memory_info(self.device)

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=memory_info["total"],
            allocated_bytes=memory_info["allocated"],
            reserved_bytes=memory_info["reserved"],
            free_bytes=memory_info["free"]
        )

        # Store snapshot
        self.snapshots.append(snapshot)

        # Limit history to last 100 snapshots
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]

        # Check thresholds
        self._check_thresholds(snapshot)

        return snapshot

    def _check_thresholds(self, snapshot: MemorySnapshot):
        """Check if memory usage exceeds thresholds."""
        utilisation = snapshot.utilisation_pct

        if utilisation >= self.critical_threshold:
            logger.error(
                f"CRITICAL: Memory utilisation at {utilisation:.1f}% "
                f"on {self.device}"
            )
            if self.critical_callback:
                self.critical_callback(snapshot)

        elif utilisation >= self.warning_threshold:
            logger.warning(
                f"WARNING: Memory utilisation at {utilisation:.1f}% "
                f"on {self.device}"
            )
            if self.warning_callback:
                self.warning_callback(snapshot)

    def get_recommended_batch_size(
        self,
        current_batch_size: int,
        target_utilisation_pct: float = 75.0
    ) -> int:
        """
        Calculate recommended batch size based on memory usage.

        Args:
            current_batch_size: Current batch size being used
            target_utilisation_pct: Target memory utilisation

        Returns:
            Recommended batch size (may be smaller or larger)
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

    def clear_history(self):
        """Clear snapshot history."""
        self.snapshots.clear()
        logger.debug("Cleared memory snapshot history")
```

**Deliverables:**
- `src/gpu/memory_monitor.py` (~200 lines)
- Memory snapshot tracking
- Threshold-based callbacks
- Batch size recommendations

**Time:** 3-4 hours

---

#### Session 2.2: OOM Recovery (3-4h)

**Task:** Implement out-of-memory error handling and recovery

**Implementation:**

```python
# src/gpu/oom_handler.py

from typing import Optional, Callable, TypeVar, Any
from functools import wraps
import torch
from loguru import logger

from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType


T = TypeVar('T')


class OOMHandler:
    """
    Handle out-of-memory errors with automatic recovery strategies.

    Recovery strategies:
    1. Clear GPU cache and retry
    2. Reduce batch size and retry
    3. Fallback to CPU
    """

    def __init__(
        self,
        device_manager: DeviceManager,
        enable_cache_clearing: bool = True,
        enable_batch_reduction: bool = True,
        enable_cpu_fallback: bool = True
    ):
        """
        Initialise OOM handler.

        Args:
            device_manager: Device manager for device operations
            enable_cache_clearing: Attempt cache clearing on OOM
            enable_batch_reduction: Attempt batch size reduction on OOM
            enable_cpu_fallback: Fallback to CPU on persistent OOM
        """
        self.device_manager = device_manager
        self.enable_cache_clearing = enable_cache_clearing
        self.enable_batch_reduction = enable_batch_reduction
        self.enable_cpu_fallback = enable_cpu_fallback

        logger.info(
            f"Initialised OOMHandler "
            f"(cache={enable_cache_clearing}, "
            f"batch={enable_batch_reduction}, "
            f"cpu_fallback={enable_cpu_fallback})"
        )

    def handle_oom(
        self,
        func: Callable[..., T],
        *args,
        device: DeviceInfo,
        batch_size: Optional[int] = None,
        **kwargs
    ) -> T:
        """
        Execute function with OOM handling.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            device: Device for computation
            batch_size: Current batch size (for reduction strategy)
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            RuntimeError: If all recovery strategies fail
        """
        attempt = 0
        max_attempts = 3
        current_device = device
        current_batch_size = batch_size

        while attempt < max_attempts:
            try:
                # Execute function
                return func(*args, **kwargs)

            except RuntimeError as e:
                if "out of memory" not in str(e).lower():
                    raise  # Not an OOM error, re-raise

                attempt += 1
                logger.warning(
                    f"OOM error on attempt {attempt}/{max_attempts}: {e}"
                )

                # Strategy 1: Clear cache and retry
                if attempt == 1 and self.enable_cache_clearing:
                    logger.info("Strategy 1: Clearing GPU cache and retrying")
                    self.device_manager.clear_cache(current_device)
                    continue

                # Strategy 2: Reduce batch size
                if attempt == 2 and self.enable_batch_reduction and current_batch_size:
                    new_batch_size = max(1, current_batch_size // 2)
                    logger.info(
                        f"Strategy 2: Reducing batch size "
                        f"{current_batch_size} → {new_batch_size}"
                    )

                    # Update kwargs with new batch size
                    if "batch_size" in kwargs:
                        kwargs["batch_size"] = new_batch_size

                    current_batch_size = new_batch_size
                    continue

                # Strategy 3: Fallback to CPU
                if attempt == 3 and self.enable_cpu_fallback:
                    logger.warning("Strategy 3: Falling back to CPU")
                    cpu_device = self.device_manager.get_optimal_device(
                        device_hint="cpu"
                    )

                    # Update kwargs with CPU device
                    if "device" in kwargs:
                        kwargs["device"] = cpu_device

                    current_device = cpu_device
                    continue

        # All strategies failed
        raise RuntimeError(
            f"OOM error persists after {max_attempts} recovery attempts"
        )


def with_oom_handling(
    device_param: str = "device",
    batch_size_param: str = "batch_size"
):
    """
    Decorator for automatic OOM handling.

    Args:
        device_param: Name of device parameter in function signature
        batch_size_param: Name of batch_size parameter

    Example:
        @with_oom_handling()
        def process_batch(data, device, batch_size):
            # Processing logic
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            device = kwargs.get(device_param)
            batch_size = kwargs.get(batch_size_param)

            if device is None or device.device_type == DeviceType.CPU:
                # No OOM handling needed for CPU
                return func(*args, **kwargs)

            # TODO: Get device_manager from global context or args
            # For now, execute without OOM handling
            # (Full implementation requires dependency injection)

            return func(*args, **kwargs)

        return wrapper
    return decorator
```

**Deliverables:**
- `src/gpu/oom_handler.py` (~200 lines)
- OOM detection and recovery
- Automatic fallback strategies
- Decorator for easy integration

**Time:** 3-4 hours

---

### Phase 3: Adaptive Batch Sizing (4-6 hours)

#### Session 3.1: Batch Size Calculator (2-3h)

**Task:** Implement adaptive batch size calculation

**Implementation:**

```python
# src/gpu/batch_sizer.py

from typing import Optional
from dataclasses import dataclass
from loguru import logger

from ragged.gpu.device_manager import DeviceInfo, DeviceType
from ragged.gpu.memory_monitor import MemoryMonitor


@dataclass
class BatchSizeConfig:
    """Configuration for batch sizing."""
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
    """

    def __init__(
        self,
        device: DeviceInfo,
        memory_monitor: Optional[MemoryMonitor] = None,
        config: Optional[BatchSizeConfig] = None
    ):
        """
        Initialise adaptive batch sizer.

        Args:
            device: Compute device
            memory_monitor: Memory monitor (for adaptive sizing)
            config: Batch sizing configuration
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
        bytes_per_element: int = 4  # float32
    ) -> int:
        """
        Calculate optimal batch size for given parameters.

        Args:
            embedding_dim: Embedding dimensionality
            sequence_length: Sequence length
            bytes_per_element: Bytes per tensor element (4 for float32)

        Returns:
            Recommended batch size
        """
        if self.device.device_type == DeviceType.CPU:
            # CPU: Use max batch size (no memory constraints typically)
            return self.config.max_batch_size

        if self.device.total_memory is None:
            # Unknown memory: Use conservative batch size
            logger.warning("Unknown GPU memory. Using conservative batch size.")
            return self.config.min_batch_size

        # Estimate memory per batch item
        # Formula: embedding_dim * sequence_length * bytes_per_element * overhead_factor
        overhead_factor = 3.0  # Account for activations, gradients, optimizer state

        bytes_per_item = (
            embedding_dim * sequence_length * bytes_per_element * overhead_factor
        )

        # Calculate available memory (with safety margin)
        available_memory = self.device.total_memory * (
            self.config.target_memory_utilisation - self.config.safety_margin
        )

        # Calculate batch size
        calculated_batch_size = int(available_memory // bytes_per_item)

        # Clamp to min/max
        batch_size = max(
            self.config.min_batch_size,
            min(calculated_batch_size, self.config.max_batch_size)
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
        """
        if self.memory_monitor is None:
            return current_batch_size

        recommended = self.memory_monitor.get_recommended_batch_size(
            current_batch_size,
            target_utilisation_pct=self.config.target_memory_utilisation * 100
        )

        # Clamp to min/max
        adjusted = max(
            self.config.min_batch_size,
            min(recommended, self.config.max_batch_size)
        )

        if adjusted != current_batch_size:
            logger.info(f"Adjusted batch size: {current_batch_size} → {adjusted}")

        return adjusted
```

**Deliverables:**
- `src/gpu/batch_sizer.py` (~150 lines)
- Memory-based batch size calculation
- Adaptive adjustment based on observed usage

**Time:** 2-3 hours

---

#### Session 3.2: Integration with ColPali Embedder (2-3h)

**Task:** Integrate adaptive batch sizing into ColPaliEmbedder

**Updates to VISION-001:**

```python
# src/embeddings/colpali_embedder.py (modifications)

from ragged.gpu.device_manager import DeviceManager, DeviceInfo
from ragged.gpu.memory_monitor import MemoryMonitor
from ragged.gpu.batch_sizer import AdaptiveBatchSizer, BatchSizeConfig
from ragged.gpu.oom_handler import OOMHandler


class ColPaliEmbedder(BaseEmbedder):
    """ColPali vision embedder with GPU management."""

    def __init__(
        self,
        model_name: str = "vidore/colpali",
        device: Optional[str] = None,
        batch_size: Optional[int] = None,  # None = adaptive
        cache_dir: Optional[Path] = None,
        enable_adaptive_batching: bool = True
    ):
        """
        Initialise ColPali embedder with GPU management.

        Args:
            model_name: HuggingFace model identifier
            device: Device hint (None = auto-detect)
            batch_size: Fixed batch size (None = adaptive)
            cache_dir: Model cache directory
            enable_adaptive_batching: Use adaptive batch sizing
        """
        # Initialise device manager
        self.device_manager = DeviceManager()

        # Select optimal device
        self.device_info = self.device_manager.get_optimal_device(
            device_hint=device,
            min_memory_gb=4.0  # ColPali requires ~4GB minimum
        )

        # Initialise memory monitor (GPU only)
        self.memory_monitor = None
        if self.device_info.device_type != DeviceType.CPU:
            self.memory_monitor = MemoryMonitor(
                device=self.device_info,
                device_manager=self.device_manager
            )

        # Initialise batch sizer
        self.batch_sizer = AdaptiveBatchSizer(
            device=self.device_info,
            memory_monitor=self.memory_monitor,
            config=BatchSizeConfig(min_batch_size=1, max_batch_size=16)
        )

        # Calculate initial batch size
        if batch_size is None and enable_adaptive_batching:
            self.batch_size = self.batch_sizer.calculate_batch_size(
                embedding_dim=768,
                sequence_length=1024
            )
        else:
            self.batch_size = batch_size or 4

        # Initialise OOM handler
        self.oom_handler = OOMHandler(device_manager=self.device_manager)

        # Load model
        self._load_model()

    def embed_batch(
        self,
        images: List[Image.Image],
        adaptive: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for batch of images with adaptive sizing.

        Args:
            images: List of PIL Images
            adaptive: Whether to use adaptive batch sizing

        Returns:
            Array of embeddings (num_images, 768)
        """
        if self.memory_monitor:
            # Take memory snapshot before processing
            snapshot = self.memory_monitor.take_snapshot()
            logger.debug(f"Pre-batch memory: {snapshot.utilisation_pct:.1f}%")

        # Adjust batch size if adaptive
        current_batch_size = self.batch_size
        if adaptive and self.memory_monitor:
            current_batch_size = self.batch_sizer.adjust_batch_size(
                current_batch_size
            )

        # Process with OOM handling
        try:
            result = self.oom_handler.handle_oom(
                self._process_batch_internal,
                images=images,
                device=self.device_info,
                batch_size=current_batch_size
            )

            if self.memory_monitor:
                # Take snapshot after processing
                snapshot = self.memory_monitor.take_snapshot()
                logger.debug(f"Post-batch memory: {snapshot.utilisation_pct:.1f}%")

            return result

        except RuntimeError as e:
            logger.error(f"Batch processing failed: {e}")
            raise
```

**Deliverables:**
- Updated ColPaliEmbedder with GPU management
- Adaptive batch sizing integration
- Memory monitoring hooks

**Time:** 2-3 hours

---

### Phase 4: Testing and Documentation (4-6 hours)

#### Session 4.1: Unit Tests (2-3h)

**Test Coverage:**
1. Device detection (CUDA, MPS, CPU)
2. Memory monitoring and threshold callbacks
3. OOM recovery strategies
4. Batch size calculation
5. Adaptive batch adjustment

**Example Tests:**

```python
# tests/gpu/test_device_manager.py

import pytest
from ragged.gpu.device_manager import DeviceManager, DeviceType


class TestDeviceManager:
    """Test device detection and management."""

    def test_device_detection(self):
        """Test automatic device detection."""
        manager = DeviceManager()
        assert len(manager._available_devices) > 0

        # Should have at least CPU
        device_types = [d.device_type for d in manager._available_devices]
        assert DeviceType.CPU in device_types

    def test_optimal_device_selection(self):
        """Test optimal device selection logic."""
        manager = DeviceManager()

        # Auto-select (should prefer GPU)
        device = manager.get_optimal_device()
        assert device is not None

        # Explicit CPU selection
        cpu_device = manager.get_optimal_device(device_hint="cpu")
        assert cpu_device.device_type == DeviceType.CPU

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
    def test_cuda_memory_query(self):
        """Test CUDA memory information retrieval."""
        manager = DeviceManager()
        cuda_device = manager.get_optimal_device(device_hint="cuda")

        memory_info = manager.get_device_memory_info(cuda_device)
        assert memory_info["total"] > 0
        assert memory_info["free"] <= memory_info["total"]
```

**Time:** 2-3 hours

---

#### Session 4.2: Integration Tests and Documentation (2-3h)

**Test Coverage:**
1. End-to-end GPU resource management
2. OOM recovery in real embedding generation
3. Adaptive batch sizing with actual models
4. Multi-GPU device selection (if available)

**Time:** 2-3 hours

---

## Success Criteria

**Functional Requirements:**
- [ ] Device detection: CUDA > MPS > CPU priority
- [ ] Automatic fallback to CPU if GPU unavailable
- [ ] Memory monitoring with warning/critical thresholds
- [ ] OOM recovery: cache clearing → batch reduction → CPU fallback
- [ ] Adaptive batch sizing based on available memory
- [ ] Model lifecycle management (load/unload)

**Quality Requirements:**
- [ ] 85%+ test coverage for GPU module
- [ ] Works on CUDA, MPS, and CPU-only systems
- [ ] Type hints and British English docstrings
- [ ] No crashes on OOM (graceful degradation)

**Performance Requirements:**
- [ ] Device detection: <100ms
- [ ] Memory snapshot: <10ms
- [ ] OOM recovery: <2s total retry time
- [ ] Adaptive batch sizing: <50ms calculation time

---

## Dependencies

**Required:**
- torch >= 2.0.0 (for GPU operations)
- loguru >= 0.7.0 (logging)

**From Other Features:**
- VISION-001: ColPaliEmbedder (to be enhanced with GPU management)

---

## Known Limitations

1. **MPS Memory Tracking:** Apple Silicon MPS doesn't expose detailed memory stats (future: Metal API integration)
2. **Multi-GPU Load Balancing:** Not implemented (single device per embedder instance)
3. **Memory Estimation Accuracy:** Overhead factor (3.0x) is heuristic-based
4. **OOM Recovery Guarantee:** Cannot guarantee recovery for all OOM scenarios

---

## Future Enhancements (Post-v0.5)

1. **Multi-GPU Parallelism:** Distribute batches across multiple GPUs
2. **Model Quantization:** INT8/FP16 for reduced memory footprint
3. **Metal API Integration:** Better memory tracking for MPS devices
4. **Learned Batch Sizing:** ML-based batch size prediction from model/input characteristics

---

**Status:** Planned
**Estimated Total Effort:** 18-24 hours
