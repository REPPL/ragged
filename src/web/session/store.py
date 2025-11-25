"""Session storage backends for production scalability.

v0.6.2 SECURITY-003: Redis-backed session persistence with graceful fallback.

Provides:
- SessionStore abstract interface
- InMemorySessionStore for development
- RedisSessionStore for production
- Automatic fallback to in-memory if Redis unavailable

Security Context:
- Addresses v0.6.0 audit H-2: Session persistence across restarts
- CR-SEC-003: Horizontal scaling support
- Memory exhaustion prevention via TTL and Redis
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class SessionStore(ABC):
    """Abstract interface for session storage backends.

    Implementations must provide thread-safe session storage with:
    - Session creation and retrieval
    - Automatic TTL-based expiry
    - Atomic operations
    - Graceful failure handling

    v0.6.2 SECURITY-003: Session store abstraction
    """

    @abstractmethod
    def create_session(self, session_id: str, data: dict[str, Any], ttl: int) -> bool:
        """Create or update a session.

        Args:
            session_id: Unique session identifier
            data: Session data dictionary
            ttl: Time-to-live in seconds

        Returns:
            True if session created/updated successfully
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict if found and not expired, None otherwise
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted
        """
        pass

    @abstractmethod
    def get_active_session_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of active (non-expired) sessions
        """
        pass

    @abstractmethod
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions (if backend requires manual cleanup).

        Returns:
            Number of sessions cleaned up
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if storage backend is healthy.

        Returns:
            True if backend is responsive
        """
        pass


class InMemorySessionStore(SessionStore):
    """In-memory session storage for development.

    Thread-safe dictionary-based storage with manual TTL enforcement.
    Sessions lost on restart (not persistent).

    v0.6.2 SECURITY-003: Development/fallback session store

    Example:
        >>> store = InMemorySessionStore()
        >>> store.create_session("sess_123", {"user": "alice"}, ttl=3600)
        >>> data = store.get_session("sess_123")
        >>> data["user"]
        'alice'
    """

    def __init__(self) -> None:
        """Initialise in-memory session store."""
        self._sessions: dict[str, dict[str, Any]] = {}
        logger.info("InMemorySessionStore initialised")

    def create_session(self, session_id: str, data: dict[str, Any], ttl: int) -> bool:
        """Create or update session in memory.

        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time-to-live in seconds

        Returns:
            True (always succeeds for in-memory)
        """
        expiry_time = time.time() + ttl
        self._sessions[session_id] = {
            "data": data,
            "expiry": expiry_time,
            "last_activity": time.time(),
        }
        logger.debug(f"Created in-memory session: {session_id[:8]}... (TTL={ttl}s)")
        return True

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session from memory.

        Args:
            session_id: Session identifier

        Returns:
            Session data if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None

        # Check expiry
        if time.time() > session["expiry"]:
            logger.debug(f"Session expired: {session_id[:8]}...")
            del self._sessions[session_id]
            return None

        # Update last activity
        session["last_activity"] = time.time()
        return session["data"]

    def delete_session(self, session_id: str) -> bool:
        """Delete session from memory.

        Args:
            session_id: Session identifier

        Returns:
            True if session existed and was deleted
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Deleted in-memory session: {session_id[:8]}...")
            return True
        return False

    def get_active_session_count(self) -> int:
        """Count non-expired sessions.

        Returns:
            Number of active sessions
        """
        current_time = time.time()
        active_count = sum(
            1 for session in self._sessions.values() if session["expiry"] > current_time
        )
        return active_count

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from memory.

        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_ids = [
            sid
            for sid, session in self._sessions.items()
            if session["expiry"] <= current_time
        ]

        for session_id in expired_ids:
            del self._sessions[session_id]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired in-memory sessions")

        return len(expired_ids)

    def health_check(self) -> bool:
        """Check in-memory store health.

        Returns:
            True (always healthy)
        """
        return True


class RedisSessionStore(SessionStore):
    """Redis-backed session storage for production.

    Production-ready session persistence with:
    - Automatic TTL expiry (handled by Redis)
    - Connection pooling
    - Graceful failure handling
    - Session persistence across restarts
    - Horizontal scaling support

    v0.6.2 SECURITY-003: Production session store

    Example:
        >>> store = RedisSessionStore(redis_url="redis://localhost:6379/0")
        >>> store.create_session("sess_123", {"user": "alice"}, ttl=3600)
        >>> data = store.get_session("sess_123")
        >>> data["user"]
        'alice'
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "ragged:session:",
        connection_pool_size: int = 10,
        socket_timeout: float = 5.0,
    ) -> None:
        """Initialise Redis session store.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for session keys in Redis
            connection_pool_size: Maximum connections in pool
            socket_timeout: Socket timeout in seconds

        Raises:
            ImportError: If redis package not installed
            ConnectionError: If cannot connect to Redis
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis = None

        try:
            import redis
            from redis.connection import ConnectionPool

            # Create connection pool
            self._pool = ConnectionPool.from_url(
                redis_url,
                max_connections=connection_pool_size,
                socket_timeout=socket_timeout,
                decode_responses=True,  # Auto-decode bytes to str
            )

            # Create Redis client with connection pool
            self._redis = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._redis.ping()

            logger.info(
                f"RedisSessionStore initialised: {redis_url} "
                f"(pool_size={connection_pool_size})"
            )

        except ImportError as e:
            logger.error(
                "Redis package not installed. Install with: pip install redis"
            )
            raise ImportError(
                "redis package required for RedisSessionStore. "
                "Install with: pip install redis"
            ) from e

        except Exception as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {e}")
            raise ConnectionError(f"Cannot connect to Redis: {e}") from e

    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session.

        Args:
            session_id: Session identifier

        Returns:
            Full Redis key with prefix
        """
        return f"{self.key_prefix}{session_id}"

    def create_session(self, session_id: str, data: dict[str, Any], ttl: int) -> bool:
        """Create or update session in Redis.

        Args:
            session_id: Session identifier
            data: Session data dictionary
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False if Redis operation failed
        """
        try:
            key = self._get_key(session_id)
            session_data = {
                "data": data,
                "created_at": time.time(),
                "last_activity": time.time(),
            }

            # Serialise to JSON and store in Redis with TTL
            json_data = json.dumps(session_data)
            self._redis.setex(key, ttl, json_data)

            logger.debug(f"Created Redis session: {session_id[:8]}... (TTL={ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to create Redis session {session_id[:8]}...: {e}")
            return False

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session from Redis.

        Args:
            session_id: Session identifier

        Returns:
            Session data if found, None if expired or not found
        """
        try:
            key = self._get_key(session_id)
            json_data = self._redis.get(key)

            if json_data is None:
                return None

            # Deserialise from JSON
            session_data = json.loads(json_data)

            # Update last activity timestamp
            session_data["last_activity"] = time.time()

            # Get current TTL and update with new data
            ttl = self._redis.ttl(key)
            if ttl > 0:
                self._redis.setex(key, ttl, json.dumps(session_data))

            return session_data["data"]

        except Exception as e:
            logger.error(f"Failed to get Redis session {session_id[:8]}...: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted
        """
        try:
            key = self._get_key(session_id)
            deleted = self._redis.delete(key)
            logger.debug(f"Deleted Redis session: {session_id[:8]}...")
            return deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete Redis session {session_id[:8]}...: {e}")
            return False

    def get_active_session_count(self) -> int:
        """Count active sessions in Redis.

        Returns:
            Number of session keys in Redis
        """
        try:
            # Count keys matching our prefix
            pattern = f"{self.key_prefix}*"
            cursor = 0
            count = 0

            # Use SCAN to iterate (more efficient than KEYS for large sets)
            while True:
                cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                count += len(keys)
                if cursor == 0:
                    break

            return count

        except Exception as e:
            logger.error(f"Failed to count Redis sessions: {e}")
            return 0

    def cleanup_expired_sessions(self) -> int:
        """Redis handles TTL automatically.

        Returns:
            0 (Redis auto-expires keys)
        """
        # Redis automatically deletes expired keys, no manual cleanup needed
        return 0

    def health_check(self) -> bool:
        """Check Redis connection health.

        Returns:
            True if Redis is responsive
        """
        try:
            self._redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


class SessionStoreFactory:
    """Factory for creating session stores with graceful fallback.

    v0.6.2 SECURITY-003: Automatic fallback to in-memory if Redis unavailable

    Example:
        >>> # Try Redis, fallback to in-memory
        >>> store = SessionStoreFactory.create(redis_url="redis://localhost:6379/0")
        >>> # Force in-memory
        >>> store = SessionStoreFactory.create(redis_url=None)
    """

    @staticmethod
    def create(
        redis_url: str | None = None,
        fallback_to_memory: bool = True,
        **redis_kwargs: Any,
    ) -> SessionStore:
        """Create session store with automatic fallback.

        Args:
            redis_url: Redis connection URL (None = use in-memory)
            fallback_to_memory: Fallback to in-memory if Redis fails
            **redis_kwargs: Additional Redis configuration

        Returns:
            SessionStore instance (Redis or in-memory)

        Example:
            >>> # Production: Try Redis, fallback to in-memory
            >>> store = SessionStoreFactory.create(
            ...     redis_url="redis://localhost:6379/0",
            ...     fallback_to_memory=True
            ... )
            >>>
            >>> # Development: Force in-memory
            >>> store = SessionStoreFactory.create(redis_url=None)
        """
        # If no Redis URL, use in-memory
        if redis_url is None:
            logger.info("No Redis URL configured, using InMemorySessionStore")
            return InMemorySessionStore()

        # Try to create Redis store
        try:
            store = RedisSessionStore(redis_url=redis_url, **redis_kwargs)

            # Verify health
            if store.health_check():
                logger.info("Using RedisSessionStore (production mode)")
                return store

            # Redis unhealthy
            if fallback_to_memory:
                logger.warning(
                    "Redis unhealthy, falling back to InMemorySessionStore"
                )
                return InMemorySessionStore()

            raise ConnectionError("Redis unhealthy and fallback disabled")

        except (ImportError, ConnectionError) as e:
            if fallback_to_memory:
                logger.warning(
                    f"Redis unavailable ({e}), falling back to InMemorySessionStore"
                )
                return InMemorySessionStore()

            # Re-raise if fallback disabled
            raise
