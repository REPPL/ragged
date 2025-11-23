# Jupyter Notebooks

**Purpose:** Interactive tutorials for learning ragged through hands-on examples

---

## Overview

This directory contains Jupyter notebooks that demonstrate ragged's capabilities through interactive, step-by-step tutorials. Each notebook is self-contained with setup instructions, executable code, and explanations.

---

## Available Notebooks

### [01-getting-started.ipynb](./01-getting-started.ipynb)

**Level:** Beginner
**Time:** 15-20 minutes
**GPU Required:** No (CPU fallback works)

**What You'll Learn:**
- Install and configure ragged
- Ingest your first document
- Perform basic queries
- Understand chunking and embeddings

**Prerequisites:**
- Python 3.9+
- Jupyter installed (`pip install jupyter`)
- Docker (for ChromaDB)

**Topics Covered:**
1. Installation and setup
2. Starting ChromaDB
3. Document ingestion (text-only)
4. Basic querying
5. Viewing results

---

### [02-multi-document-analysis.ipynb](./02-multi-document-analysis.ipynb)

**Level:** Intermediate
**Time:** 25-30 minutes
**GPU Required:** No (but recommended for speed)

**What You'll Learn:**
- Ingest multiple documents
- Batch processing workflows
- Cross-document querying
- Result filtering and ranking

**Prerequisites:**
- Completed 01-getting-started.ipynb (or familiar with basics)
- Sample documents (provided in `examples/sample_documents/`)

**Topics Covered:**
1. Batch document ingestion
2. Collection management
3. Cross-document semantic search
4. Result ranking and filtering
5. Performance optimisation

---

### [03-gpu-optimization.ipynb](./03-gpu-optimization.ipynb)

**Level:** Advanced
**Time:** 30-40 minutes
**GPU Required:** Yes (CUDA or MPS)

**What You'll Learn:**
- GPU detection and configuration
- Performance benchmarking
- Batch size optimisation
- Vision embeddings with ColPali

**Prerequisites:**
- GPU hardware (NVIDIA CUDA or Apple Silicon MPS)
- Completed previous notebooks
- Vision dependencies installed (`pip install ragged[vision]`)

**Topics Covered:**
1. GPU detection (`ragged gpu detect`)
2. Performance benchmarking
3. Optimal batch size determination
4. Vision embedding generation
5. Hybrid text+vision retrieval
6. Memory management

---

## Getting Started

### 1. Install Dependencies

```bash
# Basic installation
pip install ragged[dev]

# With Jupyter support
pip install jupyter ipykernel

# For GPU notebook (optional)
pip install ragged[vision]
```

### 2. Start Services

```bash
# Start ChromaDB
docker-compose up -d chromadb

# Install Ollama models (for text embeddings)
ollama pull nomic-embed-text

# For vision notebook: install vision model
ollama pull qwen2-vl:2b
```

### 3. Launch Jupyter

```bash
# Navigate to notebooks directory
cd examples/notebooks/

# Start Jupyter
jupyter notebook

# Or JupyterLab
jupyter lab
```

### 4. Open a Notebook

Click on a notebook file (e.g., `01-getting-started.ipynb`) in the Jupyter interface.

---

## Notebook Execution Tips

### Running Cells

- **Execute:** `Shift + Enter` (run cell and move to next)
- **Execute in place:** `Ctrl + Enter` (run cell, stay in place)
- **Run all:** Menu → Cell → Run All

### Kernel Management

- **Restart kernel:** Menu → Kernel → Restart
- **Restart and run all:** Menu → Kernel → Restart & Run All
- **Interrupt execution:** Press ⏹ (Stop) button

### Troubleshooting

**Issue:** "ModuleNotFoundError: No module named 'ragged'"

**Solution:**
```bash
# Install ragged in editable mode
pip install -e /path/to/ragged

# Or install from PyPI
pip install ragged
```

**Issue:** ChromaDB connection fails

**Solution:**
```bash
# Check ChromaDB is running
docker ps | grep chromadb

# Start if not running
docker-compose up -d chromadb
```

**Issue:** GPU not detected

**Solution:**
- Check GPU drivers installed
- Run `ragged gpu detect` in terminal
- See [GPU Configuration Guide](../../docs/guides/gpu-configuration-optimisation.md)

---

## What Doesn't Belong Here

**❌ Don't Add:**
- Production code (goes in `src/`)
- Sample data (goes in `examples/sample_documents/`)
- Configuration files (goes in `examples/configs/`)
- Test scripts (goes in `tests/`)

**✅ Do Add:**
- Interactive tutorials with explanations
- Step-by-step learning materials
- Example workflows with expected outputs

---

## Contributing Notebooks

### Notebook Standards

**Required Sections:**
1. **Title and metadata** (level, time, prerequisites)
2. **Learning objectives**
3. **Setup and dependencies**
4. **Step-by-step tutorial** (with explanations)
5. **Expected outputs** (show what success looks like)
6. **Troubleshooting** (common issues)
7. **Next steps** (where to go from here)

**Code Standards:**
- Clear, commented code
- One concept per cell
- Explanatory markdown cells between code cells
- British English in all text

**Output Standards:**
- Include example outputs (run before committing)
- Clear success indicators
- Error handling demonstrations

### Creating a New Notebook

1. **Copy template structure** from existing notebook
2. **Write learning objectives** first
3. **Create step-by-step code** with explanations
4. **Run completely** and verify all cells execute
5. **Add to this README** in the "Available Notebooks" section
6. **Update numbering** if adding to sequence

---

## Related Documentation

- [Getting Started Tutorial](../../docs/tutorials/multimodal-workflow.md) - Text-based alternative
- [Installation Guide](../../docs/tutorials/installation.md) - Detailed setup
- [GPU Configuration](../../docs/guides/gpu-configuration-optimisation.md) - GPU setup
- [API Reference](../../docs/api/) - Python API documentation
- [Sample Documents](../sample_documents/README.md) - Test data for notebooks

---

**Status**: Active (3 notebooks)
