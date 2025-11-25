"""Rate limiting middleware with per-user and per-endpoint limits.

v0.6.0 SECURITY-RATE-001: Advanced rate limiting implementation.

Features:
- Per-user rate limiting with quotas
- Per-endpoint limits (cost-based)
- Redis-backed storage (optional)
- Rate limit headers (X-RateLimit-*)
"""
from __future__ import annotations


import time
from collections import defaultdict
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ragged.config.rate_limits import RateLimitConfig
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware.

    v0.6.0 SECURITY-RATE-001: Per-user, per-endpoint rate limiting.

    Features:
    - Token bucket algorithm for rate limiting
    - Per-user quotas based on tier
    - Per-endpoint limits
    - Rate limit headers
    - Optional Redis backend for distributed systems
    """

    def __init__(
        self,
        app: ASGIApp,
        config: RateLimitConfig | None = None,
        enable_redis: bool = False,
        redis_url: str | None = None,
    ):
        """Initialise rate limit middleware.

        Args:
            app: ASGI application
            config: Rate limit configuration
            enable_redis: Use Redis for distributed rate limiting
            redis_url: Redis connection URL
        """
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.enable_redis = enable_redis
        self.redis_url = redis_url

        # In-memory storage (for single instance or when Redis disabled)
        # Format: {user_id: {endpoint: {tokens: int, last_refill: float}}}
        self._buckets: dict[str, dict[str, dict[str, Any]]] = defaultdict(
            lambda: defaultdict(dict)
        )

        # Redis client (lazy loaded)
        self._redis = None
        if self.enable_redis and self.redis_url:
            self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            import redis
            self._redis = redis.from_url(self.redis_url)
            logger.info("Redis rate limiting enabled")
        except ImportError:
            logger.warning(
                "Redis library not installed. Falling back to in-memory rate limiting."
            )
            self.enable_redis = False
        except Exception:  # noqa: BLE001
            logger.exception("Failed to connect to Redis")
            self.enable_redis = False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with rate limit headers or 429 if limit exceeded
        """
        # Extract user identifier (from session, JWT, or IP)
        user_id = self._get_user_id(request)

        # Get endpoint path
        endpoint = request.url.path

        # Determine rate limit for this request
        limit = self._get_rate_limit(endpoint, user_id, request)

        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            user_id, endpoint, limit
        )

        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for user {user_id} on {endpoint} "
                f"(limit: {limit}/min)"
            )

            response = Response(
                content='{"error":"Rate limit exceeded","retry_after":' + str(int(reset_time - time.time())) + '}',
                status_code=429,
                media_type="application/json",
            )

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
            response.headers["Retry-After"] = str(int(reset_time - time.time()))

            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response

    def _get_user_id(self, request: Request) -> str:
        """Extract user identifier from request.

        Args:
            request: HTTP request

        Returns:
            User identifier (session ID, JWT user_id, or IP address)
        """
        # Try session ID first
        if hasattr(request.state, "session_id"):
            return f"session:{request.state.session_id}"

        # Try JWT user ID
        if hasattr(request.state, "jwt_user_id"):
            return f"user:{request.state.jwt_user_id}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        return "anonymous"

    def _get_rate_limit(self, endpoint: str, user_id: str, request: Request) -> int:
        """Determine rate limit for this request.

        Args:
            endpoint: API endpoint path
            user_id: User identifier
            request: HTTP request

        Returns:
            Requests per minute limit
        """
        # Check if user has a tier (from JWT or session)
        user_tier = getattr(request.state, "user_tier", "free")

        # Get per-endpoint limit
        endpoint_limit = self.config.get_endpoint_limit(endpoint)

        # Get per-user tier limit
        tier_limit = self.config.get_user_tier_limit(user_tier)

        # Use the minimum of endpoint and tier limits
        return min(endpoint_limit, tier_limit)

    async def _check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int
    ) -> tuple[bool, int, float]:
        """Check if request is within rate limit.

        Args:
            user_id: User identifier
            endpoint: API endpoint path
            limit: Requests per minute limit

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        now = time.time()
        window = 60.0  # 1 minute window

        if self.enable_redis and self._redis:
            return await self._check_rate_limit_redis(user_id, endpoint, limit, now, window)
        else:
            return self._check_rate_limit_memory(user_id, endpoint, limit, now, window)

    def _check_rate_limit_memory(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        now: float,
        window: float
    ) -> tuple[bool, int, float]:
        """Check rate limit using in-memory storage.

        Args:
            user_id: User identifier
            endpoint: API endpoint path
            limit: Requests per minute limit
            now: Current timestamp
            window: Time window in seconds

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        bucket = self._buckets[user_id][endpoint]

        # Initialize bucket if needed
        if "tokens" not in bucket:
            bucket["tokens"] = limit
            bucket["last_refill"] = now

        # Refill tokens based on time passed
        time_passed = now - bucket["last_refill"]
        refill_amount = (time_passed / window) * limit

        bucket["tokens"] = min(limit, bucket["tokens"] + refill_amount)
        bucket["last_refill"] = now

        # Check if request is allowed
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            remaining = int(bucket["tokens"])
            reset_time = now + window
            return True, remaining, reset_time
        else:
            remaining = 0
            # Calculate when bucket will have at least 1 token
            time_until_refill = (1.0 - bucket["tokens"]) * (window / limit)
            reset_time = now + time_until_refill
            return False, remaining, reset_time

    async def _check_rate_limit_redis(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        now: float,
        window: float
    ) -> tuple[bool, int, float]:
        """Check rate limit using Redis storage.

        Args:
            user_id: User identifier
            endpoint: API endpoint path
            limit: Requests per minute limit
            now: Current timestamp
            window: Time window in seconds

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        key = f"ratelimit:{user_id}:{endpoint}"

        try:
            # Use Redis INCR with EXPIRE for sliding window
            count = self._redis.incr(key)

            if count == 1:
                # First request in window - set expiry
                self._redis.expire(key, int(window))

            remaining = max(0, limit - count)
            reset_time = now + window

            allowed = count <= limit

            return allowed, remaining, reset_time

        except Exception:  # noqa: BLE001
            logger.exception("Redis rate limit check failed, falling back to memory")
            return self._check_rate_limit_memory(user_id, endpoint, limit, now, window)
