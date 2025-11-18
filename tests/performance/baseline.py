"""Baseline management for performance regression tests.

v0.2.9: Load, compare, and update performance baselines.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from src.utils.benchmarks import BenchmarkResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaselineNotFoundError(Exception):
    """Raised when baseline file is not found."""
    pass


class RegressionError(Exception):
    """Raised when performance regression is detected."""

    def __init__(self, benchmark_name: str, current: float, baseline: float, threshold: float):
        """
        Initialize regression error.

        Args:
            benchmark_name: Name of failing benchmark
            current: Current performance (seconds)
            baseline: Baseline performance (seconds)
            threshold: Regression threshold (e.g., 1.05 for 5%)
        """
        regression_percent = ((current - baseline) / baseline) * 100
        super().__init__(
            f"Performance regression detected in '{benchmark_name}': "
            f"{current:.3f}s vs baseline {baseline:.3f}s "
            f"({regression_percent:+.1f}%, threshold: {(threshold-1)*100:.0f}%)"
        )
        self.benchmark_name = benchmark_name
        self.current = current
        self.baseline = baseline
        self.regression_percent = regression_percent


def load_baseline(baseline_path: Path) -> Dict[str, BenchmarkResult]:
    """
    Load baseline from JSON file.

    Args:
        baseline_path: Path to baseline.json

    Returns:
        Dictionary mapping benchmark names to results

    Raises:
        BaselineNotFoundError: If baseline file doesn't exist

    Example:
        >>> baselines = load_baseline(Path("baseline.json"))
        >>> embedder_baseline = baselines["embedder-init-cold"]
    """
    if not baseline_path.exists():
        raise BaselineNotFoundError(f"Baseline not found: {baseline_path}")

    with open(baseline_path, "r") as f:
        data = json.load(f)

    baselines = {}
    for name, benchmark_data in data.get("benchmarks", {}).items():
        result = BenchmarkResult(
            name=name,
            duration=benchmark_data.get("duration", benchmark_data["mean"] * benchmark_data["iterations"]),
            iterations=benchmark_data["iterations"],
            mean=benchmark_data["mean"],
            median=benchmark_data["median"],
            std_dev=benchmark_data["std_dev"],
            min_time=benchmark_data["min"],
            max_time=benchmark_data["max"],
        )
        baselines[name] = result

    logger.info(f"Loaded {len(baselines)} baseline benchmarks from {baseline_path}")
    return baselines


def save_baseline(
    baseline_path: Path,
    benchmarks: Dict[str, BenchmarkResult],
    version: str = "0.2.9",
    metadata: Optional[Dict] = None
) -> None:
    """
    Save benchmark results as new baseline.

    Args:
        baseline_path: Path to save baseline.json
        benchmarks: Dictionary of benchmark results
        version: Version string
        metadata: Optional metadata (hardware, environment, etc.)

    Example:
        >>> results = {"test": benchmark_result}
        >>> save_baseline(Path("baseline.json"), results, "0.2.9")
    """
    from datetime import datetime

    data = {
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
        "benchmarks": {
            name: {
                "mean": result.mean,
                "median": result.median,
                "std_dev": result.std_dev,
                "min": result.min_time,
                "max": result.max_time,
                "iterations": result.iterations,
                "duration": result.duration,
            }
            for name, result in benchmarks.items()
        }
    }

    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    with open(baseline_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(benchmarks)} benchmarks to {baseline_path}")


def compare_to_baseline(
    current: BenchmarkResult,
    baseline: BenchmarkResult,
    threshold: float = 1.05
) -> None:
    """
    Compare current result to baseline and raise if regression detected.

    Args:
        current: Current benchmark result
        baseline: Baseline benchmark result
        threshold: Maximum acceptable ratio (1.05 = 5% slower allowed)

    Raises:
        RegressionError: If current is slower than threshold

    Example:
        >>> compare_to_baseline(current_result, baseline_result, threshold=1.05)
        # Raises RegressionError if >5% slower
    """
    # Use median for more stable comparison (less affected by outliers)
    current_time = current.median
    baseline_time = baseline.median

    if current_time > baseline_time * threshold:
        raise RegressionError(
            benchmark_name=current.name,
            current=current_time,
            baseline=baseline_time,
            threshold=threshold
        )

    # Log if faster
    if current_time < baseline_time:
        improvement = ((baseline_time - current_time) / baseline_time) * 100
        logger.info(
            f"✅ {current.name}: {improvement:.1f}% faster than baseline "
            f"({current_time:.3f}s vs {baseline_time:.3f}s)"
        )
    else:
        degradation = ((current_time - baseline_time) / baseline_time) * 100
        logger.info(
            f"✅ {current.name}: {degradation:.1f}% slower (within {(threshold-1)*100:.0f}% threshold) "
            f"({current_time:.3f}s vs {baseline_time:.3f}s)"
        )


def get_default_baseline_path() -> Path:
    """
    Get default baseline file path.

    Returns:
        Path to baseline.json in project root

    Example:
        >>> baseline_path = get_default_baseline_path()
        >>> print(baseline_path)
        PosixPath('/path/to/ragged/baseline.json')
    """
    # Project root is 3 levels up from tests/performance/
    import sys
    from pathlib import Path

    # Try to find project root
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current / "baseline.json"
        current = current.parent

    # Fallback to tests/performance/baseline.json
    return Path(__file__).parent / "baseline.json"
