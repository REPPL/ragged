# Test: Batch Size Optimization

**Test ID:** GPU-03 | **Category:** gpu-management | **Status:** Pending

---

## Objective

Verify automatic batch size optimization based on available GPU memory.

## Prerequisites

- GPU with known memory capacity
- Vision embeddings enabled
- Multiple test PDFs

## Test Commands

```bash
# Auto-detect optimal batch size
ragged gpu optimize-batch-size

# Test with different batch sizes
ragged ingest pdf examples/sample_documents/*.pdf --vision --vision-batch-size 1
ragged ingest pdf examples/sample_documents/*.pdf --vision --vision-batch-size 4
ragged ingest pdf examples/sample_documents/*.pdf --vision --vision-batch-size 8

# Monitor memory during processing
ragged gpu stats --watch
```

## Expected Results

- Optimal batch size recommended based on VRAM
- Smaller batch sizes work on limited memory
- Larger batch sizes faster when memory available
- No OOM (out-of-memory) errors at recommended size
- Clear warnings if batch size too large

## Verification

- [ ] Batch size recommendations reasonable
- [ ] Batch size=1 always works (safety)
- [ ] Larger batches improve performance
- [ ] Memory usage scales with batch size
- [ ] Automatic adjustment prevents OOM

## Performance Expectations

| VRAM | Recommended Batch Size | Expected Speed |
|------|------------------------|----------------|
| 4GB | 1-2 | Baseline |
| 8GB | 4-6 | 2-3x faster |
| 16GB+ | 8-12 | 4-6x faster |
