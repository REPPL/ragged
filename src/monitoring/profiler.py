"""
Performance profiling for RAG pipeline.

v0.3.9: Timing and bottleneck identification.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileStage:
    """A profiled pipeline stage."""

    name: str
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: float | None = None
    end_time: float | None = None

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0


class PerformanceProfiler:
    """
    Performance profiler for RAG pipeline.

    Captures timing information for pipeline stages and provides
    bottleneck analysis.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialise profiler.

        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.stages: list[ProfileStage] = []
        self._current_stage: ProfileStage | None = None

    @contextmanager
    def stage(self, name: str, **metadata: Any):
        """
        Profile a pipeline stage using context manager.

        Args:
            name: Stage name
            **metadata: Additional stage metadata

        Example:
            >>> profiler = PerformanceProfiler()
            >>> with profiler.stage("Query Embedding", model="all-MiniLM-L6-v2"):
            ...     embedding = embed(query)
        """
        if not self.enabled:
            yield
            return

        # Start timing
        start_time = time.perf_counter()

        try:
            yield
        finally:
            # End timing
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            # Record stage
            stage = ProfileStage(
                name=name,
                duration_ms=duration_ms,
                metadata=metadata,
                start_time=start_time,
                end_time=end_time,
            )
            self.stages.append(stage)

    def record_stage(self, name: str, duration_ms: float, **metadata: Any) -> None:
        """
        Manually record a stage (without context manager).

        Args:
            name: Stage name
            duration_ms: Duration in milliseconds
            **metadata: Additional metadata
        """
        if not self.enabled:
            return

        stage = ProfileStage(
            name=name,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        self.stages.append(stage)

    @property
    def total_duration_ms(self) -> float:
        """Get total pipeline duration in milliseconds."""
        if not self.stages:
            return 0.0

        # If stages have timestamps, use first start and last end
        if self.stages[0].start_time and self.stages[-1].end_time:
            return (self.stages[-1].end_time - self.stages[0].start_time) * 1000

        # Otherwise sum durations
        return sum(stage.duration_ms for stage in self.stages)

    @property
    def total_duration_seconds(self) -> float:
        """Get total duration in seconds."""
        return self.total_duration_ms / 1000.0

    def get_slowest_stages(self, top_n: int = 3) -> list[ProfileStage]:
        """
        Get the slowest pipeline stages.

        Args:
            top_n: Number of top slowest stages to return

        Returns:
            List of slowest stages
        """
        return sorted(self.stages, key=lambda s: s.duration_ms, reverse=True)[:top_n]

    def analyse_bottlenecks(self, threshold_percent: float = 20.0) -> list[str]:
        """
        Analyse bottlenecks and generate recommendations.

        Args:
            threshold_percent: Percentage threshold for bottleneck (default: 20%)

        Returns:
            List of bottleneck warnings and recommendations
        """
        if not self.stages:
            return []

        total_time = self.total_duration_ms
        if total_time == 0:
            return []

        recommendations = []

        for stage in self.stages:
            percentage = (stage.duration_ms / total_time) * 100

            if percentage >= threshold_percent:
                recommendations.append(
                    f"⚠️  {stage.name} taking {percentage:.1f}% of total time "
                    f"({stage.duration_ms:.1f}ms)"
                )

        return recommendations

    def render(self, show_metadata: bool = True) -> str:
        """
        Render profiling report as formatted text.

        Args:
            show_metadata: Whether to show stage metadata

        Returns:
            Formatted profiling report
        """
        if not self.stages:
            return "No profiling data recorded."

        output = []
        output.append("\n⏱️  Performance Profile\n")

        # Stage breakdown
        output.append("Pipeline Breakdown:")
        output.append("-" * 70)

        for i, stage in enumerate(self.stages, 1):
            percentage = (stage.duration_ms / self.total_duration_ms) * 100
            output.append(
                f"{i}. {stage.name:30s} {stage.duration_ms:8.1f}ms  ({percentage:5.1f}%)"
            )

            # Show metadata if requested
            if show_metadata and stage.metadata:
                for key, value in stage.metadata.items():
                    output.append(f"   {key}: {value}")

        output.append("-" * 70)
        output.append(f"Total: {self.total_duration_ms:.1f}ms")

        # Bottleneck analysis
        bottlenecks = self.analyse_bottlenecks()
        if bottlenecks:
            output.append("\n🔍 Bottleneck Analysis:")
            for bottleneck in bottlenecks:
                output.append(f"  {bottleneck}")

        # Recommendations
        if self.total_duration_ms > 2000:
            output.append("\n💡 Recommendations:")
            output.append(
                "  • Total time exceeds 2s - consider optimising slowest stages"
            )
        else:
            output.append("\n✓ Performance: Good (< 2s target)")

        output.append("")  # Blank line
        return "\n".join(output)

    def render_summary(self) -> str:
        """
        Render brief summary.

        Returns:
            Summary string
        """
        if not self.stages:
            return "No profiling data."

        slowest = self.get_slowest_stages(1)[0] if self.stages else None

        return (
            f"⏱️  Pipeline: {len(self.stages)} stages, "
            f"{self.total_duration_ms:.1f}ms total"
            + (f", slowest: {slowest.name} ({slowest.duration_ms:.1f}ms)" if slowest else "")
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert profiling data to dictionary.

        Returns:
            Dictionary with profiling data
        """
        return {
            "enabled": self.enabled,
            "total_duration_ms": self.total_duration_ms,
            "stages": [
                {
                    "name": stage.name,
                    "duration_ms": stage.duration_ms,
                    "metadata": stage.metadata,
                }
                for stage in self.stages
            ],
            "bottlenecks": self.analyse_bottlenecks(),
        }

    def clear(self) -> None:
        """Clear all profiling data."""
        self.stages.clear()
        self._current_stage = None


# Convenience function
def create_profiler(enabled: bool = True) -> PerformanceProfiler:
    """
    Create a performance profiler.

    Args:
        enabled: Whether profiling is enabled

    Returns:
        PerformanceProfiler instance

    Example:
        >>> profiler = create_profiler(enabled=True)
        >>> with profiler.stage("Query Processing"):
        ...     process_query()
        >>> print(profiler.render())
    """
    return PerformanceProfiler(enabled=enabled)
