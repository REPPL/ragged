"""Out-of-memory error handling and recovery strategies.

This module provides automatic OOM recovery through cache clearing,
batch size reduction, and CPU fallback strategies.

v0.5.2: OOM handling (VISION-004 Phase 2)
"""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OOMHandler:
    """
    Handle out-of-memory errors with automatic recovery strategies.

    Recovery strategies (applied in order):
    1. Clear GPU cache and retry
    2. Reduce batch size by 50% and retry
    3. Fallback to CPU

    Example:
        >>> manager = DeviceManager()
        >>> handler = OOMHandler(manager)
        >>> def process_batch(images, device, batch_size):
        ...     # Processing logic that might OOM
        ...     return embeddings
        >>> result = handler.handle_oom(
        ...     process_batch,
        ...     images=image_list,
        ...     device=gpu_device,
        ...     batch_size=16
        ... )
    """

    def __init__(
        self,
        device_manager: DeviceManager,
        enable_cache_clearing: bool = True,
        enable_batch_reduction: bool = True,
        enable_cpu_fallback: bool = True,
    ) -> None:
        """
        Initialise OOM handler.

        Args:
            device_manager: Device manager for device operations
            enable_cache_clearing: Attempt cache clearing on OOM (default: True)
            enable_batch_reduction: Attempt batch size reduction on OOM (default: True)
            enable_cpu_fallback: Fallback to CPU on persistent OOM (default: True)

        Example:
            >>> manager = DeviceManager()
            >>> # Handler with all recovery strategies enabled
            >>> handler = OOMHandler(manager)
            >>> # Handler with CPU fallback disabled
            >>> handler_no_cpu = OOMHandler(manager, enable_cpu_fallback=False)
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

    def _sanitize_oom_message(self, error: Exception) -> str:
        """
        Sanitize OOM error message to remove sensitive system information.

        Removes:
        - GPU model/ID
        - Exact memory sizes
        - System configuration details

        Security (v0.5.7 HIGH-3):
        - Prevents information disclosure via error messages
        - Returns generic message for production use
        - Full details only in debug logs

        Args:
            error: Original exception with potentially sensitive details

        Returns:
            Sanitized error message safe for user display
        """
        import re

        msg = str(error)

        # Remove GPU IDs (e.g., "GPU 0", "GPU 1")
        msg = re.sub(r"GPU\s+\d+", "GPU", msg)

        # Remove exact memory sizes (e.g., "23.70 GiB", "18.45 GiB")
        msg = re.sub(r"\d+\.\d+\s+[KMGT]iB", "X.XX GiB", msg)

        # Remove large integer memory values
        msg = re.sub(r"\d{4,}\s*(?:bytes?|KB|MB|GB)", "XXXX bytes", msg)

        # Truncate to prevent long technical stack traces
        if len(msg) > 200:
            msg = msg[:200] + "..."

        # Generic message if sanitization removed too much
        if len(msg.strip()) < 20:
            return "GPU out of memory error (details sanitized for security)"

        return msg

    def handle_oom(
        self,
        func: Callable[..., T],
        *args: Any,
        device: DeviceInfo,
        batch_size: int | None = None,
        **kwargs: Any,
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
            RuntimeError: If all recovery strategies fail or non-OOM error occurs

        Example:
            >>> handler = OOMHandler(device_manager)
            >>> result = handler.handle_oom(
            ...     embed_images,
            ...     device=cuda_device,
            ...     batch_size=32,
            ...     images=image_list
            ... )
        """
        # Build list of enabled recovery strategies
        strategies = []
        if self.enable_cache_clearing:
            strategies.append("cache_clear")
        if self.enable_batch_reduction and batch_size is not None:
            strategies.append("batch_reduce")
        if self.enable_cpu_fallback:
            strategies.append("cpu_fallback")

        attempt = 0
        max_attempts = len(strategies) + 1  # Initial attempt + recovery strategies
        current_device = device
        current_batch_size = batch_size
        strategy_index = 0

        # Add batch_size to kwargs if provided (for functions that expect it)
        if batch_size is not None and "batch_size" not in kwargs:
            kwargs["batch_size"] = batch_size

        while attempt < max_attempts:
            try:
                # Execute function
                return func(*args, **kwargs)

            except RuntimeError as e:
                # Check if this is an OOM error
                error_msg = str(e).lower()
                is_oom = any(
                    keyword in error_msg
                    for keyword in [
                        "out of memory",
                        "oom",
                        "cuda error",
                        "mps error",
                        "memory error",
                    ]
                )

                if not is_oom:
                    raise  # Not an OOM error, re-raise

                attempt += 1

                # SECURITY FIX (v0.5.7 HIGH-3): Sanitize OOM error messages
                # - User-facing warning uses sanitized message (no sensitive GPU details)
                # - Full error details only in debug logs for troubleshooting
                sanitized_msg = self._sanitize_oom_message(e)
                logger.warning(f"GPU memory error on attempt {attempt}/{max_attempts}")
                logger.debug(f"OOM details (debug only): {sanitized_msg}")

                # No more strategies to try
                if strategy_index >= len(strategies):
                    break

                # Apply next recovery strategy
                strategy = strategies[strategy_index]
                strategy_index += 1

                if strategy == "cache_clear":
                    logger.info("Recovery Strategy 1: Clearing GPU cache and retrying")
                    self.device_manager.clear_cache(current_device)
                    continue

                elif strategy == "batch_reduce":
                    new_batch_size = max(1, current_batch_size // 2)
                    logger.info(
                        f"Recovery Strategy 2: Reducing batch size "
                        f"{current_batch_size} → {new_batch_size}"
                    )

                    # Update kwargs with new batch size
                    if "batch_size" in kwargs:
                        kwargs["batch_size"] = new_batch_size

                    current_batch_size = new_batch_size
                    continue

                elif strategy == "cpu_fallback":
                    logger.warning("Recovery Strategy 3: Falling back to CPU")
                    cpu_device = self.device_manager.get_optimal_device(device_hint="cpu")

                    # Update kwargs with CPU device
                    if "device" in kwargs:
                        kwargs["device"] = cpu_device

                    current_device = cpu_device
                    continue

        # All strategies failed
        raise RuntimeError(f"OOM error persists after {attempt} recovery attempts")


def with_oom_handling(device_param: str = "device", batch_size_param: str = "batch_size"):
    """
    Decorator for automatic OOM handling.

    Note: This is a placeholder decorator. Full implementation requires
    dependency injection of DeviceManager instance.

    Args:
        device_param: Name of device parameter in function signature (default: "device")
        batch_size_param: Name of batch_size parameter (default: "batch_size")

    Example:
        >>> @with_oom_handling()
        ... def process_batch(data, device, batch_size):
        ...     # Processing logic
        ...     return results
        >>> # Function will automatically retry with OOM recovery if needed
        >>> results = process_batch(data, device=gpu, batch_size=16)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            device = kwargs.get(device_param)

            if device is None or device.device_type == DeviceType.CPU:
                # No OOM handling needed for CPU
                return func(*args, **kwargs)

            # TODO: Get device_manager from global context or args
            # For now, execute without OOM handling
            # (Full implementation requires dependency injection)
            logger.debug(f"@with_oom_handling decorator on {func.__name__}")

            return func(*args, **kwargs)

        return wrapper

    return decorator
