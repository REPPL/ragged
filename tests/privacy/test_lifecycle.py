"""Tests for data lifecycle management.

v0.2.11 FEAT-PRIV-003: Data Lifecycle Management

Tests for TTL-based expiration and automatic cleanup.
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.privacy.lifecycle import (
    DataLifecycleManager,
    get_lifecycle_manager,
)


class TestDataLifecycleManager:
    """Test suite for DataLifecycleManager."""

    def test_manager_initialization(self) -> None:
        """Test lifecycle manager initialisation with default values."""
        manager = DataLifecycleManager()

        assert manager.query_history_ttl_days == 30
        assert manager.session_ttl_days == 7
        assert manager.auto_cleanup_enabled is True
        assert manager.cleanup_interval_hours == 24
        assert manager._running is False

    def test_manager_initialization_custom_values(self) -> None:
        """Test lifecycle manager with custom configuration."""
        manager = DataLifecycleManager(
            query_history_ttl_days=60,
            session_ttl_days=14,
            auto_cleanup_enabled=False,
            cleanup_interval_hours=12,
        )

        assert manager.query_history_ttl_days == 60
        assert manager.session_ttl_days == 14
        assert manager.auto_cleanup_enabled is False
        assert manager.cleanup_interval_hours == 12

    def test_is_expired_recent_timestamp(self) -> None:
        """Test that recent timestamps are not expired."""
        manager = DataLifecycleManager()

        recent = datetime.now() - timedelta(hours=1)
        assert not manager.is_expired(recent, ttl_days=30)

    def test_is_expired_old_timestamp(self) -> None:
        """Test that old timestamps are expired."""
        manager = DataLifecycleManager()

        old = datetime.now() - timedelta(days=31)
        assert manager.is_expired(old, ttl_days=30)

    def test_is_expired_exact_boundary(self) -> None:
        """Test expiration at exact TTL boundary."""
        manager = DataLifecycleManager()

        # Exactly at boundary (should be expired)
        boundary = datetime.now() - timedelta(days=30, seconds=1)
        assert manager.is_expired(boundary, ttl_days=30)

        # Just before boundary (should not be expired)
        before_boundary = datetime.now() - timedelta(days=29, hours=23)
        assert not manager.is_expired(before_boundary, ttl_days=30)

    def test_is_expired_ttl_zero_never_expires(self) -> None:
        """Test that TTL=0 means unlimited retention (never expires)."""
        manager = DataLifecycleManager()

        very_old = datetime.now() - timedelta(days=365)
        assert not manager.is_expired(very_old, ttl_days=0)

    def test_is_expired_custom_reference_time(self) -> None:
        """Test expiration with custom reference time."""
        manager = DataLifecycleManager()

        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        reference = datetime(2024, 2, 1, 12, 0, 0)  # 31 days later

        assert manager.is_expired(timestamp, ttl_days=30, reference_time=reference)
        assert not manager.is_expired(timestamp, ttl_days=31, reference_time=reference)

    def test_filter_expired_entries_all_recent(self) -> None:
        """Test filtering when all entries are recent."""
        manager = DataLifecycleManager()

        entries = [
            {"timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "data": "A"},
            {"timestamp": (datetime.now() - timedelta(days=5)).isoformat(), "data": "B"},
            {"timestamp": (datetime.now() - timedelta(days=10)).isoformat(), "data": "C"},
        ]

        filtered, removed = manager.filter_expired_entries(entries, ttl_days=30)

        assert len(filtered) == 3
        assert removed == 0

    def test_filter_expired_entries_all_old(self) -> None:
        """Test filtering when all entries are expired."""
        manager = DataLifecycleManager()

        entries = [
            {"timestamp": (datetime.now() - timedelta(days=31)).isoformat(), "data": "A"},
            {"timestamp": (datetime.now() - timedelta(days=40)).isoformat(), "data": "B"},
            {"timestamp": (datetime.now() - timedelta(days=50)).isoformat(), "data": "C"},
        ]

        filtered, removed = manager.filter_expired_entries(entries, ttl_days=30)

        assert len(filtered) == 0
        assert removed == 3

    def test_filter_expired_entries_mixed(self) -> None:
        """Test filtering with mix of recent and expired entries."""
        manager = DataLifecycleManager()

        entries = [
            {"timestamp": (datetime.now() - timedelta(days=5)).isoformat(), "data": "A"},
            {"timestamp": (datetime.now() - timedelta(days=31)).isoformat(), "data": "B"},
            {"timestamp": (datetime.now() - timedelta(days=10)).isoformat(), "data": "C"},
            {"timestamp": (datetime.now() - timedelta(days=40)).isoformat(), "data": "D"},
        ]

        filtered, removed = manager.filter_expired_entries(entries, ttl_days=30)

        assert len(filtered) == 2
        assert removed == 2
        # Verify correct entries kept
        assert filtered[0]["data"] == "A"
        assert filtered[1]["data"] == "C"

    def test_filter_expired_entries_custom_timestamp_key(self) -> None:
        """Test filtering with custom timestamp key."""
        manager = DataLifecycleManager()

        entries = [
            {"created_at": (datetime.now() - timedelta(days=5)).isoformat(), "data": "A"},
            {"created_at": (datetime.now() - timedelta(days=31)).isoformat(), "data": "B"},
        ]

        filtered, removed = manager.filter_expired_entries(
            entries, timestamp_key="created_at", ttl_days=30
        )

        assert len(filtered) == 1
        assert removed == 1
        assert filtered[0]["data"] == "A"

    def test_filter_expired_entries_ttl_zero(self) -> None:
        """Test that TTL=0 keeps all entries (unlimited retention)."""
        manager = DataLifecycleManager()

        entries = [
            {"timestamp": (datetime.now() - timedelta(days=100)).isoformat(), "data": "A"},
            {"timestamp": (datetime.now() - timedelta(days=200)).isoformat(), "data": "B"},
        ]

        filtered, removed = manager.filter_expired_entries(entries, ttl_days=0)

        assert len(filtered) == 2
        assert removed == 0

    def test_filter_expired_entries_missing_timestamp(self) -> None:
        """Test handling of entries with missing timestamp."""
        manager = DataLifecycleManager()

        entries = [
            {"timestamp": (datetime.now() - timedelta(days=5)).isoformat(), "data": "A"},
            {"data": "B"},  # Missing timestamp
            {"timestamp": (datetime.now() - timedelta(days=31)).isoformat(), "data": "C"},
        ]

        filtered, removed = manager.filter_expired_entries(entries, ttl_days=30)

        # Entry without timestamp should be skipped (not included in filtered)
        assert len(filtered) == 1
        assert removed == 1  # Only the expired entry is counted as removed

    def test_filter_expired_entries_invalid_timestamp(self) -> None:
        """Test handling of entries with invalid timestamp format."""
        manager = DataLifecycleManager()

        entries = [
            {"timestamp": (datetime.now() - timedelta(days=5)).isoformat(), "data": "A"},
            {"timestamp": "invalid-timestamp", "data": "B"},
            {"timestamp": (datetime.now() - timedelta(days=10)).isoformat(), "data": "C"},
        ]

        filtered, removed = manager.filter_expired_entries(entries, ttl_days=30)

        # Invalid timestamp entry should be kept (safer than deleting)
        assert len(filtered) == 3
        assert removed == 0

    def test_filter_expired_entries_empty_list(self) -> None:
        """Test filtering empty list."""
        manager = DataLifecycleManager()

        filtered, removed = manager.filter_expired_entries([], ttl_days=30)

        assert len(filtered) == 0
        assert removed == 0

    def test_start_automatic_cleanup(self) -> None:
        """Test starting automatic cleanup scheduler."""
        manager = DataLifecycleManager(
            auto_cleanup_enabled=True, cleanup_interval_hours=1
        )

        assert not manager._running

        manager.start_automatic_cleanup()

        assert manager._running
        assert manager._cleanup_thread is not None
        assert manager._cleanup_thread.is_alive()

        # Cleanup
        manager.stop_automatic_cleanup()

    def test_start_automatic_cleanup_when_disabled(self) -> None:
        """Test that cleanup doesn't start when disabled."""
        manager = DataLifecycleManager(auto_cleanup_enabled=False)

        manager.start_automatic_cleanup()

        assert not manager._running
        assert manager._cleanup_thread is None

    def test_start_automatic_cleanup_already_running(self) -> None:
        """Test starting cleanup when already running (should be idempotent)."""
        manager = DataLifecycleManager(
            auto_cleanup_enabled=True, cleanup_interval_hours=1
        )

        manager.start_automatic_cleanup()
        assert manager._running

        # Try to start again
        manager.start_automatic_cleanup()

        # Should still be running (no crash)
        assert manager._running

        # Cleanup
        manager.stop_automatic_cleanup()

    def test_stop_automatic_cleanup(self) -> None:
        """Test stopping automatic cleanup scheduler."""
        manager = DataLifecycleManager(
            auto_cleanup_enabled=True, cleanup_interval_hours=1
        )

        manager.start_automatic_cleanup()
        assert manager._running

        manager.stop_automatic_cleanup()

        assert not manager._running
        # Thread should have stopped
        time.sleep(0.1)  # Give thread time to stop
        if manager._cleanup_thread:
            assert not manager._cleanup_thread.is_alive()

    def test_stop_automatic_cleanup_when_not_running(self) -> None:
        """Test stopping cleanup when not running (should be idempotent)."""
        manager = DataLifecycleManager()

        # Stop without starting (should not crash)
        manager.stop_automatic_cleanup()

        assert not manager._running

    def test_perform_full_cleanup(self) -> None:
        """Test full cleanup execution."""
        manager = DataLifecycleManager()

        # Should return count (currently 0 as it's a placeholder)
        removed = manager.perform_full_cleanup()

        assert isinstance(removed, int)
        assert removed >= 0

    def test_cleanup_thread_runs_periodically(self) -> None:
        """Test that cleanup thread executes periodically."""
        # Use very short interval for testing
        manager = DataLifecycleManager(
            auto_cleanup_enabled=True, cleanup_interval_hours=0.001  # ~3.6 seconds
        )

        cleanup_count = 0

        # Mock perform_full_cleanup to track calls
        original_cleanup = manager.perform_full_cleanup

        def mock_cleanup():
            nonlocal cleanup_count
            cleanup_count += 1
            return original_cleanup()

        manager.perform_full_cleanup = mock_cleanup

        manager.start_automatic_cleanup()

        # Wait for at least one cleanup cycle
        time.sleep(5)

        manager.stop_automatic_cleanup()

        # Should have run at least once
        assert cleanup_count >= 1


class TestLifecycleManagerSingleton:
    """Test suite for lifecycle manager singleton."""

    def test_get_lifecycle_manager_creates_instance(self) -> None:
        """Test that get_lifecycle_manager creates instance."""
        # Reset global instance
        import src.privacy.lifecycle as lifecycle_module

        lifecycle_module._lifecycle_manager = None

        manager = get_lifecycle_manager()

        assert manager is not None
        assert isinstance(manager, DataLifecycleManager)

    def test_get_lifecycle_manager_singleton(self) -> None:
        """Test that get_lifecycle_manager returns same instance."""
        # Reset global instance
        import src.privacy.lifecycle as lifecycle_module

        lifecycle_module._lifecycle_manager = None

        manager1 = get_lifecycle_manager()
        manager2 = get_lifecycle_manager()

        assert manager1 is manager2

    def test_get_lifecycle_manager_custom_config(self) -> None:
        """Test lifecycle manager with custom configuration."""
        # Reset global instance
        import src.privacy.lifecycle as lifecycle_module

        lifecycle_module._lifecycle_manager = None

        manager = get_lifecycle_manager(
            query_history_ttl_days=60,
            session_ttl_days=14,
            auto_cleanup_enabled=False,
        )

        assert manager.query_history_ttl_days == 60
        assert manager.session_ttl_days == 14
        assert manager.auto_cleanup_enabled is False


class TestLifecycleIntegration:
    """Integration tests for lifecycle management."""

    def test_lifecycle_with_query_history_format(self) -> None:
        """Test lifecycle with ragged query history format."""
        manager = DataLifecycleManager()

        # Simulate query history entries
        history = [
            {
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "query": "What is RAG?",
                "session_id": "abc123",
            },
            {
                "timestamp": (datetime.now() - timedelta(days=31)).isoformat(),
                "query": "Old query",
                "session_id": "xyz789",
            },
            {
                "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
                "query": "Recent query",
                "session_id": "def456",
            },
        ]

        filtered, removed = manager.filter_expired_entries(history, ttl_days=30)

        assert len(filtered) == 2
        assert removed == 1
        assert all("query" in entry for entry in filtered)

    def test_lifecycle_respects_data_minimisation(self) -> None:
        """Test that lifecycle implements GDPR data minimisation."""
        manager = DataLifecycleManager(query_history_ttl_days=30)

        # Create 100 entries spanning 100 days
        entries = []
        for days_ago in range(100):
            entries.append(
                {
                    "timestamp": (datetime.now() - timedelta(days=days_ago)).isoformat(),
                    "data": f"entry_{days_ago}",
                }
            )

        filtered, removed = manager.filter_expired_entries(
            entries, ttl_days=manager.query_history_ttl_days
        )

        # Should keep only entries within TTL
        assert len(filtered) <= 30
        assert removed >= 30
        # Total should equal original
        assert len(filtered) + removed == 100


# Mark all tests as privacy tests
pytestmark = pytest.mark.privacy
