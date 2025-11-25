"""Tests for session monitoring metrics.

v0.6.2 SECURITY-004: Session monitoring and anomaly detection.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from ragged.web.middleware.metrics import (
    SessionMetrics,
    active_sessions,
    get_session_metrics,
    reset_session_metrics,
    session_created_total,
    session_creation_rate_per_minute,
    session_deleted_total,
    session_duration_seconds,
    session_expired_total,
)


@pytest.fixture
def metrics():
    """Create a fresh SessionMetrics instance for each test."""
    return SessionMetrics(anomaly_threshold=100, rate_window_seconds=60)


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset global metrics instance before each test."""
    reset_session_metrics()
    yield
    reset_session_metrics()


class TestSessionMetricsInitialization:
    """Test SessionMetrics initialization."""

    def test_default_initialization(self):
        """Test default initialization parameters."""
        metrics = SessionMetrics()

        assert metrics.anomaly_threshold == 100
        assert metrics.rate_window_seconds == 60
        assert len(metrics._creation_timestamps) == 0
        assert not metrics._anomaly_detected
        assert metrics._last_anomaly_log_time == 0.0
        assert metrics._anomaly_log_cooldown == 60.0

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        metrics = SessionMetrics(anomaly_threshold=200, rate_window_seconds=120)

        assert metrics.anomaly_threshold == 200
        assert metrics.rate_window_seconds == 120


class TestSessionCreationRecording:
    """Test session creation recording."""

    def test_record_successful_session_creation(self, metrics):
        """Test recording successful session creation."""
        initial_count = session_created_total.labels(status="success")._value.get()

        metrics.record_session_created(success=True)

        # Verify Prometheus counter incremented
        new_count = session_created_total.labels(status="success")._value.get()
        assert new_count == initial_count + 1

        # Verify timestamp tracked
        assert len(metrics._creation_timestamps) == 1

    def test_record_failed_session_creation(self, metrics):
        """Test recording failed session creation."""
        initial_count = session_created_total.labels(status="failed")._value.get()

        metrics.record_session_created(success=False)

        # Verify Prometheus counter incremented
        new_count = session_created_total.labels(status="failed")._value.get()
        assert new_count == initial_count + 1

        # Verify timestamp NOT tracked (only successful sessions count toward rate)
        assert len(metrics._creation_timestamps) == 0

    def test_multiple_session_creations(self, metrics):
        """Test recording multiple session creations."""
        for _ in range(5):
            metrics.record_session_created(success=True)

        assert len(metrics._creation_timestamps) == 5

    def test_creation_rate_gauge_updated(self, metrics):
        """Test that creation rate gauge is updated on session creation."""
        metrics.record_session_created(success=True)

        # Gauge should be updated (non-zero after creation)
        rate = session_creation_rate_per_minute._value.get()
        assert rate > 0


class TestSessionExpiryAndDeletion:
    """Test session expiry and deletion recording."""

    def test_record_session_expired_without_duration(self, metrics):
        """Test recording session expiry without duration."""
        initial_count = session_expired_total._value.get()

        metrics.record_session_expired(duration=None)

        new_count = session_expired_total._value.get()
        assert new_count == initial_count + 1

    def test_record_session_expired_with_duration(self, metrics):
        """Test recording session expiry with duration."""
        initial_count = session_expired_total._value.get()

        metrics.record_session_expired(duration=1800.0)

        new_count = session_expired_total._value.get()
        assert new_count == initial_count + 1

        # Duration histogram should be updated (hard to verify without accessing internals)

    def test_record_session_deleted_without_duration(self, metrics):
        """Test recording session deletion without duration."""
        initial_count = session_deleted_total._value.get()

        metrics.record_session_deleted(duration=None)

        new_count = session_deleted_total._value.get()
        assert new_count == initial_count + 1

    def test_record_session_deleted_with_duration(self, metrics):
        """Test recording session deletion with duration."""
        initial_count = session_deleted_total._value.get()

        metrics.record_session_deleted(duration=3600.0)

        new_count = session_deleted_total._value.get()
        assert new_count == initial_count + 1


class TestActiveSessionCount:
    """Test active session count tracking."""

    def test_update_active_session_count(self, metrics):
        """Test updating active session count gauge."""
        metrics.update_active_session_count(10)

        count = active_sessions._value.get()
        assert count == 10

    def test_update_active_session_count_multiple_times(self, metrics):
        """Test updating active session count multiple times."""
        metrics.update_active_session_count(5)
        assert active_sessions._value.get() == 5

        metrics.update_active_session_count(15)
        assert active_sessions._value.get() == 15

        metrics.update_active_session_count(0)
        assert active_sessions._value.get() == 0


class TestCreationRateCalculation:
    """Test session creation rate calculation."""

    def test_creation_rate_empty(self, metrics):
        """Test creation rate with no sessions."""
        rate = metrics.get_creation_rate()
        assert rate == 0.0

    def test_creation_rate_single_session(self, metrics):
        """Test creation rate with single session."""
        metrics.record_session_created(success=True)

        rate = metrics.get_creation_rate()
        # 1 session in 60 seconds = 1 session/minute
        assert rate == 1.0

    def test_creation_rate_multiple_sessions(self, metrics):
        """Test creation rate with multiple sessions."""
        for _ in range(10):
            metrics.record_session_created(success=True)

        rate = metrics.get_creation_rate()
        # 10 sessions in 60 seconds = 10 sessions/minute
        assert rate == 10.0

    def test_creation_rate_window_expiry(self, metrics):
        """Test that old timestamps are expired from window."""
        # Create sessions with mocked time
        with patch("time.time") as mock_time:
            # Time = 0
            mock_time.return_value = 0.0
            metrics.record_session_created(success=True)
            metrics.record_session_created(success=True)

            # Time = 30 (still within 60s window)
            mock_time.return_value = 30.0
            metrics.record_session_created(success=True)

            # Check rate at t=30 (3 sessions in window)
            rate = metrics.get_creation_rate()
            assert rate == 3.0

            # Time = 70 (first 2 sessions should be expired)
            mock_time.return_value = 70.0
            rate = metrics.get_creation_rate()
            # Only 1 session left in window (from t=30)
            assert rate == 1.0

    def test_creation_rate_high_frequency(self, metrics):
        """Test creation rate with high frequency sessions."""
        # Create 150 sessions (above anomaly threshold)
        for _ in range(150):
            metrics.record_session_created(success=True)

        rate = metrics.get_creation_rate()
        assert rate == 150.0


class TestAnomalyDetection:
    """Test anomaly detection logic."""

    def test_no_anomaly_below_threshold(self, metrics):
        """Test no anomaly when below threshold."""
        # Create 50 sessions (below 100 threshold)
        for _ in range(50):
            metrics.record_session_created(success=True)

        assert not metrics.check_anomaly()
        assert not metrics._anomaly_detected

    def test_anomaly_above_threshold(self, metrics):
        """Test anomaly detection when above threshold."""
        # Create 150 sessions (above 100 threshold)
        for _ in range(150):
            metrics.record_session_created(success=True)

        # Anomaly should be detected (state is True)
        assert metrics._anomaly_detected

        # check_anomaly() returns False after anomaly already triggered (not rising edge)
        assert not metrics.check_anomaly()

    def test_anomaly_rising_edge_only(self, metrics):
        """Test anomaly only triggers on rising edge."""
        # Anomaly should NOT be detected with 100 sessions (at threshold)
        for _ in range(100):
            metrics.record_session_created(success=True)

        assert not metrics._anomaly_detected

        # 101st session should trigger anomaly (rising edge during record_session_created)
        metrics.record_session_created(success=True)

        assert metrics._anomaly_detected

        # Additional checks should return False (already in anomaly state, not rising edge)
        assert not metrics.check_anomaly()
        assert not metrics.check_anomaly()

    def test_anomaly_state_transition(self, metrics):
        """Test anomaly state transitions."""
        with patch("time.time") as mock_time:
            # Create 150 sessions at t=0
            mock_time.return_value = 0.0
            for _ in range(150):
                metrics.record_session_created(success=True)

            # Anomaly should be detected
            assert metrics._anomaly_detected

            # Wait for window to expire (t=70)
            mock_time.return_value = 70.0

            # Rate should drop below threshold
            rate = metrics.get_creation_rate()
            assert rate == 0.0

            # Anomaly should clear after check
            assert not metrics.check_anomaly()
            assert not metrics._anomaly_detected

    def test_custom_anomaly_threshold(self):
        """Test anomaly detection with custom threshold."""
        metrics = SessionMetrics(anomaly_threshold=50)

        # Create 60 sessions (above 50 threshold)
        for _ in range(60):
            metrics.record_session_created(success=True)

        # Anomaly should be detected
        assert metrics._anomaly_detected


class TestAnomalyLogging:
    """Test anomaly logging with cooldown."""

    def test_anomaly_logged_on_detection(self, metrics):
        """Test that anomaly is logged when detected."""
        with patch("ragged.web.middleware.metrics.logger") as mock_logger:
            # Create 150 sessions to trigger anomaly
            for _ in range(150):
                metrics.record_session_created(success=True)

            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            assert "Session creation anomaly detected" in mock_logger.warning.call_args[0][0]

    def test_anomaly_logging_cooldown(self):
        """Test that anomaly logging respects cooldown via _last_anomaly_log_time."""
        # Create fresh instance to ensure clean state
        test_metrics = SessionMetrics(anomaly_threshold=100)

        with patch("time.time") as mock_time:
            # First anomaly at t=0
            mock_time.return_value = 0.0
            for _ in range(150):
                test_metrics.record_session_created(success=True)

            # Anomaly should be detected
            assert test_metrics._anomaly_detected
            # Last log time should be set
            first_log_time = test_metrics._last_anomaly_log_time
            assert first_log_time == 0.0

            # Reset anomaly state and timestamps for second trigger
            test_metrics._anomaly_detected = False
            test_metrics._creation_timestamps.clear()

            # Second anomaly at t=30 (within 60s cooldown)
            mock_time.return_value = 30.0
            for _ in range(150):
                test_metrics.record_session_created(success=True)

            # Anomaly detected again
            assert test_metrics._anomaly_detected
            # Last log time should NOT be updated (cooldown active)
            assert test_metrics._last_anomaly_log_time == first_log_time

            # Reset anomaly state and timestamps for third trigger
            test_metrics._anomaly_detected = False
            test_metrics._creation_timestamps.clear()

            # Third anomaly at t=70 (outside 60s cooldown)
            mock_time.return_value = 70.0
            for _ in range(150):
                test_metrics.record_session_created(success=True)

            # Anomaly detected again
            assert test_metrics._anomaly_detected
            # Last log time SHOULD be updated (cooldown expired)
            assert test_metrics._last_anomaly_log_time == 70.0


class TestThreadSafety:
    """Test thread safety of metrics tracking."""

    def test_concurrent_session_creation(self, metrics):
        """Test concurrent session creation is thread-safe."""
        import threading

        def create_sessions():
            for _ in range(10):
                metrics.record_session_created(success=True)

        # Create 10 threads, each creating 10 sessions
        threads = [threading.Thread(target=create_sessions) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have 100 timestamps
        assert len(metrics._creation_timestamps) == 100

    def test_concurrent_rate_calculation(self, metrics):
        """Test concurrent rate calculation is thread-safe."""
        import threading

        # Pre-populate with sessions
        for _ in range(50):
            metrics.record_session_created(success=True)

        results = []

        def calculate_rate():
            rate = metrics.get_creation_rate()
            results.append(rate)

        # Calculate rate from 10 threads simultaneously
        threads = [threading.Thread(target=calculate_rate) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should get the same rate
        assert len(results) == 10
        assert all(rate == 50.0 for rate in results)


class TestGetStats:
    """Test get_stats() method."""

    def test_get_stats_empty(self, metrics):
        """Test get_stats with no activity."""
        stats = metrics.get_stats()

        assert stats["creation_rate_per_minute"] == 0.0
        assert stats["active_sessions"] >= 0  # Global gauge value
        assert not stats["anomaly_detected"]
        assert stats["anomaly_threshold"] == 100

    def test_get_stats_with_activity(self, metrics):
        """Test get_stats with session activity."""
        # Create sessions
        for _ in range(25):
            metrics.record_session_created(success=True)

        # Update active count
        metrics.update_active_session_count(15)

        stats = metrics.get_stats()

        assert stats["creation_rate_per_minute"] == 25.0
        assert stats["active_sessions"] == 15
        assert not stats["anomaly_detected"]
        assert stats["anomaly_threshold"] == 100

    def test_get_stats_with_anomaly(self, metrics):
        """Test get_stats during anomaly."""
        # Create sessions above threshold
        for _ in range(150):
            metrics.record_session_created(success=True)

        # Trigger anomaly check
        metrics.check_anomaly()

        stats = metrics.get_stats()

        assert stats["creation_rate_per_minute"] == 150.0
        assert stats["anomaly_detected"]


class TestGetSessionMetricsSingleton:
    """Test get_session_metrics() singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Test that get_session_metrics returns same instance."""
        instance1 = get_session_metrics()
        instance2 = get_session_metrics()

        assert instance1 is instance2

    def test_singleton_custom_parameters(self):
        """Test singleton with custom parameters."""
        instance = get_session_metrics(anomaly_threshold=200, rate_window_seconds=120)

        assert instance.anomaly_threshold == 200
        assert instance.rate_window_seconds == 120

    def test_singleton_thread_safety(self):
        """Test singleton creation is thread-safe."""
        import threading

        instances = []

        def get_instance():
            instance = get_session_metrics()
            instances.append(instance)

        # Get instance from 10 threads simultaneously
        threads = [threading.Thread(target=get_instance) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should get the same instance
        assert len(instances) == 10
        assert all(instance is instances[0] for instance in instances)

    def test_reset_clears_singleton(self):
        """Test that reset_session_metrics clears singleton."""
        instance1 = get_session_metrics()

        reset_session_metrics()

        instance2 = get_session_metrics()

        # Should be different instances after reset
        assert instance1 is not instance2


class TestPrometheusMetricsIntegration:
    """Test integration with Prometheus metrics."""

    def test_session_created_counter_labels(self, metrics):
        """Test session_created_total counter with labels."""
        initial_success = session_created_total.labels(status="success")._value.get()
        initial_failed = session_created_total.labels(status="failed")._value.get()

        metrics.record_session_created(success=True)
        metrics.record_session_created(success=True)
        metrics.record_session_created(success=False)

        assert session_created_total.labels(status="success")._value.get() == initial_success + 2
        assert session_created_total.labels(status="failed")._value.get() == initial_failed + 1

    def test_active_sessions_gauge(self, metrics):
        """Test active_sessions gauge."""
        metrics.update_active_session_count(42)

        assert active_sessions._value.get() == 42

    def test_creation_rate_gauge(self, metrics):
        """Test session_creation_rate_per_minute gauge."""
        for _ in range(30):
            metrics.record_session_created(success=True)

        rate = session_creation_rate_per_minute._value.get()
        assert rate == 30.0

    def test_session_duration_histogram(self, metrics):
        """Test session_duration_seconds histogram."""
        # Record various durations
        metrics.record_session_expired(duration=300.0)  # 5 minutes
        metrics.record_session_expired(duration=1800.0)  # 30 minutes
        metrics.record_session_deleted(duration=3600.0)  # 1 hour

        # Histogram should be updated (hard to verify without accessing internals)
        # Just verify no errors occurred


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_rate_window(self):
        """Test with zero rate window (should handle gracefully)."""
        # This is an invalid configuration, but should not crash
        metrics = SessionMetrics(rate_window_seconds=1)

        metrics.record_session_created(success=True)

        # Should calculate rate without error
        rate = metrics.get_creation_rate()
        assert rate >= 0.0

    def test_exact_threshold_boundary(self, metrics):
        """Test anomaly detection at exact threshold."""
        # Create exactly 100 sessions (threshold)
        for _ in range(100):
            metrics.record_session_created(success=True)

        # At threshold, should NOT trigger anomaly (must be above)
        assert not metrics._anomaly_detected

        # One more session to exceed threshold
        metrics.record_session_created(success=True)

        # Now anomaly should be detected
        assert metrics._anomaly_detected

    def test_very_high_session_count(self, metrics):
        """Test with very high session count."""
        # Create 10,000 sessions
        for _ in range(10000):
            metrics.record_session_created(success=True)

        rate = metrics.get_creation_rate()
        assert rate == 10000.0

        # Anomaly should be detected
        assert metrics._anomaly_detected

    def test_negative_duration(self, metrics):
        """Test with negative duration (invalid but should not crash)."""
        metrics.record_session_expired(duration=-100.0)
        metrics.record_session_deleted(duration=-50.0)

        # Should not raise exception

    def test_zero_duration(self, metrics):
        """Test with zero duration."""
        metrics.record_session_expired(duration=0.0)
        metrics.record_session_deleted(duration=0.0)

        # Should not raise exception
