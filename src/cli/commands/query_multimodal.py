"""Multi-modal query commands for ragged CLI.

v0.5.3: Text, image, and hybrid query modes with interactive REPL.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from PIL import Image

from ragged.cli.common import ProgressType, console
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@click.group(name="query")
def query_group() -> None:
    """Multi-modal query interface.

    \b
    Commands:
        text        - Text-only query with visual boosting
        image       - Image-only visual similarity search
        hybrid      - Combined text + image query
        interactive - Interactive query REPL

    \b
    Examples:
        ragged query text "database schema" --boost-diagrams
        ragged query image architecture.png --num-results 5
        ragged query hybrid "auth flow" diagram.png --text-weight 0.6
    """
    pass


@query_group.command()
@click.argument("query_text")
@click.option(
    "--num-results",
    "-n",
    default=5,
    help="Number of results to retrieve (default: 5)",
)
@click.option(
    "--boost-diagrams",
    is_flag=True,
    help="Boost results containing diagrams",
)
@click.option(
    "--boost-tables",
    is_flag=True,
    help="Boost results containing tables",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--show-metadata",
    is_flag=True,
    help="Show detailed metadata for each result",
)
def text(
    query_text: str,
    num_results: int,
    boost_diagrams: bool,
    boost_tables: bool,
    output_format: str,
    show_metadata: bool,
) -> None:
    """Text-only query with optional visual content boosting.

    \b
    Visual Boosting:
    When --boost-diagrams or --boost-tables is enabled, results containing
    visual content are prioritised even when querying with text alone.

    \b
    Examples:
        ragged query text "database schema"
        ragged query text "network topology" --boost-diagrams
        ragged query text "financial data" --boost-tables --num-results 10
        ragged query text "architecture" --format json > results.json
    """
    from ragged.retrieval.vision_retriever import VisionRetriever

    if output_format == "text":
        console.print(f"[bold blue]Query:[/bold blue] {query_text}")
        if boost_diagrams:
            console.print("[dim]Boosting: diagrams[/dim]")
        if boost_tables:
            console.print("[dim]Boosting: tables[/dim]")
        console.print()

    try:
        retriever = VisionRetriever()

        # Execute text query
        with ProgressType() as progress:
            task = progress.add_task("Searching...", total=100)

            response = retriever.query_text(
                text=query_text,
                n_results=num_results,
                boost_diagrams=boost_diagrams,
                boost_tables=boost_tables,
            )

            progress.update(task, completed=100)

        # Format and display results
        if output_format == "json":
            output = {
                "query": query_text,
                "query_type": response.query_type.value,
                "total_results": response.total_results,
                "execution_time_ms": response.execution_time_ms,
                "results": [
                    {
                        "rank": r.rank,
                        "document_id": r.document_id,
                        "score": r.score,
                        "embedding_type": r.embedding_type,
                        "metadata": r.metadata,
                    }
                    for r in response.results
                ],
            }
            print(json.dumps(output, indent=2))

        else:
            console.print(
                f"[bold]Found {response.total_results} results "
                f"({response.execution_time_ms:.1f}ms):[/bold]"
            )
            console.print()

            for result in response.results:
                # Display result
                console.print(f"[bold cyan][{result.rank}][/bold cyan] {result.document_id}")
                console.print(f"    Score: {result.score:.4f}")
                console.print(f"    Type: {result.embedding_type}")

                # Show metadata if requested
                if show_metadata:
                    console.print("    Metadata:")
                    for key, value in result.metadata.items():
                        if key not in ["document_id", "embedding_type"]:
                            console.print(f"      {key}: {value}")

                console.print()

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e), "query": query_text}))
        else:
            console.print(f"[bold red]✗[/bold red] Query failed: {e}")
        logger.error(f"Text query failed: {e}", exc_info=True)
        sys.exit(1)


@query_group.command()
@click.argument("image_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--num-results",
    "-n",
    default=5,
    help="Number of results to retrieve (default: 5)",
)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "mps", "cpu"], case_sensitive=False),
    default="auto",
    help="Device for vision processing (default: auto)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--show-metadata",
    is_flag=True,
    help="Show detailed metadata for each result",
)
def image(
    image_path: Path,
    num_results: int,
    device: str,
    output_format: str,
    show_metadata: bool,
) -> None:
    """Image-only visual similarity search.

    \b
    Vision Querying:
    Finds documents with visually similar pages using ColPali vision embeddings.
    Requires documents to have been ingested with --vision flag.

    \b
    Examples:
        ragged query image architecture_diagram.png
        ragged query image screenshot.png --num-results 10
        ragged query image sketch.jpg --device cuda:0
        ragged query image chart.png --format json
    """
    from ragged.retrieval.vision_retriever import VisionRetriever

    if output_format == "text":
        console.print(f"[bold blue]Image Query:[/bold blue] {image_path.name}")
        console.print()

    try:
        # Load image
        query_image = Image.open(image_path)

        retriever = VisionRetriever()

        # Execute image query
        with ProgressType() as progress:
            task = progress.add_task("Searching...", total=100)

            response = retriever.query_image(
                image=query_image,
                n_results=num_results,
            )

            progress.update(task, completed=100)

        # Format and display results
        if output_format == "json":
            output = {
                "image_path": str(image_path),
                "query_type": response.query_type.value,
                "total_results": response.total_results,
                "execution_time_ms": response.execution_time_ms,
                "results": [
                    {
                        "rank": r.rank,
                        "document_id": r.document_id,
                        "score": r.score,
                        "embedding_type": r.embedding_type,
                        "metadata": r.metadata,
                    }
                    for r in response.results
                ],
            }
            print(json.dumps(output, indent=2))

        else:
            console.print(
                f"[bold]Found {response.total_results} results "
                f"({response.execution_time_ms:.1f}ms):[/bold]"
            )
            console.print()

            for result in response.results:
                console.print(f"[bold cyan][{result.rank}][/bold cyan] {result.document_id}")
                console.print(f"    Score: {result.score:.4f}")
                console.print(f"    Type: {result.embedding_type}")

                if show_metadata:
                    console.print("    Metadata:")
                    for key, value in result.metadata.items():
                        if key not in ["document_id", "embedding_type"]:
                            console.print(f"      {key}: {value}")

                console.print()

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e), "image_path": str(image_path)}))
        else:
            console.print(f"[bold red]✗[/bold red] Query failed: {e}")
        logger.error(f"Image query failed: {e}", exc_info=True)
        sys.exit(1)


@query_group.command()
@click.argument("query_text")
@click.argument("image_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--num-results",
    "-n",
    default=5,
    help="Number of results to retrieve (default: 5)",
)
@click.option(
    "--text-weight",
    type=float,
    default=0.5,
    help="Weight for text scores (0-1, default: 0.5)",
)
@click.option(
    "--vision-weight",
    type=float,
    default=0.5,
    help="Weight for vision scores (0-1, default: 0.5)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--show-metadata",
    is_flag=True,
    help="Show detailed metadata for each result",
)
def hybrid(
    query_text: str,
    image_path: Path,
    num_results: int,
    text_weight: float,
    vision_weight: float,
    output_format: str,
    show_metadata: bool,
) -> None:
    """Hybrid text + image query with configurable weights.

    \b
    Multi-Modal Fusion:
    Combines text semantic search with visual similarity search using
    Reciprocal Rank Fusion (RRF). Weights control the influence of each modality.

    \b
    Weight Configuration:
    - text-weight=0.7, vision-weight=0.3: Prioritise text matching
    - text-weight=0.3, vision-weight=0.7: Prioritise visual similarity
    - text-weight=0.5, vision-weight=0.5: Equal balance (default)

    \b
    Examples:
        ragged query hybrid "auth flow" diagram.png
        ragged query hybrid "database" schema.png --text-weight 0.6 --vision-weight 0.4
        ragged query hybrid "API design" sketch.jpg --num-results 10
        ragged query hybrid "architecture" design.png --format json
    """
    from ragged.retrieval.vision_retriever import VisionRetriever

    # Validate weights
    if not (0 <= text_weight <= 1):
        console.print("[red]Error: text-weight must be between 0 and 1[/red]")
        sys.exit(1)
    if not (0 <= vision_weight <= 1):
        console.print("[red]Error: vision-weight must be between 0 and 1[/red]")
        sys.exit(1)

    if output_format == "text":
        console.print(f"[bold blue]Hybrid Query:[/bold blue]")
        console.print(f"  Text: {query_text}")
        console.print(f"  Image: {image_path.name}")
        console.print(f"  Weights: text={text_weight:.2f}, vision={vision_weight:.2f}")
        console.print()

    try:
        # Load image
        query_image = Image.open(image_path)

        retriever = VisionRetriever()

        # Execute hybrid query
        with ProgressType() as progress:
            task = progress.add_task("Searching...", total=100)

            response = retriever.query_hybrid(
                text=query_text,
                image=query_image,
                n_results=num_results,
                text_weight=text_weight,
                vision_weight=vision_weight,
            )

            progress.update(task, completed=100)

        # Format and display results
        if output_format == "json":
            output = {
                "text": query_text,
                "image_path": str(image_path),
                "text_weight": text_weight,
                "vision_weight": vision_weight,
                "query_type": response.query_type.value,
                "total_results": response.total_results,
                "execution_time_ms": response.execution_time_ms,
                "results": [
                    {
                        "rank": r.rank,
                        "document_id": r.document_id,
                        "score": r.score,
                        "embedding_type": r.embedding_type,
                        "metadata": r.metadata,
                    }
                    for r in response.results
                ],
            }
            print(json.dumps(output, indent=2))

        else:
            console.print(
                f"[bold]Found {response.total_results} results "
                f"({response.execution_time_ms:.1f}ms):[/bold]"
            )
            console.print()

            for result in response.results:
                console.print(f"[bold cyan][{result.rank}][/bold cyan] {result.document_id}")
                console.print(f"    Score: {result.score:.4f}")
                console.print(f"    Type: {result.embedding_type}")

                if show_metadata:
                    console.print("    Metadata:")
                    for key, value in result.metadata.items():
                        if key not in ["document_id", "embedding_type"]:
                            console.print(f"      {key}: {value}")

                console.print()

    except Exception as e:
        if output_format == "json":
            print(
                json.dumps(
                    {
                        "error": str(e),
                        "text": query_text,
                        "image_path": str(image_path),
                    }
                )
            )
        else:
            console.print(f"[bold red]✗[/bold red] Query failed: {e}")
        logger.error(f"Hybrid query failed: {e}", exc_info=True)
        sys.exit(1)


@query_group.command()
@click.option(
    "--default-mode",
    type=click.Choice(["text", "image", "hybrid"], case_sensitive=False),
    default="text",
    help="Default query mode (default: text)",
)
def interactive(default_mode: str) -> None:
    """Interactive query REPL.

    \b
    Interactive Mode:
    Provides a REPL interface for exploring documents with text, image, and
    hybrid queries. Switch modes, adjust weights, and view metadata interactively.

    \b
    Commands:
        :mode <text|image|hybrid>  - Switch query mode
        :weights <text> <vision>   - Set hybrid weights
        :results <n>               - Set number of results
        :metadata on|off           - Toggle metadata display
        :quit or :q                - Exit REPL

    \b
    Examples:
        ragged query interactive
        ragged query interactive --default-mode hybrid
    """
    from ragged.retrieval.vision_retriever import VisionRetriever

    console.print("[bold blue]Interactive Query Mode[/bold blue]")
    console.print("[dim]Type ':help' for commands, ':quit' to exit[/dim]")
    console.print()

    # REPL state
    mode = default_mode
    num_results = 5
    text_weight = 0.5
    vision_weight = 0.5
    show_metadata = False

    retriever = VisionRetriever()

    try:
        while True:
            # Show prompt
            console.print(f"[cyan]{mode}>[/cyan] ", end="")
            user_input = input().strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith(":"):
                cmd_parts = user_input[1:].split()
                cmd = cmd_parts[0].lower()

                if cmd in ["quit", "q", "exit"]:
                    console.print("[dim]Goodbye![/dim]")
                    break

                elif cmd == "help":
                    console.print("[bold]Commands:[/bold]")
                    console.print("  :mode <text|image|hybrid>  - Switch query mode")
                    console.print("  :weights <text> <vision>   - Set hybrid weights")
                    console.print("  :results <n>               - Set number of results")
                    console.print("  :metadata <on|off>         - Toggle metadata display")
                    console.print("  :quit                      - Exit")
                    console.print()

                elif cmd == "mode":
                    if len(cmd_parts) < 2:
                        console.print("[yellow]Usage: :mode <text|image|hybrid>[/yellow]")
                    elif cmd_parts[1] in ["text", "image", "hybrid"]:
                        mode = cmd_parts[1]
                        console.print(f"[green]Mode set to: {mode}[/green]")
                    else:
                        console.print("[yellow]Invalid mode. Choose: text, image, hybrid[/yellow]")

                elif cmd == "weights":
                    if len(cmd_parts) < 3:
                        console.print("[yellow]Usage: :weights <text> <vision>[/yellow]")
                    else:
                        try:
                            text_weight = float(cmd_parts[1])
                            vision_weight = float(cmd_parts[2])
                            console.print(
                                f"[green]Weights set: text={text_weight:.2f}, "
                                f"vision={vision_weight:.2f}[/green]"
                            )
                        except ValueError:
                            console.print("[yellow]Weights must be numbers[/yellow]")

                elif cmd == "results":
                    if len(cmd_parts) < 2:
                        console.print("[yellow]Usage: :results <n>[/yellow]")
                    else:
                        try:
                            num_results = int(cmd_parts[1])
                            console.print(f"[green]Results set to: {num_results}[/green]")
                        except ValueError:
                            console.print("[yellow]Results must be a number[/yellow]")

                elif cmd == "metadata":
                    if len(cmd_parts) < 2:
                        console.print(
                            f"[dim]Metadata display: {'on' if show_metadata else 'off'}[/dim]"
                        )
                    elif cmd_parts[1].lower() in ["on", "true", "yes"]:
                        show_metadata = True
                        console.print("[green]Metadata display: on[/green]")
                    elif cmd_parts[1].lower() in ["off", "false", "no"]:
                        show_metadata = False
                        console.print("[green]Metadata display: off[/green]")

                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                    console.print("[dim]Type :help for available commands[/dim]")

                console.print()
                continue

            # Execute query based on mode
            try:
                if mode == "text":
                    response = retriever.query_text(text=user_input, n_results=num_results)

                elif mode == "image":
                    # user_input is image path
                    image_path = Path(user_input)
                    if not image_path.exists():
                        console.print(f"[yellow]Image not found: {user_input}[/yellow]")
                        console.print()
                        continue

                    query_image = Image.open(image_path)
                    response = retriever.query_image(image=query_image, n_results=num_results)

                elif mode == "hybrid":
                    # Parse "text | image_path"
                    if "|" not in user_input:
                        console.print(
                            "[yellow]Hybrid mode requires: <text> | <image_path>[/yellow]"
                        )
                        console.print()
                        continue

                    text_part, image_part = user_input.split("|", 1)
                    text_query = text_part.strip()
                    image_path = Path(image_part.strip())

                    if not image_path.exists():
                        console.print(f"[yellow]Image not found: {image_part}[/yellow]")
                        console.print()
                        continue

                    query_image = Image.open(image_path)
                    response = retriever.query_hybrid(
                        text=text_query,
                        image=query_image,
                        n_results=num_results,
                        text_weight=text_weight,
                        vision_weight=vision_weight,
                    )

                else:
                    console.print(f"[red]Unknown mode: {mode}[/red]")
                    console.print()
                    continue

                # Display results
                console.print(
                    f"[dim]Found {response.total_results} results "
                    f"({response.execution_time_ms:.1f}ms)[/dim]"
                )

                for result in response.results:
                    console.print(
                        f"  [{result.rank}] {result.document_id} (score: {result.score:.4f})"
                    )

                    if show_metadata:
                        for key, value in result.metadata.items():
                            if key not in ["document_id", "embedding_type"]:
                                console.print(f"      {key}: {value}")

                console.print()

            except Exception as e:
                console.print(f"[red]Query failed: {e}[/red]")
                logger.error(f"Interactive query failed: {e}", exc_info=True)
                console.print()

    except KeyboardInterrupt:
        console.print()
        console.print("[dim]Goodbye![/dim]")
    except EOFError:
        console.print()
        console.print("[dim]Goodbye![/dim]")
