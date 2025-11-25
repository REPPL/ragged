"""Tests for session persistence backends (v0.6.2 SECURITY-003).

Success criteria:
- InMemorySessionStore functional with TTL expiry
- RedisSessionStore with connection pooling and persistence
- SessionStoreFactory graceful fallback
- Integration with SessionSecurityMiddleware
- 100% test coverage for session stores
"""

import time
from unittest.mock import MagicMock, patch

import pytest

# Check if redis is installed
try:
    import redis  # noqa: F401

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ragged.web.session import (
    InMemorySessionStore,
    RedisSessionStore,
    SessionStore,
    SessionStoreFactory,
)


class TestSessionStoreInterface:
    """Test SessionStore abstract interface."""

    def test_sessionstore_is_abstract(self) -> None:
        """Test that SessionStore cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            SessionStore()  # type: ignore[abstract]


class TestInMemorySessionStore:
    """Test in-memory session storage."""

    @pytest.fixture
    def store(self) -> InMemorySessionStore:
        """Create in-memory session store."""
        return InMemorySessionStore()

    def test_initialization(self, store: InMemorySessionStore) -> None:
        """Test in-memory store initialisation."""
        assert store is not None
        assert store.get_active_session_count() == 0

    def test_create_session(self, store: InMemorySessionStore) -> None:
        """Test session creation."""
        session_data = {"user": "alice", "created_at": time.time()}
        success = store.create_session("sess_123", session_data, ttl=3600)

        assert success is True
        assert store.get_active_session_count() == 1

    def test_get_session(self, store: InMemorySessionStore) -> None:
        """Test session retrieval."""
        session_data = {"user": "alice", "role": "admin"}
        store.create_session("sess_123", session_data, ttl=3600)

        retrieved = store.get_session("sess_123")

        assert retrieved is not None
        assert retrieved["user"] == "alice"
        assert retrieved["role"] == "admin"

    def test_get_nonexistent_session(self, store: InMemorySessionStore) -> None:
        """Test retrieving non-existent session returns None."""
        retrieved = store.get_session("nonexistent")
        assert retrieved is None

    def test_session_expiry(self, store: InMemorySessionStore) -> None:
        """Test session expires after TTL."""
        session_data = {"user": "bob"}
        store.create_session("sess_123", session_data, ttl=1)  # 1 second TTL

        # Should exist immediately
        assert store.get_session("sess_123") is not None

        # Wait for expiry
        time.sleep(1.1)

        # Should be expired
        assert store.get_session("sess_123") is None

    def test_update_session(self, store: InMemorySessionStore) -> None:
        """Test updating existing session."""
        session_data = {"user": "alice", "count": 1}
        store.create_session("sess_123", session_data, ttl=3600)

        # Update session
        updated_data = {"user": "alice", "count": 2}
        store.create_session("sess_123", updated_data, ttl=3600)

        retrieved = store.get_session("sess_123")
        assert retrieved["count"] == 2

    def test_delete_session(self, store: InMemorySessionStore) -> None:
        """Test session deletion."""
        session_data = {"user": "alice"}
        store.create_session("sess_123", session_data, ttl=3600)

        assert store.get_active_session_count() == 1

        deleted = store.delete_session("sess_123")

        assert deleted is True
        assert store.get_active_session_count() == 0
        assert store.get_session("sess_123") is None

    def test_delete_nonexistent_session(self, store: InMemorySessionStore) -> None:
        """Test deleting non-existent session returns False."""
        deleted = store.delete_session("nonexistent")
        assert deleted is False

    def test_get_active_session_count(self, store: InMemorySessionStore) -> None:
        """Test counting active sessions."""
        assert store.get_active_session_count() == 0

        # Create 3 sessions
        for i in range(3):
            store.create_session(f"sess_{i}", {"user": f"user{i}"}, ttl=3600)

        assert store.get_active_session_count() == 3

        # Create 1 expired session
        store.create_session("sess_expired", {"user": "expired"}, ttl=1)
        time.sleep(1.1)

        # Should still be 3 (expired not counted)
        assert store.get_active_session_count() == 3

    def test_cleanup_expired_sessions(self, store: InMemorySessionStore) -> None:
        """Test cleanup of expired sessions."""
        # Create 2 active sessions
        store.create_session("sess_1", {"user": "alice"}, ttl=3600)
        store.create_session("sess_2", {"user": "bob"}, ttl=3600)

        # Create 2 expired sessions
        store.create_session("sess_3", {"user": "charlie"}, ttl=1)
        store.create_session("sess_4", {"user": "dave"}, ttl=1)
        time.sleep(1.1)

        # Cleanup
        cleaned = store.cleanup_expired_sessions()

        assert cleaned == 2
        assert store.get_active_session_count() == 2

    def test_health_check(self, store: InMemorySessionStore) -> None:
        """Test in-memory store health check."""
        assert store.health_check() is True


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis package not installed")
class TestRedisSessionStore:
    """Test Redis-backed session storage."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 1
        mock.ttl.return_value = 3600
        mock.scan.return_value = (0, [])
        return mock

    @pytest.fixture
    def store(self, mock_redis: MagicMock) -> RedisSessionStore:
        """Create Redis session store with mocked Redis."""
        # Patch the redis module import inside RedisSessionStore.__init__
        with patch.dict("sys.modules", {"redis": MagicMock()}):
            import sys

            mock_redis_module = sys.modules["redis"]

            # Mock ConnectionPool.from_url
            mock_pool = MagicMock()
            mock_redis_module.connection = MagicMock()
            mock_redis_module.connection.ConnectionPool = MagicMock()
            mock_redis_module.connection.ConnectionPool.from_url = MagicMock(
                return_value=mock_pool
            )

            # Mock Redis client creation
            mock_redis_module.Redis = MagicMock(return_value=mock_redis)

            store = RedisSessionStore(redis_url="redis://localhost:6379/0")
            store._redis = mock_redis  # Ensure _redis attribute is set
            return store

    def test_initialization(self, store: RedisSessionStore) -> None:
        """Test Redis store initialisation."""
        assert store is not None
        assert store.redis_url == "redis://localhost:6379/0"
        assert store.key_prefix == "ragged:session:"

    def test_initialization_without_redis_package(self) -> None:
        """Test initialisation fails gracefully without redis package."""
        # Temporarily remove redis from sys.modules to simulate it not being installed
        with patch.dict("sys.modules", {"redis": None}):
            with pytest.raises(ImportError, match="redis package required"):
                RedisSessionStore(redis_url="redis://localhost:6379/0")

    def test_create_session(self, store: RedisSessionStore) -> None:
        """Test session creation in Redis."""
        session_data = {"user": "alice", "role": "admin"}
        success = store.create_session("sess_123", session_data, ttl=3600)

        assert success is True
        store._redis.setex.assert_called_once()

    def test_get_session(self, store: RedisSessionStore, mock_redis: MagicMock) -> None:
        """Test session retrieval from Redis."""
        # Mock Redis get to return session data
        session_data = {"user": "alice", "role": "admin"}
        import json

        redis_value = json.dumps(
            {
                "data": session_data,
                "created_at": time.time(),
                "last_activity": time.time(),
            }
        )
        mock_redis.get.return_value = redis_value

        retrieved = store.get_session("sess_123")

        assert retrieved is not None
        assert retrieved["user"] == "alice"
        assert retrieved["role"] == "admin"

    def test_get_nonexistent_session(
        self, store: RedisSessionStore, mock_redis: MagicMock
    ) -> None:
        """Test retrieving non-existent session from Redis."""
        mock_redis.get.return_value = None

        retrieved = store.get_session("nonexistent")
        assert retrieved is None

    def test_delete_session(self, store: RedisSessionStore) -> None:
        """Test session deletion from Redis."""
        deleted = store.delete_session("sess_123")

        assert deleted is True
        store._redis.delete.assert_called_once()

    def test_get_active_session_count(
        self, store: RedisSessionStore, mock_redis: MagicMock
    ) -> None:
        """Test counting active sessions in Redis."""
        # Mock SCAN to return 3 keys
        mock_redis.scan.return_value = (
            0,
            ["ragged:session:1", "ragged:session:2", "ragged:session:3"],
        )

        count = store.get_active_session_count()

        assert count == 3

    def test_cleanup_expired_sessions(self, store: RedisSessionStore) -> None:
        """Test cleanup returns 0 (Redis auto-expires)."""
        cleaned = store.cleanup_expired_sessions()

        # Redis handles TTL automatically, no manual cleanup
        assert cleaned == 0

    def test_health_check_healthy(self, store: RedisSessionStore) -> None:
        """Test health check when Redis is healthy."""
        assert store.health_check() is True
        store._redis.ping.assert_called()

    def test_health_check_unhealthy(
        self, store: RedisSessionStore, mock_redis: MagicMock
    ) -> None:
        """Test health check when Redis is unhealthy."""
        mock_redis.ping.side_effect = Exception("Connection failed")

        assert store.health_check() is False

    def test_get_session_with_error(
        self, store: RedisSessionStore, mock_redis: MagicMock
    ) -> None:
        """Test session retrieval handles Redis errors gracefully."""
        mock_redis.get.side_effect = Exception("Redis error")

        retrieved = store.get_session("sess_123")
        assert retrieved is None

    def test_create_session_with_error(
        self, store: RedisSessionStore, mock_redis: MagicMock
    ) -> None:
        """Test session creation handles Redis errors gracefully."""
        mock_redis.setex.side_effect = Exception("Redis error")

        success = store.create_session("sess_123", {"user": "alice"}, ttl=3600)
        assert success is False

    def test_delete_session_with_error(
        self, store: RedisSessionStore, mock_redis: MagicMock
    ) -> None:
        """Test session deletion handles Redis errors gracefully."""
        mock_redis.delete.side_effect = Exception("Redis error")

        deleted = store.delete_session("sess_123")
        assert deleted is False


class TestSessionStoreFactory:
    """Test session store factory with fallback logic."""

    def test_create_inmemory_with_none_url(self) -> None:
        """Test factory creates in-memory store when redis_url is None."""
        store = SessionStoreFactory.create(redis_url=None)

        assert isinstance(store, InMemorySessionStore)

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis package not installed")
    def test_create_redis_with_valid_url(self) -> None:
        """Test factory creates Redis store with valid URL."""
        with patch.dict("sys.modules", {"redis": MagicMock()}):
            import sys

            mock_redis_module = sys.modules["redis"]

            # Mock successful Redis connection
            mock_pool = MagicMock()
            mock_client = MagicMock()
            mock_client.ping.return_value = True

            mock_redis_module.connection = MagicMock()
            mock_redis_module.connection.ConnectionPool = MagicMock()
            mock_redis_module.connection.ConnectionPool.from_url = MagicMock(
                return_value=mock_pool
            )
            mock_redis_module.Redis = MagicMock(return_value=mock_client)

            store = SessionStoreFactory.create(redis_url="redis://localhost:6379/0")

            assert isinstance(store, RedisSessionStore)

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis package not installed")
    def test_fallback_to_inmemory_when_redis_unavailable(self) -> None:
        """Test factory falls back to in-memory when Redis unavailable."""
        with patch.dict("sys.modules", {"redis": MagicMock()}):
            import sys

            mock_redis_module = sys.modules["redis"]

            # Mock Redis connection failure
            mock_redis_module.connection = MagicMock()
            mock_redis_module.connection.ConnectionPool = MagicMock()
            mock_redis_module.connection.ConnectionPool.from_url = MagicMock(
                side_effect=ConnectionError("Cannot connect")
            )

            store = SessionStoreFactory.create(
                redis_url="redis://localhost:6379/0", fallback_to_memory=True
            )

            assert isinstance(store, InMemorySessionStore)

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis package not installed")
    def test_raise_error_when_fallback_disabled(self) -> None:
        """Test factory raises error when Redis unavailable and fallback disabled."""
        with patch.dict("sys.modules", {"redis": MagicMock()}):
            import sys

            mock_redis_module = sys.modules["redis"]

            # Mock Redis connection failure
            mock_redis_module.connection = MagicMock()
            mock_redis_module.connection.ConnectionPool = MagicMock()
            mock_redis_module.connection.ConnectionPool.from_url = MagicMock(
                side_effect=ConnectionError("Cannot connect")
            )

            with pytest.raises(ConnectionError):
                SessionStoreFactory.create(
                    redis_url="redis://localhost:6379/0", fallback_to_memory=False
                )

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis package not installed")
    def test_fallback_when_redis_unhealthy(self) -> None:
        """Test factory falls back when Redis health check fails."""
        with patch.dict("sys.modules", {"redis": MagicMock()}):
            import sys

            mock_redis_module = sys.modules["redis"]

            # Mock Redis connection succeeds but health check fails
            mock_pool = MagicMock()
            mock_client = MagicMock()
            mock_client.ping.return_value = False

            mock_redis_module.connection = MagicMock()
            mock_redis_module.connection.ConnectionPool = MagicMock()
            mock_redis_module.connection.ConnectionPool.from_url = MagicMock(
                return_value=mock_pool
            )
            mock_redis_module.Redis = MagicMock(return_value=mock_client)

            store = SessionStoreFactory.create(
                redis_url="redis://localhost:6379/0", fallback_to_memory=True
            )

            assert isinstance(store, InMemorySessionStore)

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis package not installed")
    def test_fallback_on_import_error(self) -> None:
        """Test factory falls back when redis package not installed."""
        # Simulate ImportError during Redis instantiation
        with patch(
            "ragged.web.session.store.RedisSessionStore.__init__",
            side_effect=ImportError("No module named redis"),
        ):
            store = SessionStoreFactory.create(
                redis_url="redis://localhost:6379/0", fallback_to_memory=True
            )

            assert isinstance(store, InMemorySessionStore)


class TestSessionStoreIntegration:
    """Integration tests for session stores with middleware."""

    @pytest.fixture
    def inmemory_store(self) -> InMemorySessionStore:
        """Create in-memory store."""
        return InMemorySessionStore()

    def test_session_lifecycle_inmemory(
        self, inmemory_store: InMemorySessionStore
    ) -> None:
        """Test complete session lifecycle with in-memory store."""
        # Create session
        session_data = {
            "user": "alice",
            "created_at": time.time(),
            "csrf_token": "token123",
        }
        inmemory_store.create_session("sess_123", session_data, ttl=3600)

        # Retrieve session
        retrieved = inmemory_store.get_session("sess_123")
        assert retrieved["user"] == "alice"
        assert retrieved["csrf_token"] == "token123"

        # Update session
        retrieved["page_views"] = 5
        inmemory_store.create_session("sess_123", retrieved, ttl=3600)

        # Verify update
        updated = inmemory_store.get_session("sess_123")
        assert updated["page_views"] == 5

        # Delete session
        inmemory_store.delete_session("sess_123")
        assert inmemory_store.get_session("sess_123") is None

    def test_concurrent_session_access(
        self, inmemory_store: InMemorySessionStore
    ) -> None:
        """Test concurrent access to multiple sessions."""
        # Create multiple sessions
        for i in range(10):
            inmemory_store.create_session(
                f"sess_{i}", {"user": f"user{i}", "count": i}, ttl=3600
            )

        assert inmemory_store.get_active_session_count() == 10

        # Access sessions concurrently (simulated)
        for i in range(10):
            session = inmemory_store.get_session(f"sess_{i}")
            assert session["user"] == f"user{i}"
            assert session["count"] == i

    def test_session_expiry_boundary(
        self, inmemory_store: InMemorySessionStore
    ) -> None:
        """Test session expiry boundary conditions."""
        # Create session with 2-second TTL
        inmemory_store.create_session("sess_123", {"user": "alice"}, ttl=2)

        # Should exist at 1 second
        time.sleep(1)
        assert inmemory_store.get_session("sess_123") is not None

        # Should be expired at 2.1 seconds
        time.sleep(1.1)
        assert inmemory_store.get_session("sess_123") is None
