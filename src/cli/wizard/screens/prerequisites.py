"""
Prerequisites Screen.

WIZARD-001: Screen for checking and displaying prerequisite status.
"""

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ragged.cli.wizard.framework import NavigationAction, WizardScreen


class PrerequisitesScreen(WizardScreen):
    """Screen for checking prerequisites."""

    @property
    def title(self) -> str:
        """Return screen title."""
        return "Checking Prerequisites"

    @property
    def subtitle(self) -> str | None:
        """Return screen subtitle."""
        return "Verifying your system is ready for ragged"

    def render(self) -> None:
        """Render prerequisites check."""
        # Run detection if not already done
        if not self.wizard.get_result("prerequisites_checked"):
            self._run_detection()

        # Display results
        self._display_results()

    def _run_detection(self) -> None:
        """Run prerequisite detection."""
        from ragged.install.detection import (
            DockerDetector,
            OllamaDetector,
            PythonDetector,
            EnvironmentDetector,
        )

        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Check Docker
            task = progress.add_task("Checking Docker...", total=None)
            docker = DockerDetector()
            results["docker"] = docker.detect()
            progress.remove_task(task)

            # Check Python
            task = progress.add_task("Checking Python...", total=None)
            python = PythonDetector()
            results["python"] = python.detect()
            progress.remove_task(task)

            # Check Ollama
            task = progress.add_task("Checking Ollama...", total=None)
            ollama = OllamaDetector()
            results["ollama"] = ollama.detect()
            progress.remove_task(task)

            # Check environment
            task = progress.add_task("Checking environment...", total=None)
            env = EnvironmentDetector()
            results["environment"] = env.detect()
            progress.remove_task(task)

        self.wizard.set_result("prerequisites", results)
        self.wizard.set_result("prerequisites_checked", True)

    def _display_results(self) -> None:
        """Display detection results."""
        results = self.wizard.get_result("prerequisites", {})

        # Create results table
        table = Table(
            title="Prerequisites Status",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Component", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Version", justify="center")
        table.add_column("Notes")

        # Docker
        docker = results.get("docker")
        if docker:
            status = "[green]Ready[/green]" if docker.installed else "[red]Missing[/red]"
            version = docker.version or "-"
            notes = ""
            if not docker.installed:
                notes = "[yellow]Will be installed[/yellow]"
            elif docker.details.get("daemon_running") is False:
                notes = "[yellow]Daemon not running[/yellow]"
            table.add_row("Docker", status, version, notes)

        # Python
        python = results.get("python")
        if python:
            status = "[green]Ready[/green]" if python.installed else "[red]Missing[/red]"
            version = python.version or "-"
            notes = ""
            if python.details.get("version_compatible") is False:
                notes = "[yellow]Version 3.10-3.12 required[/yellow]"
            table.add_row("Python", status, version, notes)

        # Ollama
        ollama = results.get("ollama")
        if ollama:
            status = "[green]Ready[/green]" if ollama.installed else "[red]Missing[/red]"
            version = ollama.version or "-"
            notes = ""
            if not ollama.installed:
                notes = "[yellow]Will be installed[/yellow]"
            elif not ollama.details.get("models"):
                notes = "[dim]No models installed[/dim]"
            table.add_row("Ollama", status, version, notes)

        # Environment
        env = results.get("environment")
        if env:
            status = "[green]Ready[/green]" if env.installed else "[yellow]Issues[/yellow]"
            version = "-"
            notes = ""
            if env.issues:
                notes = f"[yellow]{len(env.issues)} issues[/yellow]"
            table.add_row("Environment", status, version, notes)

        self.console.print(table)
        self.console.print()

        # Show issues if any
        all_issues = []
        for name, result in results.items():
            if result and result.issues:
                for issue in result.issues:
                    all_issues.append(f"[yellow]{name}:[/yellow] {issue}")

        if all_issues:
            self.console.print(
                Panel(
                    "\n".join(all_issues),
                    title="Issues Found",
                    border_style="yellow",
                )
            )
            self.console.print()

        # Determine if we can proceed
        missing = []
        if docker and not docker.installed:
            missing.append("Docker")
        if python and not python.installed:
            missing.append("Python")
        if ollama and not ollama.installed:
            missing.append("Ollama")

        if missing:
            self.console.print(
                f"[yellow]Missing components will be installed: {', '.join(missing)}[/yellow]"
            )
        else:
            self.console.print("[green]All prerequisites are met![/green]")

        self.wizard.set_choice("missing_components", missing)

    def process(self) -> NavigationAction:
        """Process user navigation."""
        return self.prompt_navigation()
