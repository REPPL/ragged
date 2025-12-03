# GPU Management Tests

**Purpose:** Validate GPU detection, optimisation, and monitoring

---

## Overview

These tests validate ragged's GPU management capabilities across different hardware configurations (CUDA, MPS, CPU).

## Test Scenarios

| Test | Purpose | Hardware |
|------|---------|----------|
| **GPU-01** | Device detection | CUDA/MPS/CPU |
| **GPU-02** | Performance benchmarking | GPU required |
| **GPU-03** | Batch size optimisation | GPU required |

---

## Prerequisites

- ragged CLI installed
- GPU hardware (NVIDIA CUDA or Apple Silicon MPS) OR CPU fallback
- Test documents available

---

## Success Criteria

- [ ] Correct device detection
- [ ] Performance metrics accurate
- [ ] Batch size recommendations work
- [ ] No crashes on any hardware

---

## Related Documentation

- [GPU Configuration Guide](../../../guides/gpu-configuration-optimisation.md)
- Device Management Reference
