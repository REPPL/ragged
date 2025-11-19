# v0.3.4 - Modern Document Processing (Progressive Enhancement)

**Category:** State-of-the-Art OCR & Document Intelligence
**Total Estimated Time:** 52-63 hours
**Strategy:** Progressive Enhancement (MVP → Routing → Optional Features)

---

## Overview

v0.3.4 transforms document processing from basic PDF text extraction to state-of-the-art layout analysis, table extraction, and OCR capabilities. Due to complexity and dependency concerns, we're implementing this as a **progressive enhancement** across three sub-versions.

### Why Progressive Enhancement?

**Original Plan Issues:**
- Assumes replacing Tesseract/Camelot (they don't exist in codebase)
- PaddleOCR has Python 3.12 compatibility concerns
- Complex installation (~1GB models + C++ dependencies)
- High risk for single monolithic release

**Solution:**
- Ship value incrementally
- Make complex dependencies optional
- Validate architecture with real usage
- Lower risk, faster delivery

---

## Implementation Phases

### Phase 1: v0.3.4a - MVP (Docling Core)
**Status:** Planned
**Effort:** 25-30 hours
**Value:** 80% of benefits
**Timeline:** 2 weeks

**Delivers:**
- Docling integration (MIT-licensed, mature)
- 10-30× faster processing
- 97% table accuracy (TableFormer)
- Layout preservation
- Born-digital PDF optimisation

**What's Excluded:**
- No PaddleOCR (avoid complexity)
- No advanced routing (simple quality check only)
- Minimal vision integration

[→ Full v0.3.4a Roadmap](./v0.3.4a.md)

---

### Phase 2: v0.3.4b - Intelligent Routing
**Status:** Planned
**Effort:** 12-15 hours
**Value:** 15% additional
**Timeline:** After v0.3.4a validated

**Delivers:**
- Comprehensive quality assessment
- Smart routing logic
- Confidence-based processor selection
- Per-page quality scoring

**Prerequisites:**
- v0.3.4a deployed and tested
- User feedback incorporated
- Performance validated

[→ Full v0.3.4b Roadmap](./v0.3.4b.md)

---

### Phase 3: v0.3.4c - PaddleOCR (Optional)
**Status:** Planned
**Effort:** 15-18 hours
**Value:** 5% additional
**Timeline:** Optional, user-demand driven

**Delivers:**
- PaddleOCR as optional dependency
- Handles severely degraded scans
- 80+ language support
- Rotated text handling

**Prerequisites:**
- v0.3.4a + v0.3.4b complete
- User demand for messy document support
- Python 3.12 compatibility confirmed

[→ Full v0.3.4c Roadmap](./v0.3.4c.md)

---

## Performance Targets

| Metric | Current (pymupdf) | v0.3.4a Target | Achievement |
|--------|-------------------|----------------|-------------|
| Born-digital PDF (100 pages) | 5s | 2s | 2.5× faster |
| Table accuracy | Poor/manual | 97% | ✅ Major improvement |
| Layout preservation | None | Full | ✅ New capability |
| Reading order | None | Correct | ✅ New capability |
| Formula recognition | None | Supported | ✅ New capability |

---

## Dependency Strategy

### Required (v0.3.4a)
- `docling` - MIT license, ~50MB, stable API
- `transformers` - Already in project (for sentence-transformers)
- Models: ~200MB (lazy loaded)

### Optional (v0.3.4c)
- `paddleocr` - Apache 2.0, ~500MB framework + models
- Only installed if user needs messy document support
- Graceful degradation if not available

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Python 3.12 compatibility | Make PaddleOCR optional, test thoroughly |
| Large model downloads | Lazy loading, cloud storage option |
| Breaking changes | Migration guide, backwards compatibility |
| Installation complexity | Docker option, clear documentation |
| Performance regression | Benchmarks, rollback plan |

---

## Migration Strategy

### From Current (pymupdf)

**Backwards Compatibility:**
- Keep pymupdf as ultra-lightweight fallback
- Docling becomes default for new documents
- Existing ingested documents unaffected

**Configuration:**
```python
# settings.py
document_processor: str = "docling"  # or "pymupdf" for basic
enable_paddleocr: bool = False  # Optional advanced features
```

**User Impact:**
- Existing workflows continue working
- Opt-in to advanced features
- Clear upgrade documentation

---

## Implementation Order

1. **Start with v0.3.4a** (MVP)
   - Immediate value (80% benefits)
   - Lower risk (no PaddleOCR)
   - 2-week delivery

2. **Validate with users**
   - Gather feedback on Docling
   - Measure actual performance improvements
   - Identify gaps (do we need PaddleOCR?)

3. **Add v0.3.4b** (Routing)
   - Build on validated v0.3.4a
   - Incremental complexity
   - Clear value proposition

4. **Consider v0.3.4c** (PaddleOCR)
   - Only if user demand exists
   - Optional installation
   - Doesn't burden all users

---

## Success Criteria

### v0.3.4a (MVP)
- ✅ 10× faster than pymupdf on born-digital PDFs
- ✅ 97%+ table extraction accuracy
- ✅ Layout preservation working
- ✅ Zero regression on existing documents
- ✅ Installation < 5 minutes

### v0.3.4b (Routing)
- ✅ Accurate born-digital vs scan detection
- ✅ Quality-based routing working
- ✅ No performance regression

### v0.3.4c (PaddleOCR)
- ✅ Optional dependency installable
- ✅ Graceful fallback if unavailable
- ✅ Handles messy documents
- ✅ No impact on users who don't need it

---

## Related Documentation

- [v0.3.4 Original Roadmap](../v0.3.4.md) - Original monolithic plan (for reference)
- [v0.3.4 Implementation Plan](../../../planning/version/v0.3.4-implementation-plan.md) - Architectural analysis
- [v0.3 Overview](../README.md) - All v0.3.x versions

---

**Strategy:** Progressive Enhancement
**First Ship:** v0.3.4a (MVP) in 2 weeks
**Philosophy:** Deliver value incrementally, validate assumptions, reduce risk
