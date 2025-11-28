"""Pydantic schemas for Workflow API.

Provides request/response models for workflow endpoints:
- Workflow definitions and templates
- Workflow execution and progress
- Step management and results

v0.9.0: Initial implementation
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowStepSchema(BaseModel):
    """Schema for a workflow step."""

    id: str = Field(..., min_length=1, description="Unique step identifier")
    name: str = Field(..., min_length=1, description="Human-readable name")
    tool: str = Field(..., min_length=1, description="Tool to execute")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the tool"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="List of step IDs this depends on"
    )
    condition: str | None = Field(
        None, description="Optional condition for execution"
    )
    on_failure: Literal["stop", "continue", "retry"] = Field(
        "stop", description="Action on failure"
    )
    retries: int = Field(0, ge=0, le=10, description="Number of retries on failure")
    timeout_seconds: int = Field(
        60, ge=1, le=3600, description="Step timeout in seconds"
    )


class WorkflowInputSpec(BaseModel):
    """Schema for workflow input specification."""

    type: str = Field("string", description="Input type")
    description: str = Field("", description="Input description")
    required: bool = Field(True, description="Whether input is required")
    default: Any = Field(None, description="Default value")


class WorkflowDefinitionSchema(BaseModel):
    """Schema for a complete workflow definition."""

    id: str = Field(..., min_length=1, description="Unique workflow identifier")
    name: str = Field(..., min_length=1, description="Human-readable name")
    description: str = Field("", description="Workflow description")
    version: str = Field("1.0.0", description="Workflow version")
    trigger: Literal["manual", "scheduled", "event", "api"] = Field(
        "manual", description="How workflow is triggered"
    )
    steps: list[WorkflowStepSchema] = Field(
        ..., min_length=1, description="Ordered list of steps"
    )
    inputs: dict[str, WorkflowInputSpec] = Field(
        default_factory=dict, description="Expected input parameters"
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Output specification"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class WorkflowSummary(BaseModel):
    """Summary view of a workflow for listing."""

    id: str = Field(..., description="Workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field("", description="Brief description")
    version: str = Field(..., description="Workflow version")
    trigger: str = Field(..., description="Trigger type")
    step_count: int = Field(..., ge=0, description="Number of steps")
    is_template: bool = Field(False, description="Whether this is a built-in template")


class WorkflowListResponse(BaseModel):
    """Response for listing workflows."""

    workflows: list[WorkflowSummary] = Field(
        default_factory=list, description="List of workflows"
    )
    count: int = Field(..., ge=0, description="Total count")
    templates: int = Field(0, ge=0, description="Number of templates")
    custom: int = Field(0, ge=0, description="Number of custom workflows")


class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    id: str = Field(..., min_length=1, max_length=100, description="Workflow ID")
    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    description: str = Field("", max_length=1000, description="Description")
    steps: list[WorkflowStepSchema] = Field(
        ..., min_length=1, description="Workflow steps"
    )
    inputs: dict[str, WorkflowInputSpec] = Field(
        default_factory=dict, description="Input specifications"
    )
    trigger: Literal["manual", "scheduled", "event", "api"] = Field(
        "manual", description="Trigger type"
    )


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow."""

    inputs: dict[str, Any] = Field(
        default_factory=dict, description="Input values for the workflow"
    )
    persona: str = Field("default", description="Persona executing the workflow")
    async_execution: bool = Field(
        True, description="Execute asynchronously (recommended)"
    )


class StepResultSchema(BaseModel):
    """Schema for step execution result."""

    step_id: str = Field(..., description="Step identifier")
    success: bool = Field(..., description="Whether step succeeded")
    output: Any = Field(None, description="Step output")
    error: str | None = Field(None, description="Error message if failed")
    duration_ms: float = Field(0, ge=0, description="Execution time in milliseconds")
    retries_used: int = Field(0, ge=0, description="Number of retries attempted")
    started_at: datetime | None = Field(None, description="Start time")
    completed_at: datetime | None = Field(None, description="Completion time")


class ExecutionStatus(BaseModel):
    """Status of a workflow execution."""

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    state: Literal["pending", "running", "paused", "completed", "failed", "cancelled"] = Field(
        ..., description="Current execution state"
    )
    current_step: str | None = Field(None, description="Currently executing step")
    progress: float = Field(
        0, ge=0, le=1, description="Execution progress (0-1)"
    )
    started_at: datetime | None = Field(None, description="Execution start time")
    completed_at: datetime | None = Field(None, description="Execution completion time")


class ExecutionResponse(BaseModel):
    """Response for workflow execution."""

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    state: str = Field(..., description="Execution state")
    message: str = Field(..., description="Status message")


class ExecutionDetailResponse(BaseModel):
    """Detailed execution response with results."""

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    state: str = Field(..., description="Final execution state")
    step_results: list[StepResultSchema] = Field(
        default_factory=list, description="Results for each step"
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Final workflow outputs"
    )
    duration_ms: float = Field(0, ge=0, description="Total execution time")
    error: str | None = Field(None, description="Error message if failed")
    started_at: datetime | None = Field(None, description="Start time")
    completed_at: datetime | None = Field(None, description="Completion time")


class ExecutionListResponse(BaseModel):
    """Response for listing executions."""

    executions: list[ExecutionStatus] = Field(
        default_factory=list, description="List of executions"
    )
    count: int = Field(..., ge=0, description="Total count")
    workflow_id: str | None = Field(None, description="Filter by workflow ID")


class WorkflowValidationError(BaseModel):
    """Validation error detail."""

    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")


class WorkflowValidationResponse(BaseModel):
    """Response for workflow validation."""

    valid: bool = Field(..., description="Whether workflow is valid")
    errors: list[WorkflowValidationError] = Field(
        default_factory=list, description="Validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Validation warnings"
    )


class WorkflowSuccessResponse(BaseModel):
    """Generic success response for workflow operations."""

    success: bool = Field(True, description="Operation success")
    message: str = Field(..., description="Success message")
    workflow_id: str | None = Field(None, description="Affected workflow ID")


class ProgressUpdate(BaseModel):
    """Progress update for SSE streaming."""

    event_type: Literal[
        "started", "step_started", "step_completed", "step_failed", "completed", "failed"
    ] = Field(..., description="Event type")
    execution_id: str = Field(..., description="Execution identifier")
    step_id: str | None = Field(None, description="Current step ID")
    step_name: str | None = Field(None, description="Current step name")
    progress: float = Field(0, ge=0, le=1, description="Overall progress")
    message: str = Field("", description="Status message")
    output: Any = Field(None, description="Step output (if completed)")
    error: str | None = Field(None, description="Error message (if failed)")
    timestamp: datetime = Field(..., description="Event timestamp")
