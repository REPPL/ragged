"""Analytics CLI commands for displaying performance metrics.

v0.6.6: CLI Analytics Commands - Display caching and streaming metrics
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ragged.caching import get_cache_manager


@click.group(name="analytics")
def analytics_group():
    """Display analytics and performance metrics."""
    pass


@analytics_group.command(name="cache")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed cache statistics")
def cache_stats(detailed: bool):
    """Display cache performance statistics."""
    console = Console()
    manager = get_cache_manager()

    if not manager.enabled:
        console.print("[yellow]Caching is currently disabled[/yellow]")
        return

    stats = manager.get_stats()

    # Create summary table
    table = Table(title="Cache Performance Metrics", show_header=True, header_style="bold cyan")
    table.add_column("Layer", style="cyan")
    table.add_column("Hit Rate", justify="right")
    table.add_column("Entries", justify="right")
    table.add_column("Size (MB)", justify="right")

    for layer_name, layer_stats in stats.items():
        if layer_name == "total_size_mb":
            continue

        hit_rate = layer_stats.get("hit_rate", 0) * 100
        entries = layer_stats.get("entries", 0)
        size_mb = layer_stats.get("size_mb", 0)

        table.add_row(
            layer_name.replace("_", " ").title(),
            f"{hit_rate:.1f}%",
            str(entries),
            f"{size_mb:.2f}"
        )

    console.print(table)
    console.print(f"\n[bold]Total Cache Size:[/bold] {stats.get('total_size_mb', 0):.2f} MB\n")

    if detailed:
        # Show detailed stats in panel
        details = []
        for layer_name, layer_stats in stats.items():
            if layer_name != "total_size_mb":
                details.append(f"[cyan]{layer_name}:[/cyan]")
                details.append(f"  Hits: {layer_stats.get('cache_hits', 0)}")
                details.append(f"  Misses: {layer_stats.get('cache_misses', 0)}")
                details.append(f"  Evictions: {layer_stats.get('evictions', 0)}")
                details.append("")

        console.print(Panel("\n".join(details), title="Detailed Statistics", border_style="blue"))


@analytics_group.command(name="clear-cache")
@click.confirmation_option(prompt="Are you sure you want to clear all caches?")
def clear_cache():
    """Clear all caches."""
    console = Console()
    manager = get_cache_manager()

    manager.clear_all()
    console.print("[green]✓ All caches cleared successfully[/green]")


@analytics_group.command(name="status")
def status():
    """Show overall system status and configuration."""
    console = Console()

    # Check caching status
    manager = get_cache_manager()
    cache_status = "[green]Enabled[/green]" if manager.enabled else "[red]Disabled[/red]"

    status_info = f"""
[bold cyan]Ragged v0.6.x Status[/bold cyan]

[bold]Caching:[/bold] {cache_status}
[bold]Analytics:[/bold] [green]Available[/green]
[bold]Streaming:[/bold] [green]Available[/green]

[dim]Use 'ragged analytics cache' to view cache metrics[/dim]
"""

    console.print(Panel(status_info.strip(), title="System Status", border_style="cyan"))
