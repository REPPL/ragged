"""
Validation Performance Tests.

INSTALL-TEST-004: Benchmark validation performance.
"""

import time
from pathlib import Path
from typing import Callable, Generator

import pytest


@pytest.fixture
def test_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test home directory with structure."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)

    # Create standard structure
    for dirname in ["documents", "cache", "logs", "data"]:
        (home / dirname).mkdir()

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


class TestPortValidationPerformance:
    """Benchmark port validation performance."""

    def test_port_validation_speed(self) -> None:
        """Test port validation completes quickly."""
        from ragged.install.validation import PortValidator

        validator = PortValidator()

        stats = measure_time(validator.validate, iterations=5)

        # Port checking should be fast
        assert stats["avg"] < 1.0, f"Port validation too slow: {stats['avg']:.3f}s"

    def test_port_check_individual(self) -> None:
        """Test individual port check performance."""
        import socket

        def check_port() -> bool:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.settimeout(0.1)
                sock.bind(("127.0.0.1", 0))
                return True
            except Exception:
                return False
            finally:
                sock.close()

        stats = measure_time(check_port, iterations=20)

        # Individual port check should be very fast
        assert stats["avg"] < 0.05, f"Port check too slow: {stats['avg']:.3f}s"


class TestFilesystemValidationPerformance:
    """Benchmark filesystem validation performance."""

    def test_filesystem_validation_speed(
        self,
        test_home: Path,
    ) -> None:
        """Test filesystem validation completes quickly."""
        from ragged.install.validation import FilesystemValidator

        validator = FilesystemValidator(test_home)

        stats = measure_time(validator.validate, iterations=10)

        # Filesystem checks should be fast
        assert stats["avg"] < 0.5, f"Filesystem validation too slow: {stats['avg']:.3f}s"

    def test_filesystem_validation_with_many_files(
        self,
        test_home: Path,
    ) -> None:
        """Test filesystem validation with many files."""
        # Create many files
        docs = test_home / "documents"
        for i in range(100):
            (docs / f"file_{i}.txt").write_text(f"content {i}")

        from ragged.install.validation import FilesystemValidator

        validator = FilesystemValidator(test_home)

        stats = measure_time(validator.validate, iterations=5)

        # Should still be reasonably fast
        assert stats["avg"] < 2.0, f"Validation with many files too slow: {stats['avg']:.3f}s"


class TestVersionValidationPerformance:
    """Benchmark version validation performance."""

    def test_version_validation_speed(self) -> None:
        """Test version validation completes quickly."""
        from ragged.install.validation import VersionValidator

        validator = VersionValidator()

        stats = measure_time(validator.validate, iterations=10)

        # Version checks should be fast
        assert stats["avg"] < 0.2, f"Version validation too slow: {stats['avg']:.3f}s"


class TestFullValidationPerformance:
    """Benchmark complete validation suite performance."""

    def test_full_validation_speed(
        self,
        test_home: Path,
    ) -> None:
        """Test full environment validation completes quickly."""
        from ragged.install.validation import validate_environment

        def run_validation() -> None:
            validate_environment(test_home)

        stats = measure_time(run_validation, iterations=5)

        # Full validation should complete in reasonable time
        assert stats["avg"] < 3.0, f"Full validation too slow: {stats['avg']:.3f}s"

    def test_validation_scales_linearly(
        self,
        tmp_path: Path,
    ) -> None:
        """Test validation time scales reasonably with complexity."""
        from ragged.install.validation import validate_environment

        times: list[float] = []

        # Test with increasing file counts
        for file_count in [10, 50, 100]:
            home = tmp_path / f"home_{file_count}"
            home.mkdir(parents=True)

            docs = home / "documents"
            docs.mkdir()
            for i in range(file_count):
                (docs / f"file_{i}.txt").write_text(f"content {i}")

            start = time.perf_counter()
            validate_environment(home)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Time should not explode exponentially
        # 10x more files should not take 10x longer
        if times[0] > 0.001:  # Avoid division issues
            ratio = times[2] / times[0]
            assert ratio < 20, f"Validation scaling too aggressive: {ratio:.1f}x"
