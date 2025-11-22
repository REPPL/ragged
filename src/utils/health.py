"""Comprehensive health check system with deep diagnostics.

v0.2.9: Enhanced health checks for proactive issue detection.
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    details: dict[str, Any] | None = None
    duration_ms: float = 0.0
    error: str | None = None

    def is_healthy(self) -> bool:
        """Check if result is healthy.

        Returns:
            True if healthy
        """
        return self.status == HealthStatus.HEALTHY

    def is_degraded(self) -> bool:
        """Check if result is degraded.

        Returns:
            True if degraded
        """
        return self.status == HealthStatus.DEGRADED

    def is_unhealthy(self) -> bool:
        """Check if result is unhealthy.

        Returns:
            True if unhealthy
        """
        return self.status == HealthStatus.UNHEALTHY


class HealthChecker:
    """Comprehensive health check system.

    Features:
    - Service connectivity checks (Ollama, ChromaDB)
    - Resource availability checks (memory, disk)
    - Performance validation (query latency, embedder speed)
    - Deep diagnostics (index integrity, cache health)

    Example:
        >>> checker = HealthChecker()
        >>> results = checker.run_all_checks(deep=True)
        >>> if all(r.is_healthy() for r in results):
        ...     print("All systems healthy!")
    """

    def __init__(self):
        """Initialize health checker."""
        self.settings = get_settings()

    def _time_check(self, check_func, *args, **kwargs) -> tuple[Any, float]:
        """Time a health check function.

        Args:
            check_func: Function to time
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tuple of (result, duration_ms)
        """
        start = time.time()
        result = check_func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        return result, duration_ms

    def check_ollama(self) -> HealthCheckResult:
        """Check Ollama service connectivity.

        Returns:
            Health check result
        """
        try:
            from src.generation.ollama_client import OllamaClient

            result, duration = self._time_check(
                lambda: OllamaClient().health_check()
            )

            if result:
                return HealthCheckResult(
                    name="ollama",
                    status=HealthStatus.HEALTHY,
                    message="Ollama service is running",
                    duration_ms=duration,
                )
            else:
                return HealthCheckResult(
                    name="ollama",
                    status=HealthStatus.UNHEALTHY,
                    message="Ollama service not responding",
                    duration_ms=duration,
                )
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return HealthCheckResult(
                name="ollama",
                status=HealthStatus.UNHEALTHY,
                message="Ollama health check failed",
                error=str(e),
            )

    def check_chromadb(self) -> HealthCheckResult:
        """Check ChromaDB connectivity and status.

        Returns:
            Health check result
        """
        try:
            from src.storage.vector_store import VectorStore

            store = VectorStore()
            result, duration = self._time_check(store.health_check)

            if result:
                count = store.count()
                return HealthCheckResult(
                    name="chromadb",
                    status=HealthStatus.HEALTHY,
                    message=f"ChromaDB is running ({count} chunks stored)",
                    details={"chunk_count": count},
                    duration_ms=duration,
                )
            else:
                return HealthCheckResult(
                    name="chromadb",
                    status=HealthStatus.UNHEALTHY,
                    message="ChromaDB not responding",
                    duration_ms=duration,
                )
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return HealthCheckResult(
                name="chromadb",
                status=HealthStatus.UNHEALTHY,
                message="ChromaDB health check failed",
                error=str(e),
            )

    def check_embedder(self) -> HealthCheckResult:
        """Check embedder initialization and performance.

        Returns:
            Health check result
        """
        try:
            from src.embeddings.factory import get_embedder

            # Time embedder initialization
            start = time.time()
            embedder = get_embedder()
            init_duration_ms = (time.time() - start) * 1000

            # Test embedding performance
            test_text = "Health check test"
            embed_start = time.time()
            embedder.embed_text(test_text)
            embed_duration_ms = (time.time() - embed_start) * 1000

            total_duration = init_duration_ms + embed_duration_ms

            # Check if initialization is fast enough (<500ms for warm start)
            if init_duration_ms > 500:
                status = HealthStatus.DEGRADED
                message = f"Embedder slow to initialize ({init_duration_ms:.0f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Embedder is healthy"

            return HealthCheckResult(
                name="embedder",
                status=status,
                message=message,
                details={
                    "init_time_ms": round(init_duration_ms, 2),
                    "embed_time_ms": round(embed_duration_ms, 2),
                },
                duration_ms=total_duration,
            )
        except Exception as e:
            logger.error(f"Embedder health check failed: {e}")
            return HealthCheckResult(
                name="embedder",
                status=HealthStatus.UNHEALTHY,
                message="Embedder health check failed",
                error=str(e),
            )

    def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space.

        Returns:
            Health check result
        """
        try:
            # Check disk space for data directory
            data_dir = Path.home() / ".ragged"
            usage = psutil.disk_usage(str(data_dir.parent))

            free_gb = usage.free / (1024 ** 3)
            percent_used = usage.percent

            # Thresholds: <1GB = unhealthy, <5GB = degraded
            if free_gb < 1:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_gb:.1f}GB free ({percent_used}% used)"
            elif free_gb < 5:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {free_gb:.1f}GB free ({percent_used}% used)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient disk space ({free_gb:.1f}GB free)"

            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=message,
                details={
                    "free_gb": round(free_gb, 2),
                    "percent_used": percent_used,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                },
            )
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message="Disk space check failed",
                error=str(e),
            )

    def check_memory_available(self) -> HealthCheckResult:
        """Check available memory.

        Returns:
            Health check result
        """
        try:
            memory = psutil.virtual_memory()

            available_gb = memory.available / (1024 ** 3)
            percent_used = memory.percent

            # Thresholds: <512MB = unhealthy, <2GB = degraded
            if available_gb < 0.5:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {available_gb:.1f}GB available ({percent_used}% used)"
            elif available_gb < 2:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {available_gb:.1f}GB available ({percent_used}% used)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient memory ({available_gb:.1f}GB available)"

            return HealthCheckResult(
                name="memory",
                status=status,
                message=message,
                details={
                    "available_gb": round(available_gb, 2),
                    "percent_used": percent_used,
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                },
            )
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message="Memory check failed",
                error=str(e),
            )

    def check_cache_status(self) -> HealthCheckResult:
        """Check cache system health.

        Returns:
            Health check result
        """
        try:
            # Check if embedder caching is enabled and working
            from src.config.settings import get_settings

            settings = get_settings()

            if not settings.feature_flags.enable_embedder_caching:
                return HealthCheckResult(
                    name="cache",
                    status=HealthStatus.DEGRADED,
                    message="Embedder caching is disabled",
                    details={"caching_enabled": False},
                )

            # Check if cache is populated
            from src.embeddings.factory import _embedder_cache

            cache_size = len(_embedder_cache)

            if cache_size > 0:
                status = HealthStatus.HEALTHY
                message = f"Cache is healthy ({cache_size} embedders cached)"
            else:
                status = HealthStatus.DEGRADED
                message = "Cache is empty (cold start)"

            return HealthCheckResult(
                name="cache",
                status=status,
                message=message,
                details={
                    "caching_enabled": True,
                    "cached_embedders": cache_size,
                },
            )
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return HealthCheckResult(
                name="cache",
                status=HealthStatus.UNKNOWN,
                message="Cache check failed",
                error=str(e),
            )

    def check_query_performance(self) -> HealthCheckResult:
        """Deep check: Run test query and validate performance.

        Returns:
            Health check result
        """
        try:
            from src.embeddings.factory import get_embedder
            from src.storage.vector_store import VectorStore

            store = VectorStore()

            # Skip if no data
            if store.count() == 0:
                return HealthCheckResult(
                    name="query_performance",
                    status=HealthStatus.DEGRADED,
                    message="Cannot test query performance (no data indexed)",
                    details={"skipped": True},
                )

            # Run test query
            embedder = get_embedder()
            test_query = "test query for health check"

            start = time.time()
            query_embedding = embedder.embed_text(test_query)
            results = store.query(query_embedding=query_embedding, n_results=5)
            query_duration_ms = (time.time() - start) * 1000

            # Performance threshold: <500ms = healthy, <1000ms = degraded
            if query_duration_ms < 500:
                status = HealthStatus.HEALTHY
                message = f"Query performance is excellent ({query_duration_ms:.0f}ms)"
            elif query_duration_ms < 1000:
                status = HealthStatus.DEGRADED
                message = f"Query performance is acceptable ({query_duration_ms:.0f}ms)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Query performance is slow ({query_duration_ms:.0f}ms)"

            return HealthCheckResult(
                name="query_performance",
                status=status,
                message=message,
                details={
                    "query_time_ms": round(query_duration_ms, 2),
                    "results_returned": len(results.get("ids", [])),
                },
                duration_ms=query_duration_ms,
            )
        except Exception as e:
            logger.error(f"Query performance check failed: {e}")
            return HealthCheckResult(
                name="query_performance",
                status=HealthStatus.UNHEALTHY,
                message="Query performance check failed",
                error=str(e),
            )

    def check_index_integrity(self) -> HealthCheckResult:
        """Deep check: Validate index integrity.

        Returns:
            Health check result
        """
        try:
            from src.storage.vector_store import VectorStore

            store = VectorStore()
            count = store.count()

            if count == 0:
                return HealthCheckResult(
                    name="index_integrity",
                    status=HealthStatus.HEALTHY,
                    message="Index is empty (no integrity issues)",
                    details={"chunk_count": 0},
                )

            # Sample some documents to verify metadata
            sample = store.query(query_embedding=None, n_results=min(10, count))

            if not sample or not sample.get("ids"):
                return HealthCheckResult(
                    name="index_integrity",
                    status=HealthStatus.UNHEALTHY,
                    message="Index query returned no results",
                )

            # Verify metadata structure
            metadatas = sample.get("metadatas", [])
            if not metadatas:
                return HealthCheckResult(
                    name="index_integrity",
                    status=HealthStatus.DEGRADED,
                    message="Index missing metadata",
                    details={"chunk_count": count},
                )

            # Check for required metadata fields
            required_fields = {"document_id", "chunk_index"}
            sample_metadata = metadatas[0]
            missing_fields = required_fields - set(sample_metadata.keys())

            if missing_fields:
                status = HealthStatus.DEGRADED
                message = f"Index metadata missing fields: {missing_fields}"
            else:
                status = HealthStatus.HEALTHY
                message = "Index integrity is good"

            return HealthCheckResult(
                name="index_integrity",
                status=status,
                message=message,
                details={
                    "chunk_count": count,
                    "sample_size": len(metadatas),
                },
            )
        except Exception as e:
            logger.error(f"Index integrity check failed: {e}")
            return HealthCheckResult(
                name="index_integrity",
                status=HealthStatus.UNHEALTHY,
                message="Index integrity check failed",
                error=str(e),
            )

    def check_network_latency(self) -> HealthCheckResult:
        """Deep check: Check network latency to services.

        Returns:
            Health check result
        """
        try:
            from src.generation.ollama_client import OllamaClient

            client = OllamaClient()

            # Time a simple health check request
            start = time.time()
            client.health_check()
            latency_ms = (time.time() - start) * 1000

            # Thresholds: <100ms = healthy, <500ms = degraded
            if latency_ms < 100:
                status = HealthStatus.HEALTHY
                message = f"Network latency is excellent ({latency_ms:.0f}ms)"
            elif latency_ms < 500:
                status = HealthStatus.DEGRADED
                message = f"Network latency is acceptable ({latency_ms:.0f}ms)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Network latency is high ({latency_ms:.0f}ms)"

            return HealthCheckResult(
                name="network_latency",
                status=status,
                message=message,
                details={"latency_ms": round(latency_ms, 2)},
                duration_ms=latency_ms,
            )
        except Exception as e:
            logger.error(f"Network latency check failed: {e}")
            return HealthCheckResult(
                name="network_latency",
                status=HealthStatus.UNHEALTHY,
                message="Network latency check failed",
                error=str(e),
            )

    def run_basic_checks(self) -> list[HealthCheckResult]:
        """Run basic health checks.

        Returns:
            List of health check results
        """
        return [
            self.check_ollama(),
            self.check_chromadb(),
            self.check_embedder(),
            self.check_disk_space(),
            self.check_memory_available(),
            self.check_cache_status(),
        ]

    def run_deep_checks(self) -> list[HealthCheckResult]:
        """Run deep diagnostic checks.

        Returns:
            List of health check results
        """
        return [
            self.check_query_performance(),
            self.check_index_integrity(),
            self.check_network_latency(),
        ]

    def run_all_checks(self, deep: bool = False) -> list[HealthCheckResult]:
        """Run all health checks.

        Args:
            deep: Include deep diagnostic checks

        Returns:
            List of all health check results
        """
        results = self.run_basic_checks()

        if deep:
            results.extend(self.run_deep_checks())

        return results
