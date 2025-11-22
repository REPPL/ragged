"""
Quality metrics collection and tracking.

v0.3.9: RAGAS scores and performance metrics.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for a single query."""

    query_hash: str  # Privacy: hashed query, not plaintext
    timestamp: datetime
    duration_ms: float
    chunks_retrieved: int
    avg_confidence: float
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    ragas_score: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "query_hash": self.query_hash,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "chunks_retrieved": self.chunks_retrieved,
            "avg_confidence": self.avg_confidence,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "ragas_score": self.ragas_score,
            "success": self.success,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityMetrics":
        """Create from dictionary."""
        return cls(
            query_hash=data["query_hash"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration_ms=data["duration_ms"],
            chunks_retrieved=data["chunks_retrieved"],
            avg_confidence=data["avg_confidence"],
            context_precision=data.get("context_precision"),
            context_recall=data.get("context_recall"),
            faithfulness=data.get("faithfulness"),
            answer_relevancy=data.get("answer_relevancy"),
            ragas_score=data.get("ragas_score"),
            success=data.get("success", True),
            metadata=data.get("metadata", {}),
        )


class MetricsCollector:
    """
    Collect and track quality metrics for RAG pipeline.

    Uses JSON file storage for simplicity (MVP approach).
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialise metrics collector.

        Args:
            storage_path: Path to metrics storage file (JSON)
        """
        if storage_path is None:
            storage_path = Path.home() / ".ragged" / "metrics" / "metrics.json"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Set file permissions if exists
        if self.storage_path.exists():
            import os

            os.chmod(self.storage_path, 0o600)

        self.metrics: List[QualityMetrics] = []
        self._load()

    def _load(self) -> None:
        """Load metrics from storage."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            self.metrics = [QualityMetrics.from_dict(m) for m in data.get("metrics", [])]
            logger.info(f"Loaded {len(self.metrics)} metrics from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            self.metrics = []

    def _save(self) -> None:
        """Save metrics to storage."""
        try:
            data = {
                "metrics": [m.to_dict() for m in self.metrics],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

            # Set restrictive permissions
            import os

            os.chmod(self.storage_path, 0o600)

            logger.debug(f"Saved {len(self.metrics)} metrics to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def record(self, metrics: QualityMetrics) -> None:
        """
        Record quality metrics.

        Args:
            metrics: Quality metrics to record
        """
        self.metrics.append(metrics)
        self._save()

    def get_recent(self, limit: int = 100) -> List[QualityMetrics]:
        """
        Get recent metrics.

        Args:
            limit: Maximum number of metrics to return

        Returns:
            List of recent metrics (most recent first)
        """
        return sorted(self.metrics, key=lambda m: m.timestamp, reverse=True)[:limit]

    def get_statistics(self, last_n: int = 100) -> Dict[str, Any]:
        """
        Compute aggregate statistics.

        Args:
            last_n: Number of recent metrics to analyse

        Returns:
            Dictionary with statistics
        """
        recent = self.get_recent(last_n)

        if not recent:
            return {
                "count": 0,
                "avg_duration_ms": 0.0,
                "avg_confidence": 0.0,
                "avg_chunks": 0.0,
                "success_rate": 0.0,
            }

        # Filter successful queries
        successful = [m for m in recent if m.success]

        stats = {
            "count": len(recent),
            "success_count": len(successful),
            "failure_count": len(recent) - len(successful),
            "success_rate": len(successful) / len(recent) if recent else 0.0,
        }

        if successful:
            stats.update(
                {
                    "avg_duration_ms": sum(m.duration_ms for m in successful)
                    / len(successful),
                    "avg_confidence": sum(m.avg_confidence for m in successful)
                    / len(successful),
                    "avg_chunks": sum(m.chunks_retrieved for m in successful)
                    / len(successful),
                }
            )

            # RAGAS scores (if available)
            ragas_scores = [m for m in successful if m.ragas_score is not None]
            if ragas_scores:
                stats["avg_ragas_score"] = sum(m.ragas_score for m in ragas_scores) / len(
                    ragas_scores
                )

            # Individual RAGAS components
            for metric in [
                "context_precision",
                "context_recall",
                "faithfulness",
                "answer_relevancy",
            ]:
                values = [
                    getattr(m, metric)
                    for m in successful
                    if getattr(m, metric) is not None
                ]
                if values:
                    stats[f"avg_{metric}"] = sum(values) / len(values)

        return stats

    def render_dashboard(self, last_n: int = 100) -> str:
        """
        Render metrics dashboard.

        Args:
            last_n: Number of recent metrics to display

        Returns:
            Formatted dashboard text
        """
        stats = self.get_statistics(last_n)

        if stats["count"] == 0:
            return "No metrics recorded yet."

        output = []
        output.append("\n📊 Quality Metrics Dashboard\n")

        output.append(f"Metrics Summary (last {last_n} queries):")
        output.append("-" * 70)
        output.append(f"  Total Queries: {stats['count']}")
        output.append(
            f"  Success Rate: {stats['success_rate']*100:.1f}% "
            f"({stats['success_count']}/{stats['count']})"
        )

        if stats.get("avg_duration_ms"):
            output.append(f"  Avg Duration: {stats['avg_duration_ms']:.1f}ms")
            output.append(f"  Avg Chunks Retrieved: {stats['avg_chunks']:.1f}")
            output.append(f"  Avg Confidence: {stats['avg_confidence']:.3f}")

        # RAGAS scores
        if stats.get("avg_ragas_score"):
            output.append("\nRAGAS Scores:")
            output.append(f"  Overall RAGAS: {stats['avg_ragas_score']:.3f}")

            if stats.get("avg_context_precision"):
                output.append(f"  Context Precision: {stats['avg_context_precision']:.3f}")
            if stats.get("avg_context_recall"):
                output.append(f"  Context Recall: {stats['avg_context_recall']:.3f}")
            if stats.get("avg_faithfulness"):
                output.append(f"  Faithfulness: {stats['avg_faithfulness']:.3f}")
            if stats.get("avg_answer_relevancy"):
                output.append(f"  Answer Relevancy: {stats['avg_answer_relevancy']:.3f}")

        output.append("-" * 70)

        # Quality assessment
        if stats.get("avg_ragas_score"):
            if stats["avg_ragas_score"] >= 0.8:
                output.append("\n✓ Quality: Excellent (RAGAS ≥ 0.8)")
            elif stats["avg_ragas_score"] >= 0.6:
                output.append("\n⚠️  Quality: Good (RAGAS 0.6-0.8)")
            else:
                output.append("\n❌ Quality: Needs Improvement (RAGAS < 0.6)")

        output.append("")
        return "\n".join(output)

    def export(self, output_path: Path, last_n: Optional[int] = None) -> None:
        """
        Export metrics to JSON file.

        Args:
            output_path: Path to export file
            last_n: Number of recent metrics to export (None = all)
        """
        metrics_to_export = self.get_recent(last_n) if last_n else self.metrics

        data = {
            "export_timestamp": datetime.now().isoformat(),
            "metrics_count": len(metrics_to_export),
            "metrics": [m.to_dict() for m in metrics_to_export],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(metrics_to_export)} metrics to {output_path}")

    def clear(self, confirm: bool = False) -> int:
        """
        Clear all metrics.

        Args:
            confirm: Must be True to actually clear

        Returns:
            Number of metrics cleared
        """
        if not confirm:
            raise ValueError("Must confirm=True to clear metrics")

        count = len(self.metrics)
        self.metrics.clear()
        self._save()

        logger.info(f"Cleared {count} metrics")
        return count


# Convenience function
def create_metrics_collector(storage_path: Optional[Path] = None) -> MetricsCollector:
    """
    Create a metrics collector.

    Args:
        storage_path: Path to metrics storage file

    Returns:
        MetricsCollector instance

    Example:
        >>> collector = create_metrics_collector()
        >>> metrics = QualityMetrics(...)
        >>> collector.record(metrics)
        >>> print(collector.render_dashboard())
    """
    return MetricsCollector(storage_path=storage_path)
