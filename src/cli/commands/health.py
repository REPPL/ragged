"""Health check command for ragged CLI."""

import sys

import click
from rich.table import Table

from src.cli.common import console
from src.utils.health import HealthChecker, HealthStatus


@click.command()
@click.option("--deep", is_flag=True, help="Run deep diagnostics (slower but thorough)")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def health(deep: bool, json_output: bool) -> None:
    """Check health of all services.

    Basic checks (fast):
    - Ollama connectivity
    - ChromaDB connectivity
    - Embedder performance
    - Disk space
    - Memory availability
    - Cache status

    Deep checks (--deep, slower):
    - Query performance
    - Index integrity
    - Network latency
    """
    checker = HealthChecker()

    if deep:
        console.print("[bold]Running deep health diagnostics...[/bold]")
    else:
        console.print("[bold]Running health checks...[/bold]")

    console.print()

    # Run checks
    results = checker.run_all_checks(deep=deep)

    # Output as JSON if requested
    if json_output:
        import json

        output = {
            "overall_status": _determine_overall_status(results).value,
            "checks": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details or {},
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                }
                for r in results
            ],
        }
        console.print(json.dumps(output, indent=2))
        sys.exit(0 if output["overall_status"] == "healthy" else 1)

    # Display results as table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Message")
    table.add_column("Time", justify="right")

    for result in results:
        # Status symbol and color
        if result.is_healthy():
            status_str = "[green]✓ HEALTHY[/green]"
        elif result.is_degraded():
            status_str = "[yellow]⚠ DEGRADED[/yellow]"
        else:
            status_str = "[red]✗ UNHEALTHY[/red]"

        # Format message with details
        message = result.message
        if result.details:
            # Add key details to message
            details_str = ", ".join(
                f"{k}={v}" for k, v in list(result.details.items())[:2]
            )
            if details_str:
                message = f"{message}\n[dim]{details_str}[/dim]"

        # Format duration
        if result.duration_ms > 0:
            duration_str = f"{result.duration_ms:.0f}ms"
        else:
            duration_str = "-"

        table.add_row(
            result.name.replace("_", " ").title(),
            status_str,
            message,
            duration_str,
        )

    console.print(table)
    console.print()

    # Overall status
    overall_status = _determine_overall_status(results)

    if overall_status == HealthStatus.HEALTHY:
        console.print("[bold green]✓ All systems healthy![/bold green]")
        sys.exit(0)
    elif overall_status == HealthStatus.DEGRADED:
        console.print("[bold yellow]⚠ Some systems degraded (functionality may be limited)[/bold yellow]")
        sys.exit(0)  # Exit 0 for degraded (not critical)
    else:
        console.print("[bold red]✗ Critical issues detected (some functionality unavailable)[/bold red]")
        sys.exit(1)


def _determine_overall_status(results) -> HealthStatus:
    """Determine overall health status from individual results.

    Args:
        results: List of HealthCheckResult

    Returns:
        Overall health status
    """
    if any(r.is_unhealthy() for r in results):
        return HealthStatus.UNHEALTHY
    elif any(r.is_degraded() for r in results):
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.HEALTHY
