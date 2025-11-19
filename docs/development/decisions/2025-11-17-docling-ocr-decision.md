# Architectural Decision: Modern OCR Stack (Docling + PaddleOCR)

**Date:** 2025-11-17

**Status:** Approved for v0.3.5

**Decision Maker:** ragged development team

**Context:** v0.3.0 planning, state-of-the-art OCR research

---

## Decision

Replace Tesseract + Camelot with **Docling + PaddleOCR** for document processing in v0.3.5.

**Primary:** Docling (MIT licensed)
**Fallback:** PaddleOCR (Apache 2.0 licensed)

---

## Context

### Current State (v0.2.x)

**OCR Stack:**
- pytesseract for OCR
- camelot-py for table extraction
- PyMuPDF for PDF parsing

**Problems:**
1. Tesseract struggles with messy, rotated, or poor-quality scans
2. Camelot table extraction accuracy limited
3. No layout analysis or reading order preservation
4. No formula recognition
5. No document structure understanding

### Requirements for v0.3.0

1. Handle messy scanned PDFs (rotated, skewed, poor quality)
2. Extract tables with high accuracy
3. Preserve document structure (headings, lists, reading order)
4. Support formula recognition
5. Enable exceptional Markdown conversion
6. Maintain GPL-3.0 license compatibility
7. Support automated PDF correction workflow

---

## Research Summary

### State-of-the-Art Tools Evaluated

**1. Docling** (IBM Research, 2024)
- **Type:** Modern computer vision + OCR hybrid
- **Strengths:**
  - 30× faster than traditional OCR
  - 97.9% accuracy on complex table extraction
  - Layout analysis (DocLayNet model)
  - Table structure (TableFormer)
  - Reading order preservation
  - Built-in EasyOCR integration for scanned docs
  - Simple API (5 lines of code)
  - Active development (new models in 2025)
- **License:** MIT (GPL-3.0 compatible ✓)
- **Performance:** Born-digital PDFs <1s/page, scanned 2-3s/page

**2. PaddleOCR** (Baidu, 2024)
- **Type:** Deep learning OCR
- **Strengths:**
  - State-of-the-art accuracy on poor quality scans
  - Only tool handling rotated/skewed text with slanted bounding boxes
  - 80+ languages supported
  - PP-StructureV3 for tables, formulas, handwriting
  - Fully offline/privacy-preserving
  - PaddleOCR-VL (0.9B params) surpasses DeepSeek-OCR
- **License:** Apache 2.0 (GPL-3.0 compatible ✓)
- **Performance:** 5-8s/page on messy scans with GPU

**3. Tesseract** (Google, traditional)
- **Type:** Traditional OCR
- **Strengths:**
  - Mature, battle-tested
  - 100+ languages
  - Best CPU-only performance
- **Weaknesses:**
  - Struggles with complex layouts
  - Poor on low-quality scans
  - No table/formula recognition
  - Word breaking issues
- **License:** Apache 2.0
- **Performance:** 2-4s/page, often misses text

**4. DeepSeek-OCR** (2024)
- **Type:** Vision-language model
- **Strengths:**
  - 100-200 tokens/page (revolutionary compression)
  - 2,500 tokens/second on A100
  - State-of-the-art until surpassed by PaddleOCR-VL
- **Weaknesses:**
  - GPU required (impractical for CPU-only)
  - Can hallucinate with overlapping elements
  - License unclear
- **Performance:** Very fast on GPU, impractical on CPU

---

## Decision Rationale

### Why Docling as Primary?

1. **Perfect for RAG Pipelines:**
   - Designed specifically for AI-ready document conversion
   - Structured output (JSON, Markdown)
   - Integrates with LangChain, LlamaIndex

2. **Comprehensive Features:**
   - Layout analysis out-of-the-box
   - Table extraction (97.9% accuracy)
   - Reading order preservation
   - Formula recognition (coming soon)
   - Image extraction

3. **Performance:**
   - 30× faster than traditional OCR pipelines
   - Born-digital PDFs: <1 second/page
   - Scanned docs: 2-3 seconds/page (with built-in EasyOCR)

4. **Developer Experience:**
   - Simple API (5 lines of code)
   - Well-documented
   - Active development
   - MIT licensed

5. **Future-Proof:**
   - New models released in 2025 (Heron, SmolDocling, Granite-Docling)
   - Growing ecosystem
   - IBM Research backing

### Why PaddleOCR as Fallback?

1. **Handles Worst Cases:**
   - Best performance on messy, rotated, poor-quality scans
   - Only tool with slanted bounding boxes (for skewed text)
   - State-of-the-art on difficult documents

2. **Privacy:**
   - Fully offline/on-prem
   - No external API calls
   - Important for ragged's privacy-first philosophy

3. **Versatility:**
   - 80+ languages
   - Handwriting recognition
   - Custom training possible

4. **Active Development:**
   - PaddleOCR-VL (2024) surpassed DeepSeek-OCR
   - Continuous improvements

### Why Not Tesseract?

**Tesseract was originally planned for v0.3.0 but:**

1. Poor performance on messy documents (ragged's stated use case)
2. No layout analysis
3. No table structure recognition
4. No formula recognition
5. Word breaking issues
6. 30× slower than Docling
7. Lower accuracy than modern deep learning approaches

**Verdict:** Tesseract is outdated for ragged's requirements

---

## Architecture Design

### Processing Pipeline

```
Document Ingestion
    ↓
Document Type Classification
    ↓
┌─────────────┬──────────────┐
│ Born-Digital│ Scanned/Messy│
└──────┬──────┴──────┬───────┘
       ↓             ↓
  DOCLING       DOCLING
  (CV-based)    (+ EasyOCR)
       ↓             ↓
  Confidence   Confidence
    Check        Check
       ↓             ↓
  High? ──Yes─→ Output
       │
      No
       ↓
  PADDLEOCR
  (Fallback)
  - Poor quality
  - Rotated text
  - Skewed scans
       ↓
    Output
```

### Confidence-Based Routing

**Thresholds:**
- High confidence: > 85% → Use Docling results
- Medium confidence: 70-85% → Consider fallback
- Low confidence: < 70% → Always use PaddleOCR fallback

**Signals:**
- OCR confidence scores
- Layout analysis confidence
- Number of unrecognised elements
- Text density heuristics

### Implementation Strategy

**Phase 1 (v0.3.5):** Primary Processor
- Integrate Docling as primary processor
- Remove Tesseract dependency
- Remove Camelot dependency
- Keep Ollama llava for vision

**Phase 2 (v0.3.5):** Quality Assessment
- Implement document type classification
- Add confidence scoring
- Engine selection logic

**Phase 3 (v0.3.5):** Fallback Integration
- Add PaddleOCR as fallback engine
- Implement confidence-based routing
- Test on worst-case documents

**Phase 4 (v0.3.6):** Automated Correction
- Build on Docling/PaddleOCR foundation
- Auto-rotate, auto-reorder, duplicate removal
- Exceptional Markdown conversion

---

## Trade-Offs

### Advantages

✓ **Quality:** 30× faster, 97.9% table accuracy, layout-aware
✓ **Features:** Tables, formulas, reading order, structure
✓ **Simplicity:** Cleaner API, easier integration
✓ **Future-Proof:** Active development, new models
✓ **License:** MIT + Apache 2.0 (GPL-3.0 compatible)
✓ **Performance:** Sub-second for born-digital PDFs
✓ **Fallback:** PaddleOCR handles worst cases

### Disadvantages

⚠ **GPU:** Docling doesn't use GPU effectively yet (slower than expected)
⚠ **Dependencies:** PaddlePaddle framework adds complexity
⚠ **Learning Curve:** New tools to learn
⚠ **Scanned Docs:** Still relies on OCR (EasyOCR/PaddleOCR)

### Mitigations

- Confidence-based routing ensures quality
- PaddleOCR fallback handles difficult cases
- Simple Docling API reduces learning curve
- CPU performance still better than Tesseract

---

## Implementation Impact

### Files Created

```
src/ingestion/
├── document_processor.py       # Main processor (Docling + PaddleOCR)
├── quality_assessor.py         # Confidence scoring, engine selection
└── ocr_engines/
    ├── __init__.py
    ├── base.py                 # Abstract engine interface
    ├── docling_engine.py       # Docling implementation
    └── paddle_engine.py        # PaddleOCR implementation
```

### Files Removed

```
# Removed in v0.3.5:
- All pytesseract usage
- All camelot-py usage
```

### Dependencies Changed

**Removed:**
```toml
pytesseract = "^0.3.10"         # REMOVED
camelot-py = "^0.11.0"          # REMOVED
```

**Added:**
```toml
docling = "^2.0.0"              # MIT
paddleocr = "^2.8.0"            # Apache 2.0
paddlepaddle = "^2.6.0"         # Apache 2.0
opencv-python = "^4.8.0"        # BSD (already planned)
Pillow = "^10.0.0"              # HPND (already planned)
```

### Migration Path

**For Users:**
- No breaking changes (automatic upgrade)
- Better quality immediately
- Faster processing
- New capabilities (tables, formulas, structure)

**For Developers:**
- Document processor API unchanged
- Internal implementation replaced
- Better testing with confidence scores
- New debugging capabilities

---

## Performance Targets

### Processing Speed

| Document Type | Tesseract (v0.2) | Docling (v0.3) | Improvement |
|--------------|------------------|----------------|-------------|
| Born-digital PDF (100 pages) | 100 pages/min | 1000+ pages/min | 10× faster |
| Clean scan (100 pages) | 50 pages/min | 500 pages/min | 10× faster |
| Messy scan (100 pages) | 30 pages/min | 100 pages/min | 3× faster |

### Quality Metrics

| Metric | Tesseract (v0.2) | Docling+Paddle (v0.3) |
|--------|------------------|----------------------|
| Born-digital accuracy | 95% | 99% |
| Clean scan accuracy | 85% | 98% |
| Messy scan accuracy | 60-70% | 95% |
| Table extraction | 70% | 97.9% |
| Layout preservation | No | Yes |
| Reading order | No | Yes |

---

## Validation Plan

### Before Full Implementation

1. **Prototype Testing (8 hours):**
   - Install Docling
   - Test on 10-20 representative documents
   - Measure accuracy, speed, structured output quality

2. **Fallback Testing (4 hours):**
   - Install PaddleOCR
   - Test on worst-case documents
   - Validate confidence routing logic

3. **Comparison Benchmark (4 hours):**
   - Run Tesseract vs Docling vs PaddleOCR
   - Measure accuracy, speed, quality
   - Document results

4. **Decision Point:**
   - If results validate research: Proceed with implementation
   - If issues found: Adjust architecture or investigate alternatives

### Success Criteria

✓ Docling accuracy > 95% on born-digital PDFs
✓ Docling + PaddleOCR accuracy > 90% on messy scans
✓ Processing speed 5× faster than Tesseract
✓ Table extraction accuracy > 90%
✓ Layout preservation working correctly
✓ Confidence scoring identifies difficult cases

---

## Risks & Contingencies

### Risk 1: Docling Performance Issues

**Risk:** Docling may be slower than benchmarks suggest (GPU utilisation issues noted)

**Mitigation:**
- Test on real hardware before full implementation
- PaddleOCR can be primary if Docling underperforms
- Can optimise with batch processing

**Contingency:**
- Revert to Tesseract (low likelihood)
- Use PaddleOCR as primary (medium likelihood)
- Wait for Docling GPU improvements (low likelihood)

### Risk 2: PaddleOCR Complexity

**Risk:** PaddlePaddle framework adds dependency complexity

**Mitigation:**
- Well-documented installation
- Docker containers isolate dependencies
- Fallback is optional (not required for basic usage)

**Contingency:**
- Use EasyOCR instead (simpler, slightly less accurate)
- Make PaddleOCR optional extra

### Risk 3: License Changes

**Risk:** Docling or PaddleOCR could change licenses

**Mitigation:**
- Pin to specific versions
- Both tools have permissive licenses unlikely to change
- Active communities would reject license changes

**Contingency:**
- Fork last MIT/Apache version
- Switch to EasyOCR (Apache 2.0)

---

## References

### Research Papers

1. **Docling:** https://arxiv.org/abs/2408.09869
2. **TableFormer:** https://arxiv.org/abs/2203.01017
3. **DocLayNet:** https://arxiv.org/abs/2206.01062
4. **PaddleOCR-VL:** https://arxiv.org/abs/2412.16263
5. **DeepSeek-OCR:** https://github.com/deepseek-ai/DeepSeek-VL2

### Documentation

- Docling: https://github.com/DS4SD/docling
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- Tesseract: https://github.com/tesseract-ocr/tesseract

### Benchmarks

- OCR Comparison: https://github.com/factful/ocr_testing
- Table Extraction: PubTables-1M benchmark
- Document AI: OmniDocBench

---

## Related Documentation

- [v0.3.5 Implementation Plan](../roadmap/version/v0.3.0/IMPLEMENTATION-PLAN.md#v035---modern-document-processing-55-62-hours)
- [Multi-Modal Support Feature](../roadmap/version/v0.3.0/features/multi-modal-support.md) (needs update)
- [v0.3.0 Roadmap](../roadmap/version/v0.3.0/README.md)

---

**Approved By:** ragged development team

**Implementation Target:** v0.3.5 (Q2 2026)

