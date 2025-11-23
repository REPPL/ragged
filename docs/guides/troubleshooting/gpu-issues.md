# GPU Troubleshooting Guide

**Purpose**: Solutions to common GPU-related issues in ragged vision RAG.

**Audience**: Users experiencing GPU detection, memory, or performance problems.

---

## Table of Contents

1. [GPU Detection Issues](#gpu-detection-issues)
2. [Memory Issues](#memory-issues)
3. [Performance Issues](#performance-issues)
4. [Platform-Specific Issues](#platform-specific-issues)
5. [Advanced Diagnostics](#advanced-diagnostics)

---

## GPU Detection Issues

### "No GPU detected" / "Using CPU fallback"

**Symptoms**:
- `ragged gpu list` shows only CPU
- Vision ingestion uses CPU (very slow)
- Warnings about GPU not available

---

#### CUDA Not Detected (NVIDIA GPUs)

**Diagnosis**:
```bash
# Check if NVIDIA driver installed
nvidia-smi

# Check if PyTorch sees CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

**Solution 1: NVIDIA drivers not installed**

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nvidia-driver-535  # Or latest version

# Fedora
sudo dnf install akmod-nvidia

# Verify installation
nvidia-smi
```

**Windows**:
1. Download from [NVIDIA Driver Downloads](https://www.nvidia.com/download/index.aspx)
2. Install and reboot
3. Verify: Run `nvidia-smi` in PowerShell

---

**Solution 2: PyTorch not compiled with CUDA**

```bash
# Check PyTorch version
python -c "import torch; print(torch.__version__)"

# Reinstall PyTorch with CUDA 11.8
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Verify**:
```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Version: {torch.version.cuda}')"
```

---

**Solution 3: CUDA version mismatch**

```bash
# Check CUDA version
nvidia-smi  # Look for "CUDA Version: X.Y"

# Install matching PyTorch
# For CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1+
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

#### MPS Not Detected (Apple Silicon)

**Diagnosis**:
```bash
# Check if MPS available
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

**Solution 1: macOS too old**

MPS requires **macOS 12.3+** (Monterey or later).

```bash
# Check macOS version
sw_vers

# If < 12.3, upgrade macOS
```

---

**Solution 2: PyTorch MPS bug (v2.6.0)**

PyTorch 2.6.0 has MPS bugs. Downgrade to 2.5.1:

```bash
pip install torch==2.5.1 torchvision torchaudio
```

**Verify**:
```bash
python -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}, PyTorch: {torch.__version__}')"
```

---

### GPU Detected but Not Used

**Symptoms**:
- `ragged gpu list` shows GPU
- Vision ingestion still slow (using CPU)

**Diagnosis**:
```bash
# Check which device ragged selects
ragged gpu info

# Monitor GPU usage during ingestion
ragged gpu stats --watch
# (separate terminal)
ragged ingest pdf test.pdf --vision --debug
```

**Solution 1: Explicitly specify device**

```bash
# Force CUDA
ragged ingest pdf document.pdf --vision --device cuda:0

# Force MPS
ragged ingest pdf document.pdf --vision --device mps
```

**Solution 2: Check environment variables**

```bash
# These can force CPU fallback
echo $RAGGED_VISION_DEVICE  # Should be "auto", "cuda", or "mps", NOT "cpu"
echo $CUDA_VISIBLE_DEVICES  # Should not be empty or "-1"

# Unset if needed
unset RAGGED_VISION_DEVICE
export RAGGED_VISION_DEVICE=auto
```

---

## Memory Issues

### Out of Memory (OOM) Errors

**Symptoms**:
- "CUDA out of memory" error during ingestion
- Process crashes mid-batch
- System freezes

---

**Solution 1: Reduce batch size**

```bash
# Try batch size 1 (slowest but safest)
ragged ingest pdf document.pdf --vision --vision-batch-size 1

# Gradually increase
ragged ingest pdf document.pdf --vision --vision-batch-size 2
ragged ingest pdf document.pdf --vision --vision-batch-size 4
```

**Recommended batch sizes**:
- 4GB VRAM: batch size 1
- 8GB VRAM: batch size 2-4
- 16GB VRAM: batch size 6-8
- 24GB+ VRAM: batch size 12-16

---

**Solution 2: Enable OOM recovery**

```bash
ragged ingest pdf document.pdf --vision --enable-oom-recovery
```

Automatically:
- Detects OOM errors
- Reduces batch size
- Retries failed batches

---

**Solution 3: Free GPU memory**

```bash
# Check what's using GPU
ragged gpu stats

# Stop other GPU processes
# (close other applications using GPU)

# Clear PyTorch cache
python -c "import torch; torch.cuda.empty_cache()"
```

---

**Solution 4: Use CPU for large documents**

If document is too large for GPU:

```bash
# Fallback to CPU (slow but works)
ragged ingest pdf huge-document.pdf --vision --device cpu
```

---

### Memory Leak / Increasing Usage

**Symptoms**:
- Memory usage grows over time
- Eventually crashes after many documents

**Diagnosis**:
```bash
# Monitor memory during batch ingestion
ragged gpu stats --watch
# (separate terminal)
ragged ingest batch ~/Documents/ --vision --debug
```

**Solution 1: Process in smaller batches**

```bash
# Instead of 100 documents at once
ragged ingest batch ~/Documents/*.pdf --vision

# Process 10 at a time
for file in ~/Documents/*.pdf; do
  ragged ingest pdf "$file" --vision
done
```

**Solution 2: Restart between batches**

```bash
# Batch 1
ragged ingest batch ~/Documents/batch1/ --vision

# Clear memory
python -c "import torch; torch.cuda.empty_cache()"

# Batch 2
ragged ingest batch ~/Documents/batch2/ --vision
```

---

## Performance Issues

### Vision Embedding Too Slow

**Expected speeds**:
- CUDA (8GB): 3-5 pages/sec
- CUDA (24GB): 6-10 pages/sec
- Apple M1/M2: 2-4 pages/sec
- CPU: 0.3-0.5 pages/sec

---

**Diagnosis**:
```bash
# Benchmark your hardware
ragged gpu benchmark --num-pages 20
```

Compare results to expected speeds above.

---

**Solution 1: Verify GPU is being used**

```bash
# Check device selection
ragged gpu info

# Monitor GPU during ingestion
ragged gpu stats --watch
```

If GPU memory isn't increasing during ingestion, you're using CPU.

---

**Solution 2: Increase batch size**

```bash
# Check available memory
ragged gpu info

# If <50% memory used, increase batch size
ragged ingest pdf document.pdf --vision --vision-batch-size 8
```

**Warning**: Watch memory usage with `ragged gpu stats --watch`

---

**Solution 3: Use faster GPU**

If you have multiple GPUs:

```bash
# List all GPUs
ragged gpu list

# Benchmark all
ragged gpu benchmark

# Use fastest one
ragged ingest pdf document.pdf --vision --device cuda:0
```

---

**Solution 4: Optimise environment**

```bash
# Disable other GPU applications
# (browsers, video players, games)

# Set PyTorch optimisations
export CUDA_LAUNCH_BLOCKING=0  # Async execution
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Memory optimisation
```

---

### Slower Than Benchmark Results

**Symptoms**:
- `ragged gpu benchmark` shows 5 pages/sec
- Actual ingestion only 2 pages/sec

**Cause**: Benchmark uses synthetic images. Real PDFs require:
- PDF rendering (pdf2image)
- Image preprocessing
- Additional overhead

**Expected**: Real-world performance is 60-80% of benchmark.

**Solution**: This is normal. To improve:

```bash
# 1. Ensure poppler-utils installed (faster PDF rendering)
# Ubuntu/Debian
sudo apt install poppler-utils

# macOS
brew install poppler

# 2. Use SSD for document storage (faster disk I/O)
# 3. Reduce image quality if acceptable
# (currently not configurable - future feature)
```

---

## Platform-Specific Issues

### Windows

**Issue: "CUDA not available" despite GPU**

**Solution 1: Visual C++ Redistributable**

PyTorch requires Visual C++ 2015-2022 Redistributable:

1. Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Install and reboot
3. Verify: `python -c "import torch; print(torch.cuda.is_available())"`

**Issue: PowerShell execution error**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Linux

**Issue: "libcudnn not found"**

```bash
# Ubuntu/Debian
sudo apt install libcudnn8

# Fedora
sudo dnf install cudnn
```

**Issue: Permission denied accessing /dev/nvidia**

```bash
# Add user to video group
sudo usermod -a -G video $USER

# Log out and back in
```

---

### macOS (Apple Silicon)

**Issue: "MPS backend out of memory"**

MPS has stricter memory limits than CUDA:

```bash
# Reduce batch size more aggressively
ragged ingest pdf document.pdf --vision --vision-batch-size 1
```

**Issue: MPS slower than expected**

Verify you're using PyTorch 2.5.1 (not 2.6.0):

```bash
python -c "import torch; print(torch.__version__)"

# If 2.6.0, downgrade
pip install torch==2.5.1
```

---

## Advanced Diagnostics

### Check PyTorch GPU Support

```python
import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"cuDNN version: {torch.backends.cudnn.version()}")
print(f"Number of GPUs: {torch.cuda.device_count()}")

if torch.cuda.is_available():
    print(f"GPU 0: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

print(f"MPS available: {torch.backends.mps.is_available()}")
```

Save as `check_gpu.py` and run:
```bash
python check_gpu.py
```

---

### Monitor GPU Usage (CUDA)

```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# Log to file
nvidia-smi dmon -s pucvmet -c 100 > gpu_log.txt
```

---

### Debug Vision Embedding

```bash
# Maximum debug output
ragged ingest pdf test.pdf --vision --debug

# Check device selection and memory
ragged gpu info
ragged gpu stats
```

Look for:
- `Device: cuda:0` (or mps) - confirms GPU usage
- `Batch size: X` - adaptive batching working
- `Memory allocated: X GB` - increasing during processing

---

### Test Vision Embedding Directly

```python
from ragged.embeddings.colpali_embedder import ColPaliEmbedder
from PIL import Image
import numpy as np

# Create test image
img = Image.fromarray(np.random.randint(0, 255, (1024, 768, 3), dtype=np.uint8))

# Try embedding with CUDA
try:
    embedder = ColPaliEmbedder(device="cuda", batch_size=1)
    embedding = embedder.embed_batch_images([img])
    print(f"✓ CUDA works! Embedding shape: {embedding.shape}")
except Exception as e:
    print(f"✗ CUDA failed: {e}")

# Try MPS
try:
    embedder = ColPaliEmbedder(device="mps", batch_size=1)
    embedding = embedder.embed_batch_images([img])
    print(f"✓ MPS works! Embedding shape: {embedding.shape}")
except Exception as e:
    print(f"✗ MPS failed: {e}")
```

---

## Getting Help

### Before Asking for Help

1. **Run diagnostics**:
   ```bash
   ragged gpu list
   ragged gpu info
   ragged gpu benchmark
   python check_gpu.py  # From Advanced Diagnostics above
   ```

2. **Check system info**:
   ```bash
   ragged env-info --verbose > system_info.txt
   ```

3. **Test with single document**:
   ```bash
   ragged ingest pdf test.pdf --vision --debug > debug_log.txt 2>&1
   ```

### Report Issues

**Include in your bug report**:
1. Output of `ragged gpu list` and `ragged gpu info`
2. Output of `python check_gpu.py` (see Advanced Diagnostics)
3. Full error message and stack trace
4. Operating system and GPU model
5. Output of `ragged env-info --verbose`

**Report here**: [GitHub Issues](https://github.com/REPPL/ragged/issues/new)

---

## Related Documentation

- Installation Guide: GPU Setup - Initial GPU configuration
- [GPU Management Guide](../gpu-management.md) - GPU commands and workflows
- [Performance Tuning Guide](../performance-tuning.md) - Optimisation techniques
- [Setup Issues](./setup-issues.md) - General troubleshooting

---
