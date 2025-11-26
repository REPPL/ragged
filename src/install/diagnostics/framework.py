"""
Diagnostic Framework.

REFINE-001: Core framework for error diagnostics including
pipeline, categories, and result aggregation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import logging
import time


logger = logging.getLogger(__name__)


class DiagnosticCategory(Enum):
    """Categories of diagnostic issues."""

    CONNECTIVITY = "connectivity"
    PERMISSIONS = "permissions"
    RESOURCES = "resources"
    DEPENDENCIES = "dependencies"
    CONFIGURATION = "configuration"
    SERVICES = "services"


class DiagnosticSeverity(Enum):
    """Severity of diagnostic findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DiagnosticFix:
    """Suggested fix for a diagnostic issue."""

    description: str
    command: str | None = None
    auto_fixable: bool = False
    requires_sudo: bool = False
    destructive: bool = False


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    message: str
    root_cause: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    fixes: list[DiagnosticFix] = field(default_factory=list)
    documentation_url: str | None = None
    duration_ms: float = 0.0

    @property
    def is_critical(self) -> bool:
        """Check if result is critical."""
        return self.severity == DiagnosticSeverity.CRITICAL

    @property
    def is_error(self) -> bool:
        """Check if result is error or critical."""
        return self.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL)

    @property
    def has_auto_fix(self) -> bool:
        """Check if any fix is auto-applicable."""
        return any(fix.auto_fixable for fix in self.fixes)


class Diagnostic(ABC):
    """Abstract base class for diagnostics."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the diagnostic."""
        ...

    @property
    @abstractmethod
    def category(self) -> DiagnosticCategory:
        """Category of the diagnostic."""
        ...

    @abstractmethod
    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        """
        Run the diagnostic.

        Args:
            context: Diagnostic context (paths, config, etc.)

        Returns:
            List of diagnostic results.
        """
        ...


class DiagnosticPipeline:
    """
    Diagnostic pipeline for running multiple diagnostics.

    Manages diagnostic execution, result aggregation, and reporting.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise diagnostic pipeline.

        Args:
            ragged_home: Path to ragged home directory.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self._diagnostics: list[Diagnostic] = []
        self._results: list[DiagnosticResult] = []
        self._callbacks: list[Callable[[DiagnosticResult], None]] = []

    def register(self, diagnostic: Diagnostic) -> None:
        """Register a diagnostic."""
        self._diagnostics.append(diagnostic)

    def add_callback(self, callback: Callable[[DiagnosticResult], None]) -> None:
        """Add a result callback."""
        self._callbacks.append(callback)

    def run(
        self,
        categories: list[DiagnosticCategory] | None = None,
        error: Exception | None = None,
    ) -> list[DiagnosticResult]:
        """
        Run diagnostics.

        Args:
            categories: Categories to run (all if None).
            error: Original error to diagnose.

        Returns:
            List of diagnostic results.
        """
        self._results = []

        # Build context
        context = self._build_context(error)

        # Filter diagnostics by category
        diagnostics = self._diagnostics
        if categories:
            diagnostics = [d for d in diagnostics if d.category in categories]

        # Run each diagnostic
        for diagnostic in diagnostics:
            try:
                start = time.perf_counter()
                results = diagnostic.run(context)
                duration = (time.perf_counter() - start) * 1000

                for result in results:
                    result.duration_ms = duration / len(results) if results else 0
                    self._results.append(result)
                    self._notify(result)

            except Exception as e:
                logger.warning(f"Diagnostic {diagnostic.name} failed: {e}")
                self._results.append(DiagnosticResult(
                    name=diagnostic.name,
                    category=diagnostic.category,
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Diagnostic failed: {e}",
                ))

        return self._results

    def _build_context(self, error: Exception | None = None) -> dict[str, Any]:
        """Build diagnostic context."""
        import platform
        import sys

        return {
            "ragged_home": self.ragged_home,
            "error": error,
            "error_type": type(error).__name__ if error else None,
            "error_message": str(error) if error else None,
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "architecture": platform.machine(),
        }

    def _notify(self, result: DiagnosticResult) -> None:
        """Notify callbacks of result."""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.warning(f"Callback error: {e}")

    @property
    def results(self) -> list[DiagnosticResult]:
        """Get all results."""
        return self._results

    @property
    def critical_results(self) -> list[DiagnosticResult]:
        """Get critical results."""
        return [r for r in self._results if r.is_critical]

    @property
    def error_results(self) -> list[DiagnosticResult]:
        """Get error and critical results."""
        return [r for r in self._results if r.is_error]

    @property
    def has_errors(self) -> bool:
        """Check if any errors found."""
        return len(self.error_results) > 0

    @property
    def has_auto_fixes(self) -> bool:
        """Check if any auto-fixes available."""
        return any(r.has_auto_fix for r in self._results)


def run_diagnostics(
    ragged_home: Path | None = None,
    error: Exception | None = None,
    categories: list[DiagnosticCategory] | None = None,
) -> list[DiagnosticResult]:
    """
    Run all diagnostics.

    Args:
        ragged_home: Path to ragged home directory.
        error: Original error to diagnose.
        categories: Categories to run.

    Returns:
        List of diagnostic results.
    """
    from ragged.install.diagnostics.connectivity import (
        PortConflictDetector,
        NetworkDiagnostic,
        FirewallDiagnostic,
    )
    from ragged.install.diagnostics.permissions import (
        FilePermissionChecker,
        SELinuxDiagnostic,
    )
    from ragged.install.diagnostics.resources import (
        DiskSpaceDiagnostic,
        MemoryDiagnostic,
    )

    pipeline = DiagnosticPipeline(ragged_home)

    # Register all diagnostics
    pipeline.register(PortConflictDetector())
    pipeline.register(NetworkDiagnostic())
    pipeline.register(FirewallDiagnostic())
    pipeline.register(FilePermissionChecker())
    pipeline.register(SELinuxDiagnostic())
    pipeline.register(DiskSpaceDiagnostic())
    pipeline.register(MemoryDiagnostic())

    return pipeline.run(categories=categories, error=error)
