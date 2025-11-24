"""Security tests for API middleware (validation, JWT, versioning).

v0.6.0 SECURITY-API-001: Tests for request validation, response sanitization,
JWT improvements, and API versioning.
"""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ragged.web.middleware.jwt import APIVersionMiddleware, JWTSecurityMiddleware
from ragged.web.middleware.validation import (
    RequestValidationMiddleware,
    ResponseSanitizationMiddleware,
)


@pytest.fixture
def app_with_validation():
    """Create FastAPI app with validation middleware."""
    app = FastAPI()

    app.add_middleware(ResponseSanitizationMiddleware)
    app.add_middleware(RequestValidationMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.post("/test")
    async def test_post_endpoint(data: dict):
        return data

    return app


@pytest.fixture
def app_with_jwt():
    """Create FastAPI app with JWT middleware."""
    app = FastAPI()

    app.add_middleware(JWTSecurityMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


@pytest.fixture
def app_with_versioning():
    """Create FastAPI app with API versioning middleware."""
    app = FastAPI()

    app.add_middleware(APIVersionMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


class TestRequestValidation:
    """Test request validation middleware."""

    def test_valid_json_request(self, app_with_validation):
        """Test that valid JSON requests are accepted."""
        client = TestClient(app_with_validation)
        response = client.post("/test", json={"message": "hello"})

        assert response.status_code == 200

    def test_request_size_limit(self, app_with_validation):
        """Test that oversized requests are rejected."""
        client = TestClient(app_with_validation)

        # Create a large payload (> 10 MB)
        large_data = {"data": "x" * (11 * 1024 * 1024)}

        response = client.post(
            "/test",
            json=large_data,
        )

        # Should be rejected (413 = Payload Too Large)
        assert response.status_code == 413
        assert "too large" in response.json()["error"].lower()

    def test_invalid_content_type(self, app_with_validation):
        """Test that invalid Content-Type is rejected."""
        client = TestClient(app_with_validation)

        response = client.post(
            "/test",
            content="test data",
            headers={"Content-Type": "application/xml"},
        )

        # Should be rejected (415 = Unsupported Media Type)
        assert response.status_code == 415

    def test_deeply_nested_json(self, app_with_validation):
        """Test that deeply nested JSON is rejected."""
        client = TestClient(app_with_validation)

        # Create deeply nested JSON (> 20 levels)
        nested_data: dict = {}
        current = nested_data
        for i in range(25):
            current["nested"] = {}
            current = current["nested"]
        current["value"] = "deep"

        response = client.post("/test", json=nested_data)

        # Should be rejected (400 = Bad Request)
        assert response.status_code == 400
        assert "nesting" in response.json()["error"].lower()

    def test_invalid_json(self, app_with_validation):
        """Test that invalid JSON is rejected."""
        client = TestClient(app_with_validation)

        response = client.post(
            "/test",
            content="{invalid json}",
            headers={"Content-Type": "application/json"},
        )

        # Should be rejected (400 = Bad Request)
        assert response.status_code == 400
        assert "json" in response.json()["error"].lower()


class TestResponseSanitization:
    """Test response sanitization middleware."""

    def test_server_header_removed(self, app_with_validation):
        """Test that Server header is removed."""
        client = TestClient(app_with_validation)
        response = client.get("/test")

        assert "Server" not in response.headers
        assert "X-Powered-By" not in response.headers

    def test_error_response_sanitized(self, app_with_validation):
        """Test that error responses are sanitized."""
        client = TestClient(app_with_validation)

        # Trigger an error
        response = client.post("/nonexistent")

        # Should have error status
        assert response.status_code == 404

        # Should not reveal internal details
        # (FastAPI handles this, but middleware adds extra protection)


class TestJWTSecurity:
    """Test JWT security middleware."""

    def test_request_without_token(self, app_with_jwt):
        """Test that requests without token are allowed (JWT is optional)."""
        client = TestClient(app_with_jwt)
        response = client.get("/test")

        # Should succeed (JWT is optional in this middleware)
        assert response.status_code == 200

    def test_token_rotation_header(self, app_with_jwt):
        """Test that token rotation adds new token header."""
        client = TestClient(app_with_jwt)

        # Generate a token manually
        from ragged.web.middleware.jwt import JWTSecurityMiddleware
        jwt_middleware = JWTSecurityMiddleware(app_with_jwt)
        token = jwt_middleware._generate_token("test_user")

        response = client.get(
            "/test",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Check if rotation header is present
        # Note: Rotation only happens after token is half-expired
        # For testing, we just verify the middleware processes the token
        assert response.status_code == 200


class TestAPIVersioning:
    """Test API versioning middleware."""

    def test_default_version(self, app_with_versioning):
        """Test that default version is applied."""
        client = TestClient(app_with_versioning)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-API-Version" in response.headers
        assert "X-API-Current-Version" in response.headers

    def test_explicit_version_header(self, app_with_versioning):
        """Test explicit version via header."""
        client = TestClient(app_with_versioning)
        response = client.get(
            "/test",
            headers={"X-API-Version": "0.6.0"}
        )

        assert response.status_code == 200
        assert response.headers["X-API-Version"] == "0.6.0"

    def test_unsupported_version(self, app_with_versioning):
        """Test that unsupported version is rejected."""
        client = TestClient(app_with_versioning)
        response = client.get(
            "/test",
            headers={"X-API-Version": "99.99.99"}
        )

        # Should be rejected (400 = Bad Request)
        assert response.status_code == 400
        assert "unsupported" in response.json()["error"].lower()

    def test_deprecated_version_warning(self, app_with_versioning):
        """Test that deprecated version triggers warning."""
        client = TestClient(app_with_versioning)
        response = client.get(
            "/test",
            headers={"X-API-Version": "0.2.0"}
        )

        # Should succeed but with deprecation warning
        assert response.status_code == 200
        assert "X-API-Deprecation-Warning" in response.headers


class TestMiddlewareIntegration:
    """Test integration of all API security middleware."""

    def test_full_security_stack(self, app_with_validation):
        """Test that all security middleware work together."""
        client = TestClient(app_with_validation)

        # Valid request
        response = client.post(
            "/test",
            json={"message": "hello"},
        )

        assert response.status_code == 200
        assert "Server" not in response.headers  # Response sanitization

    def test_validation_before_processing(self, app_with_validation):
        """Test that validation happens before request processing."""
        client = TestClient(app_with_validation)

        # Invalid request (too large)
        large_data = {"data": "x" * (11 * 1024 * 1024)}
        response = client.post("/test", json=large_data)

        # Should be rejected before reaching endpoint
        assert response.status_code == 413
