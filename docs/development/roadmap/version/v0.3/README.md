# ragged v0.3.0 Implementation Roadmap

**Version:** v0.3.0

**Status:** Approved

**Last Updated:** 2025-11-17

---

## Executive Summary

This roadmap breaks v0.3.0 (437-501 hours total) into **13 minor releases** delivered over 6-8 months. Each release focuses on specific categories (Core Functionality, Document Intelligence, Configuration, CLI Enhancements) and delivers shippable value.

**Key Innovations:**
- **Modern OCR Stack:** Docling + PaddleOCR (replacing Tesseract)
- **Automated Messy PDF Handling:** Zero user intervention for document correction
- **Configuration Personas:** User-friendly "accuracy", "speed", "balanced" profiles
- **Transparent Processing:** Users always know what ragged is doing
- **Proper Agent Usage:** Documentation quality maintained throughout

---

## Total Effort Breakdown

| Category | Hours | Percentage |
|----------|-------|------------|
| Implementation | 334-390h | 68-78% |
| Documentation & Agents | 103-111h | 22-32% |
| **Total** | **437-501h** | **100%** |

**Timeline Estimates:**
- At 10 hours/week: 44-50 weeks (10-12 months)
- At 15 hours/week: 29-34 weeks (7-8 months)

---

## Minor Version Releases

### [v0.3.1 - Foundation & Metrics](./v0.3.1.md) (30 hours)

**Category:** Quality & Evaluation Infrastructure

Establish metrics BEFORE any improvements to enable data-driven development.

**Deliverable:** Objective quality metrics, baseline scores for comparison

---

### [v0.3.2 - Configuration Transparency](./v0.3.2.md) (28-34 hours)

**Category:** User Experience & Configuration

Transparent, customisable configuration with personas.

**Deliverable:** "accuracy", "speed", "balanced" profiles, `ragged explain` command

---

### [v0.3.3 - Advanced Query Processing](./v0.3.3.md) (53-55 hours)

**Category:** Core Retrieval Functionality

State-of-the-art retrieval techniques.

**Deliverable:** 10-20% quality improvement, MRR@10 > 0.75

---

### [v0.3.4 - Intelligent Chunking](./v0.3.4.md) (38-40 hours)

**Category:** Core Chunking Intelligence

Topic-coherent chunks with parent-child relationships.

**Deliverable:** Semantic and hierarchical chunking strategies

---

### [v0.3.5 - Modern Document Processing](./v0.3.5.md) (55-62 hours)

**Category:** State-of-the-Art OCR & Document Intelligence

Replace Tesseract + Camelot with Docling + PaddleOCR.

**Deliverable:** 30× faster processing, 97.9% table accuracy, automatic messy PDF handling

---

### [v0.3.6 - Messy Document Intelligence](./v0.3.6.md) (49-57 hours)

**Category:** Automated Document Correction & Exceptional Markdown (KILLER FEATURE)

Fully automated PDF correction with exceptional markdown conversion.

**Deliverable:** Auto-rotate, auto-reorder, duplicate removal, 98% OCR confidence

---

### [v0.3.7 - VectorStore Abstraction](./v0.3.7.md) (16-22 hours)

**Category:** API Foundation for v0.4 LEANN

Clean abstraction for multi-backend support.

**Deliverable:** VectorStore interface, ChromaDB refactor

---

### [v0.3.8 - Production Data & Generation](./v0.3.8.md) (68-74 hours)

**Category:** Production-Ready Features

Versioned documents, rich queries, transparent reasoning.

**Deliverable:** RAGAS > 0.80, chain-of-thought, enhanced citations

---

### [v0.3.9 - Developer Experience I](./v0.3.9.md) (20-24 hours)

**Category:** CLI - Interactive & Debug

Exploratory workflows and debugging tools.

**Deliverable:** REPL interface, step-by-step execution

---

### [v0.3.10 - Performance & Quality Tools](./v0.3.10.md) (19-24 hours)

**Category:** CLI - Measurement & Optimisation

Bottleneck identification and quality dashboards.

**Deliverable:** Performance profiling, quality metrics

---

### [v0.3.11 - Automation & Templates](./v0.3.11.md) (18-24 hours)

**Category:** CLI - Workflow Automation

Template-based queries and testing tools.

**Deliverable:** Jinja2 templates, config validation utilities

---

### [v0.3.12 - Production Operations](./v0.3.12.md) (17-23 hours)

**Category:** CLI - Production Monitoring

Production monitoring and automation.

**Deliverable:** Watch mode, scheduled operations

---

### [v0.3.13 - Polish & Integration](./v0.3.13.md) (26-32 hours)

**Category:** API, Web, Final UX

REST API, refined UX, accessibility, complete documentation.

**Deliverable:** FastAPI server, accessibility, comprehensive docs

---

## Category Distribution

| Category | Versions | Total Hours | Percentage |
|----------|----------|-------------|------------|
| **Core Functionality** | v0.3.3, v0.3.4 | 91-95h | 21% |
| **Document Intelligence** | v0.3.5, v0.3.6 | 104-119h | 24% |
| **Quality & Metrics** | v0.3.1, v0.3.10 | 49-54h | 11% |
| **Configuration & UX** | v0.3.2 | 28-34h | 6% |
| **Production Features** | v0.3.8 | 68-74h | 15% |
| **Developer Experience** | v0.3.9, v0.3.11, v0.3.12 | 55-71h | 14% |
| **API & Integration** | v0.3.7, v0.3.13 | 42-54h | 10% |

---

## Success Metrics

### Performance Targets

| Metric | v0.2 | v0.3 Target |
|--------|------|-------------|
| **Retrieval Quality** | MRR@10 ~0.60 | > 0.75 |
| **Answer Quality** | RAGAS ~0.70 | > 0.80 |
| **Multi-Modal Success** | - | 95%+ PDFs |
| **OCR Confidence** | - | 98%+ (good quality) |
| **Processing Speed** | 100 pages/min | 1000 pages/min |

### User Experience Goals

- ✓ Zero-configuration messy PDF handling
- ✓ Persona-based configuration
- ✓ Transparent decision-making
- ✓ Sub-second queries on cached results
- ✓ Interactive exploration workflows

### Developer Experience Goals

- ✓ 70%+ test coverage (from 58%)
- ✓ Interactive debugging tools
- ✓ Performance profiling
- ✓ Automated testing utilities

---

## Dependency Changes

### Removed Dependencies (v0.3.5)
```toml
# REMOVED in v0.3.5
# pytesseract = "^0.3.10"      # Replaced by Docling/PaddleOCR
# camelot-py = "^0.11.0"       # Replaced by Docling TableFormer
```

### New Dependencies

#### Document Processing (v0.3.5-v0.3.6)
```toml
docling = "^2.0.0"              # MIT - Modern document processing
paddleocr = "^2.8.0"            # Apache 2.0 - Fallback OCR
paddlepaddle = "^2.6.0"         # Apache 2.0 - PaddleOCR backend
pypdf = "^3.17.0"               # BSD - PDF manipulation
img2pdf = "^0.5.1"              # LGPL - Image to PDF
opencv-python = "^4.8.0"        # BSD - Image preprocessing
scikit-image = "^0.22.0"        # BSD - Image quality assessment
Pillow = "^10.0.0"              # HPND - Image handling
```

#### Chunking (v0.3.4)
```toml
nltk = "*"                      # Apache 2.0 - Sentence splitting
scipy = "*"                     # BSD - Similarity calculations
```

#### CLI Enhancements (v0.3.9-v0.3.13)
```toml
prompt-toolkit = "*"            # BSD - REPL interface
jinja2 = "*"                    # BSD - Templates
watchdog = "*"                  # Apache 2.0 - File watching
apscheduler = "*"               # MIT - Scheduling
fastapi = "*"                   # MIT - API server
uvicorn = "*"                   # BSD - ASGI server
```

**All dependencies are GPL-3.0 compatible (MIT, Apache 2.0, BSD, HPND, LGPL)**

---

## Version Comparison Table

| Feature Area | v0.1 | v0.2 | v0.3 |
|--------------|------|------|------|
| **Retrieval** | Basic dense | Dense + BM25 hybrid | Hybrid + reranking + query expansion |
| **Chunking** | Recursive | + Overlap optimisation | + Semantic/hierarchical |
| **Documents** | PDF, TXT, MD | + Metadata extraction | + Multi-modal + auto-correction |
| **OCR** | None | Tesseract | Docling + PaddleOCR |
| **Evaluation** | Manual | Basic metrics | RAGAS framework |
| **CLI** | Basic | Enhanced output | Interactive + automation + personas |
| **Generation** | Basic | Few-shot | Chain-of-thought + confidence |
| **Configuration** | Static | File-based | Personas + transparency |
| **Test Coverage** | ~40% | ~58% | Target: 70-80% |

---

## Timeline Estimates

### At 10 Hours/Week

| Version | Hours | Weeks |
|---------|-------|-------|
| v0.3.1 | 30 | 3 |
| v0.3.2 | 28-34 | 3-4 |
| v0.3.3 | 53-55 | 5-6 |
| v0.3.4 | 38-40 | 4 |
| v0.3.5 | 55-62 | 6 |
| v0.3.6 | 49-57 | 5-6 |
| v0.3.7 | 16-22 | 2 |
| v0.3.8 | 68-74 | 7 |
| v0.3.9 | 20-24 | 2-3 |
| v0.3.10 | 19-24 | 2-3 |
| v0.3.11 | 18-24 | 2-3 |
| v0.3.12 | 17-23 | 2-3 |
| v0.3.13 | 26-32 | 3 |
| **Total** | **437-501** | **44-50** |

### At 15 Hours/Week

Total: 29-34 weeks (7-8 months)

---

## Agent Usage Patterns

### Standard Workflow Per Version

**1. Before Implementation (optional, 2-3h when needed):**
- architecture-advisor: Design review
- ux-architect: UX validation

**2. After Implementation (4-8h):**
- documentation-architect: Plan structure (2-4h)
- Write documentation following plan

**3. Before Commit (4-8h):**
- documentation-auditor: Comprehensive review (2-4h)
- Fix any issues found
- git-documentation-committer: Commit (2-4h)

### Agent Roles & When to Use

| Agent | Use Case | Typical Duration |
|-------|----------|------------------|
| **architecture-advisor** | Complex design decisions, technology choices, trade-off analysis | 2-3h per decision |
| **ux-architect** | User-facing features, CLI design, persona/configuration UX | 2h per feature |
| **documentation-architect** | Planning doc structure BEFORE writing, new feature docs | 2-4h per version |
| **documentation-auditor** | Before EVERY commit, comprehensive quality check | 2-4h per version |
| **git-documentation-committer** | For EVERY commit, ensures quality and consistency | 2-4h per version |

---

## Configuration Personas Design

### Built-in Personas

**"accuracy"** - Maximum quality, slower
- Query decomposition: Enabled
- Retrieval method: Hybrid
- Reranking: Enabled (top-10 → top-3)
- Contextual compression: Enabled
- Confidence threshold: 95%
- Use case: Research, critical decisions

**"speed"** - Fast answers
- Query decomposition: Disabled
- Retrieval method: Vector only
- Reranking: Disabled
- Contextual compression: Disabled
- Confidence threshold: 80%
- Use case: Quick lookups, exploration

**"balanced"** - Default
- Query decomposition: Auto (on complex queries)
- Retrieval method: Hybrid
- Reranking: Enabled (top-15 → top-5)
- Contextual compression: Auto
- Confidence threshold: 85%
- Use case: General usage

**"research"** - Deep exploration
- Query decomposition: Enabled
- Retrieval method: Hybrid
- Retrieve: Top-30 chunks
- Reranking: Enabled (top-30 → top-10)
- Multi-query: Enabled
- Use case: Academic research, comprehensive analysis

**"quick-answer"** - Single best answer
- Retrieval method: Hybrid
- Retrieve: Top-1
- Reranking: Disabled (too slow for single result)
- Format: Concise
- Use case: CLI automation, scripts

### User Custom Personas

Users can create custom personas in `~/.config/ragged/personas.yml`:

```yaml
personas:
  my-research:
    description: "Custom research profile"
    inherits: accuracy
    overrides:
      retrieval_method: hybrid
      top_k: 50
      rerank_to: 15
```

---

## Risk Mitigation

### High Risk Items

**1. Docling Performance on Very Messy Scans**
- **Risk:** Docling may struggle with worst-case documents
- **Mitigation:** PaddleOCR fallback, confidence tracking
- **Validation:** Test on representative sample before full implementation

**2. Automated Correction Accuracy**
- **Risk:** Auto-correction may make wrong decisions
- **Mitigation:** Confidence tracking, metadata logging, user can review corrections
- **Validation:** Manual review of 50+ corrected documents

### Medium Risk Items

**3. Configuration Persona Design**
- **Risk:** Personas may not match user mental models
- **Mitigation:** User testing, iteration based on feedback
- **Validation:** Get feedback from 3-5 users before finalising

**4. Test Coverage Goals**
- **Risk:** May not reach 70% coverage
- **Mitigation:** Focus on core paths first, defer edge cases
- **Validation:** Track coverage per version, adjust if needed

### Low Risk Items

- License compatibility (all verified GPL-3.0 compatible)
- OCR technology maturity (proven tools)
- Query processing techniques (well-established)

---

## Related Documentation

- [v0.3.0 Planning](../../planning/version/v0.3/) - Design goals
- [Query Processing Features](./features/query-processing.md) - Detailed specs
- [Chunking Strategies](./features/chunking-strategies.md) - Detailed specs
- [Multi-Modal Support](./features/multi-modal-support.md) - Detailed specs (needs update for Docling)
- [Evaluation & Quality](./features/evaluation-quality.md) - Detailed specs
- [Data & Generation](./features/data-generation.md) - Detailed specs
- [CLI Features](./features/cli-features.md) - Detailed specs
- [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md) - Comprehensive CLI specs
- [Docling OCR Decision](../../../decisions/2025-11-17-docling-ocr-decision.md) - Architecture decision record

---

**Maintained By:** ragged development team

**License:** GPL-3.0

**Last Reviewed:** 2025-11-17

**Status:** Ready for implementation
