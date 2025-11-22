"""Tests for debug logging functionality.

v0.3.8: Test debug logger and pipeline visualisation.
"""

import time
from unittest.mock import Mock

import pytest

from src.cli.debug import (
    DebugLogger,
    DebugStep,
    DebugStepContext,
    create_debug_logger,
)


class TestDebugStep:
    """Test DebugStep dataclass."""

    def test_debug_step_creation(self):
        """Test creating a debug step."""
        step = DebugStep(name="Test Step", details={"key": "value"})

        assert step.name == "Test Step"
        assert step.details == {"key": "value"}
        assert step.start_time > 0
        assert step.end_time is None

    def test_debug_step_duration(self):
        """Test step duration calculation."""
        step = DebugStep(name="Test Step")
        time.sleep(0.01)  # 10ms

        duration = step.duration_ms
        assert duration >= 10  # At least 10ms

    def test_debug_step_complete(self):
        """Test completing a step."""
        step = DebugStep(name="Test Step")
        assert step.end_time is None

        step.complete()
        assert step.end_time is not None
        assert step.end_time > step.start_time

    def test_debug_step_duration_after_complete(self):
        """Test duration is fixed after completion."""
        step = DebugStep(name="Test Step")
        time.sleep(0.01)
        step.complete()

        duration1 = step.duration_ms
        time.sleep(0.01)
        duration2 = step.duration_ms

        # Duration should be the same after completion
        assert abs(duration1 - duration2) < 1  # Less than 1ms difference


class TestDebugLogger:
    """Test DebugLogger class."""

    def test_logger_init_disabled(self):
        """Test logger initialisation when disabled."""
        logger = DebugLogger(enabled=False)

        assert logger.enabled is False
        assert len(logger.steps) == 0

    def test_logger_init_enabled(self):
        """Test logger initialisation when enabled."""
        logger = DebugLogger(enabled=True)

        assert logger.enabled is True
        assert len(logger.steps) == 0

    def test_start_step(self):
        """Test starting a debug step."""
        logger = DebugLogger(enabled=True)
        logger.start_step("Step 1", key="value")

        assert len(logger.steps) == 1
        assert logger.steps[0].name == "Step 1"
        assert logger.steps[0].details == {"key": "value"}

    def test_start_step_when_disabled(self):
        """Test starting a step when logger is disabled."""
        logger = DebugLogger(enabled=False)
        logger.start_step("Step 1")

        # Should not record steps when disabled
        assert len(logger.steps) == 0

    def test_add_detail(self):
        """Test adding details to current step."""
        logger = DebugLogger(enabled=True)
        logger.start_step("Step 1")
        logger.add_detail("key1", "value1")
        logger.add_detail("key2", "value2")

        assert logger.steps[0].details["key1"] == "value1"
        assert logger.steps[0].details["key2"] == "value2"

    def test_add_detail_when_disabled(self):
        """Test adding details when logger is disabled."""
        logger = DebugLogger(enabled=False)
        logger.start_step("Step 1")
        logger.add_detail("key", "value")

        # Should do nothing when disabled
        assert len(logger.steps) == 0

    def test_complete_step(self):
        """Test completing a step."""
        logger = DebugLogger(enabled=True)
        logger.start_step("Step 1")
        time.sleep(0.01)
        logger.complete_step()

        assert logger.steps[0].end_time is not None

    def test_multiple_steps(self):
        """Test multiple debug steps."""
        logger = DebugLogger(enabled=True)

        logger.start_step("Step 1", step="first")
        logger.add_detail("data", "value1")
        logger.complete_step()

        logger.start_step("Step 2", step="second")
        logger.add_detail("data", "value2")
        logger.complete_step()

        logger.start_step("Step 3", step="third")
        logger.complete_step()

        assert len(logger.steps) == 3
        assert logger.steps[0].name == "Step 1"
        assert logger.steps[1].name == "Step 2"
        assert logger.steps[2].name == "Step 3"

    def test_auto_complete_previous_step(self):
        """Test that starting new step completes previous one."""
        logger = DebugLogger(enabled=True)

        logger.start_step("Step 1")
        assert logger.steps[0].end_time is None

        logger.start_step("Step 2")

        # Step 1 should be auto-completed
        assert logger.steps[0].end_time is not None
        assert logger.steps[1].end_time is None

    def test_log_step(self):
        """Test logging a complete step (start and complete)."""
        logger = DebugLogger(enabled=True)
        logger.log_step("Complete Step", key="value")

        assert len(logger.steps) == 1
        assert logger.steps[0].name == "Complete Step"
        assert logger.steps[0].details["key"] == "value"
        assert logger.steps[0].end_time is not None

    def test_total_duration(self):
        """Test total pipeline duration calculation."""
        logger = DebugLogger(enabled=True)

        logger.start_step("Step 1")
        time.sleep(0.01)
        logger.complete_step()

        logger.start_step("Step 2")
        time.sleep(0.01)
        logger.complete_step()

        duration = logger.total_duration_ms
        assert duration >= 20  # At least 20ms (two 10ms steps)

    def test_total_duration_empty(self):
        """Test total duration with no steps."""
        logger = DebugLogger(enabled=True)

        assert logger.total_duration_ms == 0.0

    def test_render_output(self):
        """Test rendering debug output."""
        logger = DebugLogger(enabled=True)

        logger.start_step("Query Preprocessing", original="test query")
        logger.add_detail("normalised", "test query")
        logger.complete_step()

        logger.start_step("Query Embedding", model="all-MiniLM-L6-v2")
        logger.add_detail("dimensions", 384)
        logger.complete_step()

        output = logger.render()

        assert "Debug Mode: Query Pipeline" in output
        assert "[Step 1/2] Query Preprocessing" in output
        assert "[Step 2/2] Query Embedding" in output
        assert "original: test query" in output
        assert "model: all-MiniLM-L6-v2" in output
        assert "Total Pipeline Duration" in output

    def test_render_empty(self):
        """Test rendering with no steps."""
        logger = DebugLogger(enabled=True)

        output = logger.render()
        assert "No debug steps recorded" in output

    def test_render_verbose(self):
        """Test verbose rendering."""
        logger = DebugLogger(enabled=True)

        logger.start_step("Step 1")
        for i in range(10):
            logger.add_detail(f"key{i}", f"value{i}")
        logger.complete_step()

        # Non-verbose should summarize
        output_brief = logger.render(verbose=False)
        assert "10 entries" in output_brief or "key0" in output_brief

        # Verbose should show all
        output_verbose = logger.render(verbose=True)
        assert "key0" in output_verbose
        assert "key9" in output_verbose

    def test_render_summary(self):
        """Test rendering summary output."""
        logger = DebugLogger(enabled=True)

        logger.log_step("Step 1", key="value1")
        logger.log_step("Step 2", key="value2")

        summary = logger.render_summary()

        assert "Pipeline Summary" in summary
        assert "1. Step 1:" in summary
        assert "2. Step 2:" in summary
        assert "Total:" in summary

    def test_to_dict(self):
        """Test converting to dictionary."""
        logger = DebugLogger(enabled=True)

        logger.start_step("Step 1", key="value")
        logger.complete_step()

        data = logger.to_dict()

        assert data["enabled"] is True
        assert len(data["steps"]) == 1
        assert data["steps"][0]["name"] == "Step 1"
        assert data["steps"][0]["details"]["key"] == "value"
        assert "duration_ms" in data["steps"][0]
        assert "total_duration_ms" in data

    def test_clear(self):
        """Test clearing debug steps."""
        logger = DebugLogger(enabled=True)

        logger.log_step("Step 1")
        logger.log_step("Step 2")

        assert len(logger.steps) == 2

        logger.clear()

        assert len(logger.steps) == 0

    def test_format_different_value_types(self):
        """Test rendering different value types."""
        logger = DebugLogger(enabled=True)

        logger.start_step(
            "Test Step",
            float_value=3.14159,
            list_value=[1, 2, 3],
            dict_value={"a": 1, "b": 2},
            string_value="test",
        )
        logger.complete_step()

        output = logger.render()

        # Float should be formatted
        assert "3.1416" in output or "3.14159" in output

        # List should show count
        assert "3 items" in output

        # Dict should show count
        assert "2 entries" in output

        # String should show as-is
        assert "test" in output


class TestDebugStepContext:
    """Test DebugStepContext context manager."""

    def test_context_manager_success(self):
        """Test context manager with successful execution."""
        logger = DebugLogger(enabled=True)

        with DebugStepContext(logger, "Test Step", key="value") as step:
            step.add_detail("result", "success")

        assert len(logger.steps) == 1
        assert logger.steps[0].name == "Test Step"
        assert logger.steps[0].details["key"] == "value"
        assert logger.steps[0].details["result"] == "success"
        assert logger.steps[0].end_time is not None

    def test_context_manager_exception(self):
        """Test context manager with exception."""
        logger = DebugLogger(enabled=True)

        try:
            with DebugStepContext(logger, "Test Step") as step:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Step should still be recorded with error details
        assert len(logger.steps) == 1
        assert logger.steps[0].details["error"] == "Test error"
        assert logger.steps[0].details["error_type"] == "ValueError"
        assert logger.steps[0].end_time is not None


class TestConvenienceFunction:
    """Test convenience functions."""

    def test_create_debug_logger(self):
        """Test create_debug_logger function."""
        logger = create_debug_logger(enabled=True)

        assert isinstance(logger, DebugLogger)
        assert logger.enabled is True

    def test_create_debug_logger_disabled(self):
        """Test creating disabled logger."""
        logger = create_debug_logger(enabled=False)

        assert isinstance(logger, DebugLogger)
        assert logger.enabled is False
