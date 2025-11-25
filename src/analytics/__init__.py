"""Analytics module for performance monitoring and metrics collection.

Provides comprehensive metrics collection, storage, and analysis for all
optimisation features in ragged.

v0.6.4 OPTIMISE-004: Performance Analytics
"""

from ragged.analytics.collector import MetricsCollector, get_metrics_collector
from ragged.analytics.models import (
    CacheMetrics,
    ModelMetrics,
    QueryMetrics,
    RetrievalMetrics,
)
from ragged.analytics.queries import MetricsQuery, get_metrics_query
from ragged.analytics.storage import MetricsStorage

__all__ = [
    # Core
    "MetricsCollector",
    "get_metrics_collector",
    "MetricsStorage",
    # Queries
    "MetricsQuery",
    "get_metrics_query",
    # Models
    "QueryMetrics",
    "RetrievalMetrics",
    "ModelMetrics",
    "CacheMetrics",
]
