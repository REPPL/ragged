"""Authentication and user management for ragged.

Phase 0 Infrastructure: User identity abstraction enabling:
- Single-user mode (default, backward compatible)
- Future multi-user collaboration (v1.5)
- Enterprise identity integration (v2.0)

Usage:
    >>> from ragged.auth import get_current_user, User
    >>>
    >>> # Get current user (default in single-user mode)
    >>> user = get_current_user()
    >>> print(user.display_name)
    'Default User'
"""

from ragged.auth.user import (
    User,
    UserRole,
    UserManager,
    get_current_user,
    get_user_manager,
)

__all__ = [
    "User",
    "UserRole",
    "UserManager",
    "get_current_user",
    "get_user_manager",
]
