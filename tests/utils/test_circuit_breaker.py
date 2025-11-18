"""Tests for circuit breaker pattern."""

import pytest
import time
from unittest.mock import Mock

from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreakerInitialization:
    """Tests for CircuitBreaker initialization."""

    def test_default_initialization(self):
        """Test circuit breaker with default parameters."""
        breaker = CircuitBreaker()

        assert breaker.name == "service"
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60.0
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed
        assert not breaker.is_open
        assert not breaker.is_half_open

    def test_custom_initialization(self):
        """Test circuit breaker with custom parameters."""
        breaker = CircuitBreaker(
            name="test_service",
            failure_threshold=3,
            recovery_timeout=30.0,
            half_open_max_calls=2,
            success_threshold=1,
        )

        assert breaker.name == "test_service"
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.half_open_max_calls == 2
        assert breaker.success_threshold == 1


class TestCircuitBreakerClosedState:
    """Tests for circuit breaker in CLOSED state."""

    def test_successful_calls_keep_circuit_closed(self):
        """Test that successful calls keep circuit closed."""
        breaker = CircuitBreaker(failure_threshold=3)
        mock_func = Mock(return_value="success")

        # Multiple successful calls
        for _ in range(10):
            result = breaker.call(mock_func)
            assert result == "success"
            assert breaker.is_closed

        assert mock_func.call_count == 10

    def test_single_failure_doesnt_open_circuit(self):
        """Test that single failure doesn't open circuit."""
        breaker = CircuitBreaker(failure_threshold=3)

        with pytest.raises(Exception):
            breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        assert breaker.is_closed

    def test_failures_below_threshold_keep_circuit_closed(self):
        """Test that failures below threshold keep circuit closed."""
        breaker = CircuitBreaker(failure_threshold=3)
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("error")
            return "success"

        # First two calls fail
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(flaky_func)

        assert breaker.is_closed

        # Third call succeeds - should reset failure count
        result = breaker.call(flaky_func)
        assert result == "success"
        assert breaker.is_closed

    def test_threshold_failures_open_circuit(self):
        """Test that reaching failure threshold opens circuit."""
        breaker = CircuitBreaker(failure_threshold=3)

        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        assert breaker.is_open


class TestCircuitBreakerOpenState:
    """Tests for circuit breaker in OPEN state."""

    def test_open_circuit_rejects_calls(self):
        """Test that open circuit immediately rejects calls."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10.0)

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        assert breaker.is_open

        # Subsequent calls should be rejected immediately
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            breaker.call(lambda: "should not execute")

        assert "OPEN" in str(exc_info.value)

    def test_open_circuit_transitions_to_half_open_after_timeout(self):
        """Test that circuit transitions to half-open after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        assert breaker.is_open

        # Wait for recovery timeout
        time.sleep(0.15)

        # Next call should transition to half-open
        mock_func = Mock(return_value="success")
        result = breaker.call(mock_func)

        assert result == "success"
        assert breaker.is_half_open or breaker.is_closed  # Depends on success_threshold


class TestCircuitBreakerHalfOpenState:
    """Tests for circuit breaker in HALF_OPEN state."""

    def test_half_open_allows_limited_calls(self):
        """Test that half-open state allows limited calls."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=2,
            success_threshold=2,
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        # Wait for recovery
        time.sleep(0.15)

        # First call transitions to half-open
        mock_func = Mock(return_value="success")
        breaker.call(mock_func)
        assert breaker.is_half_open

        # Second call still in half-open
        breaker.call(mock_func)

        # Should have transitioned to closed after success_threshold (2) successes
        assert breaker.is_closed

    def test_half_open_success_closes_circuit(self):
        """Test that enough successes in half-open close the circuit."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2,
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        # Wait for recovery
        time.sleep(0.15)

        # Successful calls in half-open
        mock_func = Mock(return_value="success")
        for _ in range(2):
            breaker.call(mock_func)

        # Should be closed after 2 successes
        assert breaker.is_closed

    def test_half_open_failure_reopens_circuit(self):
        """Test that failure in half-open immediately reopens circuit."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        # Wait for recovery
        time.sleep(0.15)

        # Fail in half-open state
        with pytest.raises(Exception):
            breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        # Should be open again
        assert breaker.is_open

    def test_half_open_exceeds_max_calls(self):
        """Test that exceeding max calls in half-open rejects requests."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=1,
            success_threshold=2,
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        # Wait for recovery
        time.sleep(0.15)

        # First call in half-open
        mock_func = Mock(return_value="success")
        breaker.call(mock_func)
        assert breaker.is_half_open

        # Second call should be rejected (exceeds max_calls=1)
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(mock_func)


class TestCircuitBreakerDecorator:
    """Tests for circuit breaker decorator."""

    def test_decorator_protects_function(self):
        """Test that decorator provides circuit protection."""
        breaker = CircuitBreaker(failure_threshold=2)

        @breaker.protect
        def risky_function():
            raise Exception("error")

        # Fail twice to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                risky_function()

        assert breaker.is_open

        # Next call should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerOpenError):
            risky_function()

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        breaker = CircuitBreaker()

        @breaker.protect
        def test_function():
            """Test docstring."""
            return "result"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."

    def test_decorator_with_arguments(self):
        """Test decorated function with arguments."""
        breaker = CircuitBreaker(failure_threshold=5)

        @breaker.protect
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5


class TestCircuitBreakerStatistics:
    """Tests for circuit breaker statistics."""

    def test_get_stats_closed(self):
        """Test statistics for closed circuit."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        stats = breaker.get_stats()

        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["failure_threshold"] == 3
        assert stats["recent_failures"] == []

    def test_get_stats_after_failures(self):
        """Test statistics after some failures."""
        breaker = CircuitBreaker(failure_threshold=3)

        # Fail once
        with pytest.raises(Exception):
            breaker.call(lambda: (_ for _ in ()).throw(Exception("test error")))

        stats = breaker.get_stats()

        assert stats["failure_count"] == 1
        assert len(stats["recent_failures"]) == 1
        assert "test error" in stats["recent_failures"][0]

    def test_get_stats_open(self):
        """Test statistics for open circuit."""
        breaker = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        stats = breaker.get_stats()

        assert stats["state"] == "open"
        assert stats["failure_count"] == 2
        assert stats["last_failure_time"] is not None

    def test_recent_failures_limited(self):
        """Test that recent failures list is limited."""
        breaker = CircuitBreaker(failure_threshold=20)

        # Generate 15 failures
        for i in range(15):
            with pytest.raises(Exception):
                breaker.call(lambda i=i: (_ for _ in ()).throw(Exception(f"error {i}")))

        stats = breaker.get_stats()

        # Should only keep last 10 (maxlen=10 in deque)
        assert len(stats["recent_failures"]) == 10


class TestCircuitBreakerReset:
    """Tests for manual circuit reset."""

    def test_reset_closes_circuit(self):
        """Test that reset closes open circuit."""
        breaker = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        assert breaker.is_open

        # Manual reset
        breaker.reset()

        assert breaker.is_closed

        # Should accept calls now
        mock_func = Mock(return_value="success")
        result = breaker.call(mock_func)
        assert result == "success"

    def test_reset_clears_failure_count(self):
        """Test that reset clears failure count."""
        breaker = CircuitBreaker(failure_threshold=3)

        # Accumulate failures
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        stats = breaker.get_stats()
        assert stats["failure_count"] == 2

        # Reset
        breaker.reset()

        stats = breaker.get_stats()
        assert stats["failure_count"] == 0
        assert stats["recent_failures"] == []


class TestCircuitBreakerThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_calls_thread_safe(self):
        """Test that concurrent calls are thread-safe."""
        import threading

        breaker = CircuitBreaker(failure_threshold=10)
        call_count = 0
        lock = threading.Lock()

        def test_func():
            nonlocal call_count
            with lock:
                call_count += 1
            return "success"

        # Simulate concurrent calls
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=lambda: breaker.call(test_func))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert call_count == 20
        assert breaker.is_closed

    def test_concurrent_failures_thread_safe(self):
        """Test that concurrent failures are handled thread-safely."""
        import threading

        breaker = CircuitBreaker(failure_threshold=5)
        failure_count = 0
        lock = threading.Lock()

        def failing_func():
            nonlocal failure_count
            with lock:
                failure_count += 1
            raise Exception("error")

        # Simulate concurrent failures
        threads = []
        for _ in range(10):
            thread = threading.Thread(
                target=lambda: breaker.call(failing_func) if not breaker.is_open else None
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Circuit should be open after threshold failures
        assert breaker.is_open


class TestIntegration:
    """Integration tests for circuit breaker."""

    def test_full_lifecycle(self):
        """Test full circuit breaker lifecycle."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.1,
            success_threshold=2,
        )

        # Phase 1: Closed -> Open
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("error")))

        assert breaker.is_open

        # Phase 2: Open (rejects calls)
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "success")

        # Phase 3: Open -> Half-Open
        time.sleep(0.15)
        mock_func = Mock(return_value="success")
        breaker.call(mock_func)
        assert breaker.is_half_open

        # Phase 4: Half-Open -> Closed
        breaker.call(mock_func)  # Second success
        assert breaker.is_closed

        # Phase 5: Normal operation
        result = breaker.call(mock_func)
        assert result == "success"

    def test_realistic_service_protection(self):
        """Test realistic scenario protecting a flaky service."""
        call_count = 0

        breaker = CircuitBreaker(
            name="external_api",
            failure_threshold=3,
            recovery_timeout=0.1,
        )

        @breaker.protect
        def call_external_api():
            nonlocal call_count
            call_count += 1

            # First 5 calls fail (simulating service outage)
            if call_count <= 5:
                raise Exception("service unavailable")

            # Then service recovers
            return "success"

        # Fail 3 times - opens circuit
        for _ in range(3):
            with pytest.raises(Exception):
                call_external_api()

        assert breaker.is_open

        # Next 2 calls rejected immediately (circuit open)
        rejected_count = 0
        for _ in range(2):
            try:
                call_external_api()
            except CircuitBreakerOpenError:
                rejected_count += 1

        assert rejected_count == 2

        # Wait for recovery
        time.sleep(0.15)

        # Service has recovered, calls succeed
        result = call_external_api()
        assert result == "success"
        assert breaker.is_half_open or breaker.is_closed
