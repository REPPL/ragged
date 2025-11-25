"""Session management for web UI and API.

v0.6.2 SECURITY-003: Production-ready session persistence

Provides:
- SessionStore interface for pluggable backends
- InMemorySessionStore for development
- RedisSessionStore for production
- SessionStoreFactory for automatic fallback
"""

from ragged.web.session.store import (
    InMemorySessionStore,
    RedisSessionStore,
    SessionStore,
    SessionStoreFactory,
)

__all__ = [
    "SessionStore",
    "InMemorySessionStore",
    "RedisSessionStore",
    "SessionStoreFactory",
]
