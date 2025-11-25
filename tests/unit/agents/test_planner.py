"""Unit tests for agent planner."""

import pytest
from unittest.mock import MagicMock

from ragged.agents.planner import Plan, PlanStep, Planner
from ragged.agents.base import ExecutionContext, ToolCategory, ToolSpec
from ragged.auth.user import User


class TestPlanStep:
    """Tests for PlanStep dataclass."""

    def test_create_plan_step(self):
        """Test creating a plan step."""
        step = PlanStep(
            step_number=1,
            description="Search for documents",
            tool_name="search",
            arguments={"query": "test"},
        )
        assert step.step_number == 1
        assert step.description == "Search for documents"
        assert step.tool_name == "search"
        assert step.arguments == {"query": "test"}
        assert step.depends_on == []

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = PlanStep(
            step_number=2,
            description="Analyse results",
            tool_name="analyse",
            arguments={},
            depends_on=[1],
        )
        assert step.depends_on == [1]

    def test_to_dict(self):
        """Test converting step to dictionary."""
        step = PlanStep(
            step_number=1,
            description="Test",
            tool_name="test",
            arguments={"a": 1},
            depends_on=[],
            expected_output="result",
        )
        d = step.to_dict()
        assert d["step_number"] == 1
        assert d["description"] == "Test"
        assert d["tool_name"] == "test"
        assert d["arguments"] == {"a": 1}
        assert d["expected_output"] == "result"

    def test_step_defaults(self):
        """Test step default values."""
        step = PlanStep(
            step_number=1,
            description="Test",
            tool_name="test",
            arguments={},
        )
        assert step.depends_on == []
        assert step.expected_output == ""


class TestPlan:
    """Tests for Plan dataclass."""

    def test_create_plan(self):
        """Test creating a plan."""
        steps = [
            PlanStep(step_number=1, description="Step 1", tool_name="search", arguments={}),
            PlanStep(step_number=2, description="Step 2", tool_name="query", arguments={}, depends_on=[1]),
        ]
        plan = Plan(
            task="Find and summarise documents",
            steps=steps,
            reasoning="First search, then summarise",
        )
        assert plan.task == "Find and summarise documents"
        assert len(plan.steps) == 2
        assert plan.reasoning == "First search, then summarise"

    def test_empty_plan(self):
        """Test plan with no steps."""
        plan = Plan(task="Simple task", steps=[])
        assert len(plan.steps) == 0

    def test_to_dict(self):
        """Test converting plan to dictionary."""
        plan = Plan(
            task="Test task",
            steps=[PlanStep(step_number=1, description="S1", tool_name="t1", arguments={})],
            reasoning="Testing",
        )
        d = plan.to_dict()
        assert d["task"] == "Test task"
        assert len(d["steps"]) == 1
        assert d["reasoning"] == "Testing"


class TestPlanner:
    """Tests for Planner class."""

    @pytest.fixture
    def planner(self):
        """Create a planner instance."""
        return Planner()

    @pytest.fixture
    def mock_context(self):
        """Create a mock execution context."""
        user = User(user_id="test", display_name="Test")
        return ExecutionContext(
            user=user,
            session_id="session-1",
            task_id="task-1",
        )

    @pytest.fixture
    def sample_tools(self):
        """Create sample tool specs."""
        return [
            ToolSpec(
                name="search",
                description="Search documents",
                category=ToolCategory.RAG,
                parameters={},
            ),
            ToolSpec(
                name="query",
                description="Query with RAG",
                category=ToolCategory.RAG,
                parameters={},
            ),
            ToolSpec(
                name="ingest",
                description="Ingest documents",
                category=ToolCategory.RAG,
                parameters={},
            ),
        ]

    @pytest.mark.asyncio
    async def test_create_plan_search_task(self, planner, mock_context, sample_tools):
        """Test creating plan for a search task."""
        plan = await planner.create_plan(
            task="Find documents about authentication",
            tools=sample_tools,
            context=mock_context,
        )
        assert plan.task == "Find documents about authentication"
        assert len(plan.steps) > 0
        assert plan.steps[0].tool_name == "search"

    @pytest.mark.asyncio
    async def test_create_plan_ingest_task(self, planner, mock_context, sample_tools):
        """Test creating plan for an ingest task."""
        plan = await planner.create_plan(
            task="Add document readme.md to the system",
            tools=sample_tools,
            context=mock_context,
        )
        assert len(plan.steps) > 0
        assert plan.steps[0].tool_name == "ingest"

    @pytest.mark.asyncio
    async def test_create_plan_query_task(self, planner, mock_context, sample_tools):
        """Test creating plan for a query task."""
        plan = await planner.create_plan(
            task="What is the purpose of this codebase?",
            tools=sample_tools,
            context=mock_context,
        )
        assert len(plan.steps) > 0
        assert plan.steps[0].tool_name == "query"

    @pytest.mark.asyncio
    async def test_create_plan_no_matching_tools(self, planner, mock_context):
        """Test creating plan with no matching tools."""
        tools = [
            ToolSpec(
                name="unrelated",
                description="Unrelated tool",
                category=ToolCategory.EXTERNAL,
                parameters={},
            ),
        ]
        plan = await planner.create_plan(
            task="Search for documents",
            tools=tools,
            context=mock_context,
        )
        # Should return empty plan when no tools match
        assert len(plan.steps) == 0

    @pytest.mark.asyncio
    async def test_refine_plan_after_success(self, planner, mock_context, sample_tools):
        """Test refining plan after successful steps."""
        original_plan = Plan(
            task="Multi-step task",
            steps=[
                PlanStep(step_number=1, description="Step 1", tool_name="search", arguments={}),
                PlanStep(step_number=2, description="Step 2", tool_name="query", arguments={}),
            ],
        )
        step_results = [{"step_number": 1, "success": True}]

        refined = await planner.refine_plan(
            plan=original_plan,
            step_results=step_results,
            tools=sample_tools,
            context=mock_context,
        )
        # Should have remaining steps
        assert refined.metadata.get("refined") is True

    def test_generate_reasoning(self, planner):
        """Test reasoning generation."""
        steps = [
            PlanStep(step_number=1, description="Search", tool_name="search", arguments={}),
        ]
        tools = [
            ToolSpec(name="search", description="Search", category=ToolCategory.RAG, parameters={}),
        ]
        reasoning = planner._generate_reasoning("Find documents", steps, tools)
        assert "search" in reasoning.lower()
        assert "1 step" in reasoning
