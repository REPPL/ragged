"""
Debug logging for RAG pipeline visualization.

v0.3.8: Step-by-step execution visualisation for understanding RAG pipeline.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DebugStep:
    """A single debug step in the pipeline."""

    name: str
    details: dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    @property
    def duration_ms(self) -> float:
        """Get step duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def complete(self) -> None:
        """Mark step as complete."""
        self.end_time = time.time()


class DebugLogger:
    """
    Debug logger for RAG pipeline visualisation.

    Captures step-by-step execution details with timing information.
    """

    def __init__(self, enabled: bool = False):
        """
        Initialise debug logger.

        Args:
            enabled: Whether debug logging is enabled
        """
        self.enabled = enabled
        self.steps: list[DebugStep] = []
        self._current_step: DebugStep | None = None

    def start_step(self, name: str, **details: Any) -> None:
        """
        Start a new debug step.

        Args:
            name: Step name
            **details: Additional step details
        """
        if not self.enabled:
            return

        # Complete previous step if exists
        if self._current_step is not None:
            self._current_step.complete()

        # Start new step
        self._current_step = DebugStep(name=name, details=details)
        self.steps.append(self._current_step)

    def add_detail(self, key: str, value: Any) -> None:
        """
        Add detail to current step.

        Args:
            key: Detail key
            value: Detail value
        """
        if not self.enabled or self._current_step is None:
            return

        self._current_step.details[key] = value

    def complete_step(self) -> None:
        """Complete the current step."""
        if not self.enabled or self._current_step is None:
            return

        self._current_step.complete()
        self._current_step = None

    def log_step(self, name: str, **details: Any) -> None:
        """
        Log a complete step (start and immediately complete).

        Args:
            name: Step name
            **details: Step details
        """
        if not self.enabled:
            return

        self.start_step(name, **details)
        self.complete_step()

    @property
    def total_duration_ms(self) -> float:
        """Get total pipeline duration in milliseconds."""
        if not self.steps:
            return 0.0

        start = self.steps[0].start_time
        end = self.steps[-1].end_time if self.steps[-1].end_time else time.time()
        return (end - start) * 1000

    def render(self, verbose: bool = False) -> str:
        """
        Render debug output for display.

        Args:
            verbose: Include all details (default: summary only)

        Returns:
            Formatted debug output string
        """
        if not self.steps:
            return "No debug steps recorded."

        output = []
        output.append("\n🔍 Debug Mode: Query Pipeline\n")

        for i, step in enumerate(self.steps, 1):
            # Step header
            output.append(f"[Step {i}/{len(self.steps)}] {step.name}")

            # Step details
            if verbose or len(step.details) <= 5:
                for key, value in step.details.items():
                    # Format value based on type
                    if isinstance(value, float):
                        formatted_value = f"{value:.4f}"
                    elif isinstance(value, list):
                        formatted_value = f"{len(value)} items"
                    elif isinstance(value, dict):
                        formatted_value = f"{len(value)} entries"
                    else:
                        formatted_value = str(value)

                    output.append(f"  {key}: {formatted_value}")
            else:
                # Summary for large detail sets
                output.append(f"  Details: {len(step.details)} entries")

            # Duration
            output.append(f"  Duration: {step.duration_ms:.1f}ms")
            output.append("")  # Blank line

        # Total duration
        output.append(f"✓ Total Pipeline Duration: {self.total_duration_ms:.1f}ms\n")

        return "\n".join(output)

    def render_summary(self) -> str:
        """
        Render summary output (step names and durations only).

        Returns:
            Formatted summary string
        """
        if not self.steps:
            return "No debug steps recorded."

        output = []
        output.append("\n🔍 Pipeline Summary\n")

        for i, step in enumerate(self.steps, 1):
            output.append(f"  {i}. {step.name}: {step.duration_ms:.1f}ms")

        output.append(f"\n  Total: {self.total_duration_ms:.1f}ms\n")

        return "\n".join(output)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert debug log to dictionary for serialisation.

        Returns:
            Dictionary with all debug information
        """
        return {
            "enabled": self.enabled,
            "steps": [
                {
                    "name": step.name,
                    "details": step.details,
                    "duration_ms": step.duration_ms,
                }
                for step in self.steps
            ],
            "total_duration_ms": self.total_duration_ms,
        }

    def clear(self) -> None:
        """Clear all debug steps."""
        self.steps.clear()
        self._current_step = None


# Context manager for automatic step completion
class DebugStepContext:
    """Context manager for debug steps."""

    def __init__(self, debug_logger: DebugLogger, name: str, **details: Any):
        """
        Initialise debug step context manager.

        Args:
            debug_logger: DebugLogger instance
            name: Step name
            **details: Initial step details
        """
        self.logger = debug_logger
        self.name = name
        self.details = details

    def __enter__(self) -> "DebugStepContext":
        """Enter context, start step."""
        self.logger.start_step(self.name, **self.details)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context, complete step."""
        if exc_type is not None:
            # Log exception if occurred
            self.logger.add_detail("error", str(exc_val))
            self.logger.add_detail("error_type", exc_type.__name__)

        self.logger.complete_step()

    def add_detail(self, key: str, value: Any) -> None:
        """
        Add detail to current step.

        Args:
            key: Detail key
            value: Detail value
        """
        self.logger.add_detail(key, value)


# Convenience function
def create_debug_logger(enabled: bool = False) -> DebugLogger:
    """
    Create a debug logger instance.

    Args:
        enabled: Whether debug logging is enabled

    Returns:
        DebugLogger instance

    Example:
        >>> debug = create_debug_logger(enabled=True)
        >>> debug.start_step("Query Preprocessing", original="test query")
        >>> debug.add_detail("normalised", "test query")
        >>> debug.complete_step()
        >>> print(debug.render())
    """
    return DebugLogger(enabled=enabled)
