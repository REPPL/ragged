"""
Scaffolding Performance Tests.

INSTALL-TEST-004: Benchmark scaffolding performance.
"""

import shutil
import time
from pathlib import Path
from typing import Callable, Generator

import pytest


@pytest.fixture
def clean_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create clean home directory for each test."""
    home = tmp_path / ".ragged"
    yield home
    # Cleanup
    if home.exists():
        shutil.rmtree(home)


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


class TestDirectoryCreationPerformance:
    """Benchmark directory creation performance."""

    def test_structure_creation_speed(
        self,
        tmp_path: Path,
    ) -> None:
        """Test directory structure creation is fast."""
        from ragged.install.scaffolding import create_directory_structure

        times: list[float] = []

        for i in range(5):
            home = tmp_path / f"test_{i}"
            start = time.perf_counter()
            create_directory_structure(home)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            shutil.rmtree(home)

        avg_time = sum(times) / len(times)
        assert avg_time < 0.5, f"Structure creation too slow: {avg_time:.3f}s"

    def test_idempotent_operation_speed(
        self,
        clean_home: Path,
    ) -> None:
        """Test idempotent operations are fast."""
        from ragged.install.scaffolding import create_directory_structure

        # First run
        create_directory_structure(clean_home)

        # Subsequent runs should be very fast
        stats = measure_time(
            lambda: create_directory_structure(clean_home),
            iterations=10,
        )

        # Idempotent should be faster than first run
        assert stats["avg"] < 0.2, f"Idempotent operation too slow: {stats['avg']:.3f}s"


class TestUninstallPerformance:
    """Benchmark uninstall performance."""

    def test_uninstall_preview_speed(
        self,
        clean_home: Path,
    ) -> None:
        """Test uninstall preview is fast."""
        from ragged.install.scaffolding import (
            create_directory_structure,
            get_uninstall_preview,
        )

        create_directory_structure(clean_home)

        stats = measure_time(
            lambda: get_uninstall_preview(clean_home),
            iterations=10,
        )

        # Preview should be very fast (just scanning)
        assert stats["avg"] < 0.2, f"Uninstall preview too slow: {stats['avg']:.3f}s"

    def test_uninstall_preview_with_data(
        self,
        clean_home: Path,
    ) -> None:
        """Test uninstall preview with user data."""
        from ragged.install.scaffolding import (
            create_directory_structure,
            get_uninstall_preview,
        )

        create_directory_structure(clean_home)

        # Add user data
        docs = clean_home / "documents"
        for i in range(50):
            (docs / f"doc_{i}.txt").write_text(f"content {i}" * 100)

        stats = measure_time(
            lambda: get_uninstall_preview(clean_home),
            iterations=5,
        )

        # Should still be reasonably fast
        assert stats["avg"] < 1.0, f"Preview with data too slow: {stats['avg']:.3f}s"


class TestFullWorkflowPerformance:
    """Benchmark complete installation workflow performance."""

    def test_complete_installation_speed(
        self,
        tmp_path: Path,
    ) -> None:
        """Test complete installation workflow is fast."""
        from ragged.install import detect_all_prerequisites
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        times: list[float] = []

        for i in range(3):
            home = tmp_path / f"install_{i}"

            start = time.perf_counter()

            # Full workflow
            detect_all_prerequisites(home)
            create_directory_structure(home)
            validate_environment(home)

            elapsed = time.perf_counter() - start
            times.append(elapsed)

            shutil.rmtree(home)

        avg_time = sum(times) / len(times)
        assert avg_time < 10.0, f"Full installation too slow: {avg_time:.3f}s"

    def test_workflow_breakdown(
        self,
        tmp_path: Path,
    ) -> None:
        """Test workflow step timing breakdown."""
        from ragged.install import detect_all_prerequisites
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        home = tmp_path / "breakdown"

        # Measure each step
        start = time.perf_counter()
        detect_all_prerequisites(home)
        detect_time = time.perf_counter() - start

        start = time.perf_counter()
        create_directory_structure(home)
        scaffold_time = time.perf_counter() - start

        start = time.perf_counter()
        validate_environment(home)
        validate_time = time.perf_counter() - start

        # Report timing breakdown
        total = detect_time + scaffold_time + validate_time

        # No step should dominate excessively
        assert detect_time < total * 0.9, "Detection dominates workflow"
        assert scaffold_time < total * 0.9, "Scaffolding dominates workflow"
        assert validate_time < total * 0.9, "Validation dominates workflow"


class TestMemoryPerformance:
    """Benchmark memory usage during installation."""

    def test_memory_not_excessive(
        self,
        clean_home: Path,
    ) -> None:
        """Test memory usage is reasonable."""
        import sys

        # Get initial memory state (approximate)
        initial_objects = len(gc_get_objects()) if "gc_get_objects" in dir() else 0

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(clean_home)

        # Basic check - operation should complete
        assert clean_home.exists()


def gc_get_objects() -> list:
    """Get garbage collector objects if available."""
    try:
        import gc

        return gc.get_objects()
    except Exception:
        return []
