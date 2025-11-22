"""Plugin loading and discovery system.

Discovers and loads plugins using Python entry points and validates them
before making them available to the system.
"""

from typing import Dict, List, Optional, Type
from pathlib import Path
import importlib
import logging
import sys

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # Python <3.8

from ragged.plugins.interfaces import Plugin, PLUGIN_TYPES
from ragged.plugins.validation import PluginValidator
from ragged.plugins.permissions import PermissionManager
from ragged.plugins.sandbox import PluginSandbox

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin fails to load."""

    pass


class PluginLoader:
    """Loads and manages plugins."""

    def __init__(
        self,
        validator: Optional[PluginValidator] = None,
        permission_manager: Optional[PermissionManager] = None,
    ):
        """Initialise plugin loader.

        Args:
            validator: Plugin validator (creates new if None)
            permission_manager: Permission manager (creates new if None)
        """
        self.validator = validator or PluginValidator()
        self.permission_manager = permission_manager or PermissionManager()
        self._loaded_plugins: Dict[str, Plugin] = {}

    def discover_plugins(self, plugin_type: Optional[str] = None) -> List[str]:
        """Discover available plugins via entry points.

        Args:
            plugin_type: Filter by plugin type (embedder, retriever, etc.)

        Returns:
            List of plugin names
        """
        discovered = []

        try:
            # Get entry points for ragged plugins
            eps = entry_points()
            if hasattr(eps, "select"):  # Python 3.10+
                plugin_eps = eps.select(group="ragged.plugins")
            else:  # Python 3.8-3.9
                plugin_eps = eps.get("ragged.plugins", [])

            for ep in plugin_eps:
                # Check if matches plugin type filter
                if plugin_type:
                    if not ep.name.startswith(f"{plugin_type}."):
                        continue
                discovered.append(ep.name)

            logger.info(f"Discovered {len(discovered)} plugins")

        except Exception as e:
            logger.error(f"Failed to discover plugins: {e}")

        return discovered

    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict] = None,
        validate: bool = True,
    ) -> Plugin:
        """Load a plugin by name.

        Args:
            plugin_name: Name of the plugin
            config: Optional configuration for the plugin
            validate: Whether to validate the plugin before loading

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin fails to load or validate
        """
        if plugin_name in self._loaded_plugins:
            logger.info(f"Plugin {plugin_name} already loaded")
            return self._loaded_plugins[plugin_name]

        try:
            # Find entry point
            eps = entry_points()
            if hasattr(eps, "select"):
                plugin_eps = eps.select(group="ragged.plugins", name=plugin_name)
                ep = next(iter(plugin_eps), None)
            else:
                plugin_eps = eps.get("ragged.plugins", [])
                ep = next((e for e in plugin_eps if e.name == plugin_name), None)

            if not ep:
                raise PluginLoadError(f"Plugin {plugin_name} not found")

            # Load the plugin class
            plugin_class = ep.load()

            # Validate it's a proper plugin
            if not issubclass(plugin_class, Plugin):
                raise PluginLoadError(f"Plugin {plugin_name} does not inherit from Plugin")

            # Get plugin type from name (e.g., "embedder.custom" -> "embedder")
            plugin_type = plugin_name.split(".")[0]
            if plugin_type not in PLUGIN_TYPES:
                raise PluginLoadError(f"Unknown plugin type: {plugin_type}")

            expected_base = PLUGIN_TYPES[plugin_type]
            if not issubclass(plugin_class, expected_base):
                raise PluginLoadError(
                    f"Plugin {plugin_name} should inherit from {expected_base.__name__}"
                )

            # Create instance
            plugin = plugin_class(config=config)

            # Validate if requested
            if validate:
                metadata = plugin.get_metadata()
                logger.info(f"Loaded plugin {metadata.name} v{metadata.version}")

            # Initialise the plugin
            plugin.initialize()

            # Store loaded plugin
            self._loaded_plugins[plugin_name] = plugin

            logger.info(f"Successfully loaded plugin {plugin_name}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise PluginLoadError(f"Failed to load plugin {plugin_name}: {e}")

    def unload_plugin(self, plugin_name: str) -> None:
        """Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload
        """
        if plugin_name in self._loaded_plugins:
            try:
                plugin = self._loaded_plugins[plugin_name]
                plugin.shutdown()
                del self._loaded_plugins[plugin_name]
                logger.info(f"Unloaded plugin {plugin_name}")
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {e}")

    def get_loaded_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, Plugin]:
        """Get currently loaded plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            Dictionary of plugin name to plugin instance
        """
        if plugin_type:
            return {
                name: plugin
                for name, plugin in self._loaded_plugins.items()
                if name.startswith(f"{plugin_type}.")
            }
        return self._loaded_plugins.copy()

    def reload_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Plugin:
        """Reload a plugin.

        Args:
            plugin_name: Name of the plugin
            config: Optional new configuration

        Returns:
            Reloaded plugin instance
        """
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name, config=config)
