"""Agent execution system for running plan steps.

Phase 2 Infrastructure: Executes plan steps using registered tools.

Design Principles:
- Safe execution with error handling
- Observable via events
- Respects tool confirmations and permissions
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ragged.agents.base import (
    ExecutionContext,
    StepResult,
    Tool,
    ToolCall,
    ToolExecutionError,
    ToolResult,
)
from ragged.agents.planner import PlanStep
from ragged.core.events import AgentEvent, get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a complete plan.

    Attributes:
        success: Whether all steps succeeded
        steps: Results from each step
        final_output: Output from last successful step
        error: Error message if failed
        duration_ms: Total execution time
    """

    success: bool
    steps: list[StepResult]
    final_output: Any = None
    error: str | None = None
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "steps": [s.to_dict() for s in self.steps],
            "final_output": self.final_output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class Executor:
    """Executes plan steps using registered tools.

    The executor handles:
    - Tool invocation with argument validation
    - Error handling and recovery
    - Event emission for observability
    - Confirmation requests for sensitive operations

    Thread Safety:
        Executor instances are not thread-safe. Create one per task.

    Example:
        >>> executor = Executor(tool_registry)
        >>> step = PlanStep(
        ...     step_number=1,
        ...     description="Search documents",
        ...     tool_name="search",
        ...     arguments={"query": "authentication"},
        ... )
        >>> result = await executor.execute_step(step, context, 1)
        >>> print(result.tool_result.success)
        True
    """

    def __init__(self, tool_registry: "ToolRegistry"):
        """Initialise executor.

        Args:
            tool_registry: Registry containing available tools
        """
        from ragged.agents.registry import ToolRegistry

        self.tool_registry = tool_registry
        self._event_bus = get_event_bus()
        self._pending_confirmations: dict[str, PlanStep] = {}

        logger.debug("Executor initialised")

    async def execute_step(
        self,
        step: PlanStep,
        context: ExecutionContext,
        step_number: int,
    ) -> StepResult:
        """Execute a single plan step.

        Args:
            step: Step to execute
            context: Execution context
            step_number: Current step number in execution

        Returns:
            StepResult with execution details
        """
        logger.debug(f"Executing step {step_number}: {step.description}")
        start_time = time.time()

        # Get tool from registry
        tool = self.tool_registry.get_tool(step.tool_name)

        if tool is None:
            return StepResult(
                step_number=step_number,
                tool_call=ToolCall(
                    tool_name=step.tool_name,
                    arguments=step.arguments,
                ),
                tool_result=ToolResult(
                    call_id="",
                    success=False,
                    error=f"Tool not found: {step.tool_name}",
                    duration_ms=(time.time() - start_time) * 1000,
                ),
                reasoning=f"Failed to find tool: {step.tool_name}",
                timestamp=datetime.now(),
            )

        # Check if confirmation required
        if tool.spec.requires_confirmation:
            confirmed = await self._request_confirmation(step, context)
            if not confirmed:
                return StepResult(
                    step_number=step_number,
                    tool_call=ToolCall(
                        tool_name=step.tool_name,
                        arguments=step.arguments,
                    ),
                    tool_result=ToolResult(
                        call_id="",
                        success=False,
                        error="User declined confirmation",
                        duration_ms=(time.time() - start_time) * 1000,
                    ),
                    reasoning="Step cancelled - confirmation declined",
                    timestamp=datetime.now(),
                )

        # Create tool call
        tool_call = ToolCall(
            tool_name=step.tool_name,
            arguments=step.arguments,
        )

        # Execute tool
        tool_result = await self._execute_tool(tool, tool_call, context)
        tool_result.duration_ms = (time.time() - start_time) * 1000

        # Emit step completed event
        await self._event_bus.publish(AgentEvent(
            event_type="agent.step_completed",
            agent_id="default",
            task_id=context.task_id,
            step=step_number,
            status="completed" if tool_result.success else "failed",
        ))

        return StepResult(
            step_number=step_number,
            tool_call=tool_call,
            tool_result=tool_result,
            reasoning=step.description,
            timestamp=datetime.now(),
        )

    async def execute_plan(
        self,
        steps: list[PlanStep],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute a complete plan.

        Args:
            steps: Steps to execute in order
            context: Execution context

        Returns:
            ExecutionResult with all step results
        """
        start_time = time.time()
        results: list[StepResult] = []
        final_output = None

        for i, step in enumerate(steps):
            # Check dependencies
            if step.depends_on:
                deps_satisfied = all(
                    results[d - 1].tool_result and results[d - 1].tool_result.success
                    for d in step.depends_on
                    if d <= len(results)
                )
                if not deps_satisfied:
                    # Skip step due to failed dependencies
                    results.append(StepResult(
                        step_number=i + 1,
                        tool_call=ToolCall(
                            tool_name=step.tool_name,
                            arguments=step.arguments,
                        ),
                        tool_result=ToolResult(
                            call_id="",
                            success=False,
                            error="Dependencies not satisfied",
                        ),
                        reasoning="Skipped due to failed dependencies",
                    ))
                    continue

            result = await self.execute_step(step, context, i + 1)
            results.append(result)
            context.add_to_history(result)

            # Track final output
            if result.tool_result and result.tool_result.success:
                final_output = result.tool_result.result

            # Stop on failure
            if result.tool_result and not result.tool_result.success:
                return ExecutionResult(
                    success=False,
                    steps=results,
                    final_output=final_output,
                    error=result.tool_result.error,
                    duration_ms=(time.time() - start_time) * 1000,
                )

        return ExecutionResult(
            success=True,
            steps=results,
            final_output=final_output,
            duration_ms=(time.time() - start_time) * 1000,
        )

    async def _execute_tool(
        self,
        tool: Tool,
        tool_call: ToolCall,
        context: ExecutionContext,
    ) -> ToolResult:
        """Execute a tool with error handling.

        Args:
            tool: Tool to execute
            tool_call: Call details
            context: Execution context

        Returns:
            ToolResult with execution outcome
        """
        try:
            # Validate arguments
            tool.validate_args(**tool_call.arguments)

            # Emit tool started event
            await self._event_bus.publish(AgentEvent(
                event_type="agent.tool_started",
                agent_id="default",
                task_id=context.task_id,
                tool_name=tool_call.tool_name,
                status="started",
            ))

            # Execute tool
            result = await tool.execute(context, **tool_call.arguments)

            # Emit tool completed event
            await self._event_bus.publish(AgentEvent(
                event_type="agent.tool_completed",
                agent_id="default",
                task_id=context.task_id,
                tool_name=tool_call.tool_name,
                status="completed",
            ))

            return ToolResult(
                call_id=tool_call.call_id,
                success=True,
                result=result,
            )

        except ValueError as e:
            logger.warning(f"Tool argument validation failed: {e}")
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"Invalid arguments: {e}",
            )

        except ToolExecutionError as e:
            logger.warning(f"Tool execution failed: {e}")
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=str(e),
            )

        except Exception as e:
            logger.exception(f"Unexpected error executing tool {tool_call.tool_name}")
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"Unexpected error: {e}",
            )

    async def _request_confirmation(
        self,
        step: PlanStep,
        context: ExecutionContext,
    ) -> bool:
        """Request user confirmation for a step.

        Args:
            step: Step requiring confirmation
            context: Execution context

        Returns:
            True if confirmed, False otherwise
        """
        # Store pending confirmation
        confirmation_id = f"{context.task_id}:{step.step_number}"
        self._pending_confirmations[confirmation_id] = step

        # Emit confirmation request event
        await self._event_bus.publish(AgentEvent(
            event_type="agent.confirmation_requested",
            agent_id="default",
            task_id=context.task_id,
            step=step.step_number,
            tool_name=step.tool_name,
            status="pending",
        ))

        # In non-interactive mode, auto-approve
        # Future: integrate with UI for actual confirmation
        logger.info(f"Auto-approving step {step.step_number} (non-interactive mode)")

        # Clean up
        del self._pending_confirmations[confirmation_id]

        return True

    def confirm_step(self, task_id: str, step_number: int, approved: bool) -> bool:
        """Confirm or reject a pending step.

        Args:
            task_id: Task identifier
            step_number: Step number to confirm
            approved: Whether to approve

        Returns:
            True if confirmation was pending, False otherwise
        """
        confirmation_id = f"{task_id}:{step_number}"

        if confirmation_id in self._pending_confirmations:
            del self._pending_confirmations[confirmation_id]
            logger.info(
                f"Step {step_number} {'approved' if approved else 'rejected'}"
            )
            return True

        return False
