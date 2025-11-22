# Installation Guide

**ragged** is a privacy-first local RAG (Retrieval-Augmented Generation) system for document question-answering. This guide covers installation for both basic text-based RAG and advanced vision-based document understanding (v0.5.0+).

---

## System Requirements

### Basic Requirements (Text-Only RAG)

- **Python:** 3.12 (required)
- **OS:** Linux, macOS, Windows
- **RAM:** 4GB minimum, 8GB+ recommended
- **Disk Space:** 2GB for dependencies + storage for your documents

### Vision RAG Requirements (v0.5.0+)

For vision-based document understanding (ColPali), additional requirements apply:

- **RAM:** 16GB minimum, 32GB+ recommended
- **GPU (Recommended):**
  - NVIDIA GPU with 8GB+ VRAM (CUDA 11.8+), **OR**
  - Apple Silicon (M1/M2/M3) with 16GB+ unified memory
- **Disk Space:** Additional 1.2GB for ColPali model
- **CPU Fallback:** Available but 10x+ slower (development only)

---

## Installation Methods

### Option 1: Standard Installation (pip)

#### 1. Create Virtual Environment

```bash
# Create Python 3.12 virtual environment
python3.12 -m venv ~/.ragged-venv

# Activate environment
source ~/.ragged-venv/bin/activate  # Linux/macOS
# or
~/.ragged-venv/Scripts/activate  # Windows
```

#### 2. Install ragged

```bash
# Basic installation (text-only RAG)
pip install ragged

# With development dependencies
pip install ragged[dev]
```

#### 3. Verify Installation

```bash
ragged --version
ragged --help
```

---

### Option 2: From Source (Development)

For contributors or those wanting the latest features:

```bash
# Clone repository
git clone https://github.com/your-org/ragged.git
cd ragged

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests to verify
pytest
```

---

## GPU Setup for Vision RAG (v0.5.0+)

Vision-based document understanding using ColPali requires GPU acceleration for practical use. This section covers setup for NVIDIA GPUs and Apple Silicon.

### NVIDIA GPU Setup (CUDA)

#### 1. Verify CUDA Installation

```bash
# Check NVIDIA driver
nvidia-smi

# Should show GPU details and CUDA version >= 11.8
```

**If CUDA is not installed:**

- **Linux:** Install CUDA Toolkit from [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)
- **Windows:** Install CUDA Toolkit and cuDNN from NVIDIA website

Recommended CUDA versions:
- CUDA 11.8 (most compatible with PyTorch 2.x)
- CUDA 12.1+ (newer, faster)

#### 2. Install PyTorch with CUDA

PyTorch is automatically installed with ragged v0.5.0+, but verify CUDA support:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
```

**Expected output:**
```
CUDA available: True
CUDA version: 11.8
GPU: NVIDIA GeForce RTX 4090
```

If CUDA is not detected, reinstall PyTorch with CUDA:

```bash
# Example: PyTorch with CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Example: PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### 3. Verify GPU Memory

```bash
nvidia-smi

# Check available VRAM (8GB+ recommended)
```

#### 4. Test Vision Embedding

```python
from ragged.embeddings.colpali_embedder import ColPaliEmbedder

embedder = ColPaliEmbedder(device="cuda")
info = embedder.get_device_info()
print(f"Device: {info['device']}")
print(f"GPU: {info['name']}")
print(f"VRAM: {info['vram_free_gb']:.2f} GB free")
```

---

### Apple Silicon Setup (MPS)

Apple Silicon (M1/M2/M3) supports GPU acceleration via Metal Performance Shaders (MPS).

#### 1. Verify macOS Version

MPS requires **macOS 12.3+** (Monterey or later).

```bash
sw_vers
```

#### 2. Install PyTorch with MPS Support

PyTorch 2.0+ includes MPS support by default. Verify:

```python
import torch
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")
```

**Expected output:**
```
MPS available: True
MPS built: True
```

**Known Issue:** PyTorch 2.6.0 has MPS bugs. Use **PyTorch 2.5.1** instead:

```bash
pip install torch==2.5.1 torchvision torchaudio
```

#### 3. Test Vision Embedding

```python
from ragged.embeddings.colpali_embedder import ColPaliEmbedder

embedder = ColPaliEmbedder(device="mps")
info = embedder.get_device_info()
print(f"Device: {info['device']}")
print(f"Name: {info['name']}")
```

---

### CPU-Only Setup (Not Recommended for Production)

If no GPU is available, ragged falls back to CPU. This is **10x+ slower** and only suitable for development/testing.

```python
from ragged.embeddings.colPali_embedder import ColPaliEmbedder

# Explicitly use CPU
embedder = ColPaliEmbedder(device="cpu")

# Auto-detection will also fallback to CPU if no GPU found
embedder = ColPaliEmbedder()  # device=None → auto-detect → CPU
```

**Performance:**
- GPU: 1-3 seconds/page
- CPU: 10-20 seconds/page

---

## System Dependencies

### pdf2image (Required for Vision RAG)

pdf2image requires **poppler-utils** for PDF rendering.

#### Linux (Debian/Ubuntu)

```bash
sudo apt-get install poppler-utils
```

#### Linux (Fedora/RHEL)

```bash
sudo dnf install poppler-utils
```

#### macOS

```bash
brew install poppler
```

#### Windows

1. Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\Program Files\poppler`
3. Add `C:\Program Files\poppler\Library\bin` to PATH

**Verify Installation:**

```bash
pdftoppm -v
# Should show version information
```

---

## Configuration

### Environment Variables

Create `.env` file in your working directory or set system environment variables:

```bash
# Basic configuration
RAGGED_STORAGE_PATH=~/.ragged/storage
RAGGED_MODEL=all-MiniLM-L6-v2

# Vision configuration (v0.5.0+)
RAGGED_VISION_ENABLED=true
RAGGED_VISION_DEVICE=auto  # auto | cuda | mps | cpu
RAGGED_VISION_MODEL=vidore/colpali-v1.3-hf
RAGGED_VISION_BATCH_SIZE=4  # Adjust based on VRAM

# Ollama configuration
OLLAMA_HOST=http://localhost:11434
```

### GPU Batch Size Guidelines

Adjust batch size based on available VRAM:

| VRAM | Batch Size |
|------|------------|
| 4GB  | 1-2        |
| 8GB  | 4-6        |
| 16GB | 8-12       |
| 24GB+ | 16-32     |

**Auto-detection:** ragged automatically estimates optimal batch size if not specified.

---

## First Run

### Download Models

On first run, ragged downloads required models:

**Text embedding model:**
- all-MiniLM-L6-v2 (~90MB)
- Downloads in ~30 seconds

**Vision model (if vision enabled):**
- vidore/colpali-v1.3-hf (~1.2GB)
- Downloads in 5-10 minutes on first use
- Cached locally for future runs

**Download Location:**
- Linux/macOS: `~/.cache/huggingface/`
- Windows: `C:\Users\<username>\.cache\huggingface\`

### Test Installation

```bash
# Test basic functionality
ragged --help

# Test document ingestion
ragged add path/to/document.pdf

# Test vision capabilities (v0.5.0+)
ragged add --vision path/to/document.pdf
```

---

## Troubleshooting

### Common Issues

#### 1. "CUDA not available" on GPU system

**Cause:** PyTorch not compiled with CUDA support

**Fix:**
```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 2. "MPS not available" on Apple Silicon

**Cause:** PyTorch 2.6.0 MPS bug

**Fix:**
```bash
pip install torch==2.5.1 torchvision torchaudio
```

#### 3. "poppler not found" error

**Cause:** poppler-utils not installed

**Fix:** Install poppler-utils (see System Dependencies above)

#### 4. GPU out of memory (OOM)

**Cause:** Batch size too large for available VRAM

**Fix:**
```bash
# Reduce batch size
export RAGGED_VISION_BATCH_SIZE=2  # or 1 for 4GB GPUs

# Or use CLI flag
ragged add --vision --vision-batch-size 2 document.pdf
```

#### 5. Slow vision embedding on CPU

**Cause:** No GPU detected, falling back to CPU

**Fix:** Verify GPU setup (see GPU Setup sections above)

---

## Upgrading

### Upgrade to Latest Version

```bash
pip install --upgrade ragged
```

### Upgrade from v0.4.x to v0.5.0 (Vision RAG)

v0.5.0 adds vision dependencies. Upgrade procedure:

```bash
# 1. Upgrade ragged (pulls in new dependencies automatically)
pip install --upgrade ragged

# 2. Verify vision dependencies
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"

# 3. Migrate existing storage (if needed)
ragged storage migrate --dry-run  # Preview changes
ragged storage migrate  # Apply migration
```

**Breaking Changes (v0.4 → v0.5):**
- Storage schema updated (dual embedding support)
- New metadata fields: `embedding_type`
- ID format changed: `doc_chunk_5` → `doc_chunk_5_text`

Migration is automatic and preserves existing text embeddings.

---

## Uninstallation

### Remove ragged

```bash
pip uninstall ragged
```

### Remove All Data

```bash
# Remove storage
rm -rf ~/.ragged/storage

# Remove model cache
rm -rf ~/.cache/huggingface/hub/models--*colpali*
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers*
```

---

## Related Documentation

- [Docker Setup Guide](../guides/docker-setup.md) - Docker installation
- [Configuration Guide](../guides/configuration.md) - Configuration options
- [Quick Start Guide](./quickstart.md) - First steps after installation
- [FAQ](../guides/faq.md) - Common questions

---

**Last Updated:** 2025-11-22 (v0.5.0)
