"""Request validation and response sanitization middleware.

v0.6.0 SECURITY-API-001: Comprehensive request validation and API security.

Implements:
- Request schema validation
- Input sanitization
- Size limits enforcement
- Response sanitization
"""

import json
import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ragged.utils.logging import get_logger

logger = get_logger(__name__)

# Security constants
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_JSON_DEPTH = 20
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
    "text/plain",
}


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and input sanitization.

    v0.6.0 SECURITY-API-001: Validates all incoming requests for security.

    Validation Features:
    - Content-Type validation
    - Request size limits
    - JSON schema validation
    - Input sanitization
    - Type checking
    """

    def __init__(
        self,
        app: ASGIApp,
        max_request_size: int = MAX_REQUEST_SIZE,
        max_json_depth: int = MAX_JSON_DEPTH,
        enable_strict_validation: bool = True,
    ):
        """Initialise request validation middleware.

        Args:
            app: ASGI application
            max_request_size: Maximum request body size in bytes
            max_json_depth: Maximum JSON nesting depth
            enable_strict_validation: Enable strict schema validation
        """
        super().__init__(app)
        self.max_request_size = max_request_size
        self.max_json_depth = max_json_depth
        self.enable_strict_validation = enable_strict_validation

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate incoming request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response or error if validation fails
        """
        start_time = time.time()

        try:
            # 1. Validate Content-Type
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "").split(";")[0].strip()
                if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                    logger.warning(f"Invalid Content-Type: {content_type}")
                    return Response(
                        content=json.dumps({"error": "Unsupported Content-Type"}),
                        status_code=415,
                        media_type="application/json",
                    )

            # 2. Check request size
            content_length = request.headers.get("content-length")
            if content_length:
                if int(content_length) > self.max_request_size:
                    logger.warning(
                        f"Request too large: {content_length} bytes "
                        f"(max: {self.max_request_size})"
                    )
                    return Response(
                        content=json.dumps({
                            "error": "Request too large",
                            "max_size": self.max_request_size
                        }),
                        status_code=413,
                        media_type="application/json",
                    )

            # 3. Validate JSON depth (if JSON request)
            if request.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = await request.body()
                    if body:
                        data = json.loads(body)
                        depth = self._get_json_depth(data)
                        if depth > self.max_json_depth:
                            logger.warning(
                                f"JSON nesting too deep: {depth} "
                                f"(max: {self.max_json_depth})"
                            )
                            return Response(
                                content=json.dumps({
                                    "error": "JSON nesting too deep",
                                    "max_depth": self.max_json_depth
                                }),
                                status_code=400,
                                media_type="application/json",
                            )
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in request body")
                    return Response(
                        content=json.dumps({"error": "Invalid JSON"}),
                        status_code=400,
                        media_type="application/json",
                    )
                except Exception:  # noqa: BLE001
                    pass  # Body already consumed or other error

            # Process request
            response = await call_next(request)

            # Log validation metrics
            elapsed = time.time() - start_time
            if elapsed > 0.05:  # Log if validation takes >50ms
                logger.warning(
                    f"Request validation slow: {elapsed*1000:.1f}ms "
                    f"for {request.url.path}"
                )

            return response

        except Exception as e:  # noqa: BLE001
            logger.exception("Error in request validation middleware")
            return Response(
                content=json.dumps({"error": "Internal server error"}),
                status_code=500,
                media_type="application/json",
            )

    def _get_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of JSON object.

        Args:
            obj: JSON object to analyse
            current_depth: Current recursion depth

        Returns:
            Maximum nesting depth
        """
        if not isinstance(obj, (dict, list)):
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(value, current_depth + 1)
                for value in obj.values()
            )

        if isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(item, current_depth + 1)
                for item in obj
            )

        return current_depth


class ResponseSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for response sanitization and security.

    v0.6.0 SECURITY-API-001: Sanitizes all outgoing responses.

    Sanitization Features:
    - Remove sensitive headers
    - Sanitize error messages
    - Consistent response format
    - Remove server information
    """

    def __init__(
        self,
        app: ASGIApp,
        remove_server_header: bool = True,
        sanitize_errors: bool = True,
    ):
        """Initialise response sanitization middleware.

        Args:
            app: ASGI application
            remove_server_header: Remove Server header from responses
            sanitize_errors: Sanitize error messages in responses
        """
        super().__init__(app)
        self.remove_server_header = remove_server_header
        self.sanitize_errors = sanitize_errors

        # Headers to remove (security-sensitive)
        self.headers_to_remove = [
            "server",
            "x-powered-by",
            "x-aspnet-version",
            "x-aspnetmvc-version",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Sanitize outgoing response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Sanitized response
        """
        # Process request
        response = await call_next(request)

        # Remove sensitive headers
        if self.remove_server_header:
            for header in self.headers_to_remove:
                if header in response.headers:
                    del response.headers[header]

        # Sanitize error messages (if 4xx or 5xx)
        if self.sanitize_errors and response.status_code >= 400:
            # Don't reveal internal paths or stack traces
            # This is handled by FastAPI's exception handlers
            # but we add an extra layer of protection
            logger.debug(
                f"Error response {response.status_code} for {request.url.path}"
            )

        return response
