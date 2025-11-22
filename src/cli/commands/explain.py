"""
Explainability commands for ragged CLI.

Provides transparency into ragged's decision-making and pipeline execution.
"""

import click

from src.cli.common import console
from src.config.config_manager import RaggedConfig
from src.config.personas import PersonaManager


@click.group()
def explain() -> None:
    """Explain ragged's decision-making and configuration."""
    pass


@explain.command()
@click.argument("query_text")
@click.option("--persona", help="Persona to explain")
def query(query_text: str, persona: str) -> None:
    """
    Explain what will happen when executing this query.

    Shows the pipeline without actually executing it.

    \b
    Examples:
        ragged explain query "What is machine learning?"
        ragged explain query "How does RAG work?" --persona accuracy
    """
    config = RaggedConfig.load()

    # Apply persona if specified
    if persona:
        try:
            PersonaManager.apply_persona(config, persona)
            console.print(f"[cyan]Applied persona:[/cyan] {persona}\n")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            import sys
            sys.exit(1)

    # Display configuration summary
    console.print("[bold]Query Pipeline Explanation[/bold]\n")
    console.print(f"[cyan]Query:[/cyan] {query_text}\n")

    # Retrieval configuration
    console.print("[bold]1. Retrieval[/bold]")
    console.print(f"   Method: {config.retrieval_method}")
    console.print(f"   Top-K: {config.top_k} chunks")
    if config.retrieval_method == "hybrid":
        console.print(
            f"   Weights: BM25={config.bm25_weight}, Vector={config.vector_weight}"
        )
    console.print()

    # Query processing
    console.print("[bold]2. Query Processing[/bold]")
    if config.enable_query_decomposition:
        console.print("   ✓ Query decomposition enabled")
    if config.enable_hyde:
        console.print("   ✓ HyDE (Hypothetical Document Embeddings) enabled")
    if config.enable_compression:
        console.print("   ✓ Context compression enabled")
    if not (
        config.enable_query_decomposition
        or config.enable_hyde
        or config.enable_compression
    ):
        console.print("   No advanced query processing")
    console.print()

    # Reranking
    console.print("[bold]3. Reranking[/bold]")
    if config.enable_reranking:
        console.print(f"   ✓ Enabled - rerank to top {config.rerank_to}")
        console.print(f"   Model: {config.rerank_model}")
    else:
        console.print("   Disabled")
    console.print()

    # Generation
    console.print("[bold]4. Generation[/bold]")
    console.print(f"   LLM: {config.llm_model}")
    console.print(f"   Temperature: {config.temperature}")
    console.print(f"   Max tokens: {config.max_tokens}")
    console.print()

    # Confidence
    console.print("[bold]5. Quality Assessment[/bold]")
    console.print(f"   Confidence threshold: {config.confidence_threshold}")
    console.print()

    # Performance expectations
    console.print("[bold]Expected Performance[/bold]")
    if persona == "speed" or config.persona == "speed":
        console.print("   Speed: [green]Very Fast[/green]")
        console.print("   Quality: [yellow]Good[/yellow]")
    elif persona == "accuracy" or config.persona == "accuracy":
        console.print("   Speed: [yellow]Slower[/yellow]")
        console.print("   Quality: [green]Excellent[/green]")
    elif persona == "research" or config.persona == "research":
        console.print("   Speed: [red]Slowest[/red]")
        console.print("   Quality: [green]Comprehensive[/green]")
    elif persona == "quick-answer" or config.persona == "quick-answer":
        console.print("   Speed: [green]Fastest[/green]")
        console.print("   Quality: [yellow]Single answer[/yellow]")
    else:  # balanced
        console.print("   Speed: [green]Fast[/green]")
        console.print("   Quality: [green]Good[/green]")


@explain.command()
def config() -> None:
    """
    Explain current configuration and its sources.

    Shows configuration values and where they come from.
    """
    cfg = RaggedConfig.load()

    console.print("[bold]Current Configuration[/bold]\n")
    console.print(f"[cyan]Active Persona:[/cyan] {cfg.persona}\n")

    console.print("[bold]Retrieval Settings[/bold]")
    console.print(f"  retrieval_method: {cfg.retrieval_method}")
    console.print(f"  top_k: {cfg.top_k}")
    console.print(f"  bm25_weight: {cfg.bm25_weight}")
    console.print(f"  vector_weight: {cfg.vector_weight}")
    console.print()

    console.print("[bold]Advanced Features[/bold]")
    console.print(f"  enable_reranking: {cfg.enable_reranking}")
    console.print(f"  rerank_to: {cfg.rerank_to}")
    console.print(f"  enable_query_decomposition: {cfg.enable_query_decomposition}")
    console.print(f"  enable_hyde: {cfg.enable_hyde}")
    console.print(f"  enable_compression: {cfg.enable_compression}")
    console.print()

    console.print("[bold]Generation Settings[/bold]")
    console.print(f"  llm_model: {cfg.llm_model}")
    console.print(f"  temperature: {cfg.temperature}")
    console.print(f"  max_tokens: {cfg.max_tokens}")
    console.print()

    console.print("[bold]Quality Thresholds[/bold]")
    console.print(f"  confidence_threshold: {cfg.confidence_threshold}")
    console.print()

    console.print("[dim]Configuration loaded from:[/dim]")
    console.print("[dim]  ~/.config/ragged/config.yml (if exists)[/dim]")
    console.print("[dim]  Environment variables (RAGGED_*)[/dim]")
