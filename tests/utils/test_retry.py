"""Tests for retry utilities with exponential backoff."""

import pytest
import time
from unittest.mock import Mock, patch

from src.utils.retry import (
    should_retry,
    exponential_backoff,
    with_retry,
    RetryContext,
    RETRYABLE_EXCEPTIONS,
    NON_RETRYABLE_EXCEPTIONS,
)
from src.exceptions import (
    LLMConnectionError,
    VectorStoreConnectionError,
    ResourceExhaustedError,
    RaggedError,
)


class TestShouldRetry:
    """Tests for should_retry function."""

    def test_retryable_exceptions(self):
        """Test that retryable exceptions return True."""
        assert should_retry(LLMConnectionError("timeout"))
        assert should_retry(VectorStoreConnectionError("connection failed"))

    def test_non_retryable_exceptions(self):
        """Test that non-retryable exceptions return False."""
        assert not should_retry(ResourceExhaustedError("out of memory"))
        assert not should_retry(ValueError("invalid input"))
        assert not should_retry(TypeError("wrong type"))

    def test_unknown_exceptions(self):
        """Test that unknown exceptions default to non-retryable."""
        assert not should_retry(Exception("unknown error"))


class TestExponentialBackoff:
    """Tests for exponential backoff calculation."""

    def test_first_attempt(self):
        """Test delay for first retry attempt."""
        delay = exponential_backoff(0, base_delay=1.0, jitter=False)
        assert delay == 1.0

    def test_second_attempt(self):
        """Test delay for second retry attempt."""
        delay = exponential_backoff(1, base_delay=1.0, jitter=False)
        assert delay == 2.0

    def test_third_attempt(self):
        """Test delay for third retry attempt."""
        delay = exponential_backoff(2, base_delay=1.0, jitter=False)
        assert delay == 4.0

    def test_max_delay_clamping(self):
        """Test that delay is clamped to max_delay."""
        delay = exponential_backoff(10, base_delay=1.0, max_delay=10.0, jitter=False)
        assert delay == 10.0

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delay."""
        delays = [exponential_backoff(0, base_delay=1.0, jitter=True) for _ in range(10)]

        # All delays should be different (with very high probability)
        assert len(set(delays)) > 1

        # All delays should be within reasonable range (0.5 to 1.5 seconds)
        for delay in delays:
            assert 0.5 <= delay <= 1.5

    def test_custom_base_delay(self):
        """Test custom base delay."""
        delay = exponential_backoff(0, base_delay=2.0, jitter=False)
        assert delay == 2.0

        delay = exponential_backoff(1, base_delay=2.0, jitter=False)
        assert delay == 4.0


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retry."""
        mock_func = Mock(return_value="success")

        @with_retry(max_attempts=3)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retries_on_retryable_exception(self):
        """Test that retryable exceptions trigger retries."""
        mock_func = Mock(side_effect=[
            LLMConnectionError("timeout"),
            LLMConnectionError("timeout"),
            "success"
        ])

        @with_retry(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_max_attempts_exhausted(self):
        """Test that exception is raised after max attempts."""
        mock_func = Mock(side_effect=LLMConnectionError("timeout"))

        @with_retry(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(LLMConnectionError):
            test_func()

        assert mock_func.call_count == 3

    def test_non_retryable_exception_no_retry(self):
        """Test that non-retryable exceptions don't trigger retry."""
        mock_func = Mock(side_effect=ValueError("invalid"))

        @with_retry(max_attempts=3)
        def test_func():
            return mock_func()

        with pytest.raises(ValueError):
            test_func()

        # Should only call once (no retry)
        assert mock_func.call_count == 1

    def test_custom_retryable_exceptions(self):
        """Test custom retryable exceptions."""
        mock_func = Mock(side_effect=[ValueError("error"), "success"])

        @with_retry(max_attempts=3, base_delay=0.01, retryable_exceptions=(ValueError,))
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_on_retry_callback(self):
        """Test that on_retry callback is called on each retry."""
        callback = Mock()
        mock_func = Mock(side_effect=[
            LLMConnectionError("timeout"),
            "success"
        ])

        @with_retry(max_attempts=3, base_delay=0.01, on_retry=callback)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert callback.call_count == 1

        # Check callback was called with exception and attempt number
        callback.assert_called_once()
        args = callback.call_args[0]
        assert isinstance(args[0], LLMConnectionError)
        assert args[1] == 1  # First retry

    def test_on_retry_callback_failure_doesnt_stop_retry(self):
        """Test that on_retry callback failure doesn't stop retry."""
        callback = Mock(side_effect=Exception("callback failed"))
        mock_func = Mock(side_effect=[
            LLMConnectionError("timeout"),
            "success"
        ])

        @with_retry(max_attempts=3, base_delay=0.01, on_retry=callback)
        def test_func():
            return mock_func()

        # Should still succeed despite callback failure
        result = test_func()
        assert result == "success"

    def test_exponential_backoff_timing(self):
        """Test that exponential backoff delays are applied."""
        mock_func = Mock(side_effect=[
            LLMConnectionError("timeout"),
            LLMConnectionError("timeout"),
            "success"
        ])

        @with_retry(max_attempts=3, base_delay=0.05, max_delay=1.0)
        def test_func():
            return mock_func()

        start_time = time.time()
        result = test_func()
        elapsed = time.time() - start_time

        assert result == "success"
        # Should take at least 0.05s (first retry) + ~0.1s (second retry) = ~0.15s
        # With jitter it might vary, so check for minimum
        assert elapsed >= 0.05

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @with_retry(max_attempts=3)
        def test_func():
            """Test function docstring."""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."

    def test_with_function_arguments(self):
        """Test retry with function that takes arguments."""
        mock_func = Mock(side_effect=[
            LLMConnectionError("timeout"),
            "success"
        ])

        @with_retry(max_attempts=3, base_delay=0.01)
        def test_func(arg1, arg2, kwarg1=None):
            return mock_func(arg1, arg2, kwarg1=kwarg1)

        result = test_func("a", "b", kwarg1="c")

        assert result == "success"
        assert mock_func.call_count == 2
        mock_func.assert_called_with("a", "b", kwarg1="c")


class TestRetryContext:
    """Tests for RetryContext context manager."""

    def test_successful_operation_first_try(self):
        """Test successful operation on first try."""
        retry_ctx = RetryContext(max_attempts=3)

        for attempt in retry_ctx:
            assert attempt == 0
            break  # Success on first try

        assert retry_ctx.current_attempt == 1

    def test_retries_until_success(self):
        """Test retrying until success."""
        retry_ctx = RetryContext(max_attempts=3, base_delay=0.01)
        attempts = 0

        for attempt in retry_ctx:
            attempts += 1
            if attempt < 2:
                retry_ctx.record_failure(Exception("error"))
            else:
                break  # Success on third try

        assert attempts == 3

    def test_max_attempts_exhausted(self):
        """Test that iteration stops after max attempts."""
        retry_ctx = RetryContext(max_attempts=3, base_delay=0.01)
        attempts = 0

        for attempt in retry_ctx:
            attempts += 1
            retry_ctx.record_failure(Exception("error"))

        assert attempts == 3
        assert retry_ctx.last_exception is not None

    def test_delay_between_retries(self):
        """Test that delay is applied between retries."""
        retry_ctx = RetryContext(max_attempts=3, base_delay=0.05)

        start_time = time.time()
        for attempt in retry_ctx:
            if attempt < 2:
                retry_ctx.record_failure(Exception("error"))
            else:
                break
        elapsed = time.time() - start_time

        # Should have at least 2 delays (after first 2 failures)
        assert elapsed >= 0.05

    def test_last_exception_stored(self):
        """Test that last exception is stored."""
        retry_ctx = RetryContext(max_attempts=2, base_delay=0.01)

        test_exception = ValueError("test error")

        for attempt in retry_ctx:
            retry_ctx.record_failure(test_exception)

        assert retry_ctx.last_exception is test_exception

    def test_custom_delays(self):
        """Test custom base and max delays."""
        retry_ctx = RetryContext(max_attempts=3, base_delay=0.1, max_delay=0.5)

        start_time = time.time()
        for attempt in retry_ctx:
            if attempt < 2:
                retry_ctx.record_failure(Exception("error"))
            else:
                break
        elapsed = time.time() - start_time

        # With base_delay=0.1, first retry ~0.1s, second retry ~0.2s
        assert elapsed >= 0.1


class TestIntegration:
    """Integration tests for retry utilities."""

    def test_retry_with_real_exception_hierarchy(self):
        """Test retry with actual exception hierarchy."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def flaky_operation():
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise VectorStoreConnectionError("connection failed")

            return "success"

        result = flaky_operation()

        assert result == "success"
        assert call_count == 3

    def test_mixed_retryable_and_non_retryable(self):
        """Test that only retryable exceptions are retried."""
        call_count = 0

        @with_retry(max_attempts=5, base_delay=0.01)
        def operation():
            nonlocal call_count
            call_count += 1

            # First 2 attempts: retryable
            if call_count <= 2:
                raise LLMConnectionError("timeout")
            # Third attempt: non-retryable
            else:
                raise ValueError("invalid input")

        with pytest.raises(ValueError):
            operation()

        # Should stop after ValueError (not retry)
        assert call_count == 3

    def test_retry_with_resource_cleanup(self):
        """Test that retry works correctly with resource cleanup."""
        resources = []

        @with_retry(max_attempts=3, base_delay=0.01)
        def operation_with_cleanup():
            resource = Mock()
            resources.append(resource)

            if len(resources) < 2:
                raise LLMConnectionError("error")

            return "success"

        result = operation_with_cleanup()

        assert result == "success"
        assert len(resources) == 2  # Failed once, succeeded on retry
