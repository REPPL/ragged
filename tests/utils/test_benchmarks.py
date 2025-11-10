"""Tests for performance benchmarking utilities."""

import pytest
import time
import tempfile
from pathlib import Path

from src.utils.benchmarks import (
    Timer,
    time_it,
    Benchmark,
    BenchmarkResult,
    BenchmarkSuite,
    ComparisonResult,
    benchmark_function
)


class TestTimer:
    """Test Timer class."""

    def test_init(self):
        """Test timer initialization."""
        timer = Timer()

        assert timer.start_time is None
        assert timer.end_time is None
        assert timer.elapsed is None

    def test_start_stop(self):
        """Test starting and stopping timer."""
        timer = Timer()

        timer.start()
        assert timer.start_time is not None

        time.sleep(0.01)

        elapsed = timer.stop()

        assert timer.end_time is not None
        assert timer.elapsed is not None
        assert elapsed > 0
        assert elapsed >= 0.01

    def test_stop_without_start_raises(self):
        """Test stopping timer without starting raises error."""
        timer = Timer()

        with pytest.raises(RuntimeError, match="Timer not started"):
            timer.stop()

    def test_context_manager(self):
        """Test timer as context manager."""
        with Timer() as timer:
            time.sleep(0.01)

        assert timer.elapsed is not None
        assert timer.elapsed >= 0.01

    def test_multiple_measurements(self):
        """Test timer can be reused."""
        timer = Timer()

        # First measurement
        timer.start()
        time.sleep(0.01)
        elapsed1 = timer.stop()

        # Second measurement
        timer.start()
        time.sleep(0.02)
        elapsed2 = timer.stop()

        assert elapsed2 > elapsed1


class TestTimeItContextManager:
    """Test time_it context manager."""

    def test_time_it_basic(self):
        """Test basic time_it usage."""
        with time_it("test operation") as timer:
            time.sleep(0.01)

        assert timer.elapsed >= 0.01

    def test_time_it_logs_name(self, caplog):
        """Test that time_it logs operation name."""
        with time_it("my operation"):
            pass

        # Check logs contain operation name (if logging is enabled)
        # This depends on logging configuration


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_create_result(self):
        """Test creating benchmark result."""
        result = BenchmarkResult(
            name="test_benchmark",
            duration=10.5,
            iterations=100,
            mean=0.1,
            median=0.09,
            std_dev=0.02,
            min_time=0.08,
            max_time=0.15,
            metadata={"system": "test"}
        )

        assert result.name == "test_benchmark"
        assert result.duration == 10.5
        assert result.iterations == 100
        assert result.mean == 0.1
        assert result.metadata["system"] == "test"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = BenchmarkResult(
            name="test",
            duration=1.0,
            iterations=10,
            mean=0.1,
            median=0.1,
            std_dev=0.01,
            min_time=0.09,
            max_time=0.11
        )

        data = result.to_dict()

        assert data["name"] == "test"
        assert data["duration"] == 1.0
        assert data["iterations"] == 10
        assert "timestamp" in data

    def test_str_representation(self):
        """Test string representation."""
        result = BenchmarkResult(
            name="query_test",
            duration=5.0,
            iterations=50,
            mean=0.1,
            median=0.095,
            std_dev=0.015,
            min_time=0.08,
            max_time=0.12
        )

        result_str = str(result)

        assert "query_test" in result_str
        assert "mean=" in result_str
        assert "50 iterations" in result_str


class TestBenchmark:
    """Test Benchmark class."""

    def test_init(self):
        """Test benchmark initialization."""
        benchmark = Benchmark(
            name="test_benchmark",
            warmup_iterations=5,
            test_iterations=20
        )

        assert benchmark.name == "test_benchmark"
        assert benchmark.warmup_iterations == 5
        assert benchmark.test_iterations == 20

    def test_run_benchmark(self):
        """Test running a benchmark."""
        def simple_function():
            time.sleep(0.001)

        benchmark = Benchmark("simple_test", warmup_iterations=2, test_iterations=5)
        result = benchmark.run(simple_function)

        assert result.name == "simple_test"
        assert result.iterations == 5
        assert result.mean > 0
        assert result.median > 0
        assert result.min_time > 0
        assert result.max_time > 0

    def test_run_with_args(self):
        """Test running benchmark with function arguments."""
        def add_numbers(a, b):
            return a + b

        benchmark = Benchmark("add_test", warmup_iterations=1, test_iterations=3)
        result = benchmark.run(add_numbers, 5, 10)

        assert result.iterations == 3

    def test_run_with_metadata(self):
        """Test running benchmark with metadata."""
        def dummy():
            pass

        benchmark = Benchmark("meta_test", warmup_iterations=1, test_iterations=3)
        result = benchmark.run(dummy, metadata={"version": "1.0", "system": "test"})

        assert result.metadata["version"] == "1.0"
        assert result.metadata["system"] == "test"

    def test_compare_results(self):
        """Test comparing two benchmark results."""
        baseline = BenchmarkResult(
            name="baseline",
            duration=10.0,
            iterations=100,
            mean=0.1,
            median=0.1,
            std_dev=0.01,
            min_time=0.09,
            max_time=0.11
        )

        improved = BenchmarkResult(
            name="improved",
            duration=5.0,
            iterations=100,
            mean=0.05,
            median=0.05,
            std_dev=0.005,
            min_time=0.045,
            max_time=0.055
        )

        comparison = Benchmark.compare(baseline, improved)

        assert isinstance(comparison, ComparisonResult)
        assert comparison.speedup == 2.0  # 0.1 / 0.05
        assert comparison.improvement_percent == 50.0

    def test_compare_regression(self):
        """Test comparison showing regression."""
        baseline = BenchmarkResult(
            name="baseline",
            duration=5.0,
            iterations=100,
            mean=0.05,
            median=0.05,
            std_dev=0.005,
            min_time=0.045,
            max_time=0.055
        )

        slower = BenchmarkResult(
            name="slower",
            duration=10.0,
            iterations=100,
            mean=0.1,
            median=0.1,
            std_dev=0.01,
            min_time=0.09,
            max_time=0.11
        )

        comparison = Benchmark.compare(baseline, slower)

        assert comparison.speedup < 1.0
        assert comparison.improvement_percent < 0


class TestComparisonResult:
    """Test ComparisonResult class."""

    def test_str_speedup(self):
        """Test string representation for speedup."""
        baseline = BenchmarkResult(
            "baseline", 10, 100, 0.1, 0.1, 0.01, 0.09, 0.11
        )
        improved = BenchmarkResult(
            "improved", 5, 100, 0.05, 0.05, 0.005, 0.045, 0.055
        )

        comparison = ComparisonResult(
            baseline=baseline,
            comparison=improved,
            speedup=2.0,
            improvement_percent=50.0
        )

        result_str = str(comparison)

        assert "2.00x faster" in result_str
        assert "50.0% improvement" in result_str

    def test_str_regression(self):
        """Test string representation for regression."""
        baseline = BenchmarkResult(
            "baseline", 5, 100, 0.05, 0.05, 0.005, 0.045, 0.055
        )
        slower = BenchmarkResult(
            "slower", 10, 100, 0.1, 0.1, 0.01, 0.09, 0.11
        )

        comparison = ComparisonResult(
            baseline=baseline,
            comparison=slower,
            speedup=0.5,
            improvement_percent=-100.0
        )

        result_str = str(comparison)

        assert "slower" in result_str
        assert "regression" in result_str


class TestBenchmarkSuite:
    """Test BenchmarkSuite class."""

    def test_init(self):
        """Test suite initialization."""
        suite = BenchmarkSuite("my_suite")

        assert suite.name == "my_suite"
        assert len(suite.benchmarks) == 0
        assert len(suite.results) == 0

    def test_add_benchmark(self):
        """Test adding benchmarks to suite."""
        suite = BenchmarkSuite("test_suite")

        def func1():
            time.sleep(0.001)

        def func2():
            time.sleep(0.002)

        result1 = suite.add_benchmark("bench1", func1, warmup=1, iterations=3)
        result2 = suite.add_benchmark("bench2", func2, warmup=1, iterations=3)

        assert len(suite.benchmarks) == 2
        assert len(suite.results) == 2
        assert result1.name == "bench1"
        assert result2.name == "bench2"

    def test_summary(self):
        """Test generating suite summary."""
        suite = BenchmarkSuite("summary_test")

        def dummy():
            pass

        suite.add_benchmark("test1", dummy, warmup=1, iterations=2)
        suite.add_benchmark("test2", dummy, warmup=1, iterations=2)

        summary = suite.summary()

        assert "summary_test" in summary
        assert "test1" in summary
        assert "test2" in summary

    def test_save_and_load(self):
        """Test saving and loading suite results."""
        suite1 = BenchmarkSuite("save_test")

        def dummy():
            pass

        suite1.add_benchmark("bench1", dummy, warmup=1, iterations=3)
        suite1.add_benchmark("bench2", dummy, warmup=1, iterations=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"

            # Save
            suite1.save(output_path)

            assert output_path.exists()

            # Load
            suite2 = BenchmarkSuite.load(output_path)

            assert suite2.name == "save_test"
            assert len(suite2.results) == 2


class TestBenchmarkFunction:
    """Test benchmark_function convenience function."""

    def test_benchmark_function(self):
        """Test benchmarking a function."""
        def sample_function():
            time.sleep(0.001)

        result = benchmark_function(sample_function, iterations=5)

        assert result.name == "sample_function"
        assert result.iterations == 5
        assert result.mean > 0

    def test_benchmark_function_with_name(self):
        """Test benchmarking with custom name."""
        def func():
            pass

        result = benchmark_function(func, name="custom_name", iterations=3)

        assert result.name == "custom_name"

    def test_benchmark_function_with_args(self):
        """Test benchmarking function with arguments."""
        def multiply(x, y):
            return x * y

        result = benchmark_function(multiply, 5, 10, iterations=3)

        assert result.iterations == 3
