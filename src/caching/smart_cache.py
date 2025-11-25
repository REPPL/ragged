"""Smart caching with frequency tracking and predictive features.

Provides intelligent caching enhancements including access pattern tracking,
query similarity matching, predictive caching, and cache warming.

v0.6.4 OPTIMISE-005 Phase 3: Smart Caching Logic
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AccessPattern:
    """Access pattern for a cache key."""

    key: str
    access_count: int = 0
    last_access: Optional[datetime] = None
    first_access: Optional[datetime] = None
    access_times: list[datetime] = field(default_factory=list)

    def record_access(self) -> None:
        """Record an access to this key."""
        now = datetime.now()
        self.access_count += 1
        self.last_access = now
        if self.first_access is None:
            self.first_access = now
        self.access_times.append(now)

        # Keep only last 100 access times to avoid memory bloat
        if len(self.access_times) > 100:
            self.access_times = self.access_times[-100:]

    def get_access_frequency(self, window_seconds: int = 3600) -> float:
        """Get access frequency (accesses per second) in time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Accesses per second in the window
        """
        if not self.access_times:
            return 0.0

        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        recent_accesses = [t for t in self.access_times if t >= cutoff]

        if not recent_accesses:
            return 0.0

        time_span = (datetime.now() - recent_accesses[0]).total_seconds()
        if time_span == 0:
            return float(len(recent_accesses))

        return len(recent_accesses) / time_span


@dataclass
class QueryPattern:
    """Pattern of query sequences for predictive caching."""

    query_hash: str
    following_queries: dict[str, int] = field(default_factory=dict)
    total_follows: int = 0

    def record_follow(self, next_query_hash: str) -> None:
        """Record a query that followed this one.

        Args:
            next_query_hash: Hash of the query that followed
        """
        self.following_queries[next_query_hash] = (
            self.following_queries.get(next_query_hash, 0) + 1
        )
        self.total_follows += 1

    def get_predictions(self, min_confidence: float = 0.2) -> list[tuple[str, float]]:
        """Get predicted next queries with confidence scores.

        Args:
            min_confidence: Minimum confidence threshold (0-1)

        Returns:
            List of (query_hash, confidence) tuples
        """
        if self.total_follows == 0:
            return []

        predictions = []
        for query_hash, count in self.following_queries.items():
            confidence = count / self.total_follows
            if confidence >= min_confidence:
                predictions.append((query_hash, confidence))

        return sorted(predictions, key=lambda x: x[1], reverse=True)


class FrequencyTracker:
    """Track access frequencies for cache optimization."""

    def __init__(self, max_patterns: int = 10000):
        """Initialise frequency tracker.

        Args:
            max_patterns: Maximum number of access patterns to track
        """
        self.max_patterns = max_patterns
        self.patterns: dict[str, AccessPattern] = {}
        self.query_sequences: list[str] = []  # Track query sequence for prediction
        self.query_patterns: dict[str, QueryPattern] = {}

    def record_access(self, key: str) -> None:
        """Record a cache access.

        Args:
            key: Cache key that was accessed
        """
        # Update access pattern
        if key not in self.patterns:
            if len(self.patterns) >= self.max_patterns:
                # Evict least accessed pattern
                self._evict_least_accessed()
            self.patterns[key] = AccessPattern(key=key)

        self.patterns[key].record_access()

        # Record query sequence for prediction
        if len(self.query_sequences) > 0:
            prev_key = self.query_sequences[-1]

            if prev_key not in self.query_patterns:
                self.query_patterns[prev_key] = QueryPattern(query_hash=prev_key)

            self.query_patterns[prev_key].record_follow(key)

        self.query_sequences.append(key)

        # Keep only last 1000 queries in sequence
        if len(self.query_sequences) > 1000:
            self.query_sequences = self.query_sequences[-1000:]

    def _evict_least_accessed(self) -> None:
        """Evict the least accessed pattern."""
        if not self.patterns:
            return

        # Find least accessed key
        least_accessed_key = min(
            self.patterns.keys(), key=lambda k: self.patterns[k].access_count
        )
        del self.patterns[least_accessed_key]

    def get_hot_keys(self, top_n: int = 100, window_seconds: int = 3600) -> list[str]:
        """Get the hottest (most frequently accessed) cache keys.

        Args:
            top_n: Number of hot keys to return
            window_seconds: Time window for frequency calculation

        Returns:
            List of hot cache keys
        """
        key_frequencies = [
            (key, pattern.get_access_frequency(window_seconds))
            for key, pattern in self.patterns.items()
        ]

        key_frequencies.sort(key=lambda x: x[1], reverse=True)
        return [key for key, _ in key_frequencies[:top_n]]

    def get_predictions(self, current_key: str, max_predictions: int = 5) -> list[str]:
        """Predict likely next queries based on current query.

        Args:
            current_key: Current cache key
            max_predictions: Maximum number of predictions

        Returns:
            List of predicted cache keys
        """
        if current_key not in self.query_patterns:
            return []

        predictions = self.query_patterns[current_key].get_predictions()
        return [query_hash for query_hash, _ in predictions[:max_predictions]]

    def get_stats(self) -> dict[str, Any]:
        """Get frequency tracking statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_patterns": len(self.patterns),
            "total_accesses": sum(p.access_count for p in self.patterns.values()),
            "tracked_sequences": len(self.query_sequences),
            "prediction_patterns": len(self.query_patterns),
        }


class SimilarityMatcher:
    """Match similar queries for cache serving."""

    def __init__(self, similarity_threshold: float = 0.8):
        """Initialise similarity matcher.

        Args:
            similarity_threshold: Minimum similarity score (0-1) for matches
        """
        self.similarity_threshold = similarity_threshold
        self.query_hashes: dict[str, str] = {}  # cache_key -> query_text

    def register_query(self, cache_key: str, query: str) -> None:
        """Register a query with its cache key.

        Args:
            cache_key: Cache key
            query: Original query text
        """
        self.query_hashes[cache_key] = query.lower().strip()

    def find_similar(
        self, query: str, top_n: int = 5
    ) -> list[tuple[str, float]]:
        """Find similar cached queries.

        Args:
            query: Query text to match
            top_n: Maximum number of similar queries to return

        Returns:
            List of (cache_key, similarity_score) tuples
        """
        query_normalized = query.lower().strip()
        similarities = []

        for cache_key, cached_query in self.query_hashes.items():
            similarity = self._calculate_similarity(query_normalized, cached_query)
            if similarity >= self.similarity_threshold:
                similarities.append((cache_key, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries.

        Uses simple word overlap ratio for efficiency.

        Args:
            query1: First query
            query2: Second query

        Returns:
            Similarity score (0-1)
        """
        # Simple word-based similarity (Jaccard similarity)
        words1 = set(query1.split())
        words2 = set(query2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)


class CacheWarmer:
    """Warm cache with frequently accessed queries on startup."""

    def __init__(self, frequency_tracker: FrequencyTracker):
        """Initialise cache warmer.

        Args:
            frequency_tracker: Frequency tracker for identifying hot queries
        """
        self.frequency_tracker = frequency_tracker

    def get_warmup_keys(self, max_keys: int = 100) -> list[str]:
        """Get cache keys that should be warmed up.

        Args:
            max_keys: Maximum number of keys to warm up

        Returns:
            List of cache keys to warm up
        """
        # Get hot keys from frequency tracker
        hot_keys = self.frequency_tracker.get_hot_keys(top_n=max_keys)

        logger.info(f"Cache warmer identified {len(hot_keys)} keys for warmup")
        return hot_keys

    def should_warm(self, key: str) -> bool:
        """Check if a key should be warmed up.

        Args:
            key: Cache key

        Returns:
            True if key should be warmed
        """
        pattern = self.frequency_tracker.patterns.get(key)
        if not pattern:
            return False

        # Warm if accessed frequently in the past
        frequency = pattern.get_access_frequency(window_seconds=86400)  # 24h window
        return frequency > 0.001  # More than 1 access per 1000 seconds


class SmartCache:
    """Smart cache with frequency tracking and predictive features."""

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        enable_prediction: bool = True,
        enable_similarity: bool = True,
    ):
        """Initialise smart cache.

        Args:
            similarity_threshold: Minimum similarity for query matching
            enable_prediction: Enable predictive caching
            enable_similarity: Enable similarity-based cache serving
        """
        self.frequency_tracker = FrequencyTracker()
        self.similarity_matcher = SimilarityMatcher(similarity_threshold)
        self.cache_warmer = CacheWarmer(self.frequency_tracker)
        self.enable_prediction = enable_prediction
        self.enable_similarity = enable_similarity

    def record_access(self, cache_key: str, query: Optional[str] = None) -> None:
        """Record a cache access.

        Args:
            cache_key: Cache key that was accessed
            query: Original query text (for similarity matching)
        """
        self.frequency_tracker.record_access(cache_key)

        if query and self.enable_similarity:
            self.similarity_matcher.register_query(cache_key, query)

    def get_predictions(self, current_key: str) -> list[str]:
        """Get predicted next cache keys.

        Args:
            current_key: Current cache key

        Returns:
            List of predicted keys to pre-cache
        """
        if not self.enable_prediction:
            return []

        return self.frequency_tracker.get_predictions(current_key)

    def find_similar(self, query: str) -> list[tuple[str, float]]:
        """Find similar cached queries.

        Args:
            query: Query to match

        Returns:
            List of (cache_key, similarity) tuples
        """
        if not self.enable_similarity:
            return []

        return self.similarity_matcher.find_similar(query)

    def get_hot_keys(self, top_n: int = 100) -> list[str]:
        """Get hot cache keys for prioritization.

        Args:
            top_n: Number of keys to return

        Returns:
            List of hot cache keys
        """
        return self.frequency_tracker.get_hot_keys(top_n)

    def get_warmup_keys(self, max_keys: int = 100) -> list[str]:
        """Get keys for cache warming.

        Args:
            max_keys: Maximum keys to warm

        Returns:
            List of keys to warm up
        """
        return self.cache_warmer.get_warmup_keys(max_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get smart cache statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "frequency_tracking": self.frequency_tracker.get_stats(),
            "similarity_matching": {
                "registered_queries": len(self.similarity_matcher.query_hashes),
                "enabled": self.enable_similarity,
            },
            "prediction": {
                "enabled": self.enable_prediction,
                "patterns": len(self.frequency_tracker.query_patterns),
            },
        }
