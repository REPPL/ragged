# Advanced Error Recovery & Resilience

**Phase**: 1 | **Effort**: 9-12h | **Priority**: MUST-HAVE

---

## Overview

**Problem**: Exceptions exist (`src/exceptions.py` - 330 lines) but no retry/recovery logic.

**Solution**: Implement retry with exponential backoff, circuit breaker, per-error-type strategies.

**Target**: >98% error recovery success rate

---

## Implementation

```python
# src/utils/retry.py

from tenacity import retry, stop_after_attempt, wait_exponential
from src.exceptions import *

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((LLMConnectionError, VectorStoreError))
)
def with_retry(func):
    """Decorator for automatic retry with exponential backoff."""
    return func

# src/utils/circuit_breaker.py

class CircuitBreaker:
    """Circuit breaker for service calls."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise ServiceUnavailableError("Circuit breaker OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

**Success**: >98% recovery, circuit breaker prevents cascade failures

**Timeline**: 9-12h
