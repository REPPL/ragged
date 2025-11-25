"""Unit tests for workflow system."""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import AsyncMock, MagicMock, patch

from ragged.agents.workflows.definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTrigger,
    load_workflow,
    validate_workflow,
    WORKFLOW_TEMPLATES,
    _has_circular_dependency,
)
from ragged.agents.workflows.executor import (
    WorkflowExecutor,
    WorkflowResult,
    WorkflowState,
    StepExecutionResult,
)
from ragged.agents.registry import ToolRegistry
from ragged.agents.base import Tool, ToolCategory, ToolSpec, ExecutionContext
from ragged.auth.user import User


class TestWorkflowStep:
    """Tests for WorkflowStep dataclass."""

    def test_create_step(self):
        """Test creating a workflow step."""
        step = WorkflowStep(
            id="step1",
            name="Search Documents",
            tool="search",
            arguments={"query": "test"},
        )
        assert step.id == "step1"
        assert step.name == "Search Documents"
        assert step.tool == "search"
        assert step.arguments == {"query": "test"}
        assert step.depends_on == []
        assert step.on_failure == "stop"

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = WorkflowStep(
            id="step2",
            name="Process",
            tool="process",
            arguments={},
            depends_on=["step1"],
        )
        assert step.depends_on == ["step1"]

    def test_to_dict(self):
        """Test converting step to dictionary."""
        step = WorkflowStep(
            id="s1",
            name="Test",
            tool="test",
            arguments={"a": 1},
            retries=3,
        )
        d = step.to_dict()
        assert d["id"] == "s1"
        assert d["name"] == "Test"
        assert d["tool"] == "test"
        assert d["retries"] == 3

    def test_from_dict(self):
        """Test creating step from dictionary."""
        data = {
            "id": "step1",
            "name": "Search",
            "tool": "search",
            "arguments": {"q": "test"},
            "on_failure": "continue",
        }
        step = WorkflowStep.from_dict(data)
        assert step.id == "step1"
        assert step.tool == "search"
        assert step.on_failure == "continue"


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition dataclass."""

    def test_create_workflow(self):
        """Test creating a workflow definition."""
        workflow = WorkflowDefinition(
            id="test_workflow",
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", tool="tool1", arguments={}),
            ],
        )
        assert workflow.id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1
        assert workflow.trigger == WorkflowTrigger.MANUAL

    def test_to_dict(self):
        """Test converting workflow to dictionary."""
        workflow = WorkflowDefinition(
            id="w1",
            name="Workflow",
            steps=[],
        )
        d = workflow.to_dict()
        assert d["id"] == "w1"
        assert d["name"] == "Workflow"
        assert d["trigger"] == "manual"

    def test_to_json(self):
        """Test converting workflow to JSON."""
        workflow = WorkflowDefinition(
            id="w1",
            name="Workflow",
            steps=[],
        )
        json_str = workflow.to_json()
        data = json.loads(json_str)
        assert data["id"] == "w1"

    def test_from_dict(self):
        """Test creating workflow from dictionary."""
        data = {
            "id": "w1",
            "name": "Workflow",
            "description": "Test",
            "trigger": "api",
            "steps": [
                {"id": "s1", "name": "Step", "tool": "test", "arguments": {}},
            ],
        }
        workflow = WorkflowDefinition.from_dict(data)
        assert workflow.id == "w1"
        assert workflow.trigger == WorkflowTrigger.API
        assert len(workflow.steps) == 1

    def test_from_json(self):
        """Test creating workflow from JSON."""
        json_str = '{"id": "w1", "name": "Test", "steps": []}'
        workflow = WorkflowDefinition.from_json(json_str)
        assert workflow.id == "w1"


class TestLoadWorkflow:
    """Tests for load_workflow function."""

    def test_load_valid_workflow(self, tmp_path):
        """Test loading a valid workflow file."""
        workflow_data = {
            "id": "test",
            "name": "Test Workflow",
            "steps": [
                {"id": "s1", "name": "Step", "tool": "search", "arguments": {}},
            ],
        }
        file_path = tmp_path / "workflow.json"
        file_path.write_text(json.dumps(workflow_data))

        workflow = load_workflow(file_path)
        assert workflow.id == "test"
        assert len(workflow.steps) == 1

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_workflow(Path("/nonexistent/workflow.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_workflow(file_path)


class TestValidateWorkflow:
    """Tests for validate_workflow function."""

    def test_valid_workflow(self):
        """Test validating a valid workflow."""
        workflow = WorkflowDefinition(
            id="valid",
            name="Valid Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", tool="search", arguments={}),
            ],
        )
        errors = validate_workflow(workflow)
        assert len(errors) == 0

    def test_missing_id(self):
        """Test validation with missing ID."""
        workflow = WorkflowDefinition(
            id="",
            name="Test",
            steps=[WorkflowStep(id="s1", name="S", tool="t", arguments={})],
        )
        errors = validate_workflow(workflow)
        assert any("ID" in e for e in errors)

    def test_missing_name(self):
        """Test validation with missing name."""
        workflow = WorkflowDefinition(
            id="w1",
            name="",
            steps=[WorkflowStep(id="s1", name="S", tool="t", arguments={})],
        )
        errors = validate_workflow(workflow)
        assert any("name" in e for e in errors)

    def test_no_steps(self):
        """Test validation with no steps."""
        workflow = WorkflowDefinition(
            id="w1",
            name="Workflow",
            steps=[],
        )
        errors = validate_workflow(workflow)
        assert any("at least one step" in e for e in errors)

    def test_duplicate_step_ids(self):
        """Test validation with duplicate step IDs."""
        workflow = WorkflowDefinition(
            id="w1",
            name="Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", tool="t1", arguments={}),
                WorkflowStep(id="s1", name="Step 2", tool="t2", arguments={}),
            ],
        )
        errors = validate_workflow(workflow)
        assert any("unique" in e for e in errors)

    def test_invalid_dependency(self):
        """Test validation with invalid dependency."""
        workflow = WorkflowDefinition(
            id="w1",
            name="Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step", tool="t", arguments={}, depends_on=["nonexistent"]),
            ],
        )
        errors = validate_workflow(workflow)
        assert any("unknown step" in e for e in errors)

    def test_unknown_tool(self):
        """Test validation with unknown tool."""
        workflow = WorkflowDefinition(
            id="w1",
            name="Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step", tool="unknown", arguments={}),
            ],
        )
        errors = validate_workflow(workflow, available_tools=["search", "query"])
        assert any("unknown tool" in e for e in errors)


class TestCircularDependency:
    """Tests for circular dependency detection."""

    def test_no_cycle(self):
        """Test steps without cycle."""
        steps = [
            WorkflowStep(id="s1", name="S1", tool="t", arguments={}),
            WorkflowStep(id="s2", name="S2", tool="t", arguments={}, depends_on=["s1"]),
            WorkflowStep(id="s3", name="S3", tool="t", arguments={}, depends_on=["s2"]),
        ]
        assert _has_circular_dependency(steps) is False

    def test_simple_cycle(self):
        """Test simple circular dependency."""
        steps = [
            WorkflowStep(id="s1", name="S1", tool="t", arguments={}, depends_on=["s2"]),
            WorkflowStep(id="s2", name="S2", tool="t", arguments={}, depends_on=["s1"]),
        ]
        assert _has_circular_dependency(steps) is True

    def test_complex_cycle(self):
        """Test complex circular dependency."""
        steps = [
            WorkflowStep(id="s1", name="S1", tool="t", arguments={}),
            WorkflowStep(id="s2", name="S2", tool="t", arguments={}, depends_on=["s1"]),
            WorkflowStep(id="s3", name="S3", tool="t", arguments={}, depends_on=["s2", "s4"]),
            WorkflowStep(id="s4", name="S4", tool="t", arguments={}, depends_on=["s3"]),
        ]
        assert _has_circular_dependency(steps) is True


class TestWorkflowTemplates:
    """Tests for built-in workflow templates."""

    def test_templates_exist(self):
        """Test that templates are defined."""
        assert "search_and_summarise" in WORKFLOW_TEMPLATES
        assert "ingest_and_query" in WORKFLOW_TEMPLATES

    def test_templates_valid(self):
        """Test that all templates are valid."""
        for name, workflow in WORKFLOW_TEMPLATES.items():
            errors = validate_workflow(workflow)
            assert len(errors) == 0, f"Template '{name}' has errors: {errors}"


class MockTool(Tool):
    """Mock tool for testing executor."""

    def __init__(self, name: str, return_value=None):
        self._name = name
        self._return_value = return_value

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self._name,
            description=f"Mock {self._name}",
            category=ToolCategory.RAG,
            parameters={},
        )

    async def execute(self, context: ExecutionContext, **kwargs):
        if self._return_value is not None:
            return self._return_value
        return {"tool": self._name, "args": kwargs}


class TestWorkflowExecutor:
    """Tests for WorkflowExecutor class."""

    @pytest.fixture
    def registry(self):
        """Create a registry with mock tools."""
        registry = ToolRegistry()
        registry.register(MockTool("search", return_value={"results": []}))
        registry.register(MockTool("query", return_value={"answer": "test"}))
        registry.register(MockTool("ingest", return_value={"status": "ok"}))
        return registry

    @pytest.fixture
    def executor(self, registry):
        """Create an executor."""
        return WorkflowExecutor(registry)

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, executor):
        """Test executing a simple workflow."""
        workflow = WorkflowDefinition(
            id="simple",
            name="Simple",
            steps=[
                WorkflowStep(id="s1", name="Search", tool="search", arguments={"q": "test"}),
            ],
        )
        result = await executor.execute(workflow)

        assert result.state == WorkflowState.COMPLETED
        assert len(result.step_results) == 1
        assert result.step_results[0].success is True

    @pytest.mark.asyncio
    async def test_execute_multi_step_workflow(self, executor):
        """Test executing a multi-step workflow."""
        workflow = WorkflowDefinition(
            id="multi",
            name="Multi-Step",
            steps=[
                WorkflowStep(id="s1", name="Search", tool="search", arguments={}),
                WorkflowStep(id="s2", name="Query", tool="query", arguments={}, depends_on=["s1"]),
            ],
        )
        result = await executor.execute(workflow)

        assert result.state == WorkflowState.COMPLETED
        assert len(result.step_results) == 2
        assert all(r.success for r in result.step_results)

    @pytest.mark.asyncio
    async def test_execute_with_inputs(self, executor):
        """Test executing workflow with input substitution."""
        workflow = WorkflowDefinition(
            id="input",
            name="With Inputs",
            steps=[
                WorkflowStep(id="s1", name="Search", tool="search", arguments={"query": "{{input.query}}"}),
            ],
            inputs={"query": {"type": "string"}},
        )
        result = await executor.execute(workflow, inputs={"query": "test search"})

        assert result.state == WorkflowState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, executor):
        """Test executing workflow with unknown tool."""
        workflow = WorkflowDefinition(
            id="unknown",
            name="Unknown Tool",
            steps=[
                WorkflowStep(id="s1", name="Step", tool="nonexistent", arguments={}),
            ],
        )
        result = await executor.execute(workflow)

        assert result.state == WorkflowState.FAILED
        assert result.step_results[0].success is False
        assert "not found" in result.step_results[0].error.lower()

    @pytest.mark.asyncio
    async def test_execute_failed_dependency(self, executor):
        """Test that step is skipped when dependency fails."""
        # Create a tool that fails
        class FailingTool(Tool):
            @property
            def spec(self):
                return ToolSpec(name="failing", description="Fails", category=ToolCategory.RAG, parameters={})

            async def execute(self, context, **kwargs):
                raise Exception("Intentional failure")

        executor.tool_registry.register(FailingTool())

        workflow = WorkflowDefinition(
            id="dep",
            name="Dependency Test",
            steps=[
                WorkflowStep(id="s1", name="Fail", tool="failing", arguments={}),
                WorkflowStep(id="s2", name="Skip", tool="search", arguments={}, depends_on=["s1"]),
            ],
        )
        result = await executor.execute(workflow)

        assert result.state == WorkflowState.FAILED
        # Second step should have been skipped or not executed

    @pytest.mark.asyncio
    async def test_cancel_workflow(self, executor):
        """Test cancelling a workflow."""
        await executor.cancel()
        assert executor.state == WorkflowState.CANCELLED


class TestStepExecutionResult:
    """Tests for StepExecutionResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = StepExecutionResult(
            step_id="s1",
            success=True,
            output={"data": "test"},
            duration_ms=100,
        )
        assert result.success is True
        assert result.output == {"data": "test"}
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed result."""
        result = StepExecutionResult(
            step_id="s1",
            success=False,
            error="Something failed",
        )
        assert result.success is False
        assert result.error == "Something failed"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = StepExecutionResult(
            step_id="s1",
            success=True,
            output="data",
            duration_ms=50,
            retries_used=1,
        )
        d = result.to_dict()
        assert d["step_id"] == "s1"
        assert d["success"] is True
        assert d["retries_used"] == 1
