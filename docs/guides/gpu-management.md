# GPU Management Guide

**Purpose**: Guide to managing GPU devices for vision-based document understanding in ragged.

**Audience**: Users with GPU hardware (CUDA, Apple Silicon) seeking optimal performance for vision RAG.

---

## Table of Contents

1. [Overview](#overview)
2. [Device Detection](#device-detection)
3. [Device Information](#device-information)
4. [Memory Monitoring](#memory-monitoring)
5. [Performance Benchmarking](#performance-benchmarking)
6. [Best Practices](#best-practices)
7. [Common Workflows](#common-workflows)

---

## Overview

### What is GPU Management?

ragged v0.5.3+ includes comprehensive GPU management tools for:
- **Device detection**: Discover available CUDA, MPS, and CPU devices
- **Memory monitoring**: Track VRAM usage in real-time
- **Performance testing**: Benchmark vision embedding generation
- **Optimal selection**: Automatically choose the fastest device

### When to Use GPU Commands

**Use GPU commands when**:
- ✅ Setting up vision RAG for the first time
- ✅ Troubleshooting slow vision embedding generation
- ✅ Optimising batch sizes for your hardware
- ✅ Monitoring memory usage during large ingestion jobs
- ✅ Comparing performance across multiple GPUs

**Not needed for**:
- ❌ Text-only RAG (no vision embeddings)
- ❌ Systems with only CPU (automatic CPU fallback)

---

## Device Detection

### List All Available Devices

```bash
ragged gpu list
```

**Example output:**

```
Available Devices (3):

[0] cuda:0
    Name: NVIDIA GeForce RTX 4090
    Memory: 24.00 GB
    Compute Capability: 8.9

[1] cuda:1
    Name: NVIDIA GeForce RTX 3090
    Memory: 24.00 GB
    Compute Capability: 8.6

[2] cpu
    Name: CPU Fallback

Recommended device: cuda
```

### Detailed Device Listing

```bash
ragged gpu list --verbose
```

Shows additional information:
- ✓ Optimal device marker
- Device priority ranking
- Compute capability details

### Device Types

**CUDA** (NVIDIA GPUs):
- Fastest for vision RAG (2-3x faster than CPU)
- Requires CUDA 11.8+ and 8GB+ VRAM
- Supports multiple devices (cuda:0, cuda:1, etc.)

**MPS** (Apple Silicon):
- Native M1/M2/M3 Mac GPU acceleration
- Requires macOS 12.3+ and PyTorch 2.5.1
- Single device only (mps)

**CPU**:
- Fallback when no GPU available
- 10x+ slower than GPU
- No VRAM limits (uses system RAM)

---

## Device Information

### Show Optimal Device Info

```bash
ragged gpu info
```

Displays information for the automatically selected optimal device.

**Example output:**

```
Device Information:

Type: cuda
ID: 0
Name: NVIDIA GeForce RTX 4090
Total Memory: 24.00 GB
Allocated: 0.15 GB
Reserved: 0.20 GB
Free: 23.65 GB
Utilisation: 0.6%
Compute Capability: 8.9

✓ This is the optimal device
```

### Query Specific Device

```bash
# CUDA device
ragged gpu info cuda:0

# Apple Silicon
ragged gpu info mps

# CPU fallback
ragged gpu info cpu
```

### What Information is Shown?

**Always displayed**:
- Device type and ID
- Device name (if available)
- Total memory

**GPU only** (CUDA/MPS):
- Allocated memory (actively used by models)
- Reserved memory (allocated but not used)
- Free memory (available for use)
- Memory utilisation percentage

**CUDA only**:
- Compute capability version
- Multi-GPU device index

---

## Memory Monitoring

### Single Snapshot

```bash
ragged gpu stats
```

**Example output:**

```
Memory Statistics: cuda

Allocated: 2.45 GB
Reserved:  3.10 GB
Free:      20.90 GB
Total:     24.00 GB
Utilisation: 10.2%
```

### Real-Time Monitoring (Watch Mode)

```bash
ragged gpu stats --watch
```

**Features**:
- Auto-refreshes every 1 second
- Visual progress bar with colour coding:
  - 🟢 Green: <85% (healthy)
  - 🟡 Yellow: 85-95% (nearing capacity)
  - 🔴 Red: >95% (critical)
- Press Ctrl+C to stop

**Example output:**

```
Memory Statistics: cuda

Allocated: 18.45 GB
Reserved:  20.10 GB
Free:      3.90 GB
Total:     24.00 GB
Utilisation: 76.9%
████████████████████████████████░░░░░░░░

Refreshing every 1s... (Ctrl+C to stop)
```

### Custom Refresh Interval

```bash
# Refresh every 2 seconds
ragged gpu stats --watch --interval 2

# Refresh every 5 seconds
ragged gpu stats mps --watch --interval 5
```

### Monitor Specific Device

```bash
# Monitor CUDA device 0
ragged gpu stats cuda:0 --watch

# Monitor Apple Silicon GPU
ragged gpu stats mps --watch
```

### When to Monitor Memory

**Use watch mode when**:
- 🔍 Ingesting large batches of PDFs with vision embeddings
- 🔍 Experimenting with different batch sizes
- 🔍 Diagnosing out-of-memory (OOM) errors
- 🔍 Running multiple ragged processes simultaneously

---

## Performance Benchmarking

### Quick Benchmark (Default)

```bash
ragged gpu benchmark
```

Benchmarks all available devices with:
- 10 synthetic pages
- Adaptive batch sizing
- Warmup + measurement run

**Example output:**

```
Vision Embedding Benchmark
Pages: 10
Batch size: adaptive

Benchmarking cuda:0...
  Total time: 2.45s
  Throughput: 4.08 pages/sec
  Latency: 245.0ms/page
  Batch size: 8

Benchmarking cpu...
  Total time: 24.15s
  Throughput: 0.41 pages/sec
  Latency: 2415.0ms/page
  Batch size: 1

Summary:

[1] cuda:0: 4.08 pages/sec (245.0ms/page)
[2] cpu: 0.41 pages/sec (2415.0ms/page)

cuda:0 is 9.9x faster than cpu
```

### Custom Benchmark Parameters

```bash
# Test with specific batch size
ragged gpu benchmark --batch-size 4

# Test more pages for accurate measurement
ragged gpu benchmark --num-pages 50

# Combined custom settings
ragged gpu benchmark --batch-size 8 --num-pages 20
```

### Benchmark Single Device

```bash
# CUDA device
ragged gpu benchmark --device cuda:0

# Apple Silicon
ragged gpu benchmark --device mps

# CPU only
ragged gpu benchmark --device cpu
```

### Interpreting Benchmark Results

**Throughput** (pages/sec):
- Higher is better
- Typical values:
  - CUDA (8GB VRAM): 3-5 pages/sec
  - CUDA (24GB VRAM): 6-10 pages/sec
  - Apple M1/M2: 2-4 pages/sec
  - CPU: 0.3-0.5 pages/sec

**Latency** (ms/page):
- Lower is better
- Typical values:
  - CUDA: 100-300ms/page
  - Apple Silicon: 250-500ms/page
  - CPU: 2000-4000ms/page

**Batch Size**:
- Larger batches = faster throughput
- Limited by VRAM availability
- Adaptive batching finds optimal size automatically

---

## Best Practices

### 1. Check Devices Before Vision Ingestion

```bash
# Always verify GPU is detected
ragged gpu list

# Check available memory
ragged gpu info
```

If no GPU detected:
- Verify CUDA/MPS installation (see [Installation Guide](../tutorials/installation.md))
- Check PyTorch GPU support: `python -c "import torch; print(torch.cuda.is_available())"`

### 2. Monitor Memory During Large Batches

```bash
# Terminal 1: Ingest documents
ragged ingest batch ~/Papers/ --vision

# Terminal 2: Monitor memory
ragged gpu stats --watch
```

Watch for:
- 🔴 Memory utilisation >95%: Reduce batch size
- 🟢 Memory utilisation <50%: Can increase batch size for better performance

### 3. Benchmark Before Tuning

```bash
# Establish baseline
ragged gpu benchmark --num-pages 20 > baseline.txt

# After configuration changes
ragged gpu benchmark --num-pages 20 > tuned.txt

# Compare results
diff baseline.txt tuned.txt
```

### 4. Use Adaptive Batching by Default

```bash
# Let ragged find optimal batch size
ragged ingest pdf document.pdf --vision

# Only specify batch size if you know your hardware limits
ragged ingest pdf document.pdf --vision --vision-batch-size 4
```

Adaptive batching automatically:
- Detects available VRAM
- Starts with conservative batch size
- Monitors for OOM errors
- Adjusts dynamically

### 5. Multi-GPU Selection

```bash
# Check which GPUs are available
ragged gpu list

# Use specific GPU for ingestion
ragged ingest pdf document.pdf --vision --device cuda:1

# Benchmark all GPUs to find fastest
ragged gpu benchmark
```

---

## Common Workflows

### Workflow 1: First-Time Vision Setup

```bash
# 1. Check GPU detection
ragged gpu list

# 2. Verify device info
ragged gpu info

# 3. Run benchmark to establish baseline
ragged gpu benchmark

# 4. Test with single document
ragged ingest pdf test.pdf --vision

# 5. Monitor memory during test
ragged gpu stats cuda:0
```

### Workflow 2: Optimising Batch Size

```bash
# 1. Check available memory
ragged gpu info

# 2. Start monitoring
ragged gpu stats --watch  # In separate terminal

# 3. Test batch size 4
ragged gpu benchmark --batch-size 4

# 4. Test batch size 8
ragged gpu benchmark --batch-size 8

# 5. Test batch size 16
ragged gpu benchmark --batch-size 16

# 6. Use batch size with best throughput and <90% memory
```

### Workflow 3: Troubleshooting Slow Performance

```bash
# 1. Verify correct device is being used
ragged gpu info

# 2. Check if GPU is actually being used (not CPU fallback)
ragged gpu list --verbose

# 3. Benchmark to compare against expected performance
ragged gpu benchmark

# 4. Monitor memory during actual ingestion
ragged gpu stats --watch
# (separate terminal)
ragged ingest pdf document.pdf --vision --debug
```

### Workflow 4: Multi-GPU Selection

```bash
# 1. List all GPUs
ragged gpu list

# 2. Benchmark all devices
ragged gpu benchmark

# 3. Use fastest GPU for production ingestion
ragged ingest batch ~/Documents/ --vision --device cuda:0
```

### Workflow 5: Preventing OOM During Large Batches

```bash
# 1. Check available memory
ragged gpu info

# 2. Monitor in real-time
ragged gpu stats --watch

# 3. If memory >90%, reduce batch size
ragged ingest batch ~/Papers/ --vision --vision-batch-size 2

# 4. Or enable aggressive OOM recovery
ragged ingest batch ~/Papers/ --vision --enable-oom-recovery
```

---

## Related Documentation

- [Installation Guide: GPU Setup](../tutorials/installation.md#gpu-setup-for-vision-rag-v050) - GPU driver installation
- [Troubleshooting: GPU Issues](./troubleshooting/gpu-issues.md) - Common GPU problems
- [Performance Tuning Guide](./performance-tuning.md) - Optimisation techniques
- [CLI Reference](../reference/cli/) - Complete command reference

---
