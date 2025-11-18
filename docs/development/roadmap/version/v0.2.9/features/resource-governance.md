# Resource Governance System

**Phase**: 1 | **Effort**: 8-10h | **Priority**: MUST-HAVE

---

## Overview

**Current**: Memory limits exist (`src/ingestion/batch.py`) but not unified with CPU/I/O.

**Solution**: Unified resource budget system for predictable multi-user behaviour.

**Success**: No resource starvation, fair scheduling, predictable performance

---

## Implementation

```python
# src/utils/resource_governor.py

class ResourceGovernor:
    """Unified resource budget management."""

    def __init__(self):
        settings = get_settings()
        self.memory_limit_mb = settings.memory_limit_mb or 4096
        self.cpu_limit_percent = settings.cpu_limit_percent or 80
        self.max_concurrent_ops = settings.max_concurrent_ops or 4

        self.active_operations = {}
        self.operation_queue = Queue()
        self._lock = threading.Lock()

    def request_resources(self, operation_id: str, memory_mb: int, cpu_percent: int):
        """Request resource reservation."""
        with self._lock:
            # Check if resources available
            current_memory = self._total_reserved_memory()
            current_cpu = self._total_reserved_cpu()

            if (current_memory + memory_mb > self.memory_limit_mb or
                current_cpu + cpu_percent > self.cpu_limit_percent):
                # Queue operation
                self.operation_queue.put((operation_id, memory_mb, cpu_percent))
                return False

            # Reserve resources
            self.active_operations[operation_id] = {
                "memory_mb": memory_mb,
                "cpu_percent": cpu_percent
            }
            return True

    def release_resources(self, operation_id: str):
        """Release reserved resources."""
        with self._lock:
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]

            # Process queue
            if not self.operation_queue.empty():
                next_op = self.operation_queue.get()
                self.request_resources(*next_op)
```

**Timeline**: 8-10h

---

**Status**: ✅ IMPLEMENTED (commit 5ad5c9f)
