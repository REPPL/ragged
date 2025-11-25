"""Async tests for streaming response generation.

v0.6.5 OPTIMISE-005: Streaming Response Generation (Async)

NOTE: These async tests must be run separately from sync tests due to
pytest-asyncio event loop management limitations. Run with:
    pytest tests/generation/test_streaming_async.py

The tests pass correctly in isolation but hang when pytest attempts to
run them in the same session as sync tests.
"""

import pytest

from ragged.generation.streaming import StreamGenerator, StreamState


@pytest.mark.asyncio
class TestStreamGeneratorAsync:
    """Test suite for async streaming."""

    async def test_stream_tokens_async(self):
        """Test async token streaming."""
        generator = StreamGenerator()

        async def async_tokens():
            for token in ["Hello", " ", "world"]:
                yield token

        streamed = []
        async for token in generator.stream_tokens_async(async_tokens()):
            streamed.append(token)

        assert len(streamed) == 3
        assert streamed[0].token == "Hello"
        assert generator.state == StreamState.COMPLETED

    async def test_async_metrics(self):
        """Test async metrics tracking."""
        generator = StreamGenerator()

        async def async_tokens():
            for i in range(5):
                yield f"token{i}"

        async for _ in generator.stream_tokens_async(async_tokens()):
            pass

        metrics = generator.get_metrics()

        assert metrics["total_tokens"] == 5
        assert metrics["time_to_first_token"] is not None
