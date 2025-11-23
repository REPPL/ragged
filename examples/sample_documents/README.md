# Sample Documents

**Purpose:** Test and example documents for demonstrating ragged's capabilities

---

## Overview

This directory contains sample PDF documents and markdown files used for testing, demonstrations, and tutorials. All documents are openly licensed academic papers from arXiv.org, chosen for their diverse visual content and technical depth.

---

## Available Documents

### PDF Documents

#### [data_visualization.pdf](./data_visualization.pdf)

**Source:** arXiv.org
**Pages:** 9
**Size:** ~220 KB
**License:** Open access (arXiv)

**Content Characteristics:**
- Charts and graphs (bar charts, line plots, scatter plots)
- Statistical visualisations
- Data tables
- Colour-coded diagrams

**Good For Testing:**
- Vision embedding generation (ColPali)
- Chart and graph recognition
- Hybrid text+vision retrieval
- Multi-document comparisons

**Sample Queries:**
- "Show me bar charts comparing performance"
- "Find visualisations of statistical distributions"
- "Charts with error bars"

---

#### [machine_learning_survey.pdf](./machine_learning_survey.pdf)

**Source:** arXiv.org
**Pages:** 6
**Size:** ~590 KB
**License:** Open access (arXiv)

**Content Characteristics:**
- Technical diagrams (ML architectures, workflows)
- Algorithm flowcharts
- Comparison tables
- Mathematical notation

**Good For Testing:**
- Technical diagram understanding
- Flowchart recognition
- Table extraction
- Academic paper processing

**Sample Queries:**
- "Find ML architecture diagrams"
- "Show algorithm workflows"
- "Tables comparing different approaches"

---

#### [neural_networks.pdf](./neural_networks.pdf)

**Source:** arXiv.org
**Pages:** 5
**Size:** ~1 MB
**License:** Open access (arXiv)

**Content Characteristics:**
- Neural network architecture diagrams
- Layer visualisations
- Mathematical equations
- Training graphs (loss curves, accuracy plots)

**Good For Testing:**
- Architecture diagram recognition
- Mathematical content understanding
- Training visualisation retrieval
- Deep learning documentation

**Sample Queries:**
- "Neural network architecture diagrams"
- "Training loss curves"
- "Layer structure visualisations"

---

### Markdown Documents

#### [rag_introduction.md](./rag_introduction.md)

**Content:** Introduction to Retrieval-Augmented Generation

**Good For Testing:**
- Markdown ingestion
- Text-only retrieval
- Semantic search without vision
- Comparing text vs vision retrieval

---

## Usage in Examples and Tests

### In Tutorials

**Location:** `docs/tutorials/multimodal-workflow.md`

**Usage:**
```bash
# Ingest with vision embeddings
ragged ingest pdf examples/sample_documents/data_visualization.pdf --vision

# Query with hybrid retrieval
ragged query "charts showing performance" --hybrid
```

### In Jupyter Notebooks

**Location:** `examples/notebooks/`

**Usage:**
```python
from ragged import RAG

rag = RAG()

# Ingest sample document
rag.ingest_pdf("../sample_documents/neural_networks.pdf", enable_vision=True)

# Query
results = rag.query("architecture diagrams", hybrid=True)
```

### In Manual Tests

**Location:** `docs/testing/manual-tests/`

**Usage:** These PDFs are used in all visual content and multi-modal query tests.

Examples:
- `visual-content/VC-01-basic-pdf-ingestion.md`
- `multimodal-queries/MQ-01-text-query.md`
- `multimodal-queries/MQ-03-hybrid-query.md`

---

## Document Selection Criteria

These documents were chosen because:

1. **Diverse Visual Content:**
   - Charts, graphs, diagrams, tables
   - Different visualisation types
   - Colour and monochrome content

2. **Reasonable Size:**
   - 220 KB - 1 MB (manageable for testing)
   - 5-9 pages (quick to process)
   - Not too large for git repository

3. **Technical Depth:**
   - Academic quality content
   - Realistic use case (research papers)
   - Complex enough to test capabilities

4. **Open Licensing:**
   - arXiv open access
   - Freely redistributable
   - No copyright issues

---

## Adding New Sample Documents

### Requirements

**Before adding a document, verify:**

1. **License:** Must be openly licensed (arXiv, CC-BY, CC0, public domain)
2. **Size:** <2 MB per file (repository size constraints)
3. **Content:** Diverse visual content OR unique test case
4. **Purpose:** Clear testing/demonstration use case

### Process

1. **Download document** from open source

2. **Verify license:**
   ```bash
   # Check arXiv abstract page for license
   # Confirm "arXiv.org perpetual, non-exclusive license"
   ```

3. **Add to directory:**
   ```bash
   cp new_document.pdf examples/sample_documents/
   ```

4. **Update this README:**
   - Add to "Available Documents" section
   - Document content characteristics
   - Suggest sample queries
   - Explain testing use case

5. **Use in test/tutorial:**
   - Create at least one example using the document
   - Demonstrate why this document was needed

### Don't Add

**❌ Avoid:**
- Copyrighted content without clear license
- Very large files (>2 MB)
- Documents without visual content (unless unique test case)
- Redundant content (too similar to existing samples)
- Personal or sensitive information

---

## Related Documentation

- [Multi-Modal Tutorial](../../docs/tutorials/multimodal-workflow.md) - Using these documents
- [Manual Tests](../../docs/testing/manual-tests/README.md) - Test procedures using samples
- [Jupyter Notebooks](../notebooks/README.md) - Interactive examples
- [Installation Guide](../../docs/tutorials/installation.md) - Setup before using samples

---

**Status**: Active (3 PDFs, 1 markdown)
