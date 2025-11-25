"""User identity and session management.

Phase 0 Infrastructure: User abstraction layer providing:
- Single-user default mode (backward compatible)
- User identity separate from session
- Role-based access control foundation
- Integration with existing persona/profile system

Design Principles:
- Backward compatible: Single-user mode requires no configuration
- Extensible: Multi-user, enterprise auth can be added later
- Privacy-first: User data stored locally, GDPR compliant
- Thread-safe: Concurrent access supported

Usage:
    >>> from ragged.auth.user import get_current_user, User
    >>>
    >>> # Single-user mode (default)
    >>> user = get_current_user()
    >>> print(user.user_id)  # 'default'
    >>>
    >>> # Create session for user
    >>> session = user.create_session()
    >>> print(session.session_id)
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role for access control.

    Defines permission levels for future role-based access control.
    Single-user mode defaults to OWNER with full permissions.
    """

    VIEWER = "viewer"  # Read-only access
    USER = "user"  # Standard access (query, view documents)
    EDITOR = "editor"  # Can modify documents and collections
    ADMIN = "admin"  # Can manage settings and users
    OWNER = "owner"  # Full access (single-user default)


@dataclass
class UserPreferences:
    """User-specific preferences and settings.

    Stores UI preferences, default behaviours, and personalisation options.
    These preferences are separate from system configuration.

    Attributes:
        theme: UI theme preference (light, dark, system)
        language: Preferred language code (e.g., "en-GB")
        default_collection: Default collection for queries
        results_per_page: Number of results to display
        enable_history: Whether to track query history
        custom_settings: Additional user-defined settings
    """

    theme: str = "system"
    language: str = "en-GB"
    default_collection: str | None = None
    results_per_page: int = 10
    enable_history: bool = True
    custom_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """Represents a user identity in the system.

    In single-user mode, a default user is automatically created.
    In multi-user mode (v1.5+), users can be created and managed.

    Attributes:
        user_id: Unique user identifier (default: "default")
        display_name: Human-readable name
        email: Optional email address
        role: User role for access control
        preferences: User-specific preferences
        created_at: Account creation timestamp
        last_active: Last activity timestamp
        metadata: Additional user metadata
        profile_id: Link to InterestProfile for personalisation
    """

    user_id: str = "default"
    display_name: str = "Default User"
    email: str | None = None
    role: UserRole = UserRole.OWNER
    preferences: UserPreferences = field(default_factory=UserPreferences)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    profile_id: str | None = None

    def __post_init__(self):
        """Validate user data after initialisation."""
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if not self.display_name:
            self.display_name = f"User {self.user_id[:8]}"

    def is_default_user(self) -> bool:
        """Check if this is the default single-user mode user.

        Returns:
            True if this is the default user
        """
        return self.user_id == "default"

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has at least the required role level.

        Args:
            required_role: Minimum role required for the action

        Returns:
            True if user has sufficient permissions
        """
        role_hierarchy = {
            UserRole.VIEWER: 0,
            UserRole.USER: 1,
            UserRole.EDITOR: 2,
            UserRole.ADMIN: 3,
            UserRole.OWNER: 4,
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]

    def update_last_active(self) -> None:
        """Update the last_active timestamp to now."""
        self.last_active = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary for serialisation.

        Returns:
            Dictionary representation of the user
        """
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "email": self.email,
            "role": self.role.value,
            "preferences": {
                "theme": self.preferences.theme,
                "language": self.preferences.language,
                "default_collection": self.preferences.default_collection,
                "results_per_page": self.preferences.results_per_page,
                "enable_history": self.preferences.enable_history,
                "custom_settings": self.preferences.custom_settings,
            },
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
            "profile_id": self.profile_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create a User from a dictionary.

        Args:
            data: Dictionary containing user data

        Returns:
            User instance
        """
        preferences_data = data.get("preferences", {})
        preferences = UserPreferences(
            theme=preferences_data.get("theme", "system"),
            language=preferences_data.get("language", "en-GB"),
            default_collection=preferences_data.get("default_collection"),
            results_per_page=preferences_data.get("results_per_page", 10),
            enable_history=preferences_data.get("enable_history", True),
            custom_settings=preferences_data.get("custom_settings", {}),
        )

        return cls(
            user_id=data.get("user_id", "default"),
            display_name=data.get("display_name", "Default User"),
            email=data.get("email"),
            role=UserRole(data.get("role", "owner")),
            preferences=preferences,
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            last_active=datetime.fromisoformat(data["last_active"])
            if "last_active" in data
            else datetime.now(),
            metadata=data.get("metadata", {}),
            profile_id=data.get("profile_id"),
        )


class UserManager:
    """Manages user lifecycle and authentication.

    In single-user mode, provides a default user automatically.
    In multi-user mode, handles user creation, lookup, and management.

    Thread Safety:
        All public methods are thread-safe.

    Example:
        >>> manager = UserManager()
        >>> user = manager.get_user("default")
        >>> print(user.display_name)
        'Default User'
    """

    def __init__(self):
        """Initialise user manager with default user."""
        self._users: dict[str, User] = {}
        self._lock = threading.RLock()
        self._current_user_id: str = "default"

        # Create default user for single-user mode
        self._create_default_user()

        logger.debug("UserManager initialised with default user")

    def _create_default_user(self) -> None:
        """Create the default user for single-user mode."""
        default_user = User(
            user_id="default",
            display_name="Default User",
            role=UserRole.OWNER,
        )
        self._users["default"] = default_user

    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID.

        Args:
            user_id: User identifier

        Returns:
            User if found, None otherwise
        """
        with self._lock:
            return self._users.get(user_id)

    def get_current_user(self) -> User:
        """Get the currently active user.

        In single-user mode, returns the default user.
        In multi-user mode, returns the authenticated user.

        Returns:
            Current active user
        """
        with self._lock:
            user = self._users.get(self._current_user_id)
            if user is None:
                # Fallback to default user
                user = self._users["default"]
            user.update_last_active()
            return user

    def set_current_user(self, user_id: str) -> bool:
        """Set the current active user.

        Args:
            user_id: User identifier to set as current

        Returns:
            True if user was found and set, False otherwise
        """
        with self._lock:
            if user_id in self._users:
                self._current_user_id = user_id
                logger.debug(f"Current user set to {user_id}")
                return True
            logger.warning(f"User {user_id} not found")
            return False

    def create_user(
        self,
        display_name: str,
        email: str | None = None,
        role: UserRole = UserRole.USER,
        user_id: str | None = None,
    ) -> User:
        """Create a new user.

        Args:
            display_name: Human-readable name
            email: Optional email address
            role: User role (default: USER)
            user_id: Optional specific user ID (auto-generated if not provided)

        Returns:
            Newly created User

        Raises:
            ValueError: If user_id already exists
        """
        if user_id is None:
            user_id = str(uuid.uuid4())

        with self._lock:
            if user_id in self._users:
                raise ValueError(f"User {user_id} already exists")

            user = User(
                user_id=user_id,
                display_name=display_name,
                email=email,
                role=role,
            )
            self._users[user_id] = user

            logger.info(f"Created user {user_id}: {display_name}")
            return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user.

        Cannot delete the default user.

        Args:
            user_id: User identifier to delete

        Returns:
            True if user was deleted, False otherwise
        """
        if user_id == "default":
            logger.warning("Cannot delete default user")
            return False

        with self._lock:
            if user_id in self._users:
                del self._users[user_id]
                # Reset current user if deleted
                if self._current_user_id == user_id:
                    self._current_user_id = "default"
                logger.info(f"Deleted user {user_id}")
                return True

            logger.warning(f"User {user_id} not found for deletion")
            return False

    def list_users(self) -> list[User]:
        """List all users.

        Returns:
            List of all users
        """
        with self._lock:
            return list(self._users.values())

    def get_user_count(self) -> int:
        """Get total number of users.

        Returns:
            User count
        """
        with self._lock:
            return len(self._users)

    def is_single_user_mode(self) -> bool:
        """Check if running in single-user mode.

        Returns:
            True if only the default user exists
        """
        with self._lock:
            return len(self._users) == 1 and "default" in self._users

    def export_user_data(self, user_id: str) -> dict[str, Any] | None:
        """Export all user data for GDPR compliance.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing all user data, or None if user not found
        """
        with self._lock:
            user = self._users.get(user_id)
            if user is None:
                return None

            return {
                "user": user.to_dict(),
                "exported_at": datetime.now().isoformat(),
            }

    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data for GDPR compliance (right to be forgotten).

        Args:
            user_id: User identifier

        Returns:
            True if user data was deleted
        """
        return self.delete_user(user_id)


# === Global User Manager Instance ===


_user_manager: UserManager | None = None
_user_manager_lock = threading.Lock()


def get_user_manager() -> UserManager:
    """Get the global user manager instance.

    Returns the same UserManager instance on subsequent calls.
    Thread-safe singleton pattern.

    Returns:
        UserManager: The global user manager instance

    Example:
        >>> from ragged.auth.user import get_user_manager
        >>> manager = get_user_manager()
        >>> user = manager.get_current_user()
    """
    global _user_manager

    if _user_manager is None:
        with _user_manager_lock:
            if _user_manager is None:
                _user_manager = UserManager()
                logger.info("Global UserManager created")

    return _user_manager


def get_current_user() -> User:
    """Convenience function to get the current user.

    In single-user mode, returns the default user.
    In multi-user mode, returns the authenticated user.

    Returns:
        Current active user

    Example:
        >>> from ragged.auth.user import get_current_user
        >>> user = get_current_user()
        >>> print(user.display_name)
        'Default User'
    """
    return get_user_manager().get_current_user()


def reset_user_manager() -> None:
    """Reset the global user manager (for testing).

    Creates a new UserManager instance, discarding all users.
    """
    global _user_manager

    with _user_manager_lock:
        _user_manager = UserManager()
        logger.info("Global UserManager reset")
