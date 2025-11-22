"""Plugin management system.

Central registry and lifecycle management for all plugins.
"""

import json
import logging
from pathlib import Path
from typing import Any

from ragged.plugins.audit import AuditLogger
from ragged.plugins.interfaces import Plugin
from ragged.plugins.loader import PluginLoader
from ragged.plugins.permissions import PermissionManager

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin lifecycle and registry."""

    def __init__(self, config_path: Path | None = None):
        """Initialise plugin manager.

        Args:
            config_path: Path to plugin configuration (defaults to ~/.ragged/plugins/config.json)
        """
        if config_path is None:
            config_path = Path.home() / ".ragged" / "plugins" / "config.json"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.loader = PluginLoader()
        self.permission_manager = PermissionManager()
        self.audit_logger = AuditLogger()

        self._enabled_plugins: dict[str, dict[str, Any]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load plugin configuration from storage."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    self._enabled_plugins = data.get("enabled_plugins", {})
                logger.info(f"Loaded configuration for {len(self._enabled_plugins)} enabled plugins")
            except Exception as e:
                logger.error(f"Failed to load plugin configuration: {e}")

    def _save_config(self) -> None:
        """Save plugin configuration to storage."""
        try:
            data = {"enabled_plugins": self._enabled_plugins}
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved plugin configuration")
        except Exception as e:
            logger.error(f"Failed to save plugin configuration: {e}")

    def list_available_plugins(self, plugin_type: str | None = None) -> list[str]:
        """List all available plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            List of plugin names
        """
        return self.loader.discover_plugins(plugin_type=plugin_type)

    def list_enabled_plugins(self, plugin_type: str | None = None) -> list[str]:
        """List enabled plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            List of enabled plugin names
        """
        if plugin_type:
            return [
                name for name in self._enabled_plugins.keys()
                if name.startswith(f"{plugin_type}.")
            ]
        return list(self._enabled_plugins.keys())

    def enable_plugin(self, plugin_name: str, config: dict | None = None) -> bool:
        """Enable a plugin.

        Args:
            plugin_name: Name of the plugin
            config: Optional plugin configuration

        Returns:
            True if successfully enabled, False otherwise
        """
        try:
            # Load the plugin to validate it works
            plugin = self.loader.load_plugin(plugin_name, config=config)
            metadata = plugin.get_metadata()

            # Add to enabled plugins
            self._enabled_plugins[plugin_name] = {
                "version": metadata.version,
                "config": config or {},
                "enabled_at": None,  # Would use datetime in production
            }
            self._save_config()

            # Log to audit
            self.audit_logger.log_plugin_loaded(plugin_name, metadata.version)

            logger.info(f"Enabled plugin {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_name}: {e}")
            return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if successfully disabled, False otherwise
        """
        if plugin_name in self._enabled_plugins:
            try:
                # Unload the plugin
                self.loader.unload_plugin(plugin_name)

                # Remove from enabled plugins
                del self._enabled_plugins[plugin_name]
                self._save_config()

                logger.info(f"Disabled plugin {plugin_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to disable plugin {plugin_name}: {e}")
                return False
        return False

    def get_plugin(self, plugin_name: str) -> Plugin | None:
        """Get a loaded plugin instance.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance if loaded, None otherwise
        """
        loaded = self.loader.get_loaded_plugins()
        return loaded.get(plugin_name)

    def configure_plugin(self, plugin_name: str, config: dict[str, Any]) -> bool:
        """Update plugin configuration.

        Args:
            plugin_name: Name of the plugin
            config: New configuration

        Returns:
            True if successfully configured, False otherwise
        """
        if plugin_name in self._enabled_plugins:
            self._enabled_plugins[plugin_name]["config"] = config
            self._save_config()

            # Reload plugin with new config
            try:
                self.loader.reload_plugin(plugin_name, config=config)
                logger.info(f"Reconfigured plugin {plugin_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to reconfigure plugin {plugin_name}: {e}")
                return False
        return False

    def get_plugins_by_type(self, plugin_type: str) -> dict[str, Plugin]:
        """Get all loaded plugins of a specific type.

        Args:
            plugin_type: Plugin type (embedder, retriever, processor, command)

        Returns:
            Dictionary of plugin name to plugin instance
        """
        return self.loader.get_loaded_plugins(plugin_type=plugin_type)
