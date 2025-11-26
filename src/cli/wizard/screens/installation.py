"""
Installation Screen.

WIZARD-001: Screen for installing missing prerequisites.
"""

from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.prompt import Confirm
from rich.table import Table

from ragged.cli.wizard.framework import NavigationAction, WizardScreen


class InstallationScreen(WizardScreen):
    """Screen for installing missing components."""

    @property
    def title(self) -> str:
        """Return screen title."""
        return "Installing Components"

    @property
    def subtitle(self) -> str | None:
        """Return screen subtitle."""
        return "Installing missing prerequisites"

    @property
    def can_skip(self) -> bool:
        """Check if screen can be skipped."""
        missing = self.wizard.get_choice("missing_components", [])
        return len(missing) == 0

    def render(self) -> None:
        """Render installation screen."""
        missing = self.wizard.get_choice("missing_components", [])

        if not missing:
            self.console.print(
                Panel(
                    "[green]All prerequisites are already installed![/green]\n\n"
                    "No additional installation is needed.",
                    border_style="green",
                )
            )
            return

        # Show what will be installed
        self.console.print(
            Panel(
                "[bold]The following components will be installed:[/bold]\n\n"
                + "\n".join(f"  - {comp}" for comp in missing),
                border_style="blue",
            )
        )
        self.console.print()

        # Confirm installation
        if not self.wizard.get_result("installation_confirmed"):
            if not Confirm.ask("Proceed with installation?", default=True):
                self.wizard.set_result("installation_skipped", True)
                return

            self.wizard.set_result("installation_confirmed", True)

        # Run installation
        if not self.wizard.get_result("installation_complete"):
            self._run_installation(missing)

        # Show results
        self._display_results()

    def _run_installation(self, components: list[str]) -> None:
        """Run installation of missing components."""
        from ragged.install.installers import (
            DockerInstaller,
            OllamaInstaller,
            PythonInstaller,
        )

        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            for component in components:
                task = progress.add_task(f"Installing {component}...", total=100)

                try:
                    if component == "Docker":
                        installer = DockerInstaller()
                    elif component == "Python":
                        installer = PythonInstaller()
                    elif component == "Ollama":
                        installer = OllamaInstaller()
                    else:
                        progress.update(task, completed=100)
                        continue

                    # Update progress callback
                    def update_progress(pct: float) -> None:
                        progress.update(task, completed=int(pct * 100))

                    # Run installation
                    result = installer.install(progress_callback=update_progress)
                    results[component] = result

                except Exception as e:
                    from ragged.install.installers.base import (
                        InstallationResult,
                        InstallationStatus,
                    )

                    results[component] = InstallationResult(
                        status=InstallationStatus.FAILED,
                        success=False,
                        message=str(e),
                    )

                progress.update(task, completed=100)

        self.wizard.set_result("installation_results", results)
        self.wizard.set_result("installation_complete", True)

    def _display_results(self) -> None:
        """Display installation results."""
        results = self.wizard.get_result("installation_results", {})

        if not results:
            return

        table = Table(
            title="Installation Results",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Component", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Message")

        all_success = True
        requires_logout = False
        requires_reboot = False
        manual_steps = []

        for component, result in results.items():
            if result.success:
                status = "[green]Success[/green]"
            else:
                status = "[red]Failed[/red]"
                all_success = False

            table.add_row(component, status, result.message)

            if result.requires_logout:
                requires_logout = True
            if result.requires_reboot:
                requires_reboot = True
            if result.manual_steps:
                manual_steps.extend(result.manual_steps)

        self.console.print(table)
        self.console.print()

        # Show post-install requirements
        if requires_reboot:
            self.console.print(
                Panel(
                    "[yellow]A system reboot is required to complete installation.[/yellow]\n\n"
                    "Please reboot and run [bold]ragged install --resume[/bold] to continue.",
                    border_style="yellow",
                )
            )
        elif requires_logout:
            self.console.print(
                Panel(
                    "[yellow]You may need to log out and back in for changes to take effect.[/yellow]",
                    border_style="yellow",
                )
            )

        if manual_steps:
            self.console.print(
                Panel(
                    "[bold]Manual steps required:[/bold]\n\n"
                    + "\n".join(f"  {i+1}. {step}" for i, step in enumerate(manual_steps)),
                    border_style="yellow",
                )
            )

        if all_success:
            self.console.print("[green]All components installed successfully![/green]")
        else:
            self.console.print(
                "[red]Some components failed to install. "
                "You may need to install them manually.[/red]"
            )

        self.wizard.set_choice("installation_success", all_success)

    def process(self) -> NavigationAction:
        """Process user navigation."""
        if self.wizard.get_result("installation_skipped"):
            return NavigationAction.SKIP

        # Check if reboot required
        results = self.wizard.get_result("installation_results", {})
        for result in results.values():
            if result.requires_reboot:
                self.console.print(
                    "\n[yellow]Please reboot and resume installation.[/yellow]"
                )
                return NavigationAction.ABORT

        return self.prompt_navigation()
