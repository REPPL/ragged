"""Streaming response generation for real-time feedback.

Provides token-by-token streaming from LLMs with proper backpressure
handling, error recovery, and progress indication.

v0.6.5 OPTIMISE-005: Streaming Response Generation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Iterator, Optional

logger = logging.getLogger(__name__)


class StreamState(str, Enum):
    """Stream state tracking."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"
    INTERRUPTED = "interrupted"


@dataclass
class StreamToken:
    """Single token in a stream."""

    token: str
    index: int
    timestamp: float
    metadata: Optional[dict] = None


@dataclass
class StreamMetrics:
    """Metrics for stream performance."""

    time_to_first_token: Optional[float] = None
    total_tokens: int = 0
    total_time: float = 0.0
    tokens_per_second: float = 0.0
    errors: int = 0


class StreamBuffer:
    """Buffer for managing streaming tokens with backpressure.

    Implements a simple buffer to handle token streaming with
    configurable size limits and backpressure signaling.
    """

    def __init__(self, max_size: int = 1000):
        """Initialize stream buffer.

        Args:
            max_size: Maximum buffer size before backpressure
        """
        self.max_size = max_size
        self.buffer: list[StreamToken] = []
        self.total_written = 0
        self.total_read = 0

    def write(self, token: StreamToken) -> bool:
        """Write token to buffer.

        Args:
            token: Token to write

        Returns:
            True if written, False if buffer full (backpressure)
        """
        if len(self.buffer) >= self.max_size:
            logger.warning("Stream buffer full, applying backpressure")
            return False

        self.buffer.append(token)
        self.total_written += 1
        return True

    def read(self) -> Optional[StreamToken]:
        """Read token from buffer.

        Returns:
            Next token or None if buffer empty
        """
        if not self.buffer:
            return None

        token = self.buffer.pop(0)
        self.total_read += 1
        return token

    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.buffer) >= self.max_size

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0

    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)

    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()


class StreamGenerator:
    """Generate streaming responses with proper handling.

    Wraps LLM generation to provide token-by-token streaming
    with error recovery, metrics tracking, and state management.
    """

    def __init__(self, buffer_size: int = 1000):
        """Initialize stream generator.

        Args:
            buffer_size: Maximum buffer size
        """
        self.buffer = StreamBuffer(max_size=buffer_size)
        self.state = StreamState.PENDING
        self.metrics = StreamMetrics()

    def stream_tokens(
        self, tokens: Iterator[str], track_metrics: bool = True
    ) -> Iterator[StreamToken]:
        """Stream tokens with metrics tracking.

        Args:
            tokens: Iterator of token strings
            track_metrics: Whether to track performance metrics

        Yields:
            StreamToken objects
        """
        import time

        self.state = StreamState.STREAMING
        start_time = time.time()
        first_token_time = None

        try:
            for index, token in enumerate(tokens):
                if first_token_time is None and track_metrics:
                    first_token_time = time.time()
                    self.metrics.time_to_first_token = first_token_time - start_time

                stream_token = StreamToken(
                    token=token, index=index, timestamp=time.time()
                )

                # Handle backpressure
                while not self.buffer.write(stream_token):
                    logger.debug("Buffer full, waiting for consumption")
                    time.sleep(0.01)  # Brief pause for backpressure

                self.metrics.total_tokens += 1

                yield stream_token

            self.state = StreamState.COMPLETED

            if track_metrics:
                self.metrics.total_time = time.time() - start_time
                if self.metrics.total_time > 0:
                    self.metrics.tokens_per_second = (
                        self.metrics.total_tokens / self.metrics.total_time
                    )

        except GeneratorExit:
            self.state = StreamState.INTERRUPTED
            logger.info("Stream interrupted by user")
            raise

        except Exception as e:
            self.state = StreamState.ERROR
            self.metrics.errors += 1
            logger.error(f"Stream error: {e}")
            raise

    async def stream_tokens_async(
        self, tokens: AsyncIterator[str], track_metrics: bool = True
    ) -> AsyncIterator[StreamToken]:
        """Stream tokens asynchronously with metrics tracking.

        Args:
            tokens: Async iterator of token strings
            track_metrics: Whether to track performance metrics

        Yields:
            StreamToken objects
        """
        import asyncio
        import time

        self.state = StreamState.STREAMING
        start_time = time.time()
        first_token_time = None

        try:
            index = 0
            async for token in tokens:
                if first_token_time is None and track_metrics:
                    first_token_time = time.time()
                    self.metrics.time_to_first_token = first_token_time - start_time

                stream_token = StreamToken(
                    token=token, index=index, timestamp=time.time()
                )

                # Handle backpressure
                while not self.buffer.write(stream_token):
                    logger.debug("Buffer full, waiting for consumption")
                    await asyncio.sleep(0.01)

                self.metrics.total_tokens += 1
                index += 1

                yield stream_token

            self.state = StreamState.COMPLETED

            if track_metrics:
                self.metrics.total_time = time.time() - start_time
                if self.metrics.total_time > 0:
                    self.metrics.tokens_per_second = (
                        self.metrics.total_tokens / self.metrics.total_time
                    )

        except asyncio.CancelledError:
            self.state = StreamState.INTERRUPTED
            logger.info("Async stream cancelled by user")
            raise

        except Exception as e:
            self.state = StreamState.ERROR
            self.metrics.errors += 1
            logger.error(f"Async stream error: {e}")
            raise

    def get_metrics(self) -> dict:
        """Get streaming metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "state": self.state.value,
            "time_to_first_token": self.metrics.time_to_first_token,
            "total_tokens": self.metrics.total_tokens,
            "total_time": self.metrics.total_time,
            "tokens_per_second": self.metrics.tokens_per_second,
            "errors": self.metrics.errors,
            "buffer_size": self.buffer.size(),
        }

    def reset(self) -> None:
        """Reset generator state and metrics."""
        self.buffer.clear()
        self.state = StreamState.PENDING
        self.metrics = StreamMetrics()


def format_streaming_output(tokens: Iterator[StreamToken], width: int = 80) -> str:
    """Format streaming tokens for terminal display.

    Args:
        tokens: Iterator of stream tokens
        width: Terminal width for wrapping

    Returns:
        Formatted string
    """
    output = []
    current_line = ""

    for token in tokens:
        current_line += token.token

        # Simple word wrapping
        if len(current_line) >= width:
            # Find last space
            last_space = current_line.rfind(" ", 0, width)
            if last_space > 0:
                output.append(current_line[:last_space])
                current_line = current_line[last_space + 1 :]
            else:
                output.append(current_line[:width])
                current_line = current_line[width:]

    if current_line:
        output.append(current_line)

    return "\n".join(output)
