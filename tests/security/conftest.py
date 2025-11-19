"""Pytest fixtures for security tests.

v0.2.10 FEAT-SEC-003: Security testing framework.

Provides common fixtures for:
- Temporary directories with cleanup
- Session managers for testing
- Cache instances for testing
- Security test markers
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.core.session import SessionManager
from src.retrieval.cache import QueryCache


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide temporary directory that is cleaned up after test.

    Yields:
        Path to temporary directory

    Security: Ensures test data doesn't persist on filesystem.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def session_manager(temp_dir: Path) -> SessionManager:
    """Provide fresh SessionManager instance for testing.

    Args:
        temp_dir: Temporary directory for session storage

    Returns:
        SessionManager instance with test configuration

    Security: Isolated session manager per test to prevent cross-test contamination.
    """
    # Reset singleton for testing
    SessionManager._instance = None

    manager = SessionManager(
        session_ttl=3600,  # 1 hour
        enable_persistence=False,  # Disable for tests (faster)
        session_dir=temp_dir / "sessions",
    )

    return manager


@pytest.fixture
def query_cache() -> QueryCache:
    """Provide fresh QueryCache instance for testing.

    Returns:
        QueryCache instance with test configuration

    Security: Fresh cache per test to prevent cross-test data leakage.
    """
    return QueryCache(maxsize=128, ttl_seconds=None)


@pytest.fixture
def isolated_sessions(session_manager: SessionManager) -> tuple[str, str]:
    """Provide two isolated session IDs for testing.

    Args:
        session_manager: SessionManager fixture

    Returns:
        Tuple of (session_id_1, session_id_2)

    Security: Used to test cross-session isolation.
    """
    session1 = session_manager.create_session(metadata={"user": "user1"})
    session2 = session_manager.create_session(metadata={"user": "user2"})

    return session1.session_id, session2.session_id
