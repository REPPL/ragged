"""Security tests for MEDIUM-1: Rate limiting on plugin execution."""

import pytest
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.plugins.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    TokenBucket,
    RateLimitExceeded,
    DEFAULT_RATE_LIMIT,
    DEFAULT_BURST_SIZE,
    MAX_RATE_LIMIT,
    MAX_BURST_SIZE,
)


class TestTokenBucket:
    """Tests for TokenBucket implementation."""

    def test_token_bucket_creation(self):
        """Test token bucket is created with full capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)
        assert bucket.tokens == 10.0
        assert bucket.capacity == 10.0
        assert bucket.refill_rate == 1.0

    def test_consume_tokens_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)
        assert bucket.consume(1.0) is True
        assert bucket.tokens == 9.0

    def test_consume_tokens_insufficient(self):
        """Test token consumption fails when insufficient tokens."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)
        bucket.consume(10.0)  # Consume all tokens
        assert bucket.consume(1.0) is False

    def test_token_refill_over_time(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(capacity=10.0, refill_rate=10.0)  # 10 tokens/second
        bucket.consume(10.0)  # Consume all tokens

        # Wait for refill
        time.sleep(0.5)  # Should refill ~5 tokens

        assert bucket.consume(4.0) is True  # Should succeed
        assert bucket.consume(2.0) is False  # Should fail (not enough yet)

    def test_token_refill_capped_at_capacity(self):
        """Test tokens don't exceed capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=10.0)
        bucket.consume(5.0)  # 5 tokens left

        # Wait for refill
        time.sleep(1.0)  # Would add 10 tokens, but capped at capacity

        assert bucket.tokens <= 10.0

    def test_get_wait_time_zero_when_tokens_available(self):
        """Test wait time is zero when tokens available."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)
        assert bucket.get_wait_time(5.0) == 0.0

    def test_get_wait_time_nonzero_when_insufficient(self):
        """Test wait time is calculated when tokens insufficient."""
        bucket = TokenBucket(capacity=10.0, refill_rate=10.0)  # 10 tokens/second
        bucket.consume(10.0)  # Consume all

        wait_time = bucket.get_wait_time(5.0)
        assert wait_time > 0.0
        assert wait_time <= 0.5  # Should be ~0.5 seconds for 5 tokens at 10/sec

    def test_reset_bucket(self):
        """Test bucket reset restores full capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)
        bucket.consume(10.0)  # Consume all
        assert bucket.tokens == 0.0

        bucket.reset()
        assert bucket.tokens == 10.0

    def test_concurrent_token_consumption(self):
        """Test thread-safe token consumption."""
        bucket = TokenBucket(capacity=100.0, refill_rate=1.0)
        successful_consumptions = []
        lock = threading.Lock()

        def try_consume():
            if bucket.consume(1.0):
                with lock:
                    successful_consumptions.append(1)

        # Launch 150 concurrent attempts (only 100 should succeed)
        threads = [threading.Thread(target=try_consume) for _ in range(150)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have exactly 100 successful consumptions (bucket capacity)
        assert len(successful_consumptions) == 100


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_config_creation_with_defaults(self):
        """Test config creation with default values."""
        config = RateLimitConfig(plugin_name="test_plugin")
        assert config.plugin_name == "test_plugin"
        assert config.requests_per_minute == DEFAULT_RATE_LIMIT
        assert config.burst_size == DEFAULT_BURST_SIZE

    def test_config_creation_with_custom_values(self):
        """Test config creation with custom values."""
        config = RateLimitConfig(
            plugin_name="test_plugin",
            requests_per_minute=200,
            burst_size=20
        )
        assert config.requests_per_minute == 200
        assert config.burst_size == 20

    def test_config_enforces_maximum_rate(self):
        """Test config enforces maximum rate limit."""
        config = RateLimitConfig(
            plugin_name="test_plugin",
            requests_per_minute=2000,  # Exceeds MAX_RATE_LIMIT
        )
        assert config.requests_per_minute == MAX_RATE_LIMIT

    def test_config_enforces_maximum_burst(self):
        """Test config enforces maximum burst size."""
        config = RateLimitConfig(
            plugin_name="test_plugin",
            burst_size=200,  # Exceeds MAX_BURST_SIZE
        )
        assert config.burst_size == MAX_BURST_SIZE

    def test_config_enforces_minimum_values(self):
        """Test config enforces minimum values."""
        config = RateLimitConfig(
            plugin_name="test_plugin",
            requests_per_minute=0,
            burst_size=0
        )
        assert config.requests_per_minute >= 1
        assert config.burst_size >= 1

    def test_config_serialization(self):
        """Test config serialization to dict."""
        config = RateLimitConfig(
            plugin_name="test_plugin",
            requests_per_minute=150,
            burst_size=15
        )
        data = config.to_dict()

        assert data["plugin_name"] == "test_plugin"
        assert data["requests_per_minute"] == 150
        assert data["burst_size"] == 15

    def test_config_deserialization(self):
        """Test config deserialization from dict."""
        data = {
            "plugin_name": "test_plugin",
            "requests_per_minute": 150,
            "burst_size": 15
        }
        config = RateLimitConfig.from_dict(data)

        assert config.plugin_name == "test_plugin"
        assert config.requests_per_minute == 150
        assert config.burst_size == 15


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.fixture
    def rate_limiter(self, tmp_path):
        """Create rate limiter with temporary config."""
        config_path = tmp_path / "rate_limits.json"
        return RateLimiter(config_path=config_path)

    def test_rate_limiter_creation(self, rate_limiter):
        """Test rate limiter is created successfully."""
        assert rate_limiter is not None
        assert rate_limiter._configs == {}
        assert rate_limiter._buckets == {}

    def test_set_rate_limit(self, rate_limiter):
        """Test setting rate limit for a plugin."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=200, burst_size=20)

        config = rate_limiter.get_rate_limit("test_plugin")
        assert config is not None
        assert config.requests_per_minute == 200
        assert config.burst_size == 20

    def test_check_rate_limit_success(self, rate_limiter):
        """Test rate limit check succeeds when under limit."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=60, burst_size=10)

        # Should succeed for burst_size requests
        for _ in range(10):
            rate_limiter.check_rate_limit("test_plugin")

    def test_check_rate_limit_exceeds(self, rate_limiter):
        """Test rate limit check raises exception when exceeded."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=60, burst_size=5)

        # Consume all tokens
        for _ in range(5):
            rate_limiter.check_rate_limit("test_plugin")

        # Next request should fail
        with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
            rate_limiter.check_rate_limit("test_plugin")

    def test_check_rate_limit_with_cost(self, rate_limiter):
        """Test rate limit check with custom cost."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=60, burst_size=10)

        # Consume 5 tokens at once
        rate_limiter.check_rate_limit("test_plugin", cost=5.0)

        # Should have 5 tokens left
        for _ in range(5):
            rate_limiter.check_rate_limit("test_plugin", cost=1.0)

        # Next should fail
        with pytest.raises(RateLimitExceeded):
            rate_limiter.check_rate_limit("test_plugin", cost=1.0)

    def test_rate_limit_auto_created_with_defaults(self, rate_limiter):
        """Test rate limit is auto-created with defaults for unknown plugin."""
        # First check should auto-create with defaults
        rate_limiter.check_rate_limit("unknown_plugin")

        config = rate_limiter.get_rate_limit("unknown_plugin")
        assert config is not None
        assert config.requests_per_minute == DEFAULT_RATE_LIMIT
        assert config.burst_size == DEFAULT_BURST_SIZE

    def test_reset_rate_limit(self, rate_limiter):
        """Test resetting rate limit bucket."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=60, burst_size=5)

        # Consume all tokens
        for _ in range(5):
            rate_limiter.check_rate_limit("test_plugin")

        # Should fail
        with pytest.raises(RateLimitExceeded):
            rate_limiter.check_rate_limit("test_plugin")

        # Reset bucket
        rate_limiter.reset_rate_limit("test_plugin")

        # Should succeed now
        rate_limiter.check_rate_limit("test_plugin")

    def test_get_all_rate_limits(self, rate_limiter):
        """Test getting all rate limits."""
        rate_limiter.set_rate_limit("plugin1", requests_per_minute=100, burst_size=10)
        rate_limiter.set_rate_limit("plugin2", requests_per_minute=200, burst_size=20)

        all_limits = rate_limiter.get_all_rate_limits()
        assert len(all_limits) == 2
        assert "plugin1" in all_limits
        assert "plugin2" in all_limits

    def test_rate_limit_persistence(self, tmp_path):
        """Test rate limit configuration is persisted."""
        config_path = tmp_path / "rate_limits.json"

        # Create limiter and set limits
        limiter1 = RateLimiter(config_path=config_path)
        limiter1.set_rate_limit("test_plugin", requests_per_minute=200, burst_size=20)

        # Create new limiter with same config path
        limiter2 = RateLimiter(config_path=config_path)

        # Should load persisted config
        config = limiter2.get_rate_limit("test_plugin")
        assert config is not None
        assert config.requests_per_minute == 200
        assert config.burst_size == 20


class TestRateLimitingConcurrency:
    """Tests for rate limiting under concurrent load."""

    @pytest.fixture
    def rate_limiter(self, tmp_path):
        """Create rate limiter with temporary config."""
        config_path = tmp_path / "rate_limits.json"
        return RateLimiter(config_path=config_path)

    def test_concurrent_rate_limit_checks(self, rate_limiter):
        """Test concurrent rate limit checks are handled correctly."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=60, burst_size=50)

        successful_checks = []
        failed_checks = []
        lock = threading.Lock()

        def check_limit():
            try:
                rate_limiter.check_rate_limit("test_plugin")
                with lock:
                    successful_checks.append(1)
            except RateLimitExceeded:
                with lock:
                    failed_checks.append(1)

        # Launch 100 concurrent checks (only 50 should succeed)
        threads = [threading.Thread(target=check_limit) for _ in range(100)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have exactly 50 successes (burst size)
        assert len(successful_checks) == 50
        assert len(failed_checks) == 50

    def test_concurrent_multi_plugin_rate_limits(self, rate_limiter):
        """Test concurrent rate limits for multiple plugins."""
        rate_limiter.set_rate_limit("plugin1", requests_per_minute=60, burst_size=10)
        rate_limiter.set_rate_limit("plugin2", requests_per_minute=60, burst_size=10)

        results = {"plugin1": [], "plugin2": []}
        lock = threading.Lock()

        def check_plugin1():
            try:
                rate_limiter.check_rate_limit("plugin1")
                with lock:
                    results["plugin1"].append("success")
            except RateLimitExceeded:
                with lock:
                    results["plugin1"].append("failed")

        def check_plugin2():
            try:
                rate_limiter.check_rate_limit("plugin2")
                with lock:
                    results["plugin2"].append("success")
            except RateLimitExceeded:
                with lock:
                    results["plugin2"].append("failed")

        # Launch concurrent checks for both plugins
        threads = []
        for _ in range(15):
            threads.append(threading.Thread(target=check_plugin1))
            threads.append(threading.Thread(target=check_plugin2))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Each plugin should have 10 successes and 5 failures
        assert results["plugin1"].count("success") == 10
        assert results["plugin1"].count("failed") == 5
        assert results["plugin2"].count("success") == 10
        assert results["plugin2"].count("failed") == 5

    def test_stress_test_with_thread_pool(self, rate_limiter):
        """Stress test rate limiting with thread pool."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=600, burst_size=100)

        def check_limit_batch(batch_id):
            successes = 0
            failures = 0
            for _ in range(20):
                try:
                    rate_limiter.check_rate_limit("test_plugin")
                    successes += 1
                except RateLimitExceeded:
                    failures += 1
            return (successes, failures)

        # Run with thread pool
        total_successes = 0
        total_failures = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_limit_batch, i) for i in range(10)]
            for future in as_completed(futures):
                successes, failures = future.result()
                total_successes += successes
                total_failures += failures

        # Should have exactly 100 successes (burst size)
        assert total_successes == 100
        assert total_failures == 100


class TestRateLimitingDoSPrevention:
    """Tests for DoS attack prevention via rate limiting."""

    @pytest.fixture
    def rate_limiter(self, tmp_path):
        """Create rate limiter with temporary config."""
        config_path = tmp_path / "rate_limits.json"
        return RateLimiter(config_path=config_path)

    def test_prevents_rapid_fire_dos(self, rate_limiter):
        """Test rate limiting prevents rapid-fire DoS attacks."""
        rate_limiter.set_rate_limit("malicious_plugin", requests_per_minute=60, burst_size=5)

        # Simulate rapid-fire attack (100 requests immediately)
        blocked_count = 0
        for _ in range(100):
            try:
                rate_limiter.check_rate_limit("malicious_plugin")
            except RateLimitExceeded:
                blocked_count += 1

        # Should block 95 requests (100 - 5 burst)
        assert blocked_count == 95

    def test_expensive_operation_costs_more_tokens(self, rate_limiter):
        """Test expensive operations can cost more tokens."""
        rate_limiter.set_rate_limit("expensive_plugin", requests_per_minute=60, burst_size=10)

        # Expensive operation costs 5 tokens
        rate_limiter.check_rate_limit("expensive_plugin", cost=5.0)

        # Should only allow 1 more expensive operation (5 tokens left)
        rate_limiter.check_rate_limit("expensive_plugin", cost=5.0)

        # Next expensive operation should fail
        with pytest.raises(RateLimitExceeded):
            rate_limiter.check_rate_limit("expensive_plugin", cost=5.0)

    def test_rate_limit_exception_provides_retry_info(self, rate_limiter):
        """Test rate limit exception provides retry information."""
        rate_limiter.set_rate_limit("test_plugin", requests_per_minute=60, burst_size=1)

        # Consume token
        rate_limiter.check_rate_limit("test_plugin")

        # Trigger rate limit
        try:
            rate_limiter.check_rate_limit("test_plugin")
            assert False, "Should have raised RateLimitExceeded"
        except RateLimitExceeded as e:
            error_msg = str(e)
            assert "Rate limit exceeded" in error_msg
            assert "test_plugin" in error_msg
            assert "60 req/min" in error_msg
            assert "burst 1" in error_msg
            assert "Retry after" in error_msg

    def test_maximum_rate_limit_enforced(self, rate_limiter):
        """Test maximum rate limit is enforced."""
        # Try to set extremely high rate limit
        rate_limiter.set_rate_limit(
            "greedy_plugin",
            requests_per_minute=10000,  # Exceeds MAX_RATE_LIMIT
            burst_size=1000  # Exceeds MAX_BURST_SIZE
        )

        config = rate_limiter.get_rate_limit("greedy_plugin")
        assert config.requests_per_minute == MAX_RATE_LIMIT
        assert config.burst_size == MAX_BURST_SIZE
