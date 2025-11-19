"""Tests for graceful degradation utilities.

v0.2.9: Tests for fallback strategies and fault tolerance.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.utils.graceful_degradation import (
    ServiceUnavailableError,
    FallbackStrategy,
    with_fallback,
    DegradedMode,
    safe_execute,
    FallbackChain,
    adaptive_batch_size,
    CircuitBreaker,
)


class TestFallbackStrategy:
    """Tests for FallbackStrategy class."""

    def test_primary_success(self):
        """Test successful primary execution."""
        primary = Mock(return_value="primary_result")
        fallback1 = Mock(return_value="fallback1_result")

        strategy = FallbackStrategy(
            primary=primary,
            fallbacks=[fallback1],
            name="test"
        )

        result = strategy.execute()

        assert result == "primary_result"
        primary.assert_called_once()
        fallback1.assert_not_called()

    def test_primary_fails_fallback_succeeds(self):
        """Test fallback when primary fails."""
        primary = Mock(side_effect=ValueError("Primary failed"))
        fallback1 = Mock(return_value="fallback1_result")

        strategy = FallbackStrategy(
            primary=primary,
            fallbacks=[fallback1],
            name="test"
        )

        result = strategy.execute()

        assert result == "fallback1_result"
        primary.assert_called_once()
        fallback1.assert_called_once()

    def test_multiple_fallbacks(self):
        """Test multiple fallback attempts."""
        primary = Mock(side_effect=ValueError("Primary failed"))
        fallback1 = Mock(side_effect=RuntimeError("Fallback 1 failed"))
        fallback2 = Mock(return_value="fallback2_result")

        strategy = FallbackStrategy(
            primary=primary,
            fallbacks=[fallback1, fallback2],
            name="test"
        )

        result = strategy.execute()

        assert result == "fallback2_result"
        fallback2.assert_called_once()

    def test_all_methods_fail(self):
        """Test ServiceUnavailableError when all methods fail."""
        primary = Mock(side_effect=ValueError("Primary failed"))
        fallback1 = Mock(side_effect=RuntimeError("Fallback 1 failed"))
        fallback2 = Mock(side_effect=IOError("Fallback 2 failed"))

        strategy = FallbackStrategy(
            primary=primary,
            fallbacks=[fallback1, fallback2],
            name="test"
        )

        with pytest.raises(ServiceUnavailableError):
            strategy.execute()


class TestWithFallbackDecorator:
    """Tests for with_fallback decorator."""

    def test_function_succeeds(self):
        """Test decorated function that succeeds."""
        @with_fallback(fallback_value="fallback")
        def func():
            return "success"

        result = func()
        assert result == "success"

    def test_function_fails_uses_fallback_value(self):
        """Test fallback value on failure."""
        @with_fallback(fallback_value="fallback", exceptions=(ValueError,))
        def func():
            raise ValueError("Failed")

        result = func()
        assert result == "fallback"

    def test_function_fails_uses_fallback_func(self):
        """Test fallback function on failure."""
        def fallback_impl():
            return "from_fallback_func"

        @with_fallback(fallback_func=fallback_impl, exceptions=(ValueError,))
        def func():
            raise ValueError("Failed")

        result = func()
        assert result == "from_fallback_func"

    def test_specific_exceptions_only(self):
        """Test that only specified exceptions trigger fallback."""
        @with_fallback(fallback_value="fallback", exceptions=(ValueError,))
        def func():
            raise RuntimeError("Not caught")

        with pytest.raises(RuntimeError):
            func()

    def test_fallback_func_with_args(self):
        """Test fallback function receives same arguments."""
        def fallback_impl(x, y):
            return x + y + 10

        @with_fallback(fallback_func=fallback_impl)
        def func(x, y):
            raise ValueError("Failed")

        result = func(5, 3)
        assert result == 18  # 5 + 3 + 10

    def test_fallback_func_also_fails(self):
        """Test error when fallback function also fails."""
        def fallback_impl():
            raise RuntimeError("Fallback also failed")

        @with_fallback(fallback_func=fallback_impl)
        def func():
            raise ValueError("Primary failed")

        with pytest.raises(RuntimeError, match="Fallback also failed"):
            func()


class TestDegradedMode:
    """Tests for DegradedMode context manager."""

    def setup_method(self):
        """Reset degraded modes before each test."""
        DegradedMode._active_modes.clear()

    def test_enter_degraded_mode(self):
        """Test entering degraded mode."""
        assert not DegradedMode.is_active("test_mode")

        with DegradedMode("test_mode"):
            assert DegradedMode.is_active("test_mode")

        assert not DegradedMode.is_active("test_mode")

    def test_multiple_modes(self):
        """Test multiple degraded modes simultaneously."""
        with DegradedMode("mode1"):
            with DegradedMode("mode2"):
                assert DegradedMode.is_active("mode1")
                assert DegradedMode.is_active("mode2")
                assert len(DegradedMode.get_active_modes()) == 2

    def test_nested_same_mode(self):
        """Test nested same degraded mode."""
        with DegradedMode("test_mode"):
            with DegradedMode("test_mode"):
                assert DegradedMode.is_active("test_mode")

    def test_get_active_modes(self):
        """Test getting list of active modes."""
        with DegradedMode("mode1"):
            with DegradedMode("mode2"):
                active = DegradedMode.get_active_modes()
                assert "mode1" in active
                assert "mode2" in active

    def test_degraded_mode_with_reason(self):
        """Test degraded mode with reason."""
        with DegradedMode("test_mode", reason="high memory usage"):
            assert DegradedMode.is_active("test_mode")


class TestSafeExecute:
    """Tests for safe_execute function."""

    def test_successful_execution(self):
        """Test successful function execution."""
        result = safe_execute(
            lambda: "success",
            default="fallback",
            operation_name="test"
        )
        assert result == "success"

    def test_failed_execution_returns_default(self):
        """Test default returned on failure."""
        result = safe_execute(
            lambda: 1 / 0,  # Raises ZeroDivisionError
            default="fallback",
            operation_name="test"
        )
        assert result == "fallback"

    def test_no_logging_on_failure(self):
        """Test disabling failure logging."""
        result = safe_execute(
            lambda: 1 / 0,
            default="fallback",
            log_failure=False
        )
        assert result == "fallback"

    def test_default_can_be_any_type(self):
        """Test default value of any type."""
        result = safe_execute(
            lambda: 1 / 0,
            default=[],
            operation_name="list_op"
        )
        assert result == []

        result = safe_execute(
            lambda: 1 / 0,
            default=None,
            operation_name="none_op"
        )
        assert result is None


class TestFallbackChain:
    """Tests for FallbackChain class."""

    def test_first_strategy_succeeds(self):
        """Test success on first strategy."""
        chain = FallbackChain("test")
        chain.add(lambda: "strategy1")
        chain.add(lambda: "strategy2")

        result = chain.execute()
        assert result == "strategy1"

    def test_fallback_to_second_strategy(self):
        """Test fallback to second strategy."""
        chain = FallbackChain("test")
        chain.add(lambda: 1 / 0, name="divzero")  # Fails
        chain.add(lambda: "strategy2", name="success")

        result = chain.execute()
        assert result == "strategy2"

    def test_all_strategies_fail(self):
        """Test error when all strategies fail."""
        chain = FallbackChain("test")
        chain.add(lambda: 1 / 0)
        chain.add(lambda: [][999])  # IndexError

        with pytest.raises(ServiceUnavailableError):
            chain.execute()

    def test_chain_with_arguments(self):
        """Test passing arguments through chain."""
        chain = FallbackChain("test")
        chain.add(lambda x, y: x / y, name="divide")  # Fails with y=0
        chain.add(lambda x, y: x + y, name="add")

        result = chain.execute(10, 0)
        assert result == 10  # Falls back to addition

    def test_specific_exceptions(self):
        """Test catching specific exception types."""
        chain = FallbackChain("test")
        chain.add(
            lambda: 1 / 0,
            name="divzero",
            exceptions=(ZeroDivisionError,)
        )
        chain.add(lambda: "success", name="fallback")

        result = chain.execute()
        assert result == "success"

    def test_chaining_add_calls(self):
        """Test method chaining."""
        chain = (FallbackChain("test")
                 .add(lambda: 1 / 0)
                 .add(lambda: "success"))

        result = chain.execute()
        assert result == "success"


class TestAdaptiveBatchSize:
    """Tests for adaptive_batch_size function."""

    def test_increase_on_success(self):
        """Test batch size increases on success."""
        new_size = adaptive_batch_size(100, success=True)
        assert new_size > 100

    def test_decrease_on_failure(self):
        """Test batch size decreases on failure."""
        new_size = adaptive_batch_size(100, success=False)
        assert new_size < 100

    def test_respects_min_size(self):
        """Test minimum batch size limit."""
        new_size = adaptive_batch_size(10, success=False, min_size=5)
        assert new_size >= 5

    def test_respects_max_size(self):
        """Test maximum batch size limit."""
        new_size = adaptive_batch_size(900, success=True, max_size=1000)
        assert new_size <= 1000

    def test_custom_factors(self):
        """Test custom increase/decrease factors."""
        # Double on success
        new_size = adaptive_batch_size(
            100, success=True,
            increase_factor=2.0
        )
        assert new_size == 200

        # Halve on failure
        new_size = adaptive_batch_size(
            100, success=False,
            decrease_factor=0.5
        )
        assert new_size == 50

    def test_multiple_failures(self):
        """Test repeated failures reduce batch size."""
        size = 1000
        for _ in range(5):
            size = adaptive_batch_size(size, success=False)

        assert size < 100  # Significantly reduced

    def test_gradual_recovery(self):
        """Test gradual increase after failures."""
        size = 50  # Reduced due to failures
        for _ in range(3):
            size = adaptive_batch_size(size, success=True)

        assert size > 50  # Increased but gradual


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state_closed(self):
        """Test circuit starts in CLOSED state."""
        breaker = CircuitBreaker("test")
        assert not breaker.is_open()
        assert breaker.state == "CLOSED"

    def test_opens_after_threshold_failures(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker("test", failure_threshold=3)

        for _ in range(3):
            breaker.record_failure()

        assert breaker.is_open()
        assert breaker.state == "OPEN"

    def test_success_resets_failure_count(self):
        """Test success resets failure count."""
        breaker = CircuitBreaker("test", failure_threshold=3)

        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()  # Reset
        breaker.record_failure()

        assert not breaker.is_open()  # Only 1 failure since reset

    def test_recovery_timeout(self):
        """Test circuit moves to HALF_OPEN after timeout."""
        breaker = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open()

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should attempt recovery
        assert not breaker.is_open()
        assert breaker.state == "HALF_OPEN"

    def test_half_open_to_closed_on_success(self):
        """Test HALF_OPEN → CLOSED on success."""
        breaker = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)

        breaker.record_failure()
        breaker.record_failure()
        time.sleep(0.15)

        breaker.is_open()  # Moves to HALF_OPEN
        breaker.record_success()

        assert breaker.state == "CLOSED"

    def test_half_open_to_open_on_failure(self):
        """Test HALF_OPEN → OPEN on failure."""
        breaker = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)

        breaker.record_failure()
        time.sleep(0.15)

        breaker.is_open()  # Moves to HALF_OPEN
        breaker.record_failure()

        assert breaker.state == "OPEN"


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_retrieval_with_fallbacks(self):
        """Test retrieval with multiple fallback strategies."""
        # Simulate hybrid search with fallbacks
        def hybrid_search():
            raise RuntimeError("BM25 unavailable")

        def dense_search():
            raise RuntimeError("Vector store down")

        def cache_search():
            return ["cached_result"]

        strategy = FallbackStrategy(
            primary=hybrid_search,
            fallbacks=[dense_search, cache_search],
            name="search"
        )

        result = strategy.execute()
        assert result == ["cached_result"]

    def test_memory_pressure_degradation(self):
        """Test graceful degradation under memory pressure."""
        batch_size = 500

        # Simulate failures due to memory pressure
        with DegradedMode("memory_pressure"):
            # Adaptively reduce batch size
            for _ in range(3):
                batch_size = adaptive_batch_size(batch_size, success=False)

            # Should have significantly reduced
            assert batch_size < 100
            assert DegradedMode.is_active("memory_pressure")

    def test_circuit_breaker_protects_service(self):
        """Test circuit breaker prevents repeated calls to failing service."""
        breaker = CircuitBreaker("external_api", failure_threshold=3)
        call_count = 0

        def call_api():
            nonlocal call_count
            if not breaker.is_open():
                call_count += 1
                raise RuntimeError("API down")

        # Make calls until circuit opens
        for _ in range(5):
            try:
                call_api()
                breaker.record_success()
            except RuntimeError:
                breaker.record_failure()

        # Circuit should be open, preventing further calls
        assert breaker.is_open()
        assert call_count == 3  # Only called until threshold

    def test_fallback_chain_for_data_loading(self):
        """Test fallback chain for data loading."""
        chain = FallbackChain("load_data")

        # Try database (fails)
        chain.add(
            lambda: [][0],  # IndexError
            name="database",
            exceptions=(IndexError,)
        )

        # Try cache (fails)
        chain.add(
            lambda: {}["missing"],  # KeyError
            name="cache",
            exceptions=(KeyError,)
        )

        # Try default data (succeeds)
        chain.add(
            lambda: {"default": "data"},
            name="default"
        )

        result = chain.execute()
        assert result == {"default": "data"}

    def test_degraded_mode_with_adaptive_sizing(self):
        """Test combining degraded mode with adaptive batch sizing."""
        batch_size = 200
        failures = 0

        with DegradedMode("high_load", reason="peak traffic"):
            for _ in range(5):
                # Simulate intermittent failures
                success = failures < 2
                batch_size = adaptive_batch_size(batch_size, success=success)

                if not success:
                    failures += 1

            # Batch size should be reduced
            assert batch_size < 200
            assert DegradedMode.is_active("high_load")
