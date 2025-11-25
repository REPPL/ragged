"""Workflow execution engine.

Phase 2 Infrastructure: Execute workflow definitions.

Design Principles:
- Respect step dependencies
- Emit events for observability
- Handle failures gracefully
- Support variable substitution
"""

import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ragged.agents.base import (
    AgentConfig,
    AgentResult,
    AgentState,
    ExecutionContext,
    StepResult,
    ToolCall,
    ToolResult,
)
from ragged.agents.registry import ToolRegistry
from ragged.agents.workflows.definition import WorkflowDefinition, WorkflowStep
from ragged.auth.user import User, get_current_user
from ragged.core.events import AgentEvent, get_event_bus

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow execution state."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepExecutionResult:
    """Result of executing a workflow step.

    Attributes:
        step_id: Step identifier
        success: Whether step succeeded
        output: Step output
        error: Error message if failed
        duration_ms: Execution time
        retries_used: Number of retries attempted
    """

    step_id: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: float = 0
    retries_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries_used": self.retries_used,
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution.

    Attributes:
        workflow_id: Workflow identifier
        execution_id: Unique execution identifier
        state: Final workflow state
        step_results: Results for each step
        outputs: Final workflow outputs
        duration_ms: Total execution time
        error: Error message if failed
    """

    workflow_id: str
    execution_id: str
    state: WorkflowState
    step_results: list[StepExecutionResult]
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "state": self.state.value,
            "step_results": [r.to_dict() for r in self.step_results],
            "outputs": self.outputs,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


class WorkflowExecutor:
    """Execute workflow definitions.

    Handles step execution, dependency resolution, variable substitution,
    and failure recovery.

    Thread Safety:
        Not thread-safe. Create one executor per workflow execution.

    Example:
        >>> executor = WorkflowExecutor(registry)
        >>> result = await executor.execute(
        ...     workflow,
        ...     inputs={"query": "authentication"},
        ... )
        >>> print(result.state)
        WorkflowState.COMPLETED
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        config: AgentConfig | None = None,
    ):
        """Initialise executor.

        Args:
            tool_registry: Registry of available tools
            config: Agent configuration
        """
        self.tool_registry = tool_registry
        self.config = config or AgentConfig()
        self._event_bus = get_event_bus()

        # Execution state
        self._state = WorkflowState.PENDING
        self._step_outputs: dict[str, Any] = {}
        self._current_step: str | None = None

        logger.debug("WorkflowExecutor initialised")

    @property
    def state(self) -> WorkflowState:
        """Get current execution state."""
        return self._state

    async def execute(
        self,
        workflow: WorkflowDefinition,
        inputs: dict[str, Any] | None = None,
        user: User | None = None,
    ) -> WorkflowResult:
        """Execute a workflow.

        Args:
            workflow: Workflow definition to execute
            inputs: Input values for workflow variables
            user: User executing the workflow

        Returns:
            WorkflowResult with execution details
        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())
        inputs = inputs or {}

        if user is None:
            user = get_current_user()

        logger.info(f"Starting workflow '{workflow.name}' (exec: {execution_id[:8]})")

        # Create execution context
        context = ExecutionContext(
            user=user,
            session_id=str(uuid.uuid4()),
            task_id=execution_id,
            variables={"input": inputs},
        )

        # Publish workflow started event
        await self._event_bus.publish(AgentEvent(
            event_type="workflow.started",
            agent_id="workflow",
            task_id=execution_id,
            status="started",
        ))

        self._state = WorkflowState.RUNNING
        step_results: list[StepExecutionResult] = []

        try:
            # Sort steps by dependencies
            sorted_steps = self._topological_sort(workflow.steps)

            # Execute each step
            for step in sorted_steps:
                self._current_step = step.id

                # Check if dependencies succeeded
                if not self._dependencies_satisfied(step, step_results):
                    step_results.append(StepExecutionResult(
                        step_id=step.id,
                        success=False,
                        error="Dependencies not satisfied",
                    ))
                    if step.on_failure == "stop":
                        break
                    continue

                # Check condition (if any)
                if step.condition and not self._evaluate_condition(step.condition, context):
                    logger.debug(f"Skipping step '{step.id}' (condition not met)")
                    continue

                # Execute step with retries
                result = await self._execute_step_with_retries(step, context)
                step_results.append(result)

                # Store output for variable substitution
                if result.success:
                    self._step_outputs[step.id] = result.output
                    context.set_variable(f"step.{step.id}", result.output)

                # Handle failure
                if not result.success:
                    if step.on_failure == "stop":
                        self._state = WorkflowState.FAILED
                        break
                    elif step.on_failure == "continue":
                        logger.warning(f"Step '{step.id}' failed, continuing...")

            # Determine final state
            if self._state == WorkflowState.RUNNING:
                all_success = all(r.success for r in step_results if r.success is not None)
                self._state = WorkflowState.COMPLETED if all_success else WorkflowState.FAILED

            # Build outputs
            outputs = self._build_outputs(workflow, step_results)

            # Publish workflow completed event
            await self._event_bus.publish(AgentEvent(
                event_type="workflow.completed",
                agent_id="workflow",
                task_id=execution_id,
                status=self._state.value,
            ))

            return WorkflowResult(
                workflow_id=workflow.id,
                execution_id=execution_id,
                state=self._state,
                step_results=step_results,
                outputs=outputs,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            self._state = WorkflowState.FAILED

            # Publish workflow failed event
            await self._event_bus.publish(AgentEvent(
                event_type="workflow.failed",
                agent_id="workflow",
                task_id=execution_id,
                status="failed",
            ))

            return WorkflowResult(
                workflow_id=workflow.id,
                execution_id=execution_id,
                state=WorkflowState.FAILED,
                step_results=step_results,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _execute_step_with_retries(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> StepExecutionResult:
        """Execute a step with retry support.

        Args:
            step: Step to execute
            context: Execution context

        Returns:
            Step execution result
        """
        start_time = time.time()
        last_error: str | None = None
        retries = 0

        for attempt in range(step.retries + 1):
            if attempt > 0:
                logger.info(f"Retrying step '{step.id}' (attempt {attempt + 1})")
                retries = attempt

            result = await self._execute_step(step, context)

            if result.success:
                result.retries_used = retries
                return result

            last_error = result.error

            # Don't retry if not configured
            if step.on_failure != "retry":
                break

        return StepExecutionResult(
            step_id=step.id,
            success=False,
            error=last_error,
            duration_ms=(time.time() - start_time) * 1000,
            retries_used=retries,
        )

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> StepExecutionResult:
        """Execute a single step.

        Args:
            step: Step to execute
            context: Execution context

        Returns:
            Step execution result
        """
        start_time = time.time()

        # Publish step started event
        await self._event_bus.publish(AgentEvent(
            event_type="workflow.step_started",
            agent_id="workflow",
            task_id=context.task_id,
            step=step.id,
            status="started",
        ))

        # Get tool
        tool = self.tool_registry.get_tool(step.tool)
        if tool is None:
            return StepExecutionResult(
                step_id=step.id,
                success=False,
                error=f"Tool not found: {step.tool}",
                duration_ms=(time.time() - start_time) * 1000,
            )

        # Substitute variables in arguments
        arguments = self._substitute_variables(step.arguments, context)

        try:
            # Execute tool
            output = await tool.execute(context, **arguments)

            # Publish step completed event
            await self._event_bus.publish(AgentEvent(
                event_type="workflow.step_completed",
                agent_id="workflow",
                task_id=context.task_id,
                step=step.id,
                status="completed",
            ))

            return StepExecutionResult(
                step_id=step.id,
                success=True,
                output=output,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.warning(f"Step '{step.id}' failed: {e}")

            # Publish step failed event
            await self._event_bus.publish(AgentEvent(
                event_type="workflow.step_failed",
                agent_id="workflow",
                task_id=context.task_id,
                step=step.id,
                status="failed",
            ))

            return StepExecutionResult(
                step_id=step.id,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _substitute_variables(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Substitute variables in arguments.

        Supports {{input.name}} and {{step.id.field}} syntax.

        Args:
            arguments: Arguments with variable placeholders
            context: Execution context with variable values

        Returns:
            Arguments with substituted values
        """
        result = {}

        for key, value in arguments.items():
            if isinstance(value, str):
                result[key] = self._substitute_string(value, context)
            elif isinstance(value, dict):
                result[key] = self._substitute_variables(value, context)
            elif isinstance(value, list):
                result[key] = [
                    self._substitute_string(v, context) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                result[key] = value

        return result

    def _substitute_string(self, value: str, context: ExecutionContext) -> str:
        """Substitute variables in a string.

        Args:
            value: String with {{variable}} placeholders
            context: Execution context

        Returns:
            String with substituted values
        """
        pattern = r"\{\{([^}]+)\}\}"

        def replace(match: re.Match) -> str:
            var_path = match.group(1).strip()
            parts = var_path.split(".")

            # Navigate variable path
            current = context.variables
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part, match.group(0))
                else:
                    return match.group(0)

            return str(current) if current is not None else match.group(0)

        return re.sub(pattern, replace, value)

    def _topological_sort(self, steps: list[WorkflowStep]) -> list[WorkflowStep]:
        """Sort steps by dependencies.

        Args:
            steps: Unsorted steps

        Returns:
            Steps in execution order
        """
        # Build graph
        in_degree: dict[str, int] = {s.id: len(s.depends_on) for s in steps}
        graph: dict[str, list[str]] = {s.id: [] for s in steps}

        for step in steps:
            for dep in step.depends_on:
                if dep in graph:
                    graph[dep].append(step.id)

        # Kahn's algorithm
        queue = [s.id for s in steps if in_degree[s.id] == 0]
        sorted_ids: list[str] = []

        while queue:
            node = queue.pop(0)
            sorted_ids.append(node)

            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Map back to steps
        step_map = {s.id: s for s in steps}
        return [step_map[sid] for sid in sorted_ids]

    def _dependencies_satisfied(
        self,
        step: WorkflowStep,
        results: list[StepExecutionResult],
    ) -> bool:
        """Check if step dependencies are satisfied.

        Args:
            step: Step to check
            results: Results from previous steps

        Returns:
            True if all dependencies succeeded
        """
        if not step.depends_on:
            return True

        result_map = {r.step_id: r for r in results}

        for dep_id in step.depends_on:
            dep_result = result_map.get(dep_id)
            if dep_result is None or not dep_result.success:
                return False

        return True

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a step condition.

        Args:
            condition: Condition expression
            context: Execution context

        Returns:
            True if condition is met
        """
        # Simple evaluation - expand as needed
        # Currently supports: "truthy" check on variable
        condition = condition.strip()

        # Check if it's a variable reference
        if condition.startswith("{{") and condition.endswith("}}"):
            var_path = condition[2:-2].strip()
            parts = var_path.split(".")

            current = context.variables
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return False

            return bool(current)

        # Default: treat as truthy
        return bool(condition)

    def _build_outputs(
        self,
        workflow: WorkflowDefinition,
        results: list[StepExecutionResult],
    ) -> dict[str, Any]:
        """Build workflow outputs from step results.

        Args:
            workflow: Workflow definition
            results: Step execution results

        Returns:
            Dictionary of output values
        """
        # Get last successful step output as default
        last_output = None
        for result in reversed(results):
            if result.success and result.output is not None:
                last_output = result.output
                break

        outputs = {
            "result": last_output,
            "step_outputs": {r.step_id: r.output for r in results if r.success},
        }

        return outputs

    async def cancel(self) -> None:
        """Cancel workflow execution."""
        self._state = WorkflowState.CANCELLED
        logger.info("Workflow execution cancelled")
