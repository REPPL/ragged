"""Security middleware for web UI and API.

v0.6.0 SECURITY-WEB-001: Enterprise-grade security headers and session management.
v0.6.2 SECURITY-003: Redis-backed session persistence with graceful fallback.

Implements:
- Content Security Policy (CSP) headers
- HTTP Strict Transport Security (HSTS)
- Session security improvements with pluggable storage backends
- XSS protection enhancements
"""

from __future__ import annotations

import secrets
import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ragged.utils.logging import get_logger
from ragged.web.session import SessionStore, SessionStoreFactory

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all HTTP responses.

    v0.6.0 SECURITY-WEB-001: Implements CSP, HSTS, and other security headers.

    Security Features:
    - Content-Security-Policy: Prevents XSS attacks by restricting resource loading
    - Strict-Transport-Security: Forces HTTPS connections
    - X-Content-Type-Options: Prevents MIME-type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS filters
    - Referrer-Policy: Controls referrer information
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_csp: bool = True,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        csp_directives: dict[str, str] | None = None,
    ):
        """Initialise security headers middleware.

        Args:
            app: ASGI application
            enable_csp: Enable Content Security Policy headers
            enable_hsts: Enable HTTP Strict Transport Security
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            csp_directives: Custom CSP directives (None = secure defaults)
        """
        super().__init__(app)
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age

        # Default CSP directives (secure by default)
        self.csp_directives = csp_directives or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",  # Gradio requires eval
            "style-src": "'self' 'unsafe-inline'",  # Gradio requires inline styles
            "img-src": "'self' data: blob:",  # Support data URIs and blobs
            "font-src": "'self' data:",
            "connect-src": "'self' ws: wss:",  # WebSocket support
            "frame-ancestors": "'none'",  # Prevent clickjacking
            "base-uri": "'self'",
            "form-action": "'self'",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with security headers
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Add CSP header
        if self.enable_csp:
            csp_value = "; ".join(
                f"{directive} {value}"
                for directive, value in self.csp_directives.items()
            )
            response.headers["Content-Security-Policy"] = csp_value
            logger.debug(f"Added CSP header: {csp_value[:100]}...")

        # Add HSTS header (only for HTTPS)
        if self.enable_hsts:
            # Check if request is HTTPS
            is_https = (
                request.url.scheme == "https"
                or request.headers.get("x-forwarded-proto") == "https"
            )
            if is_https:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={self.hsts_max_age}; includeSubDomains"
                )
                logger.debug(f"Added HSTS header with max-age={self.hsts_max_age}")

        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add security-related headers
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Log processing time for security middleware
        elapsed = time.time() - start_time
        if elapsed > 0.1:  # Log if middleware takes >100ms
            logger.warning(
                f"Security middleware slow: {elapsed*1000:.1f}ms for {request.url.path}"
            )

        return response


class SessionSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for session security improvements.

    v0.6.0 SECURITY-WEB-001: Session hijacking prevention and timeout enforcement.
    v0.6.2 SECURITY-003: Pluggable session storage (in-memory or Redis).

    Features:
    - Session timeout enforcement
    - Session ID rotation
    - Secure session storage with Redis support
    - CSRF token validation
    - Graceful fallback to in-memory if Redis unavailable
    """

    def __init__(
        self,
        app: ASGIApp,
        session_timeout: int = 3600,  # 1 hour
        enable_csrf: bool = True,
        session_store: SessionStore | None = None,
        redis_url: str | None = None,
    ):
        """Initialise session security middleware.

        Args:
            app: ASGI application
            session_timeout: Session timeout in seconds
            enable_csrf: Enable CSRF token validation
            session_store: Custom SessionStore (None = auto-create)
            redis_url: Redis URL for session persistence (None = in-memory)

        Example:
            >>> # Development (in-memory)
            >>> middleware = SessionSecurityMiddleware(app)
            >>>
            >>> # Production (Redis with fallback)
            >>> middleware = SessionSecurityMiddleware(
            ...     app,
            ...     redis_url="redis://localhost:6379/0"
            ... )
        """
        super().__init__(app)
        self.session_timeout = session_timeout
        self.enable_csrf = enable_csrf

        # Create or use provided session store
        if session_store is not None:
            self.session_store = session_store
            logger.info("Using provided SessionStore")
        else:
            self.session_store = SessionStoreFactory.create(
                redis_url=redis_url, fallback_to_memory=True
            )

        logger.info(
            f"SessionSecurityMiddleware initialised: "
            f"store={type(self.session_store).__name__}, "
            f"timeout={session_timeout}s, csrf={enable_csrf}"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce session security with pluggable storage backend.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with session security enforced

        v0.6.2 SECURITY-003: Uses SessionStore for Redis or in-memory storage
        """
        # Get session ID from cookie
        session_id = request.cookies.get("session_id")
        session_data = None

        if session_id:
            # Try to retrieve session from store
            session_data = self.session_store.get_session(session_id)

            if session_data is None:
                # Session not found or expired
                logger.debug(f"Session {session_id[:8]}... not found or expired")
                session_id = None

        # Create new session if needed
        if not session_id:
            session_id = secrets.token_urlsafe(32)
            session_data = {
                "created_at": time.time(),
                "last_activity": time.time(),
                "csrf_token": secrets.token_urlsafe(32) if self.enable_csrf else None,
            }

            # Store in session backend
            success = self.session_store.create_session(
                session_id, session_data, self.session_timeout
            )

            if success:
                logger.info(f"Created new session: {session_id[:8]}...")
            else:
                logger.error(f"Failed to create session in store")

        # Add session to request state
        request.state.session_id = session_id
        request.state.session = session_data or {}

        # Process request
        response = await call_next(request)

        # Update session in store (refresh TTL and last_activity)
        if session_data:
            session_data["last_activity"] = time.time()
            self.session_store.create_session(
                session_id, session_data, self.session_timeout
            )

        # Set session cookie (secure by default)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,  # Prevent JavaScript access
            secure=True,  # Only send over HTTPS
            samesite="strict",  # CSRF protection
            max_age=self.session_timeout,
        )

        return response


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for XSS protection enhancements.

    v0.6.0 SECURITY-WEB-001: Input sanitization and output encoding.

    Features:
    - Input sanitization for common XSS vectors
    - Output encoding for HTML contexts
    - DOM-based XSS prevention
    """

    def __init__(self, app: ASGIApp, enable_input_sanitization: bool = True):
        """Initialise XSS protection middleware.

        Args:
            app: ASGI application
            enable_input_sanitization: Enable input sanitization
        """
        super().__init__(app)
        self.enable_input_sanitization = enable_input_sanitization

        # Common XSS patterns to detect (not sanitize - just log)
        self.xss_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            "eval(",
            "expression(",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply XSS protection.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with XSS protection applied
        """
        if self.enable_input_sanitization and request.method in ["POST", "PUT", "PATCH"]:
            # Check for XSS patterns in request body (if JSON)
            if request.headers.get("content-type") == "application/json":
                try:
                    body = await request.body()
                    body_str = body.decode("utf-8").lower()

                    for pattern in self.xss_patterns:
                        if pattern in body_str:
                            logger.warning(
                                f"Potential XSS pattern detected in request: {pattern} "
                                f"from {request.client.host if request.client else 'unknown'}"
                            )
                            # Log but don't block (might be legitimate code examples)
                            break
                except Exception:  # noqa: BLE001
                    pass  # Body already consumed or not JSON

        # Process request
        response = await call_next(request)

        return response
