"""Unit tests for agent chaining module."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from ragged.agents.chaining import (
    ChainStatus,
    ChainStep,
    ChainResult,
    ToolChain,
    ChainExecutor,
    ChainBuilder,
    CommonChains,
    chain,
)


class TestChainStep:
    """Tests for ChainStep dataclass."""

    def test_create_step(self):
        """Test creating a chain step."""
        step = ChainStep(
            name="search",
            tool_name="search_tool",
            arguments={"query": "test"},
        )
        assert step.name == "search"
        assert step.tool_name == "search_tool"
        assert step.arguments == {"query": "test"}

    def test_step_defaults(self):
        """Test default values."""
        step = ChainStep(name="test", tool_name="test_tool")
        assert step.arguments == {}
        assert step.transform is None
        assert step.condition is None
        assert step.on_error == "fail"
        assert step.max_retries == 3
        assert step.timeout is None

    def test_should_execute_no_condition(self):
        """Test should_execute with no condition."""
        step = ChainStep(name="test", tool_name="test_tool")
        assert step.should_execute({}) is True

    def test_should_execute_with_condition(self):
        """Test should_execute with condition."""
        step = ChainStep(
            name="test",
            tool_name="test_tool",
            condition=lambda ctx: ctx.get("enabled", False),
        )
        assert step.should_execute({}) is False
        assert step.should_execute({"enabled": True}) is True

    def test_resolve_arguments_no_placeholders(self):
        """Test resolving arguments without placeholders."""
        step = ChainStep(
            name="test",
            tool_name="test_tool",
            arguments={"query": "literal", "limit": 10},
        )
        resolved = step.resolve_arguments({})
        assert resolved == {"query": "literal", "limit": 10}

    def test_resolve_arguments_with_placeholders(self):
        """Test resolving arguments with placeholders."""
        step = ChainStep(
            name="query",
            tool_name="query_tool",
            arguments={"context": "${search.output}"},
        )
        context = {"search": {"output": "search results"}}
        resolved = step.resolve_arguments(context)
        assert resolved["context"] == "search results"

    def test_resolve_arguments_nested_path(self):
        """Test resolving nested placeholder paths."""
        step = ChainStep(
            name="test",
            tool_name="test_tool",
            arguments={"data": "${prev.result.items}"},
        )
        context = {"prev": {"result": {"items": [1, 2, 3]}}}
        resolved = step.resolve_arguments(context)
        assert resolved["data"] == [1, 2, 3]

    def test_resolve_arguments_missing_placeholder(self):
        """Test resolving with missing placeholder."""
        step = ChainStep(
            name="test",
            tool_name="test_tool",
            arguments={"data": "${missing.value}"},
        )
        resolved = step.resolve_arguments({})
        # Should keep original placeholder if not found
        assert resolved["data"] == "${missing.value}"


class TestChainResult:
    """Tests for ChainResult dataclass."""

    def test_create_result(self):
        """Test creating a chain result."""
        result = ChainResult(
            step_name="search",
            status=ChainStatus.COMPLETED,
            output={"items": [1, 2, 3]},
            duration=1.5,
        )
        assert result.step_name == "search"
        assert result.status == ChainStatus.COMPLETED
        assert result.output == {"items": [1, 2, 3]}
        assert result.duration == 1.5

    def test_result_with_error(self):
        """Test result with error."""
        result = ChainResult(
            step_name="failed",
            status=ChainStatus.FAILED,
            error="Connection timeout",
            retries=3,
        )
        assert result.status == ChainStatus.FAILED
        assert result.error == "Connection timeout"
        assert result.retries == 3

    def test_to_dict(self):
        """Test serialisation to dictionary."""
        result = ChainResult(
            step_name="test",
            status=ChainStatus.COMPLETED,
            output="result",
        )
        d = result.to_dict()
        assert d["step_name"] == "test"
        assert d["status"] == "completed"
        assert d["output"] == "result"


class TestToolChain:
    """Tests for ToolChain dataclass."""

    def test_create_chain(self):
        """Test creating a tool chain."""
        chain = ToolChain(name="test_chain", description="A test chain")
        assert chain.name == "test_chain"
        assert chain.description == "A test chain"
        assert chain.steps == []

    def test_add_step(self):
        """Test adding steps fluently."""
        tc = ToolChain(name="fluent")
        result = tc.add_step("search", "search_tool", {"query": "test"})

        assert result is tc  # Fluent interface
        assert len(tc.steps) == 1
        assert tc.steps[0].name == "search"

    def test_add_multiple_steps(self):
        """Test adding multiple steps."""
        tc = ToolChain(name="multi")
        tc.add_step("step1", "tool1").add_step("step2", "tool2").add_step("step3", "tool3")

        assert len(tc.steps) == 3

    def test_to_dict(self):
        """Test serialisation to dictionary."""
        tc = ToolChain(name="serialise", description="Test")
        tc.add_step("s1", "t1", {"arg": "value"})

        d = tc.to_dict()
        assert d["name"] == "serialise"
        assert d["description"] == "Test"
        assert len(d["steps"]) == 1


class TestChainBuilder:
    """Tests for ChainBuilder."""

    def test_basic_chain(self):
        """Test building a basic chain."""
        built = ChainBuilder("basic").step("s1", "t1").step("s2", "t2").build()

        assert built.name == "basic"
        assert len(built.steps) == 2

    def test_step_with_transform(self):
        """Test adding transform to step."""
        transform_fn = lambda x: x.upper()
        built = ChainBuilder("transform").step("s1", "t1").transform(transform_fn).build()

        assert built.steps[0].transform is transform_fn

    def test_step_with_condition(self):
        """Test adding condition to step."""
        condition_fn = lambda ctx: ctx.get("ready", False)
        built = ChainBuilder("conditional").step("s1", "t1").when(condition_fn).build()

        assert built.steps[0].condition is condition_fn

    def test_step_with_error_handling(self):
        """Test setting error handling."""
        built = ChainBuilder("error").step("s1", "t1").on_error("skip").build()

        assert built.steps[0].on_error == "skip"

    def test_step_with_timeout(self):
        """Test setting timeout."""
        built = ChainBuilder("timeout").step("s1", "t1").with_timeout(30.0).build()

        assert built.steps[0].timeout == 30.0

    def test_step_with_retries(self):
        """Test setting max retries."""
        built = ChainBuilder("retries").step("s1", "t1").with_retries(5).build()

        assert built.steps[0].max_retries == 5

    def test_chain_metadata(self):
        """Test adding metadata."""
        built = ChainBuilder("meta").metadata(version="1.0", author="test").build()

        assert built.metadata["version"] == "1.0"
        assert built.metadata["author"] == "test"

    def test_chain_helper_function(self):
        """Test the chain() helper function."""
        built = chain("helper_test", "Description").step("s1", "t1").build()

        assert built.name == "helper_test"
        assert built.description == "Description"


class TestChainExecutor:
    """Tests for ChainExecutor."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock tool registry."""
        registry = MagicMock()
        return registry

    @pytest.fixture
    def executor(self, mock_registry):
        """Create a chain executor."""
        return ChainExecutor(tool_registry=mock_registry)

    @pytest.mark.asyncio
    async def test_execute_empty_chain(self, executor):
        """Test executing an empty chain."""
        empty_chain = ToolChain(name="empty")
        results = await executor.execute(empty_chain)
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_single_step(self, executor, mock_registry):
        """Test executing a single step chain."""
        # Setup mock tool
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="result")
        mock_registry.get.return_value = mock_tool

        single_chain = chain("single").step("s1", "search").build()
        results = await executor.execute(single_chain)

        assert len(results) == 1
        assert results[0].status == ChainStatus.COMPLETED
        assert results[0].output == "result"

    @pytest.mark.asyncio
    async def test_execute_with_context_flow(self, executor, mock_registry):
        """Test that context flows between steps."""
        # Setup mock tools
        search_tool = MagicMock()
        search_tool.execute = AsyncMock(return_value="search results")

        query_tool = MagicMock()
        query_tool.execute = AsyncMock(return_value="query answer")

        def get_tool(name):
            if name == "search":
                return search_tool
            return query_tool

        mock_registry.get.side_effect = get_tool

        flow_chain = (
            chain("flow")
            .step("search", "search", {"query": "test"})
            .step("query", "query", {"context": "${search}"})
            .build()
        )

        results = await executor.execute(flow_chain)

        assert len(results) == 2
        assert executor.context["search"] == "search results"

    @pytest.mark.asyncio
    async def test_execute_with_condition_skip(self, executor, mock_registry):
        """Test that steps are skipped when condition is false."""
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="result")
        mock_registry.get.return_value = mock_tool

        conditional_chain = (
            chain("conditional")
            .step("s1", "t1")
            .when(lambda ctx: False)  # Always skip
            .build()
        )

        results = await executor.execute(conditional_chain)

        assert len(results) == 1
        assert results[0].status == ChainStatus.COMPLETED
        assert results[0].output is None  # Skipped

    @pytest.mark.asyncio
    async def test_execute_with_transform(self, executor, mock_registry):
        """Test that transforms are applied to output."""
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="hello")
        mock_registry.get.return_value = mock_tool

        transform_chain = (
            chain("transform")
            .step("s1", "t1")
            .transform(lambda x: x.upper())
            .build()
        )

        results = await executor.execute(transform_chain)

        assert results[0].output == "HELLO"

    @pytest.mark.asyncio
    async def test_execute_failure_stops_chain(self, executor, mock_registry):
        """Test that failure stops chain execution."""
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=ValueError("Test error"))
        mock_registry.get.return_value = mock_tool

        failing_chain = (
            chain("failing")
            .step("s1", "t1")
            .with_retries(0)  # No retries
            .step("s2", "t2")  # Should not execute
            .build()
        )

        results = await executor.execute(failing_chain)

        assert len(results) == 1
        assert results[0].status == ChainStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_skip_on_error(self, executor, mock_registry):
        """Test skip error handling strategy."""
        failing_tool = MagicMock()
        failing_tool.execute = AsyncMock(side_effect=ValueError("Error"))

        success_tool = MagicMock()
        success_tool.execute = AsyncMock(return_value="success")

        mock_registry.get.side_effect = [failing_tool, success_tool]

        skip_chain = (
            chain("skip")
            .step("s1", "t1")
            .on_error("skip")
            .with_retries(0)
            .step("s2", "t2")
            .build()
        )

        results = await executor.execute(skip_chain)

        assert len(results) == 2
        assert results[0].status == ChainStatus.COMPLETED  # Skipped, not failed
        assert results[1].status == ChainStatus.COMPLETED

    def test_cancel(self, executor):
        """Test cancelling execution."""
        executor.cancel()
        # Internal state check
        assert executor._cancelled is True


class TestCommonChains:
    """Tests for pre-built common chains."""

    def test_search_and_query(self):
        """Test search_and_query chain factory."""
        c = CommonChains.search_and_query("test query")
        assert c.name == "search_and_query"
        assert len(c.steps) == 2
        assert c.steps[0].tool_name == "search"
        assert c.steps[1].tool_name == "query"

    def test_ingest_and_index(self):
        """Test ingest_and_index chain factory."""
        c = CommonChains.ingest_and_index("/path/to/docs")
        assert c.name == "ingest_and_index"
        assert len(c.steps) == 2
        assert c.steps[0].on_error == "fail"
        assert c.steps[1].on_error == "skip"

    def test_validate_and_process(self):
        """Test validate_and_process chain factory."""
        c = CommonChains.validate_and_process({"data": "test"})
        assert c.name == "validate_and_process"
        assert len(c.steps) == 2
        # Validate step has the condition (added via fluent .when() after .step())
        assert c.steps[0].condition is not None
