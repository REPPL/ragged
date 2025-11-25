"""Workflow system for agent framework.

Phase 2 Infrastructure: Declarative workflow definitions and execution.

Workflows are JSON-defined sequences of agent tasks that can be:
- Loaded from files or created programmatically
- Executed with progress tracking
- Validated before execution
- Composed from reusable steps
"""

from ragged.agents.workflows.definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTrigger,
    load_workflow,
    validate_workflow,
    WORKFLOW_TEMPLATES,
)
from ragged.agents.workflows.executor import (
    WorkflowExecutor,
    WorkflowResult,
    WorkflowState,
)

__all__ = [
    # Definitions
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowTrigger",
    "load_workflow",
    "validate_workflow",
    "WORKFLOW_TEMPLATES",
    # Execution
    "WorkflowExecutor",
    "WorkflowResult",
    "WorkflowState",
]
