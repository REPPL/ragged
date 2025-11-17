"""Configuration management commands for ragged CLI."""

import sys
from typing import Any, Dict, Optional

import click

from src.cli.common import console, TableType
from src.config.settings import get_settings


@click.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    settings = get_settings()

    table = TableType(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Environment", settings.environment)
    table.add_row("Log Level", settings.log_level)
    table.add_row("Data Directory", str(settings.data_dir))
    table.add_row("Embedding Model", settings.embedding_model.value)
    table.add_row("Embedding Model Name", settings.embedding_model_name)
    table.add_row("LLM Model", settings.llm_model)
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Chunk Overlap", str(settings.chunk_overlap))
    table.add_row("ChromaDB URL", settings.chroma_url)
    table.add_row("Ollama URL", settings.ollama_url)

    console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    console.print("[yellow]Config modification not yet implemented. Edit .env file manually.[/yellow]")
    console.print(f"To set {key}={value}, add to .env file:")


@config.command("set-model")
@click.argument("model_name", required=False)
@click.option("--auto", is_flag=True, help="Automatically select recommended model")
def config_set_model(model_name: Optional[str], auto: bool) -> None:
    """Set the LLM model to use for generation.

    If no model specified, shows interactive selection menu.
    Use --auto to automatically select the recommended model.
    """
    from src.config.model_manager import ModelManager
    from src.config.settings import get_settings
    import yaml  # type: ignore[import-untyped]

    settings = get_settings()
    manager = ModelManager(settings.ollama_url)

    # Auto mode
    if auto:
        recommended = manager.get_recommended_model()
        if not recommended:
            console.print("[red]✗[/red] No models available. Install with: ollama pull llama3.2:latest")
            sys.exit(1)
        model_name = recommended
        console.print(f"[green]✓[/green] Auto-selected: {model_name}")

    # If model specified directly
    elif model_name:
        if not manager.verify_model(model_name):
            console.print(f"[red]✗[/red] Model '{model_name}' not found.")
            console.print("\nRun 'ragged config list-models' to see available models")
            sys.exit(1)

    # Interactive mode
    else:
        models = manager.list_available_models()

        if not models:
            console.print("[red]✗[/red] No models available.")
            console.print("\nInstall a model with:")
            console.print("  ollama pull llama3.2:latest")
            sys.exit(1)

        # Display selection table
        table = TableType(title="Available Models")
        table.add_column("#", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Context", style="yellow")
        table.add_column("Suitability", style="green")

        for i, m in enumerate(models[:10], 1):  # Show top 10
            score_bar = "█" * (m.suitability_score // 10)
            context_str = f"{m.context_length // 1000}k"
            table.add_row(str(i), m.name, context_str, f"{score_bar} ({m.suitability_score})")

        console.print(table)
        console.print()

        # Get selection
        while True:
            choice = click.prompt(f"Select model [1-{min(10, len(models))}]", type=int, default=1)
            if 1 <= choice <= min(10, len(models)):
                model_name = models[choice - 1].name
                break
            console.print("[red]Invalid selection[/red]")

    # Save to config file (ensure directory exists first)
    data_dir = settings.ensure_data_dir()
    config_file = data_dir / "config.yml"
    config: Dict[str, Any] = {}

    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}

    config["llm_model"] = model_name

    with open(config_file, "w") as f:
        yaml.dump(config, f)

    console.print(f"[green]✓[/green] Model set to: {model_name}")
    console.print(f"  Config: {config_file}")
    console.print("\nNote: Set RAGGED_LLM_MODEL in .env for persistent configuration")


@config.command("list-models")
def config_list_models() -> None:
    """List all available Ollama models with RAG suitability scores."""
    from src.config.model_manager import ModelManager
    from src.config.settings import get_settings

    settings = get_settings()
    manager = ModelManager(settings.ollama_url)

    try:
        models = manager.list_available_models()

        if not models:
            console.print("[yellow]No models available.[/yellow]")
            console.print("\nInstall a model with:")
            console.print("  ollama pull llama3.2:latest")
            return

        table = TableType(title="Available Ollama Models")
        table.add_column("Model", style="cyan")
        table.add_column("Family", style="magenta")
        table.add_column("Context", style="yellow")
        table.add_column("RAG Suitability", style="green")
        table.add_column("Status", style="blue")

        current_model = settings.llm_model

        for m in models:
            score_bar = "█" * (m.suitability_score // 10)
            context_str = f"{m.context_length // 1000}k tokens"
            status = "✓ Current" if m.name == current_model else ""

            table.add_row(m.name, m.family, context_str, f"{score_bar} {m.suitability_score}/100", status)

        console.print(table)
        console.print()
        console.print(f"Current model: [bold]{current_model}[/bold]")
        console.print(f"\nChange model with: ragged config set-model")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list models: {e}")
        sys.exit(1)
