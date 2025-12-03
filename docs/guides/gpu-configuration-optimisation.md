# GPU Configuration & Optimisation Guide

**Purpose:** Maximise performance with GPU acceleration for vision embeddings

**Target Audience:** Users with NVIDIA CUDA or Apple Silicon GPUs

---

## Overview

ragged v0.5.0+ supports GPU acceleration for vision embeddings using the ColPali model. This guide covers:
- GPU detection and setup
- Performance optimisation
- Memory management
- Troubleshooting

### Performance Impact

GPU acceleration provides **5-10x speedup** for vision embedding generation compared to CPU:

| Hardware | Pages/Second | 100-Page PDF |
|----------|--------------|--------------|
| CPU (16-core) | ~0.5 | ~3.5 minutes |
| Apple M2 (MPS) | ~3 | ~30 seconds |
| NVIDIA RTX 4090 | ~5 | ~20 seconds |

---

## Quick Start

### Verify GPU Detection

```bash
# Check if GPU is detected
ragged gpu list

# View detailed information
ragged gpu info
```

**Expected output (Apple Silicon):**
```
Available Devices:
  ✓ MPS (Apple M2) - 16GB Unified Memory
  ✓ CPU (Apple M2) - 16GB RAM
```

**Expected output (NVIDIA):**
```
Available Devices:
  ✓ CUDA (NVIDIA RTX 4090) - 24GB VRAM
  ✓ CPU (AMD Ryzen 9) - 64GB RAM
```

### Enable Vision Embeddings

```bash
# Ingest PDF with GPU-accelerated vision embeddings
ragged ingest pdf document.pdf --vision
```

That's it! ragged automatically uses your GPU when available.

---

## GPU Detection

### Supported Backends

| Backend | Hardware | OS | Status |
|---------|----------|-----|---------|
| **CUDA** | NVIDIA GPUs | Linux, Windows | ✅ Fully supported |
| **MPS** | Apple Silicon | macOS 13+ | ✅ Fully supported |
| **CPU** | Any | All | ✅ Fallback mode |

### Detection Logic

ragged automatically detects GPUs in this order:

1. **CUDA** (if `torch.cuda.is_available()`)
2. **MPS** (if `torch.backends.mps.is_available()`)
3. **CPU** (fallback)

### Force Specific Backend

Override automatic detection:

```bash
# Force CPU mode
export RAGGED_VISION_DEVICE=cpu
ragged ingest pdf document.pdf --vision

# Force MPS (macOS only)
export RAGGED_VISION_DEVICE=mps

# Force CUDA (Linux/Windows)
export RAGGED_VISION_DEVICE=cuda

# Auto-detect (default)
export RAGGED_VISION_DEVICE=auto
```

---

## Memory Requirements

### ColPali Model Size

The ColPali model requires:
- **Disk space:** ~5GB (first-time download)
- **GPU memory:** ~2GB (loaded model)
- **Processing memory:** Varies by batch size

### Recommended VRAM by Use Case

| VRAM | Batch Size | Suitable For |
|------|------------|--------------|
| 4GB | 1-2 | Light usage, few documents |
| 8GB | 4-6 | Standard usage, moderate load |
| 12GB | 6-8 | Heavy usage, large documents |
| 16GB+ | 8-12 | Professional, batch processing |

### Calculate Your Needs

**Formula:**
```
Required VRAM = Model Size + (Batch Size × Page Size)
              = 2GB + (Batch Size × 100MB)
```

**Examples:**
- Batch 1: 2GB + 100MB = **~2.1GB**
- Batch 4: 2GB + 400MB = **~2.4GB**
- Batch 8: 2GB + 800MB = **~2.8GB**

---

## Batch Size Optimisation

### Manual Configuration

#### Environment Variable (Persistent)

```bash
# Add to ~/.bashrc or ~/.zshrc
export RAGGED_VISION_BATCH_SIZE=4
```

#### Command-Line Flag (One-Time)

```bash
ragged ingest pdf document.pdf --vision --vision-batch-size 4
```

#### Configuration File

```yaml
# ~/.ragged/config.yml
vision_batch_size: 4
```

### Finding Your Optimal Batch Size

Run benchmark with different sizes:

```bash
# Test batch sizes 1, 2, 4, 8
for size in 1 2 4 8; do
  echo "Testing batch size: $size"
  time ragged ingest pdf test.pdf --vision --vision-batch-size $size
done
```

**Interpret results:**
- **Fastest time:** Optimal batch size
- **Out of memory:** Batch too large
- **No speedup:** GPU not utilised

---

## Performance Tuning

### PDF-to-Image DPI

Higher DPI = better quality but slower processing:

```bash
# Fast (recommended for most cases)
export RAGGED_VISION_PDF_DPI=100

# Balanced (default)
export RAGGED_VISION_PDF_DPI=150

# High quality (slow)
export RAGGED_VISION_PDF_DPI=200
```

**Impact:**
- 100 DPI: ~2x faster than 150 DPI
- 200 DPI: ~2x slower than 150 DPI
- Quality difference minimal for most documents

### Recommended Configurations

#### MacBook Pro (M2, 16GB)
```bash
export RAGGED_VISION_DEVICE=mps
export RAGGED_VISION_BATCH_SIZE=4
export RAGGED_VISION_PDF_DPI=150
```

#### Desktop Workstation (RTX 4090, 24GB)
```bash
export RAGGED_VISION_DEVICE=cuda
export RAGGED_VISION_BATCH_SIZE=8
export RAGGED_VISION_PDF_DPI=200
```

#### Laptop (GTX 1660 Ti, 6GB)
```bash
export RAGGED_VISION_DEVICE=cuda
export RAGGED_VISION_BATCH_SIZE=2
export RAGGED_VISION_PDF_DPI=100
```

#### Server (CPU only, 64GB RAM)
```bash
export RAGGED_VISION_DEVICE=cpu
export RAGGED_VISION_BATCH_SIZE=1
export RAGGED_VISION_PDF_DPI=100
```

---

## Monitoring & Debugging

### Real-Time GPU Monitoring

```bash
# Watch GPU usage during processing
ragged gpu stats --watch

# One-time snapshot
ragged gpu stats
```

**Example output:**
```
GPU Statistics:
  Device: NVIDIA RTX 4090
  Utilisation: 87%
  Memory Used: 3.2GB / 24GB
  Temperature: 65°C
  Power: 280W / 450W
```

### Platform-Specific Tools

#### NVIDIA (Linux/Windows)

```bash
# Watch GPU in real-time
watch -n 1 nvidia-smi

# Detailed information
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv
```

#### Apple Silicon (macOS)

```bash
# Monitor in Activity Monitor (GUI)
# - View > Window > GPU History

# Command-line monitoring
sudo powermetrics --samplers gpu_power -i 1000
```

### Performance Benchmarking

```bash
# Run standardised benchmark
ragged gpu benchmark --iterations 10

# Detailed profiling
ragged gpu benchmark --iterations 10 --verbose
```

---

## Troubleshooting

### Issue: GPU Not Detected

**Symptoms:**
```
Available Devices:
  ✓ CPU - Fallback mode
```

**Solutions:**

1. **Verify PyTorch GPU support:**
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"MPS available: {torch.backends.mps.is_available()}")
   ```

2. **Reinstall PyTorch with GPU support:**

   **CUDA (Linux/Windows):**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

   **MPS (macOS):**
   ```bash
   pip install torch torchvision
   # Ensure macOS 13+ and Apple Silicon
   ```

3. **Check GPU drivers:**
   - **NVIDIA:** Update to latest drivers (535+)
   - **Apple:** Update to macOS 13+

### Issue: Out of Memory (OOM)

**Symptoms:**
```
RuntimeError: CUDA out of memory
```
or
```
RuntimeError: MPS backend out of memory
```

**Solutions:**

1. **Reduce batch size:**
   ```bash
   ragged ingest pdf doc.pdf --vision --vision-batch-size 1
   ```

2. **Lower DPI:**
   ```bash
   export RAGGED_VISION_PDF_DPI=100
   ```

3. **Close other applications** using GPU

4. **Check available memory:**
   ```bash
   ragged gpu info
   ```

5. **Use CPU fallback:**
   ```bash
   export RAGGED_VISION_DEVICE=cpu
   ```

### Issue: Slow Performance

**Symptoms:**
- Processing slower than expected
- GPU utilisation <50%

**Solutions:**

1. **Benchmark different batch sizes:**
   ```bash
   ragged gpu benchmark --batch-size 4
   ragged gpu benchmark --batch-size 8
   ```

2. **Verify GPU is being used:**
   ```bash
   ragged gpu stats  # Check utilisation
   ```

3. **Check thermal throttling:**
   - NVIDIA: `nvidia-smi` (check temperature)
   - Apple: Activity Monitor > GPU History

4. **Update GPU drivers**

### Issue: Model Download Stuck

**Symptoms:**
- Command hangs after "Quality: XX% (Excellent)"
- No progress indication

**Root Cause:**
- ColPali model downloading silently (5GB, 10-30 minutes)

**Solutions:**

1. **Wait for download to complete** (first time only)

2. **Pre-download model:**
   ```python
   from transformers import AutoModel
   model = AutoModel.from_pretrained("vidore/colpali-v1.3-hf")
   ```

3. **Check download progress:**
   ```bash
   # Watch HuggingFace cache
   watch -n 5 du -sh ~/.cache/huggingface/
   ```

4. **Verify download completed:**
   ```bash
   ls ~/.cache/huggingface/hub/ | grep colpali
   ```

---

## Advanced Configuration

### Custom Model Cache Directory

```bash
# Use custom cache location (e.g., faster SSD)
export RAGGED_VISION_CACHE_DIR=/path/to/fast/storage
```

### Mixed Precision (Experimental)

For even faster processing on supported GPUs:

```python
# In Python code
from ragged.embeddings.colpali_embedder import ColPaliEmbedder

embedder = ColPaliEmbedder(
    model_name="vidore/colpali-v1.3-hf",
    device="cuda",
    precision="fp16"  # Half precision
)
```

**Benefits:**
- ~2x faster inference
- ~50% less memory

**Trade-offs:**
- Slightly lower precision
- Requires GPU with FP16 support

---

## Performance Benchmarks

### Reference Systems

#### Apple M2 Max (32GB)
- **Configuration:** Batch 6, DPI 150
- **Performance:** ~3 pages/second
- **100-page PDF:** ~35 seconds

#### NVIDIA RTX 4090 (24GB)
- **Configuration:** Batch 8, DPI 150
- **Performance:** ~5 pages/second
- **100-page PDF:** ~20 seconds

#### Intel i9-13900K + RTX 3080 (10GB)
- **Configuration:** Batch 4, DPI 150
- **Performance:** ~4 pages/second
- **100-page PDF:** ~25 seconds

#### CPU-only (AMD Ryzen 9 5950X, 64GB)
- **Configuration:** Batch 1, DPI 100
- **Performance:** ~0.5 pages/second
- **100-page PDF:** ~3.5 minutes

---

## Related Documentation

- [ADR-001: Vision Embeddings Opt-In Design](../development/decisions/adrs/ADR-001-vision-embeddings-opt-in-design.md) - Why vision uses `--vision` flag
- [Manual Testing: GPU Management](../development/testing/manual-tests/gpu-management/README.md)
- [Example Notebook: GPU Optimisation](../../examples/notebooks/03-gpu-optimization.ipynb)
- [Multi-Modal Workflow Tutorial](../tutorials/multimodal-workflow.md)
- [Cross-Platform Tests](../development/testing/manual-tests/cross-platform/README.md)

---

## Questions & Support

**Common Questions:**

**Q: Do I need a GPU for ragged?**
A: No, ragged works on CPU. GPU accelerates vision embeddings 5-10x.

**Q: Which is better, CUDA or MPS?**
A: Both work great. Use what you have. High-end NVIDIA (RTX 4090) slightly faster than Apple Silicon.

**Q: Can I use multiple GPUs?**
A: Not yet. Multi-GPU support planned for future release.

**Q: Does GPU help with text embeddings?**
A: No, only vision embeddings. Text embeddings use Ollama (CPU/GPU depends on Ollama config).

**For help:**
- [Troubleshooting Guide](./troubleshooting.md)
- [GitHub Issues](https://github.com/your-org/ragged/issues)
- [Community Discord](#)
