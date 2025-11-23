# Test: Linux with CUDA Backend

**Test ID:** CP-02 | **Category:** cross-platform | **Status:** Pending

---

## Objective

Validate full functionality on Linux with NVIDIA CUDA acceleration.

## Prerequisites

- Linux (Ubuntu 22.04+ recommended)
- NVIDIA GPU with CUDA support
- CUDA 11.8+ and cuDNN installed
- Python 3.12
- Docker or native ChromaDB

## Test Commands

```bash
# Verify CUDA detection
ragged gpu list
# Expected: Shows "CUDA" backend with GPU model

# Check CUDA version
ragged gpu info --format json

# Test ingestion with CUDA
ragged ingest pdf examples/sample_documents/data_visualization.pdf --vision

# Benchmark CUDA performance
ragged gpu benchmark --iterations 10

# Monitor CUDA usage
nvidia-smi  # Watch VRAM usage
ragged gpu stats --watch
```

## Expected Results

- CUDA backend detected
- GPU model and VRAM reported correctly
- Vision embeddings use CUDA
- Performance significantly better than CPU
- No CUDA errors or warnings

## Verification

- [ ] CUDA detected (not CPU fallback)
- [ ] GPU utilization > 0% during processing
- [ ] VRAM usage tracked
- [ ] No "CUDA out of memory" errors
- [ ] Performance meets expectations

## Platform-Specific Notes

- Requires NVIDIA drivers (535+)
- `nvidia-smi` should show GPU
- Check CUDA version compatibility
- May need `LD_LIBRARY_PATH` configuration
