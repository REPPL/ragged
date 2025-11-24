"""Rate limiting configuration and utilities.

v0.6.0 SECURITY-RATE-001: Advanced rate limiting configuration.
"""

from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Global defaults
    default_requests_per_minute: int = 60
    default_burst_size: int = 10

    # Per-endpoint configurations
    endpoint_limits: dict[str, int] | None = None

    # Per-user tier configurations
    user_tier_limits: dict[str, int] | None = None

    def __post_init__(self):
        """Initialize default configurations."""
        if self.endpoint_limits is None:
            self.endpoint_limits = {
                "/api/query": 30,  # More expensive operation
                "/api/upload": 10,  # Resource-intensive
                "/api/health": 120,  # Lightweight check
                "/api/collections": 60,  # List operations
            }

        if self.user_tier_limits is None:
            self.user_tier_limits = {
                "free": 30,  # 30 requests/minute
                "basic": 100,  # 100 requests/minute
                "premium": 300,  # 300 requests/minute
                "enterprise": 1000,  # 1000 requests/minute
            }

    def get_endpoint_limit(self, endpoint: str) -> int:
        """Get rate limit for specific endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Requests per minute limit
        """
        return self.endpoint_limits.get(endpoint, self.default_requests_per_minute)

    def get_user_tier_limit(self, tier: str) -> int:
        """Get rate limit for user tier.

        Args:
            tier: User tier (free, basic, premium, enterprise)

        Returns:
            Requests per minute limit
        """
        return self.user_tier_limits.get(tier, self.default_requests_per_minute)
