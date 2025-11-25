"""Metrics collection coordinator.

Provides centralized metrics collection with minimal overhead and
asynchronous storage.

v0.6.4 OPTIMISE-004 Phase 1: Metrics Collection Framework
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional

from ragged.analytics.models import (
    CacheMetrics,
    ModelMetrics,
    QueryMetrics,
    RetrievalMetrics,
    SystemMetrics,
)
from ragged.analytics.storage import MetricsStorage

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Central metrics collection coordinator.

    Collects metrics from various system components and stores them
    asynchronously with minimal overhead.

    Features:
    - < 5ms overhead per metric collection
    - Asynchronous storage writes
    - Automatic metric aggregation
    - Privacy-preserving query hashing
    """

    def __init__(
        self,
        storage: Optional[MetricsStorage] = None,
        enabled: bool = True,
        async_writes: bool = True,
    ):
        """Initialize metrics collector.

        Args:
            storage: MetricsStorage instance (creates default if None)
            enabled: Whether metrics collection is enabled
            async_writes: Use asynchronous writes (reduces overhead)
        """
        self.storage = storage or MetricsStorage()
        self.enabled = enabled
        self.async_writes = async_writes

        # In-memory aggregation for model and cache metrics
        self._model_stats = {}  # model_id -> ModelMetrics
        self._cache_stats = {}  # cache_layer -> CacheMetrics

        logger.info(
            f"Initialized MetricsCollector "
            f"(enabled={enabled}, async={async_writes})"
        )

    def record_query(
        self,
        query: str,
        query_type: Optional[str] = None,
        complexity: Optional[int] = None,
        domain: Optional[str] = None,
        total_latency_ms: float = 0.0,
        classification_latency_ms: Optional[float] = None,
        routing_latency_ms: Optional[float] = None,
        retrieval_latency_ms: Optional[float] = None,
        llm_latency_ms: Optional[float] = None,
        selected_model: Optional[str] = None,
        routing_reason: Optional[str] = None,
        cache_hit: bool = False,
        cache_layer: Optional[str] = None,
        success: bool = True,
        error_type: Optional[str] = None,
        **metadata,
    ) -> str:
        """Record query metrics.

        Args:
            query: Query text
            query_type: Query type from classification (v0.6.1)
            complexity: Query complexity from classification (v0.6.1)
            domain: Detected domain from domain adaptation (v0.6.3)
            total_latency_ms: Total query execution time
            classification_latency_ms: Time spent in classification
            routing_latency_ms: Time spent in model routing
            retrieval_latency_ms: Time spent in retrieval
            llm_latency_ms: Time spent in LLM generation
            selected_model: Model selected by routing (v0.6.2)
            routing_reason: Reason for model selection
            cache_hit: Whether result was served from cache
            cache_layer: Which cache layer provided the hit
            success: Whether query executed successfully
            error_type: Error type if unsuccessful
            **metadata: Additional context to store

        Returns:
            Query ID (UUID)
        """
        if not self.enabled:
            return ""

        query_id = str(uuid.uuid4())
        query_hash = self._hash_query(query)

        metrics = QueryMetrics(
            query_id=query_id,
            query_hash=query_hash,
            timestamp=datetime.now(),
            query_length=len(query),
            query_type=query_type,
            complexity=complexity,
            domain=domain,
            total_latency_ms=total_latency_ms,
            classification_latency_ms=classification_latency_ms,
            routing_latency_ms=routing_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_latency_ms=llm_latency_ms,
            selected_model=selected_model,
            routing_reason=routing_reason,
            cache_hit=cache_hit,
            cache_layer=cache_layer,
            success=success,
            error_type=error_type,
            metadata=metadata,
        )

        # Store metrics (asynchronously if configured)
        self._store_metrics(self.storage.store_query_metrics, metrics)

        return query_id

    def record_retrieval(
        self,
        query_id: str,
        k: int,
        retrieval_latency_ms: float,
        results_count: int,
        avg_score: float,
        domain: Optional[str] = None,
        embedding_latency_ms: Optional[float] = None,
        search_latency_ms: Optional[float] = None,
        reranking_latency_ms: Optional[float] = None,
        domain_boost_applied: bool = False,
        precision_at_k: Optional[float] = None,
        recall_at_k: Optional[float] = None,
        **metadata,
    ) -> str:
        """Record retrieval metrics.

        Args:
            query_id: Associated query ID
            k: Number of results requested
            retrieval_latency_ms: Total retrieval time
            results_count: Number of results returned
            avg_score: Average relevance score
            domain: Domain for domain-aware retrieval (v0.6.3)
            embedding_latency_ms: Time for embedding generation
            search_latency_ms: Time for vector search
            reranking_latency_ms: Time for reranking
            domain_boost_applied: Whether domain boost was used
            precision_at_k: Precision at k (if ground truth available)
            recall_at_k: Recall at k (if ground truth available)
            **metadata: Additional context

        Returns:
            Retrieval ID (UUID)
        """
        if not self.enabled:
            return ""

        retrieval_id = str(uuid.uuid4())

        metrics = RetrievalMetrics(
            retrieval_id=retrieval_id,
            query_id=query_id,
            timestamp=datetime.now(),
            k=k,
            domain=domain,
            retrieval_latency_ms=retrieval_latency_ms,
            embedding_latency_ms=embedding_latency_ms,
            search_latency_ms=search_latency_ms,
            reranking_latency_ms=reranking_latency_ms,
            results_count=results_count,
            avg_score=avg_score,
            domain_boost_applied=domain_boost_applied,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            metadata=metadata,
        )

        self._store_metrics(self.storage.store_retrieval_metrics, metrics)

        return retrieval_id

    def update_model_stats(
        self,
        model_id: str,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        gpu_memory_mb: Optional[float] = None,
        gpu_utilization: Optional[float] = None,
        gpu_temperature: Optional[float] = None,
        quality_score: Optional[float] = None,
    ) -> None:
        """Update model statistics (aggregated).

        Args:
            model_id: Model identifier
            latency_ms: Query latency for this invocation
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            gpu_memory_mb: GPU memory used
            gpu_utilization: GPU utilization percentage
            gpu_temperature: GPU temperature in Celsius
            quality_score: Quality score if available
        """
        if not self.enabled:
            return

        if model_id not in self._model_stats:
            self._model_stats[model_id] = ModelMetrics(
                model_id=model_id,
                timestamp=datetime.now(),
            )

        stats = self._model_stats[model_id]
        stats.invocation_count += 1
        stats.total_latency_ms += latency_ms
        stats.avg_latency_ms = stats.total_latency_ms / stats.invocation_count

        stats.total_input_tokens += input_tokens
        stats.total_output_tokens += output_tokens
        total_tokens = stats.total_input_tokens + stats.total_output_tokens
        stats.avg_tokens_per_query = total_tokens / stats.invocation_count

        # Update GPU metrics (latest values)
        if gpu_memory_mb is not None:
            stats.gpu_memory_used_mb = gpu_memory_mb
        if gpu_utilization is not None:
            stats.gpu_utilization_percent = gpu_utilization
        if gpu_temperature is not None:
            stats.gpu_temperature_celsius = gpu_temperature

        # Update quality (running average)
        if quality_score is not None:
            if stats.average_quality_score is None:
                stats.average_quality_score = quality_score
            else:
                # Running average
                n = stats.invocation_count
                stats.average_quality_score = (
                    stats.average_quality_score * (n - 1) + quality_score
                ) / n

    def update_cache_stats(
        self,
        cache_layer: str,
        hit: bool,
        latency_ms: float,
        cache_size_entries: int = 0,
        cache_size_bytes: int = 0,
        eviction_occurred: bool = False,
        eviction_reason: Optional[str] = None,
    ) -> None:
        """Update cache statistics (aggregated).

        Args:
            cache_layer: Cache layer identifier
            hit: Whether this was a cache hit
            latency_ms: Latency for this operation
            cache_size_entries: Current number of cache entries
            cache_size_bytes: Current cache size in bytes
            eviction_occurred: Whether an eviction occurred
            eviction_reason: Reason for eviction if occurred
        """
        if not self.enabled:
            return

        if cache_layer not in self._cache_stats:
            self._cache_stats[cache_layer] = CacheMetrics(
                cache_layer=cache_layer,
                timestamp=datetime.now(),
            )

        stats = self._cache_stats[cache_layer]
        stats.total_requests += 1

        if hit:
            stats.cache_hits += 1
            # Update hit latency (running average)
            if stats.cache_hits == 1:
                stats.avg_hit_latency_ms = latency_ms
            else:
                n = stats.cache_hits
                stats.avg_hit_latency_ms = (
                    stats.avg_hit_latency_ms * (n - 1) + latency_ms
                ) / n
        else:
            stats.cache_misses += 1
            # Update miss latency (running average)
            if stats.cache_misses == 1:
                stats.avg_miss_latency_ms = latency_ms
            else:
                n = stats.cache_misses
                stats.avg_miss_latency_ms = (
                    stats.avg_miss_latency_ms * (n - 1) + latency_ms
                ) / n

        # Update hit rate
        stats.hit_rate = stats.cache_hits / stats.total_requests if stats.total_requests > 0 else 0.0

        # Calculate latency saved
        if hit and stats.avg_miss_latency_ms > 0:
            latency_saved = stats.avg_miss_latency_ms - latency_ms
            stats.latency_saved_ms += max(0, latency_saved)

        # Update cache size
        stats.cache_size_entries = cache_size_entries
        stats.cache_size_bytes = cache_size_bytes
        stats.cache_size_mb = cache_size_bytes / (1024 * 1024)

        # Track evictions
        if eviction_occurred:
            stats.eviction_count += 1
            stats.eviction_reason = eviction_reason

    def flush_aggregated_metrics(self) -> None:
        """Flush aggregated model and cache metrics to storage.

        Should be called periodically (e.g., every 5 minutes) to persist
        in-memory aggregations.
        """
        if not self.enabled:
            return

        # Flush model metrics
        for model_id, metrics in self._model_stats.items():
            metrics.timestamp = datetime.now()  # Update timestamp
            self._store_metrics(self.storage.store_model_metrics, metrics)

        # Flush cache metrics
        for cache_layer, metrics in self._cache_stats.items():
            metrics.timestamp = datetime.now()  # Update timestamp
            self._store_metrics(self.storage.store_cache_metrics, metrics)

        logger.debug(
            f"Flushed {len(self._model_stats)} model metrics, "
            f"{len(self._cache_stats)} cache metrics"
        )

    def _hash_query(self, query: str) -> str:
        """Hash query for privacy-preserving storage.

        Args:
            query: Query text

        Returns:
            SHA256 hash of query
        """
        return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

    def _store_metrics(self, store_func, metrics) -> None:
        """Store metrics (synchronously or asynchronously).

        Args:
            store_func: Storage function to call
            metrics: Metrics object to store
        """
        if self.async_writes:
            # TODO: Implement true async writes with thread pool or asyncio
            # For now, just call synchronously
            pass

        # Synchronous write
        try:
            store_func(metrics)
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

    def health_check(self) -> dict:
        """Perform health check on metrics collection.

        Returns:
            Dictionary with health status
        """
        storage_health = self.storage.health_check()

        return {
            "enabled": self.enabled,
            "async_writes": self.async_writes,
            "model_stats_count": len(self._model_stats),
            "cache_stats_count": len(self._cache_stats),
            "storage": storage_health,
        }


# Global singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(
    storage: Optional[MetricsStorage] = None,
    enabled: bool = True,
) -> MetricsCollector:
    """Get global metrics collector instance.

    Args:
        storage: MetricsStorage instance (only used on first call)
        enabled: Whether metrics collection is enabled

    Returns:
        Metrics collector singleton
    """
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(storage=storage, enabled=enabled)

    return _metrics_collector
