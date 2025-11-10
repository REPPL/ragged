"""Performance benchmarking utilities.

Tools for measuring and comparing system performance.
"""

import time
import statistics
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import json
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Single benchmark measurement result."""

    name: str
    duration: float
    iterations: int
    mean: float
    median: float
    std_dev: float
    min_time: float
    max_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "duration": self.duration,
            "iterations": self.iterations,
            "mean": self.mean,
            "median": self.median,
            "std_dev": self.std_dev,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.name}: "
            f"mean={self.mean*1000:.2f}ms, "
            f"median={self.median*1000:.2f}ms, "
            f"std={self.std_dev*1000:.2f}ms "
            f"({self.iterations} iterations)"
        )


@dataclass
class ComparisonResult:
    """Comparison between two benchmark results."""

    baseline: BenchmarkResult
    comparison: BenchmarkResult
    speedup: float
    improvement_percent: float

    def __str__(self) -> str:
        """Human-readable representation."""
        if self.speedup > 1:
            return (
                f"{self.comparison.name} is {self.speedup:.2f}x faster "
                f"than {self.baseline.name} "
                f"({self.improvement_percent:.1f}% improvement)"
            )
        else:
            slowdown = 1 / self.speedup
            return (
                f"{self.comparison.name} is {slowdown:.2f}x slower "
                f"than {self.baseline.name} "
                f"({abs(self.improvement_percent):.1f}% regression)"
            )


class Timer:
    """Simple timer for measuring elapsed time."""

    def __init__(self):
        """Initialize timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: Optional[float] = None

    def start(self) -> None:
        """Start timer."""
        self.start_time = time.perf_counter()
        self.end_time = None
        self.elapsed = None

    def stop(self) -> float:
        """Stop timer and return elapsed time.

        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")

        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time
        return self.elapsed

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


@contextmanager
def time_it(name: str = "operation"):
    """Context manager for timing operations.

    Args:
        name: Operation name

    Yields:
        Timer object

    Example:
        with time_it("document loading") as timer:
            load_documents()
        print(f"Took {timer.elapsed:.2f}s")
    """
    timer = Timer()
    timer.start()
    logger.debug(f"Starting: {name}")

    try:
        yield timer
    finally:
        duration = timer.stop()
        logger.debug(f"Completed: {name} in {duration:.3f}s")


class Benchmark:
    """Benchmark runner for performance testing."""

    def __init__(
        self,
        name: str,
        warmup_iterations: int = 3,
        test_iterations: int = 10
    ):
        """Initialize benchmark.

        Args:
            name: Benchmark name
            warmup_iterations: Number of warmup runs (not measured)
            test_iterations: Number of measured runs
        """
        self.name = name
        self.warmup_iterations = warmup_iterations
        self.test_iterations = test_iterations
        self.results: List[BenchmarkResult] = []

    def run(
        self,
        func: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BenchmarkResult:
        """Run benchmark on function.

        Args:
            func: Function to benchmark
            *args: Function arguments
            metadata: Optional metadata to include
            **kwargs: Function keyword arguments

        Returns:
            Benchmark result
        """
        logger.info(
            f"Running benchmark: {self.name} "
            f"({self.warmup_iterations} warmup + {self.test_iterations} test)"
        )

        # Warmup runs
        logger.debug(f"Warmup runs: {self.warmup_iterations}")
        for i in range(self.warmup_iterations):
            func(*args, **kwargs)

        # Measured runs
        logger.debug(f"Measured runs: {self.test_iterations}")
        times = []
        start_time = time.perf_counter()

        for i in range(self.test_iterations):
            iter_start = time.perf_counter()
            func(*args, **kwargs)
            iter_time = time.perf_counter() - iter_start
            times.append(iter_time)

        total_duration = time.perf_counter() - start_time

        # Calculate statistics
        result = BenchmarkResult(
            name=self.name,
            duration=total_duration,
            iterations=self.test_iterations,
            mean=statistics.mean(times),
            median=statistics.median(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            min_time=min(times),
            max_time=max(times),
            metadata=metadata or {}
        )

        self.results.append(result)

        logger.info(str(result))

        return result

    @staticmethod
    def compare(
        baseline: BenchmarkResult,
        comparison: BenchmarkResult
    ) -> ComparisonResult:
        """Compare two benchmark results.

        Args:
            baseline: Baseline result
            comparison: Comparison result

        Returns:
            Comparison result
        """
        speedup = baseline.mean / comparison.mean
        improvement_percent = ((baseline.mean - comparison.mean) / baseline.mean) * 100

        return ComparisonResult(
            baseline=baseline,
            comparison=comparison,
            speedup=speedup,
            improvement_percent=improvement_percent
        )


class BenchmarkSuite:
    """Collection of related benchmarks."""

    def __init__(self, name: str):
        """Initialize benchmark suite.

        Args:
            name: Suite name
        """
        self.name = name
        self.benchmarks: List[Benchmark] = []
        self.results: List[BenchmarkResult] = []

    def add_benchmark(
        self,
        name: str,
        func: Callable,
        *args,
        warmup: int = 3,
        iterations: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BenchmarkResult:
        """Add and run benchmark.

        Args:
            name: Benchmark name
            func: Function to benchmark
            *args: Function arguments
            warmup: Warmup iterations
            iterations: Test iterations
            metadata: Optional metadata
            **kwargs: Function keyword arguments

        Returns:
            Benchmark result
        """
        benchmark = Benchmark(name, warmup_iterations=warmup, test_iterations=iterations)
        result = benchmark.run(func, *args, metadata=metadata, **kwargs)

        self.benchmarks.append(benchmark)
        self.results.append(result)

        return result

    def summary(self) -> str:
        """Generate summary of all benchmarks.

        Returns:
            Summary string
        """
        if not self.results:
            return f"Benchmark Suite: {self.name} (no results)"

        lines = [
            f"Benchmark Suite: {self.name}",
            "=" * 60,
            ""
        ]

        for result in self.results:
            lines.append(str(result))

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def save(self, output_path: Path) -> None:
        """Save results to JSON file.

        Args:
            output_path: Output file path
        """
        data = {
            "suite_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved benchmark results to {output_path}")

    @staticmethod
    def load(input_path: Path) -> "BenchmarkSuite":
        """Load results from JSON file.

        Args:
            input_path: Input file path

        Returns:
            Loaded benchmark suite
        """
        with open(input_path, "r") as f:
            data = json.load(f)

        suite = BenchmarkSuite(data["suite_name"])

        for result_data in data["results"]:
            result = BenchmarkResult(
                name=result_data["name"],
                duration=result_data["duration"],
                iterations=result_data["iterations"],
                mean=result_data["mean"],
                median=result_data["median"],
                std_dev=result_data["std_dev"],
                min_time=result_data["min_time"],
                max_time=result_data["max_time"],
                timestamp=datetime.fromisoformat(result_data["timestamp"]),
                metadata=result_data.get("metadata", {})
            )
            suite.results.append(result)

        logger.info(f"Loaded benchmark results from {input_path}")

        return suite


# Convenience functions

def benchmark_function(
    func: Callable,
    *args,
    name: Optional[str] = None,
    iterations: int = 10,
    **kwargs
) -> BenchmarkResult:
    """Quick benchmark of a function.

    Args:
        func: Function to benchmark
        *args: Function arguments
        name: Benchmark name (defaults to function name)
        iterations: Number of iterations
        **kwargs: Function keyword arguments

    Returns:
        Benchmark result
    """
    name = name or func.__name__
    benchmark = Benchmark(name, warmup_iterations=3, test_iterations=iterations)
    return benchmark.run(func, *args, **kwargs)
