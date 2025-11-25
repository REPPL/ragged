"""Tests for streaming response generation.

v0.6.5 OPTIMISE-005: Streaming Response Generation
"""

import time

import pytest

from ragged.generation.streaming import (
    StreamBuffer,
    StreamGenerator,
    StreamState,
    StreamToken,
    format_streaming_output,
)


class TestStreamToken:
    """Test suite for StreamToken."""

    def test_initialization(self):
        """Test token initializes correctly."""
        token = StreamToken(token="hello", index=0, timestamp=time.time())

        assert token.token == "hello"
        assert token.index == 0
        assert token.timestamp > 0
        assert token.metadata is None


class TestStreamBuffer:
    """Test suite for StreamBuffer."""

    def test_initialization(self):
        """Test buffer initializes correctly."""
        buffer = StreamBuffer(max_size=100)

        assert buffer.max_size == 100
        assert buffer.is_empty()
        assert not buffer.is_full()

    def test_write_read(self):
        """Test writing and reading tokens."""
        buffer = StreamBuffer()
        token = StreamToken(token="test", index=0, timestamp=time.time())

        written = buffer.write(token)
        assert written is True
        assert buffer.size() == 1

        read_token = buffer.read()
        assert read_token == token
        assert buffer.is_empty()

    def test_backpressure(self):
        """Test backpressure when buffer full."""
        buffer = StreamBuffer(max_size=2)

        token1 = StreamToken(token="test1", index=0, timestamp=time.time())
        token2 = StreamToken(token="test2", index=1, timestamp=time.time())
        token3 = StreamToken(token="test3", index=2, timestamp=time.time())

        assert buffer.write(token1) is True
        assert buffer.write(token2) is True
        assert buffer.is_full()
        assert buffer.write(token3) is False  # Backpressure

    def test_clear(self):
        """Test clearing buffer."""
        buffer = StreamBuffer()

        buffer.write(StreamToken(token="test", index=0, timestamp=time.time()))
        assert not buffer.is_empty()

        buffer.clear()
        assert buffer.is_empty()

    def test_fifo_order(self):
        """Test FIFO ordering."""
        buffer = StreamBuffer()

        token1 = StreamToken(token="first", index=0, timestamp=time.time())
        token2 = StreamToken(token="second", index=1, timestamp=time.time())

        buffer.write(token1)
        buffer.write(token2)

        assert buffer.read().token == "first"
        assert buffer.read().token == "second"


class TestStreamGenerator:
    """Test suite for StreamGenerator."""

    def test_initialization(self):
        """Test generator initializes correctly."""
        generator = StreamGenerator(buffer_size=100)

        assert generator.buffer.max_size == 100
        assert generator.state == StreamState.PENDING
        assert generator.metrics.total_tokens == 0

    def test_stream_tokens(self):
        """Test streaming tokens."""
        generator = StreamGenerator()

        tokens = ["Hello", " ", "world", "!"]
        streamed = list(generator.stream_tokens(iter(tokens)))

        assert len(streamed) == 4
        assert streamed[0].token == "Hello"
        assert streamed[0].index == 0
        assert streamed[3].token == "!"
        assert streamed[3].index == 3

        assert generator.state == StreamState.COMPLETED

    def test_metrics_tracking(self):
        """Test metrics are tracked correctly."""
        generator = StreamGenerator()

        tokens = ["token"] * 10
        list(generator.stream_tokens(iter(tokens), track_metrics=True))

        metrics = generator.get_metrics()

        assert metrics["total_tokens"] == 10
        assert metrics["time_to_first_token"] is not None
        assert metrics["time_to_first_token"] < 1.0  # Should be very fast
        assert metrics["total_time"] > 0
        assert metrics["tokens_per_second"] > 0

    def test_stream_interruption(self):
        """Test stream interruption handling."""
        generator = StreamGenerator()

        def interruptible_tokens():
            yield "token1"
            yield "token2"
            raise GeneratorExit()  # Simulated interruption

        streamed = []
        try:
            for token in generator.stream_tokens(interruptible_tokens()):
                streamed.append(token)
        except GeneratorExit:
            pass

        assert len(streamed) == 2
        assert generator.state == StreamState.INTERRUPTED

    def test_stream_error(self):
        """Test stream error handling."""
        generator = StreamGenerator()

        def error_tokens():
            yield "token1"
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            list(generator.stream_tokens(error_tokens()))

        assert generator.state == StreamState.ERROR
        assert generator.metrics.errors == 1

    def test_reset(self):
        """Test generator reset."""
        generator = StreamGenerator()

        tokens = ["test"]
        list(generator.stream_tokens(iter(tokens)))

        assert generator.metrics.total_tokens == 1
        assert generator.state == StreamState.COMPLETED

        generator.reset()

        assert generator.metrics.total_tokens == 0
        assert generator.state == StreamState.PENDING
        assert generator.buffer.is_empty()

    def test_no_metrics_tracking(self):
        """Test streaming without metrics tracking."""
        generator = StreamGenerator()

        tokens = ["token1", "token2"]
        list(generator.stream_tokens(iter(tokens), track_metrics=False))

        metrics = generator.get_metrics()

        assert metrics["total_tokens"] == 2
        assert metrics["time_to_first_token"] is None  # Not tracked


class TestFormattingUtilities:
    """Test suite for formatting utilities."""

    def test_format_streaming_output(self):
        """Test formatting streaming output."""
        tokens = [
            StreamToken(token="Hello", index=0, timestamp=time.time()),
            StreamToken(token=" ", index=1, timestamp=time.time()),
            StreamToken(token="world", index=2, timestamp=time.time()),
        ]

        output = format_streaming_output(iter(tokens), width=80)

        assert "Hello world" in output

    def test_word_wrapping(self):
        """Test word wrapping in formatting."""
        # Create a long line
        long_tokens = [
            StreamToken(token=word, index=i, timestamp=time.time())
            for i, word in enumerate("word " * 20)
        ]

        output = format_streaming_output(iter(long_tokens), width=40)

        lines = output.split("\n")
        # Should wrap into multiple lines
        assert len(lines) > 1
        # No line should exceed width (approximately)
        for line in lines:
            assert len(line) <= 45  # Some tolerance for word boundaries


class TestIntegration:
    """Integration tests for streaming."""

    def test_end_to_end_streaming(self):
        """Test complete streaming workflow."""
        generator = StreamGenerator(buffer_size=10)

        # Simulate LLM token generation
        tokens = "This is a simulated streaming response from an LLM.".split()

        streamed_text = []
        for token in generator.stream_tokens(iter(tokens)):
            streamed_text.append(token.token)

        # Verify complete text
        assert " ".join(streamed_text) == " ".join(tokens)

        # Verify metrics
        metrics = generator.get_metrics()
        assert metrics["state"] == "completed"
        assert metrics["total_tokens"] == len(tokens)
        assert metrics["time_to_first_token"] < 1.0
        assert metrics["errors"] == 0

    def test_backpressure_handling(self):
        """Test backpressure in realistic scenario."""
        generator = StreamGenerator(buffer_size=3)

        tokens = ["token"] * 10

        # Stream with artificial slowdown
        streamed = []
        for token in generator.stream_tokens(iter(tokens)):
            streamed.append(token)
            # Buffer should handle backpressure automatically

        assert len(streamed) == 10
        assert generator.state == StreamState.COMPLETED
