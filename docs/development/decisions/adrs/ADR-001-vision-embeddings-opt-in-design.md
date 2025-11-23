# ADR-001: Vision Embeddings Opt-In Design

**Status:** Accepted

---

## Context and Problem Statement

ragged v0.5.0 introduced vision embeddings using ColPali for multi-modal document understanding. This raises a fundamental UX question: should GPU-accelerated vision embeddings be enabled automatically when GPU hardware is detected, or should users explicitly opt-in via a `--vision` flag?

The decision affects user experience, resource utilisation, system predictability, and storage requirements.

**Key Requirements**:
- Vision embeddings should be accessible to users with capable hardware
- System should remain usable on resource-constrained devices
- Storage costs should be predictable and controllable
- Performance characteristics should be consistent across runs

**Constraints**:
- ColPali model requires 4GB+ VRAM minimum
- First-time model download is 5GB (~10-30 minutes)
- Vision embeddings (128-dim) incompatible with text embeddings (384-dim) - requires separate storage
- CPU fallback is 50-100x slower than GPU (10+ sec/page vs 0.1 sec/page)

## Prior Art

**Influences from Other Projects**:
- ❌ No directly comparable prior art reviewed
- Vision RAG systems typically require explicit model selection
- Standard ML frameworks (PyTorch, TensorFlow) use explicit device specification

**Key Differences**: ragged is designed for end-user document processing, not ML engineering. The decision must prioritise user experience over technical flexibility.

## Decision Drivers

1. **Resource Predictability**: Users should know upfront what resources (disk, memory, bandwidth) will be consumed
2. **Performance Consistency**: Same command should produce predictable performance characteristics
3. **Storage Control**: Vision embeddings roughly double storage requirements - users should consciously opt-in
4. **Graceful Degradation**: System should work reliably on underpowered hardware
5. **User Agency**: Users should control resource-intensive features explicitly
6. **Error Prevention**: Silent failures on low-memory systems harm user trust

## Considered Options

### Option 1: Explicit Opt-In (Current Implementation)

**Description**: Users must specify `--vision` flag to enable GPU-accelerated vision embeddings. Default behaviour is text-only embeddings.

```bash
ragged ingest pdf document.pdf          # Text-only (fast, small)
ragged ingest pdf document.pdf --vision # Text + vision (slow first run, better accuracy)
```

**Pros**:
- ✅ Predictable resource usage - no surprise 5GB downloads
- ✅ Consistent performance - same command always behaves the same
- ✅ Works reliably on low-memory systems (4GB RAM laptops)
- ✅ User explicitly controls storage costs
- ✅ Clear mental model - text is default, vision is enhancement

**Cons**:
- ❌ Users may not discover vision embeddings
- ❌ Requires documentation to explain benefits
- ❌ Extra flag to remember

**Implementation Effort**: Low (already implemented)

### Option 2: Auto-Detection with Smart Defaults

**Description**: Automatically enable vision embeddings when GPU with 4GB+ VRAM is detected. Fallback to text-only if insufficient resources.

```bash
ragged ingest pdf document.pdf  # Auto-detects GPU, uses vision if available
ragged ingest pdf document.pdf --no-vision  # Force text-only
```

**Pros**:
- ✅ Users automatically get best quality on capable hardware
- ✅ No flag to remember
- ✅ Utilises available GPU resources

**Cons**:
- ❌ Silent 5GB download on first run (bandwidth surprise)
- ❌ Unpredictable storage usage (some docs have vision, others don't)
- ❌ Performance variance - same command runs differently on different machines
- ❌ Potential OOM crashes on borderline systems (exactly 4GB VRAM)
- ❌ Mixed storage schemas (some collections text-only, others dual)
- ❌ Harder to debug - "works on my machine" issues

**Implementation Effort**: Medium (requires detection logic, fallback handling, mixed schema support)

### Option 3: Three-Way Configuration

**Description**: Support `--vision auto|always|never` with configurable default.

```bash
ragged ingest pdf doc.pdf --vision auto    # Check GPU, use if available (new default)
ragged ingest pdf doc.pdf --vision always  # Force vision, error if unavailable
ragged ingest pdf doc.pdf --vision never   # Text-only
```

**Pros**:
- ✅ Flexibility for power users
- ✅ Can set default in config file
- ✅ Explicit control with smart default

**Cons**:
- ❌ More complex API surface
- ❌ Still has auto-detection issues (bandwidth, performance variance)
- ❌ Configuration complexity

**Implementation Effort**: High (requires config system, detection logic, fallback handling)

## Decision Outcome

**Chosen Option**: "Explicit Opt-In (Option 1)"

**Justification**:

The opt-in design aligns with ragged's philosophy of **user control and predictability**. While auto-detection seems convenient, it introduces multiple failure modes that harm user experience:

1. **Silent Resource Consumption**: A user running `ragged ingest` on a new system would trigger a 5GB model download without warning. On bandwidth-limited connections, this could take hours and consume significant quota.

2. **Storage Unpredictability**: Vision embeddings roughly double storage per document. Auto-enabling based on GPU availability means:
   - User ingests 10 PDFs on laptop (text-only, 10MB total)
   - User ingests 10 PDFs on desktop with GPU (dual embeddings, 100MB total)
   - Result: Inconsistent storage schema, unpredictable costs

3. **Performance Variance**: The same command `ragged ingest pdf doc.pdf` would:
   - Run in 30 seconds on GPU machine
   - Run in 5 minutes on CPU machine
   - Users cannot predict execution time
   - Impossible to reproduce benchmarks across machines

4. **Failure Modes**: Systems with exactly 4GB VRAM are at OOM risk. Auto-detection would:
   - Attempt to load ColPali model (2GB)
   - Start processing with batch size 1-2
   - Hit OOM during processing
   - User sees cryptic error without understanding why
   - With opt-in: Users with 4GB systems simply don't use `--vision` until upgrading

5. **Semantic Clarity**: Vision embeddings are fundamentally **optional**:
   - Text RAG works excellently for most documents
   - Vision adds value for charts, tables, complex layouts
   - Not all documents benefit equally from vision
   - Users should consciously choose when vision is worth the cost

**Consequences**:
- **Positive**:
  - Predictable resource usage across all systems
  - Consistent performance characteristics
  - No silent failures on resource-constrained hardware
  - Users explicitly control storage costs
  - Clear documentation path - explain when to use `--vision`
  - Reproducible behaviour across machines
  - Simple mental model: text is default, vision is enhancement

- **Negative**:
  - Users may not discover vision embeddings without reading documentation
  - Requires explicit flag for every vision ingestion
  - Perceived as "extra work" compared to auto-detection

- **Neutral**:
  - Aligns with ragged's privacy-first philosophy (explicit user control)
  - Similar to other systems requiring explicit model/feature selection
  - Can be revisited if usage patterns show strong preference for auto-detection

## Implementation Notes

**When**: Implemented in v0.5.0

**Dependencies**:
- ColPali model support (v0.5.0)
- Dual embedding storage layer (v0.5.0)
- GPU device detection (v0.5.0)

**Migration Strategy**: Not applicable - this is the initial design for vision embeddings.

## Validation

**How will we know this was the right decision?**
- User feedback indicates they understand when/why to use `--vision`
- No user reports of surprise resource consumption
- Low incidence of OOM errors (indicating users with insufficient resources aren't attempting vision)
- Storage costs remain predictable for users
- Performance benchmarks are reproducible across different machines

**Review Date**: After v0.6.0 (6 months of user feedback)

**Potential Future Changes**:
- If 80%+ of users have capable GPUs and want vision by default, reconsider auto-detection
- If configuration system is added (v0.6+), consider supporting default preference in config file
- Monitor user feedback for requests to change default behaviour

## References

- [Vision Embeddings Implementation](../../implementation/version/v0.5/v0.5.0/README.md)
- [GPU Configuration Guide](../../../guides/gpu-configuration-optimisation.md)
- [ColPali Model Documentation](https://huggingface.co/vidore/colpali-v1.3-hf)
- [ADR-005: Dual Embedding Storage Architecture](./ADR-005-dual-embedding-storage-architecture.md)

---

## Research Notes

**Sources Consulted**:
- ragged codebase analysis (`src/cli/ingest.py`, `src/embeddings/colpali_embedder.py`, `src/storage/dual_store.py`)
- ColPali model specifications and requirements
- PyTorch GPU detection API documentation
- User feedback patterns from similar RAG systems

**Key Insights**:
- Vision and text embeddings use incompatible vector spaces (128-dim vs 384-dim)
- Requires separate ChromaDB collections and hybrid retrieval (RRF)
- ColPali model loading occupies 2GB VRAM + batch processing memory
- CPU fallback exists but is 50-100x slower than GPU
- First-time model download is substantial (5GB) with no progress indication currently

## Alternatives Not Considered

- **Always-On Vision**: Rejected early - incompatible with CPU-only systems
- **Vision-Only Mode**: Rejected - text embeddings provide fast, reliable baseline
- **Dynamic Switching**: Rejected - would create inconsistent collection schemas

---

**Supersedes**: N/A (first ADR)

**Superseded By**: N/A
