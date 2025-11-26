"""
Progress Callbacks.

WIZARD-003: Callback implementations for progress tracking.
"""

from abc import ABC, abstractmethod
import logging
from typing import TextIO
import sys

from rich.console import Console

from ragged.install.progress.tracker import (
    ProgressTracker,
    PhaseInfo,
    PhaseStatus,
    InstallationPhase,
)


logger = logging.getLogger(__name__)


class ProgressCallback(ABC):
    """Abstract base class for progress callbacks."""

    @abstractmethod
    def __call__(
        self,
        tracker: ProgressTracker,
        info: PhaseInfo,
    ) -> None:
        """
        Handle progress update.

        Args:
            tracker: Progress tracker.
            info: Updated phase info.
        """
        ...


class LoggingCallback(ProgressCallback):
    """
    Callback that logs progress updates.

    Uses Python logging to record installation progress.
    """

    def __init__(
        self,
        logger_name: str = "ragged.install",
        level: int = logging.INFO,
    ) -> None:
        """
        Initialise logging callback.

        Args:
            logger_name: Logger name to use.
            level: Logging level.
        """
        self._logger = logging.getLogger(logger_name)
        self._level = level

    def __call__(
        self,
        tracker: ProgressTracker,
        info: PhaseInfo,
    ) -> None:
        """Log progress update."""
        status_map = {
            PhaseStatus.PENDING: "PENDING",
            PhaseStatus.IN_PROGRESS: "STARTED",
            PhaseStatus.COMPLETED: "COMPLETED",
            PhaseStatus.SKIPPED: "SKIPPED",
            PhaseStatus.FAILED: "FAILED",
        }

        status_str = status_map.get(info.status, info.status.value)
        message = f"[{status_str}] {info.phase.value}"

        if info.message:
            message += f": {info.message}"

        if info.status == PhaseStatus.IN_PROGRESS and info.progress > 0:
            message += f" ({int(info.progress * 100)}%)"

        if info.error:
            message += f" - ERROR: {info.error}"

        self._logger.log(self._level, message)


class ConsoleCallback(ProgressCallback):
    """
    Callback that prints progress to console.

    Simple text output without rich formatting.
    """

    def __init__(
        self,
        output: TextIO | None = None,
        verbose: bool = False,
    ) -> None:
        """
        Initialise console callback.

        Args:
            output: Output stream (default: stdout).
            verbose: Whether to show verbose output.
        """
        self._output = output or sys.stdout
        self._verbose = verbose
        self._last_phase: InstallationPhase | None = None

    def __call__(
        self,
        tracker: ProgressTracker,
        info: PhaseInfo,
    ) -> None:
        """Print progress update."""
        # Only print on phase changes or if verbose
        if info.phase == self._last_phase and not self._verbose:
            return

        self._last_phase = info.phase

        # Status indicator
        if info.status == PhaseStatus.COMPLETED:
            indicator = "[OK]"
        elif info.status == PhaseStatus.IN_PROGRESS:
            indicator = "[..]"
        elif info.status == PhaseStatus.SKIPPED:
            indicator = "[--]"
        elif info.status == PhaseStatus.FAILED:
            indicator = "[!!]"
        else:
            indicator = "[  ]"

        # Phase name
        phase_name = info.phase.value.replace("_", " ").title()

        # Build message
        message = f"{indicator} {phase_name}"

        if info.message and self._verbose:
            message += f": {info.message}"

        if info.status == PhaseStatus.FAILED and info.error:
            message += f" - {info.error}"

        print(message, file=self._output)


class RichCallback(ProgressCallback):
    """
    Callback that uses Rich for pretty output.

    Provides formatted console output with colours and styling.
    """

    def __init__(
        self,
        console: Console | None = None,
        show_progress: bool = True,
    ) -> None:
        """
        Initialise Rich callback.

        Args:
            console: Rich console.
            show_progress: Whether to show progress percentages.
        """
        self._console = console or Console()
        self._show_progress = show_progress
        self._last_phase: InstallationPhase | None = None

    def __call__(
        self,
        tracker: ProgressTracker,
        info: PhaseInfo,
    ) -> None:
        """Print formatted progress update."""
        # Only print on phase transitions
        if info.phase == self._last_phase:
            return

        self._last_phase = info.phase

        # Status styling
        if info.status == PhaseStatus.COMPLETED:
            status = "[green]Done[/green]"
        elif info.status == PhaseStatus.IN_PROGRESS:
            status = "[blue]...[/blue]"
        elif info.status == PhaseStatus.SKIPPED:
            status = "[dim]Skipped[/dim]"
        elif info.status == PhaseStatus.FAILED:
            status = "[red]Failed[/red]"
        else:
            status = "[dim]Pending[/dim]"

        # Phase name
        phase_name = info.phase.value.replace("_", " ").title()

        # Build output
        if info.status == PhaseStatus.IN_PROGRESS:
            self._console.print(f"  {status} {phase_name}...", end="")
        elif info.status == PhaseStatus.COMPLETED:
            self._console.print(f"\r  {status} {phase_name}")
        else:
            self._console.print(f"  {status} {phase_name}")

        # Show error if failed
        if info.status == PhaseStatus.FAILED and info.error:
            self._console.print(f"       [red]{info.error}[/red]")


class FileCallback(ProgressCallback):
    """
    Callback that writes progress to a file.

    Useful for logging installation progress to a file.
    """

    def __init__(
        self,
        filepath: str,
        mode: str = "a",
        include_timestamp: bool = True,
    ) -> None:
        """
        Initialise file callback.

        Args:
            filepath: Path to output file.
            mode: File open mode.
            include_timestamp: Whether to include timestamps.
        """
        self._filepath = filepath
        self._mode = mode
        self._include_timestamp = include_timestamp

    def __call__(
        self,
        tracker: ProgressTracker,
        info: PhaseInfo,
    ) -> None:
        """Write progress update to file."""
        from datetime import datetime

        parts = []

        if self._include_timestamp:
            parts.append(datetime.now().isoformat())

        parts.append(info.status.value.upper())
        parts.append(info.phase.value)

        if info.message:
            parts.append(info.message)

        if info.progress > 0:
            parts.append(f"{int(info.progress * 100)}%")

        if info.error:
            parts.append(f"ERROR: {info.error}")

        line = " | ".join(parts) + "\n"

        try:
            with open(self._filepath, self._mode) as f:
                f.write(line)
        except OSError as e:
            logger.warning(f"Failed to write to progress file: {e}")
