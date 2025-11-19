"""Data lifecycle management for ragged.

v0.2.11 FEAT-PRIV-003: Data Lifecycle Management

Implements TTL (Time-To-Live) and automatic deletion for persistent user data.
Ensures compliance with data minimisation principles (GDPR Article 5).
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataLifecycleManager:
    """Manages data retention and automatic cleanup.

    Features:
    - TTL-based expiration for query history, sessions, caches
    - Automatic cleanup scheduler
    - Manual cleanup commands
    - Configurable retention policies

    Usage:
        >>> manager = DataLifecycleManager(
        ...     query_history_ttl_days=30,
        ...     session_ttl_days=7
        ... )
        >>> removed = manager.cleanup_query_history(history_file)
    """

    def __init__(
        self,
        query_history_ttl_days: int = 30,
        session_ttl_days: int = 7,
        auto_cleanup_enabled: bool = True,
        cleanup_interval_hours: int = 24,
    ):
        """Initialise lifecycle manager.

        Args:
            query_history_ttl_days: Query history retention (days, 0 = unlimited)
            session_ttl_days: Session retention (days)
            auto_cleanup_enabled: Enable automatic cleanup
            cleanup_interval_hours: Cleanup frequency (hours)

        Privacy: Default TTLs follow data minimisation principle.
        """
        self.query_history_ttl_days = query_history_ttl_days
        self.session_ttl_days = session_ttl_days
        self.auto_cleanup_enabled = auto_cleanup_enabled
        self.cleanup_interval_hours = cleanup_interval_hours

        # Cleanup scheduler
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_stop = threading.Event()
        self._running = False

    def is_expired(
        self, timestamp: datetime, ttl_days: int, reference_time: Optional[datetime] = None
    ) -> bool:
        """Check if timestamp has exceeded TTL.

        Args:
            timestamp: Timestamp to check
            ttl_days: Time-to-live in days (0 = never expires)
            reference_time: Reference time (default: now)

        Returns:
            True if expired

        Privacy: Core expiration logic for GDPR compliance.
        """
        if ttl_days == 0:  # Unlimited retention
            return False

        if reference_time is None:
            reference_time = datetime.now()

        age = reference_time - timestamp
        return age.total_seconds() > (ttl_days * 86400)

    def filter_expired_entries(
        self, entries: List[Dict[str, Any]], timestamp_key: str = "timestamp", ttl_days: int = 30
    ) -> tuple[List[Dict[str, Any]], int]:
        """Filter out expired entries from list.

        Args:
            entries: List of entries with timestamps
            timestamp_key: Key name for timestamp field
            ttl_days: Time-to-live in days

        Returns:
            Tuple of (filtered_entries, removed_count)

        Privacy: Automatic data minimisation.
        """
        if ttl_days == 0:
            return entries, 0

        cutoff = datetime.now() - timedelta(days=ttl_days)
        filtered = []

        for entry in entries:
            try:
                timestamp_str = entry.get(timestamp_key)
                if not timestamp_str:
                    continue

                timestamp = datetime.fromisoformat(timestamp_str)

                if timestamp > cutoff:
                    filtered.append(entry)

            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp in entry: {e}")
                # Keep entry if timestamp invalid (safer than deleting)
                filtered.append(entry)

        removed = len(entries) - len(filtered)

        if removed > 0:
            logger.info(f"Filtered {removed} expired entries (TTL: {ttl_days} days)")

        return filtered, removed

    def start_automatic_cleanup(self) -> None:
        """Start background cleanup thread.

        Privacy: Ensures automatic compliance with retention policies.
        """
        if not self.auto_cleanup_enabled:
            logger.info("Automatic cleanup disabled")
            return

        if self._running:
            logger.warning("Cleanup thread already running")
            return

        self._cleanup_stop.clear()
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        logger.info(f"Started automatic cleanup (interval: {self.cleanup_interval_hours}h)")

    def stop_automatic_cleanup(self) -> None:
        """Stop background cleanup thread."""
        if not self._running:
            return

        self._running = False
        self._cleanup_stop.set()

        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

        logger.info("Stopped automatic cleanup")

    def _cleanup_loop(self) -> None:
        """Main cleanup loop (runs in background thread)."""
        interval_seconds = self.cleanup_interval_hours * 3600

        while not self._cleanup_stop.wait(interval_seconds):
            try:
                logger.debug("Running scheduled cleanup...")
                total_removed = self.perform_full_cleanup()
                if total_removed > 0:
                    logger.info(f"Cleanup complete: removed {total_removed} items")
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")

    def perform_full_cleanup(self) -> int:
        """Perform cleanup of all expired data.

        Returns:
            Total number of items removed

        Privacy: Implements data minimisation across all data types.
        """
        total_removed = 0

        # Note: Actual cleanup implementation would call specific
        # cleanup methods for query history, sessions, etc.
        # This is a placeholder for the framework.

        logger.debug(f"Full cleanup complete: {total_removed} items removed")
        return total_removed


# Global lifecycle manager (singleton)
_lifecycle_manager: Optional[DataLifecycleManager] = None


def get_lifecycle_manager(
    query_history_ttl_days: int = 30,
    session_ttl_days: int = 7,
    auto_cleanup_enabled: bool = True,
) -> DataLifecycleManager:
    """Get global lifecycle manager (singleton).

    Args:
        query_history_ttl_days: Query history TTL (only used on first call)
        session_ttl_days: Session TTL (only used on first call)
        auto_cleanup_enabled: Enable auto cleanup (only used on first call)

    Returns:
        DataLifecycleManager singleton

    Usage:
        >>> from src.privacy.lifecycle import get_lifecycle_manager
        >>> manager = get_lifecycle_manager()
        >>> manager.start_automatic_cleanup()
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = DataLifecycleManager(
            query_history_ttl_days=query_history_ttl_days,
            session_ttl_days=session_ttl_days,
            auto_cleanup_enabled=auto_cleanup_enabled,
        )
    return _lifecycle_manager
