# Cross-Platform Tests

**Purpose:** Validate functionality across operating systems and hardware

---

## Overview

These tests ensure ragged works correctly across:
- **macOS** (Apple Silicon MPS / Intel)
- **Linux** (CUDA / CPU)
- **CPU-only** fallback on any platform

## Test Scenarios

| Test | Platform | Focus |
|------|----------|-------|
| **CP-01** | macOS (MPS) | Apple Silicon optimization |
| **CP-02** | Linux (CUDA) | NVIDIA GPU support |
| **CP-03** | CPU fallback | Universal compatibility |

---

## Success Criteria

- [ ] Core functionality works on all platforms
- [ ] GPU acceleration when available
- [ ] Graceful CPU fallback
- [ ] Consistent CLI behavior
- [ ] No platform-specific bugs

---

## Related Documentation

- [Installation Guide](../../../tutorials/installation.md)
- [Platform-Specific Notes](../../../guides/platform-compatibility.md)
