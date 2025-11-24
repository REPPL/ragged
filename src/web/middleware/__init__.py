"""Web middleware for security, validation, and rate limiting.

v0.6.0: Complete security middleware stack for web UI and API.

Includes:
- Security headers (CSP, HSTS)
- Session management
- XSS protection
- Request validation
- Response sanitization
- JWT authentication
- API versioning
- Rate limiting
"""

from ragged.web.middleware.jwt import APIVersionMiddleware, JWTSecurityMiddleware
from ragged.web.middleware.rate_limit import RateLimitMiddleware
from ragged.web.middleware.security import (
    SecurityHeadersMiddleware,
    SessionSecurityMiddleware,
    XSSProtectionMiddleware,
)
from ragged.web.middleware.validation import (
    RequestValidationMiddleware,
    ResponseSanitizationMiddleware,
)

__all__ = [
    "SecurityHeadersMiddleware",
    "SessionSecurityMiddleware",
    "XSSProtectionMiddleware",
    "RequestValidationMiddleware",
    "ResponseSanitizationMiddleware",
    "JWTSecurityMiddleware",
    "APIVersionMiddleware",
    "RateLimitMiddleware",
]
