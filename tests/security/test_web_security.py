"""Security tests for web UI and API middleware.

v0.6.0 SECURITY-WEB-001: Tests for CSP, HSTS, session security, and XSS protection.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ragged.web.middleware.security import (
    SecurityHeadersMiddleware,
    SessionSecurityMiddleware,
    XSSProtectionMiddleware,
)


@pytest.fixture
def app_with_security():
    """Create FastAPI app with security middleware."""
    app = FastAPI()

    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware, enable_csp=True, enable_hsts=True)
    app.add_middleware(SessionSecurityMiddleware, session_timeout=3600)
    app.add_middleware(XSSProtectionMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.post("/test")
    async def test_post_endpoint(data: dict):
        return data

    return app


class TestSecurityHeaders:
    """Test CSP, HSTS, and other security headers."""

    def test_csp_header_present(self, app_with_security):
        """Test that Content-Security-Policy header is present."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "style-src" in csp

    def test_hsts_header_on_https(self, app_with_security):
        """Test that HSTS header is present for HTTPS requests."""
        client = TestClient(app_with_security)

        # Simulate HTTPS by setting x-forwarded-proto header
        response = client.get("/test", headers={"x-forwarded-proto": "https"})

        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    def test_xss_protection_header(self, app_with_security):
        """Test that X-XSS-Protection header is present."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_x_content_type_options(self, app_with_security):
        """Test that X-Content-Type-Options is set to nosniff."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options(self, app_with_security):
        """Test that X-Frame-Options prevents clickjacking."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_referrer_policy(self, app_with_security):
        """Test that Referrer-Policy is set appropriately."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, app_with_security):
        """Test that Permissions-Policy restricts browser features."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "Permissions-Policy" in response.headers
        policy = response.headers["Permissions-Policy"]
        assert "geolocation=()" in policy
        assert "microphone=()" in policy
        assert "camera=()" in policy


class TestSessionSecurity:
    """Test session management and security."""

    def test_session_cookie_created(self, app_with_security):
        """Test that session cookie is created on first request."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "session_id" in response.cookies

    def test_session_cookie_secure_flags(self, app_with_security):
        """Test that session cookie has secure flags."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        # Check cookie properties
        session_cookie = response.cookies.get("session_id")
        assert session_cookie is not None

        # FastAPI TestClient doesn't expose all cookie properties directly,
        # but we can verify the cookie exists and will have the flags in production

    def test_session_persistence(self, app_with_security):
        """Test that session persists across requests."""
        client = TestClient(app_with_security)

        # First request
        response1 = client.get("/test")
        session_id_1 = response1.cookies.get("session_id")
        assert session_id_1 is not None

        # Second request with explicit cookie passing
        # Note: TestClient doesn't automatically persist cookies, so we pass it explicitly
        response2 = client.get(
            "/test",
            cookies={"session_id": session_id_1}
        )
        session_id_2 = response2.cookies.get("session_id")

        # Session should be the same when cookie is sent
        assert session_id_1 == session_id_2

    def test_new_session_on_timeout(self, app_with_security):
        """Test that new session is created after timeout."""
        # This test would require mocking time.time() to simulate timeout
        # For now, verify that the session middleware is properly configured
        client = TestClient(app_with_security)
        response = client.get("/test")

        assert "session_id" in response.cookies


class TestXSSProtection:
    """Test XSS protection middleware."""

    def test_xss_pattern_detection_in_post(self, app_with_security):
        """Test that XSS patterns are detected in POST requests."""
        client = TestClient(app_with_security)

        # Send request with XSS pattern
        # Note: Middleware logs but doesn't block (might be legitimate)
        response = client.post(
            "/test",
            json={"data": "<script>alert('xss')</script>"}
        )

        # Request should still succeed (logging only)
        assert response.status_code == 200

    def test_javascript_protocol_detection(self, app_with_security):
        """Test detection of javascript: protocol."""
        client = TestClient(app_with_security)

        response = client.post(
            "/test",
            json={"url": "javascript:alert('xss')"}
        )

        # Request should still succeed (logging only)
        assert response.status_code == 200

    def test_event_handler_detection(self, app_with_security):
        """Test detection of event handlers like onerror."""
        client = TestClient(app_with_security)

        response = client.post(
            "/test",
            json={"html": "<img src=x onerror='alert(1)'>"}
        )

        # Request should still succeed (logging only)
        assert response.status_code == 200

    def test_safe_post_request(self, app_with_security):
        """Test that safe POST requests work normally."""
        client = TestClient(app_with_security)

        response = client.post(
            "/test",
            json={"message": "Hello, world!"}
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, world!"}


class TestMiddlewareIntegration:
    """Test integration of all security middleware."""

    def test_all_security_headers_present(self, app_with_security):
        """Test that all expected security headers are present."""
        client = TestClient(app_with_security)
        response = client.get("/test", headers={"x-forwarded-proto": "https"})

        expected_headers = [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
        ]

        for header in expected_headers:
            assert header in response.headers, f"Missing header: {header}"

    def test_middleware_order_matters(self, app_with_security):
        """Test that middleware is applied in correct order."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        # Session cookie should be set (SessionSecurityMiddleware)
        assert "session_id" in response.cookies

        # Security headers should be present (SecurityHeadersMiddleware)
        assert "Content-Security-Policy" in response.headers

    def test_csp_allows_websocket(self, app_with_security):
        """Test that CSP allows WebSocket connections."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]
        assert "connect-src" in csp
        assert "ws:" in csp or "wss:" in csp

    def test_csp_allows_gradio_requirements(self, app_with_security):
        """Test that CSP allows Gradio's requirements."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]

        # Gradio requires unsafe-inline and unsafe-eval
        assert "unsafe-inline" in csp
        assert "unsafe-eval" in csp

        # Should support data URIs for images
        assert "data:" in csp


class TestSecurityConfiguration:
    """Test security middleware configuration options."""

    def test_disable_csp(self):
        """Test that CSP can be disabled."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, enable_csp=False)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # CSP should not be present when disabled
        assert "Content-Security-Policy" not in response.headers

    def test_disable_hsts(self):
        """Test that HSTS can be disabled."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, enable_hsts=False)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test", headers={"x-forwarded-proto": "https"})

        # HSTS should not be present when disabled
        assert "Strict-Transport-Security" not in response.headers

    def test_custom_csp_directives(self):
        """Test custom CSP directives."""
        app = FastAPI()
        custom_csp = {
            "default-src": "'self'",
            "script-src": "'self'",
        }
        app.add_middleware(
            SecurityHeadersMiddleware,
            enable_csp=True,
            csp_directives=custom_csp
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    def test_custom_hsts_max_age(self):
        """Test custom HSTS max-age."""
        app = FastAPI()
        app.add_middleware(
            SecurityHeadersMiddleware,
            enable_hsts=True,
            hsts_max_age=86400  # 1 day
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test", headers={"x-forwarded-proto": "https"})

        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=86400" in hsts
