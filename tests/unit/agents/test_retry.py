"""Unit tests for agent retry module."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from ragged.agents.retry import (
    RetryStrategy,
    ErrorCategory,
    RetryConfig,
    RetryState,
    ErrorClassifier,
    RecoveryAction,
    RecoveryManager,
    RetryExecutor,
    RetryConfigs,
    CircuitBreaker,
    with_retry,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True

    def test_calculate_delay_immediate(self):
        """Test immediate strategy (no delay)."""
        config = RetryConfig(strategy=RetryStrategy.IMMEDIATE, jitter=False)
        assert config.calculate_delay(1) == 0.0
        assert config.calculate_delay(5) == 0.0

    def test_calculate_delay_linear(self):
        """Test linear backoff."""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            base_delay=1.0,
            jitter=False,
        )
        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 3.0

    def test_calculate_delay_exponential(self):
        """Test exponential backoff."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            jitter=False,
        )
        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 4.0
        assert config.calculate_delay(4) == 8.0

    def test_calculate_delay_fibonacci(self):
        """Test Fibonacci backoff."""
        config = RetryConfig(
            strategy=RetryStrategy.FIBONACCI,
            base_delay=1.0,
            jitter=False,
        )
        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 1.0
        assert config.calculate_delay(3) == 2.0
        assert config.calculate_delay(4) == 3.0
        assert config.calculate_delay(5) == 5.0

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=10.0,
            max_delay=30.0,
            jitter=False,
        )
        # 10 * 2^4 = 160, should be capped at 30
        assert config.calculate_delay(5) == 30.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness."""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            base_delay=10.0,
            jitter=True,
        )
        delays = [config.calculate_delay(2) for _ in range(10)]
        # With jitter, delays should vary
        assert len(set(delays)) > 1  # At least some variation


class TestRetryState:
    """Tests for RetryState."""

    def test_initial_state(self):
        """Test initial state values."""
        state = RetryState()
        assert state.attempt == 0
        assert state.total_attempts == 0
        assert state.last_error is None
        assert state.errors == []

    def test_record_error(self):
        """Test recording errors."""
        state = RetryState()
        error = ValueError("Test error")
        state.record_error(error)

        assert state.total_attempts == 1
        assert state.last_error is error
        assert len(state.errors) == 1

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        state = RetryState()
        # Should be very small since just created
        assert state.elapsed_time < 1.0


class TestErrorClassifier:
    """Tests for ErrorClassifier."""

    def test_classify_timeout(self):
        """Test classifying timeout errors."""
        assert ErrorClassifier.classify(TimeoutError()) == ErrorCategory.TIMEOUT
        assert ErrorClassifier.classify(asyncio.TimeoutError()) == ErrorCategory.TIMEOUT

    def test_classify_transient(self):
        """Test classifying transient errors."""
        assert ErrorClassifier.classify(ConnectionError()) == ErrorCategory.TRANSIENT
        assert ErrorClassifier.classify(ConnectionRefusedError()) == ErrorCategory.TRANSIENT

    def test_classify_validation(self):
        """Test classifying validation errors."""
        assert ErrorClassifier.classify(ValueError()) == ErrorCategory.VALIDATION
        assert ErrorClassifier.classify(TypeError()) == ErrorCategory.VALIDATION
        assert ErrorClassifier.classify(KeyError("missing")) == ErrorCategory.VALIDATION

    def test_classify_permanent(self):
        """Test classifying permanent errors."""
        assert ErrorClassifier.classify(PermissionError()) == ErrorCategory.PERMANENT
        assert ErrorClassifier.classify(FileNotFoundError()) == ErrorCategory.PERMANENT

    def test_classify_resource(self):
        """Test classifying resource errors."""
        assert ErrorClassifier.classify(MemoryError()) == ErrorCategory.RESOURCE

    def test_classify_by_message(self):
        """Test classifying by error message patterns."""
        assert ErrorClassifier.classify(Exception("Connection timeout")) == ErrorCategory.TIMEOUT
        assert ErrorClassifier.classify(Exception("network error")) == ErrorCategory.TRANSIENT
        assert ErrorClassifier.classify(Exception("memory limit exceeded")) == ErrorCategory.RESOURCE

    def test_classify_unknown(self):
        """Test classifying unknown errors."""
        assert ErrorClassifier.classify(Exception("random error")) == ErrorCategory.UNKNOWN

    def test_is_retryable(self):
        """Test retryability check."""
        config = RetryConfig()

        assert ErrorClassifier.is_retryable(TimeoutError(), config) is True
        assert ErrorClassifier.is_retryable(ConnectionError(), config) is True
        assert ErrorClassifier.is_retryable(ValueError(), config) is False

    def test_register_custom_classification(self):
        """Test registering custom error classifications."""

        class CustomError(Exception):
            pass

        ErrorClassifier.register(CustomError, ErrorCategory.TRANSIENT)
        assert ErrorClassifier.classify(CustomError()) == ErrorCategory.TRANSIENT


class TestRecoveryManager:
    """Tests for RecoveryManager."""

    @pytest.fixture
    def manager(self):
        """Create a recovery manager."""
        return RecoveryManager()

    def test_register_action(self, manager):
        """Test registering recovery actions."""
        action = RecoveryAction(
            name="reconnect",
            description="Attempt to reconnect",
            handler=lambda e, ctx: "reconnected",
            applicable_categories=(ErrorCategory.TRANSIENT,),
        )
        manager.register_action(action)
        assert len(manager._actions) == 1

    def test_register_fallback(self, manager):
        """Test registering fallbacks."""
        manager.register_fallback("default", lambda: "fallback result")
        assert manager.get_fallback("default") is not None
        assert manager.get_fallback("nonexistent") is None

    @pytest.mark.asyncio
    async def test_attempt_recovery(self, manager):
        """Test attempting recovery."""
        action = RecoveryAction(
            name="timeout_recovery",
            description="Handle timeout",
            handler=lambda e, ctx: "recovered",
            applicable_categories=(ErrorCategory.TIMEOUT,),
        )
        manager.register_action(action)

        result = await manager.attempt_recovery(TimeoutError(), {})
        assert result == "recovered"

    @pytest.mark.asyncio
    async def test_attempt_recovery_no_match(self, manager):
        """Test recovery with no matching action."""
        result = await manager.attempt_recovery(ValueError(), {})
        assert result is None

    @pytest.mark.asyncio
    async def test_attempt_recovery_async_handler(self, manager):
        """Test recovery with async handler."""

        async def async_handler(error, context):
            return "async recovered"

        action = RecoveryAction(
            name="async_recovery",
            description="Async recovery",
            handler=async_handler,
            applicable_categories=(ErrorCategory.TRANSIENT,),
        )
        manager.register_action(action)

        result = await manager.attempt_recovery(ConnectionError(), {})
        assert result == "async recovered"


class TestRetryExecutor:
    """Tests for RetryExecutor."""

    @pytest.fixture
    def executor(self):
        """Create a retry executor."""
        return RetryExecutor(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """Test successful execution."""

        async def success_op():
            return "success"

        result = await executor.execute(success_op)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_retry_then_success(self, executor):
        """Test retry then success."""
        attempts = [0]

        async def flaky_op():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await executor.execute(flaky_op)
        assert result == "success"
        assert attempts[0] == 2

    @pytest.mark.asyncio
    async def test_execute_exhaust_retries(self, executor):
        """Test exhausting all retries."""

        async def always_fail():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            await executor.execute(always_fail)

    @pytest.mark.asyncio
    async def test_execute_non_retryable_error(self, executor):
        """Test non-retryable error fails immediately."""

        async def validation_error():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            await executor.execute(validation_error)

    @pytest.mark.asyncio
    async def test_execute_with_recovery(self):
        """Test execution with recovery manager."""
        recovery = RecoveryManager()
        recovery.register_action(
            RecoveryAction(
                name="recover",
                description="Recovery",
                handler=lambda e, ctx: "recovered value",
                applicable_categories=(ErrorCategory.TIMEOUT,),
            )
        )
        executor = RetryExecutor(
            RetryConfig(max_attempts=2, base_delay=0.01),
            recovery_manager=recovery,
        )

        async def timeout_op():
            raise TimeoutError("Timeout")

        result = await executor.execute(timeout_op)
        assert result == "recovered value"


class TestWithRetryDecorator:
    """Tests for the with_retry decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator with successful function."""

        @with_retry(RetryConfig(max_attempts=3))
        async def success_fn():
            return "decorated success"

        result = await success_fn()
        assert result == "decorated success"

    @pytest.mark.asyncio
    async def test_decorator_retry(self):
        """Test decorator with retries."""
        attempts = [0]

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))
        async def flaky_fn():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Flaky")
            return "success"

        result = await flaky_fn()
        assert result == "success"
        assert attempts[0] == 2

    @pytest.mark.asyncio
    async def test_decorator_on_retry_callback(self):
        """Test on_retry callback."""
        retry_calls = []

        def on_retry(attempt, error):
            retry_calls.append((attempt, str(error)))

        @with_retry(
            RetryConfig(max_attempts=3, base_delay=0.01, jitter=False),
            on_retry=on_retry,
        )
        async def flaky_fn():
            if len(retry_calls) < 2:
                raise ConnectionError("Retry me")
            return "done"

        result = await flaky_fn()
        assert result == "done"
        assert len(retry_calls) == 2


class TestRetryConfigs:
    """Tests for pre-configured retry settings."""

    def test_fast_config(self):
        """Test FAST configuration."""
        config = RetryConfigs.FAST
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.IMMEDIATE

    def test_standard_config(self):
        """Test STANDARD configuration."""
        config = RetryConfigs.STANDARD
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL

    def test_patient_config(self):
        """Test PATIENT configuration."""
        config = RetryConfigs.PATIENT
        assert config.max_attempts == 5
        assert config.max_delay == 60.0

    def test_aggressive_config(self):
        """Test AGGRESSIVE configuration."""
        config = RetryConfigs.AGGRESSIVE
        assert config.max_attempts == 10
        assert config.strategy == RetryStrategy.FIBONACCI


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker."""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.1,
            half_open_requests=2,
        )

    def test_initial_state_closed(self, breaker):
        """Test initial state is closed."""
        assert breaker.state == CircuitBreaker.State.CLOSED

    def test_allow_request_when_closed(self, breaker):
        """Test requests allowed when closed."""
        assert breaker.allow_request() is True

    def test_opens_after_failures(self, breaker):
        """Test circuit opens after failure threshold."""
        for _ in range(3):
            breaker.record_failure()

        assert breaker.state == CircuitBreaker.State.OPEN
        assert breaker.allow_request() is False

    def test_success_resets_failure_count(self, breaker):
        """Test success resets failure count."""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()

        assert breaker.state == CircuitBreaker.State.CLOSED
        # Two more failures needed to open
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreaker.State.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, breaker):
        """Test transition to half-open after timeout."""
        for _ in range(3):
            breaker.record_failure()

        assert breaker.state == CircuitBreaker.State.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        assert breaker.state == CircuitBreaker.State.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_to_closed(self, breaker):
        """Test transition from half-open to closed."""
        for _ in range(3):
            breaker.record_failure()
        await asyncio.sleep(0.2)  # Wait longer than recovery_timeout (0.1s)

        # Verify we're in half-open state
        assert breaker.state == CircuitBreaker.State.HALF_OPEN

        # Record successful requests in half-open state (need half_open_requests = 2)
        breaker.record_success()
        assert breaker.state == CircuitBreaker.State.HALF_OPEN  # Still half-open after 1
        breaker.record_success()

        assert breaker.state == CircuitBreaker.State.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self, breaker):
        """Test transition back to open on failure in half-open."""
        for _ in range(3):
            breaker.record_failure()
        await asyncio.sleep(0.15)

        breaker.record_failure()
        assert breaker.state == CircuitBreaker.State.OPEN

    def test_reset(self, breaker):
        """Test resetting the circuit breaker."""
        for _ in range(3):
            breaker.record_failure()

        breaker.reset()
        assert breaker.state == CircuitBreaker.State.CLOSED
        assert breaker.allow_request() is True

    @pytest.mark.asyncio
    async def test_execute_success(self, breaker):
        """Test execute with successful operation."""

        async def success_op():
            return "success"

        result = await breaker.execute(success_op)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_rejected_when_open(self, breaker):
        """Test execute rejects when circuit is open."""
        for _ in range(3):
            breaker.record_failure()

        async def any_op():
            return "should not run"

        with pytest.raises(RuntimeError, match="Circuit breaker"):
            await breaker.execute(any_op)
