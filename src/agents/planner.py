"""Agent planning system for multi-step task decomposition.

Phase 2 Infrastructure: Decomposes tasks into executable steps.

Design Principles:
- LLM-based planning with tool awareness
- Iterative refinement based on execution results
- Observable planning process via events
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from ragged.agents.base import ExecutionContext, ToolSpec

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """A single step in an execution plan.

    Attributes:
        step_number: Order in the plan (1-indexed)
        description: Human-readable description
        tool_name: Tool to invoke for this step
        arguments: Arguments to pass to the tool
        depends_on: Step numbers this depends on
        expected_output: Description of expected result
    """

    step_number: int
    description: str
    tool_name: str
    arguments: dict[str, Any]
    depends_on: list[int] = field(default_factory=list)
    expected_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "description": self.description,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "depends_on": self.depends_on,
            "expected_output": self.expected_output,
        }


@dataclass
class Plan:
    """Execution plan for a task.

    Attributes:
        task: Original task description
        steps: Ordered list of steps to execute
        reasoning: Planner's reasoning for this plan
        metadata: Additional planning metadata
    """

    task: str
    steps: list[PlanStep]
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task": self.task,
            "steps": [s.to_dict() for s in self.steps],
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }


class Planner:
    """Creates execution plans from task descriptions.

    The planner analyses tasks and available tools to create
    step-by-step execution plans. It supports:
    - Simple single-step plans for basic tasks
    - Multi-step plans with dependencies
    - Plan refinement based on execution feedback

    Thread Safety:
        Planner instances are stateless and thread-safe.

    Example:
        >>> planner = Planner()
        >>> tools = [search_tool.spec, ingest_tool.spec]
        >>> plan = await planner.create_plan(
        ...     task="Find documents about authentication",
        ...     tools=tools,
        ...     context=context,
        ... )
        >>> print(plan.steps[0].tool_name)
        'search'
    """

    def __init__(self, model_name: str | None = None):
        """Initialise planner.

        Args:
            model_name: LLM model to use for planning (uses default if None)
        """
        self.model_name = model_name
        logger.debug(f"Planner initialised with model: {model_name or 'default'}")

    async def create_plan(
        self,
        task: str,
        tools: list[ToolSpec],
        context: ExecutionContext,
    ) -> Plan:
        """Create an execution plan for a task.

        Args:
            task: Task description in natural language
            tools: Available tools for the plan
            context: Execution context with user info

        Returns:
            Plan with steps to execute
        """
        logger.debug(f"Creating plan for task: {task[:50]}...")

        # Analyse task to determine required steps
        steps = await self._analyse_task(task, tools, context)

        plan = Plan(
            task=task,
            steps=steps,
            reasoning=self._generate_reasoning(task, steps, tools),
        )

        logger.info(f"Created plan with {len(steps)} steps for: {task[:30]}...")
        return plan

    async def refine_plan(
        self,
        plan: Plan,
        step_results: list[dict[str, Any]],
        tools: list[ToolSpec],
        context: ExecutionContext,
    ) -> Plan:
        """Refine a plan based on execution results.

        Called when a step fails or produces unexpected results.

        Args:
            plan: Original plan
            step_results: Results from executed steps
            tools: Available tools
            context: Execution context

        Returns:
            Refined plan with adjusted steps
        """
        logger.debug(f"Refining plan after {len(step_results)} steps")

        # Check for failures
        failed_steps = [r for r in step_results if not r.get("success", True)]

        if not failed_steps:
            # No failures, return remaining steps
            completed = len(step_results)
            remaining_steps = [
                PlanStep(
                    step_number=i + 1,
                    description=s.description,
                    tool_name=s.tool_name,
                    arguments=s.arguments,
                    depends_on=[d - completed for d in s.depends_on if d > completed],
                    expected_output=s.expected_output,
                )
                for i, s in enumerate(plan.steps[completed:])
            ]

            return Plan(
                task=plan.task,
                steps=remaining_steps,
                reasoning=f"Continuing plan after {completed} successful steps",
                metadata={"refined": True, "original_steps": len(plan.steps)},
            )

        # Handle failures by creating alternative steps
        alternative_steps = await self._handle_failures(
            plan, failed_steps, tools, context
        )

        return Plan(
            task=plan.task,
            steps=alternative_steps,
            reasoning=f"Refined plan after {len(failed_steps)} failures",
            metadata={"refined": True, "failures": len(failed_steps)},
        )

    async def _analyse_task(
        self,
        task: str,
        tools: list[ToolSpec],
        context: ExecutionContext,
    ) -> list[PlanStep]:
        """Analyse task and create execution steps.

        This is the core planning logic. Currently uses rule-based
        matching; future versions will use LLM-based planning.

        Args:
            task: Task description
            tools: Available tools
            context: Execution context

        Returns:
            List of plan steps
        """
        task_lower = task.lower()
        steps: list[PlanStep] = []

        # Build tool lookup
        tool_map = {t.name: t for t in tools}

        # Rule-based task analysis
        # Search/query tasks
        if any(kw in task_lower for kw in ["find", "search", "query", "look for"]):
            if "search" in tool_map:
                steps.append(PlanStep(
                    step_number=1,
                    description=f"Search for: {task}",
                    tool_name="search",
                    arguments={"query": task},
                    expected_output="List of relevant documents",
                ))

        # Ingest tasks
        elif any(kw in task_lower for kw in ["add", "ingest", "import", "upload"]):
            if "ingest" in tool_map:
                steps.append(PlanStep(
                    step_number=1,
                    description=f"Ingest documents: {task}",
                    tool_name="ingest",
                    arguments={"source": task},
                    expected_output="Ingestion result",
                ))

        # Analysis tasks
        elif any(kw in task_lower for kw in ["summarise", "summarize", "analyse", "analyze"]):
            # First search, then analyse
            if "search" in tool_map:
                steps.append(PlanStep(
                    step_number=1,
                    description="Find relevant documents",
                    tool_name="search",
                    arguments={"query": task},
                    expected_output="Documents to analyse",
                ))

            if "analyse" in tool_map or "analyze" in tool_map:
                tool_name = "analyse" if "analyse" in tool_map else "analyze"
                steps.append(PlanStep(
                    step_number=2,
                    description="Analyse found documents",
                    tool_name=tool_name,
                    arguments={"task": task},
                    depends_on=[1] if steps else [],
                    expected_output="Analysis result",
                ))

        # Default: try direct query
        if not steps and "query" in tool_map:
            steps.append(PlanStep(
                step_number=1,
                description=f"Query: {task}",
                tool_name="query",
                arguments={"question": task},
                expected_output="Query response",
            ))

        return steps

    async def _handle_failures(
        self,
        plan: Plan,
        failed_steps: list[dict[str, Any]],
        tools: list[ToolSpec],
        context: ExecutionContext,
    ) -> list[PlanStep]:
        """Create alternative steps after failures.

        Args:
            plan: Original plan
            failed_steps: Information about failed steps
            tools: Available tools
            context: Execution context

        Returns:
            Alternative steps to try
        """
        # Simple retry strategy - could be enhanced with LLM reasoning
        alternative_steps: list[PlanStep] = []

        for i, failure in enumerate(failed_steps):
            original_step_num = failure.get("step_number", i + 1)
            original_step = next(
                (s for s in plan.steps if s.step_number == original_step_num),
                None
            )

            if original_step:
                # Create retry with modified arguments
                alternative_steps.append(PlanStep(
                    step_number=i + 1,
                    description=f"Retry: {original_step.description}",
                    tool_name=original_step.tool_name,
                    arguments=original_step.arguments,
                    expected_output=original_step.expected_output,
                ))

        return alternative_steps

    def _generate_reasoning(
        self,
        task: str,
        steps: list[PlanStep],
        tools: list[ToolSpec],
    ) -> str:
        """Generate human-readable reasoning for the plan.

        Args:
            task: Original task
            steps: Planned steps
            tools: Available tools

        Returns:
            Reasoning explanation
        """
        if not steps:
            return f"No suitable tools found for task: {task}"

        tool_names = [s.tool_name for s in steps]
        return (
            f"To accomplish '{task[:50]}...', "
            f"will use {len(steps)} step(s) with tools: {', '.join(tool_names)}"
        )
