"""Agent framework for multi-step task execution.

Phase 2 Infrastructure: Enables autonomous task completion through:
- Tool-based RAG operations (search, ingest, query)
- Multi-step planning and execution
- Workflow definitions for complex tasks
- Integration with existing plugin sandbox
- Memory and conversation history persistence
- Tool chaining and error recovery

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

    >>> # Use memory for context persistence
    >>> from ragged.agents import AgentMemory
    >>> memory = AgentMemory()
    >>> memory.start_conversation()
    >>> memory.add_turn("user", "Hello!")

    >>> # Chain tools together
    >>> from ragged.agents import chain, ChainExecutor
    >>> my_chain = chain("search_query").step("search", "search", {"query": "test"}).build()
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
from ragged.agents.memory import (
    AgentMemory,
    MemoryEntry,
    MemoryStore,
    InMemoryStore,
    FileStore,
    ConversationTurn,
)
from ragged.agents.history import (
    ConversationHistory,
    ConversationMetadata,
    HistoryMessage,
    Conversation,
    get_conversation_history,
)
from ragged.agents.chaining import (
    ToolChain,
    ChainStep,
    ChainResult,
    ChainStatus,
    ChainExecutor,
    ChainBuilder,
    CommonChains,
    chain,
)
from ragged.agents.retry import (
    RetryConfig,
    RetryStrategy,
    RetryState,
    RetryExecutor,
    RetryConfigs,
    ErrorCategory,
    ErrorClassifier,
    RecoveryAction,
    RecoveryManager,
    CircuitBreaker,
    with_retry,
)

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
    # Memory
    "AgentMemory",
    "MemoryEntry",
    "MemoryStore",
    "InMemoryStore",
    "FileStore",
    "ConversationTurn",
    # History
    "ConversationHistory",
    "ConversationMetadata",
    "HistoryMessage",
    "Conversation",
    "get_conversation_history",
    # Chaining
    "ToolChain",
    "ChainStep",
    "ChainResult",
    "ChainStatus",
    "ChainExecutor",
    "ChainBuilder",
    "CommonChains",
    "chain",
    # Retry & Recovery
    "RetryConfig",
    "RetryStrategy",
    "RetryState",
    "RetryExecutor",
    "RetryConfigs",
    "ErrorCategory",
    "ErrorClassifier",
    "RecoveryAction",
    "RecoveryManager",
    "CircuitBreaker",
    "with_retry",
]
