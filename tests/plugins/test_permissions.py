"""Tests for plugin permission system."""

import pytest
from pathlib import Path
import tempfile
import json

from ragged.plugins.permissions import (
    PermissionType,
    PluginPermission,
    PluginPermissions,
    PermissionManager,
)


class TestPluginPermission:
    """Tests for PluginPermission class."""

    def test_create_permission(self):
        """Test creating a permission."""
        perm = PluginPermission(
            permission_type=PermissionType.READ_DOCUMENTS,
            granted=True,
            description="Read documents",
        )
        assert perm.permission_type == PermissionType.READ_DOCUMENTS
        assert perm.granted is True

    def test_permission_to_dict(self):
        """Test serialising permission to dict."""
        perm = PluginPermission(permission_type=PermissionType.READ_DOCUMENTS, granted=True)
        data = perm.to_dict()
        assert data["type"] == "read:documents"
        assert data["granted"] is True

    def test_permission_from_dict(self):
        """Test deserialising permission from dict."""
        data = {"type": "read:documents", "granted": True, "required": True}
        perm = PluginPermission.from_dict(data)
        assert perm.permission_type == PermissionType.READ_DOCUMENTS
        assert perm.granted is True


class TestPluginPermissions:
    """Tests for PluginPermissions class."""

    def test_create_permissions(self):
        """Test creating plugin permissions."""
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        assert perms.plugin_name == "test-plugin"
        assert len(perms.required_permissions) == 0

    def test_add_required_permission(self):
        """Test adding required permission."""
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)
        assert PermissionType.READ_DOCUMENTS in perms.required_permissions

    def test_grant_permission(self):
        """Test granting a permission."""
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)
        perms.grant(PermissionType.READ_DOCUMENTS)
        assert perms.has_permission(PermissionType.READ_DOCUMENTS)

    def test_grant_unrquested_permission_raises(self):
        """Test that granting unrequested permission raises error."""
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        with pytest.raises(ValueError):
            perms.grant(PermissionType.READ_DOCUMENTS)

    def test_revoke_permission(self):
        """Test revoking a permission."""
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)
        perms.grant(PermissionType.READ_DOCUMENTS)
        perms.revoke(PermissionType.READ_DOCUMENTS)
        assert not perms.has_permission(PermissionType.READ_DOCUMENTS)

    def test_all_required_granted(self):
        """Test checking if all required permissions granted."""
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)
        perms.add_required(PermissionType.SYSTEM_EMBEDDING)

        assert not perms.all_required_granted()

        perms.grant(PermissionType.READ_DOCUMENTS)
        assert not perms.all_required_granted()

        perms.grant(PermissionType.SYSTEM_EMBEDDING)
        assert perms.all_required_granted()


class TestPermissionManager:
    """Tests for PermissionManager."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "permissions.json"

    def test_create_manager(self, temp_storage):
        """Test creating permission manager."""
        manager = PermissionManager(storage_path=temp_storage)
        assert manager.storage_path == temp_storage

    def test_register_plugin(self, temp_storage):
        """Test registering a plugin."""
        manager = PermissionManager(storage_path=temp_storage)
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)

        manager.register_plugin(perms)
        assert "test-plugin" in manager.list_plugins()

    def test_grant_permission(self, temp_storage):
        """Test granting permission through manager."""
        manager = PermissionManager(storage_path=temp_storage)
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)
        manager.register_plugin(perms)

        manager.grant_permission("test-plugin", PermissionType.READ_DOCUMENTS)
        assert manager.check_permission("test-plugin", PermissionType.READ_DOCUMENTS)

    def test_persistence(self, temp_storage):
        """Test that permissions persist across instances."""
        manager1 = PermissionManager(storage_path=temp_storage)
        perms = PluginPermissions(plugin_name="test-plugin", plugin_version="1.0.0")
        perms.add_required(PermissionType.READ_DOCUMENTS)
        manager1.register_plugin(perms)
        manager1.grant_permission("test-plugin", PermissionType.READ_DOCUMENTS)

        # Create new manager instance
        manager2 = PermissionManager(storage_path=temp_storage)
        assert manager2.check_permission("test-plugin", PermissionType.READ_DOCUMENTS)
