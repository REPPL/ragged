"""Data models for analytics metrics.

v0.6.4 OPTIMISE-004 Phase 1: Metrics Collection Framework
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QueryMetrics:
    """Metrics for a single query execution.

    Tracks comprehensive performance and behavior metrics.
    """

    # Identity (required)
    query_id: str  # Unique query execution ID
    query_hash: str  # Hash of query content
    timestamp: datetime
    query_length: int
    total_latency_ms: float

    # Query characteristics (optional)
    query_type: Optional[str] = None  # From v0.6.1 classification
    complexity: Optional[int] = None  # From v0.6.1 (1-10)
    domain: Optional[str] = None  # From v0.6.3 detection

    # Performance (optional)
    classification_latency_ms: Optional[float] = None
    routing_latency_ms: Optional[float] = None
    retrieval_latency_ms: Optional[float] = None
    llm_latency_ms: Optional[float] = None

    # Model routing
    selected_model: Optional[str] = None  # From v0.6.2
    routing_reason: Optional[str] = None

    # Cache
    cache_hit: bool = False
    cache_layer: Optional[str] = None  # Which cache layer hit

    # Status
    success: bool = True
    error_type: Optional[str] = None

    # Additional context
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval operations.

    Tracks retrieval quality and performance.
    """

    # Identity (required)
    retrieval_id: str
    query_id: str  # Links to QueryMetrics
    timestamp: datetime
    k: int  # Number of results requested
    retrieval_latency_ms: float
    results_count: int
    avg_score: float  # Average relevance score

    # Retrieval configuration (optional)
    domain: Optional[str] = None  # Domain-aware retrieval
    filter_metadata: Optional[dict] = None

    # Performance (optional)
    embedding_latency_ms: Optional[float] = None
    search_latency_ms: Optional[float] = None
    reranking_latency_ms: Optional[float] = None
    domain_boost_applied: bool = False  # From v0.6.3

    # Quality (if ground truth available)
    precision_at_k: Optional[float] = None
    recall_at_k: Optional[float] = None

    # Additional context
    metadata: dict = field(default_factory=dict)


@dataclass
class ModelMetrics:
    """Metrics for model usage and performance.

    Tracks model selection frequency and performance characteristics.
    """

    # Identity
    model_id: str  # e.g., "llama3.2:3b", "llama3.2:70b"
    timestamp: datetime

    # Usage
    invocation_count: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0

    # Tokens
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_tokens_per_query: float = 0.0

    # GPU (if applicable)
    gpu_memory_used_mb: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None
    gpu_temperature_celsius: Optional[float] = None

    # Quality
    average_quality_score: Optional[float] = None  # User feedback if available

    # Additional context
    metadata: dict = field(default_factory=dict)


@dataclass
class CacheMetrics:
    """Metrics for cache performance and effectiveness.

    Tracks cache hit rates, memory usage, and effectiveness.
    """

    # Identity
    cache_layer: str  # e.g., "query_classification", "retrieval_results"
    timestamp: datetime

    # Hit rates
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0

    # Performance
    avg_hit_latency_ms: float = 0.0
    avg_miss_latency_ms: float = 0.0
    latency_saved_ms: float = 0.0  # Total latency saved by caching

    # Memory
    cache_size_entries: int = 0
    cache_size_bytes: int = 0
    cache_size_mb: float = 0.0

    # Evictions
    eviction_count: int = 0
    eviction_reason: Optional[str] = None  # "ttl", "lru", "size_limit"

    # Additional context
    metadata: dict = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-wide resource utilization metrics.

    Tracks overall system health and resource usage.
    """

    # Identity
    timestamp: datetime

    # Memory
    system_memory_used_mb: float
    system_memory_available_mb: float
    system_memory_percent: float

    # CPU
    cpu_percent: float
    cpu_count: int

    # Disk (for analytics database)
    analytics_db_size_mb: float
    analytics_db_path: str

    # Process
    process_memory_mb: float
    process_threads: int

    # Additional context
    metadata: dict = field(default_factory=dict)
