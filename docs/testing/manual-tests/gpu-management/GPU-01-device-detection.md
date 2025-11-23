# Test: GPU Device Detection

**Test ID:** GPU-01 | **Category:** gpu-management | **Status:** Pending

---

## Objective

Verify correct detection and reporting of available compute devices.

## Test Commands

```bash
# List all available devices
ragged gpu list

# Show detailed device information
ragged gpu info

# Check device capabilities
ragged gpu info --format json
```

## Expected Results

### On Apple Silicon (MPS):
- Detects MPS backend
- Shows device name (e.g., "Apple M1/M2/M3")
- Reports available memory
- Indicates MPS support enabled

### On NVIDIA GPU (CUDA):
- Detects CUDA backend
- Shows GPU model (e.g., "RTX 4090")
- Reports VRAM available
- Shows CUDA version

### On CPU-only:
- Detects CPU fallback
- Shows CPU model
- Reports system RAM
- No GPU listed

## Verification

- [ ] Correct backend detected
- [ ] Device specifications accurate
- [ ] Memory reporting correct
- [ ] No false positives/negatives
