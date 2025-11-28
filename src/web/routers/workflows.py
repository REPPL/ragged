"""Workflow API router.

Provides endpoints for workflow operations:
- List and get workflow definitions
- Create and validate workflows
- Execute workflows with progress streaming
- Get execution status and results
- Cancel executions

v0.9.0: Initial implementation
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse

from ragged.agents.registry import ToolRegistry
from ragged.agents.workflows.definition import (
    WORKFLOW_TEMPLATES,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTrigger,
    validate_workflow,
)
from ragged.agents.workflows.executor import (
    WorkflowExecutor,
    WorkflowResult,
    WorkflowState,
)
from ragged.utils.logging import get_logger
from ragged.web.schemas.workflows import (
    CreateWorkflowRequest,
    ExecuteWorkflowRequest,
    ExecutionDetailResponse,
    ExecutionListResponse,
    ExecutionResponse,
    ExecutionStatus,
    ProgressUpdate,
    StepResultSchema,
    WorkflowDefinitionSchema,
    WorkflowListResponse,
    WorkflowStepSchema,
    WorkflowSuccessResponse,
    WorkflowSummary,
    WorkflowValidationError,
    WorkflowValidationResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# In-memory storage for custom workflows and executions
_custom_workflows: dict[str, WorkflowDefinition] = {}
_executions: dict[str, dict[str, Any]] = {}
_execution_results: dict[str, WorkflowResult] = {}

# Tool registry (lazy initialisation)
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry.

    Returns:
        ToolRegistry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        logger.info("Tool registry initialised")
    return _tool_registry


def _workflow_to_summary(
    workflow: WorkflowDefinition,
    is_template: bool = False,
) -> WorkflowSummary:
    """Convert workflow definition to summary.

    Args:
        workflow: Workflow definition
        is_template: Whether this is a built-in template

    Returns:
        WorkflowSummary
    """
    return WorkflowSummary(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        trigger=workflow.trigger.value,
        step_count=len(workflow.steps),
        is_template=is_template,
    )


def _workflow_to_schema(workflow: WorkflowDefinition) -> WorkflowDefinitionSchema:
    """Convert workflow definition to schema.

    Args:
        workflow: Workflow definition

    Returns:
        WorkflowDefinitionSchema
    """
    steps = [
        WorkflowStepSchema(
            id=s.id,
            name=s.name,
            tool=s.tool,
            arguments=s.arguments,
            depends_on=s.depends_on,
            condition=s.condition,
            on_failure=s.on_failure,  # type: ignore[arg-type]
            retries=s.retries,
            timeout_seconds=s.timeout_seconds,
        )
        for s in workflow.steps
    ]

    return WorkflowDefinitionSchema(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        trigger=workflow.trigger.value,  # type: ignore[arg-type]
        steps=steps,
        inputs=workflow.inputs,
        outputs=workflow.outputs,
        metadata=workflow.metadata,
    )


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    include_templates: bool = Query(True, description="Include built-in templates"),
) -> WorkflowListResponse:
    """List all available workflows.

    Args:
        include_templates: Whether to include built-in templates

    Returns:
        WorkflowListResponse with all workflows
    """
    workflows: list[WorkflowSummary] = []
    template_count = 0
    custom_count = 0

    # Add built-in templates
    if include_templates:
        for workflow in WORKFLOW_TEMPLATES.values():
            workflows.append(_workflow_to_summary(workflow, is_template=True))
            template_count += 1

    # Add custom workflows
    for workflow in _custom_workflows.values():
        workflows.append(_workflow_to_summary(workflow, is_template=False))
        custom_count += 1

    return WorkflowListResponse(
        workflows=workflows,
        count=len(workflows),
        templates=template_count,
        custom=custom_count,
    )


@router.get("/templates", response_model=WorkflowListResponse)
async def list_templates() -> WorkflowListResponse:
    """List built-in workflow templates.

    Returns:
        WorkflowListResponse with templates only
    """
    workflows = [
        _workflow_to_summary(wf, is_template=True)
        for wf in WORKFLOW_TEMPLATES.values()
    ]

    return WorkflowListResponse(
        workflows=workflows,
        count=len(workflows),
        templates=len(workflows),
        custom=0,
    )


# NOTE: Execution routes must come BEFORE /{workflow_id} to avoid path conflicts
@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: str | None = Query(None, description="Filter by workflow ID"),
    state: str | None = Query(None, description="Filter by state"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
) -> ExecutionListResponse:
    """List workflow executions.

    Args:
        workflow_id: Optional workflow ID filter
        state: Optional state filter
        limit: Maximum number of results

    Returns:
        ExecutionListResponse with executions
    """
    executions: list[ExecutionStatus] = []

    for exec_id, exec_data in _executions.items():
        # Apply filters
        if workflow_id and exec_data["workflow_id"] != workflow_id:
            continue
        if state and exec_data["state"] != state:
            continue

        executions.append(ExecutionStatus(
            execution_id=exec_id,
            workflow_id=exec_data["workflow_id"],
            state=exec_data["state"],  # type: ignore[arg-type]
            current_step=exec_data.get("current_step"),
            progress=exec_data.get("progress", 0),
            started_at=exec_data.get("started_at"),
            completed_at=exec_data.get("completed_at"),
        ))

        if len(executions) >= limit:
            break

    # Sort by start time (newest first)
    executions.sort(key=lambda x: x.started_at or datetime.min, reverse=True)

    return ExecutionListResponse(
        executions=executions[:limit],
        count=len(executions),
        workflow_id=workflow_id,
    )


@router.get("/executions/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(execution_id: str) -> ExecutionDetailResponse:
    """Get detailed execution information.

    Args:
        execution_id: Execution identifier

    Returns:
        ExecutionDetailResponse with full details

    Raises:
        HTTPException: If execution not found
    """
    if execution_id not in _executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )

    exec_data = _executions[execution_id]
    result = _execution_results.get(execution_id)

    step_results: list[StepResultSchema] = []
    outputs: dict[str, Any] = {}
    duration_ms = 0.0
    error: str | None = None

    if result:
        step_results = [
            StepResultSchema(
                step_id=r.step_id,
                success=r.success,
                output=r.output,
                error=r.error,
                duration_ms=r.duration_ms,
                retries_used=r.retries_used,
            )
            for r in result.step_results
        ]
        outputs = result.outputs
        duration_ms = result.duration_ms
        error = result.error

    return ExecutionDetailResponse(
        execution_id=execution_id,
        workflow_id=exec_data["workflow_id"],
        state=exec_data["state"],
        step_results=step_results,
        outputs=outputs,
        duration_ms=duration_ms,
        error=error or exec_data.get("error"),
        started_at=exec_data.get("started_at"),
        completed_at=exec_data.get("completed_at"),
    )


@router.post("/executions/{execution_id}/cancel", response_model=WorkflowSuccessResponse)
async def cancel_execution(execution_id: str) -> WorkflowSuccessResponse:
    """Cancel a running execution.

    Args:
        execution_id: Execution identifier

    Returns:
        WorkflowSuccessResponse on success

    Raises:
        HTTPException: If execution not found or already completed
    """
    if execution_id not in _executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )

    exec_data = _executions[execution_id]
    current_state = exec_data["state"]

    if current_state in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel execution in state: {current_state}"
        )

    # Update state to cancelled
    _executions[execution_id]["state"] = WorkflowState.CANCELLED.value
    _executions[execution_id]["completed_at"] = datetime.now(UTC)

    logger.info(f"Cancelled execution: {execution_id[:8]}")

    return WorkflowSuccessResponse(
        success=True,
        message=f"Execution '{execution_id[:8]}...' cancelled",
    )


@router.get("/{workflow_id}", response_model=WorkflowDefinitionSchema)
async def get_workflow(workflow_id: str) -> WorkflowDefinitionSchema:
    """Get workflow definition by ID.

    Args:
        workflow_id: Workflow identifier

    Returns:
        WorkflowDefinitionSchema

    Raises:
        HTTPException: If workflow not found
    """
    # Check templates first
    if workflow_id in WORKFLOW_TEMPLATES:
        return _workflow_to_schema(WORKFLOW_TEMPLATES[workflow_id])

    # Check custom workflows
    if workflow_id in _custom_workflows:
        return _workflow_to_schema(_custom_workflows[workflow_id])

    raise HTTPException(
        status_code=404,
        detail=f"Workflow not found: {workflow_id}"
    )


@router.post("", response_model=WorkflowSuccessResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
) -> WorkflowSuccessResponse:
    """Create a new custom workflow.

    Args:
        request: Workflow creation request

    Returns:
        WorkflowSuccessResponse on success

    Raises:
        HTTPException: If workflow ID already exists or validation fails
    """
    # Check for duplicate ID
    if request.id in WORKFLOW_TEMPLATES or request.id in _custom_workflows:
        raise HTTPException(
            status_code=409,
            detail=f"Workflow with ID '{request.id}' already exists"
        )

    # Convert to WorkflowDefinition
    steps = [
        WorkflowStep(
            id=s.id,
            name=s.name,
            tool=s.tool,
            arguments=s.arguments,
            depends_on=s.depends_on,
            condition=s.condition,
            on_failure=s.on_failure,
            retries=s.retries,
            timeout_seconds=s.timeout_seconds,
        )
        for s in request.steps
    ]

    workflow = WorkflowDefinition(
        id=request.id,
        name=request.name,
        description=request.description,
        trigger=WorkflowTrigger(request.trigger),
        steps=steps,
        inputs=request.inputs,
    )

    # Validate workflow
    errors = validate_workflow(workflow)
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow validation failed: {'; '.join(errors)}"
        )

    # Store workflow
    _custom_workflows[request.id] = workflow
    logger.info(f"Created custom workflow: {request.id}")

    return WorkflowSuccessResponse(
        success=True,
        message=f"Workflow '{request.name}' created successfully",
        workflow_id=request.id,
    )


@router.post("/validate", response_model=WorkflowValidationResponse)
async def validate_workflow_endpoint(
    request: CreateWorkflowRequest,
) -> WorkflowValidationResponse:
    """Validate a workflow definition without creating it.

    Args:
        request: Workflow to validate

    Returns:
        WorkflowValidationResponse with validation results
    """
    # Convert to WorkflowDefinition
    steps = [
        WorkflowStep(
            id=s.id,
            name=s.name,
            tool=s.tool,
            arguments=s.arguments,
            depends_on=s.depends_on,
            condition=s.condition,
            on_failure=s.on_failure,
            retries=s.retries,
            timeout_seconds=s.timeout_seconds,
        )
        for s in request.steps
    ]

    workflow = WorkflowDefinition(
        id=request.id,
        name=request.name,
        description=request.description,
        trigger=WorkflowTrigger(request.trigger),
        steps=steps,
        inputs=request.inputs,
    )

    # Get available tools for tool validation
    registry = get_tool_registry()
    available_tools = registry.list_tools()

    # Validate
    errors = validate_workflow(workflow, available_tools)

    validation_errors = [
        WorkflowValidationError(field="workflow", message=e)
        for e in errors
    ]

    # Check for warnings
    warnings: list[str] = []
    if not workflow.description:
        warnings.append("Workflow has no description")
    for step in steps:
        if step.retries > 5:
            warnings.append(f"Step '{step.id}' has high retry count ({step.retries})")
        if step.timeout_seconds > 300:
            warnings.append(f"Step '{step.id}' has long timeout ({step.timeout_seconds}s)")

    return WorkflowValidationResponse(
        valid=len(errors) == 0,
        errors=validation_errors,
        warnings=warnings,
    )


@router.delete("/{workflow_id}", response_model=WorkflowSuccessResponse)
async def delete_workflow(workflow_id: str) -> WorkflowSuccessResponse:
    """Delete a custom workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        WorkflowSuccessResponse on success

    Raises:
        HTTPException: If workflow not found or is a template
    """
    if workflow_id in WORKFLOW_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete built-in template workflows"
        )

    if workflow_id not in _custom_workflows:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}"
        )

    del _custom_workflows[workflow_id]
    logger.info(f"Deleted custom workflow: {workflow_id}")

    return WorkflowSuccessResponse(
        success=True,
        message=f"Workflow '{workflow_id}' deleted successfully",
        workflow_id=workflow_id,
    )


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks,
) -> ExecutionResponse:
    """Execute a workflow.

    Args:
        workflow_id: Workflow identifier
        request: Execution request with inputs
        background_tasks: FastAPI background tasks

    Returns:
        ExecutionResponse with execution ID

    Raises:
        HTTPException: If workflow not found
    """
    # Get workflow
    workflow: WorkflowDefinition | None = None
    if workflow_id in WORKFLOW_TEMPLATES:
        workflow = WORKFLOW_TEMPLATES[workflow_id]
    elif workflow_id in _custom_workflows:
        workflow = _custom_workflows[workflow_id]

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}"
        )

    # Generate execution ID
    execution_id = str(uuid.uuid4())

    # Create execution record
    _executions[execution_id] = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "state": WorkflowState.PENDING.value,
        "current_step": None,
        "progress": 0.0,
        "started_at": datetime.now(UTC),
        "completed_at": None,
        "inputs": request.inputs,
        "persona": request.persona,
    }

    if request.async_execution:
        # Execute in background
        background_tasks.add_task(
            _execute_workflow_async,
            execution_id,
            workflow,
            request.inputs,
        )

        return ExecutionResponse(
            execution_id=execution_id,
            workflow_id=workflow_id,
            state="pending",
            message=f"Workflow '{workflow.name}' execution started",
        )
    else:
        # Execute synchronously (blocking)
        await _execute_workflow_async(execution_id, workflow, request.inputs)

        result = _execution_results.get(execution_id)
        state = result.state.value if result else "unknown"

        return ExecutionResponse(
            execution_id=execution_id,
            workflow_id=workflow_id,
            state=state,
            message=f"Workflow '{workflow.name}' execution completed",
        )


async def _execute_workflow_async(
    execution_id: str,
    workflow: WorkflowDefinition,
    inputs: dict[str, Any],
) -> None:
    """Execute workflow asynchronously.

    Args:
        execution_id: Execution identifier
        workflow: Workflow to execute
        inputs: Input values
    """
    try:
        # Update state
        _executions[execution_id]["state"] = WorkflowState.RUNNING.value

        # Create executor
        registry = get_tool_registry()
        executor = WorkflowExecutor(registry)

        # Execute workflow
        result = await executor.execute(workflow, inputs=inputs)

        # Store result
        _execution_results[execution_id] = result

        # Update execution record
        _executions[execution_id]["state"] = result.state.value
        _executions[execution_id]["completed_at"] = datetime.now(UTC)
        _executions[execution_id]["progress"] = 1.0 if result.state == WorkflowState.COMPLETED else 0.0

        logger.info(f"Workflow execution {execution_id[:8]} completed: {result.state.value}")

    except Exception as e:
        logger.exception(f"Workflow execution failed: {e}")
        _executions[execution_id]["state"] = WorkflowState.FAILED.value
        _executions[execution_id]["error"] = str(e)
        _executions[execution_id]["completed_at"] = datetime.now(UTC)


@router.get("/{workflow_id}/execute/{execution_id}/stream")
async def stream_execution(
    workflow_id: str,
    execution_id: str,
) -> StreamingResponse:
    """Stream execution progress via Server-Sent Events.

    Args:
        workflow_id: Workflow identifier
        execution_id: Execution identifier

    Returns:
        SSE stream of progress updates

    Raises:
        HTTPException: If execution not found
    """
    if execution_id not in _executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )

    async def event_stream():
        """Generate SSE events for execution progress."""
        last_state = None
        last_step = None

        while True:
            execution = _executions.get(execution_id)
            if execution is None:
                yield "event: error\n"
                yield f"data: {json.dumps({'error': 'Execution not found'})}\n\n"
                break

            state = execution["state"]
            current_step = execution.get("current_step")

            # Emit progress update if state or step changed
            if state != last_state or current_step != last_step:
                update = ProgressUpdate(
                    event_type="step_started" if current_step and current_step != last_step else "started",
                    execution_id=execution_id,
                    step_id=current_step,
                    progress=execution.get("progress", 0),
                    message=f"Execution state: {state}",
                    timestamp=datetime.now(UTC),
                )

                yield f"event: progress\n"
                yield f"data: {update.model_dump_json()}\n\n"

                last_state = state
                last_step = current_step

            # Check if execution is complete
            if state in ("completed", "failed", "cancelled"):
                result = _execution_results.get(execution_id)

                final_update = ProgressUpdate(
                    event_type="completed" if state == "completed" else "failed",
                    execution_id=execution_id,
                    progress=1.0 if state == "completed" else execution.get("progress", 0),
                    message=f"Execution {state}",
                    error=result.error if result else execution.get("error"),
                    timestamp=datetime.now(UTC),
                )

                yield f"event: {state}\n"
                yield f"data: {final_update.model_dump_json()}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )
