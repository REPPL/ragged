"""
Health Dashboard.

REFINE-003: Rich-based health dashboard for real-time status.
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ragged.install.health.checks import (
    CheckCategory,
    HealthCheckSuite,
    HealthLevel,
    ServiceHealth,
)


class HealthDashboard:
    """
    Interactive health dashboard.

    Displays real-time health status with rich formatting.
    """

    def __init__(
        self,
        ragged_home: Path | None = None,
        console: Console | None = None,
    ) -> None:
        """
        Initialise health dashboard.

        Args:
            ragged_home: Path to ragged home.
            console: Rich console.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self.console = console or Console()
        self.suite = HealthCheckSuite(self.ragged_home)

    def display(self, refresh: bool = False) -> None:
        """
        Display health dashboard.

        Args:
            refresh: Whether to auto-refresh.
        """
        if refresh:
            self._display_live()
        else:
            self._display_static()

    def _display_static(self) -> None:
        """Display static health dashboard."""
        results = self.suite.check_all()

        # Overall status
        overall = self._get_overall_status(results)
        self._display_header(overall)

        # Service table
        self._display_services(results)

        # Quick actions
        self._display_actions(results)

    def _display_live(self) -> None:
        """Display live-updating dashboard."""
        import time

        with Live(
            self._render_dashboard(),
            console=self.console,
            refresh_per_second=1,
        ) as live:
            try:
                while True:
                    live.update(self._render_dashboard())
                    time.sleep(5)
            except KeyboardInterrupt:
                pass

    def _render_dashboard(self) -> Panel:
        """Render dashboard panel."""
        results = self.suite.check_all()
        overall = self._get_overall_status(results)

        # Build content
        content = []

        # Status line
        status_text = self._get_status_text(overall)
        content.append(status_text)
        content.append(Text())

        # Service table
        table = self._build_service_table(results)
        content.append(table)

        from rich.console import Group
        return Panel(
            Group(*content),
            title=self._get_title(overall),
            border_style=self._get_border_style(overall),
        )

    def _display_header(self, overall: HealthLevel) -> None:
        """Display dashboard header."""
        status_text = self._get_status_text(overall)
        self.console.print(
            Panel(
                status_text,
                title=self._get_title(overall),
                border_style=self._get_border_style(overall),
            )
        )
        self.console.print()

    def _display_services(self, results: list[ServiceHealth]) -> None:
        """Display service status table."""
        table = self._build_service_table(results)
        self.console.print(table)
        self.console.print()

    def _build_service_table(self, results: list[ServiceHealth]) -> Table:
        """Build service status table."""
        table = Table(show_header=True, header_style="bold")
        table.add_column("Service")
        table.add_column("Status", justify="center")
        table.add_column("Connectivity", justify="center")
        table.add_column("Performance", justify="center")
        table.add_column("Details")

        for health in results:
            # Status
            status = self._format_level(health.level)

            # Connectivity
            conn = "[green]OK[/green]" if health.connectivity_ok else "[red]X[/red]"

            # Performance
            perf = "[green]OK[/green]" if health.performance_ok else "[yellow]Slow[/yellow]"

            # Details
            failed = [c for c in health.checks if not c.passed]
            if failed:
                details = failed[0].message
            elif health.version:
                details = f"v{health.version}"
            else:
                details = ""

            table.add_row(
                health.name,
                status,
                conn,
                perf,
                details,
            )

        return table

    def _display_actions(self, results: list[ServiceHealth]) -> None:
        """Display quick actions based on status."""
        unhealthy = [h for h in results if h.level == HealthLevel.UNHEALTHY]
        degraded = [h for h in results if h.level == HealthLevel.DEGRADED]

        if not unhealthy and not degraded:
            self.console.print("[green]All services healthy[/green]")
            return

        self.console.print("[bold]Quick Actions:[/bold]")

        for health in unhealthy:
            if health.name == "Ollama":
                self.console.print("  [cyan]ollama serve[/cyan] - Start Ollama")
            elif health.name == "ChromaDB":
                self.console.print("  [cyan]ragged start[/cyan] - Start ChromaDB")
            elif health.name == "ragged API":
                self.console.print("  [cyan]ragged start[/cyan] - Start API server")

        for health in degraded:
            self.console.print(f"  [cyan]ragged doctor --fix[/cyan] - Fix {health.name} issues")

    def _get_overall_status(self, results: list[ServiceHealth]) -> HealthLevel:
        """Get overall health status."""
        levels = [h.level for h in results]

        if HealthLevel.UNHEALTHY in levels:
            return HealthLevel.UNHEALTHY
        if HealthLevel.DEGRADED in levels:
            return HealthLevel.DEGRADED
        if HealthLevel.UNKNOWN in levels:
            return HealthLevel.DEGRADED

        return HealthLevel.HEALTHY

    def _get_status_text(self, level: HealthLevel) -> Text:
        """Get status text for level."""
        if level == HealthLevel.HEALTHY:
            return Text("All systems operational", style="green bold")
        elif level == HealthLevel.DEGRADED:
            return Text("Some systems degraded", style="yellow bold")
        elif level == HealthLevel.UNHEALTHY:
            return Text("Systems need attention", style="red bold")
        else:
            return Text("Status unknown", style="dim")

    def _get_title(self, level: HealthLevel) -> str:
        """Get panel title for level."""
        if level == HealthLevel.HEALTHY:
            return "[green]ragged Health[/green]"
        elif level == HealthLevel.DEGRADED:
            return "[yellow]ragged Health[/yellow]"
        else:
            return "[red]ragged Health[/red]"

    def _get_border_style(self, level: HealthLevel) -> str:
        """Get border style for level."""
        if level == HealthLevel.HEALTHY:
            return "green"
        elif level == HealthLevel.DEGRADED:
            return "yellow"
        else:
            return "red"

    def _format_level(self, level: HealthLevel) -> str:
        """Format health level."""
        if level == HealthLevel.HEALTHY:
            return "[green]Healthy[/green]"
        elif level == HealthLevel.DEGRADED:
            return "[yellow]Degraded[/yellow]"
        elif level == HealthLevel.UNHEALTHY:
            return "[red]Unhealthy[/red]"
        else:
            return "[dim]Unknown[/dim]"


def display_health_dashboard(
    ragged_home: Path | None = None,
    refresh: bool = False,
) -> None:
    """
    Display health dashboard.

    Args:
        ragged_home: Path to ragged home.
        refresh: Whether to auto-refresh.
    """
    dashboard = HealthDashboard(ragged_home)
    dashboard.display(refresh=refresh)
