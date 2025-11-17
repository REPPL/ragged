"""Health check command for ragged CLI."""

import sys

import click

from src.cli.common import console


@click.command()
def health() -> None:
    """Check health of all services."""
    from src.generation.ollama_client import OllamaClient
    from src.storage.vector_store import VectorStore

    console.print("[bold]Checking services...[/bold]")
    console.print()

    all_healthy = True

    # Ollama
    try:
        client = OllamaClient()
        if client.health_check():
            console.print("[green]✓[/green] Ollama: Running")
        else:
            console.print("[red]✗[/red] Ollama: Not responding")
            all_healthy = False
    except Exception as e:
        console.print(f"[red]✗[/red] Ollama: {e}")
        all_healthy = False

    # ChromaDB
    try:
        vector_store = VectorStore()
        if vector_store.health_check():
            count = vector_store.count()
            console.print(f"[green]✓[/green] ChromaDB: Running ({count} chunks stored)")
        else:
            console.print("[red]✗[/red] ChromaDB: Not responding")
            all_healthy = False
    except Exception as e:
        console.print(f"[red]✗[/red] ChromaDB: {e}")
        all_healthy = False

    console.print()
    if all_healthy:
        console.print("[bold green]All services healthy![/bold green]")
    else:
        console.print("[bold yellow]Some services are not available.[/bold yellow]")
        sys.exit(1)
