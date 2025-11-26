"""
Wizard Framework.

WIZARD-001: Core framework for the interactive installation wizard
including screen management, navigation, and state persistence.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import json
import logging

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


logger = logging.getLogger(__name__)


class NavigationAction(Enum):
    """Navigation actions within the wizard."""

    NEXT = "next"
    BACK = "back"
    SKIP = "skip"
    ABORT = "abort"
    RETRY = "retry"


@dataclass
class WizardState:
    """
    Persistent state for the installation wizard.

    Allows resuming interrupted installations.
    """

    current_screen: int = 0
    completed_screens: list[int] = field(default_factory=list)
    user_choices: dict[str, Any] = field(default_factory=dict)
    installation_results: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None
    last_updated: str | None = None

    def save(self, path: Path) -> None:
        """Save state to file."""
        from datetime import datetime

        self.last_updated = datetime.now().isoformat()
        if not self.started_at:
            self.started_at = self.last_updated

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(
                {
                    "current_screen": self.current_screen,
                    "completed_screens": self.completed_screens,
                    "user_choices": self.user_choices,
                    "installation_results": self.installation_results,
                    "started_at": self.started_at,
                    "last_updated": self.last_updated,
                },
                f,
                indent=2,
            )

    @classmethod
    def load(cls, path: Path) -> "WizardState":
        """Load state from file."""
        if not path.exists():
            return cls()

        try:
            with open(path) as f:
                data = json.load(f)
                return cls(
                    current_screen=data.get("current_screen", 0),
                    completed_screens=data.get("completed_screens", []),
                    user_choices=data.get("user_choices", {}),
                    installation_results=data.get("installation_results", {}),
                    started_at=data.get("started_at"),
                    last_updated=data.get("last_updated"),
                )
        except (json.JSONDecodeError, KeyError):
            return cls()

    def clear(self, path: Path) -> None:
        """Clear saved state."""
        if path.exists():
            path.unlink()


class WizardScreen(ABC):
    """
    Abstract base class for wizard screens.

    Each screen represents a step in the installation process.
    """

    def __init__(self, wizard: "Wizard") -> None:
        """
        Initialise wizard screen.

        Args:
            wizard: Parent wizard instance.
        """
        self.wizard = wizard
        self.console = wizard.console

    @property
    @abstractmethod
    def title(self) -> str:
        """Return the screen title."""
        ...

    @property
    def subtitle(self) -> str | None:
        """Return optional subtitle."""
        return None

    @property
    def can_skip(self) -> bool:
        """Whether this screen can be skipped."""
        return False

    @abstractmethod
    def render(self) -> None:
        """Render the screen content."""
        ...

    @abstractmethod
    def process(self) -> NavigationAction:
        """
        Process user input and return navigation action.

        Returns:
            NavigationAction indicating where to go next.
        """
        ...

    def on_enter(self) -> None:
        """Called when entering this screen."""
        pass

    def on_exit(self) -> None:
        """Called when leaving this screen."""
        pass

    def display_header(self) -> None:
        """Display screen header."""
        header_text = f"[bold blue]{self.title}[/bold blue]"
        if self.subtitle:
            header_text += f"\n[dim]{self.subtitle}[/dim]"

        self.console.print(
            Panel(
                header_text,
                border_style="blue",
                padding=(1, 2),
            )
        )
        self.console.print()

    def prompt_navigation(self) -> NavigationAction:
        """Prompt user for navigation choice."""
        options = "[B]ack [N]ext"
        if self.can_skip:
            options += " [S]kip"
        options += " [A]bort"

        self.console.print()
        choice = Prompt.ask(
            f"[dim]{options}[/dim]",
            default="n",
        ).lower()

        if choice in ("n", "next", ""):
            return NavigationAction.NEXT
        elif choice in ("b", "back"):
            return NavigationAction.BACK
        elif choice in ("s", "skip") and self.can_skip:
            return NavigationAction.SKIP
        elif choice in ("a", "abort"):
            if Confirm.ask("[red]Are you sure you want to abort?[/red]"):
                return NavigationAction.ABORT
            return self.prompt_navigation()
        else:
            self.console.print("[red]Invalid choice. Please try again.[/red]")
            return self.prompt_navigation()


class Wizard:
    """
    Installation wizard controller.

    Manages screens, navigation, and state persistence.
    """

    def __init__(
        self,
        state_path: Path | None = None,
        console: Console | None = None,
    ) -> None:
        """
        Initialise wizard.

        Args:
            state_path: Path for state persistence.
            console: Rich console for output.
        """
        self.console = console or Console()
        self._state_path = state_path or (Path.home() / ".ragged" / ".install_state")
        self._state = WizardState()
        self._screens: list[WizardScreen] = []
        self._current_index = 0
        self._aborted = False

    @property
    def state(self) -> WizardState:
        """Get current wizard state."""
        return self._state

    def add_screen(self, screen: WizardScreen) -> None:
        """Add a screen to the wizard."""
        self._screens.append(screen)

    def run(self, resume: bool = False) -> bool:
        """
        Run the wizard.

        Args:
            resume: Whether to resume from saved state.

        Returns:
            True if wizard completed successfully.
        """
        if resume:
            self._state = WizardState.load(self._state_path)
            self._current_index = self._state.current_screen
            if self._current_index > 0:
                self.console.print(
                    f"[green]Resuming from step {self._current_index + 1}[/green]\n"
                )
        else:
            self._state = WizardState()
            self._current_index = 0

        while 0 <= self._current_index < len(self._screens):
            screen = self._screens[self._current_index]

            # Clear and display progress
            self.console.clear()
            self._display_progress()

            # Run screen
            screen.on_enter()
            screen.display_header()
            screen.render()
            action = screen.process()
            screen.on_exit()

            # Handle navigation
            if action == NavigationAction.NEXT:
                self._state.completed_screens.append(self._current_index)
                self._current_index += 1
            elif action == NavigationAction.BACK:
                self._current_index = max(0, self._current_index - 1)
            elif action == NavigationAction.SKIP:
                self._current_index += 1
            elif action == NavigationAction.ABORT:
                self._aborted = True
                self._handle_abort()
                return False
            elif action == NavigationAction.RETRY:
                pass  # Stay on current screen

            # Save state
            self._state.current_screen = self._current_index
            self._state.save(self._state_path)

        # Wizard completed
        self._state.clear(self._state_path)
        return not self._aborted

    def _display_progress(self) -> None:
        """Display wizard progress indicator."""
        total = len(self._screens)
        current = self._current_index + 1

        progress_text = f"Step {current} of {total}"
        progress_bar = "━" * self._current_index + "●" + "─" * (total - current)

        self.console.print(
            f"[dim]{progress_text}[/dim]  [{progress_bar}]",
            justify="center",
        )
        self.console.print()

    def _handle_abort(self) -> None:
        """Handle wizard abort."""
        self.console.print()
        self.console.print(
            Panel(
                "[yellow]Installation aborted.[/yellow]\n\n"
                "Your progress has been saved. To resume:\n"
                "[bold]ragged install --resume[/bold]",
                title="Aborted",
                border_style="yellow",
            )
        )

    def set_choice(self, key: str, value: Any) -> None:
        """Set a user choice in state."""
        self._state.user_choices[key] = value

    def get_choice(self, key: str, default: Any = None) -> Any:
        """Get a user choice from state."""
        return self._state.user_choices.get(key, default)

    def set_result(self, key: str, value: Any) -> None:
        """Set an installation result in state."""
        self._state.installation_results[key] = value

    def get_result(self, key: str, default: Any = None) -> Any:
        """Get an installation result from state."""
        return self._state.installation_results.get(key, default)
