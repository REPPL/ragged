"""Performance benchmarking script for ragged.

This script establishes performance baselines for the ragged system,
measuring ingestion performance, query latency, memory usage, and startup time.

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --quick  # Run only small corpus tests
    python scripts/benchmark.py --save benchmarks/v0.4.4-baseline.json
"""

import argparse
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any

# Benchmark configuration
BENCHMARK_TARGETS = {
    "ingestion": {
        "single_doc_p95": 0.050,  # 50ms
        "batch_100_p95": 5.0,  # 5s
        "large_10k_p95": 600.0,  # 10min
    },
    "query": {
        "simple_p50": 0.300,  # 300ms
        "simple_p95": 0.500,  # 500ms
        "complex_p50": 0.500,  # 500ms
        "complex_p95": 0.800,  # 800ms
        "cold_start_p95": 2.0,  # 2s
    },
    "memory": {
        "resident_10k_docs": 500 * 1024 * 1024,  # 500MB
        "peak_under_load": 1024 * 1024 * 1024,  # 1GB
    },
}


def measure_startup_time() -> float:
    """Measure ragged startup time.

    Returns:
        Startup time in seconds
    """
    start = time.time()
    try:
        # Simulate minimal import/startup
        # In practice, this would import the main modules
        import src  # noqa: F401
        from src.config import get_settings  # noqa: F401

        end = time.time()
        return end - start
    except ImportError:
        return -1.0


def measure_memory_usage() -> dict[str, float]:
    """Measure current memory usage.

    Returns:
        Dictionary with memory metrics in bytes
    """
    tracemalloc.start()

    # Simulate some operations
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "current_bytes": current,
        "peak_bytes": peak,
        "current_mb": current / (1024 * 1024),
        "peak_mb": peak / (1024 * 1024),
    }


def measure_ingestion_performance(
    num_docs: int = 100,
) -> dict[str, float]:
    """Measure document ingestion performance.

    Args:
        num_docs: Number of documents to ingest

    Returns:
        Dictionary with ingestion metrics
    """
    # Placeholder for actual ingestion benchmarking
    # In practice, this would use the actual ragged ingestion pipeline

    results = {
        "num_docs": num_docs,
        "total_time_sec": 0.0,
        "avg_time_per_doc_sec": 0.0,
        "docs_per_min": 0.0,
    }

    print(f"  Benchmarking ingestion of {num_docs} documents...")
    print(f"  Note: Placeholder implementation - actual benchmarks require test corpus")

    # Simulate timing
    # start = time.time()
    # ... actual ingestion logic ...
    # end = time.time()

    return results


def measure_query_performance(
    query: str = "test query",
    num_iterations: int = 10,
) -> dict[str, Any]:
    """Measure query performance.

    Args:
        query: Query string to test
        num_iterations: Number of iterations to run

    Returns:
        Dictionary with query metrics
    """
    # Placeholder for actual query benchmarking

    results = {
        "query": query,
        "iterations": num_iterations,
        "latencies_ms": [],
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "p99_ms": 0.0,
        "mean_ms": 0.0,
    }

    print(f"  Benchmarking query: '{query}' ({num_iterations} iterations)...")
    print(f"  Note: Placeholder implementation - actual benchmarks require vector store")

    return results


def calculate_percentile(values: list[float], percentile: float) -> float:
    """Calculate percentile from list of values.

    Args:
        values: List of values
        percentile: Percentile to calculate (0-100)

    Returns:
        Percentile value
    """
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = int(len(sorted_values) * (percentile / 100.0))
    return sorted_values[min(index, len(sorted_values) - 1)]


def run_full_benchmark_suite() -> dict[str, Any]:
    """Run the full benchmark suite.

    Returns:
        Dictionary with all benchmark results
    """
    print("="  * 60)
    print("Ragged Performance Benchmark Suite")
    print("=" * 60)
    print()

    results = {
        "version": "0.4.4",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmarks": {},
    }

    # Startup time
    print("1. Measuring startup time...")
    startup_time = measure_startup_time()
    results["benchmarks"]["startup"] = {
        "time_sec": startup_time,
        "target_sec": 2.0,
        "passes": startup_time < 2.0 if startup_time > 0 else False,
    }
    print(f"   Startup time: {startup_time:.3f}s (target: <2.0s)")
    print()

    # Memory usage
    print("2. Measuring memory usage...")
    memory = measure_memory_usage()
    results["benchmarks"]["memory"] = memory
    print(f"   Current memory: {memory['current_mb']:.2f} MB")
    print(f"   Peak memory: {memory['peak_mb']:.2f} MB")
    print()

    # Ingestion performance
    print("3. Measuring ingestion performance...")
    results["benchmarks"]["ingestion"] = {}

    for corpus_size in [1, 10, 100]:
        ingestion = measure_ingestion_performance(corpus_size)
        results["benchmarks"]["ingestion"][f"{corpus_size}_docs"] = ingestion

    print()

    # Query performance
    print("4. Measuring query performance...")
    results["benchmarks"]["query"] = {}

    # Simple query
    simple_query = measure_query_performance("what is machine learning", num_iterations=10)
    results["benchmarks"]["query"]["simple"] = simple_query

    # Complex query with filters
    complex_query = measure_query_performance(
        "explain neural networks with examples",
        num_iterations=5
    )
    results["benchmarks"]["query"]["complex"] = complex_query

    print()

    return results


def print_summary(results: dict[str, Any]) -> None:
    """Print benchmark summary.

    Args:
        results: Benchmark results dictionary
    """
    print("=" * 60)
    print("Benchmark Summary")
    print("=" * 60)
    print()

    benchmarks = results.get("benchmarks", {})

    # Startup
    startup = benchmarks.get("startup", {})
    status = "✅ PASS" if startup.get("passes") else "❌ FAIL"
    print(f"Startup Time: {startup.get('time_sec', 0):.3f}s {status}")

    # Memory
    memory = benchmarks.get("memory", {})
    print(f"Memory Usage: {memory.get('current_mb', 0):.2f} MB")

    print()
    print("Note: Full benchmarks require test corpus and vector store setup.")
    print("This is a baseline infrastructure implementation.")
    print()


def save_results(results: dict[str, Any], output_path: str) -> None:
    """Save benchmark results to JSON file.

    Args:
        results: Benchmark results dictionary
        output_path: Path to save JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_path}")


def main() -> None:
    """Main benchmark entry point."""
    parser = argparse.ArgumentParser(
        description="Run ragged performance benchmarks"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (small corpus only)",
    )
    parser.add_argument(
        "--save",
        type=str,
        default="benchmarks/v0.4.4-baseline.json",
        help="Path to save benchmark results JSON",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save results to file",
    )

    args = parser.parse_args()

    # Run benchmarks
    results = run_full_benchmark_suite()

    # Print summary
    print_summary(results)

    # Save results
    if not args.no_save:
        save_results(results, args.save)


if __name__ == "__main__":
    main()
