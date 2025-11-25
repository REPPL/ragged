"""Time-series metrics storage using SQLite.

Provides efficient storage and retrieval of analytics metrics with
automatic retention policy enforcement.

v0.6.4 OPTIMISE-004 Phase 1: Metrics Collection Framework
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ragged.analytics.models import (
    CacheMetrics,
    ModelMetrics,
    QueryMetrics,
    RetrievalMetrics,
    SystemMetrics,
)

logger = logging.getLogger(__name__)


class MetricsStorage:
    """SQLite-based time-series storage for analytics metrics.

    Features:
    - Automatic schema creation
    - Asynchronous writes (optional)
    - Retention policy enforcement
    - Efficient time-based queries
    - Automatic database size management
    """

    DEFAULT_DB_PATH = Path.home() / ".ragged" / "analytics.db"
    DEFAULT_RETENTION_DAYS = 30
    DEFAULT_MAX_SIZE_MB = 500

    def __init__(
        self,
        db_path: Optional[Path] = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        max_size_mb: int = DEFAULT_MAX_SIZE_MB,
    ):
        """Initialize metrics storage.

        Args:
            db_path: Path to SQLite database file
            retention_days: Number of days to retain metrics
            max_size_mb: Maximum database size in MB
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.retention_days = retention_days
        self.max_size_mb = max_size_mb

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"Initialized MetricsStorage at {self.db_path}")

    def _init_database(self) -> None:
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Query metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_metrics (
                query_id TEXT PRIMARY KEY,
                query_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                query_length INTEGER,
                query_type TEXT,
                complexity INTEGER,
                domain TEXT,
                total_latency_ms REAL,
                classification_latency_ms REAL,
                routing_latency_ms REAL,
                retrieval_latency_ms REAL,
                llm_latency_ms REAL,
                selected_model TEXT,
                routing_reason TEXT,
                cache_hit INTEGER,
                cache_layer TEXT,
                success INTEGER,
                error_type TEXT,
                metadata TEXT
            )
        """)

        # Create index on timestamp for time-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_timestamp
            ON query_metrics(timestamp)
        """)

        # Create index on query_hash for deduplication
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_hash
            ON query_metrics(query_hash)
        """)

        # Retrieval metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retrieval_metrics (
                retrieval_id TEXT PRIMARY KEY,
                query_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                k INTEGER,
                domain TEXT,
                retrieval_latency_ms REAL,
                embedding_latency_ms REAL,
                search_latency_ms REAL,
                reranking_latency_ms REAL,
                results_count INTEGER,
                avg_score REAL,
                domain_boost_applied INTEGER,
                precision_at_k REAL,
                recall_at_k REAL,
                metadata TEXT,
                FOREIGN KEY (query_id) REFERENCES query_metrics(query_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_retrieval_timestamp
            ON retrieval_metrics(timestamp)
        """)

        # Model metrics table (aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                model_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                invocation_count INTEGER,
                total_latency_ms REAL,
                avg_latency_ms REAL,
                total_input_tokens INTEGER,
                total_output_tokens INTEGER,
                avg_tokens_per_query REAL,
                gpu_memory_used_mb REAL,
                gpu_utilization_percent REAL,
                gpu_temperature_celsius REAL,
                average_quality_score REAL,
                metadata TEXT,
                PRIMARY KEY (model_id, timestamp)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_timestamp
            ON model_metrics(timestamp)
        """)

        # Cache metrics table (aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metrics (
                cache_layer TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                total_requests INTEGER,
                cache_hits INTEGER,
                cache_misses INTEGER,
                hit_rate REAL,
                avg_hit_latency_ms REAL,
                avg_miss_latency_ms REAL,
                latency_saved_ms REAL,
                cache_size_entries INTEGER,
                cache_size_bytes INTEGER,
                cache_size_mb REAL,
                eviction_count INTEGER,
                eviction_reason TEXT,
                metadata TEXT,
                PRIMARY KEY (cache_layer, timestamp)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_timestamp
            ON cache_metrics(timestamp)
        """)

        # System metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                timestamp TEXT PRIMARY KEY,
                system_memory_used_mb REAL,
                system_memory_available_mb REAL,
                system_memory_percent REAL,
                cpu_percent REAL,
                cpu_count INTEGER,
                analytics_db_size_mb REAL,
                analytics_db_path TEXT,
                process_memory_mb REAL,
                process_threads INTEGER,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_timestamp
            ON system_metrics(timestamp)
        """)

        conn.commit()
        conn.close()

        logger.debug("Database schema initialized")

    def store_query_metrics(self, metrics: QueryMetrics) -> None:
        """Store query metrics.

        Args:
            metrics: QueryMetrics instance
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO query_metrics VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """,
            (
                metrics.query_id,
                metrics.query_hash,
                metrics.timestamp.isoformat(),
                metrics.query_length,
                metrics.query_type,
                metrics.complexity,
                metrics.domain,
                metrics.total_latency_ms,
                metrics.classification_latency_ms,
                metrics.routing_latency_ms,
                metrics.retrieval_latency_ms,
                metrics.llm_latency_ms,
                metrics.selected_model,
                metrics.routing_reason,
                1 if metrics.cache_hit else 0,
                metrics.cache_layer,
                1 if metrics.success else 0,
                metrics.error_type,
                str(metrics.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def store_retrieval_metrics(self, metrics: RetrievalMetrics) -> None:
        """Store retrieval metrics.

        Args:
            metrics: RetrievalMetrics instance
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO retrieval_metrics VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """,
            (
                metrics.retrieval_id,
                metrics.query_id,
                metrics.timestamp.isoformat(),
                metrics.k,
                metrics.domain,
                metrics.retrieval_latency_ms,
                metrics.embedding_latency_ms,
                metrics.search_latency_ms,
                metrics.reranking_latency_ms,
                metrics.results_count,
                metrics.avg_score,
                1 if metrics.domain_boost_applied else 0,
                metrics.precision_at_k,
                metrics.recall_at_k,
                str(metrics.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def store_model_metrics(self, metrics: ModelMetrics) -> None:
        """Store model metrics.

        Args:
            metrics: ModelMetrics instance
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO model_metrics VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """,
            (
                metrics.model_id,
                metrics.timestamp.isoformat(),
                metrics.invocation_count,
                metrics.total_latency_ms,
                metrics.avg_latency_ms,
                metrics.total_input_tokens,
                metrics.total_output_tokens,
                metrics.avg_tokens_per_query,
                metrics.gpu_memory_used_mb,
                metrics.gpu_utilization_percent,
                metrics.gpu_temperature_celsius,
                metrics.average_quality_score,
                str(metrics.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def store_cache_metrics(self, metrics: CacheMetrics) -> None:
        """Store cache metrics.

        Args:
            metrics: CacheMetrics instance
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO cache_metrics VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """,
            (
                metrics.cache_layer,
                metrics.timestamp.isoformat(),
                metrics.total_requests,
                metrics.cache_hits,
                metrics.cache_misses,
                metrics.hit_rate,
                metrics.avg_hit_latency_ms,
                metrics.avg_miss_latency_ms,
                metrics.latency_saved_ms,
                metrics.cache_size_entries,
                metrics.cache_size_bytes,
                metrics.cache_size_mb,
                metrics.eviction_count,
                metrics.eviction_reason,
                str(metrics.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def store_system_metrics(self, metrics: SystemMetrics) -> None:
        """Store system metrics.

        Args:
            metrics: SystemMetrics instance
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO system_metrics VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """,
            (
                metrics.timestamp.isoformat(),
                metrics.system_memory_used_mb,
                metrics.system_memory_available_mb,
                metrics.system_memory_percent,
                metrics.cpu_percent,
                metrics.cpu_count,
                metrics.analytics_db_size_mb,
                metrics.analytics_db_path,
                metrics.process_memory_mb,
                metrics.process_threads,
                str(metrics.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def cleanup_old_metrics(self) -> int:
        """Remove metrics older than retention period.

        Returns:
            Number of rows deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cutoff_iso = cutoff_date.isoformat()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        tables = ["query_metrics", "retrieval_metrics", "model_metrics", "cache_metrics", "system_metrics"]

        total_deleted = 0
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff_iso,))
            total_deleted += cursor.rowcount

        conn.commit()
        conn.close()

        if total_deleted > 0:
            logger.info(f"Cleaned up {total_deleted} old metrics (older than {self.retention_days} days)")

        # Vacuum to reclaim space
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("VACUUM")
        conn.close()

        return total_deleted

    def get_database_size_mb(self) -> float:
        """Get current database size in MB.

        Returns:
            Database size in megabytes
        """
        if not self.db_path.exists():
            return 0.0

        size_bytes = self.db_path.stat().st_size
        return size_bytes / (1024 * 1024)

    def health_check(self) -> dict:
        """Perform storage health check.

        Returns:
            Dictionary with health status
        """
        db_size_mb = self.get_database_size_mb()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Count rows in each table
        counts = {}
        for table in ["query_metrics", "retrieval_metrics", "model_metrics", "cache_metrics", "system_metrics"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]

        conn.close()

        return {
            "database_path": str(self.db_path),
            "database_size_mb": round(db_size_mb, 2),
            "size_limit_mb": self.max_size_mb,
            "size_utilization_percent": round((db_size_mb / self.max_size_mb) * 100, 1),
            "retention_days": self.retention_days,
            "table_counts": counts,
            "healthy": db_size_mb < self.max_size_mb,
        }
