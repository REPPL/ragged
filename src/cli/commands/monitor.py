"""Observability dashboard command for ragged CLI.

v0.2.9: Real-time metrics monitoring.
"""

import time
import click
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.cli.common import console
from src.utils.metrics import get_metrics_collector


def create_system_panel(metrics: dict) -> Panel:
    """Create system metrics panel.

    Args:
        metrics: Metrics dictionary

    Returns:
        Rich Panel with system metrics
    """
    cpu = metrics.get("cpu_percent", 0.0)
    memory = metrics.get("memory_percent", 0.0)
    disk = metrics.get("disk_percent", 0.0)

    # Color-code based on thresholds
    cpu_color = "green" if cpu < 70 else "yellow" if cpu < 90 else "red"
    mem_color = "green" if memory < 70 else "yellow" if memory < 90 else "red"
    disk_color = "green" if disk < 70 else "yellow" if disk < 90 else "red"

    content = (
        f"[bold]CPU:[/bold] [{cpu_color}]{cpu:.1f}%[/{cpu_color}]\n"
        f"[bold]Memory:[/bold] [{mem_color}]{memory:.1f}%[/{mem_color}] "
        f"({metrics.get('memory_available_mb', 0):.0f} MB available)\n"
        f"[bold]Disk:[/bold] [{disk_color}]{disk:.1f}%[/{disk_color}] "
        f"({metrics.get('disk_free_gb', 0):.1f} GB free)"
    )

    return Panel(content, title="[bold cyan]System Resources[/bold cyan]", border_style="cyan")


def create_application_panel(metrics: dict) -> Panel:
    """Create application metrics panel.

    Args:
        metrics: Metrics dictionary

    Returns:
        Rich Panel with application metrics
    """
    cache_hit_rate = metrics.get("cache_hit_rate", 0.0)
    cache_size = metrics.get("cache_size", 0)
    active_ops = metrics.get("active_operations", 0)
    queued_ops = metrics.get("queued_operations", 0)
    log_queue = metrics.get("log_queue_size", 0)
    logs_dropped = metrics.get("logs_dropped", 0)

    # Color-code cache hit rate
    cache_color = "green" if cache_hit_rate > 0.7 else "yellow" if cache_hit_rate > 0.5 else "red"

    content = (
        f"[bold]Cache Hit Rate:[/bold] [{cache_color}]{cache_hit_rate:.1%}[/{cache_color}] ({cache_size} entries)\n"
        f"[bold]Active Operations:[/bold] {active_ops}\n"
        f"[bold]Queued Operations:[/bold] {queued_ops}\n"
        f"[bold]Log Queue:[/bold] {log_queue} (dropped: {logs_dropped})"
    )

    return Panel(content, title="[bold green]Application[/bold green]", border_style="green")


def create_performance_table(metrics: dict) -> Table:
    """Create performance metrics table.

    Args:
        metrics: Metrics dictionary

    Returns:
        Rich Table with performance metrics
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    # Add timer metrics
    timer_metrics = {
        k.replace("timer_", "").replace("_avg", ""): v
        for k, v in metrics.items()
        if k.startswith("timer_") and k.endswith("_avg")
    }

    for name, value in sorted(timer_metrics.items()):
        table.add_row(f"{name} (avg)", f"{value*1000:.2f} ms")

    # Add counter metrics
    counter_metrics = {
        k.replace("counter_", ""): v
        for k, v in metrics.items()
        if k.startswith("counter_")
    }

    for name, value in sorted(counter_metrics.items()):
        table.add_row(name, str(value))

    if not table.rows:
        table.add_row("[dim]No performance metrics yet[/dim]", "")

    return table


def create_dashboard(metrics: dict) -> Layout:
    """Create complete dashboard layout.

    Args:
        metrics: Metrics dictionary

    Returns:
        Rich Layout with complete dashboard
    """
    layout = Layout()

    # Split into top and bottom
    layout.split_column(
        Layout(name="top", size=7),
        Layout(name="middle", size=7),
        Layout(name="bottom"),
    )

    # Top: System resources
    layout["top"].update(create_system_panel(metrics))

    # Middle: Application metrics
    layout["middle"].update(create_application_panel(metrics))

    # Bottom: Performance table
    layout["bottom"].update(
        Panel(
            create_performance_table(metrics),
            title="[bold yellow]Performance Metrics[/bold yellow]",
            border_style="yellow"
        )
    )

    return layout


@click.command()
@click.option("--interval", "-i", default=1.0, help="Refresh interval in seconds")
@click.option("--duration", "-d", type=int, help="Duration to run in seconds (default: run forever)")
@click.option("--prometheus", is_flag=True, help="Export Prometheus metrics instead of dashboard")
def monitor(interval: float, duration: Optional[int], prometheus: bool) -> None:
    """Live performance monitoring dashboard.

    Displays real-time metrics including:
    - System resources (CPU, memory, disk)
    - Application metrics (cache, operations, logging)
    - Performance timers and counters

    Examples:
        ragged monitor                 # Run dashboard
        ragged monitor -i 0.5          # Refresh every 0.5s
        ragged monitor -d 60           # Run for 60 seconds
        ragged monitor --prometheus    # Export Prometheus metrics
    """
    collector = get_metrics_collector()

    if prometheus:
        # One-time Prometheus export
        console.print(collector.export_prometheus())
        return

    # Live dashboard
    start_time = time.time()

    try:
        with Live(create_dashboard({}), refresh_per_second=1/interval, console=console) as live:
            while True:
                # Collect metrics
                metrics = collector.collect_metrics()

                # Update dashboard
                live.update(create_dashboard(metrics))

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break

                # Sleep
                time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped.[/yellow]")


# Import fix for Optional
from typing import Optional
