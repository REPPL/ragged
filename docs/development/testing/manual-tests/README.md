# Manual Testing Documentation

**Purpose:** Manual test execution results for v0.5.6 multi-modal features

---

## Overview

This directory contains manual test procedures and execution results for ragged's multi-modal RAG capabilities. These tests complement the automated test suite by validating real-world workflows, visual content processing, and cross-platform compatibility.

---

## Directory Structure

```
manual-tests/
├── README.md                    # This file
├── TEST-TEMPLATE.md             # Template for new test documents
├── visual-content/              # PDF visual content ingestion tests
├── multimodal-queries/          # Multi-modal query tests
├── gpu-management/              # GPU detection and optimisation tests
└── cross-platform/              # Cross-platform compatibility tests
```

---

## Test Categories

### 1. Visual Content Tests

**Directory:** `visual-content/`

**Purpose:** Validate PDF ingestion with visual embeddings (ColPali)

**Test Scenarios:**
- Basic PDF ingestion with vision embeddings
- Multi-document batch ingestion
- Visual content verification
- Storage backend validation

### 2. Multi-Modal Query Tests

**Directory:** `multimodal-queries/`

**Purpose:** Validate hybrid text+vision retrieval

**Test Scenarios:**
- Text-only queries
- Image-based queries
- Hybrid queries (text + vision)
- Result relevance validation
- Cross-modal retrieval accuracy

### 3. GPU Management Tests

**Directory:** `gpu-management/`

**Purpose:** Validate GPU detection and optimisation features

**Test Scenarios:**
- GPU device detection (CUDA, MPS, CPU)
- Performance benchmarking
- Batch size optimisation
- Memory management

### 4. Cross-Platform Tests

**Directory:** `cross-platform/`

**Purpose:** Validate functionality across operating systems

**Test Scenarios:**
- macOS (MPS backend)
- Linux (CUDA backend)
- CPU-only fallback behaviour

---

## Running Tests

### Prerequisites

1. **Install ragged:**
   ```bash
   pip install -e .
   ```

2. **Start ChromaDB:**
   ```bash
   docker-compose up -d chromadb
   ```

3. **Install Ollama models:**
   ```bash
   ollama pull qwen2-vl:2b
   ollama pull nomic-embed-text
   ```

4. **Verify sample data:**
   ```bash
   ls examples/sample_documents/*.pdf
   ```

### Execution Process

1. **Select test** from the appropriate category directory

2. **Review prerequisites** section in the test document

3. **Execute each step** sequentially, documenting:
   - Exact commands run
   - Actual results observed
   - Any deviations from expected behaviour

4. **Capture evidence:**
   - Command output (copy-paste into test doc)
   - Screenshots (for visual results)
   - Performance metrics (timing, memory usage)

5. **Complete verification** checklist

6. **Document issues** encountered

7. **Write summary** with overall status and recommendations

### Using the Template

To create a new test:

```bash
cp TEST-TEMPLATE.md visual-content/VC-01-basic-pdf-ingestion.md
```

Then fill in:
- Test name and metadata
- Objective
- Prerequisites
- Step-by-step procedure with commands
- Results and evidence
- Summary and findings

---

## Test Execution Standards

### Documentation Quality

- **Commands:** Must be exact, copy-pasteable
- **Results:** Include full output (truncate if >50 lines)
- **Evidence:** Provide sufficient proof of success/failure
- **Issues:** Document with severity and resolution

### Status Indicators

- ✅ **Pass:** Feature works as expected
- ❌ **Fail:** Feature broken or incorrect behaviour
- ⚠️ **Partial:** Feature works but with limitations/issues

### British English

All test documentation uses British English spelling:
- optimisation (not optimization)
- behaviour (not behavior)
- colour (not color)

---

## Sample Data

**Location:** `examples/sample_documents/`

**Available PDFs:**
- `data_visualization.pdf` (9 pages) - Charts and graphs
- `machine_learning_survey.pdf` (6 pages) - Technical diagrams
- `neural_networks.pdf` (5 pages) - Architecture diagrams

**Source:** arXiv.org (openly licensed academic papers)

**Usage:** These PDFs are specifically chosen for:
- Diverse visual content (diagrams, tables, charts)
- Technical text for semantic search
- Reasonable size for testing (220KB - 1MB)

---

## Reporting Issues

If tests reveal bugs or unexpected behaviour:

1. **Document in test report** (Issues Encountered section)
2. **Create GitHub issue** with:
   - Link to test document
   - Steps to reproduce
   - Expected vs actual behaviour
   - Environment details

3. **Update test status** (❌ Fail or ⚠️ Partial)

---

## Test Maintenance

### When to Update Tests

- After fixing reported issues (re-run affected tests)
- After adding new features (create new test scenarios)
- After significant refactoring (verify nothing broken)
- Before releases (full test pass)

### Versioning

Tests are version-specific:
- **v0.5.6 tests** validate v0.5.6 features
- Tests may need updating for future versions
- Mark tests as "deprecated" if features change significantly

---

## Related Documentation

- [Automated Tests](../../../tests/) - Pytest test suite
- [Multi-Modal Workflow Tutorial](../../../tutorials/multimodal-workflow.md) - User guide
- [GPU Configuration Guide](../../../guides/gpu-configuration-optimisation.md) - GPU setup
- [API Reference](../../../../reference/api/) - Technical specifications

---

## Questions?

For questions about:
- **Running tests:** See [Installation Guide](../../../tutorials/installation.md)
- **Test failures:** Check [Troubleshooting](../../../guides/troubleshooting.md)
- **Contributing tests:** See [Contributing Guide](../../../README.md)
