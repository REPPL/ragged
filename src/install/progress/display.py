"""
Progress Display.

WIZARD-003: Rich-based progress display for installation.
"""

from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from ragged.install.progress.tracker import (
    ProgressTracker,
    PhaseInfo,
    PhaseStatus,
    InstallationPhase,
)


# Phase display names
PHASE_NAMES = {
    InstallationPhase.INITIALISING: "Initialising",
    InstallationPhase.DETECTING: "Detecting prerequisites",
    InstallationPhase.VALIDATING: "Validating environment",
    InstallationPhase.INSTALLING_DOCKER: "Installing Docker",
    InstallationPhase.INSTALLING_PYTHON: "Installing Python",
    InstallationPhase.INSTALLING_OLLAMA: "Installing Ollama",
    InstallationPhase.CREATING_DIRECTORIES: "Creating directories",
    InstallationPhase.GENERATING_CONFIG: "Generating configuration",
    InstallationPhase.SETTING_UP_DOCKER: "Setting up Docker services",
    InstallationPhase.PULLING_MODEL: "Pulling LLM model",
    InstallationPhase.VERIFYING: "Verifying installation",
    InstallationPhase.COMPLETE: "Complete",
    InstallationPhase.FAILED: "Failed",
}


class ProgressDisplay:
    """
    Rich-based progress display.

    Shows installation progress with phases, current status, and timing.
    """

    def __init__(
        self,
        tracker: ProgressTracker,
        console: Console | None = None,
    ) -> None:
        """
        Initialise progress display.

        Args:
            tracker: Progress tracker to display.
            console: Rich console for output.
        """
        self.tracker = tracker
        self.console = console or Console()
        self._live: Live | None = None
        self._progress: Progress | None = None
        self._task_id: Any = None

    def start(self) -> None:
        """Start live progress display."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )

        self._task_id = self._progress.add_task(
            "Installing ragged",
            total=100,
        )

        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=4,
        )
        self._live.start()

        # Add callback to tracker
        self.tracker.add_callback(self._on_progress_update)

    def stop(self) -> None:
        """Stop live progress display."""
        if self._live:
            self._live.stop()
            self._live = None

        # Remove callback
        self.tracker.remove_callback(self._on_progress_update)

    def _on_progress_update(
        self,
        tracker: ProgressTracker,
        info: PhaseInfo,
    ) -> None:
        """Handle progress update."""
        if self._progress and self._task_id is not None:
            overall = int(tracker.overall_progress * 100)
            self._progress.update(
                self._task_id,
                completed=overall,
                description=info.message or PHASE_NAMES.get(info.phase, info.phase.value),
            )

        if self._live:
            self._live.update(self._render())

    def _render(self) -> Panel:
        """Render progress display."""
        # Create phases table
        table = Table(
            show_header=False,
            box=None,
            padding=(0, 1),
        )
        table.add_column("Status", width=3)
        table.add_column("Phase")
        table.add_column("Duration", justify="right", width=10)

        for phase in self.tracker.phases:
            info = self.tracker.phase_info.get(phase)
            if not info:
                continue

            # Skip terminal states in phase list
            if phase in (InstallationPhase.COMPLETE, InstallationPhase.FAILED):
                continue

            # Status icon
            if info.status == PhaseStatus.COMPLETED:
                status = "[green]check[/green]"
            elif info.status == PhaseStatus.IN_PROGRESS:
                status = "[blue]...[/blue]"
            elif info.status == PhaseStatus.SKIPPED:
                status = "[dim]-[/dim]"
            elif info.status == PhaseStatus.FAILED:
                status = "[red]X[/red]"
            else:
                status = "[dim]o[/dim]"

            # Phase name with styling
            name = PHASE_NAMES.get(phase, phase.value)
            if info.status == PhaseStatus.IN_PROGRESS:
                name = f"[bold blue]{name}[/bold blue]"
            elif info.status == PhaseStatus.COMPLETED:
                name = f"[green]{name}[/green]"
            elif info.status == PhaseStatus.SKIPPED:
                name = f"[dim]{name}[/dim]"
            elif info.status == PhaseStatus.FAILED:
                name = f"[red]{name}[/red]"
            else:
                name = f"[dim]{name}[/dim]"

            # Duration
            if info.duration is not None:
                duration = f"{info.duration:.1f}s"
            else:
                duration = ""

            table.add_row(status, name, duration)

        # Current message
        current_info = None
        if self.tracker.current_phase:
            current_info = self.tracker.phase_info.get(self.tracker.current_phase)

        message = ""
        if current_info and current_info.message:
            message = f"\n[dim]{current_info.message}[/dim]"

        # Overall progress bar
        overall = int(self.tracker.overall_progress * 100)
        progress_bar = self._render_progress_bar(overall)

        # Compose display
        content = Group(
            table,
            Text(),  # Spacer
            progress_bar,
            Text(message) if message else Text(),
        )

        # Title with status
        if self.tracker.is_complete:
            title = "[green]Installation Complete[/green]"
            border_style = "green"
        elif self.tracker.is_failed:
            title = "[red]Installation Failed[/red]"
            border_style = "red"
        else:
            title = "Installing ragged"
            border_style = "blue"

        return Panel(
            content,
            title=title,
            border_style=border_style,
            padding=(1, 2),
        )

    def _render_progress_bar(self, percent: int) -> Text:
        """Render a text-based progress bar."""
        width = 40
        filled = int(width * percent / 100)
        empty = width - filled

        bar = "━" * filled + "─" * empty
        return Text(f"[{bar}] {percent}%", style="blue")

    def __enter__(self) -> "ProgressDisplay":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.stop()


def create_progress_display(
    tracker: ProgressTracker,
    console: Console | None = None,
) -> ProgressDisplay:
    """
    Create a progress display for a tracker.

    Args:
        tracker: Progress tracker.
        console: Rich console.

    Returns:
        ProgressDisplay instance.
    """
    return ProgressDisplay(tracker, console)
