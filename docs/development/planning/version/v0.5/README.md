# ragged v0.5 Design Overview


**Status:** 📋 Planned

---

## Overview

Version 0.5 introduces **ColPali vision integration** for multi-modal document understanding, enabling vision-based retrieval that understands document layouts, diagrams, tables, and images without relying solely on text extraction.

**Goal**: Enable ragged to "see" documents like humans do, understanding visual layout and content.

**For detailed implementation plans, see:**
- [Roadmap: v0.5.0](../../../roadmap/version/v0.5.0/) - ColPali vision integration (140-180 hours)

---

## Prerequisites

**Security & Privacy Foundation (REQUIRED):**

v0.5 processes visual content which may contain sensitive information. The security and privacy infrastructure from v0.2.10 and v0.2.11 is **mandatory** before implementing vision features.

- ✅ **v0.2.10 (Security Hardening)** - Session isolation, JSON serialisation, security testing
- ✅ **v0.2.11 (Privacy Infrastructure)** - Encryption, PII detection, TTL cleanup, GDPR compliance
- ✅ **v0.3.x (Production-Ready RAG)** - All v0.3 features complete
- ✅ **v0.4.0 (Personal Memory & Knowledge Graphs)** - Memory system and graph infrastructure

**Why Critical for v0.5:**

v0.5 processes visual content which may reveal sensitive information:
- **Vision embeddings** - Capture visual PII (faces, signatures, personal photos)
- **Image queries** - User-uploaded images may contain sensitive content
- **Layout understanding** - Document structure may reveal confidential information
- **Dual storage** - Increased data footprint (text + vision embeddings)
- **GPU processing** - Vision models process potentially sensitive images

**Without v0.2.10/v0.2.11:**
- ❌ Vision embeddings stored unencrypted (visual PII exposure)
- ❌ Image query history in plaintext (privacy violation)
- ❌ No cleanup of vision data (indefinite storage)
- ❌ GDPR non-compliance for visual data

**See:**
- [Security & Privacy Foundation](../../security/README.md)
- [v0.2.10 Roadmap](../../../roadmap/version/v0.2/v0.2.10/)
- [v0.2.11 Roadmap](../../../roadmap/version/v0.2/v0.2.11/)

---

## Design Goals

### 1. Vision-Based Document Understanding
**Problem**: Text extraction misses visual layout, diagrams, and non-textual content.

**Solution**:
- ColPali model integration for vision embeddings
- Dual embedding storage (text + vision)
- Vision-enhanced retrieval
- Layout-aware understanding

**Expected Impact**: Handle PDFs with complex layouts, diagrams, and visual content

### 2. Multi-Modal Retrieval
**Problem**: Can only search by text, missing visual similarity.

**Solution**:
- Image-based queries ("show me documents with charts")
- Hybrid text + vision retrieval
- Visual similarity scoring
- Fusion of text and vision results

**Expected Impact**: Find documents by visual content, not just keywords

### 3. GPU Acceleration
**Problem**: Vision models are computationally expensive.

**Solution**:
- GPU detection and utilization (CUDA)
- Graceful CPU fallback
- Batch processing optimisation
- Memory-efficient vision processing

**Expected Impact**: Fast vision processing with GPU, acceptable performance on CPU

---

## Key Features

- **ColPali Integration**: State-of-the-art vision model for document understanding
- **Dual Embeddings**: Store both text and vision representations
- **Vision Retrieval**: Query by visual similarity
- **Hybrid Mode**: Combine text and vision for best results
- **GPU Support**: Hardware acceleration for vision processing

---

## Success Criteria

- Vision embeddings capture layout and diagrams
- Hybrid retrieval combines text + vision effectively
- GPU acceleration provides >5x speedup vs CPU
- Works on documents with complex visual layouts
- Graceful degradation when GPU unavailable

---

## Total Effort

**140-180 hours** for ColPali integration and vision retrieval

**Timeline:** ~3-5 months with single developer

**Dependencies:** Requires v0.4.0 completion (knowledge graphs)

**Hardware:** CUDA-compatible GPU recommended (minimum 8GB VRAM)

---

## Privacy & Security Considerations

v0.5 processes visual content which may contain sensitive information. All features **must** integrate with v0.2.10/v0.2.11 privacy infrastructure.

### Data Privacy Requirements

| Feature | Data Stored | Privacy Mitigation | TTL |
|---------|-------------|-------------------|-----|
| **Vision Embeddings** | Image embeddings (768-dim vectors) | Encrypted storage, session isolation | 180 days |
| **Image Queries** | Query image hashes | Hash images (NOT store originals), temp processing | Immediate deletion |
| **Dual Storage** | Text + vision embeddings | Encrypted database, 0o600 permissions | 180 days |
| **GPU Processing** | Temporary image tensors | In-memory only, cleared after processing | N/A (memory) |

### Privacy-by-Design Principles

**1. Visual PII Detection:**
```python
# Detect visual PII before processing
from ragged.privacy import contains_visual_pii

image_path = Path("user_uploaded.jpg")
if contains_visual_pii(image_path):
    logger.warning("Visual PII detected (faces/signatures) - processing with encryption")
    # Flag for encrypted storage
```

**2. Temporary Image Processing:**
```python
# Images processed in memory, never persisted
def process_image_query(image: PIL.Image) -> np.ndarray:
    """Process image query without storing."""
    # Convert to tensor (in-memory)
    tensor = transform(image)

    # Generate embedding (in-memory)
    with torch.no_grad():
        embedding = model(tensor)

    # Image and tensor garbage collected immediately
    return embedding.cpu().numpy()
# Image data never written to disk
```

**3. Encrypted Vision Storage:**
```python
# Vision embeddings encrypted at rest
from ragged.privacy import EncryptionManager

encryption = EncryptionManager()

# Store dual embeddings
vision_db_path = Path("~/.ragged/vectors/vision.db")
vision_db_path.chmod(0o600)  # User-only permissions

# Encrypt embedding before storage
encrypted_embedding = encryption.encrypt(embedding.tobytes())
db.store(doc_id, encrypted_embedding)
```

**4. Image Query Hashing:**
```python
# Never store original images
from ragged.privacy import hash_image

query_image = PIL.Image.open("query.jpg")
image_hash = hash_image(query_image)  # SHA-256 hash

# Log hash only (not image)
logger.info(f"Image query processed: {image_hash}")

# Image deleted immediately after processing
query_image.close()
del query_image
```

**5. GDPR Compliance:**
```bash
# User can export vision data
ragged privacy export --include-vision --output my-vision-data.json

# User can delete all vision data
ragged privacy delete --confirm  # Includes vision embeddings

# User can view vision storage
ragged privacy status
# Output:
#   Vision Embeddings: 1,234 documents (250 MB)
#   Oldest Data:       45 days ago
#   Encryption:        Enabled
```

### Privacy Risk Assessment

| Feature | Privacy Risk | Risk Score | Mitigation |
|---------|-------------|-----------|-----------|
| **ColPali Model** | Medium | 90/100 | Local inference only, no external API calls |
| **Vision Embeddings** | **HIGH** | **88/100** | Encrypted storage, session isolation, TTL |
| **Image Queries** | **HIGH** | **92/100** | Hashing only, immediate deletion, no storage |
| **Dual Storage** | Medium | 89/100 | Encrypted DB, file permissions 0o600, TTL |
| **GPU Processing** | Low | 95/100 | In-memory only, immediate cleanup |

**Interpretation:** 88-95/100 = Excellent privacy with strong visual PII protections

### Visual PII Considerations

**Types of Visual PII:**
- Faces (biometric data under GDPR)
- Signatures (authentication identifiers)
- Personal photos (intimate content)
- ID documents (passports, driver's licenses)
- Medical images (protected health information)
- Financial documents (bank statements, invoices)

**Detection Strategy:**
- Face detection (using lightweight model)
- Signature detection (stroke analysis)
- ID document patterns (template matching)
- Medical image markers (DICOM headers)

**Handling:**
- Warn user if visual PII detected
- Require explicit consent to process
- Encrypt all vision data by default
- Shorter TTL for high-risk content (30 days)

### Security Testing Requirements

**For ALL v0.5 features:**
- [ ] No original images stored on disk
- [ ] Vision embeddings encrypted at rest
- [ ] Image query hashing verified
- [ ] Temporary processing files cleaned up
- [ ] GPU memory cleared after processing
- [ ] File permissions 0o600 enforced
- [ ] Session isolation tested
- [ ] TTL cleanup functional
- [ ] GDPR deletion complete (vision data removed)
- [ ] Visual PII detection tested (faces, signatures)

**Security Agent Workflow:**

Use `codebase-security-auditor` agent:
1. After implementing vision processing pipeline
2. Before committing image handling code
3. Before release
4. After ColPali model updates

### User Control & Transparency

**Privacy Configuration:**
```bash
# Configure vision data retention
ragged config set vision.ttl_days 180
ragged config set vision.enable_face_detection true
ragged config set vision.require_consent_for_pii true

# Disable vision features (opt-out)
ragged config set vision.enabled false

# View vision statistics
ragged vision stats
```

**Privacy Warnings:**
- First use: "ColPali will process document images locally - no data sent externally"
- Image upload: "Processing image (will be deleted after embedding generation)"
- Visual PII detected: "Image contains faces/signatures - encrypted storage will be used"
- GPU processing: "Using GPU for vision processing (faster, still private)"

---

## Out of Scope (Deferred to v1.0+)

❌ **Not in v0.5**:
- Web UI (v1.0)
- Multi-user support (v1.0)
- API server (v1.0)
- Cloud deployment (v1.0)

---

## Related Documentation

- [v0.4 Planning](../v0.4/) - Personal memory & knowledge graphs
- [v1.0 Planning](../v1.0/) - Production release
- [Roadmap: v0.5.0](../../../roadmap/version/v0.5.0/) - Detailed implementation plan
- [Architecture](../../architecture/) - System architecture

---
