"""Session management for user isolation and security.

v0.2.10 FEAT-SEC-002: Session isolation to prevent cross-user data leakage.

This module provides:
- UUID-based session identification
- Thread-safe session management
- Session lifecycle (create, access, cleanup)
- Automatic session cleanup on exit

Security Context:
- CRITICAL-003: No session isolation in caches
- CVSS 8.1: Cross-user information leakage in multi-user scenarios
- GDPR: User data isolation requirement
"""

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils.logging import get_logger
from src.utils.serialization import load_json, save_json

logger = get_logger(__name__)


@dataclass
class Session:
    """Represents a user session with isolation guarantees.

    Each session has a unique ID that isolates cache entries, query history,
    and other user-specific data from other sessions.

    Attributes:
        session_id: Unique session identifier (UUID4)
        created_at: Session creation timestamp
        last_accessed: Last activity timestamp
        metadata: Optional session metadata (user info, preferences, etc.)
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: dict[str, any] = field(default_factory=dict)

    def touch(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now()

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if session has expired.

        Args:
            ttl_seconds: Session TTL in seconds (default: 1 hour)

        Returns:
            True if session has been inactive longer than TTL
        """
        age = datetime.now() - self.last_accessed
        return age.total_seconds() > ttl_seconds

    def to_dict(self) -> dict[str, any]:
        """Convert session to dictionary for serialization.

        Returns:
            Dictionary representation of session
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "Session":
        """Create session from dictionary.

        Args:
            data: Dictionary with session data

        Returns:
            Session instance
        """
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Thread-safe singleton for managing user sessions.

    Provides centralized session management with:
    - Session creation and retrieval
    - Automatic cleanup of expired sessions
    - Thread-safe operations
    - Optional persistence across restarts

    Usage:
        >>> manager = SessionManager.get_instance()
        >>> session = manager.create_session()
        >>> session_id = session.session_id
        >>>
        >>> # Later, retrieve session
        >>> session = manager.get_session(session_id)
        >>> session.touch()  # Update activity

    Security: Each session ID is unique (UUID4), preventing session prediction attacks.
    """

    _instance: Optional["SessionManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        session_ttl: int = 3600,
        enable_persistence: bool = False,
        session_dir: Path | None = None,
    ):
        """Initialize session manager.

        Args:
            session_ttl: Session time-to-live in seconds (default: 1 hour)
            enable_persistence: Enable session persistence across restarts
            session_dir: Directory for session files (required if persistence enabled)
        """
        self.session_ttl = session_ttl
        self.enable_persistence = enable_persistence
        self.session_dir = session_dir or Path.home() / ".ragged" / "sessions"

        # Active sessions
        self._sessions: dict[str, Session] = {}
        self._session_lock = threading.RLock()

        # Cleanup tracking
        self._cleanup_thread: threading.Thread | None = None
        self._cleanup_interval = 300  # 5 minutes
        self._cleanup_stop = threading.Event()

        if self.enable_persistence:
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self._load_persisted_sessions()

        logger.info(
            f"SessionManager initialized (TTL={session_ttl}s, "
            f"persistence={'enabled' if enable_persistence else 'disabled'})"
        )

    @classmethod
    def get_instance(
        cls,
        session_ttl: int = 3600,
        enable_persistence: bool = False,
        session_dir: Path | None = None,
    ) -> "SessionManager":
        """Get singleton instance of SessionManager.

        Args:
            session_ttl: Session TTL (only used on first call)
            enable_persistence: Enable persistence (only used on first call)
            session_dir: Session directory (only used on first call)

        Returns:
            SessionManager singleton instance

        Thread-safe: Uses double-checked locking pattern.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(session_ttl, enable_persistence, session_dir)
        return cls._instance

    def create_session(self, metadata: dict[str, any] | None = None) -> Session:
        """Create a new session with unique ID.

        Args:
            metadata: Optional session metadata

        Returns:
            New Session instance

        Security: Uses UUID4 for unpredictable session IDs.
        """
        session = Session(metadata=metadata or {})

        with self._session_lock:
            self._sessions[session.session_id] = session

        if self.enable_persistence:
            self._persist_session(session)

        logger.info(f"Created session: {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Retrieve session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found and not expired, None otherwise
        """
        with self._session_lock:
            session = self._sessions.get(session_id)

            if session is None:
                logger.debug(f"Session not found: {session_id}")
                return None

            if session.is_expired(self.session_ttl):
                logger.info(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None

            session.touch()

            if self.enable_persistence:
                self._persist_session(session)

            return session

    def delete_session(self, session_id: str) -> bool:
        """Delete session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        with self._session_lock:
            if session_id not in self._sessions:
                return False

            del self._sessions[session_id]

        # Remove persisted session file
        if self.enable_persistence:
            session_file = self.session_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()

        logger.info(f"Deleted session: {session_id}")
        return True

    def get_active_sessions(self) -> set[str]:
        """Get set of active (non-expired) session IDs.

        Returns:
            Set of active session IDs
        """
        with self._session_lock:
            active = {
                sid
                for sid, session in self._sessions.items()
                if not session.is_expired(self.session_ttl)
            }
            return active

    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = []

        with self._session_lock:
            for session_id, session in self._sessions.items():
                if session.is_expired(self.session_ttl):
                    expired_ids.append(session_id)

        # Delete expired sessions
        for session_id in expired_ids:
            self.delete_session(session_id)

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")

        return len(expired_ids)

    def start_cleanup_thread(self) -> None:
        """Start background thread for automatic session cleanup.

        The cleanup thread runs every 5 minutes and removes expired sessions.
        """
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            logger.warning("Cleanup thread already running")
            return

        self._cleanup_stop.clear()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        logger.info(f"Started session cleanup thread (interval={self._cleanup_interval}s)")

    def stop_cleanup_thread(self) -> None:
        """Stop background cleanup thread."""
        if self._cleanup_thread is None:
            return

        self._cleanup_stop.set()
        self._cleanup_thread.join(timeout=5)
        self._cleanup_thread = None

        logger.info("Stopped session cleanup thread")

    def _cleanup_loop(self) -> None:
        """Background cleanup loop (runs in thread)."""
        while not self._cleanup_stop.wait(self._cleanup_interval):
            try:
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def _persist_session(self, session: Session) -> None:
        """Persist session to disk.

        Args:
            session: Session to persist
        """
        if not self.enable_persistence:
            return

        try:
            session_file = self.session_dir / f"{session.session_id}.json"
            save_json(session.to_dict(), session_file)
        except Exception as e:
            logger.error(f"Failed to persist session {session.session_id}: {e}")

    def _load_persisted_sessions(self) -> None:
        """Load persisted sessions from disk."""
        if not self.enable_persistence or not self.session_dir.exists():
            return

        loaded = 0
        for session_file in self.session_dir.glob("*.json"):
            try:
                data = load_json(session_file)
                session = Session.from_dict(data)

                # Only load non-expired sessions
                if not session.is_expired(self.session_ttl):
                    self._sessions[session.session_id] = session
                    loaded += 1
                else:
                    # Clean up expired session file
                    session_file.unlink()

            except Exception as e:
                logger.warning(f"Failed to load session from {session_file}: {e}")

        if loaded > 0:
            logger.info(f"Loaded {loaded} persisted sessions")

    def shutdown(self) -> None:
        """Clean shutdown of session manager.

        Stops cleanup thread and optionally persists active sessions.
        """
        logger.info("Shutting down SessionManager...")

        # Stop cleanup thread
        self.stop_cleanup_thread()

        # Persist all active sessions
        if self.enable_persistence:
            with self._session_lock:
                for session in self._sessions.values():
                    self._persist_session(session)

        logger.info(f"SessionManager shutdown complete ({len(self._sessions)} sessions)")

    def get_stats(self) -> dict[str, any]:
        """Get session manager statistics.

        Returns:
            Dictionary with statistics
        """
        with self._session_lock:
            total_sessions = len(self._sessions)
            expired_sessions = sum(
                1 for s in self._sessions.values() if s.is_expired(self.session_ttl)
            )
            active_sessions = total_sessions - expired_sessions

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "session_ttl": self.session_ttl,
                "persistence_enabled": self.enable_persistence,
                "cleanup_thread_running": (
                    self._cleanup_thread is not None and self._cleanup_thread.is_alive()
                ),
            }
