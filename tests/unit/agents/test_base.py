"""Unit tests for agent base classes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ragged.agents.base import (
    AgentState,
    AgentConfig,
    AgentResult,
    ExecutionContext,
    StepResult,
    Tool,
    ToolCall,
    ToolCategory,
    ToolExecutionError,
    ToolResult,
    ToolSpec,
)
from ragged.auth.user import User


class TestAgentState:
    """Tests for AgentState enum."""

    def test_all_states_exist(self):
        """Verify all expected states are defined."""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.PLANNING.value == "planning"
        assert AgentState.EXECUTING.value == "executing"
        assert AgentState.WAITING.value == "waiting"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"
        assert AgentState.CANCELLED.value == "cancelled"


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_all_categories_exist(self):
        """Verify all expected categories are defined."""
        assert ToolCategory.RAG.value == "rag"
        assert ToolCategory.STORAGE.value == "storage"
        assert ToolCategory.ANALYSIS.value == "analysis"
        assert ToolCategory.EXTERNAL.value == "external"
        assert ToolCategory.SYSTEM.value == "system"


class TestToolSpec:
    """Tests for ToolSpec dataclass."""

    def test_create_basic_spec(self):
        """Test creating a basic tool spec."""
        spec = ToolSpec(
            name="test_tool",
            description="A test tool",
            category=ToolCategory.RAG,
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        )
        assert spec.name == "test_tool"
        assert spec.description == "A test tool"
        assert spec.category == ToolCategory.RAG
        assert spec.requires_confirmation is False

    def test_spec_with_confirmation(self):
        """Test spec with confirmation required."""
        spec = ToolSpec(
            name="dangerous_tool",
            description="A dangerous tool",
            category=ToolCategory.SYSTEM,
            parameters={},
            requires_confirmation=True,
        )
        assert spec.requires_confirmation is True

    def test_to_dict(self):
        """Test converting spec to dictionary."""
        spec = ToolSpec(
            name="test",
            description="Test",
            category=ToolCategory.RAG,
            parameters={"type": "object"},
        )
        result = spec.to_dict()
        assert result["name"] == "test"
        assert result["description"] == "Test"
        assert result["parameters"] == {"type": "object"}


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCall(
            tool_name="search",
            arguments={"query": "test"},
        )
        assert call.tool_name == "search"
        assert call.arguments == {"query": "test"}
        assert call.call_id is not None
        assert len(call.call_id) == 8

    def test_tool_call_custom_id(self):
        """Test tool call with custom ID."""
        call = ToolCall(
            tool_name="search",
            arguments={},
            call_id="custom123",
        )
        assert call.call_id == "custom123"


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = ToolResult(
            call_id="abc123",
            success=True,
            result={"data": "test"},
            duration_ms=100.5,
        )
        assert result.success is True
        assert result.result == {"data": "test"}
        assert result.error is None
        assert result.duration_ms == 100.5

    def test_failed_result(self):
        """Test creating a failed result."""
        result = ToolResult(
            call_id="abc123",
            success=False,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = ToolResult(
            call_id="abc",
            success=True,
            result="test",
            duration_ms=50,
        )
        d = result.to_dict()
        assert d["call_id"] == "abc"
        assert d["success"] is True
        assert d["result"] == "test"
        assert d["duration_ms"] == 50


class TestToolExecutionError:
    """Tests for ToolExecutionError exception."""

    def test_create_error(self):
        """Test creating a tool execution error."""
        error = ToolExecutionError("search", "Query failed")
        assert error.tool_name == "search"
        assert error.message == "Query failed"
        assert str(error) == "Tool 'search' failed: Query failed"

    def test_error_with_cause(self):
        """Test error with underlying cause."""
        cause = ValueError("Invalid input")
        error = ToolExecutionError("ingest", "Failed to process", cause=cause)
        assert error.cause is cause


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        return User(user_id="test-user", display_name="Test User")

    def test_create_context(self, mock_user):
        """Test creating execution context."""
        context = ExecutionContext(
            user=mock_user,
            session_id="session-123",
            task_id="task-456",
        )
        assert context.user.user_id == "test-user"
        assert context.session_id == "session-123"
        assert context.task_id == "task-456"
        assert context.variables == {}
        assert context.history == []

    def test_set_and_get_variable(self, mock_user):
        """Test variable management."""
        context = ExecutionContext(
            user=mock_user,
            session_id="s1",
            task_id="t1",
        )
        context.set_variable("key", "value")
        assert context.get_variable("key") == "value"
        assert context.get_variable("missing", "default") == "default"

    def test_add_to_history(self, mock_user):
        """Test adding to history."""
        context = ExecutionContext(
            user=mock_user,
            session_id="s1",
            task_id="t1",
        )
        step = StepResult(
            step_number=1,
            tool_call=None,
            tool_result=None,
        )
        context.add_to_history(step)
        assert len(context.history) == 1
        assert context.history[0].step_number == 1


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_create_step_result(self):
        """Test creating a step result."""
        tool_call = ToolCall(tool_name="search", arguments={"q": "test"})
        tool_result = ToolResult(call_id=tool_call.call_id, success=True, result="data")

        step = StepResult(
            step_number=1,
            tool_call=tool_call,
            tool_result=tool_result,
            reasoning="Searching for documents",
        )
        assert step.step_number == 1
        assert step.tool_call.tool_name == "search"
        assert step.tool_result.success is True
        assert step.reasoning == "Searching for documents"

    def test_to_dict(self):
        """Test converting step result to dictionary."""
        step = StepResult(
            step_number=2,
            tool_call=ToolCall(tool_name="query", arguments={}),
            tool_result=ToolResult(call_id="x", success=True),
            reasoning="Querying",
        )
        d = step.to_dict()
        assert d["step_number"] == 2
        assert d["tool_call"]["tool_name"] == "query"
        assert d["tool_result"]["success"] is True
        assert d["reasoning"] == "Querying"


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AgentConfig()
        assert config.max_steps == 10
        assert config.timeout_seconds == 300
        assert config.require_confirmation is False
        assert ToolCategory.RAG in config.allowed_categories
        assert config.temperature == 0.0
        assert config.verbose is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = AgentConfig(
            max_steps=5,
            timeout_seconds=60,
            require_confirmation=True,
            allowed_categories=[ToolCategory.RAG],
            temperature=0.7,
            verbose=True,
        )
        assert config.max_steps == 5
        assert config.timeout_seconds == 60
        assert config.require_confirmation is True
        assert len(config.allowed_categories) == 1


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful agent result."""
        result = AgentResult(
            task_id="task-123",
            state=AgentState.COMPLETED,
            output={"answer": "42"},
            steps=[],
            total_duration_ms=1000.0,
        )
        assert result.task_id == "task-123"
        assert result.state == AgentState.COMPLETED
        assert result.output == {"answer": "42"}
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed agent result."""
        result = AgentResult(
            task_id="task-456",
            state=AgentState.FAILED,
            output=None,
            steps=[],
            total_duration_ms=500.0,
            error="Task failed",
        )
        assert result.state == AgentState.FAILED
        assert result.error == "Task failed"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = AgentResult(
            task_id="t1",
            state=AgentState.COMPLETED,
            output="result",
            steps=[],
            total_duration_ms=100,
        )
        d = result.to_dict()
        assert d["task_id"] == "t1"
        assert d["state"] == "completed"
        assert d["output"] == "result"
        assert d["steps"] == []
