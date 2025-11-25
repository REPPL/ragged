"""Analytics module for performance monitoring and metrics collection.

Provides comprehensive metrics collection, storage, and analysis for all
optimisation features in ragged.

v0.6.4 OPTIMISE-004: Performance Analytics
v0.7.2: Extended analytics (similarity, query performance, storage)
"""

from ragged.analytics.collector import MetricsCollector, get_metrics_collector
from ragged.analytics.export import (
    ASCIIVisualiser,
    MetricsExporter,
    export_query_metrics_to_csv,
    export_summary_to_json,
    visualise_cache_effectiveness,
    visualise_latency_distribution,
    visualise_model_usage,
)
from ragged.analytics.models import (
    CacheMetrics,
    ModelMetrics,
    QueryMetrics,
    RetrievalMetrics,
)
from ragged.analytics.queries import MetricsQuery, get_metrics_query
from ragged.analytics.storage import MetricsStorage

# v0.7.2: Extended analytics modules
from ragged.analytics.similarity import (
    SimilarityAnalytics,
    SimilarityCalculator,
    ClusterDetector,
    SimilarityGraph,
    SimilarityEdge,
    DocumentNode,
    SimilarityCluster,
    get_similarity_analytics,
)
from ragged.analytics.query_performance import (
    QueryPerformanceAnalytics,
    QueryPerformanceTracker,
    PerformanceAggregator,
    AnomalyDetector,
    QueryRecord,
    PerformanceMetrics,
    PerformanceAnomaly,
    AggregationPeriod,
    get_query_performance_analytics,
)
from ragged.analytics.storage_analytics import (
    StorageAnalytics,
    StorageScanner,
    GrowthProjector,
    CleanupRecommender,
    StorageReport,
    StorageCategory,
    StorageItem,
    get_storage_analytics,
)

__all__ = [
    # Core
    "MetricsCollector",
    "get_metrics_collector",
    "MetricsStorage",
    # Queries
    "MetricsQuery",
    "get_metrics_query",
    # Export
    "MetricsExporter",
    "ASCIIVisualiser",
    "export_summary_to_json",
    "export_query_metrics_to_csv",
    "visualise_latency_distribution",
    "visualise_model_usage",
    "visualise_cache_effectiveness",
    # Models
    "QueryMetrics",
    "RetrievalMetrics",
    "ModelMetrics",
    "CacheMetrics",
    # v0.7.2: Similarity Analytics
    "SimilarityAnalytics",
    "SimilarityCalculator",
    "ClusterDetector",
    "SimilarityGraph",
    "SimilarityEdge",
    "DocumentNode",
    "SimilarityCluster",
    "get_similarity_analytics",
    # v0.7.2: Query Performance Analytics
    "QueryPerformanceAnalytics",
    "QueryPerformanceTracker",
    "PerformanceAggregator",
    "AnomalyDetector",
    "QueryRecord",
    "PerformanceMetrics",
    "PerformanceAnomaly",
    "AggregationPeriod",
    "get_query_performance_analytics",
    # v0.7.2: Storage Analytics
    "StorageAnalytics",
    "StorageScanner",
    "GrowthProjector",
    "CleanupRecommender",
    "StorageReport",
    "StorageCategory",
    "StorageItem",
    "get_storage_analytics",
]
