"""Session monitoring metrics for Prometheus.

v0.6.2 SECURITY-004: Session monitoring and DoS attack detection.

Provides:
- Prometheus-compatible metrics for session lifecycle
- Anomaly detection for unusual session creation rates
- Active session count tracking
- Session creation/expiry counters

Security Context:
- Addresses v0.6.0 audit R-4: No visibility into session behaviour
- CR-SEC-004: Session exhaustion attack detection
- DoS prevention via rate monitoring
"""

import logging
import time
from collections import deque
from threading import Lock
from typing import TYPE_CHECKING

from prometheus_client import Counter, Gauge, Histogram

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Prometheus metrics for session monitoring
session_created_total = Counter(
    "ragged_session_created_total",
    "Total number of sessions created",
    ["status"],  # Labels: success, failed
)

session_expired_total = Counter(
    "ragged_session_expired_total",
    "Total number of sessions expired",
)

session_deleted_total = Counter(
    "ragged_session_deleted_total",
    "Total number of sessions explicitly deleted",
)

active_sessions = Gauge(
    "ragged_active_sessions",
    "Number of currently active sessions",
)

session_creation_rate_per_minute = Gauge(
    "ragged_session_creation_rate_per_minute",
    "Session creation rate over the last minute",
)

session_duration_seconds = Histogram(
    "ragged_session_duration_seconds",
    "Duration of sessions in seconds",
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800],  # 1m to 8h
)


class SessionMetrics:
    """Session metrics tracker with anomaly detection.

    Tracks session lifecycle events and detects unusual patterns
    that may indicate DoS attacks or system issues.

    v0.6.2 SECURITY-004: Session monitoring

    Example:
        >>> metrics = SessionMetrics()
        >>> metrics.record_session_created()
        >>> metrics.record_session_expired(duration=1800)
        >>> metrics.get_creation_rate()
        15.2
        >>> metrics.check_anomaly()
        False
    """

    def __init__(
        self,
        anomaly_threshold: int = 100,
        rate_window_seconds: int = 60,
    ) -> None:
        """Initialise session metrics tracker.

        Args:
            anomaly_threshold: Sessions/minute threshold for anomaly detection
            rate_window_seconds: Time window for rate calculation
        """
        self.anomaly_threshold = anomaly_threshold
        self.rate_window_seconds = rate_window_seconds

        # Thread-safe deque for tracking creation timestamps
        self._creation_timestamps: deque[float] = deque()
        self._lock = Lock()

        # Anomaly detection state
        self._anomaly_detected = False
        self._last_anomaly_log_time = 0.0
        self._anomaly_log_cooldown = 60.0  # Log anomalies at most once per minute

        logger.info(
            f"SessionMetrics initialised: threshold={anomaly_threshold}/min, "
            f"window={rate_window_seconds}s"
        )

    def record_session_created(self, success: bool = True) -> None:
        """Record session creation event.

        Args:
            success: Whether session creation succeeded
        """
        current_time = time.time()

        # Update Prometheus counter
        status = "success" if success else "failed"
        session_created_total.labels(status=status).inc()

        if success:
            # Track creation timestamp for rate calculation
            with self._lock:
                self._creation_timestamps.append(current_time)

                # Clean old timestamps outside window
                cutoff_time = current_time - self.rate_window_seconds
                while (
                    self._creation_timestamps
                    and self._creation_timestamps[0] < cutoff_time
                ):
                    self._creation_timestamps.popleft()

            # Update creation rate gauge
            rate = self.get_creation_rate()
            session_creation_rate_per_minute.set(rate)

            # Check for anomalies
            if self.check_anomaly():
                self._log_anomaly(rate)

    def record_session_expired(self, duration: float | None = None) -> None:
        """Record session expiry event.

        Args:
            duration: Session duration in seconds (if known)
        """
        session_expired_total.inc()

        if duration is not None:
            session_duration_seconds.observe(duration)

    def record_session_deleted(self, duration: float | None = None) -> None:
        """Record session deletion event.

        Args:
            duration: Session duration in seconds (if known)
        """
        session_deleted_total.inc()

        if duration is not None:
            session_duration_seconds.observe(duration)

    def update_active_session_count(self, count: int) -> None:
        """Update active session count gauge.

        Args:
            count: Current number of active sessions
        """
        active_sessions.set(count)

    def get_creation_rate(self) -> float:
        """Calculate current session creation rate.

        Returns:
            Sessions created per minute in the current window
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.rate_window_seconds

            # Clean old timestamps
            while (
                self._creation_timestamps
                and self._creation_timestamps[0] < cutoff_time
            ):
                self._creation_timestamps.popleft()

            # Calculate rate (sessions per minute)
            count = len(self._creation_timestamps)
            rate = (count / self.rate_window_seconds) * 60

            return rate

    def check_anomaly(self) -> bool:
        """Check if current session creation rate indicates an anomaly.

        Returns:
            True if creation rate exceeds anomaly threshold
        """
        rate = self.get_creation_rate()
        anomaly = rate > self.anomaly_threshold

        # Update anomaly state
        prev_anomaly = self._anomaly_detected
        self._anomaly_detected = anomaly

        # Return True on anomaly state transition (rising edge)
        return anomaly and not prev_anomaly

    def _log_anomaly(self, rate: float) -> None:
        """Log anomaly detection with cooldown.

        Args:
            rate: Current session creation rate
        """
        current_time = time.time()

        # Apply cooldown to avoid log spam
        if current_time - self._last_anomaly_log_time < self._anomaly_log_cooldown:
            return

        logger.warning(
            f"Session creation anomaly detected: {rate:.1f} sessions/min "
            f"(threshold: {self.anomaly_threshold}/min). "
            f"Possible DoS attack or system issue."
        )

        self._last_anomaly_log_time = current_time

    def get_stats(self) -> dict[str, float]:
        """Get current metrics statistics.

        Returns:
            Dictionary with current metrics values
        """
        return {
            "creation_rate_per_minute": self.get_creation_rate(),
            "active_sessions": active_sessions._value.get(),  # type: ignore[attr-defined]
            "anomaly_detected": self._anomaly_detected,
            "anomaly_threshold": self.anomaly_threshold,
        }


# Global metrics instance (singleton)
_metrics_instance: SessionMetrics | None = None
_metrics_lock = Lock()


def get_session_metrics(
    anomaly_threshold: int = 100,
    rate_window_seconds: int = 60,
) -> SessionMetrics:
    """Get or create global session metrics instance.

    Args:
        anomaly_threshold: Sessions/minute threshold for anomaly detection
        rate_window_seconds: Time window for rate calculation

    Returns:
        SessionMetrics singleton instance

    Thread-safe: Uses double-checked locking pattern.
    """
    global _metrics_instance

    if _metrics_instance is None:
        with _metrics_lock:
            if _metrics_instance is None:
                _metrics_instance = SessionMetrics(
                    anomaly_threshold=anomaly_threshold,
                    rate_window_seconds=rate_window_seconds,
                )

    return _metrics_instance


def reset_session_metrics() -> None:
    """Reset global metrics instance (for testing).

    Warning: This should only be used in tests!
    """
    global _metrics_instance

    with _metrics_lock:
        _metrics_instance = None
