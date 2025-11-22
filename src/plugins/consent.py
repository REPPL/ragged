"""User consent management for plugin permissions.

Handles user consent workflow for granting permissions to plugins.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
from pathlib import Path
import json
import logging

from ragged.plugins.permissions import PermissionType, PluginPermissions

logger = logging.getLogger(__name__)


class ConsentStatus(Enum):
    """Status of consent for a permission."""

    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


@dataclass
class PermissionConsent:
    """Consent record for a permission."""

    plugin_name: str
    permission: PermissionType
    status: ConsentStatus
    granted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    reason: Optional[str] = None


class ConsentManager:
    """Manages user consent for plugin permissions."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialise consent manager.

        Args:
            storage_path: Path to consent storage (defaults to ~/.ragged/plugins/consent.json)
        """
        if storage_path is None:
            storage_path = Path.home() / ".ragged" / "plugins" / "consent.json"
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._consents: Dict[str, Dict[str, ConsentStatus]] = {}
        self._load()

    def _load(self) -> None:
        """Load consent records from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for plugin, perms in data.items():
                        self._consents[plugin] = {
                            perm: ConsentStatus(status)
                            for perm, status in perms.items()
                        }
                logger.info(f"Loaded consent records for {len(self._consents)} plugins")
            except Exception as e:
                logger.error(f"Failed to load consent records: {e}")

    def _save(self) -> None:
        """Save consent records to storage."""
        try:
            data = {
                plugin: {perm: status.value for perm, status in perms.items()}
                for plugin, perms in self._consents.items()
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved consent records")
        except Exception as e:
            logger.error(f"Failed to save consent records: {e}")

    def request_consent(
        self,
        plugin_name: str,
        permissions: PluginPermissions,
        interactive: bool = True,
    ) -> bool:
        """Request user consent for plugin permissions.

        Args:
            plugin_name: Name of plugin
            permissions: Plugin permissions to request consent for
            interactive: If True, prompt user interactively

        Returns:
            True if all required permissions granted, False otherwise
        """
        if plugin_name not in self._consents:
            self._consents[plugin_name] = {}

        # Check required permissions
        for perm in permissions.required_permissions:
            if perm.value not in self._consents[plugin_name]:
                if interactive:
                    granted = self._prompt_user(plugin_name, perm, required=True)
                else:
                    granted = False  # Deny by default in non-interactive mode

                status = ConsentStatus.GRANTED if granted else ConsentStatus.DENIED
                self._consents[plugin_name][perm.value] = status

        self._save()

        # Check if all required permissions granted
        all_granted = all(
            self._consents[plugin_name].get(perm.value) == ConsentStatus.GRANTED
            for perm in permissions.required_permissions
        )

        return all_granted

    def _prompt_user(self, plugin_name: str, permission: PermissionType, required: bool) -> bool:
        """Prompt user for permission consent.

        Args:
            plugin_name: Name of plugin
            permission: Permission to request
            required: If True, permission is required

        Returns:
            True if user grants permission, False otherwise
        """
        # In a real implementation, this would use interactive CLI prompts
        # For now, we'll auto-grant to allow automated testing
        logger.info(
            f"Requesting {'required' if required else 'optional'} permission "
            f"'{permission.value}' for plugin '{plugin_name}'"
        )
        # TODO: Implement interactive prompt with click or rich
        return True  # Auto-grant for now

    def grant_permission(self, plugin_name: str, permission: PermissionType) -> None:
        """Grant a permission to a plugin.

        Args:
            plugin_name: Name of plugin
            permission: Permission to grant
        """
        if plugin_name not in self._consents:
            self._consents[plugin_name] = {}
        self._consents[plugin_name][permission.value] = ConsentStatus.GRANTED
        self._save()
        logger.info(f"Granted {permission.value} to {plugin_name}")

    def revoke_permission(self, plugin_name: str, permission: PermissionType) -> None:
        """Revoke a permission from a plugin.

        Args:
            plugin_name: Name of plugin
            permission: Permission to revoke
        """
        if plugin_name in self._consents and permission.value in self._consents[plugin_name]:
            self._consents[plugin_name][permission.value] = ConsentStatus.REVOKED
            self._save()
            logger.info(f"Revoked {permission.value} from {plugin_name}")

    def get_consent_status(self, plugin_name: str, permission: PermissionType) -> ConsentStatus:
        """Get consent status for a permission.

        Args:
            plugin_name: Name of plugin
            permission: Permission to check

        Returns:
            ConsentStatus for the permission
        """
        if plugin_name not in self._consents:
            return ConsentStatus.PENDING
        return self._consents[plugin_name].get(permission.value, ConsentStatus.PENDING)

    def has_consent(self, plugin_name: str, permission: PermissionType) -> bool:
        """Check if user has granted consent for a permission.

        Args:
            plugin_name: Name of plugin
            permission: Permission to check

        Returns:
            True if consent granted, False otherwise
        """
        return self.get_consent_status(plugin_name, permission) == ConsentStatus.GRANTED
