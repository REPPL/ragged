# ColPali Architecture Research

**Date:** 2025-11-22
**Version:** v0.5.0 VISION-001 Research
**Model:** vidore/colpali (PaliGemma-3B extension)

---

## Executive Summary

ColPali is a Vision Language Model (VLM) designed for efficient document retrieval that combines visual document understanding with ColBERT-style multi-vector embeddings. It processes document pages as images, eliminating the need for complex OCR and layout recognition pipelines whilst capturing both textual and visual content (diagrams, tables, layout).

**Key Innovation:** Treats document pages as images and generates contextualised multi-vector embeddings (D=128 per patch) that can be efficiently matched against text queries using late interaction mechanisms.

---

## Architecture Components

### 1. Vision Encoder: SigLIP-So400m

- **Input:** Document page images (any resolution, automatically resized)
- **Processing:** Splits images into patches (similar to ViT patch extraction)
- **Output:** Patch embeddings fed to language model

**Technical Details:**
- Enhanced version called BiSigLIP in newer model variants
- Pre-trained vision-language contrastive model
- Handles arbitrary image sizes through dynamic patching

### 2. Language Model: PaliGemma-3B

- **Base Model:** Google's PaliGemma-3B-mix-448 (open weights)
- **Language Backbone:** Gemma 2B parameters
- **Function:** Processes vision patch embeddings as "soft" tokens to produce contextualised embeddings

**Architecture Flow:**
```
Image Patches → SigLIP Encoder → Linear Projection → Gemma 2B → Contextualised Embeddings
```

### 3. Projection & Adaptation Layer

- **Type:** Randomly initialised projection layer
- **Training:** LoRA adapters (r=32, alpha=32)
- **Output Dimension:** D=128 (for efficient storage and retrieval)
- **Purpose:** Maps high-dimensional language model space to compact retrieval space

---

## Training Specifications

### Dataset

- **Size:** 127,460 query-page pairs
- **Sources:**
  - 63% academic documents (papers, technical reports)
  - 37% synthetic queries (generated from PDFs via VQA datasets)
- **Total training data:** ~100k query-image pairs

### Training Configuration

- **Precision:** bfloat16
- **Optimiser:** paged_adamw_8bit
- **Learning Rate:** 5e-5 with linear decay
- **Batch Size:** 32 per GPU (8 GPU setup = 256 total)
- **Epochs:** 1
- **Hardware:** 8 GPU training setup (specific GPU type not documented)

---

## Model Specifications

### Embedding Dimensions

- **Vision Patches:** Variable (depends on image size and patch extraction)
- **Language Model Hidden Size:** PaliGemma standard (not explicitly documented)
- **Final Embedding Dimension:** **128** per patch token
- **Query Embedding:** Variable number of tokens × 128 dimensions

**Note:** Unlike single-vector models (384-dim or 768-dim), ColPali produces **multi-vector** embeddings—one 128-dim vector per visual patch/query token.

### Model Variants

| Model | Base | Release | Notes |
|-------|------|---------|-------|
| vidore/colpali | PaliGemma-3B | v1.0 | Original release |
| vidore/colpali-v1.1 | PaliGemma-3B | v1.1 | Improved training |
| vidore/colpali-v1.2 | PaliGemma-3B | v1.2 | Performance updates |
| vidore/colpali-v1.3-hf | PaliGemma-3B | v1.3 | Native HF Transformers |

**Recommended for ragged:** `vidore/colpali-v1.3-hf` (native transformers support, no custom engine required)

### Model Size

- **Parameters:** ~3 billion (PaliGemma-3B base)
- **Download Size:** ~1.2GB (safetensors format)
- **Format:** bfloat16 precision

---

## GPU Requirements

### Estimated VRAM Usage

Based on similar 3B parameter VLMs:

| Configuration | VRAM Required | Batch Size |
|---------------|---------------|------------|
| Inference (bfloat16) | 4-6GB | 1-2 pages |
| Inference (float16) | 4-6GB | 1-2 pages |
| Inference (8-bit quantization) | 2-3GB | 1 page |
| Batch processing (4 pages) | 8-12GB | 4 pages |
| Batch processing (8 pages) | 16-20GB | 8 pages |

**Recommended Setup:**
- **Minimum:** 8GB VRAM (NVIDIA GPU) or 16GB unified memory (Apple Silicon)
- **Optimal:** 16GB+ VRAM for batch processing
- **CPU Fallback:** Supported but 10x+ slower (not practical for production)

### Device Support

- **CUDA:** Full support (NVIDIA GPUs)
- **MPS:** Apple Silicon support (requires PyTorch 2.5.1, not 2.6.0 due to MPS bugs)
- **CPU:** Functional but very slow (development/testing only)

---

## Implementation Details

### Installation

```bash
# Option 1: Use colpali-engine (custom wrapper)
pip install colpali-engine>=0.2.0

# Option 2: Use native transformers (v1.3-hf model)
# Already available with transformers>=4.35.0
```

**For ragged:** We'll use **Option 2** (native transformers) to avoid additional dependencies.

### Loading the Model

```python
import torch
from transformers import AutoModel, AutoProcessor

model_name = "vidore/colpali-v1.3-hf"

# Load model
model = AutoModel.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",  # Automatically assigns to best device
)
model.eval()  # Inference mode

# Load processor
processor = AutoProcessor.from_pretrained(model_name)
```

### Generating Embeddings

#### For Document Pages (Images)

```python
from PIL import Image
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path("document.pdf", dpi=150)

# Process images
batch_images = processor.process_images(images).to(model.device)

# Generate embeddings
with torch.no_grad():
    image_embeddings = model(**batch_images)

# Shape: (num_pages, num_patches, 128)
```

#### For Text Queries

```python
queries = ["What is the main conclusion?"]

# Process queries
batch_queries = processor.process_queries(queries).to(model.device)

# Generate embeddings
with torch.no_grad():
    query_embeddings = model(**batch_queries)

# Shape: (num_queries, num_tokens, 128)
```

### Late Interaction Matching

```python
# Compute similarity scores (ColBERT-style)
scores = processor.score_multi_vector(query_embeddings, image_embeddings)

# Returns: similarity scores for each query-page pair
```

---

## Advantages for ragged

### 1. No OCR Pipeline Required

- **Traditional RAG:** PDF → OCR → Layout Detection → Text Extraction → Chunking → Embedding
- **ColPali:** PDF → Images → Embeddings (2 steps vs 5+)

**Benefit:** Simpler, faster, fewer failure points

### 2. Visual Content Understanding

ColPali captures:
- Diagrams, flowcharts, and visualisations
- Tables and formatted data
- Mathematical equations and notation
- Document layout and structure
- Handwriting and annotations

**Use Case:** Technical papers, research reports, infographics, presentations

### 3. Multi-Modal Retrieval

- **Text-only queries:** "Find documents about neural networks"
- **Image queries:** Upload a diagram, find similar visualisations
- **Hybrid queries:** Combine text and visual similarity

### 4. End-to-End Training

Unlike OCR → embedding pipelines (brittle, error-prone), ColPali is trained end-to-end for retrieval, making it robust to:
- Poor scan quality
- Complex layouts
- Non-Latin scripts
- Handwritten annotations

---

## Limitations & Considerations

### 1. Model Size (~1.2GB)

- **Download Time:** 5-10 minutes on first use (cached locally)
- **Storage:** 1.2GB disk space per model
- **Loading Time:** 2-5 seconds on GPU, 10-20 seconds on CPU

### 2. Inference Speed

- **GPU (CUDA):** <2 seconds/page (acceptable)
- **GPU (MPS):** <3 seconds/page (acceptable)
- **CPU:** 10-20 seconds/page (too slow for production)

**Implication:** GPU strongly recommended for practical use

### 3. Embedding Dimensionality Mismatch

- **Text embeddings (ragged v0.4.x):** 384-dimensional single vector
- **Vision embeddings (ColPali):** Multi-vector (N × 128), where N varies by image

**Challenge:** Cannot directly compare text and vision embeddings (different semantic spaces)

**Solution (v0.5.0):** Store separately with `embedding_type` metadata, use RRF for hybrid queries

### 4. Memory Overhead

Multi-vector embeddings require more storage than single-vector:
- **Text chunk:** 1 × 384 floats = 1.5KB
- **Vision page:** ~100 patches × 128 floats = ~50KB

**Storage Impact:** Vision embeddings ~30x larger than text (acceptable trade-off for quality)

### 5. Limited to Visual Documents

ColPali excels on:
- ✅ PDFs with visual content (papers, reports, presentations)
- ✅ Scanned documents
- ✅ Infographics and charts

Less useful for:
- ❌ Plain text documents (text embeddings sufficient)
- ❌ Audio transcripts
- ❌ Code files

---

## Performance Benchmarks

### ViDoRe Benchmark Results

ColPali is the **top-performing model** on the ViDoRe (Visual Document Retrieval) benchmark, outperforming:
- Traditional OCR + text embedding pipelines
- Other vision-language retrieval models
- CLIP-based document retrievers

**Particularly strong on:**
- Academic papers with equations
- Infographics and visualisations
- Tables and structured data
- Multi-lingual documents

### Throughput Estimates

Based on PaliGemma-3B benchmarks:

| Hardware | Pages/Second | Batch Size |
|----------|--------------|------------|
| NVIDIA A100 (40GB) | 15-20 | 16 |
| NVIDIA RTX 4090 (24GB) | 10-12 | 8 |
| NVIDIA RTX 3090 (24GB) | 8-10 | 4 |
| Apple M2 Max (64GB) | 5-7 | 4 |
| CPU (32 cores) | 0.5-1 | 1 |

---

## Integration Strategy for ragged v0.5.0

### Phase 1: Core Integration (VISION-001)

1. **Add ColPali embedder class** (`src/embeddings/colpali_embedder.py`)
   - Inherit from `BaseEmbedder`
   - Implement device detection (CUDA > MPS > CPU)
   - Implement batch processing with adaptive batch sizing
   - Add GPU memory monitoring

2. **Handle multi-vector embeddings**
   - ColPali produces variable-length embeddings (N × 128)
   - Need to flatten or pool for storage in ChromaDB (single-vector requirement)
   - **Decision:** Store mean-pooled 128-dim embedding initially (simplest), explore multi-vector in v0.6+

3. **Configuration & CLI**
   - Add `VisionConfig` to settings
   - CLI flags: `--vision`, `--vision-only`, `--gpu-device`
   - Environment variables: `RAGGED_VISION_ENABLED`, `RAGGED_VISION_DEVICE`

### Phase 2: Dual Storage (VISION-002)

1. **Extend storage schema**
   - Text embeddings: 384-dim (existing)
   - Vision embeddings: 128-dim (mean-pooled from ColPali)
   - Metadata: `embedding_type: "text" | "vision"`

2. **Implement retrieval modes**
   - Text-only: Query with text embedding (existing)
   - Vision-only: Query with vision embedding
   - Hybrid: RRF fusion of text + vision results

---

## Resources

### Official Documentation

- [HuggingFace Model Card](https://huggingface.co/vidore/colpali)
- [ColPali Blog Post](https://huggingface.co/blog/manu/colpali)
- [arXiv Paper](https://arxiv.org/abs/2407.01449) - "ColPali: Efficient Document Retrieval with Vision Language Models"
- [GitHub Repository](https://github.com/illuin-tech/colpali) - Training and inference code

### ViDoRe Benchmark

- [Benchmark Collection](https://huggingface.co/collections/vidore/colpali-paper-resources-6684070d22572e729829ce72)
- [ViDoRe Leaderboard](https://huggingface.co/spaces/vidore/vidore-leaderboard)

### Community Resources

- [Vespa.ai Integration Guide](https://blog.vespa.ai/retrieval-with-vision-language-models-colpali/)
- [Qdrant Integration Guide](https://qdrant.tech/blog/qdrant-colpali/)
- [Zilliz Technical Explainer](https://zilliz.com/blog/colpali-enhanced-doc-retrieval-with-vision-language-models-and-colbert-strategy)

---

## Decision: Model Version for ragged

**Chosen Model:** `vidore/colpali-v1.3-hf`

**Rationale:**
1. **Native transformers support:** No need for `colpali-engine` dependency
2. **Latest version:** Most recent improvements
3. **Wider compatibility:** Works with standard HuggingFace API
4. **Simpler integration:** Fewer dependencies to manage

**Alternative Considered:** `vidore/colqwen2-v1.0` (newer Qwen2-based variant)
- **Pros:** Potentially better performance, newer architecture
- **Cons:** Less mature, fewer benchmarks, different API

**Conclusion:** Start with `colpali-v1.3-hf` (proven, stable), consider Qwen2 variant in v0.6+ if needed.

---

## Next Steps

1. ✅ **Session 1.1 Complete:** ColPali architecture researched and documented
2. **Session 1.2:** Add PyTorch, transformers, Pillow, pdf2image to `pyproject.toml`
3. **Session 2.1:** Implement `ColPaliEmbedder` class skeleton
4. **Session 2.2:** Implement core embedding methods
5. **Session 2.3:** Add PDF processing pipeline
6. **Session 2.4:** Implement error handling and CPU fallback

---

**Status:** Research Complete
**Next Session:** VISION-001 Session 1.2 (Dependency Setup)
