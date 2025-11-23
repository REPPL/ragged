# Configuration Examples

**Purpose:** Example configuration files for common ragged usage scenarios

---

## Overview

This directory contains example YAML configuration files demonstrating how to configure ragged for different use cases, user personas, and deployment scenarios.

---

## Available Configurations

### [researcher_config.yml](./researcher_config.yml)

**Use Case:** Academic research workflows

**Optimised For:**
- High accuracy and relevance
- Comprehensive retrieval (more results)
- Slower but thorough processing

**Key Settings:**
- Top-k retrieval: 20 results
- Chunk size: Larger (for academic papers)
- Vision embeddings: Enabled (for diagrams/figures)
- GPU: Enabled with conservative memory settings

**Best For:**
- Literature reviews
- Academic paper analysis
- Research documentation
- Technical report processing

---

### [developer_config.yml](./developer_config.yml)

**Use Case:** Software development documentation

**Optimised For:**
- Fast iteration speed
- Code snippet retrieval
- API documentation search

**Key Settings:**
- Top-k retrieval: 10 results
- Chunk size: Smaller (for code blocks)
- Vision embeddings: Disabled (text-focused)
- GPU: Enabled with aggressive batch sizes

**Best For:**
- Code documentation
- API reference search
- Technical specifications
- Internal wikis

---

## Configuration File Structure

All configuration files follow this structure:

```yaml
# Metadata
name: "Configuration Name"
description: "What this config is optimised for"
version: "0.5.6"

# Storage backend
storage:
  backend: "chromadb"
  collection_name: "collection_name"
  host: "localhost"
  port: 8000

# Embedding configuration
embeddings:
  text_model: "nomic-embed-text"
  vision_model: "vidore/colpali-v1.3-hf"
  enable_vision: true/false

# Chunking strategy
chunking:
  strategy: "recursive"
  chunk_size: 1000
  chunk_overlap: 200

# Retrieval parameters
retrieval:
  top_k: 10
  hybrid_weight_text: 0.7
  hybrid_weight_vision: 0.3

# GPU configuration
gpu:
  enable_gpu: true/false
  device: "auto"  # or "cuda", "mps", "cpu"
  batch_size: "auto"  # or specific number
  enable_memory_monitoring: true/false
```

---

## Using Configuration Files

### Command-Line Usage

```bash
# Use specific config file
ragged --config researcher_config.yml ingest pdf paper.pdf

# Override specific settings
ragged --config developer_config.yml --top-k 20 query "API docs"
```

### Environment Variable

```bash
# Set default config
export RAGGED_CONFIG=researcher_config.yml

# All commands use this config
ragged ingest pdf paper.pdf
ragged query "research question"
```

### Python API

```python
from ragged.config import load_config
from ragged import RAG

# Load configuration
config = load_config("researcher_config.yml")

# Initialize RAG with config
rag = RAG(config=config)

# Use as normal
rag.ingest_pdf("paper.pdf")
results = rag.query("research question")
```

---

## Creating Custom Configurations

### 1. Start with Template

Copy the closest existing configuration:

```bash
cp researcher_config.yml my_custom_config.yml
```

### 2. Modify Settings

Edit YAML file with your requirements:

```yaml
name: "My Custom Configuration"
description: "Optimised for my specific use case"

# Adjust settings...
retrieval:
  top_k: 15  # Your preferred number of results
```

### 3. Test Configuration

```bash
# Verify valid YAML
ragged --config my_custom_config.yml --validate

# Test with ingestion
ragged --config my_custom_config.yml ingest pdf test.pdf

# Test with query
ragged --config my_custom_config.yml query "test query"
```

### 4. Document Use Case

Add to this README in "Available Configurations" section.

---

## Configuration Guidelines

### When to Create New Config

**Create new config when:**
- Distinct use case (different user persona)
- Significantly different settings
- Reusable across multiple projects

**Don't create new config when:**
- One-off setting change (use command-line flags)
- Temporary testing (use environment variables)
- Project-specific paths (use environment variables)

### Naming Conventions

**Format:** `[usecase]_config.yml`

**Examples:**
- `researcher_config.yml` (persona-based)
- `legal_config.yml` (domain-based)
- `fast_config.yml` (performance-based)
- `accurate_config.yml` (quality-based)

### Documentation Requirements

Each config file should include:

```yaml
# At the top of file:
name: "Clear Name"
description: "What this optimises for"
version: "0.5.6"  # ragged version

# Comments explaining non-obvious settings
retrieval:
  top_k: 20  # Higher for research workflows
```

---

## Common Configuration Patterns

### High Accuracy (Research)

```yaml
retrieval:
  top_k: 20  # More results
  hybrid_weight_text: 0.6
  hybrid_weight_vision: 0.4  # More vision weight

chunking:
  chunk_size: 1500  # Larger chunks preserve context
  chunk_overlap: 300  # More overlap reduces boundary issues
```

### High Speed (Development)

```yaml
retrieval:
  top_k: 5  # Fewer results

embeddings:
  enable_vision: false  # Text-only faster

gpu:
  batch_size: 32  # Aggressive batching
```

### Balanced (General Purpose)

```yaml
retrieval:
  top_k: 10  # Moderate results
  hybrid_weight_text: 0.7
  hybrid_weight_vision: 0.3

chunking:
  chunk_size: 1000  # Standard
  chunk_overlap: 200
```

---

## What Doesn't Belong Here

**❌ Don't Include:**
- Secrets or credentials (use environment variables)
- User-specific paths (use environment variables)
- Project-specific settings (use project config)
- Temporary test configs (delete after testing)

**✅ Do Include:**
- Reusable persona-based configs
- Domain-specific optimisations
- Performance/quality trade-off examples
- Well-documented, tested configurations

---

## Related Documentation

- [Configuration Guide](../../docs/guides/configuration.md) - Comprehensive config documentation
- [GPU Configuration](../../docs/guides/gpu-configuration-optimisation.md) - GPU-specific settings
- [Basic Examples](../basic/README.md) - Simple usage examples
- [Jupyter Notebooks](../notebooks/README.md) - Interactive configuration tutorials

---

**Status**: Active (2 configurations)
