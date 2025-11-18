# Performance-Aware Logging

**Phase**: 1 | **Effort**: 6-8h | **Priority**: MUST-HAVE

---

## Overview

**Current**: Synchronous JSON logging (`src/utils/logging.py` - 170 lines) may impact performance under load.

**Solution**: Async logging, dynamic log levels, sampling for high-frequency events.

**Success**: <5% logging overhead, non-blocking writes

---

## Implementation

```python
# src/utils/async_logging.py

import asyncio, queue, threading
from logging.handlers import QueueHandler, QueueListener

class AsyncLogHandler:
    """Non-blocking async log handler."""

    def __init__(self):
        self.log_queue = queue.Queue(-1)  # Unbounded queue
        self.queue_handler = QueueHandler(self.log_queue)

        # Background thread for log processing
        self.listener = QueueListener(
            self.log_queue,
            *self._get_handlers(),
            respect_handler_level=True
        )
        self.listener.start()

    def _get_handlers(self):
        # Existing handlers (file, console)
        return [
            RotatingFileHandler("ragged.log", maxBytes=10MB, backupCount=5),
            StreamHandler(sys.stdout)
        ]

# Sampling for high-frequency logs
class SamplingFilter(logging.Filter):
    """Sample high-frequency logs (log 1/N events)."""

    def __init__(self, sample_rate=100):
        self.sample_rate = sample_rate
        self.counter = 0

    def filter(self, record):
        # Always log WARNING+
        if record.levelno >= logging.WARNING:
            return True

        # Sample INFO/DEBUG
        self.counter += 1
        return (self.counter % self.sample_rate) == 0
```

**Timeline**: 6-8h
