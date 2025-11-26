"""
Welcome Screen.

WIZARD-001: Welcome screen introducing ragged and the installation process.
"""

from rich.markdown import Markdown
from rich.panel import Panel

from ragged.cli.wizard.framework import NavigationAction, WizardScreen


WELCOME_TEXT = """
# Welcome to ragged

**Privacy-first Retrieval-Augmented Generation**

ragged is a local RAG system that lets you ask questions about your documents
using AI, all while keeping your data completely private on your device.

## What we'll do

This wizard will guide you through:

1. **Check prerequisites** - Verify Docker, Python, and Ollama are ready
2. **Install dependencies** - Automatically install any missing components
3. **Configure ragged** - Set up storage locations and preferences
4. **Verify installation** - Confirm everything works correctly

## Requirements

- **Disk space**: At least 10GB free (for models and documents)
- **Memory**: 8GB RAM recommended (4GB minimum)
- **Internet**: Required for initial model downloads

## Time estimate

The installation typically takes 5-15 minutes, depending on your
internet speed and which components need to be installed.
"""


class WelcomeScreen(WizardScreen):
    """Welcome screen for the installation wizard."""

    @property
    def title(self) -> str:
        """Return screen title."""
        return "Welcome to ragged"

    @property
    def subtitle(self) -> str | None:
        """Return screen subtitle."""
        return "Privacy-first local RAG system"

    def render(self) -> None:
        """Render welcome content."""
        self.console.print(Markdown(WELCOME_TEXT))
        self.console.print()

        # Check for resume capability
        if self.wizard.get_choice("resumed"):
            self.console.print(
                Panel(
                    "[green]Welcome back![/green] Your previous progress has been restored.",
                    border_style="green",
                )
            )
            self.console.print()

    def process(self) -> NavigationAction:
        """Process user input."""
        self.console.print(
            "[dim]Press Enter to begin, or 'a' to abort[/dim]"
        )

        from rich.prompt import Prompt

        choice = Prompt.ask("", default="").lower().strip()

        if choice in ("a", "abort"):
            from rich.prompt import Confirm

            if Confirm.ask("[red]Are you sure you want to abort?[/red]"):
                return NavigationAction.ABORT

        return NavigationAction.NEXT
