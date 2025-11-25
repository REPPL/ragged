"""Agent framework for multi-step task execution.

Phase 2 Infrastructure: Enables autonomous task completion through:
- Tool-based RAG operations (search, ingest, query)
- Multi-step planning and execution
- Workflow definitions for complex tasks
- Integration with existing plugin sandbox

Usage:
    >>> from ragged.agents import Agent, ToolRegistry
    >>>
    >>> # Create agent with tools
    >>> registry = ToolRegistry()
    >>> registry.register_defaults()
    >>> agent = Agent(tool_registry=registry)
    >>>
    >>> # Execute task
    >>> result = await agent.run("Find documents about authentication")
"""

from ragged.agents.base import (
    Agent,
    AgentConfig,
    AgentState,
    ExecutionContext,
    StepResult,
)
from ragged.agents.planner import Planner, Plan, PlanStep
from ragged.agents.executor import Executor, ExecutionResult
from ragged.agents.registry import ToolRegistry

__all__ = [
    # Core
    "Agent",
    "AgentConfig",
    "AgentState",
    "ExecutionContext",
    "StepResult",
    # Planning
    "Planner",
    "Plan",
    "PlanStep",
    # Execution
    "Executor",
    "ExecutionResult",
    # Tools
    "ToolRegistry",
]
