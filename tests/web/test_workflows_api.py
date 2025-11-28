"""Tests for Workflow API endpoints.

v0.9.0: Initial implementation
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    # Clear any existing state before each test
    import ragged.web.routers.workflows as workflows_module
    workflows_module._custom_workflows.clear()
    workflows_module._executions.clear()
    workflows_module._execution_results.clear()

    from ragged.web.api import app
    return TestClient(app)


@pytest.fixture
def sample_workflow_request() -> dict[str, Any]:
    """Create a sample workflow creation request."""
    return {
        "id": "test_workflow",
        "name": "Test Workflow",
        "description": "A test workflow for unit testing",
        "trigger": "manual",
        "steps": [
            {
                "id": "step_1",
                "name": "First Step",
                "tool": "search",
                "arguments": {"query": "{{input.query}}"},
            },
            {
                "id": "step_2",
                "name": "Second Step",
                "tool": "query",
                "arguments": {"question": "Summarise: {{step.step_1}}"},
                "depends_on": ["step_1"],
            },
        ],
        "inputs": {
            "query": {
                "type": "string",
                "description": "Search query",
                "required": True,
            }
        },
    }


class TestListWorkflows:
    """Tests for GET /api/workflows endpoint."""

    def test_list_workflows_includes_templates(self, client: TestClient) -> None:
        """Test that listing workflows includes built-in templates."""
        response = client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()

        assert "workflows" in data
        assert "count" in data
        assert "templates" in data
        assert "custom" in data
        assert data["templates"] > 0  # Should have built-in templates

    def test_list_workflows_without_templates(self, client: TestClient) -> None:
        """Test listing workflows excluding templates."""
        response = client.get("/api/workflows?include_templates=false")

        assert response.status_code == 200
        data = response.json()

        assert data["templates"] == 0

    def test_list_workflows_includes_custom(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test that listing includes custom workflows."""
        # Create a custom workflow
        client.post("/api/workflows", json=sample_workflow_request)

        response = client.get("/api/workflows")
        data = response.json()

        assert data["custom"] >= 1
        workflow_ids = [w["id"] for w in data["workflows"]]
        assert "test_workflow" in workflow_ids

    def test_workflow_summary_structure(self, client: TestClient) -> None:
        """Test that workflow summaries have correct structure."""
        response = client.get("/api/workflows")
        data = response.json()

        if data["workflows"]:
            workflow = data["workflows"][0]
            assert "id" in workflow
            assert "name" in workflow
            assert "description" in workflow
            assert "version" in workflow
            assert "trigger" in workflow
            assert "step_count" in workflow
            assert "is_template" in workflow


class TestListTemplates:
    """Tests for GET /api/workflows/templates endpoint."""

    def test_list_templates(self, client: TestClient) -> None:
        """Test listing built-in templates."""
        response = client.get("/api/workflows/templates")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] > 0
        assert data["custom"] == 0
        for workflow in data["workflows"]:
            assert workflow["is_template"] is True


class TestGetWorkflow:
    """Tests for GET /api/workflows/{workflow_id} endpoint."""

    def test_get_template_workflow(self, client: TestClient) -> None:
        """Test getting a built-in template workflow."""
        response = client.get("/api/workflows/search_and_summarise")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "search_and_summarise"
        assert data["name"] == "Search and Summarise"
        assert "steps" in data
        assert len(data["steps"]) > 0

    def test_get_custom_workflow(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test getting a custom workflow."""
        # Create workflow first
        client.post("/api/workflows", json=sample_workflow_request)

        response = client.get("/api/workflows/test_workflow")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_workflow"
        assert data["name"] == "Test Workflow"

    def test_get_workflow_not_found(self, client: TestClient) -> None:
        """Test getting non-existent workflow."""
        response = client.get("/api/workflows/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_workflow_step_structure(self, client: TestClient) -> None:
        """Test that workflow steps have correct structure."""
        response = client.get("/api/workflows/search_and_summarise")
        data = response.json()

        step = data["steps"][0]
        assert "id" in step
        assert "name" in step
        assert "tool" in step
        assert "arguments" in step
        assert "depends_on" in step
        assert "on_failure" in step
        assert "retries" in step
        assert "timeout_seconds" in step


class TestCreateWorkflow:
    """Tests for POST /api/workflows endpoint."""

    def test_create_workflow_success(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test successfully creating a workflow."""
        response = client.post("/api/workflows", json=sample_workflow_request)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["workflow_id"] == "test_workflow"
        assert "created successfully" in data["message"]

    def test_create_workflow_duplicate_id(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test creating workflow with duplicate ID."""
        # Create first
        client.post("/api/workflows", json=sample_workflow_request)

        # Try to create again
        response = client.post("/api/workflows", json=sample_workflow_request)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_workflow_template_id_conflict(
        self,
        client: TestClient,
    ) -> None:
        """Test creating workflow with template ID."""
        request = {
            "id": "search_and_summarise",  # Conflicts with template
            "name": "My Search",
            "steps": [
                {"id": "s1", "name": "Step 1", "tool": "search"},
            ],
        }

        response = client.post("/api/workflows", json=request)

        assert response.status_code == 409

    def test_create_workflow_validation_error(self, client: TestClient) -> None:
        """Test creating workflow with validation errors."""
        request = {
            "id": "invalid_workflow",
            "name": "Invalid Workflow",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Step 1",
                    "tool": "search",
                    "depends_on": ["nonexistent"],  # Invalid dependency
                },
            ],
        }

        response = client.post("/api/workflows", json=request)

        assert response.status_code == 400
        assert "validation failed" in response.json()["detail"].lower()

    def test_create_workflow_empty_steps(self, client: TestClient) -> None:
        """Test creating workflow with no steps."""
        request = {
            "id": "empty_workflow",
            "name": "Empty Workflow",
            "steps": [],
        }

        response = client.post("/api/workflows", json=request)

        assert response.status_code == 422  # Pydantic validation


class TestValidateWorkflow:
    """Tests for POST /api/workflows/validate endpoint."""

    def test_validate_valid_workflow(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test validating a valid workflow."""
        response = client.post("/api/workflows/validate", json=sample_workflow_request)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert len(data["errors"]) == 0

    def test_validate_invalid_workflow(self, client: TestClient) -> None:
        """Test validating an invalid workflow."""
        request = {
            "id": "invalid",
            "name": "Invalid",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Step 1",
                    "tool": "search",
                    "depends_on": ["step_2"],  # Forward reference
                },
                {
                    "id": "step_2",
                    "name": "Step 2",
                    "tool": "query",
                    "depends_on": ["step_1"],  # Circular dependency
                },
            ],
        }

        response = client.post("/api/workflows/validate", json=request)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_includes_warnings(self, client: TestClient) -> None:
        """Test that validation includes warnings."""
        request = {
            "id": "warning_workflow",
            "name": "Warning Workflow",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Step 1",
                    "tool": "search",
                    "retries": 10,  # High retry count
                    "timeout_seconds": 600,  # Long timeout
                },
            ],
        }

        response = client.post("/api/workflows/validate", json=request)
        data = response.json()

        assert len(data["warnings"]) > 0


class TestDeleteWorkflow:
    """Tests for DELETE /api/workflows/{workflow_id} endpoint."""

    def test_delete_custom_workflow(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test deleting a custom workflow."""
        # Create first
        client.post("/api/workflows", json=sample_workflow_request)

        response = client.delete("/api/workflows/test_workflow")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deletion
        get_response = client.get("/api/workflows/test_workflow")
        assert get_response.status_code == 404

    def test_delete_template_workflow(self, client: TestClient) -> None:
        """Test that templates cannot be deleted."""
        response = client.delete("/api/workflows/search_and_summarise")

        assert response.status_code == 400
        assert "cannot delete" in response.json()["detail"].lower()

    def test_delete_nonexistent_workflow(self, client: TestClient) -> None:
        """Test deleting non-existent workflow."""
        response = client.delete("/api/workflows/nonexistent")

        assert response.status_code == 404


class TestExecuteWorkflow:
    """Tests for POST /api/workflows/{workflow_id}/execute endpoint."""

    def test_execute_workflow_async(self, client: TestClient) -> None:
        """Test executing workflow asynchronously."""
        response = client.post(
            "/api/workflows/search_and_summarise/execute",
            json={
                "inputs": {"query": "test query"},
                "async_execution": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "execution_id" in data
        assert data["workflow_id"] == "search_and_summarise"
        assert data["state"] == "pending"

    def test_execute_workflow_not_found(self, client: TestClient) -> None:
        """Test executing non-existent workflow."""
        response = client.post(
            "/api/workflows/nonexistent/execute",
            json={"inputs": {}},
        )

        assert response.status_code == 404

    def test_execute_with_inputs(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test executing workflow with inputs."""
        # Create workflow
        client.post("/api/workflows", json=sample_workflow_request)

        response = client.post(
            "/api/workflows/test_workflow/execute",
            json={
                "inputs": {"query": "test query"},
                "persona": "researcher",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data


class TestListExecutions:
    """Tests for GET /api/workflows/executions endpoint."""

    def test_list_executions_empty(self, client: TestClient) -> None:
        """Test listing executions when empty."""
        response = client.get("/api/workflows/executions")

        assert response.status_code == 200
        data = response.json()

        assert "executions" in data
        assert "count" in data

    def test_list_executions_after_execute(self, client: TestClient) -> None:
        """Test listing executions after executing workflow."""
        # Execute a workflow
        client.post(
            "/api/workflows/search_and_summarise/execute",
            json={"inputs": {"query": "test"}},
        )

        response = client.get("/api/workflows/executions")
        data = response.json()

        assert data["count"] >= 1

    def test_list_executions_filter_by_workflow(self, client: TestClient) -> None:
        """Test filtering executions by workflow ID."""
        # Execute workflow
        client.post(
            "/api/workflows/search_and_summarise/execute",
            json={"inputs": {"query": "test"}},
        )

        response = client.get("/api/workflows/executions?workflow_id=search_and_summarise")
        data = response.json()

        assert data["workflow_id"] == "search_and_summarise"
        for execution in data["executions"]:
            assert execution["workflow_id"] == "search_and_summarise"

    def test_list_executions_filter_by_state(self, client: TestClient) -> None:
        """Test filtering executions by state."""
        # Execute workflow
        client.post(
            "/api/workflows/search_and_summarise/execute",
            json={"inputs": {"query": "test"}},
        )

        response = client.get("/api/workflows/executions?state=pending")

        assert response.status_code == 200

    def test_list_executions_with_limit(self, client: TestClient) -> None:
        """Test limiting execution results."""
        # Execute multiple workflows
        for i in range(3):
            client.post(
                "/api/workflows/search_and_summarise/execute",
                json={"inputs": {"query": f"test {i}"}},
            )

        response = client.get("/api/workflows/executions?limit=2")
        data = response.json()

        assert len(data["executions"]) <= 2


class TestGetExecution:
    """Tests for GET /api/workflows/executions/{execution_id} endpoint."""

    def test_get_execution_details(self, client: TestClient) -> None:
        """Test getting execution details."""
        # Execute workflow
        exec_response = client.post(
            "/api/workflows/search_and_summarise/execute",
            json={"inputs": {"query": "test"}},
        )
        execution_id = exec_response.json()["execution_id"]

        response = client.get(f"/api/workflows/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["execution_id"] == execution_id
        assert data["workflow_id"] == "search_and_summarise"
        assert "state" in data
        assert "step_results" in data
        assert "outputs" in data

    def test_get_execution_not_found(self, client: TestClient) -> None:
        """Test getting non-existent execution."""
        response = client.get("/api/workflows/executions/nonexistent-id")

        assert response.status_code == 404


class TestCancelExecution:
    """Tests for POST /api/workflows/executions/{execution_id}/cancel endpoint."""

    def test_cancel_pending_execution(self, client: TestClient) -> None:
        """Test cancelling a pending execution.

        Note: Due to async execution, the state may have changed by the time
        cancel is called. We accept both successful cancellation (200) or
        400 if already in a terminal state.
        """
        # Execute workflow
        exec_response = client.post(
            "/api/workflows/search_and_summarise/execute",
            json={"inputs": {"query": "test"}},
        )
        execution_id = exec_response.json()["execution_id"]

        response = client.post(f"/api/workflows/executions/{execution_id}/cancel")

        # Either successfully cancelled, or already in a terminal state
        assert response.status_code in (200, 400)

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

            # Verify state
            detail_response = client.get(f"/api/workflows/executions/{execution_id}")
            assert detail_response.json()["state"] == "cancelled"
        else:
            # Already in terminal state - that's acceptable
            assert "Cannot cancel" in response.json()["detail"]

    def test_cancel_nonexistent_execution(self, client: TestClient) -> None:
        """Test cancelling non-existent execution."""
        response = client.post("/api/workflows/executions/nonexistent/cancel")

        assert response.status_code == 404


class TestWorkflowAPIOpenAPI:
    """Tests for Workflow API OpenAPI documentation."""

    def test_openapi_includes_workflow_endpoints(self, client: TestClient) -> None:
        """Test that OpenAPI schema includes workflow endpoints."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        paths = schema["paths"]
        assert "/api/workflows" in paths
        assert "/api/workflows/templates" in paths
        assert "/api/workflows/validate" in paths
        assert "/api/workflows/{workflow_id}" in paths
        assert "/api/workflows/executions" in paths

    def test_openapi_has_workflows_tag(self, client: TestClient) -> None:
        """Test that workflow endpoints are tagged correctly."""
        response = client.get("/openapi.json")
        schema = response.json()

        workflows_path = schema["paths"]["/api/workflows"]["get"]
        assert "workflows" in workflows_path["tags"]


class TestWorkflowAPIErrorHandling:
    """Tests for Workflow API error handling."""

    def test_invalid_trigger_type(self, client: TestClient) -> None:
        """Test validation for invalid trigger type."""
        request = {
            "id": "test",
            "name": "Test",
            "trigger": "invalid_trigger",
            "steps": [
                {"id": "s1", "name": "Step 1", "tool": "search"},
            ],
        }

        response = client.post("/api/workflows", json=request)

        assert response.status_code == 422

    def test_invalid_on_failure_action(self, client: TestClient) -> None:
        """Test validation for invalid on_failure action."""
        request = {
            "id": "test",
            "name": "Test",
            "steps": [
                {
                    "id": "s1",
                    "name": "Step 1",
                    "tool": "search",
                    "on_failure": "invalid",
                },
            ],
        }

        response = client.post("/api/workflows", json=request)

        assert response.status_code == 422

    def test_negative_retries(self, client: TestClient) -> None:
        """Test validation for negative retries."""
        request = {
            "id": "test",
            "name": "Test",
            "steps": [
                {
                    "id": "s1",
                    "name": "Step 1",
                    "tool": "search",
                    "retries": -1,
                },
            ],
        }

        response = client.post("/api/workflows", json=request)

        assert response.status_code == 422


class TestWorkflowAPIIntegration:
    """Integration tests for Workflow API."""

    def test_full_workflow_lifecycle(
        self,
        client: TestClient,
        sample_workflow_request: dict[str, Any],
    ) -> None:
        """Test complete workflow lifecycle: create, validate, execute, get, delete."""
        # 1. Validate workflow
        validate_response = client.post(
            "/api/workflows/validate",
            json=sample_workflow_request,
        )
        assert validate_response.json()["valid"] is True

        # 2. Create workflow
        create_response = client.post("/api/workflows", json=sample_workflow_request)
        assert create_response.status_code == 200

        # 3. Get workflow
        get_response = client.get("/api/workflows/test_workflow")
        assert get_response.status_code == 200

        # 4. Execute workflow
        exec_response = client.post(
            "/api/workflows/test_workflow/execute",
            json={"inputs": {"query": "integration test"}},
        )
        assert exec_response.status_code == 200
        execution_id = exec_response.json()["execution_id"]

        # 5. Get execution
        detail_response = client.get(f"/api/workflows/executions/{execution_id}")
        assert detail_response.status_code == 200

        # 6. List executions
        list_response = client.get("/api/workflows/executions")
        assert list_response.json()["count"] >= 1

        # 7. Delete workflow
        delete_response = client.delete("/api/workflows/test_workflow")
        assert delete_response.status_code == 200

        # 8. Verify deleted
        verify_response = client.get("/api/workflows/test_workflow")
        assert verify_response.status_code == 404

    def test_multiple_workflows(self, client: TestClient) -> None:
        """Test creating and managing multiple workflows."""
        workflows = [
            {
                "id": f"workflow_{i}",
                "name": f"Workflow {i}",
                "steps": [{"id": "s1", "name": "Step", "tool": "search"}],
            }
            for i in range(3)
        ]

        # Create all
        for wf in workflows:
            response = client.post("/api/workflows", json=wf)
            assert response.status_code == 200

        # List and verify count
        list_response = client.get("/api/workflows")
        data = list_response.json()
        assert data["custom"] >= 3

        # Delete all
        for wf in workflows:
            client.delete(f"/api/workflows/{wf['id']}")

        # Verify deleted
        final_response = client.get("/api/workflows?include_templates=false")
        assert final_response.json()["custom"] == 0
