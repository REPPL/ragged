"""
Post-Install Setup Wizard.

WIZARD-005: Guide users through post-installation setup.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table


@dataclass
class SetupResult:
    """Result of post-install setup."""

    success: bool
    steps_completed: list[str]
    steps_skipped: list[str]
    errors: list[str]
    recommendations: list[str]


class PostInstallSetup:
    """
    Post-installation setup wizard.

    Guides users through optional setup steps after installation.
    """

    def __init__(
        self,
        ragged_home: Path | None = None,
        console: Console | None = None,
    ) -> None:
        """
        Initialise post-install setup.

        Args:
            ragged_home: Path to ragged home directory.
            console: Rich console for output.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self.console = console or Console()

    def run(self, interactive: bool = True) -> SetupResult:
        """
        Run post-installation setup.

        Args:
            interactive: Whether to prompt user for choices.

        Returns:
            Setup result.
        """
        result = SetupResult(
            success=True,
            steps_completed=[],
            steps_skipped=[],
            errors=[],
            recommendations=[],
        )

        self.console.print(
            Panel(
                "[bold]Post-Installation Setup[/bold]\n\n"
                "This wizard will help you complete your ragged setup.",
                border_style="blue",
            )
        )
        self.console.print()

        # Step 1: Verify installation
        self._verify_installation(result)

        # Step 2: Pull recommended models
        if interactive:
            self._setup_models(result)

        # Step 3: Create example collection
        if interactive:
            self._setup_example_collection(result)

        # Step 4: Configure shell integration
        if interactive:
            self._setup_shell_integration(result)

        # Step 5: Show recommendations
        self._show_recommendations(result)

        # Summary
        self._show_summary(result)

        return result

    def _verify_installation(self, result: SetupResult) -> None:
        """Verify installation is complete."""
        self.console.print("[bold]Verifying Installation...[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Running health checks...", total=None)

            from ragged.install.post_install.health_check import run_health_checks

            status, checks = run_health_checks(self.ragged_home)

            progress.remove_task(task)

        # Display results
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Check")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        for check in checks:
            if check.status.value == "healthy":
                status_str = "[green]OK[/green]"
            elif check.status.value == "degraded":
                status_str = "[yellow]Warning[/yellow]"
            elif check.status.value == "unhealthy":
                status_str = "[red]Failed[/red]"
            else:
                status_str = "[dim]Unknown[/dim]"

            table.add_row(check.name.title(), status_str, check.message)

            if check.fix_suggestion:
                result.recommendations.append(check.fix_suggestion)

        self.console.print(table)
        self.console.print()

        result.steps_completed.append("Verified installation")

    def _setup_models(self, result: SetupResult) -> None:
        """Set up recommended models."""
        self.console.print("[bold]LLM Models[/bold]\n")

        recommended_models = [
            ("llama3.2:3b", "Fast, efficient 3B model for general use"),
            ("nomic-embed-text", "Text embeddings for document search"),
        ]

        self.console.print("Recommended models for ragged:\n")
        for model, description in recommended_models:
            self.console.print(f"  - [cyan]{model}[/cyan]: {description}")
        self.console.print()

        if not Confirm.ask("Pull recommended models now?", default=True):
            result.steps_skipped.append("Model setup")
            result.recommendations.append(
                "Run 'ollama pull llama3.2:3b' to get the recommended model"
            )
            return

        import subprocess

        for model, _ in recommended_models:
            self.console.print(f"\n[dim]Pulling {model}...[/dim]")
            try:
                subprocess.run(
                    ["ollama", "pull", model],
                    check=True,
                    timeout=600,  # 10 minute timeout
                )
                self.console.print(f"[green]Successfully pulled {model}[/green]")
            except subprocess.CalledProcessError as e:
                self.console.print(f"[red]Failed to pull {model}: {e}[/red]")
                result.errors.append(f"Failed to pull {model}")
            except FileNotFoundError:
                self.console.print("[red]Ollama not found. Skipping model setup.[/red]")
                result.errors.append("Ollama not installed")
                break
            except subprocess.TimeoutExpired:
                self.console.print(f"[yellow]Model pull timed out for {model}[/yellow]")
                result.errors.append(f"Timeout pulling {model}")

        result.steps_completed.append("Model setup")
        self.console.print()

    def _setup_example_collection(self, result: SetupResult) -> None:
        """Create example document collection."""
        self.console.print("[bold]Example Collection[/bold]\n")

        if not Confirm.ask(
            "Create an example document collection?",
            default=False,
        ):
            result.steps_skipped.append("Example collection")
            return

        # Create example documents directory
        example_dir = self.ragged_home / "documents" / "examples"
        example_dir.mkdir(parents=True, exist_ok=True)

        # Create a sample document
        sample_doc = example_dir / "welcome.md"
        sample_doc.write_text("""# Welcome to ragged

This is an example document to help you get started with ragged.

## What is ragged?

ragged is a privacy-first Retrieval-Augmented Generation (RAG) system.
It lets you ask questions about your documents using AI, while keeping
all your data local on your device.

## Getting Started

1. Add documents to the `documents` folder
2. Run `ragged add .` to index them
3. Ask questions with `ragged ask "your question"`

## Features

- **Local Processing**: All data stays on your device
- **Multiple Formats**: PDF, Word, Markdown, HTML, and more
- **Smart Search**: Semantic search finds relevant content
- **Context-Aware**: AI understands your documents

Enjoy using ragged!
""")

        self.console.print(f"[green]Created example document at {sample_doc}[/green]")
        result.steps_completed.append("Example collection created")
        self.console.print()

    def _setup_shell_integration(self, result: SetupResult) -> None:
        """Set up shell integration."""
        self.console.print("[bold]Shell Integration[/bold]\n")

        shell_rc_files = {
            "bash": Path.home() / ".bashrc",
            "zsh": Path.home() / ".zshrc",
            "fish": Path.home() / ".config" / "fish" / "config.fish",
        }

        # Detect current shell
        import os

        shell = os.environ.get("SHELL", "")
        shell_name = Path(shell).name if shell else "unknown"

        if shell_name not in shell_rc_files:
            self.console.print(
                f"[dim]Unknown shell: {shell_name}. Skipping shell integration.[/dim]\n"
            )
            result.steps_skipped.append("Shell integration")
            return

        rc_file = shell_rc_files[shell_name]

        self.console.print(f"Detected shell: [cyan]{shell_name}[/cyan]\n")

        if not Confirm.ask(
            f"Add ragged completions to {rc_file}?",
            default=False,
        ):
            result.steps_skipped.append("Shell integration")
            result.recommendations.append(
                f"Add shell completions manually: ragged --install-completion {shell_name}"
            )
            return

        # Add completion to shell RC
        completion_line = f'\neval "$(ragged --show-completion {shell_name})"\n'

        try:
            with open(rc_file, "a") as f:
                f.write(completion_line)

            self.console.print(
                f"[green]Added completions to {rc_file}[/green]\n"
                f"[dim]Restart your shell or run: source {rc_file}[/dim]"
            )
            result.steps_completed.append("Shell integration")
        except OSError as e:
            self.console.print(f"[red]Failed to update {rc_file}: {e}[/red]")
            result.errors.append(f"Shell integration failed: {e}")

        self.console.print()

    def _show_recommendations(self, result: SetupResult) -> None:
        """Show recommendations."""
        if not result.recommendations:
            return

        self.console.print("[bold]Recommendations[/bold]\n")

        for i, rec in enumerate(result.recommendations, 1):
            self.console.print(f"  {i}. {rec}")

        self.console.print()

    def _show_summary(self, result: SetupResult) -> None:
        """Show setup summary."""
        self.console.print()

        if result.errors:
            self.console.print(
                Panel(
                    "[yellow]Setup completed with some issues.[/yellow]\n\n"
                    "Errors:\n"
                    + "\n".join(f"  - {e}" for e in result.errors),
                    border_style="yellow",
                )
            )
        else:
            self.console.print(
                Panel(
                    "[green]Setup complete![/green]\n\n"
                    "Quick start commands:\n\n"
                    "  [cyan]ragged start[/cyan]     - Start all services\n"
                    "  [cyan]ragged add .[/cyan]     - Add documents from current directory\n"
                    "  [cyan]ragged ask[/cyan]       - Ask questions about your documents\n\n"
                    "Web interface: http://localhost:5173",
                    border_style="green",
                )
            )


def run_post_install_setup(
    ragged_home: Path | None = None,
    interactive: bool = True,
) -> SetupResult:
    """
    Run post-installation setup.

    Args:
        ragged_home: Path to ragged home directory.
        interactive: Whether to run interactively.

    Returns:
        Setup result.
    """
    setup = PostInstallSetup(ragged_home)
    return setup.run(interactive=interactive)
