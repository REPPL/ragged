"""Agent tool chaining and pipeline execution.

Provides mechanisms for chaining tool executions together,
enabling complex multi-step operations with data flow between tools.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ChainStatus(Enum):
    """Status of a chain execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ChainStep:
    """A single step in a tool chain.

    Attributes:
        name: Step identifier
        tool_name: Name of the tool to execute
        arguments: Tool arguments (may include placeholders)
        transform: Optional function to transform output
        condition: Optional condition for execution
        on_error: Error handling strategy
    """

    name: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    transform: Callable[[Any], Any] | None = None
    condition: Callable[[dict[str, Any]], bool] | None = None
    on_error: str = "fail"  # fail, skip, retry
    max_retries: int = 3
    timeout: float | None = None

    def should_execute(self, context: dict[str, Any]) -> bool:
        """Check if step should execute based on condition."""
        if self.condition is None:
            return True
        try:
            return self.condition(context)
        except Exception as e:
            logger.warning(f"Condition check failed for step '{self.name}': {e}")
            return False

    def resolve_arguments(self, context: dict[str, Any]) -> dict[str, Any]:
        """Resolve argument placeholders from context.

        Placeholders use format: ${step_name.output} or ${step_name.key}
        """
        resolved = {}
        for key, value in self.arguments.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract reference path
                path = value[2:-1]  # Remove ${ and }
                parts = path.split(".")

                # Navigate context
                current = context
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        logger.warning(f"Could not resolve placeholder {value}")
                        current = value
                        break
                resolved[key] = current
            else:
                resolved[key] = value
        return resolved


@dataclass
class ChainResult:
    """Result of a chain step execution.

    Attributes:
        step_name: Name of the step
        status: Execution status
        output: Step output data
        error: Error message if failed
        duration: Execution time in seconds
        retries: Number of retry attempts
    """

    step_name: str
    status: ChainStatus
    output: Any = None
    error: str | None = None
    duration: float = 0.0
    retries: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration": self.duration,
            "retries": self.retries,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolChain:
    """A chain of tools to execute in sequence.

    Attributes:
        name: Chain identifier
        description: Human-readable description
        steps: Ordered list of chain steps
        metadata: Additional chain metadata
    """

    name: str
    description: str = ""
    steps: list[ChainStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        transform: Callable[[Any], Any] | None = None,
        condition: Callable[[dict[str, Any]], bool] | None = None,
        on_error: str = "fail",
    ) -> "ToolChain":
        """Add a step to the chain (fluent interface)."""
        step = ChainStep(
            name=name,
            tool_name=tool_name,
            arguments=arguments or {},
            transform=transform,
            condition=condition,
            on_error=on_error,
        )
        self.steps.append(step)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert chain to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "name": s.name,
                    "tool_name": s.tool_name,
                    "arguments": s.arguments,
                    "on_error": s.on_error,
                }
                for s in self.steps
            ],
            "metadata": self.metadata,
        }


class ChainExecutor:
    """Executes tool chains with context management.

    Manages the execution of multi-step tool chains, handling
    data flow, error recovery, and execution control.
    """

    def __init__(
        self,
        tool_registry: Any | None = None,
        max_concurrent: int = 1,
    ) -> None:
        """Initialise chain executor.

        Args:
            tool_registry: Registry for resolving tool names
            max_concurrent: Maximum concurrent step executions
        """
        self.tool_registry = tool_registry
        self.max_concurrent = max_concurrent
        self._execution_context: dict[str, Any] = {}
        self._results: list[ChainResult] = []
        self._cancelled = False

    async def execute(
        self,
        chain: ToolChain,
        initial_context: dict[str, Any] | None = None,
        execution_context: Any | None = None,
    ) -> list[ChainResult]:
        """Execute a tool chain.

        Args:
            chain: The chain to execute
            initial_context: Initial context data
            execution_context: Agent execution context

        Returns:
            List of results for each step
        """
        self._execution_context = initial_context or {}
        self._results = []
        self._cancelled = False

        logger.info(f"Starting chain execution: {chain.name}")

        for step in chain.steps:
            if self._cancelled:
                logger.info(f"Chain '{chain.name}' cancelled")
                break

            result = await self._execute_step(step, execution_context)
            self._results.append(result)

            if result.status == ChainStatus.FAILED and step.on_error == "fail":
                logger.error(f"Chain '{chain.name}' failed at step '{step.name}'")
                break

            # Store output in context for subsequent steps
            if result.output is not None:
                self._execution_context[step.name] = result.output

        return self._results

    async def _execute_step(
        self,
        step: ChainStep,
        execution_context: Any | None,
    ) -> ChainResult:
        """Execute a single chain step."""
        start_time = datetime.now()
        retries = 0

        # Check condition
        if not step.should_execute(self._execution_context):
            logger.info(f"Skipping step '{step.name}' - condition not met")
            return ChainResult(
                step_name=step.name,
                status=ChainStatus.COMPLETED,
                output=None,
                duration=0.0,
            )

        # Resolve arguments
        resolved_args = step.resolve_arguments(self._execution_context)

        while retries <= step.max_retries:
            try:
                logger.info(f"Executing step '{step.name}' (attempt {retries + 1})")

                # Execute the tool
                output = await self._invoke_tool(
                    step.tool_name,
                    resolved_args,
                    execution_context,
                    step.timeout,
                )

                # Apply transform if specified
                if step.transform is not None:
                    output = step.transform(output)

                duration = (datetime.now() - start_time).total_seconds()

                return ChainResult(
                    step_name=step.name,
                    status=ChainStatus.COMPLETED,
                    output=output,
                    duration=duration,
                    retries=retries,
                )

            except asyncio.TimeoutError:
                logger.warning(f"Step '{step.name}' timed out")
                error = "Execution timed out"
            except Exception as e:
                logger.warning(f"Step '{step.name}' failed: {e}")
                error = str(e)

            retries += 1

            if step.on_error == "skip":
                break
            if retries <= step.max_retries and step.on_error == "retry":
                await asyncio.sleep(0.5 * retries)  # Exponential backoff

        duration = (datetime.now() - start_time).total_seconds()
        status = ChainStatus.FAILED if step.on_error != "skip" else ChainStatus.COMPLETED

        return ChainResult(
            step_name=step.name,
            status=status,
            error=error,
            duration=duration,
            retries=retries - 1,
        )

    async def _invoke_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        execution_context: Any | None,
        timeout: float | None,
    ) -> Any:
        """Invoke a tool by name."""
        if self.tool_registry is None:
            raise ValueError("No tool registry configured")

        tool = self.tool_registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        # Execute with optional timeout
        coro = tool.execute(arguments, execution_context)
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro

    def cancel(self) -> None:
        """Cancel the current chain execution."""
        self._cancelled = True
        logger.info("Chain execution cancellation requested")

    @property
    def context(self) -> dict[str, Any]:
        """Get the current execution context."""
        return self._execution_context.copy()

    @property
    def results(self) -> list[ChainResult]:
        """Get results from the last execution."""
        return self._results.copy()


class ChainBuilder:
    """Fluent builder for creating tool chains."""

    def __init__(self, name: str, description: str = "") -> None:
        """Create a new chain builder."""
        self._chain = ToolChain(name=name, description=description)

    def step(
        self,
        name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> "ChainBuilder":
        """Add a step to the chain."""
        self._chain.add_step(name, tool_name, arguments)
        return self

    def transform(self, func: Callable[[Any], Any]) -> "ChainBuilder":
        """Add a transform to the last step."""
        if self._chain.steps:
            self._chain.steps[-1].transform = func
        return self

    def when(self, condition: Callable[[dict[str, Any]], bool]) -> "ChainBuilder":
        """Add a condition to the last step."""
        if self._chain.steps:
            self._chain.steps[-1].condition = condition
        return self

    def on_error(self, strategy: str) -> "ChainBuilder":
        """Set error handling for the last step."""
        if self._chain.steps:
            self._chain.steps[-1].on_error = strategy
        return self

    def with_timeout(self, seconds: float) -> "ChainBuilder":
        """Set timeout for the last step."""
        if self._chain.steps:
            self._chain.steps[-1].timeout = seconds
        return self

    def with_retries(self, max_retries: int) -> "ChainBuilder":
        """Set max retries for the last step."""
        if self._chain.steps:
            self._chain.steps[-1].max_retries = max_retries
        return self

    def metadata(self, **kwargs: Any) -> "ChainBuilder":
        """Add metadata to the chain."""
        self._chain.metadata.update(kwargs)
        return self

    def build(self) -> ToolChain:
        """Build and return the chain."""
        return self._chain


# Convenience function for creating chains
def chain(name: str, description: str = "") -> ChainBuilder:
    """Create a new chain builder.

    Example:
        my_chain = (
            chain("search_and_summarise", "Search then summarise results")
            .step("search", "search_tool", {"query": "example"})
            .step("summarise", "summarise_tool", {"text": "${search.output}"})
            .build()
        )
    """
    return ChainBuilder(name, description)


# Pre-built common chains
class CommonChains:
    """Factory for common tool chain patterns."""

    @staticmethod
    def search_and_query(query: str) -> ToolChain:
        """Create a search-then-query chain."""
        return (
            chain("search_and_query", "Search documents then query for answer")
            .step("search", "search", {"query": query, "limit": 5})
            .step("query", "query", {"query": query, "context": "${search.output}"})
            .build()
        )

    @staticmethod
    def ingest_and_index(source: str) -> ToolChain:
        """Create an ingest-then-index chain."""
        return (
            chain("ingest_and_index", "Ingest documents and update index")
            .step("ingest", "ingest", {"source": source})
            .on_error("fail")
            .step("reindex", "reindex", {"collection": "${ingest.collection}"})
            .on_error("skip")
            .build()
        )

    @staticmethod
    def validate_and_process(data: Any) -> ToolChain:
        """Create a validation-then-processing chain."""
        return (
            chain("validate_and_process", "Validate then process data")
            .step("validate", "validate", {"data": data})
            .when(lambda ctx: ctx.get("validate", {}).get("valid", False))
            .step("process", "process", {"data": "${validate.data}"})
            .build()
        )
