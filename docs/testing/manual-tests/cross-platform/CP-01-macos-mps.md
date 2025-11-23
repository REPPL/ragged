# Test: macOS with MPS Backend

**Test ID:** CP-01 | **Category:** cross-platform | **Status:** Pending

---

## Objective

Validate full functionality on macOS with Apple Silicon MPS acceleration.

## Prerequisites

- macOS 13+ (Ventura or later)
- Apple Silicon (M1/M2/M3/M4)
- Python 3.12
- Docker Desktop for Mac (for ChromaDB)

## Test Commands

```bash
# Verify MPS detection
ragged gpu list
# Expected: Shows "MPS" backend

# Test ingestion with MPS
ragged ingest pdf examples/sample_documents/data_visualization.pdf --vision

# Test query with MPS
ragged query hybrid "machine learning diagrams"

# Monitor MPS usage
ragged gpu stats
```

## Expected Results

- MPS backend automatically detected
- Vision embeddings use GPU acceleration
- Performance better than CPU-only
- No macOS-specific errors
- Docker integration works

## Verification

- [ ] MPS detected and used
- [ ] GPU memory usage shown
- [ ] No "CPU fallback" warnings
- [ ] Processing faster than CPU baseline
- [ ] Docker containers run correctly

## Platform-Specific Notes

- MPS support requires macOS 13+
- First run may download Metal shaders
- Activity Monitor shows GPU usage
