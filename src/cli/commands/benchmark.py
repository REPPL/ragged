"""Benchmark CLI commands for performance profiling.

v0.2.9: Performance profiling tools integration.
"""

import time
import tracemalloc
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.cli.common import console
from src.utils.benchmarks import Benchmark, time_it
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def benchmark():
    """Performance benchmarking and profiling commands.

    Tools for measuring system performance, identifying bottlenecks,
    and tracking performance over time.

    Examples:
        ragged benchmark embedding-init --runs 10
        ragged benchmark batch-embed --size 100
        ragged benchmark query --count 20
        ragged benchmark memory add document.pdf
    """
    pass


@benchmark.command("embedding-init")
@click.option("--runs", "-n", default=10, help="Number of benchmark runs")
@click.option("--warmup", "-w", default=3, help="Number of warmup runs")
@click.option("--model", "-m", default=None, help="Specific model to benchmark")
def bench_embedding_init(runs: int, warmup: int, model: Optional[str]):
    """Benchmark embedder initialization time.

    Measures cold start performance of embedding model loading.

    Examples:
        ragged benchmark embedding-init
        ragged benchmark embedding-init --runs 20 --warmup 5
        ragged benchmark embedding-init --model all-MiniLM-L6-v2
    """
    from src.embeddings.factory import get_embedder, _reset_embedder_cache

    console.print(f"\n[bold cyan]Benchmarking Embedder Initialization[/bold cyan]")
    console.print(f"Runs: {runs}, Warmup: {warmup}")
    if model:
        console.print(f"Model: {model}")
    console.print()

    def create_embedder():
        """Create embedder (cold start)."""
        _reset_embedder_cache()  # Force cold start
        embedder = get_embedder(model_name=model)
        return embedder

    bench = Benchmark(
        name="embedding-init",
        warmup_iterations=warmup,
        test_iterations=runs
    )

    result = bench.run(create_embedder)

    # Display results
    table = Table(title="Embedder Initialization Performance")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Mean", f"{result.mean*1000:.2f} ms")
    table.add_row("Median", f"{result.median*1000:.2f} ms")
    table.add_row("Std Dev", f"{result.std_dev*1000:.2f} ms")
    table.add_row("Min", f"{result.min_time*1000:.2f} ms")
    table.add_row("Max", f"{result.max_time*1000:.2f} ms")
    table.add_row("Iterations", str(result.iterations))

    console.print(table)
    console.print()


@benchmark.command("batch-embed")
@click.option("--size", "-s", default=100, help="Batch size to test")
@click.option("--runs", "-n", default=5, help="Number of benchmark runs")
@click.option("--warmup", "-w", default=2, help="Number of warmup runs")
def bench_batch_embed(size: int, runs: int, warmup: int):
    """Benchmark batch embedding performance.

    Measures throughput of embedding generation for different batch sizes.

    Examples:
        ragged benchmark batch-embed --size 50
        ragged benchmark batch-embed --size 200 --runs 10
    """
    from src.embeddings.factory import get_embedder

    console.print(f"\n[bold cyan]Benchmarking Batch Embedding[/bold cyan]")
    console.print(f"Batch size: {size}, Runs: {runs}, Warmup: {warmup}")
    console.print()

    # Create test data
    test_texts = [f"Sample text number {i} for embedding benchmark" for i in range(size)]

    # Get embedder
    embedder = get_embedder()

    def embed_batch():
        """Embed batch of texts."""
        return embedder.embed_batch(test_texts)

    bench = Benchmark(
        name=f"batch-embed-{size}",
        warmup_iterations=warmup,
        test_iterations=runs
    )

    result = bench.run(embed_batch, metadata={"batch_size": size})

    # Calculate throughput
    throughput = size / result.mean

    # Display results
    table = Table(title=f"Batch Embedding Performance (size={size})")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Mean", f"{result.mean*1000:.2f} ms")
    table.add_row("Median", f"{result.median*1000:.2f} ms")
    table.add_row("Throughput", f"{throughput:.1f} texts/sec")
    table.add_row("Per-text", f"{(result.mean/size)*1000:.2f} ms/text")
    table.add_row("Iterations", str(result.iterations))

    console.print(table)
    console.print()


@benchmark.command("query")
@click.option("--count", "-c", default=20, help="Number of queries to benchmark")
@click.option("--collection", "-col", default=None, help="Collection to query")
def bench_query(count: int, collection: Optional[str]):
    """Benchmark query performance.

    Measures retrieval latency for typical queries.

    Examples:
        ragged benchmark query --count 50
        ragged benchmark query --collection my-docs
    """
    from src.retrieval.hybrid import HybridRetriever

    console.print(f"\n[bold cyan]Benchmarking Query Performance[/bold cyan]")
    console.print(f"Queries: {count}")
    if collection:
        console.print(f"Collection: {collection}")
    console.print()

    retriever = HybridRetriever(collection_name=collection)

    # Test queries
    test_queries = [
        "What is machine learning?",
        "How does Python work?",
        "Explain neural networks",
        "What is RAG?",
        "Define embeddings",
    ] * (count // 5 + 1)
    test_queries = test_queries[:count]

    timings = []

    console.print("[dim]Running queries...[/dim]")
    for i, query in enumerate(test_queries, 1):
        with time_it(f"query-{i}") as timer:
            retriever.retrieve(query, k=5)
        timings.append(timer.elapsed)

    # Calculate statistics
    import statistics
    mean = statistics.mean(timings)
    median = statistics.median(timings)
    std_dev = statistics.stdev(timings) if len(timings) > 1 else 0
    min_time = min(timings)
    max_time = max(timings)

    # Display results
    table = Table(title=f"Query Performance ({count} queries)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Mean", f"{mean*1000:.2f} ms")
    table.add_row("Median", f"{median*1000:.2f} ms")
    table.add_row("Std Dev", f"{std_dev*1000:.2f} ms")
    table.add_row("Min", f"{min_time*1000:.2f} ms")
    table.add_row("Max", f"{max_time*1000:.2f} ms")
    table.add_row("Queries/sec", f"{1/mean:.1f}")

    console.print(table)
    console.print()


@benchmark.command("memory")
@click.argument("operation", type=click.Choice(["add", "query", "embed"]))
@click.argument("target", required=False)
@click.option("--detailed", "-d", is_flag=True, help="Show detailed memory breakdown")
def profile_memory(operation: str, target: Optional[str], detailed: bool):
    """Profile memory usage of operations.

    Measures memory allocation and peak usage for different operations.

    OPERATION is one of: add, query, embed
    TARGET is the file/query/text to process

    Examples:
        ragged benchmark memory add document.pdf
        ragged benchmark memory query "What is RAG?"
        ragged benchmark memory embed --detailed
    """
    console.print(f"\n[bold cyan]Memory Profiling: {operation}[/bold cyan]")
    if target:
        console.print(f"Target: {target}")
    console.print()

    # Start memory tracking
    tracemalloc.start()

    try:
        if operation == "add":
            if not target:
                console.print("[red]Error: TARGET file path required for 'add' operation[/red]")
                return

            from src.ingestion.pipeline import process_document

            console.print(f"[dim]Processing document: {target}[/dim]")
            snapshot_before = tracemalloc.take_snapshot()

            # Process document
            process_document(Path(target))

            snapshot_after = tracemalloc.take_snapshot()

        elif operation == "query":
            if not target:
                target = "What is machine learning?"

            from src.retrieval.hybrid import HybridRetriever

            console.print(f"[dim]Executing query: {target}[/dim]")
            snapshot_before = tracemalloc.take_snapshot()

            retriever = HybridRetriever()
            retriever.retrieve(target, k=10)

            snapshot_after = tracemalloc.take_snapshot()

        elif operation == "embed":
            from src.embeddings.factory import get_embedder

            text = target or "Sample text for embedding" * 100
            console.print(f"[dim]Embedding text ({len(text)} chars)[/dim]")
            snapshot_before = tracemalloc.take_snapshot()

            embedder = get_embedder()
            embedder.embed(text)

            snapshot_after = tracemalloc.take_snapshot()

        # Calculate memory usage
        stats = snapshot_after.compare_to(snapshot_before, 'lineno')

        # Get current and peak memory
        current, peak = tracemalloc.get_traced_memory()

        # Display results
        panel_content = (
            f"[bold]Current Memory:[/bold] {current / 1024 / 1024:.2f} MB\n"
            f"[bold]Peak Memory:[/bold] {peak / 1024 / 1024:.2f} MB\n"
            f"[bold]Allocated:[/bold] {sum(stat.size_diff for stat in stats) / 1024 / 1024:.2f} MB"
        )

        console.print(Panel(panel_content, title="Memory Usage", border_style="green"))

        if detailed and stats:
            console.print("\n[bold]Top Memory Allocations:[/bold]")
            table = Table()
            table.add_column("Location", style="cyan", width=50)
            table.add_column("Size", style="yellow", justify="right")
            table.add_column("Count", style="green", justify="right")

            for stat in stats[:10]:
                table.add_row(
                    f"{stat.traceback.format()[0][:50]}",
                    f"{stat.size_diff / 1024:.1f} KB",
                    f"{stat.count_diff:+d}"
                )

            console.print(table)

    finally:
        tracemalloc.stop()

    console.print()


@benchmark.command("all")
@click.option("--quick", "-q", is_flag=True, help="Quick benchmark (fewer runs)")
def bench_all(quick: bool):
    """Run all benchmarks and generate report.

    Comprehensive performance test suite covering all major operations.

    Examples:
        ragged benchmark all
        ragged benchmark all --quick
    """
    from src.embeddings.factory import get_embedder, _reset_embedder_cache
    from src.retrieval.hybrid import HybridRetriever

    runs = 5 if quick else 10
    warmup = 1 if quick else 3

    console.print("\n[bold cyan]Running Comprehensive Benchmark Suite[/bold cyan]")
    console.print(f"Mode: {'Quick' if quick else 'Standard'}")
    console.print()

    results = []

    # 1. Embedder init
    console.print("[bold]1/5[/bold] Benchmarking embedder initialization...")
    def create_embedder():
        _reset_embedder_cache()
        return get_embedder()

    bench1 = Benchmark("embedding-init", warmup, runs)
    result1 = bench1.run(create_embedder)
    results.append(("Embedder Init", result1.mean))
    console.print(f"  ✓ Mean: {result1.mean*1000:.2f} ms")

    # 2. Batch embedding
    console.print("[bold]2/5[/bold] Benchmarking batch embedding...")
    embedder = get_embedder()
    test_texts = [f"Sample text {i}" for i in range(50)]

    bench2 = Benchmark("batch-embed", warmup, runs)
    result2 = bench2.run(embedder.embed_batch, test_texts)
    results.append(("Batch Embed (50)", result2.mean))
    console.print(f"  ✓ Mean: {result2.mean*1000:.2f} ms")

    # 3. Single query
    console.print("[bold]3/5[/bold] Benchmarking single query...")
    retriever = HybridRetriever()

    bench3 = Benchmark("query", warmup, runs)
    result3 = bench3.run(retriever.retrieve, "What is machine learning?", k=5)
    results.append(("Query", result3.mean))
    console.print(f"  ✓ Mean: {result3.mean*1000:.2f} ms")

    # 4. Document chunking
    console.print("[bold]4/5[/bold] Benchmarking document chunking...")
    from src.chunking.orchestrator import chunk_document
    from src.ingestion.models import Document, DocumentMetadata

    test_doc = Document(
        document_id="test",
        content="This is test content. " * 100,
        metadata=DocumentMetadata(file_path=Path("test.txt"))
    )

    bench4 = Benchmark("chunking", warmup, runs)
    result4 = bench4.run(chunk_document, test_doc)
    results.append(("Chunking", result4.mean))
    console.print(f"  ✓ Mean: {result4.mean*1000:.2f} ms")

    # 5. Cache performance
    console.print("[bold]5/5[/bold] Benchmarking cache hit performance...")
    # Query twice - second should be cached
    retriever.retrieve("cached query test", k=5)

    bench5 = Benchmark("cache-hit", warmup, runs)
    result5 = bench5.run(retriever.retrieve, "cached query test", k=5)
    results.append(("Cache Hit", result5.mean))
    console.print(f"  ✓ Mean: {result5.mean*1000:.2f} ms")

    # Display summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]Benchmark Summary[/bold cyan]")
    console.print("="*60)

    table = Table()
    table.add_column("Operation", style="cyan")
    table.add_column("Mean Time", style="green", justify="right")
    table.add_column("Performance", style="yellow")

    for name, mean in results:
        # Color code based on time
        if mean < 0.1:
            perf = "[green]Excellent[/green]"
        elif mean < 0.5:
            perf = "[yellow]Good[/yellow]"
        elif mean < 1.0:
            perf = "[yellow]Acceptable[/yellow]"
        else:
            perf = "[red]Needs Optimization[/red]"

        table.add_row(name, f"{mean*1000:.2f} ms", perf)

    console.print(table)
    console.print()
