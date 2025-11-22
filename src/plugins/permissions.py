"""Permission system for plugin security.

Implements fine-grained permission model for plugin capabilities,
ensuring plugins can only access explicitly granted permissions.

SECURITY FIX (HIGH-2): Added thread-safe locking for permission operations
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Dict, Optional, List
from pathlib import Path
import json
import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Types of permissions plugins can request."""

    # File System Permissions
    READ_DOCUMENTS = "read:documents"
    WRITE_DOCUMENTS = "write:documents"
    READ_CONFIG = "read:config"
    WRITE_CONFIG = "write:config"

    # Network Permissions
    NETWORK_NONE = "network:none"
    NETWORK_API = "network:api"
    NETWORK_DOWNLOAD = "network:download"

    # System Permissions
    SYSTEM_EMBEDDING = "system:embedding"
    SYSTEM_VECTORSTORE = "system:vectorstore"
    SYSTEM_MEMORY = "system:memory"


@dataclass
class PluginPermission:
    """Individual permission with metadata."""

    permission_type: PermissionType
    granted: bool = False
    granted_at: Optional[str] = None
    required: bool = True
    description: str = ""

    def to_dict(self) -> Dict:
        """Serialise to dictionary."""
        return {
            "type": self.permission_type.value,
            "granted": self.granted,
            "granted_at": self.granted_at,
            "required": self.required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PluginPermission":
        """Deserialise from dictionary."""
        return cls(
            permission_type=PermissionType(data["type"]),
            granted=data.get("granted", False),
            granted_at=data.get("granted_at"),
            required=data.get("required", True),
            description=data.get("description", ""),
        )


@dataclass
class PluginPermissions:
    """Collection of permissions for a plugin.

    SECURITY FIX (HIGH-2): Thread-safe permission operations with locking.
    """

    plugin_name: str
    plugin_version: str
    required_permissions: Set[PermissionType] = field(default_factory=set)
    optional_permissions: Set[PermissionType] = field(default_factory=set)
    granted_permissions: Set[PermissionType] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def add_required(self, permission: PermissionType) -> None:
        """Add a required permission (thread-safe)."""
        with self._lock:
            self.required_permissions.add(permission)

    def add_optional(self, permission: PermissionType) -> None:
        """Add an optional permission (thread-safe)."""
        with self._lock:
            self.optional_permissions.add(permission)

    def grant(self, permission: PermissionType) -> None:
        """Grant a permission (thread-safe).

        SECURITY FIX (HIGH-2): Atomic check-and-grant to prevent race conditions.
        """
        with self._lock:
            if permission not in self.required_permissions and permission not in self.optional_permissions:
                raise ValueError(f"Permission {permission.value} not requested by plugin")
            self.granted_permissions.add(permission)
            logger.info(f"Granted {permission.value} to {self.plugin_name}")

    def revoke(self, permission: PermissionType) -> None:
        """Revoke a permission (thread-safe).

        SECURITY FIX (HIGH-2): Atomic revocation to prevent race conditions.
        """
        with self._lock:
            if permission in self.granted_permissions:
                self.granted_permissions.remove(permission)
                logger.info(f"Revoked {permission.value} from {self.plugin_name}")

    def has_permission(self, permission: PermissionType) -> bool:
        """Check if permission is granted (thread-safe)."""
        with self._lock:
            return permission in self.granted_permissions

    def all_required_granted(self) -> bool:
        """Check if all required permissions are granted (thread-safe)."""
        with self._lock:
            return self.required_permissions.issubset(self.granted_permissions)

    def to_dict(self) -> Dict:
        """Serialise to dictionary (thread-safe)."""
        with self._lock:
            return {
                "plugin_name": self.plugin_name,
                "plugin_version": self.plugin_version,
                "required": [p.value for p in self.required_permissions],
                "optional": [p.value for p in self.optional_permissions],
                "granted": [p.value for p in self.granted_permissions],
            }

    @classmethod
    def from_dict(cls, data: Dict) -> "PluginPermissions":
        """Deserialise from dictionary.

        Note: Creates new instance, no locking needed during construction.
        """
        return cls(
            plugin_name=data["plugin_name"],
            plugin_version=data["plugin_version"],
            required_permissions={PermissionType(p) for p in data.get("required", [])},
            optional_permissions={PermissionType(p) for p in data.get("optional", [])},
            granted_permissions={PermissionType(p) for p in data.get("granted", [])},
        )


class PermissionManager:
    """Manages permissions for all plugins.

    SECURITY FIX (HIGH-2): Thread-safe permission management with locking.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialise permission manager.

        Args:
            storage_path: Path to store permissions (defaults to ~/.ragged/plugins/permissions.json)
        """
        if storage_path is None:
            storage_path = Path.home() / ".ragged" / "plugins" / "permissions.json"
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._permissions: Dict[str, PluginPermissions] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._file_lock = threading.Lock()  # Separate lock for file I/O
        self._load()

    def _load(self) -> None:
        """Load permissions from storage (thread-safe).

        SECURITY FIX (HIGH-2): File I/O with locking to prevent corruption.
        """
        if self.storage_path.exists():
            try:
                with self._file_lock:
                    with open(self.storage_path, "r") as f:
                        data = json.load(f)

                # Update in-memory permissions with lock
                with self._lock:
                    for plugin_data in data.get("plugins", []):
                        perms = PluginPermissions.from_dict(plugin_data)
                        self._permissions[perms.plugin_name] = perms

                logger.info(f"Loaded permissions for {len(self._permissions)} plugins")
            except Exception as e:
                logger.error(f"Failed to load permissions: {e}")

    def _save(self) -> None:
        """Save permissions to storage (thread-safe).

        SECURITY FIX (HIGH-2): Atomic file write with locking to prevent corruption.
        """
        import os
        import uuid

        try:
            # Serialize permissions while holding lock
            with self._lock:
                data = {"plugins": [p.to_dict() for p in self._permissions.values()]}

            # Write to file with file lock
            with self._file_lock:
                # Atomic write: write to unique temp file then rename
                # Use UUID to avoid conflicts between multiple processes
                temp_path = self.storage_path.parent / f"{self.storage_path.stem}_{uuid.uuid4().hex}.tmp"

                try:
                    with open(temp_path, "w") as f:
                        json.dump(data, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())  # Ensure data written to disk

                    # Atomic rename (POSIX guarantees atomicity)
                    temp_path.replace(self.storage_path)

                finally:
                    # Cleanup temp file if it still exists (on error)
                    if temp_path.exists():
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass

            logger.debug("Saved permissions to storage")
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")

    def get_permissions(self, plugin_name: str) -> Optional[PluginPermissions]:
        """Get permissions for a plugin (thread-safe).

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginPermissions if exists, None otherwise
        """
        with self._lock:
            return self._permissions.get(plugin_name)

    def register_plugin(self, permissions: PluginPermissions) -> None:
        """Register a plugin with its requested permissions (thread-safe).

        Args:
            permissions: Plugin permissions to register
        """
        with self._lock:
            self._permissions[permissions.plugin_name] = permissions
        self._save()
        logger.info(f"Registered plugin {permissions.plugin_name}")

    def grant_permission(self, plugin_name: str, permission: PermissionType) -> None:
        """Grant a permission to a plugin (thread-safe).

        SECURITY FIX (HIGH-2): Atomic check-and-grant to prevent TOCTOU race conditions.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to grant

        Raises:
            ValueError: If plugin not registered or permission not requested
        """
        with self._lock:
            if plugin_name not in self._permissions:
                raise ValueError(f"Plugin {plugin_name} not registered")
            # grant() is already thread-safe, but we hold manager lock during call
            self._permissions[plugin_name].grant(permission)
        self._save()

    def revoke_permission(self, plugin_name: str, permission: PermissionType) -> None:
        """Revoke a permission from a plugin (thread-safe).

        SECURITY FIX (HIGH-2): Atomic revocation to prevent race conditions.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to revoke
        """
        with self._lock:
            if plugin_name in self._permissions:
                # revoke() is already thread-safe, but we hold manager lock during call
                self._permissions[plugin_name].revoke(permission)
        self._save()

    def check_permission(self, plugin_name: str, permission: PermissionType) -> bool:
        """Check if a plugin has a specific permission (thread-safe).

        Args:
            plugin_name: Name of the plugin
            permission: Permission to check

        Returns:
            True if permission granted, False otherwise
        """
        with self._lock:
            if plugin_name not in self._permissions:
                return False
            # has_permission() is already thread-safe, but we hold manager lock during call
            return self._permissions[plugin_name].has_permission(permission)

    def list_plugins(self) -> List[str]:
        """List all registered plugins (thread-safe).

        Returns:
            List of plugin names
        """
        with self._lock:
            return list(self._permissions.keys())

    def get_all_permissions(self) -> Dict[str, PluginPermissions]:
        """Get all permissions for all plugins (thread-safe).

        Returns:
            Dictionary mapping plugin names to their permissions
        """
        with self._lock:
            return self._permissions.copy()
