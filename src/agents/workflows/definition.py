"""Workflow definition and validation.

Phase 2 Infrastructure: JSON-based workflow definitions.

Design Principles:
- Declarative workflow structure
- Schema validation
- Reusable step definitions
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowTrigger(Enum):
    """How a workflow can be triggered."""

    MANUAL = "manual"  # User-initiated
    SCHEDULED = "scheduled"  # Time-based (cron)
    EVENT = "event"  # On event (file change, etc.)
    API = "api"  # API call


@dataclass
class WorkflowStep:
    """A single step in a workflow.

    Attributes:
        id: Unique step identifier
        name: Human-readable name
        tool: Tool to execute
        arguments: Arguments for the tool
        depends_on: List of step IDs this depends on
        condition: Optional condition for execution
        on_failure: Action on failure ('stop', 'continue', 'retry')
        retries: Number of retries on failure
        timeout_seconds: Step timeout
    """

    id: str
    name: str
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: str | None = None
    on_failure: str = "stop"
    retries: int = 0
    timeout_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tool": self.tool,
            "arguments": self.arguments,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "on_failure": self.on_failure,
            "retries": self.retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            tool=data["tool"],
            arguments=data.get("arguments", {}),
            depends_on=data.get("depends_on", []),
            condition=data.get("condition"),
            on_failure=data.get("on_failure", "stop"),
            retries=data.get("retries", 0),
            timeout_seconds=data.get("timeout_seconds", 60),
        )


@dataclass
class WorkflowDefinition:
    """Complete workflow definition.

    Attributes:
        id: Unique workflow identifier
        name: Human-readable name
        description: Workflow description
        version: Workflow version
        trigger: How workflow is triggered
        steps: Ordered list of steps
        inputs: Expected input parameters
        outputs: Output specification
        metadata: Additional metadata
    """

    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    trigger: WorkflowTrigger = WorkflowTrigger.MANUAL
    steps: list[WorkflowStep] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "trigger": self.trigger.value,
            "steps": [s.to_dict() for s in self.steps],
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowDefinition":
        """Create from dictionary."""
        trigger_str = data.get("trigger", "manual")
        trigger = WorkflowTrigger(trigger_str)

        steps = [
            WorkflowStep.from_dict(s)
            for s in data.get("steps", [])
        ]

        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            trigger=trigger,
            steps=steps,
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowDefinition":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


def load_workflow(path: Path) -> WorkflowDefinition:
    """Load workflow from JSON file.

    Args:
        path: Path to workflow JSON file

    Returns:
        WorkflowDefinition instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid JSON or missing required fields
    """
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {path}")

    try:
        with open(path) as f:
            data = json.load(f)

        workflow = WorkflowDefinition.from_dict(data)
        logger.info(f"Loaded workflow '{workflow.name}' from {path}")
        return workflow

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in workflow file: {e}")

    except KeyError as e:
        raise ValueError(f"Missing required field in workflow: {e}")


def validate_workflow(
    workflow: WorkflowDefinition,
    available_tools: list[str] | None = None,
) -> list[str]:
    """Validate a workflow definition.

    Args:
        workflow: Workflow to validate
        available_tools: List of available tool names (optional)

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Check required fields
    if not workflow.id:
        errors.append("Workflow ID is required")

    if not workflow.name:
        errors.append("Workflow name is required")

    if not workflow.steps:
        errors.append("Workflow must have at least one step")

    # Check step IDs are unique
    step_ids = [s.id for s in workflow.steps]
    if len(step_ids) != len(set(step_ids)):
        errors.append("Step IDs must be unique")

    # Check dependencies reference valid steps
    for step in workflow.steps:
        for dep_id in step.depends_on:
            if dep_id not in step_ids:
                errors.append(f"Step '{step.id}' depends on unknown step '{dep_id}'")

    # Check for circular dependencies
    if _has_circular_dependency(workflow.steps):
        errors.append("Workflow has circular dependencies")

    # Check tools exist (if tool list provided)
    if available_tools:
        for step in workflow.steps:
            if step.tool not in available_tools:
                errors.append(f"Step '{step.id}' uses unknown tool '{step.tool}'")

    # Validate on_failure values
    valid_on_failure = {"stop", "continue", "retry"}
    for step in workflow.steps:
        if step.on_failure not in valid_on_failure:
            errors.append(
                f"Step '{step.id}' has invalid on_failure: '{step.on_failure}'"
            )

    if errors:
        logger.warning(f"Workflow validation failed with {len(errors)} errors")
    else:
        logger.debug(f"Workflow '{workflow.name}' validated successfully")

    return errors


def _has_circular_dependency(steps: list[WorkflowStep]) -> bool:
    """Check for circular dependencies in steps.

    Args:
        steps: List of workflow steps

    Returns:
        True if circular dependency exists
    """
    # Build adjacency list
    graph: dict[str, list[str]] = {s.id: s.depends_on for s in steps}

    # Track visited and in-stack nodes
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str) -> bool:
        """Depth-first search for cycles."""
        if node in in_stack:
            return True  # Cycle found
        if node in visited:
            return False  # Already processed

        visited.add(node)
        in_stack.add(node)

        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True

        in_stack.remove(node)
        return False

    # Check each node
    for step_id in graph:
        if dfs(step_id):
            return True

    return False


# Built-in workflow templates
WORKFLOW_TEMPLATES = {
    "search_and_summarise": WorkflowDefinition(
        id="search_and_summarise",
        name="Search and Summarise",
        description="Search for documents and summarise the results",
        steps=[
            WorkflowStep(
                id="search",
                name="Search Documents",
                tool="search",
                arguments={"query": "{{input.query}}", "k": 10},
            ),
            WorkflowStep(
                id="summarise",
                name="Summarise Results",
                tool="query",
                arguments={
                    "question": "Summarise the following: {{input.query}}",
                    "k": 5,
                },
                depends_on=["search"],
            ),
        ],
        inputs={
            "query": {"type": "string", "description": "Search query", "required": True}
        },
    ),
    "ingest_and_query": WorkflowDefinition(
        id="ingest_and_query",
        name="Ingest and Query",
        description="Ingest a document and ask questions about it",
        steps=[
            WorkflowStep(
                id="ingest",
                name="Ingest Document",
                tool="ingest",
                arguments={"path": "{{input.path}}"},
            ),
            WorkflowStep(
                id="query",
                name="Query Document",
                tool="query",
                arguments={"question": "{{input.question}}"},
                depends_on=["ingest"],
            ),
        ],
        inputs={
            "path": {"type": "string", "description": "Document path", "required": True},
            "question": {"type": "string", "description": "Question to ask", "required": True},
        },
    ),
}
