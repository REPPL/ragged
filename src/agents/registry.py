"""Tool registry for agent framework.

Phase 2 Infrastructure: Manages available tools for agents.

Design Principles:
- Central registry for all tools
- Category-based filtering
- Thread-safe tool access
"""

import logging
import threading
from typing import Iterator

from ragged.agents.base import Tool, ToolCategory, ToolSpec

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for agent tools.

    Provides thread-safe management of tools available to agents:
    - Registration and deregistration
    - Lookup by name or category
    - Default tool set loading

    Thread Safety:
        All public methods are thread-safe.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(search_tool)
        >>> registry.register(ingest_tool)
        >>>
        >>> # List all tools
        >>> for tool in registry.list_tools():
        ...     print(tool.spec.name)
        >>>
        >>> # Get specific tool
        >>> search = registry.get_tool("search")
        >>> result = await search.execute(context, query="auth")
    """

    def __init__(self):
        """Initialise empty registry."""
        self._tools: dict[str, Tool] = {}
        self._lock = threading.RLock()

        logger.debug("ToolRegistry initialised")

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool to register

        Raises:
            ValueError: If tool with same name already exists
        """
        with self._lock:
            name = tool.spec.name

            if name in self._tools:
                raise ValueError(f"Tool already registered: {name}")

            self._tools[name] = tool
            logger.debug(f"Registered tool: {name} ({tool.spec.category.value})")

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name.

        Args:
            name: Tool name to remove

        Returns:
            True if tool was removed, False if not found
        """
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                logger.debug(f"Unregistered tool: {name}")
                return True
            return False

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        with self._lock:
            return self._tools.get(name)

    def list_tools(self, category: ToolCategory | None = None) -> list[Tool]:
        """List all registered tools.

        Args:
            category: Filter by category (None for all)

        Returns:
            List of registered tools
        """
        with self._lock:
            if category is None:
                return list(self._tools.values())

            return [
                tool for tool in self._tools.values()
                if tool.spec.category == category
            ]

    def list_specs(self, category: ToolCategory | None = None) -> list[ToolSpec]:
        """List tool specifications.

        Args:
            category: Filter by category (None for all)

        Returns:
            List of tool specifications
        """
        return [tool.spec for tool in self.list_tools(category)]

    def __len__(self) -> int:
        """Get number of registered tools."""
        with self._lock:
            return len(self._tools)

    def __iter__(self) -> Iterator[Tool]:
        """Iterate over registered tools."""
        with self._lock:
            return iter(list(self._tools.values()))

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered."""
        with self._lock:
            return name in self._tools

    def register_defaults(self) -> None:
        """Register default RAG tools.

        Loads the standard tool set for RAG operations:
        - search: Vector search over documents
        - ingest: Document ingestion
        - query: RAG query with generation

        Note:
            Tools are loaded lazily to avoid import cycles.
        """
        logger.info("Registering default tools...")

        try:
            from ragged.agents.tools import (
                VectorSearchTool,
                IngestTool,
                QueryTool,
            )

            # Register RAG tools
            self.register(VectorSearchTool())
            self.register(IngestTool())
            self.register(QueryTool())

            logger.info(f"Registered {len(self)} default tools")

        except ImportError as e:
            logger.warning(f"Could not load default tools: {e}")

    def clear(self) -> None:
        """Remove all registered tools."""
        with self._lock:
            count = len(self._tools)
            self._tools.clear()
            logger.debug(f"Cleared {count} tools from registry")

    def to_dict(self) -> dict[str, dict]:
        """Convert registry to dictionary.

        Returns:
            Dictionary mapping tool names to their specs
        """
        with self._lock:
            return {
                name: tool.spec.to_dict()
                for name, tool in self._tools.items()
            }
