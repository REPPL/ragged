# Async Operations with Backpressure

**Phase**: 2 | **Effort**: 8-10h | **Priority**: MUST-HAVE

**Current**: Async processor exists (`src/ingestion/async_processor.py` - 378 lines) but no backpressure control

**Enhancement**: Add queue depth limits, dynamic worker pool sizing, priority queues

**Implementation**:
```python
class AsyncProcessorWithBackpressure(AsyncDocumentProcessor):
    def __init__(self, max_queue_depth=100, max_workers=None):
        super().__init__(max_workers=max_workers)
        self.task_queue = asyncio.Queue(maxsize=max_queue_depth)
        self.semaphore = asyncio.Semaphore(max_workers or cpu_count())

    async def process_with_backpressure(self, items):
        async with self.semaphore:
            # Process item
            # Auto-adjust workers based on CPU usage
```

**Success**: No resource overwhelm, 2-3x faster scans maintained

**Timeline**: 8-10h
