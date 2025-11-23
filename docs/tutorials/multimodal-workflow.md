# Multi-Modal Workflow Tutorial

**What you'll learn**: How to use ragged's vision capabilities for documents with diagrams, charts, and visual content.

**Prerequisites**:
- ragged v0.5.3+ installed
- GPU available (CUDA or MPS recommended)
- Basic familiarity with ragged CLI (see [Essentials](../guides/cli/essentials.md))

**Reading time**: 20-25 minutes

---

## Overview

Multi-modal retrieval combines **text understanding** with **visual similarity** to provide more accurate results for documents containing diagrams, charts, screenshots, and other visual elements.

###When to Use Multi-Modal RAG

✅ **Perfect for**:
- Technical documentation with architecture diagrams
- Research papers with figures and charts
- Product manuals with illustrations
- Design documents with mockups
- Scientific papers with data visualisations

❌ **Not needed for**:
- Plain text documents (novels, articles, essays)
- Simple reports without visual content
- When GPU isn't available

---

## Step 1: Check GPU Availability

Before using vision features, verify you have a suitable GPU:

```bash
ragged gpu list
```

**Expected output**:
```
Available Devices (2):

[0] mps
    Name: Apple Silicon
    ✓ Optimal device

[1] cpu

Recommended device: mps
```

**What to look for**:
- ✅ CUDA (NVIDIA GPUs) - Best performance
- ✅ MPS (Apple Silicon) - Good performance
- ⚠️ CPU only - Vision will be slow, but functional

---

## Step 2: Ingest Documents with Vision

### Single PDF with Vision

```bash
# Technical documentation
ragged ingest pdf system-architecture.pdf --vision

# Research paper
ragged ingest pdf ml-research-2024.pdf --vision --device cuda:0
```

**What happens**:
1. PDF analysed for quality issues
2. Text extracted and chunked (384-dim embeddings)
3. Pages converted to images
4. Vision embeddings generated (128-dim ColPali)
5. Stored in dual collections for hybrid retrieval

### Batch Ingestion

```bash
# Ingest entire directory
ragged ingest batch ./technical-docs/ --vision

# With custom pattern
ragged ingest batch ./papers/ --pattern "*2024*.pdf" --vision
```

**Progress indicator**:
```
Processing system-architecture.pdf...
  Analysing PDF quality...
  ✓ Quality: 94 (A)
  Chunking document...
  Generating text embeddings...
  Generating vision embeddings...
  Vision device: mps
  Batch size: 8
  Pages: 24
✓ Document ingested: abc-123-def
  Chunks: 67
  Vision embeddings: 24 pages
```

---

## Step 3: Query Your Documents

### Text Query with Visual Boosting

**Use case**: You want text-based semantic search but prefer results with diagrams.

```bash
# Boost results containing diagrams
ragged query text "authentication flow" --boost-diagrams

# Boost results with tables
ragged query text "performance benchmarks" --boost-tables

# Boost both
ragged query text "system architecture" --boost-diagrams --boost-tables
```

**How it works**:
- Performs semantic text search
- Boosts scores for chunks with visual content
- Diagrams: +20% score boost
- Tables: +15% score boost

---

### Image Query (Visual Similarity)

**Use case**: "I have a diagram, find similar ones in my documents."

```bash
# Find similar diagrams
ragged query image my-sketch.png

# More results
ragged query image architecture-draft.png --num-results 10
```

**Example workflow**:
1. Draw rough architecture sketch
2. Save as PNG/JPG
3. Query to find similar existing diagrams
4. Useful for discovering related documentation

**Expected output**:
```
Image Query: architecture-draft.png

Found 5 results (184.2ms):

[1] system-design-v2.pdf
    Score: 0.9123
    Type: vision
    Page: 12

[2] api-documentation.pdf
    Score: 0.8847
    Type: vision
    Page: 8

[3] technical-spec.pdf
    Score: 0.8621
    Type: vision
    Page: 15
```

---

### Hybrid Query (Text + Image)

**Use case**: "Find pages that discuss X AND contain visuals similar to Y."

```bash
# Basic hybrid query
ragged query hybrid "authentication flow" oauth-diagram.png

# Custom weight distribution
ragged query hybrid "database schema" erd-sketch.png \
  --text-weight 0.7 \
  --vision-weight 0.3
```

**Weight tuning**:
- **70% text, 30% vision**: Prioritise semantic meaning
- **50% text, 50% vision**: Balanced (default)
- **30% text, 70% vision**: Prioritise visual similarity

**How it works**:
1. Generates text embedding from query string
2. Generates vision embedding from image
3. Retrieves results from both collections
4. Merges with Reciprocal Rank Fusion (RRF)
5. Returns ranked results

---

### Interactive Mode

**Use case**: Exploratory queries, switching between modes dynamically.

```bash
ragged query interactive
```

**Session example**:
```
Interactive Query Mode
Type ':help' for commands, ':quit' to exit

text> database architecture
Found 5 results (156.3ms):
  [1] system-design.pdf (score: 0.89)
  [2] technical-spec.pdf (score: 0.87)
  ...

text> :mode hybrid
Mode set to: hybrid

hybrid> auth flow | oauth-diagram.png
Found 3 results (203.1ms):
  [1] security-guide.pdf (score: 0.92)
  ...

hybrid> :weights 0.8 0.2
Weights set: text=0.80, vision=0.20

hybrid> :mode image
Mode set to: image

image> architecture-sketch.png
Found 4 results (127.8ms):
  ...

image> :quit
Goodbye!
```

**Commands**:
- `:mode text|image|hybrid` - Switch query mode
- `:weights <text> <vision>` - Adjust hybrid weights
- `:results <n>` - Set result count
- `:metadata on|off` - Toggle metadata display
- `:help` - Show help
- `:quit` - Exit

---

## Step 4: Monitor and Optimize

### Check Storage Statistics

```bash
ragged storage info
```

**Output**:
```
Storage Information:

Text Collection:
  Total chunks: 1,247
  Unique documents: 18

Vision Collection:
  Total page embeddings: 342
  Unique documents: 12

Storage:
  Location: /Users/you/ragged/data
  Size: 1.8 GB
```

### GPU Memory Monitoring

```bash
# Real-time monitoring
ragged gpu stats --watch

# Specific device
ragged gpu stats cuda:0 --watch --interval 2
```

**Output** (refreshes automatically):
```
Memory Statistics: mps

Allocated: 2.34 GB
Reserved:  3.12 GB
Free:      4.88 GB
Total:     8.00 GB
Utilization: 29.3%

████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░

Refreshing every 1s... (Ctrl+C to stop)
```

---

## Step 5: Benchmark Performance

Compare device performance to choose optimal configuration:

```bash
# Benchmark all devices
ragged gpu benchmark

# Custom test parameters
ragged gpu benchmark --num-pages 20 --batch-size 8

# Benchmark specific device
ragged gpu benchmark --device cuda:0
```

**Output**:
```
Vision Embedding Benchmark
Pages: 10
Batch size: adaptive

Benchmarking mps...
  Total time: 3.42s
  Throughput: 2.92 pages/sec
  Latency: 342.1ms/page
  Batch size: 4

Benchmarking cpu...
  Total time: 18.74s
  Throughput: 0.53 pages/sec
  Latency: 1874.2ms/page
  Batch size: 1

Summary:

[1] mps: 2.92 pages/sec (342.1ms/page)
[2] cpu: 0.53 pages/sec (1874.2ms/page)

mps is 5.5x faster than cpu
```

**Decision guide**:
- Use CUDA for best performance (if available)
- Use MPS for Apple Silicon (good balance)
- Use CPU only if no GPU available

---

## Real-World Examples

### Example 1: Software Architecture Documentation

**Scenario**: You maintain technical documentation with architecture diagrams and want to find related design patterns.

```bash
# Ingest all architecture docs
ragged ingest batch ./architecture-docs/ --vision

# Find auth-related diagrams
ragged query text "authentication patterns" --boost-diagrams

# Find similar to your current design
ragged query image current-design.png

# Hybrid: "Find microservice patterns with diagrams like this"
ragged query hybrid "microservice architecture" reference-diagram.png
```

---

### Example 2: Research Paper Analysis

**Scenario**: Analyzing ML research papers with charts and experimental results.

```bash
# Ingest research papers
ragged ingest batch ./papers-2024/ --vision --pattern "*.pdf"

# Find papers with specific charts
ragged query text "training loss curves" --boost-diagrams --boost-tables

# Find papers with similar experimental setup
ragged query image my-experiment-setup.png

# Multi-modal: "Find transformer architecture papers with attention diagrams"
ragged query hybrid "transformer attention mechanism" attention-diagram.png \
  --text-weight 0.6 --vision-weight 0.4
```

---

### Example 3: Product Manual Search

**Scenario**: Technical support searching product manuals for specific procedures with diagrams.

```bash
# Ingest manuals
ragged ingest batch ./product-manuals/ --vision

# Find installation procedures
ragged query text "installation steps" --boost-diagrams

# Find similar to customer's photo
ragged query image customer-issue.jpg

# Support workflow in interactive mode
ragged query interactive
```

---

## Troubleshooting

### "Out of Memory" Errors

**Symptom**: OOM errors during vision embedding generation.

**Solutions**:
1. Reduce batch size:
   ```bash
   ragged ingest pdf large-doc.pdf --vision --batch-size 2
   ```

2. Use CPU fallback:
   ```bash
   ragged ingest pdf doc.pdf --vision --device cpu
   ```

3. Monitor memory:
   ```bash
   ragged gpu stats --watch
   ```

---

### "No vision embeddings found"

**Symptom**: Image/hybrid queries return no results.

**Solutions**:
1. Verify vision embeddings exist:
   ```bash
   ragged storage info
   ```
   Should show: "Vision Collection: Total page embeddings: X"

2. Ingest documents with --vision flag:
   ```bash
   ragged ingest pdf doc.pdf --vision
   ```

3. Check storage migration:
   ```bash
   ragged storage migrate
   ```

---

### Slow Performance

**Symptom**: Vision embedding generation is very slow.

**Solutions**:
1. Check device:
   ```bash
   ragged gpu list
   ```

2. Benchmark devices:
   ```bash
   ragged gpu benchmark
   ```

3. Use faster device:
   ```bash
   ragged ingest pdf doc.pdf --vision --device cuda:0
   ```

4. Increase batch size (if memory allows):
   ```bash
   ragged ingest pdf doc.pdf --vision --batch-size 16
   ```

---

## Best Practices

### 1. **Selective Vision Embedding**

Don't enable vision for all documents - use it strategically:

✅ Enable for:
- Technical docs with diagrams
- Research papers with figures
- Design documents

❌ Skip for:
- Plain text documents
- Simple reports
- Text-heavy documents

### 2. **Batch Size Tuning**

Start with adaptive (default), then tune based on benchmarks:

```bash
# Let ragged choose
ragged ingest pdf doc.pdf --vision

# Tune for your GPU
ragged gpu benchmark
ragged ingest pdf doc.pdf --vision --batch-size 8
```

### 3. **Query Mode Selection**

Choose the right query mode for your use case:
- **Text**: Fast, semantic understanding
- **Image**: Visual similarity only
- **Hybrid**: Best of both, slightly slower

### 4. **Storage Maintenance**

Periodically clean up:
```bash
# Check storage
ragged storage info

# Clean orphaned embeddings
ragged storage vacuum
```

---

## Next Steps

### Continue Learning

**Hands-On Tutorials**:
- [Getting Started Notebook](../../examples/notebooks/01-getting-started.ipynb) - Interactive basics
- [Multi-Document Analysis Notebook](../../examples/notebooks/02-multi-document-analysis.ipynb) - Batch processing
- [GPU Optimization Notebook](../../examples/notebooks/03-gpu-optimization.ipynb) - Performance tuning

**GPU Optimization**:
- [GPU Configuration & Optimisation Guide](../guides/gpu-configuration-optimisation.md) - Complete GPU setup
- [GPU Management Tests](../testing/manual-tests/gpu-management/README.md) - Validation procedures
- [Performance Tuning](../guides/performance-tuning.md) - Speed optimization

### Experiment & Validate

**Try These**:
- Adjust weight combinations for hybrid queries (`--text-weight`, `--vision-weight`)
- Benchmark your specific GPU with `ragged gpu benchmark`
- Test with your own documents using [Manual Testing Framework](../testing/manual-tests/README.md)

**Test Scenarios**:
- [Visual Content Tests](../testing/manual-tests/visual-content/README.md) - Vision embedding validation
- [Multi-Modal Query Tests](../testing/manual-tests/multimodal-queries/README.md) - Query testing
- [Cross-Platform Tests](../testing/manual-tests/cross-platform/README.md) - Platform compatibility

---

## Related Documentation

### Getting Started
- [Installation Guide](./installation.md) - Setup and requirements
- [Complete Beginner's Guide](./complete-beginners-guide.md) - First steps
- [Getting Started](./getting-started.md) - Quick start

### Advanced Topics
- [GPU Configuration & Optimisation](../guides/gpu-configuration-optimisation.md) - GPU setup
- [CLI Advanced Commands](../guides/cli/advanced.md) - Power user features
- [Troubleshooting Guide](../guides/troubleshooting/README.md) - Common issues
