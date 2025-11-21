# ADR 003: Messy Document Intelligence Architecture (v0.3.5)

**Date:** 2025-11-21

**Status:** Accepted

**Context:** v0.3.5 - Automated PDF correction and exceptional markdown conversion

**Decision Makers:** Architecture Advisor (Opus), UX Architect (Sonnet)

---

## Context and Problem Statement

We need to design an automated system that detects and corrects common issues in messy PDFs (rotated pages, misordered pages, duplicates, poor scans) and produces exceptional-quality markdown output. The system must be completely transparent to users while maintaining full traceability of all corrections applied.

**Key Requirements:**
- Fully automated correction (no user intervention)
- High accuracy (>95% rotation, >99% duplicates, >90% ordering)
- Exceptional markdown quality (98%+ OCR confidence target)
- Complete transparency via metadata
- Original PDFs never modified
- Performance: <60s total overhead for typical messy PDF

**User Experience Goal:** `ragged add messy.pdf` → Just works™

---

## Decision Drivers

1. **Accuracy vs Speed:** Researchers value accuracy over speed
2. **Trust Building:** Users must trust automated corrections
3. **Privacy First:** All processing local, no cloud dependencies
4. **Maintainability:** Clean separation of concerns, testable components
5. **Storage Management:** Balance between performance and disk space
6. **Extensibility:** Support future enhancements (ML models, new correction types)

---

## Considered Options

### Integration Architecture

**Option A: Pre-processor Pattern** ✅ **SELECTED**
- Separate modules for analysis and correction
- Integration via pipeline coordinator
- Non-invasive to existing DoclingProcessor

**Option B: Integrated Processing**
- Embed correction logic in DoclingProcessor
- Single processing pipeline
- Violates single responsibility principle

**Option C: Wrapper/Decorator Pattern**
- Wrap existing processor with corrections
- Non-invasive but abstraction overhead
- Complex for deep integration needs

### Detection Strategy

**Option A: Multi-pass Analysis** ✅ **SELECTED**
- Parallel detectors optimised for specific tasks
- Easier to maintain and extend
- Potential for multiple PDF parses

**Option B: Single-pass Analysis**
- Better performance (single PDF parse)
- Complex implementation, harder to extend
- Risk of detector interference

### Storage Strategy

**Option A: Permanent Corrected Storage** ✅ **SELECTED**
- Store both original and corrected PDFs
- No reprocessing needed
- 2× storage requirement acceptable

**Option B: On-demand Correction**
- Minimal storage (only original)
- Performance penalty on each access
- No correction history

---

## Decision Outcome

### Chosen Architecture: **Pre-processor Pattern with Multi-pass Analysis**

**Module Structure:**
```
src/
├── correction/
│   ├── analyzer.py              # PDFAnalyzer - coordinates detection
│   ├── corrector.py             # PDFCorrector - applies fixes
│   ├── detectors/
│   │   ├── rotation.py          # RotationDetector (text orientation)
│   │   ├── ordering.py          # PageOrderDetector (page numbers, flow)
│   │   ├── duplicates.py        # DuplicateDetector (perceptual hashing)
│   │   └── quality.py           # QualityDetector (OCR confidence)
│   ├── transformers/
│   │   ├── rotation.py          # RotationTransformer (pypdf)
│   │   ├── ordering.py          # PageReorderTransformer
│   │   └── duplicates.py        # DuplicateRemover
│   └── schemas.py               # Pydantic models
├── processing/
│   ├── pipeline.py              # EnhancedDocumentPipeline
│   └── docling_processor.py    # Existing (unchanged)
```

**Processing Flow:**
```
User: ragged add messy.pdf
    ↓
PDF Analysis (parallel detectors)
    ├─ Rotation detection (text orientation + image analysis)
    ├─ Page order detection (page numbers + content flow)
    ├─ Duplicate detection (perceptual hashing)
    └─ Quality scoring (per-page OCR confidence)
    ↓
Decision Engine
    ↓
PDF Correction (if issues detected)
    ├─ Transactional correction with checkpoints
    ├─ Quality verification after each correction
    ├─ Automatic rollback if quality degrades
    └─ Store corrected PDF + metadata
    ↓
DoclingProcessor (OCR on corrected PDF)
    ↓
Exceptional Markdown Conversion
    ↓
Store + Index
```

**Storage Architecture:**
```
documents/
├── document.pdf                 # Original (never modified)
├── document.md                  # Clean markdown output
└── .ragged/
    └── document/
        ├── corrected.pdf        # Corrected version
        ├── metadata.json        # Document metadata
        ├── corrections.json     # Applied corrections
        ├── uncertainties.json   # Low-confidence sections
        ├── page_mapping.json    # Original ↔ corrected pages
        ├── quality_report.json  # Detailed quality metrics
        └── figures/             # Extracted images
```

---

## Detection Algorithms

### Rotation Detection (Hybrid Approach)

**Primary:** Text orientation analysis
- Extract text with multiple rotation attempts (0°, 90°, 180°, 270°)
- Score based on readable words ratio
- Use language detection confidence

**Secondary:** Image-based validation
- Detect horizontal/vertical lines
- Check aspect ratios of detected objects
- Validate against text detection results

**Confidence threshold:** 0.85 (85% confidence required to apply rotation)

### Page Order Detection (Multi-signal)

**Signal 1:** Page number extraction
- Regex patterns for common formats (Page X, X/Y, -X-)
- Position-based scoring (footer/header locations)

**Signal 2:** Content flow analysis
- Sentence continuation detection
- Heading hierarchy validation
- Reference tracking (Figure X, Table Y)

**Confidence threshold:** 0.80 (agreement between signals required)

### Duplicate Detection (Layered)

**Layer 1:** Quick hash (first pass)
- MD5 of rendered page at low resolution
- Catches exact duplicates fast

**Layer 2:** Perceptual hash (second pass)
- pHash or dHash for near-duplicates
- Handles minor scanning variations

**Layer 3:** Content comparison (validation)
- Text extraction and similarity scoring
- Structural element comparison

**Confidence threshold:** 0.95 (95% similarity for duplicate removal)

---

## Correction Strategy: Transactional with Verification

**Key Innovation:** Quality verification after each correction

```python
class CorrectionTransaction:
    """Transactional correction with automatic rollback"""

    def apply(self, transformer, issue):
        # Create checkpoint before correction
        checkpoint = self.working_copy.copy()
        self.checkpoints.append(checkpoint)

        try:
            transformer.transform(self.working_copy, issue)
        except Exception:
            # Rollback to checkpoint on failure
            self.working_copy = checkpoint
            raise

    def verify_improvement(self) -> bool:
        """Verify corrections improved quality"""
        metrics_after = self._capture_metrics()

        # Must improve text quality AND preserve structure
        return (
            metrics_after.readable_text_ratio >
            metrics_before.readable_text_ratio * 1.1
        ) and (
            metrics_after.detected_elements >=
            metrics_before.detected_elements * 0.95
        )
```

**Rollback triggers:**
- Any correction that degrades quality
- OCR confidence drops by >5%
- Structural elements lost (headings, tables, figures)

---

## UX Design: Progressive Disclosure

### Default CLI Output (Enhanced Summary)

**Normal quality (>80%):**
```bash
✓ Auto-corrected: 23 rotated pages, 4 duplicates removed
✓ OCR processing (1m 32s)
✓ Quality: 94% (Good) • 2,847 chunks indexed

View details: ragged show corrections document.pdf
```

**Low quality (<70%):**
```bash
⚠ Quality: 62% (Poor) • 1,203 chunks indexed
  • 45 sections with low confidence (<70%)

Recommend: Review uncertain sections
  ragged show uncertainties document.pdf
```

### Markdown Metadata: Hybrid Approach

**Document-level (YAML front matter):**
```yaml
---
title: Document Title
source: original.pdf
ocr_confidence: 0.942
quality_grade: Excellent
corrections_applied: [rotated_pages, duplicates_removed]
pages_original: 45
pages_corrected: 42
---
```

**Section-level (HTML comments - invisible):**
```markdown
<!-- page:42 confidence:0.99 -->

## Section Title

Content with <!--conf:0.72-->moderate confidence<!--/conf--> inline markers.
```

**Detailed data (separate JSON files):**
- `corrections.json` - What was corrected
- `uncertainties.json` - Low-confidence spans
- `page_mapping.json` - Original ↔ corrected pages
- `quality_report.json` - Detailed metrics

### Uncertainty Marking: Graduated Approach

**High confidence (85-100%):** No marking
**Moderate confidence (60-85%):** HTML comments (hidden)
**Low confidence (<60%):** Visible footnote
**Very low (<40%):** Placeholder with PDF reference

### Quality Scoring: Traffic Light System

| Score | Grade | Display | User Action |
|-------|-------|---------|-------------|
| 90-100% | Excellent | ✓ Quality: 98% (Excellent) | None |
| 80-89% | Good | ✓ Quality: 85% (Good) | None |
| 70-79% | Fair | ⚠ Quality: 74% (Fair) | Suggest review |
| <70% | Poor | ⚠ Quality: 62% (Poor) | Recommend check |

---

## Configuration Schema

```python
class CorrectionConfig(BaseModel):
    # Global settings
    enabled: bool = True
    auto_correct: bool = True
    preserve_originals: bool = True

    # Confidence thresholds
    confidence_thresholds:
        rotation: float = 0.85
        ordering: float = 0.80
        duplicate: float = 0.95
        quality: float = 0.70

    # Correction settings
    correction:
        max_attempts: int = 3
        verify_improvement: bool = True
        rollback_on_failure: bool = True

    # Storage settings
    storage:
        corrected_path: Path = "data/documents/corrected"
        metadata_path: Path = "data/documents/.ragged"
        compression: bool = True
```

---

## CLI Command Structure

```bash
ragged add <document>                    # Ingest with auto-correction
  --verbose                              # Detailed progress
  --show-corrections                     # Display corrections after

ragged show <document>                   # Document overview
  quality                                # Quality report
  corrections                            # Corrections applied
  uncertainties                          # Low-confidence sections
  pages                                  # Page mapping
    --original <page>                    # Look up original page
    --corrected <page>                   # Look up corrected page

ragged check                             # Check all documents
  quality                                # Quality overview
  uncertainties                          # Docs with uncertainties

ragged cite <document>                   # Citation helper
  --original-page <page>                 # Citation info for page
```

---

## Consequences

### Positive

✅ **Clean Separation:** Analysis, correction, and OCR are independent
✅ **Testable:** Each detector/transformer is unit-testable
✅ **Extensible:** Easy to add new detection/correction types
✅ **Safe:** Transactional corrections with automatic rollback
✅ **Transparent:** Complete audit trail of all corrections
✅ **User Trust:** Progressive disclosure builds confidence
✅ **Maintainable:** Clear module boundaries, single responsibility

### Negative

⚠️ **Storage Overhead:** 2× PDF storage (original + corrected)
⚠️ **Processing Time:** Multi-pass analysis adds overhead (<60s acceptable)
⚠️ **Complexity:** More modules to maintain than integrated approach
⚠️ **False Positives:** Incorrect corrections possible (mitigated by verification)

### Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Incorrect rotation | High | Medium | High confidence threshold (0.85), multiple signals |
| False duplicate removal | High | Low | Very high threshold (0.95), perceptual hashing |
| Wrong page order | High | Medium | Conservative reordering, rollback on quality drop |
| Storage explosion | Medium | High | Compression, configurable retention |
| Performance degradation | Medium | Low | Timeouts, parallel processing, early exit |

---

## Implementation Roadmap

### Phase 1: Core Detection & Correction (12-16h)
- Implement PDFAnalyzer with parallel detectors
- Implement PDFCorrector with transactional corrections
- Basic rotation, duplicate, and ordering detection

### Phase 2: Quality & Verification (8-10h)
- Implement quality scoring system
- Add correction verification logic
- Implement automatic rollback on quality degradation

### Phase 3: Exceptional Markdown (6-8h)
- Enhanced MarkdownConverter with structure preservation
- Figure and table extraction
- LaTeX equation preservation
- Page marker insertion

### Phase 4: UX & CLI (6-8h)
- CLI output formatting (traffic light system)
- Metadata file generation (corrections.json, etc.)
- `ragged show` commands for quality/corrections/uncertainties

### Phase 5: Integration & Testing (8-10h)
- Full pipeline integration
- Comprehensive testing on diverse PDFs
- Performance benchmarking
- Edge case handling

**Total estimated effort:** 40-52 hours

---

## Dependencies

**Additional libraries:**
```toml
pypdf = "^3.17.0"          # BSD - PDF manipulation
img2pdf = "^0.5.1"         # LGPL - Image to PDF conversion
scikit-image = "^0.22.0"   # BSD - Image quality assessment
```

All dependencies are GPL-3.0 compatible.

---

## Success Criteria

**Functional:**
- ✅ Rotation detection accuracy >95%
- ✅ Duplicate detection accuracy >99%
- ✅ Page ordering accuracy >90%
- ✅ Automated correction works on 95%+ of messy PDFs
- ✅ Markdown quality: 98%+ OCR confidence (Good documents)

**Performance:**
- ✅ PDF analysis <10s for 100-page document
- ✅ PDF correction <30s for 100-page document
- ✅ Total overhead <60s for typical messy PDF

**UX:**
- ✅ Fully automated (no user intervention)
- ✅ Clear progress messages with quality indicators
- ✅ Metadata accessible via CLI
- ✅ Original PDFs never modified

**Code Quality:**
- ✅ 100% test coverage for correction logic
- ✅ All unit tests passing
- ✅ Integration tests for full pipeline
- ✅ Type hints complete
- ✅ Docstrings complete (British English)

---

## Related Documentation

- [v0.3.5 Roadmap](../../roadmap/version/v0.3/v0.3.5.md) - Implementation plan
- [v0.3.0 Implementation](../../implementation/version/v0.3/v0.3.0/) - Docling integration
- [ADR 001: Docling Integration](001-docling-integration.md) - OCR foundation
- [ADR 002: Intelligent Routing](002-intelligent-routing.md) - Quality-based routing

---

**Status:** Accepted (Phase 1 - Design Complete)

**Next Steps:** Begin Phase 2 implementation (PDF Analysis)
