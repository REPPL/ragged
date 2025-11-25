"""Rate limiting for plugin execution.

SECURITY FIX (MEDIUM-1): Prevents DoS attacks via excessive plugin calls.

Implements token bucket algorithm for rate limiting with:
- Per-plugin rate limits
- Configurable rates and burst sizes
- Thread-safe operations
- Automatic token replenishment
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# SECURITY FIX (MEDIUM-1): Default rate limits to prevent DoS
DEFAULT_RATE_LIMIT = 100  # requests per minute
DEFAULT_BURST_SIZE = 10  # maximum burst requests
MAX_RATE_LIMIT = 1000  # maximum configurable rate
MAX_BURST_SIZE = 100  # maximum configurable burst


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    pass


@dataclass
class TokenBucket:
    """Token bucket for rate limiting.

    SECURITY FIX (MEDIUM-1): Thread-safe token bucket implementation.
    """

    capacity: float  # Maximum tokens (burst size)
    refill_rate: float  # Tokens added per second
    tokens: float = field(init=False)  # Current available tokens
    last_refill: float = field(init=False)  # Last refill timestamp
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self):
        """Initialise token bucket with full capacity."""
        self.tokens = self.capacity
        self.last_refill = time.time()

    def consume(self, tokens: float = 1.0) -> bool:
        """Attempt to consume tokens.

        SECURITY FIX (MEDIUM-1): Thread-safe token consumption.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        with self._lock:
            # Refill tokens based on time passed
            now = time.time()
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + (time_passed * self.refill_rate)
            )
            self.last_refill = now

            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: float = 1.0) -> float:
        """Get time to wait until tokens available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds to wait (0 if tokens available)
        """
        with self._lock:
            if self.tokens >= tokens:
                return 0.0
            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate

    def reset(self) -> None:
        """Reset bucket to full capacity."""
        with self._lock:
            self.tokens = self.capacity
            self.last_refill = time.time()


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a plugin."""

    plugin_name: str
    requests_per_minute: int = DEFAULT_RATE_LIMIT
    burst_size: int = DEFAULT_BURST_SIZE

    def __post_init__(self):
        """Validate rate limit configuration.

        SECURITY FIX (MEDIUM-1): Enforces maximum rate limits.
        """
        if self.requests_per_minute > MAX_RATE_LIMIT:
            logger.warning(
                f"Rate limit {self.requests_per_minute} exceeds maximum {MAX_RATE_LIMIT}, "
                f"capping at {MAX_RATE_LIMIT}"
            )
            self.requests_per_minute = MAX_RATE_LIMIT

        if self.burst_size > MAX_BURST_SIZE:
            logger.warning(
                f"Burst size {self.burst_size} exceeds maximum {MAX_BURST_SIZE}, "
                f"capping at {MAX_BURST_SIZE}"
            )
            self.burst_size = MAX_BURST_SIZE

        if self.burst_size < 1:
            self.burst_size = 1

        if self.requests_per_minute < 1:
            self.requests_per_minute = 1

    def to_dict(self) -> dict:
        """Serialise to dictionary."""
        return {
            "plugin_name": self.plugin_name,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitConfig":
        """Deserialise from dictionary."""
        return cls(
            plugin_name=data["plugin_name"],
            requests_per_minute=data.get("requests_per_minute", DEFAULT_RATE_LIMIT),
            burst_size=data.get("burst_size", DEFAULT_BURST_SIZE),
        )


class RateLimiter:
    """Manages rate limiting for plugin execution.

    SECURITY FIX (MEDIUM-1): Thread-safe rate limiting to prevent DoS.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialise rate limiter.

        Args:
            config_path: Path to rate limit config (defaults to ~/.ragged/plugins/rate_limits.json)
        """
        if config_path is None:
            config_path = Path.home() / ".ragged" / "plugins" / "rate_limits.json"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self._configs: dict[str, RateLimitConfig] = {}
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.RLock()

        self._load_config()

    def _load_config(self) -> None:
        """Load rate limit configuration from storage."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    for plugin_data in data.get("plugins", []):
                        config = RateLimitConfig.from_dict(plugin_data)
                        self._configs[config.plugin_name] = config
                        self._create_bucket(config)
                logger.info(f"Loaded rate limits for {len(self._configs)} plugins")
            except Exception as e:
                logger.error(f"Failed to load rate limit config: {e}")

    def _save_config(self) -> None:
        """Save rate limit configuration to storage."""
        try:
            data = {"plugins": [c.to_dict() for c in self._configs.values()]}
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved rate limit configuration")
        except Exception as e:
            logger.error(f"Failed to save rate limit config: {e}")

    def _create_bucket(self, config: RateLimitConfig) -> TokenBucket:
        """Create token bucket from config.

        Args:
            config: Rate limit configuration

        Returns:
            Token bucket instance
        """
        refill_rate = config.requests_per_minute / 60.0  # tokens per second
        return TokenBucket(
            capacity=float(config.burst_size),
            refill_rate=refill_rate
        )

    def set_rate_limit(
        self,
        plugin_name: str,
        requests_per_minute: int,
        burst_size: int | None = None
    ) -> None:
        """Set rate limit for a plugin.

        SECURITY FIX (MEDIUM-1): Enforces maximum rate limits.

        Args:
            plugin_name: Name of the plugin
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (defaults to min(10, requests_per_minute/6))
        """
        if burst_size is None:
            burst_size = min(DEFAULT_BURST_SIZE, max(1, requests_per_minute // 6))

        with self._lock:
            config = RateLimitConfig(
                plugin_name=plugin_name,
                requests_per_minute=requests_per_minute,
                burst_size=burst_size
            )
            self._configs[plugin_name] = config
            self._buckets[plugin_name] = self._create_bucket(config)
            self._save_config()

        logger.info(
            f"Set rate limit for {plugin_name}: "
            f"{requests_per_minute} req/min, burst {burst_size}"
        )

    def check_rate_limit(self, plugin_name: str, cost: float = 1.0) -> None:
        """Check and consume rate limit for plugin.

        SECURITY FIX (MEDIUM-1): Enforces rate limits to prevent DoS.

        Args:
            plugin_name: Name of the plugin
            cost: Cost in tokens (default 1.0, can be higher for expensive operations)

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        with self._lock:
            # Get or create default bucket for plugin
            if plugin_name not in self._buckets:
                default_config = RateLimitConfig(plugin_name=plugin_name)
                self._configs[plugin_name] = default_config
                self._buckets[plugin_name] = self._create_bucket(default_config)
                self._save_config()

            bucket = self._buckets[plugin_name]

        # Try to consume tokens (outside main lock to reduce contention)
        if not bucket.consume(cost):
            wait_time = bucket.get_wait_time(cost)
            config = self._configs[plugin_name]
            raise RateLimitExceeded(
                f"Rate limit exceeded for plugin '{plugin_name}'. "
                f"Limit: {config.requests_per_minute} req/min (burst {config.burst_size}). "
                f"Retry after {wait_time:.1f} seconds."
            )

        logger.debug(
            f"Rate limit check passed for {plugin_name} (cost: {cost})"
        )

    def get_rate_limit(self, plugin_name: str) -> RateLimitConfig | None:
        """Get rate limit configuration for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            RateLimitConfig if exists, None otherwise
        """
        with self._lock:
            return self._configs.get(plugin_name)

    def reset_rate_limit(self, plugin_name: str) -> None:
        """Reset rate limit bucket for a plugin.

        Args:
            plugin_name: Name of the plugin
        """
        with self._lock:
            if plugin_name in self._buckets:
                self._buckets[plugin_name].reset()
                logger.info(f"Reset rate limit for {plugin_name}")

    def get_all_rate_limits(self) -> dict[str, RateLimitConfig]:
        """Get all rate limit configurations.

        Returns:
            Dictionary mapping plugin names to their rate limit configs
        """
        with self._lock:
            return self._configs.copy()
