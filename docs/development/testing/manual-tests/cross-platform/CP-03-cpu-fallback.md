# Test: CPU-Only Fallback

**Test ID:** CP-03 | **Category:** cross-platform | **Status:** Pending

---

## Objective

Verify ragged works correctly on systems without GPU acceleration.

## Prerequisites

- Any OS (macOS, Linux, Windows)
- No GPU available OR GPU disabled
- Python 3.12
- Sufficient RAM (16GB+ recommended)

## Test Commands

```bash
# Force CPU mode (disable GPU)
export RAGGED_VISION_DEVICE=cpu

# Verify CPU detection
ragged gpu list
# Expected: Shows only "CPU" backend

# Test basic ingestion (no vision)
ragged ingest pdf examples/sample_documents/data_visualization.pdf

# Test vision on CPU (slow but should work)
ragged ingest pdf examples/sample_documents/data_visualization.pdf --vision --vision-batch-size 1

# Query functionality
ragged query text "machine learning"
```

## Expected Results

- CPU backend detected
- Text ingestion works normally
- Vision ingestion works (slower)
- Batch size automatically set to 1
- No GPU-related errors
- Clear messaging about CPU mode

## Verification

- [ ] No GPU detected/used
- [ ] Core functionality works
- [ ] Vision processing completes (slowly)
- [ ] Memory usage reasonable
- [ ] No crashes or errors
- [ ] Warning shown about CPU performance

## Performance Expectations

- **Text ingestion**: Similar to GPU (no degradation)
- **Vision ingestion**: 5-10x slower than GPU
- **Queries**: Similar to GPU for text, slower for vision
- **Memory**: Higher RAM usage than GPU

## Platform-Specific Notes

- CPU vision processing may take several minutes per page
- Recommend `--vision-batch-size 1` to avoid OOM
- Monitor RAM usage with `ragged gpu stats` even on CPU
