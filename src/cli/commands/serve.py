"""API server CLI commands.

v0.3.12: REST API server for web/mobile integration.
"""


import click
from rich.console import Console
from rich.panel import Panel

from ragged.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option(
    "--host",
    "-h",
    default="127.0.0.1",
    help="Host to bind to (default: 127.0.0.1)",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Port to bind to (default: 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload on code changes (development)",
)
@click.option(
    "--workers",
    "-w",
    default=1,
    type=int,
    help="Number of worker processes (default: 1)",
)
@click.option(
    "--log-level",
    type=click.Choice(["critical", "error", "warning", "info", "debug"]),
    default="info",
    help="Log level (default: info)",
)
def serve(
    host: str,
    port: int,
    reload: bool,
    workers: int,
    log_level: str,
):
    """
    Start the ragged REST API server.

    Examples:
        ragged serve                           # Start with defaults
        ragged serve --host 0.0.0.0 --port 8080  # Custom host/port
        ragged serve --reload                  # Development mode
        ragged serve --workers 4               # Production with 4 workers
    """
    try:
        # Import uvicorn here to avoid import errors if not installed
        import uvicorn
    except ImportError:
        console.print(
            "[red]Error:[/red] uvicorn is required to run the API server"
        )
        console.print("Install with: [cyan]pip install uvicorn[/cyan]")
        raise click.Abort()

    # Display startup banner
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]ragged REST API Server[/bold cyan]\n\n"
            f"[green]Host:[/green] {host}\n"
            f"[green]Port:[/green] {port}\n"
            f"[green]Docs:[/green] http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs\n"
            f"[green]ReDoc:[/green] http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc\n"
            f"[green]Workers:[/green] {workers}\n"
            f"[green]Reload:[/green] {'Enabled' if reload else 'Disabled'}",
            border_style="cyan",
            title="[bold]Server Configuration[/bold]",
        )
    )
    console.print()

    # v0.5.8 MEDIUM-4: Add confirmation prompt for external network exposure
    if host == "0.0.0.0":
        console.print(
            "[bold yellow]⚠ Security Warning:[/bold yellow] Server will be accessible from external network\n"
        )
        console.print("  • Anyone on your network can access the API")
        console.print("  • Ensure proper authentication is configured")
        console.print("  • Ensure firewall rules are in place\n")

        if not click.confirm("Do you want to continue with external network binding?", default=False):
            console.print("[red]Server startup cancelled[/red]")
            raise click.Abort()

    console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

    # Start server
    try:
        uvicorn.run(
            "src.web.api:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # reload requires single worker
            log_level=log_level,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        logger.exception("Server error")
        console.print(f"\n[red]Server error:[/red] {e}")
        raise click.Abort()


# Export
__all__ = ["serve"]
