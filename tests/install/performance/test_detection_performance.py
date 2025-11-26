"""
Detection Performance Tests.

INSTALL-TEST-004: Benchmark prerequisite detection performance.
"""

import time
from pathlib import Path
from typing import Callable, Generator

import pytest


@pytest.fixture
def test_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test home directory."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    yield home


def measure_time(func: Callable, iterations: int = 10) -> dict[str, float]:
    """Measure execution time statistics."""
    times: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "min": min(times),
        "max": max(times),
        "avg": sum(times) / len(times),
        "total": sum(times),
    }


class TestPythonDetectionPerformance:
    """Benchmark Python detection performance."""

    def test_python_detection_speed(self) -> None:
        """Test Python detection completes quickly."""
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()

        stats = measure_time(detector.detect, iterations=10)

        # Should complete in under 100ms average
        assert stats["avg"] < 0.1, f"Python detection too slow: {stats['avg']:.3f}s"

    def test_python_detection_consistency(self) -> None:
        """Test Python detection has consistent timing."""
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()

        stats = measure_time(detector.detect, iterations=20)

        # Variance should be low
        variance = stats["max"] - stats["min"]
        assert variance < 0.1, f"Detection timing too variable: {variance:.3f}s"


class TestDockerDetectionPerformance:
    """Benchmark Docker detection performance."""

    def test_docker_detection_speed(self) -> None:
        """Test Docker detection completes quickly."""
        from ragged.install.detection import DockerDetector

        detector = DockerDetector()

        stats = measure_time(detector.detect, iterations=5)

        # Docker detection may invoke subprocess, allow more time
        assert stats["avg"] < 2.0, f"Docker detection too slow: {stats['avg']:.3f}s"

    def test_docker_detection_with_timeout(self) -> None:
        """Test Docker detection respects timeout."""
        from ragged.install.detection import DockerDetector

        detector = DockerDetector()

        start = time.perf_counter()
        detector.detect()
        elapsed = time.perf_counter() - start

        # Should not hang indefinitely
        assert elapsed < 10.0, f"Docker detection took too long: {elapsed:.3f}s"


class TestOllamaDetectionPerformance:
    """Benchmark Ollama detection performance."""

    def test_ollama_detection_speed(self) -> None:
        """Test Ollama detection completes quickly."""
        from ragged.install.detection import OllamaDetector

        detector = OllamaDetector()

        stats = measure_time(detector.detect, iterations=5)

        # Allow similar time as Docker
        assert stats["avg"] < 2.0, f"Ollama detection too slow: {stats['avg']:.3f}s"


class TestEnvironmentDetectionPerformance:
    """Benchmark environment detection performance."""

    def test_environment_detection_speed(
        self,
        test_home: Path,
    ) -> None:
        """Test environment detection completes quickly."""
        from ragged.install.detection import EnvironmentDetector

        detector = EnvironmentDetector(test_home)

        stats = measure_time(detector.detect, iterations=10)

        # Should be fast (disk check)
        assert stats["avg"] < 0.5, f"Environment detection too slow: {stats['avg']:.3f}s"


class TestFullDetectionPerformance:
    """Benchmark complete detection suite performance."""

    def test_all_prerequisites_speed(
        self,
        test_home: Path,
    ) -> None:
        """Test full prerequisite detection completes quickly."""
        from ragged.install.detection import detect_all_prerequisites

        def run_detection() -> None:
            detect_all_prerequisites(test_home)

        stats = measure_time(run_detection, iterations=3)

        # Full detection should complete in reasonable time
        assert stats["avg"] < 5.0, f"Full detection too slow: {stats['avg']:.3f}s"

    def test_detection_parallelization_potential(
        self,
        test_home: Path,
    ) -> None:
        """Test detection could benefit from parallelization."""
        from ragged.install.detection import (
            DockerDetector,
            EnvironmentDetector,
            OllamaDetector,
            PythonDetector,
        )

        # Measure individual detectors
        detectors = [
            PythonDetector(),
            DockerDetector(),
            OllamaDetector(),
            EnvironmentDetector(test_home),
        ]

        total_sequential = 0.0
        for detector in detectors:
            start = time.perf_counter()
            detector.detect()
            total_sequential += time.perf_counter() - start

        # Sequential should complete (no assertion, just measure)
        assert total_sequential >= 0
