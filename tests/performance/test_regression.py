"""Performance regression tests for v0.2.9.

Critical path benchmarks to detect performance regressions.
Run with: pytest tests/performance/ -v -m performance
"""

import pytest
from pathlib import Path
from typing import Dict

from src.embeddings.factory import create_embedder, get_embedder, clear_embedder_cache
from src.config.settings import get_settings
from src.utils.benchmarks import Benchmark, BenchmarkResult
from tests.performance.baseline import (
    load_baseline,
    compare_to_baseline,
    get_default_baseline_path,
    BaselineNotFoundError,
)


# Global baseline storage
_baselines: Dict[str, BenchmarkResult] = {}


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks (deselect with '-m \"not performance\"')"
    )


@pytest.fixture(scope="session", autouse=True)
def load_baselines():
    """Load baselines at start of test session."""
    global _baselines

    baseline_path = get_default_baseline_path()

    try:
        _baselines = load_baseline(baseline_path)
        print(f"\n✅ Loaded {len(_baselines)} baselines from {baseline_path}")
    except BaselineNotFoundError:
        print(f"\n⚠️  No baseline found at {baseline_path}")
        print("   Skipping regression checks (will only measure current performance)")
        _baselines = {}

    yield

    # Cleanup
    _baselines.clear()


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test for consistent measurements."""
    # Clear embedder cache
    clear_embedder_cache()

    # Clear settings cache
    from src.config.settings import get_settings
    get_settings.cache_clear()

    yield

    # Cleanup after test
    clear_embedder_cache()


class TestEmbedderPerformance:
    """Embedder performance regression tests."""

    @pytest.mark.performance
    def test_embedder_cold_start(self):
        """Benchmark embedder cold start (no caching)."""
        # Disable caching for true cold start
        settings = get_settings()
        original_flag = settings.feature_flags.enable_embedder_caching
        settings.feature_flags.enable_embedder_caching = False

        try:
            benchmark = Benchmark(
                name="embedder-init-cold",
                warmup_iterations=0,  # No warmup for cold start
                test_iterations=10
            )

            result = benchmark.run(create_embedder)

            # Compare to baseline if available
            if "embedder-init-cold" in _baselines:
                compare_to_baseline(
                    current=result,
                    baseline=_baselines["embedder-init-cold"],
                    threshold=1.05  # Allow 5% regression
                )
            else:
                print(f"\n📊 {result}")

        finally:
            settings.feature_flags.enable_embedder_caching = original_flag

    @pytest.mark.performance
    def test_embedder_warm_start(self):
        """Benchmark embedder warm start (with caching)."""
        settings = get_settings()
        original_flag = settings.feature_flags.enable_embedder_caching
        settings.feature_flags.enable_embedder_caching = True

        try:
            # Prime the cache
            get_embedder()

            benchmark = Benchmark(
                name="embedder-init-warm",
                warmup_iterations=2,
                test_iterations=10
            )

            result = benchmark.run(get_embedder)

            # Compare to baseline
            if "embedder-init-warm" in _baselines:
                compare_to_baseline(
                    current=result,
                    baseline=_baselines["embedder-init-warm"],
                    threshold=1.05
                )
            else:
                print(f"\n📊 {result}")

            # Verify warm start is significantly faster than cold start
            if "embedder-init-cold" in _baselines:
                cold_time = _baselines["embedder-init-cold"].median
                warm_time = result.median
                speedup = cold_time / warm_time
                assert speedup > 2.0, f"Warm start should be >2x faster (got {speedup:.1f}x)"
                print(f"✅ Warm start is {speedup:.1f}x faster than cold start")

        finally:
            settings.feature_flags.enable_embedder_caching = original_flag

    @pytest.mark.performance
    @pytest.mark.slow
    def test_batch_embedding_10(self):
        """Benchmark batch embedding with 10 documents."""
        embedder = get_embedder()
        texts = ["Sample document text here " * 20] * 10  # 10 docs, ~100 words each

        benchmark = Benchmark(
            name="batch-embed-10",
            warmup_iterations=2,
            test_iterations=5
        )

        result = benchmark.run(lambda: embedder.embed_batch(texts))

        if "batch-embed-10" in _baselines:
            compare_to_baseline(result, _baselines["batch-embed-10"], threshold=1.05)
        else:
            print(f"\n📊 {result}")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_batch_embedding_100(self):
        """Benchmark batch embedding with 100 documents."""
        embedder = get_embedder()
        texts = ["Sample document text " * 50] * 100  # 100 docs, ~250 words each

        benchmark = Benchmark(
            name="batch-embed-100",
            warmup_iterations=1,
            test_iterations=3
        )

        result = benchmark.run(lambda: embedder.embed_batch(texts))

        if "batch-embed-100" in _baselines:
            compare_to_baseline(result, _baselines["batch-embed-100"], threshold=1.05)
        else:
            print(f"\n📊 {result}")

    @pytest.mark.performance
    def test_single_embedding(self):
        """Benchmark single text embedding."""
        embedder = get_embedder()
        text = "This is a test document with some sample text content."

        benchmark = Benchmark(
            name="single-embed",
            warmup_iterations=5,
            test_iterations=20
        )

        result = benchmark.run(lambda: embedder.embed_text(text))

        if "single-embed" in _baselines:
            compare_to_baseline(result, _baselines["single-embed"], threshold=1.05)
        else:
            print(f"\n📊 {result}")


class TestQueryPerformance:
    """Query performance regression tests."""

    @pytest.mark.performance
    @pytest.mark.skip(reason="Requires vector store setup - implement in integration tests")
    def test_query_first_time(self):
        """Benchmark first query (cache miss)."""
        # TODO: Implement when vector store test fixtures are ready
        pass

    @pytest.mark.performance
    @pytest.mark.skip(reason="Requires vector store setup - implement in integration tests")
    def test_query_cache_hit(self):
        """Benchmark repeat query (cache hit)."""
        # TODO: Implement when vector store test fixtures are ready
        pass


class TestBatchTuningPerformance:
    """Batch tuning performance regression tests."""

    @pytest.mark.performance
    def test_batch_tuner_suggest_time(self):
        """Benchmark batch size suggestion performance."""
        from src.embeddings.batch_tuner import BatchTuner

        tuner = BatchTuner()
        documents = ["x" * 1000] * 100  # 100 documents

        benchmark = Benchmark(
            name="batch-tuner-suggest",
            warmup_iterations=10,
            test_iterations=100
        )

        result = benchmark.run(
            lambda: tuner.suggest_batch_size(documents, memory_check=False)
        )

        # Batch tuner should be very fast (<1ms per call)
        assert result.mean < 0.001, f"Batch tuner too slow: {result.mean*1000:.2f}ms"

        if "batch-tuner-suggest" in _baselines:
            compare_to_baseline(result, _baselines["batch-tuner-suggest"], threshold=1.05)
        else:
            print(f"\n📊 {result}")


class TestCachingPerformance:
    """Caching performance regression tests."""

    @pytest.mark.performance
    def test_query_cache_lookup(self):
        """Benchmark query cache lookup performance."""
        from src.retrieval.cache import QueryCache

        cache = QueryCache(maxsize=1000)

        # Populate cache
        for i in range(100):
            cache.set(f"query{i}", f"result{i}", collection="test")

        # Benchmark cache hits
        benchmark = Benchmark(
            name="cache-lookup",
            warmup_iterations=100,
            test_iterations=1000
        )

        result = benchmark.run(
            lambda: cache.get("query50", collection="test")
        )

        # Cache lookup should be very fast (<0.1ms)
        assert result.mean < 0.0001, f"Cache lookup too slow: {result.mean*1000:.3f}ms"

        if "cache-lookup" in _baselines:
            compare_to_baseline(result, _baselines["cache-lookup"], threshold=1.05)
        else:
            print(f"\n📊 {result}")


# Utility function to generate baseline
def generate_baseline():
    """
    Generate baseline.json file by running all benchmarks.

    Run with: pytest tests/performance/test_regression.py --generate-baseline
    """
    from tests.performance.baseline import save_baseline
    import sys

    print("\n" + "="*60)
    print("GENERATING PERFORMANCE BASELINE")
    print("="*60 + "\n")

    # Clear any existing baselines
    global _baselines
    _baselines = {}

    # Run all performance tests
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short",
    ])

    # TODO: Collect results and save as baseline
    print("\n⚠️  Baseline generation not yet fully implemented")
    print("   Run individual benchmarks and manually create baseline.json")


if __name__ == "__main__":
    # Allow running this file directly to generate baseline
    import sys
    if "--generate-baseline" in sys.argv:
        generate_baseline()
    else:
        pytest.main([__file__, "-v", "-m", "performance"])
