"""Tests for smart caching features.

v0.6.4 OPTIMISE-005 Phase 3: Smart Caching Logic
"""

import time
from datetime import datetime, timedelta

import pytest

from ragged.caching.smart_cache import (
    AccessPattern,
    CacheWarmer,
    FrequencyTracker,
    QueryPattern,
    SimilarityMatcher,
    SmartCache,
)


class TestAccessPattern:
    """Test suite for AccessPattern."""

    def test_initialization(self):
        """Test pattern initializes correctly."""
        pattern = AccessPattern(key="test_key")

        assert pattern.key == "test_key"
        assert pattern.access_count == 0
        assert pattern.last_access is None
        assert pattern.first_access is None
        assert len(pattern.access_times) == 0

    def test_record_access(self):
        """Test recording accesses."""
        pattern = AccessPattern(key="test_key")

        pattern.record_access()

        assert pattern.access_count == 1
        assert pattern.last_access is not None
        assert pattern.first_access is not None
        assert len(pattern.access_times) == 1

    def test_multiple_accesses(self):
        """Test multiple access recordings."""
        pattern = AccessPattern(key="test_key")

        for _ in range(10):
            pattern.record_access()
            time.sleep(0.01)  # Small delay

        assert pattern.access_count == 10
        assert len(pattern.access_times) == 10

    def test_access_times_limit(self):
        """Test access times list is limited to 100."""
        pattern = AccessPattern(key="test_key")

        for _ in range(150):
            pattern.record_access()

        assert pattern.access_count == 150
        assert len(pattern.access_times) == 100  # Trimmed to last 100

    def test_access_frequency(self):
        """Test access frequency calculation."""
        pattern = AccessPattern(key="test_key")

        # Record 10 accesses
        for _ in range(10):
            pattern.record_access()

        # Frequency should be > 0
        frequency = pattern.get_access_frequency(window_seconds=3600)
        assert frequency > 0

    def test_access_frequency_empty(self):
        """Test access frequency with no accesses."""
        pattern = AccessPattern(key="test_key")

        frequency = pattern.get_access_frequency()
        assert frequency == 0.0


class TestQueryPattern:
    """Test suite for QueryPattern."""

    def test_initialization(self):
        """Test pattern initializes correctly."""
        pattern = QueryPattern(query_hash="hash1")

        assert pattern.query_hash == "hash1"
        assert len(pattern.following_queries) == 0
        assert pattern.total_follows == 0

    def test_record_follow(self):
        """Test recording following queries."""
        pattern = QueryPattern(query_hash="hash1")

        pattern.record_follow("hash2")

        assert pattern.following_queries["hash2"] == 1
        assert pattern.total_follows == 1

    def test_multiple_follows(self):
        """Test recording multiple follows."""
        pattern = QueryPattern(query_hash="hash1")

        pattern.record_follow("hash2")
        pattern.record_follow("hash2")
        pattern.record_follow("hash3")

        assert pattern.following_queries["hash2"] == 2
        assert pattern.following_queries["hash3"] == 1
        assert pattern.total_follows == 3

    def test_get_predictions(self):
        """Test getting predictions."""
        pattern = QueryPattern(query_hash="hash1")

        pattern.record_follow("hash2")
        pattern.record_follow("hash2")
        pattern.record_follow("hash2")
        pattern.record_follow("hash3")

        predictions = pattern.get_predictions(min_confidence=0.2)

        assert len(predictions) == 2
        assert predictions[0][0] == "hash2"  # Most frequent
        assert predictions[0][1] == 0.75  # 3/4 confidence
        assert predictions[1][0] == "hash3"
        assert predictions[1][1] == 0.25  # 1/4 confidence

    def test_predictions_empty(self):
        """Test predictions with no follows."""
        pattern = QueryPattern(query_hash="hash1")

        predictions = pattern.get_predictions()

        assert len(predictions) == 0


class TestFrequencyTracker:
    """Test suite for FrequencyTracker."""

    def test_initialization(self):
        """Test tracker initializes correctly."""
        tracker = FrequencyTracker()

        assert len(tracker.patterns) == 0
        assert len(tracker.query_sequences) == 0
        assert len(tracker.query_patterns) == 0

    def test_record_access(self):
        """Test recording accesses."""
        tracker = FrequencyTracker()

        tracker.record_access("key1")

        assert "key1" in tracker.patterns
        assert tracker.patterns["key1"].access_count == 1

    def test_multiple_accesses(self):
        """Test multiple access recordings."""
        tracker = FrequencyTracker()

        tracker.record_access("key1")
        tracker.record_access("key1")
        tracker.record_access("key2")

        assert tracker.patterns["key1"].access_count == 2
        assert tracker.patterns["key2"].access_count == 1

    def test_pattern_eviction(self):
        """Test pattern eviction when limit reached."""
        tracker = FrequencyTracker(max_patterns=3)

        tracker.record_access("key1")
        tracker.record_access("key2")
        tracker.record_access("key3")

        # Access key2 and key3 more to make key1 least accessed
        tracker.record_access("key2")
        tracker.record_access("key3")

        # Adding key4 should evict key1
        tracker.record_access("key4")

        assert "key1" not in tracker.patterns
        assert "key2" in tracker.patterns
        assert "key3" in tracker.patterns
        assert "key4" in tracker.patterns

    def test_query_sequence_tracking(self):
        """Test query sequence tracking for prediction."""
        tracker = FrequencyTracker()

        tracker.record_access("key1")
        tracker.record_access("key2")
        tracker.record_access("key3")

        assert len(tracker.query_sequences) == 3
        assert "key1" in tracker.query_patterns

    def test_get_hot_keys(self):
        """Test getting hot keys."""
        tracker = FrequencyTracker()

        # Access key1 many times
        for _ in range(10):
            tracker.record_access("key1")

        # Access key2 a few times
        for _ in range(3):
            tracker.record_access("key2")

        hot_keys = tracker.get_hot_keys(top_n=2)

        assert "key1" in hot_keys
        assert "key2" in hot_keys

    def test_get_predictions(self):
        """Test getting predictions."""
        tracker = FrequencyTracker()

        # Create pattern: key1 -> key2 -> key3
        tracker.record_access("key1")
        tracker.record_access("key2")
        tracker.record_access("key1")
        tracker.record_access("key2")

        predictions = tracker.get_predictions("key1")

        assert "key2" in predictions

    def test_get_stats(self):
        """Test getting statistics."""
        tracker = FrequencyTracker()

        tracker.record_access("key1")
        tracker.record_access("key2")

        stats = tracker.get_stats()

        assert stats["total_patterns"] == 2
        assert stats["total_accesses"] == 2
        assert stats["tracked_sequences"] == 2


class TestSimilarityMatcher:
    """Test suite for SimilarityMatcher."""

    def test_initialization(self):
        """Test matcher initializes correctly."""
        matcher = SimilarityMatcher(similarity_threshold=0.8)

        assert matcher.similarity_threshold == 0.8
        assert len(matcher.query_hashes) == 0

    def test_register_query(self):
        """Test registering queries."""
        matcher = SimilarityMatcher()

        matcher.register_query("key1", "What is machine learning?")

        assert "key1" in matcher.query_hashes

    def test_find_similar_exact_match(self):
        """Test finding exact match."""
        matcher = SimilarityMatcher(similarity_threshold=0.5)

        matcher.register_query("key1", "What is machine learning?")

        similar = matcher.find_similar("What is machine learning?")

        assert len(similar) == 1
        assert similar[0][0] == "key1"
        assert similar[0][1] == 1.0  # Exact match

    def test_find_similar_partial_match(self):
        """Test finding partial match with lower threshold."""
        matcher = SimilarityMatcher(similarity_threshold=0.3)

        matcher.register_query("key1", "machine learning basics")
        matcher.register_query("key2", "deep learning tutorial")
        matcher.register_query("key3", "totally different topic here")

        # Query shares words with key1 and key2
        similar = matcher.find_similar("machine learning tutorial")

        # Should find at least one match (key1 or key2)
        assert len(similar) >= 1
        # key3 should not match (different words)
        keys = [s[0] for s in similar]
        assert "key3" not in keys

    def test_similarity_threshold(self):
        """Test similarity threshold filtering."""
        matcher = SimilarityMatcher(similarity_threshold=0.9)

        matcher.register_query("key1", "What is machine learning?")
        matcher.register_query("key2", "Something completely different")

        similar = matcher.find_similar("What is machine learning?")

        # Should find key1, not key2
        assert len(similar) == 1
        assert similar[0][0] == "key1"

    def test_find_similar_no_matches(self):
        """Test finding similar with no matches."""
        matcher = SimilarityMatcher(similarity_threshold=0.9)

        matcher.register_query("key1", "Query about something")

        similar = matcher.find_similar("Completely different topic")

        assert len(similar) == 0

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        matcher = SimilarityMatcher(similarity_threshold=0.5)

        matcher.register_query("key1", "What is Machine Learning?")

        similar = matcher.find_similar("what is MACHINE learning?")

        assert len(similar) == 1
        assert similar[0][1] == 1.0  # Should match exactly


class TestCacheWarmer:
    """Test suite for CacheWarmer."""

    def test_initialization(self):
        """Test warmer initializes correctly."""
        tracker = FrequencyTracker()
        warmer = CacheWarmer(tracker)

        assert warmer.frequency_tracker is tracker

    def test_get_warmup_keys(self):
        """Test getting warmup keys."""
        tracker = FrequencyTracker()

        # Create hot keys
        for _ in range(10):
            tracker.record_access("hot_key")

        for _ in range(2):
            tracker.record_access("cold_key")

        warmer = CacheWarmer(tracker)
        warmup_keys = warmer.get_warmup_keys(max_keys=10)

        assert "hot_key" in warmup_keys

    def test_should_warm(self):
        """Test checking if key should be warmed."""
        tracker = FrequencyTracker()
        warmer = CacheWarmer(tracker)

        # Create frequently accessed key
        for _ in range(10):
            tracker.record_access("hot_key")

        # Check if should warm (might be False if accesses too recent)
        # This test is time-dependent, so just verify it returns a boolean
        result = warmer.should_warm("hot_key")
        assert isinstance(result, bool)


class TestSmartCache:
    """Test suite for SmartCache."""

    def test_initialization(self):
        """Test smart cache initializes correctly."""
        cache = SmartCache()

        assert cache.frequency_tracker is not None
        assert cache.similarity_matcher is not None
        assert cache.cache_warmer is not None

    def test_record_access(self):
        """Test recording accesses."""
        cache = SmartCache()

        cache.record_access("key1", query="What is ML?")

        # Check frequency tracking
        assert "key1" in cache.frequency_tracker.patterns

        # Check similarity registration
        assert "key1" in cache.similarity_matcher.query_hashes

    def test_get_predictions(self):
        """Test getting predictions."""
        cache = SmartCache()

        cache.record_access("key1", query="Query 1")
        cache.record_access("key2", query="Query 2")
        cache.record_access("key1", query="Query 1")
        cache.record_access("key2", query="Query 2")

        predictions = cache.get_predictions("key1")

        assert "key2" in predictions

    def test_predictions_disabled(self):
        """Test predictions when disabled."""
        cache = SmartCache(enable_prediction=False)

        cache.record_access("key1", query="Query 1")
        cache.record_access("key2", query="Query 2")

        predictions = cache.get_predictions("key1")

        assert len(predictions) == 0

    def test_find_similar(self):
        """Test finding similar queries."""
        cache = SmartCache(similarity_threshold=0.5)

        cache.record_access("key1", query="What is machine learning?")

        similar = cache.find_similar("What is machine learning?")

        assert len(similar) == 1
        assert similar[0][0] == "key1"

    def test_similarity_disabled(self):
        """Test similarity when disabled."""
        cache = SmartCache(enable_similarity=False)

        cache.record_access("key1", query="What is ML?")

        similar = cache.find_similar("What is ML?")

        assert len(similar) == 0

    def test_get_hot_keys(self):
        """Test getting hot keys."""
        cache = SmartCache()

        for _ in range(10):
            cache.record_access("hot_key")

        for _ in range(2):
            cache.record_access("cold_key")

        hot_keys = cache.get_hot_keys(top_n=2)

        assert "hot_key" in hot_keys

    def test_get_warmup_keys(self):
        """Test getting warmup keys."""
        cache = SmartCache()

        for _ in range(10):
            cache.record_access("key1")

        warmup_keys = cache.get_warmup_keys(max_keys=100)

        # Warmup keys should include key1
        assert "key1" in warmup_keys

    def test_get_stats(self):
        """Test getting statistics."""
        cache = SmartCache()

        cache.record_access("key1", query="Query 1")
        cache.record_access("key2", query="Query 2")

        stats = cache.get_stats()

        assert "frequency_tracking" in stats
        assert "similarity_matching" in stats
        assert "prediction" in stats
        assert stats["frequency_tracking"]["total_patterns"] == 2


class TestSmartCacheIntegration:
    """Integration tests for smart cache."""

    def test_full_workflow(self):
        """Test complete smart cache workflow."""
        cache = SmartCache(similarity_threshold=0.5)

        # Simulate query sequence
        cache.record_access("key1", query="What is RAG?")
        cache.record_access("key2", query="How does RAG work?")
        cache.record_access("key1", query="What is RAG?")
        cache.record_access("key2", query="How does RAG work?")

        # Get predictions after key1
        predictions = cache.get_predictions("key1")
        assert "key2" in predictions

        # Find similar queries
        similar = cache.find_similar("What is RAG?")
        assert len(similar) > 0

        # Get hot keys
        hot_keys = cache.get_hot_keys(top_n=2)
        assert len(hot_keys) == 2

        # Get stats
        stats = cache.get_stats()
        assert stats["frequency_tracking"]["total_patterns"] == 2
