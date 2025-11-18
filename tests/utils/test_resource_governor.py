"""Tests for resource governance system.

v0.2.9: Comprehensive tests for unified resource management.
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock

from src.utils.resource_governor import (
    ResourceGovernor,
    ResourcePriority,
    ResourceRequest,
    ResourceReservation,
    ResourceUnavailableError,
    get_governor,
)


@pytest.fixture(autouse=True)
def reset_governor():
    """Reset singleton before each test."""
    ResourceGovernor.reset_instance()
    yield
    ResourceGovernor.reset_instance()


@pytest.fixture
def governor():
    """Create fresh governor instance for testing."""
    return ResourceGovernor(
        memory_limit_mb=1000,
        cpu_limit_percent=80.0,
        max_concurrent_ops=4,
        enable_gc=True,
    )


class TestResourceGovernorBasics:
    """Basic resource governor functionality tests."""

    def test_initialization(self, governor):
        """Test governor initializes with correct limits."""
        assert governor.memory_limit_mb == 1000
        assert governor.cpu_limit_percent == 80.0
        assert governor.max_concurrent_ops == 4
        assert governor.enable_gc is True
        assert len(governor.reservations) == 0

    def test_singleton_pattern(self):
        """Test singleton pattern works correctly."""
        gov1 = get_governor()
        gov2 = get_governor()
        assert gov1 is gov2

    def test_reset_singleton(self):
        """Test singleton can be reset."""
        gov1 = get_governor()
        ResourceGovernor.reset_instance()
        gov2 = get_governor()
        assert gov1 is not gov2


class TestResourceReservation:
    """Tests for resource reservation and release."""

    def test_simple_reservation(self, governor):
        """Test basic resource reservation."""
        granted = governor.request_resources(
            operation_id="op1",
            memory_mb=100,
            cpu_percent=10.0,
        )

        assert granted is True
        assert "op1" in governor.reservations
        assert governor.reservations["op1"].memory_mb == 100
        assert governor.reservations["op1"].cpu_percent == 10.0

    def test_release_resources(self, governor):
        """Test resource release."""
        governor.request_resources("op1", memory_mb=100, cpu_percent=10.0)
        assert "op1" in governor.reservations

        governor.release_resources("op1")
        assert "op1" not in governor.reservations

    def test_multiple_reservations(self, governor):
        """Test multiple concurrent reservations."""
        governor.request_resources("op1", memory_mb=100, cpu_percent=10.0)
        governor.request_resources("op2", memory_mb=200, cpu_percent=15.0)
        governor.request_resources("op3", memory_mb=150, cpu_percent=20.0)

        assert len(governor.reservations) == 3
        assert governor._total_reserved_memory() == 450
        assert governor._total_reserved_cpu() == 45.0

    def test_release_unknown_operation(self, governor):
        """Test releasing unknown operation logs warning."""
        # Should not raise, just log warning
        governor.release_resources("unknown")


class TestResourceLimits:
    """Tests for resource limit enforcement."""

    def test_memory_limit_enforcement(self, governor):
        """Test memory limit prevents over-allocation."""
        # Reserve most memory
        governor.request_resources("op1", memory_mb=900, cpu_percent=10.0)

        # Try to reserve more than available - should queue/timeout
        granted = governor.request_resources(
            "op2", memory_mb=200, cpu_percent=10.0, timeout=0.5
        )

        assert granted is False  # Should timeout

    def test_cpu_limit_enforcement(self, governor):
        """Test CPU limit prevents over-allocation."""
        # Reserve most CPU
        governor.request_resources("op1", memory_mb=100, cpu_percent=70.0)

        # Try to reserve more than available
        granted = governor.request_resources(
            "op2", memory_mb=100, cpu_percent=20.0, timeout=0.5
        )

        assert granted is False  # Should timeout

    def test_concurrent_ops_limit(self, governor):
        """Test concurrent operations limit."""
        # Fill all slots
        for i in range(4):
            granted = governor.request_resources(
                f"op{i}", memory_mb=100, cpu_percent=10.0
            )
            assert granted is True

        # Try one more - should be queued/timeout
        granted = governor.request_resources(
            "op5", memory_mb=100, cpu_percent=10.0, timeout=0.5
        )

        assert granted is False


class TestPriorityQueuing:
    """Tests for priority-based resource queuing."""

    def test_high_priority_first(self, governor):
        """Test high priority requests processed first."""
        # Fill resources
        governor.request_resources("op1", memory_mb=1000, cpu_percent=10.0)

        # Queue two requests: low priority then high priority
        results = {}

        def low_priority():
            results["low"] = governor.request_resources(
                "op_low",
                memory_mb=100,
                cpu_percent=10.0,
                priority=ResourcePriority.LOW,
                timeout=2.0,
            )

        def high_priority():
            time.sleep(0.1)  # Start after low priority
            results["high"] = governor.request_resources(
                "op_high",
                memory_mb=100,
                cpu_percent=10.0,
                priority=ResourcePriority.HIGH,
                timeout=2.0,
            )

        t1 = threading.Thread(target=low_priority)
        t2 = threading.Thread(target=high_priority)

        t1.start()
        t2.start()

        time.sleep(0.5)

        # Release resources - high priority should get them
        governor.release_resources("op1")

        t1.join(timeout=3.0)
        t2.join(timeout=3.0)

        # High priority should succeed (processed first)
        assert results.get("high") is True


class TestContextManager:
    """Tests for context manager interface."""

    def test_context_manager_reserves_and_releases(self, governor):
        """Test context manager properly reserves and releases."""
        assert len(governor.reservations) == 0

        with governor.reserve("op1", memory_mb=100, cpu_percent=10.0):
            assert "op1" in governor.reservations
            assert len(governor.reservations) == 1

        # Should be released after context
        assert "op1" not in governor.reservations
        assert len(governor.reservations) == 0

    def test_context_manager_exception_handling(self, governor):
        """Test context manager releases resources even on exception."""
        assert len(governor.reservations) == 0

        try:
            with governor.reserve("op1", memory_mb=100, cpu_percent=10.0):
                assert "op1" in governor.reservations
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still be released
        assert "op1" not in governor.reservations

    def test_context_manager_timeout(self, governor):
        """Test context manager raises on timeout."""
        # Fill resources
        governor.request_resources("op1", memory_mb=1000, cpu_percent=10.0)

        # Try to reserve with timeout
        with pytest.raises(ResourceUnavailableError) as exc_info:
            with governor.reserve(
                "op2", memory_mb=200, cpu_percent=10.0, timeout=0.5
            ):
                pass

        assert "timed out" in str(exc_info.value)


class TestGarbageCollection:
    """Tests for automatic garbage collection."""

    @patch('gc.collect')
    def test_gc_triggered_on_memory_pressure(self, mock_gc, governor):
        """Test garbage collection triggered when memory constrained."""
        mock_gc.return_value = 100  # Objects collected

        # Fill memory
        governor.request_resources("op1", memory_mb=950, cpu_percent=10.0)

        # This should trigger GC before queuing
        governor.request_resources("op2", memory_mb=100, cpu_percent=10.0, timeout=0.5)

        # Verify GC was called
        assert mock_gc.called
        assert governor.stats["gc_triggers"] > 0

    def test_gc_disabled(self):
        """Test GC can be disabled."""
        gov = ResourceGovernor(
            memory_limit_mb=1000,
            cpu_limit_percent=80.0,
            max_concurrent_ops=4,
            enable_gc=False,
        )

        with patch('gc.collect') as mock_gc:
            # Fill memory
            gov.request_resources("op1", memory_mb=950, cpu_percent=10.0)

            # This should NOT trigger GC (disabled)
            gov.request_resources("op2", memory_mb=100, cpu_percent=10.0, timeout=0.5)

            assert not mock_gc.called


class TestStatistics:
    """Tests for statistics tracking."""

    def test_stats_tracking(self, governor):
        """Test statistics are tracked correctly."""
        # Make some requests
        governor.request_resources("op1", memory_mb=100, cpu_percent=10.0)
        governor.request_resources("op2", memory_mb=200, cpu_percent=20.0)

        # Release one
        governor.release_resources("op1")

        stats = governor.get_stats()

        assert stats["total_requests"] == 2
        assert stats["fulfilled_requests"] == 2
        assert stats["active_reservations"] == 1
        assert stats["reserved_memory_mb"] == 200
        assert stats["reserved_cpu_percent"] == 20.0

    def test_stats_timeout_tracking(self, governor):
        """Test timeouts tracked in stats."""
        # Fill resources
        governor.request_resources("op1", memory_mb=1000, cpu_percent=10.0)

        # Try to get resources with timeout
        governor.request_resources("op2", memory_mb=200, cpu_percent=10.0, timeout=0.2)

        stats = governor.get_stats()

        assert stats["rejected_requests"] >= 1


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_requests(self, governor):
        """Test concurrent requests from multiple threads."""
        results = []
        lock = threading.Lock()

        def make_request(op_id):
            granted = governor.request_resources(
                f"op_{op_id}",
                memory_mb=200,
                cpu_percent=15.0,
                timeout=2.0,
            )
            with lock:
                results.append((op_id, granted))

            if granted:
                time.sleep(0.1)
                governor.release_resources(f"op_{op_id}")

        # Start 8 threads (more than max_concurrent_ops=4)
        threads = [threading.Thread(target=make_request, args=(i,)) for i in range(8)]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=5.0)

        # All should eventually succeed
        granted_count = sum(1 for _, granted in results if granted)
        assert granted_count == 8

    def test_no_race_conditions(self, governor):
        """Test no race conditions in reservation tracking."""
        def reserve_and_release(op_id):
            for i in range(10):
                with governor.reserve(f"op_{op_id}_{i}", memory_mb=50, cpu_percent=5.0):
                    time.sleep(0.01)

        threads = [threading.Thread(target=reserve_and_release, args=(i,)) for i in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=10.0)

        # All reservations should be released
        assert len(governor.reservations) == 0


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_zero_resources_requested(self, governor):
        """Test requesting zero resources."""
        granted = governor.request_resources("op1", memory_mb=0, cpu_percent=0.0)
        assert granted is True

    def test_exact_limit_match(self, governor):
        """Test request exactly matching limit."""
        granted = governor.request_resources("op1", memory_mb=1000, cpu_percent=80.0)
        assert granted is True

    def test_duplicate_operation_id(self, governor):
        """Test same operation ID requested twice."""
        governor.request_resources("op1", memory_mb=100, cpu_percent=10.0)

        # Second request with same ID should also succeed
        # (different operations, same ID - not ideal but should work)
        granted = governor.request_resources("op1", memory_mb=100, cpu_percent=10.0)
        assert granted is True

    def test_repr_method(self, governor):
        """Test string representation."""
        governor.request_resources("op1", memory_mb=100, cpu_percent=10.0)

        repr_str = repr(governor)

        assert "ResourceGovernor" in repr_str
        assert "100/1000MB" in repr_str
        assert "10.0/80.0%" in repr_str
        assert "1/4" in repr_str


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_batch_processing_scenario(self, governor):
        """Test typical batch processing workload."""
        # Simulate batch processing with varying resource needs
        batch_sizes = [100, 200, 150, 300, 250]

        for i, size in enumerate(batch_sizes):
            with governor.reserve(
                f"batch_{i}",
                memory_mb=size,
                cpu_percent=size / 10.0,
                priority=ResourcePriority.NORMAL,
            ):
                # Simulate processing
                time.sleep(0.05)

        # All batches should complete successfully
        assert governor.stats["fulfilled_requests"] == len(batch_sizes)

    def test_mixed_priority_workload(self, governor):
        """Test workload with mixed priorities."""
        # Start low priority background task
        def background_task():
            with governor.reserve(
                "background",
                memory_mb=800,
                cpu_percent=20.0,
                priority=ResourcePriority.LOW,
                timeout=3.0,
            ):
                time.sleep(2.0)

        bg_thread = threading.Thread(target=background_task)
        bg_thread.start()

        time.sleep(0.2)  # Let background task start

        # High priority task should interrupt
        def high_priority_task():
            with governor.reserve(
                "important",
                memory_mb=500,
                cpu_percent=30.0,
                priority=ResourcePriority.HIGH,
                timeout=2.0,
            ):
                time.sleep(0.5)

        hp_thread = threading.Thread(target=high_priority_task)
        hp_thread.start()

        hp_thread.join(timeout=5.0)
        bg_thread.join(timeout=5.0)

        # Both should complete
        stats = governor.get_stats()
        assert stats["fulfilled_requests"] >= 2
