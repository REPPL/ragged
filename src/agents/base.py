"""Base agent classes and interfaces.

Phase 2 Infrastructure: Core agent abstractions for multi-step task execution.

Design Principles:
- Tool-based: Agents act through registered tools
- Observable: All steps emit events for monitoring
- Safe: Tools run in sandboxed environment
- Stateful: Execution context preserved across steps
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from ragged.auth.user import User, get_current_user
from ragged.core.events import AgentEvent, get_event_bus

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution state."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"  # Waiting for user input
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolCategory(Enum):
    """Tool categories for organisation and permissions."""

    RAG = "rag"  # Core RAG operations (query, ingest)
    STORAGE = "storage"  # Collection and document management
    ANALYSIS = "analysis"  # Document analysis, summarisation
    EXTERNAL = "external"  # Web search, APIs
    SYSTEM = "system"  # Configuration, diagnostics


@dataclass
class ToolSpec:
    """Specification for a tool available to agents.

    Attributes:
        name: Unique tool identifier
        description: Human-readable description for LLM
        category: Tool category for permissions
        parameters: Parameter schema (JSON Schema format)
        returns: Return value description
        examples: Example invocations
        requires_confirmation: Whether user confirmation needed
    """

    name: str
    description: str
    category: ToolCategory
    parameters: dict[str, Any]
    returns: str = ""
    examples: list[str] = field(default_factory=list)
    requires_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for LLM tool calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass
class ToolCall:
    """A tool invocation request.

    Attributes:
        tool_name: Name of tool to invoke
        arguments: Arguments to pass to tool
        call_id: Unique call identifier
    """

    tool_name: str
    arguments: dict[str, Any]
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class ToolResult:
    """Result of a tool invocation.

    Attributes:
        call_id: Matching call identifier
        success: Whether tool succeeded
        result: Tool output (if successful)
        error: Error message (if failed)
        duration_ms: Execution time in milliseconds
    """

    call_id: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class Tool(ABC):
    """Base class for agent tools.

    Tools wrap RAG capabilities for agent use, providing:
    - Consistent interface for invocation
    - Parameter validation
    - Error handling
    - Event emission

    Example:
        >>> class SearchTool(Tool):
        ...     @property
        ...     def spec(self) -> ToolSpec:
        ...         return ToolSpec(
        ...             name="search",
        ...             description="Search documents",
        ...             category=ToolCategory.RAG,
        ...             parameters={"query": {"type": "string"}}
        ...         )
        ...
        ...     async def execute(self, **kwargs) -> Any:
        ...         query = kwargs["query"]
        ...         return await self.rag_service.query(query)
    """

    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        """Get tool specification."""
        pass

    @abstractmethod
    async def execute(self, context: "ExecutionContext", **kwargs) -> Any:
        """Execute the tool.

        Args:
            context: Execution context with user, session info
            **kwargs: Tool-specific arguments

        Returns:
            Tool-specific result

        Raises:
            ToolExecutionError: If execution fails
        """
        pass

    def validate_args(self, **kwargs) -> None:
        """Validate arguments against spec.

        Args:
            **kwargs: Arguments to validate

        Raises:
            ValueError: If arguments invalid
        """
        required = []
        params = self.spec.parameters.get("properties", {})
        required_params = self.spec.parameters.get("required", [])

        for param in required_params:
            if param not in kwargs:
                required.append(param)

        if required:
            raise ValueError(f"Missing required parameters: {required}")


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, message: str, cause: Exception | None = None):
        super().__init__(f"Tool '{tool_name}' failed: {message}")
        self.tool_name = tool_name
        self.message = message
        self.cause = cause


@dataclass
class ExecutionContext:
    """Context for agent execution.

    Provides access to user info, session state, and shared resources.

    Attributes:
        user: User executing the agent
        session_id: Unique session identifier
        task_id: Current task identifier
        variables: Shared variables across steps
        history: Execution history
        metadata: Additional context metadata
    """

    user: User
    session_id: str
    task_id: str
    variables: dict[str, Any] = field(default_factory=dict)
    history: list["StepResult"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a context variable."""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a context variable."""
        return self.variables.get(name, default)

    def add_to_history(self, step: "StepResult") -> None:
        """Add step result to history."""
        self.history.append(step)


@dataclass
class StepResult:
    """Result of a single execution step.

    Attributes:
        step_number: Step sequence number
        tool_call: Tool that was called
        tool_result: Result from tool
        reasoning: Agent's reasoning for this step
        timestamp: When step completed
    """

    step_number: int
    tool_call: ToolCall | None
    tool_result: ToolResult | None
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "tool_call": {
                "tool_name": self.tool_call.tool_name,
                "arguments": self.tool_call.arguments,
            } if self.tool_call else None,
            "tool_result": self.tool_result.to_dict() if self.tool_result else None,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentConfig:
    """Configuration for agent behaviour.

    Attributes:
        max_steps: Maximum execution steps
        timeout_seconds: Overall timeout
        require_confirmation: Require user confirmation for actions
        allowed_categories: Tool categories agent can use
        temperature: LLM temperature for planning
        verbose: Enable verbose logging
    """

    max_steps: int = 10
    timeout_seconds: int = 300
    require_confirmation: bool = False
    allowed_categories: list[ToolCategory] = field(
        default_factory=lambda: [ToolCategory.RAG, ToolCategory.STORAGE, ToolCategory.ANALYSIS]
    )
    temperature: float = 0.0
    verbose: bool = False


@dataclass
class AgentResult:
    """Final result of agent execution.

    Attributes:
        task_id: Task identifier
        state: Final agent state
        output: Final output/answer
        steps: All execution steps
        total_duration_ms: Total execution time
        error: Error message if failed
    """

    task_id: str
    state: AgentState
    output: Any
    steps: list[StepResult]
    total_duration_ms: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "state": self.state.value,
            "output": self.output,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
        }


class Agent:
    """Multi-step task execution agent.

    Agents use tools to complete tasks through planning and execution:
    1. Receive task from user
    2. Plan steps to complete task
    3. Execute steps using tools
    4. Return final result

    Thread Safety:
        Agents are not thread-safe. Create one agent per task.

    Example:
        >>> from ragged.agents import Agent, ToolRegistry
        >>>
        >>> registry = ToolRegistry()
        >>> registry.register_defaults()
        >>> agent = Agent(tool_registry=registry)
        >>>
        >>> result = await agent.run("Find documents about authentication")
        >>> print(result.output)
    """

    def __init__(
        self,
        tool_registry: "ToolRegistry",
        config: AgentConfig | None = None,
        planner: "Planner | None" = None,
        executor: "Executor | None" = None,
    ):
        """Initialise agent.

        Args:
            tool_registry: Registry of available tools
            config: Agent configuration
            planner: Custom planner (uses default if None)
            executor: Custom executor (uses default if None)
        """
        from ragged.agents.planner import Planner
        from ragged.agents.executor import Executor

        self.tool_registry = tool_registry
        self.config = config or AgentConfig()
        self.planner = planner or Planner()
        self.executor = executor or Executor(tool_registry)

        self._state = AgentState.IDLE
        self._event_bus = get_event_bus()

        logger.debug(f"Agent initialised with {len(tool_registry.list_tools())} tools")

    @property
    def state(self) -> AgentState:
        """Get current agent state."""
        return self._state

    async def run(
        self,
        task: str,
        user: User | None = None,
        context: ExecutionContext | None = None,
    ) -> AgentResult:
        """Execute a task.

        Args:
            task: Task description in natural language
            user: User executing the task
            context: Existing context (creates new if None)

        Returns:
            AgentResult with execution details
        """
        import time

        start_time = time.time()

        if user is None:
            user = get_current_user()

        task_id = str(uuid.uuid4())

        if context is None:
            context = ExecutionContext(
                user=user,
                session_id=str(uuid.uuid4()),
                task_id=task_id,
            )

        # Publish task started event
        await self._event_bus.publish(AgentEvent(
            event_type="agent.task_started",
            agent_id="default",
            task_id=task_id,
            status="started",
        ))

        try:
            self._state = AgentState.PLANNING

            # Get available tools for planning
            available_tools = self._get_available_tools()

            # Plan execution steps
            plan = await self.planner.create_plan(
                task=task,
                tools=available_tools,
                context=context,
            )

            if not plan.steps:
                # Simple task - execute directly
                self._state = AgentState.EXECUTING
                output = f"Task '{task}' requires no tool execution."
                self._state = AgentState.COMPLETED

                return AgentResult(
                    task_id=task_id,
                    state=AgentState.COMPLETED,
                    output=output,
                    steps=[],
                    total_duration_ms=(time.time() - start_time) * 1000,
                )

            # Execute plan
            self._state = AgentState.EXECUTING
            steps: list[StepResult] = []
            output = None

            for i, plan_step in enumerate(plan.steps):
                if i >= self.config.max_steps:
                    logger.warning(f"Max steps ({self.config.max_steps}) reached")
                    break

                # Publish step progress
                await self._event_bus.publish(AgentEvent(
                    event_type="agent.step_started",
                    agent_id="default",
                    task_id=task_id,
                    step=i + 1,
                    total_steps=len(plan.steps),
                    status="progress",
                ))

                # Execute step
                step_result = await self.executor.execute_step(
                    step=plan_step,
                    context=context,
                    step_number=i + 1,
                )

                steps.append(step_result)
                context.add_to_history(step_result)

                # Check for failure
                if step_result.tool_result and not step_result.tool_result.success:
                    self._state = AgentState.FAILED
                    return AgentResult(
                        task_id=task_id,
                        state=AgentState.FAILED,
                        output=None,
                        steps=steps,
                        total_duration_ms=(time.time() - start_time) * 1000,
                        error=step_result.tool_result.error,
                    )

                # Store last result as output
                if step_result.tool_result:
                    output = step_result.tool_result.result

            self._state = AgentState.COMPLETED

            # Publish task completed
            await self._event_bus.publish(AgentEvent(
                event_type="agent.task_completed",
                agent_id="default",
                task_id=task_id,
                status="completed",
                output=str(output)[:500] if output else None,
            ))

            return AgentResult(
                task_id=task_id,
                state=AgentState.COMPLETED,
                output=output,
                steps=steps,
                total_duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            self._state = AgentState.FAILED
            logger.exception(f"Agent execution failed: {e}")

            # Publish task failed
            await self._event_bus.publish(AgentEvent(
                event_type="agent.task_failed",
                agent_id="default",
                task_id=task_id,
                status="failed",
            ))

            return AgentResult(
                task_id=task_id,
                state=AgentState.FAILED,
                output=None,
                steps=[],
                total_duration_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )

    def _get_available_tools(self) -> list[ToolSpec]:
        """Get tools available based on config."""
        all_tools = self.tool_registry.list_tools()
        return [
            tool.spec for tool in all_tools
            if tool.spec.category in self.config.allowed_categories
        ]

    async def cancel(self) -> None:
        """Cancel current execution."""
        self._state = AgentState.CANCELLED
        logger.info("Agent execution cancelled")
