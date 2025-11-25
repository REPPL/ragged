"""Unit tests for tool registry."""

import pytest
from unittest.mock import MagicMock, patch

from ragged.agents.registry import ToolRegistry
from ragged.agents.base import Tool, ToolCategory, ToolSpec, ExecutionContext


class MockTool(Tool):
    """A mock tool for testing."""

    def __init__(self, name: str = "mock_tool", category: ToolCategory = ToolCategory.RAG):
        self._name = name
        self._category = category

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self._name,
            description=f"Mock tool: {self._name}",
            category=self._category,
            parameters={"type": "object"},
        )

    async def execute(self, context: ExecutionContext, **kwargs):
        return {"mock": True, "args": kwargs}


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_create_empty_registry(self):
        """Test creating an empty registry."""
        registry = ToolRegistry()
        assert len(registry) == 0
        assert list(registry.list_tools()) == []

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool("search")

        registry.register(tool)

        assert len(registry) == 1
        assert "search" in registry
        assert registry.get_tool("search") is tool

    def test_register_duplicate_fails(self):
        """Test that registering duplicate tool raises error."""
        registry = ToolRegistry()
        tool1 = MockTool("search")
        tool2 = MockTool("search")

        registry.register(tool1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2)

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool("search")
        registry.register(tool)

        result = registry.unregister("search")

        assert result is True
        assert len(registry) == 0
        assert "search" not in registry

    def test_unregister_nonexistent(self):
        """Test unregistering a tool that doesn't exist."""
        registry = ToolRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_tool_not_found(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register(MockTool("tool1"))
        registry.register(MockTool("tool2"))
        registry.register(MockTool("tool3"))

        tools = registry.list_tools()
        assert len(tools) == 3
        names = [t.spec.name for t in tools]
        assert "tool1" in names
        assert "tool2" in names
        assert "tool3" in names

    def test_list_tools_by_category(self):
        """Test listing tools filtered by category."""
        registry = ToolRegistry()
        registry.register(MockTool("rag1", ToolCategory.RAG))
        registry.register(MockTool("rag2", ToolCategory.RAG))
        registry.register(MockTool("storage1", ToolCategory.STORAGE))

        rag_tools = registry.list_tools(category=ToolCategory.RAG)
        assert len(rag_tools) == 2

        storage_tools = registry.list_tools(category=ToolCategory.STORAGE)
        assert len(storage_tools) == 1

    def test_list_specs(self):
        """Test listing tool specifications."""
        registry = ToolRegistry()
        registry.register(MockTool("tool1"))
        registry.register(MockTool("tool2"))

        specs = registry.list_specs()
        assert len(specs) == 2
        assert all(isinstance(s, ToolSpec) for s in specs)

    def test_iter_registry(self):
        """Test iterating over registry."""
        registry = ToolRegistry()
        registry.register(MockTool("tool1"))
        registry.register(MockTool("tool2"))

        tools = list(registry)
        assert len(tools) == 2

    def test_contains(self):
        """Test checking if tool is in registry."""
        registry = ToolRegistry()
        registry.register(MockTool("search"))

        assert "search" in registry
        assert "query" not in registry

    def test_clear(self):
        """Test clearing all tools."""
        registry = ToolRegistry()
        registry.register(MockTool("tool1"))
        registry.register(MockTool("tool2"))
        registry.register(MockTool("tool3"))

        registry.clear()

        assert len(registry) == 0

    def test_to_dict(self):
        """Test converting registry to dictionary."""
        registry = ToolRegistry()
        registry.register(MockTool("search"))
        registry.register(MockTool("query"))

        d = registry.to_dict()
        assert "search" in d
        assert "query" in d
        assert d["search"]["name"] == "search"

    def test_register_defaults(self):
        """Test registering default tools."""
        registry = ToolRegistry()

        # This might fail if dependencies aren't available,
        # so we catch ImportError
        try:
            registry.register_defaults()
            # If it succeeds, we should have some tools
            assert len(registry) > 0
        except ImportError:
            # Expected if RAG dependencies not installed
            pass

    def test_thread_safety(self):
        """Test registry operations are thread-safe."""
        import threading

        registry = ToolRegistry()
        errors = []

        def register_tools():
            try:
                for i in range(10):
                    registry.register(MockTool(f"tool_{threading.current_thread().name}_{i}"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_tools, name=f"t{i}") for i in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0
        # Should have registered 30 tools (3 threads * 10 tools)
        assert len(registry) == 30
