"""Configuration management commands for ragged CLI."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml

from src.cli.common import console, TableType
from src.config.settings import get_settings
from src.config.config_manager import RaggedConfig, ConfigValidator
from src.config.personas import PersonaManager


@click.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command("show")
@click.option("--verbose", "-v", is_flag=True, help="Show all configuration sources")
def config_show(verbose: bool) -> None:
    """Show current merged configuration."""
    cfg = RaggedConfig.load()
    settings = get_settings()

    # Main configuration table
    table = TableType(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    # Active persona
    table.add_row("Active Persona", cfg.persona)
    table.add_row("", "")  # Separator

    # Retrieval settings
    table.add_row("Retrieval Method", cfg.retrieval_method)
    table.add_row("Top-K", str(cfg.top_k))
    table.add_row("BM25 Weight", f"{cfg.bm25_weight:.2f}")
    table.add_row("Vector Weight", f"{cfg.vector_weight:.2f}")
    table.add_row("", "")  # Separator

    # Reranking settings
    table.add_row("Enable Reranking", "✓" if cfg.enable_reranking else "✗")
    table.add_row("Rerank To", str(cfg.rerank_to))
    table.add_row("Rerank Model", cfg.rerank_model)
    table.add_row("", "")  # Separator

    # Query processing
    table.add_row("Query Decomposition", "✓" if cfg.enable_query_decomposition else "✗")
    table.add_row("HyDE", "✓" if cfg.enable_hyde else "✗")
    table.add_row("Compression", "✓" if cfg.enable_compression else "✗")
    table.add_row("", "")  # Separator

    # Generation settings
    table.add_row("LLM Model", cfg.llm_model)
    table.add_row("Temperature", f"{cfg.temperature:.2f}")
    table.add_row("Max Tokens", str(cfg.max_tokens))
    table.add_row("", "")  # Separator

    # Quality thresholds
    table.add_row("Confidence Threshold", f"{cfg.confidence_threshold:.2f}")

    console.print(table)

    if verbose:
        console.print()
        console.print("[dim]Configuration loaded from:[/dim]")
        console.print("[dim]  1. Defaults (in code)[/dim]")
        console.print("[dim]  2. User file (~/.config/ragged/config.yml)[/dim]")
        console.print("[dim]  3. Environment variables (RAGGED_*)[/dim]")
        console.print()
        console.print("[dim]Legacy settings (from .env):[/dim]")
        console.print(f"[dim]  Data Directory: {settings.data_dir}[/dim]")
        console.print(f"[dim]  Embedding Model: {settings.embedding_model.value}[/dim]")
        console.print(f"[dim]  ChromaDB URL: {settings.chroma_url}[/dim]")
        console.print(f"[dim]  Ollama URL: {settings.ollama_url}[/dim]")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value in user config file.

    \b
    Examples:
        ragged config set top_k 10
        ragged config set temperature 0.8
        ragged config set enable_reranking true
    """
    config_path = Path.home() / ".config" / "ragged" / "config.yml"

    # Load existing config or create new
    config_path.parent.mkdir(parents=True, exist_ok=True)
    user_config: Dict[str, Any] = {}

    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}

    # Set the value (with type conversion)
    try:
        # Try to infer type
        if value.lower() in ["true", "false"]:
            user_config[key] = value.lower() == "true"
        elif value.replace(".", "", 1).isdigit():
            user_config[key] = float(value) if "." in value else int(value)
        else:
            user_config[key] = value

        # Save updated config
        with open(config_path, "w") as f:
            yaml.dump(user_config, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓[/green] Set {key} = {user_config[key]}")
        console.print(f"  Config file: {config_path}")

        # Validate the resulting configuration
        cfg = RaggedConfig.load()
        validator = ConfigValidator()
        is_valid, errors = validator.validate(cfg)

        if not is_valid:
            console.print()
            console.print("[yellow]Warning: Configuration has validation errors:[/yellow]")
            for error in errors:
                console.print(f"  [yellow]•[/yellow] {error}")
            console.print()
            console.print("Run 'ragged config validate' for full validation")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to set configuration: {e}")
        sys.exit(1)


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


@config.command("validate")
@click.option("--config-file", type=click.Path(exists=True), help="Config file to validate")
def config_validate(config_file: Optional[str]) -> None:
    """Validate configuration file against constraints.

    \b
    Examples:
        ragged config validate
        ragged config validate --config-file ~/.config/ragged/config.yml
    """
    # Load configuration
    config_path = Path(config_file) if config_file else None
    try:
        cfg = RaggedConfig.load(config_path)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load configuration: {e}")
        sys.exit(1)

    # Validate
    validator = ConfigValidator()
    is_valid, errors = validator.validate(cfg)

    if is_valid:
        console.print("[green]✓[/green] Configuration is valid")
        console.print()
        console.print("[bold]Current settings:[/bold]")
        console.print(f"  Persona: {cfg.persona}")
        console.print(f"  Retrieval: {cfg.retrieval_method}")
        console.print(f"  Top-K: {cfg.top_k}")
        console.print(f"  Reranking: {'enabled' if cfg.enable_reranking else 'disabled'}")
    else:
        console.print("[red]✗[/red] Configuration has validation errors:")
        console.print()
        for error in errors:
            console.print(f"  [red]•[/red] {error}")
        console.print()
        console.print("Fix these errors in your config file:")
        if config_file:
            console.print(f"  {config_file}")
        else:
            console.print(f"  {Path.home() / '.config' / 'ragged' / 'config.yml'}")
        sys.exit(1)


@config.command("generate")
@click.option("--persona", type=click.Choice(["accuracy", "speed", "balanced", "research", "quick-answer"]),
              default="balanced", help="Base persona for generated config")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config file")
def config_generate(persona: str, force: bool) -> None:
    """Generate default configuration file.

    \b
    Examples:
        ragged config generate
        ragged config generate --persona accuracy
        ragged config generate --force
    """
    config_path = Path.home() / ".config" / "ragged" / "config.yml"

    # Check if file exists
    if config_path.exists() and not force:
        console.print("[yellow]Configuration file already exists:[/yellow]")
        console.print(f"  {config_path}")
        console.print()
        console.print("Use --force to overwrite, or edit manually")
        sys.exit(1)

    # Create config with chosen persona
    cfg = RaggedConfig()
    PersonaManager.apply_persona(cfg, persona)

    # Save
    config_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.save(config_path)

    console.print(f"[green]✓[/green] Generated configuration file with '{persona}' persona")
    console.print(f"  Location: {config_path}")
    console.print()
    console.print("Edit this file to customise settings, or use:")
    console.print("  ragged config set <key> <value>")


@config.command("list-personas")
def config_list_personas() -> None:
    """List available configuration personas.

    \b
    Examples:
        ragged config list-personas
    """
    personas = PersonaManager.list_personas()

    table = TableType(title="Available Personas")
    table.add_column("Persona", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Status", style="green")

    # Get current persona
    cfg = RaggedConfig.load()
    current = cfg.persona

    for name, description in personas.items():
        status = "✓ Active" if name == current else ""
        table.add_row(name, description, status)

    console.print(table)
    console.print()
    console.print(f"Current persona: [bold]{current}[/bold]")
    console.print()
    console.print("Change persona with:")
    console.print("  ragged config set persona <name>")
    console.print()
    console.print("Or generate new config:")
    console.print("  ragged config generate --persona <name>")


@config.command("set-persona")
@click.argument("persona_name", type=click.Choice(["accuracy", "speed", "balanced", "research", "quick-answer"]))
def config_set_persona(persona_name: str) -> None:
    """Set default persona and apply its settings.

    \b
    Examples:
        ragged config set-persona accuracy
        ragged config set-persona speed
    """
    config_path = Path.home() / ".config" / "ragged" / "config.yml"

    # Load current config
    cfg = RaggedConfig.load()

    # Apply persona
    try:
        PersonaManager.apply_persona(cfg, persona_name)
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)

    # Save
    config_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.save(config_path)

    console.print(f"[green]✓[/green] Set default persona to: {persona_name}")
    console.print(f"  Config file: {config_path}")
    console.print()

    # Show what changed
    persona_config = PersonaManager.get_persona(persona_name)
    console.print("[bold]Applied settings:[/bold]")
    console.print(f"  Retrieval method: {persona_config.retrieval_method}")
    console.print(f"  Top-K: {persona_config.top_k}")
    console.print(f"  Reranking: {'enabled' if persona_config.enable_reranking else 'disabled'}")
    console.print(f"  Query decomposition: {'enabled' if persona_config.enable_query_decomposition else 'disabled'}")
    console.print(f"  HyDE: {'enabled' if persona_config.enable_hyde else 'disabled'}")
    console.print()
    console.print("View full config with: ragged config show")
