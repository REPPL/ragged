"""Performance regression tests for critical paths.

v0.2.9: Automated benchmarking to detect >5% performance degradation.
"""

import pytest
from pathlib import Path

from src.utils.benchmarks import Benchmark
from src.embeddings.factory import create_embedder, get_embedder
from tests.performance.baseline import BaselineManager, BenchmarkResult


# Initialize baseline manager
baseline_manager = BaselineManager()


def benchmark_to_result(benchmark_result) -> BenchmarkResult:
    """Convert Benchmark result to BenchmarkResult."""
    return BenchmarkResult(
        mean=benchmark_result.mean,
        median=benchmark_result.median,
        std_dev=benchmark_result.std_dev,
        min=benchmark_result.min,
        max=benchmark_result.max,
        iterations=benchmark_result.iterations
    )


@pytest.mark.performance
@pytest.mark.slow
def test_embedder_init_cold():
    """Benchmark embedder cold start initialization.
    
    Target: <0.5s in v0.2.9 (was ~2-3s in v0.2.8)
    """
    benchmark = Benchmark(
        name="embedder-init-cold",
        warmup_iterations=0,  # No warmup for cold start
        test_iterations=10
    )
    
    result = benchmark.run(create_embedder)
    current = benchmark_to_result(result)
    
    # Compare against baseline (5% threshold)
    passed = baseline_manager.compare(
        "embedder-init-cold",
        current,
        threshold=0.05
    )
    
    assert passed, (
        f"Performance regression detected in embedder-init-cold: "
        f"{current.mean:.3f}s (>5% slower than baseline)"
    )


@pytest.mark.performance
def test_embedder_init_warm():
    """Benchmark embedder warm start (cached).
    
    Target: <0.1s in v0.2.9 with caching
    """
    # Warm up cache
    _ = get_embedder()
    
    benchmark = Benchmark(
        name="embedder-init-warm",
        warmup_iterations=2,
        test_iterations=20
    )
    
    result = benchmark.run(get_embedder)
    current = benchmark_to_result(result)
    
    passed = baseline_manager.compare(
        "embedder-init-warm",
        current,
        threshold=0.05
    )
    
    assert passed, (
        f"Performance regression in embedder-init-warm: {current.mean:.3f}s"
    )


@pytest.mark.performance
def test_batch_embedding_10():
    """Benchmark small batch embedding (10 documents).
    
    Target: <2s for 10 documents
    """
    embedder = get_embedder()
    texts = ["Sample document with some content. " * 20] * 10
    
    benchmark = Benchmark(
        name="batch-embed-10",
        warmup_iterations=2,
        test_iterations=5
    )
    
    result = benchmark.run(lambda: embedder.embed_batch(texts))
    current = benchmark_to_result(result)
    
    passed = baseline_manager.compare(
        "batch-embed-10",
        current,
        threshold=0.05
    )
    
    assert passed, f"Performance regression in batch-embed-10: {current.mean:.3f}s"


@pytest.mark.performance
@pytest.mark.slow
def test_batch_embedding_100():
    """Benchmark medium batch embedding (100 documents).
    
    Target: <10s for 100 documents
    """
    embedder = get_embedder()
    texts = ["Sample document with some content. " * 20] * 100
    
    benchmark = Benchmark(
        name="batch-embed-100",
        warmup_iterations=1,
        test_iterations=3
    )
    
    result = benchmark.run(lambda: embedder.embed_batch(texts))
    current = benchmark_to_result(result)
    
    passed = baseline_manager.compare(
        "batch-embed-100",
        current,
        threshold=0.05
    )
    
    assert passed, f"Performance regression in batch-embed-100: {current.mean:.3f}s"


@pytest.mark.performance
def test_single_embedding():
    """Benchmark single document embedding.
    
    Target: <0.2s for single document
    """
    embedder = get_embedder()
    text = "Sample document with some content. " * 20
    
    benchmark = Benchmark(
        name="single-embed",
        warmup_iterations=5,
        test_iterations=20
    )
    
    result = benchmark.run(lambda: embedder.embed(text))
    current = benchmark_to_result(result)
    
    passed = baseline_manager.compare(
        "single-embed",
        current,
        threshold=0.05
    )
    
    assert passed, f"Performance regression in single-embed: {current.mean:.3f}s"


@pytest.mark.performance
def test_query_embedding():
    """Benchmark query embedding (typically shorter than documents).
    
    Target: <0.1s for query embedding
    """
    embedder = get_embedder()
    query = "What is machine learning?"
    
    benchmark = Benchmark(
        name="query-embed",
        warmup_iterations=5,
        test_iterations=30
    )
    
    result = benchmark.run(lambda: embedder.embed(query))
    current = benchmark_to_result(result)
    
    passed = baseline_manager.compare(
        "query-embed",
        current,
        threshold=0.05
    )
    
    assert passed, f"Performance regression in query-embed: {current.mean:.3f}s"


@pytest.mark.performance
def test_hash_computation():
    """Benchmark content hashing performance.
    
    Target: <0.001s for typical document
    """
    from src.utils.hashing import hash_content
    
    content = "Sample document content. " * 100  # ~2.5KB
    
    benchmark = Benchmark(
        name="hash-content",
        warmup_iterations=10,
        test_iterations=100
    )
    
    result = benchmark.run(lambda: hash_content(content))
    current = benchmark_to_result(result)
    
    passed = baseline_manager.compare(
        "hash-content",
        current,
        threshold=0.05
    )
    
    assert passed, f"Performance regression in hash-content: {current.mean:.3f}s"


# Mark all tests in this module as performance tests
pytestmark = pytest.mark.performance
