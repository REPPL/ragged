"""Analytics query methods for metrics aggregation and analysis.

Provides comprehensive query capabilities for performance metrics,
trend analysis, and system insights.

v0.6.4 OPTIMISE-004 Phase 2: Analytics Queries
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetricsQuery:
    """Query interface for analytics metrics.

    Provides methods for:
    - Time-based metric aggregation
    - Model performance comparisons
    - Domain-specific analytics
    - Cache effectiveness analysis
    - Trend analysis (percentiles, averages)
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialise metrics query interface.

        Args:
            db_path: Path to SQLite database (defaults to MetricsStorage default)
        """
        from ragged.analytics.storage import MetricsStorage

        self.db_path = db_path or MetricsStorage.DEFAULT_DB_PATH

        if not self.db_path.exists():
            raise FileNotFoundError(f"Analytics database not found: {self.db_path}")

    def _execute_query(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute SQL query and return results as dictionaries.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dictionaries
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return results

    def query_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get summary statistics for a time period.

        Args:
            start_time: Start of time range (defaults to 24 hours ago)
            end_time: End of time range (defaults to now)

        Returns:
            Dictionary with summary statistics
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        # Query count and latency stats
        query_stats = self._execute_query(
            """
            SELECT
                COUNT(*) as total_queries,
                AVG(total_latency_ms) as avg_latency,
                MIN(total_latency_ms) as min_latency,
                MAX(total_latency_ms) as max_latency,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries,
                SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as cache_hits
            FROM query_metrics
            WHERE timestamp >= ? AND timestamp <= ?
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        # Model usage stats
        model_stats = self._execute_query(
            """
            SELECT
                selected_model,
                COUNT(*) as query_count,
                AVG(total_latency_ms) as avg_latency
            FROM query_metrics
            WHERE timestamp >= ? AND timestamp <= ?
                AND selected_model IS NOT NULL
            GROUP BY selected_model
            ORDER BY query_count DESC
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        # Domain distribution
        domain_stats = self._execute_query(
            """
            SELECT
                domain,
                COUNT(*) as query_count
            FROM query_metrics
            WHERE timestamp >= ? AND timestamp <= ?
                AND domain IS NOT NULL
            GROUP BY domain
            ORDER BY query_count DESC
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        stats = query_stats[0] if query_stats else {}

        # Calculate derived metrics
        if stats.get("total_queries", 0) > 0:
            stats["success_rate"] = (
                stats.get("successful_queries", 0) / stats["total_queries"]
            )
            stats["cache_hit_rate"] = (
                stats.get("cache_hits", 0) / stats["total_queries"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["cache_hit_rate"] = 0.0

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "query_stats": stats,
            "model_usage": model_stats,
            "domain_distribution": domain_stats,
        }

    def query_latency_percentiles(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        percentiles: list[int] = [50, 95, 99],
    ) -> dict[str, float]:
        """Calculate latency percentiles.

        Args:
            start_time: Start of time range
            end_time: End of time range
            percentiles: List of percentile values (e.g., [50, 95, 99])

        Returns:
            Dictionary mapping percentile to latency value
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        # Get all latencies in time range
        results = self._execute_query(
            """
            SELECT total_latency_ms
            FROM query_metrics
            WHERE timestamp >= ? AND timestamp <= ?
                AND total_latency_ms IS NOT NULL
            ORDER BY total_latency_ms
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        if not results:
            return {f"p{p}": 0.0 for p in percentiles}

        latencies = [r["total_latency_ms"] for r in results]
        n = len(latencies)

        percentile_values = {}
        for p in percentiles:
            index = int((p / 100.0) * n)
            if index >= n:
                index = n - 1
            percentile_values[f"p{p}"] = latencies[index]

        return percentile_values

    def query_model_performance(
        self,
        model_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get model performance metrics.

        Args:
            model_id: Specific model ID (None for all models)
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of model performance records
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        if model_id:
            results = self._execute_query(
                """
                SELECT *
                FROM model_metrics
                WHERE model_id = ?
                    AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                """,
                (model_id, start_time.isoformat(), end_time.isoformat()),
            )
        else:
            results = self._execute_query(
                """
                SELECT *
                FROM model_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC, model_id
                """,
                (start_time.isoformat(), end_time.isoformat()),
            )

        return results

    def query_cache_effectiveness(
        self,
        cache_layer: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get cache effectiveness metrics.

        Args:
            cache_layer: Specific cache layer (None for all layers)
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of cache effectiveness records
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        if cache_layer:
            results = self._execute_query(
                """
                SELECT *
                FROM cache_metrics
                WHERE cache_layer = ?
                    AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                """,
                (cache_layer, start_time.isoformat(), end_time.isoformat()),
            )
        else:
            results = self._execute_query(
                """
                SELECT *
                FROM cache_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC, cache_layer
                """,
                (start_time.isoformat(), end_time.isoformat()),
            )

        return results

    def query_domain_performance(
        self,
        domain: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get domain-specific performance metrics.

        Args:
            domain: Specific domain (None for all domains)
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with domain performance stats
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        if domain:
            query_results = self._execute_query(
                """
                SELECT
                    domain,
                    COUNT(*) as query_count,
                    AVG(total_latency_ms) as avg_latency,
                    AVG(retrieval_latency_ms) as avg_retrieval_latency,
                    AVG(llm_latency_ms) as avg_llm_latency,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM query_metrics
                WHERE domain = ?
                    AND timestamp >= ? AND timestamp <= ?
                GROUP BY domain
                """,
                (domain, start_time.isoformat(), end_time.isoformat()),
            )

            retrieval_results = self._execute_query(
                """
                SELECT
                    domain,
                    AVG(avg_score) as avg_relevance_score,
                    AVG(retrieval_latency_ms) as avg_retrieval_latency,
                    SUM(CASE WHEN domain_boost_applied = 1 THEN 1 ELSE 0 END) as boost_count
                FROM retrieval_metrics
                WHERE domain = ?
                    AND timestamp >= ? AND timestamp <= ?
                GROUP BY domain
                """,
                (domain, start_time.isoformat(), end_time.isoformat()),
            )
        else:
            query_results = self._execute_query(
                """
                SELECT
                    domain,
                    COUNT(*) as query_count,
                    AVG(total_latency_ms) as avg_latency,
                    AVG(retrieval_latency_ms) as avg_retrieval_latency,
                    AVG(llm_latency_ms) as avg_llm_latency,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM query_metrics
                WHERE domain IS NOT NULL
                    AND timestamp >= ? AND timestamp <= ?
                GROUP BY domain
                ORDER BY query_count DESC
                """,
                (start_time.isoformat(), end_time.isoformat()),
            )

            retrieval_results = self._execute_query(
                """
                SELECT
                    domain,
                    AVG(avg_score) as avg_relevance_score,
                    AVG(retrieval_latency_ms) as avg_retrieval_latency,
                    SUM(CASE WHEN domain_boost_applied = 1 THEN 1 ELSE 0 END) as boost_count
                FROM retrieval_metrics
                WHERE domain IS NOT NULL
                    AND timestamp >= ? AND timestamp <= ?
                GROUP BY domain
                ORDER BY domain
                """,
                (start_time.isoformat(), end_time.isoformat()),
            )

        # Merge query and retrieval results
        domain_stats = {}
        for qr in query_results:
            domain_key = qr["domain"]
            domain_stats[domain_key] = qr

        for rr in retrieval_results:
            domain_key = rr["domain"]
            if domain_key in domain_stats:
                domain_stats[domain_key].update({
                    "avg_relevance_score": rr["avg_relevance_score"],
                    "boost_count": rr["boost_count"],
                })

        return domain_stats if domain else {"domains": list(domain_stats.values())}

    def query_trends(
        self,
        metric: str = "total_latency_ms",
        interval: str = "hour",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get trend data for a metric over time.

        Args:
            metric: Metric to track (e.g., "total_latency_ms", "cache_hit_rate")
            interval: Time interval ("hour", "day", "week")
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of time-series data points
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(days=7))

        # SQLite doesn't have great date grouping, so we'll do it in Python
        results = self._execute_query(
            f"""
            SELECT
                timestamp,
                {metric}
            FROM query_metrics
            WHERE timestamp >= ? AND timestamp <= ?
                AND {metric} IS NOT NULL
            ORDER BY timestamp
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        # Group by interval
        interval_data = {}
        for r in results:
            ts = datetime.fromisoformat(r["timestamp"])

            if interval == "hour":
                key = ts.replace(minute=0, second=0, microsecond=0)
            elif interval == "day":
                key = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            elif interval == "week":
                # Start of week (Monday)
                days_since_monday = ts.weekday()
                key = (ts - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                raise ValueError(f"Invalid interval: {interval}")

            if key not in interval_data:
                interval_data[key] = []
            interval_data[key].append(r[metric])

        # Calculate averages per interval
        trend_data = []
        for key, values in sorted(interval_data.items()):
            trend_data.append({
                "timestamp": key.isoformat(),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            })

        return trend_data

    def compare_models(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Compare performance across models.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with model comparison data
        """
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        # Get per-model statistics from query_metrics
        model_query_stats = self._execute_query(
            """
            SELECT
                selected_model as model_id,
                COUNT(*) as query_count,
                AVG(total_latency_ms) as avg_total_latency,
                AVG(llm_latency_ms) as avg_llm_latency,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries
            FROM query_metrics
            WHERE selected_model IS NOT NULL
                AND timestamp >= ? AND timestamp <= ?
            GROUP BY selected_model
            ORDER BY query_count DESC
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        # Get per-model statistics from model_metrics
        model_metrics_stats = self._execute_query(
            """
            SELECT
                model_id,
                AVG(avg_latency_ms) as avg_latency,
                AVG(total_input_tokens) as avg_input_tokens,
                AVG(total_output_tokens) as avg_output_tokens,
                AVG(gpu_memory_used_mb) as avg_gpu_memory,
                AVG(gpu_utilization_percent) as avg_gpu_utilization
            FROM model_metrics
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY model_id
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        # Merge results
        comparison = {}
        for qs in model_query_stats:
            model_id = qs["model_id"]
            comparison[model_id] = qs

            # Calculate success rate
            if qs["query_count"] > 0:
                comparison[model_id]["success_rate"] = (
                    qs["successful_queries"] / qs["query_count"]
                )

        for ms in model_metrics_stats:
            model_id = ms["model_id"]
            if model_id in comparison:
                comparison[model_id].update({
                    "avg_input_tokens": ms["avg_input_tokens"],
                    "avg_output_tokens": ms["avg_output_tokens"],
                    "avg_gpu_memory": ms["avg_gpu_memory"],
                    "avg_gpu_utilization": ms["avg_gpu_utilization"],
                })

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "models": list(comparison.values()),
        }


def get_metrics_query(db_path: Optional[Path] = None) -> MetricsQuery:
    """Get MetricsQuery instance.

    Args:
        db_path: Path to analytics database

    Returns:
        MetricsQuery instance
    """
    return MetricsQuery(db_path=db_path)
