"""
Health Monitoring.

REFINE-003: Proactive health monitoring with background checks.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ragged.install.health.checks import (
    HealthCheckSuite,
    HealthLevel,
    ServiceHealth,
)


logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfig:
    """Configuration for health monitoring."""

    interval_seconds: int = 300  # 5 minutes
    alert_on_degraded: bool = True
    alert_on_unhealthy: bool = True
    max_history: int = 100
    enabled: bool = True


@dataclass
class HealthEvent:
    """Record of a health check event."""

    timestamp: str
    service: str
    level: HealthLevel
    previous_level: HealthLevel | None
    message: str


class HealthMonitor:
    """
    Background health monitor.

    Periodically checks service health and alerts on issues.
    """

    def __init__(
        self,
        ragged_home: Path | None = None,
        config: MonitoringConfig | None = None,
    ) -> None:
        """
        Initialise health monitor.

        Args:
            ragged_home: Path to ragged home.
            config: Monitoring configuration.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self.config = config or MonitoringConfig()

        self._running = False
        self._thread: threading.Thread | None = None
        self._history: list[HealthEvent] = []
        self._last_status: dict[str, HealthLevel] = {}
        self._callbacks: list[Callable[[HealthEvent], None]] = []

    def start(self) -> None:
        """Start background monitoring."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Health monitoring started")

    def stop(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Health monitoring stopped")

    def add_callback(self, callback: Callable[[HealthEvent], None]) -> None:
        """Add event callback."""
        self._callbacks.append(callback)

    def get_history(self, limit: int | None = None) -> list[HealthEvent]:
        """Get recent health events."""
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def get_current_status(self) -> dict[str, HealthLevel]:
        """Get current service status."""
        return self._last_status.copy()

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                self._run_checks()
            except Exception as e:
                logger.exception(f"Health check failed: {e}")

            time.sleep(self.config.interval_seconds)

    def _run_checks(self) -> None:
        """Run health checks and process results."""
        suite = HealthCheckSuite(self.ragged_home)
        results = suite.check_all()

        for health in results:
            previous = self._last_status.get(health.name)
            self._last_status[health.name] = health.level

            # Check for status change
            if previous and previous != health.level:
                event = HealthEvent(
                    timestamp=datetime.now().isoformat(),
                    service=health.name,
                    level=health.level,
                    previous_level=previous,
                    message=self._create_event_message(health, previous),
                )

                self._record_event(event)

                # Alert if needed
                if self._should_alert(health.level, previous):
                    self._send_alert(event)

    def _create_event_message(
        self,
        health: ServiceHealth,
        previous: HealthLevel,
    ) -> str:
        """Create event message."""
        direction = "improved" if health.level.value < previous.value else "degraded"
        failed_checks = [c for c in health.checks if not c.passed]

        if failed_checks:
            details = "; ".join(c.message for c in failed_checks[:3])
            return f"{health.name} {direction}: {details}"

        return f"{health.name} {direction} to {health.level.value}"

    def _record_event(self, event: HealthEvent) -> None:
        """Record health event."""
        self._history.append(event)

        # Trim history
        if len(self._history) > self.config.max_history:
            self._history = self._history[-self.config.max_history:]

    def _should_alert(
        self,
        current: HealthLevel,
        previous: HealthLevel,
    ) -> bool:
        """Check if alert should be sent."""
        if current == HealthLevel.UNHEALTHY and self.config.alert_on_unhealthy:
            return True
        if current == HealthLevel.DEGRADED and self.config.alert_on_degraded:
            return True
        return False

    def _send_alert(self, event: HealthEvent) -> None:
        """Send alert for health event."""
        logger.warning(f"Health alert: {event.message}")

        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Alert callback failed: {e}")


# Global monitor instance
_monitor: HealthMonitor | None = None


def start_monitoring(
    ragged_home: Path | None = None,
    config: MonitoringConfig | None = None,
) -> HealthMonitor:
    """
    Start health monitoring.

    Args:
        ragged_home: Path to ragged home.
        config: Monitoring configuration.

    Returns:
        Health monitor instance.
    """
    global _monitor

    if _monitor is not None:
        _monitor.stop()

    _monitor = HealthMonitor(ragged_home, config)
    _monitor.start()
    return _monitor


def stop_monitoring() -> None:
    """Stop health monitoring."""
    global _monitor

    if _monitor is not None:
        _monitor.stop()
        _monitor = None
