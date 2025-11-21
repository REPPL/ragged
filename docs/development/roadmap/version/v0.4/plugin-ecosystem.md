# v0.4.x Plugin Ecosystem Expansion

**Purpose**: Strategy for growing ragged's plugin ecosystem beyond v0.4.0 foundation

**Status**: Enhancement opportunities for consideration

**Audience**: Plugin developers, community managers, core developers

---

## Overview

This document outlines strategies for **expanding the plugin ecosystem** beyond the plugin architecture foundation established in v0.4.0.

**Foundation** (v0.4.0):
- ✅ Plugin architecture (4 plugin types)
- ✅ Entry point discovery system
- ✅ Plugin registry and loader
- ✅ CLI commands (`ragged plugin`)
- ✅ 2-3 sample plugins

**Ecosystem Vision**: Transform ragged from a tool into a **platform** where users and developers can extend functionality through a rich plugin marketplace.

---

## Plugin Ecosystem Strategy

### Phase 1: Foundation (v0.4.0) ✅

**Status**: Implemented in v0.4.0

- Plugin architecture working
- Sample plugins demonstrate capabilities
- Developer documentation available

---

### Phase 2: Official Plugins (v0.4.x - v0.5.0)

**Goal**: Establish quality baseline with curated official plugins

**Target**: 10-15 official plugins by v0.5.0

---

#### Official Plugin Categories

**Category 1: Alternative Embedders**

**Priority**: HIGH (embeddings are core to RAG)

**Plugins to Develop**:

##### Plugin: OpenAI Embeddings

**Purpose**: Use OpenAI's `text-embedding-3-small` or `text-embedding-3-large`

**Benefits**:
- High-quality embeddings
- API-based (no local GPU required)
- Multiple size options

**Implementation** (estimated 4-5 hours):
```python
from ragged.plugins.embedder import EmbedderPlugin
from openai import OpenAI
import numpy as np

class OpenAIEmbedder(EmbedderPlugin):
    """OpenAI embeddings plugin."""

    name = "openai-embedder"
    version = "1.0.0"
    description = "Use OpenAI's embedding models"

    def __init__(self, model: str = "text-embedding-3-small", api_key: str = None):
        """
        Initialize OpenAI embedder.

        Args:
            model: OpenAI model name
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return np.array([item.embedding for item in response.data])

    def get_dimension(self) -> int:
        """Return embedding dimension."""
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return dimensions.get(self.model, 1536)
```

**Configuration** (`~/.ragged/config.yaml`):
```yaml
plugins:
  embedder: "openai-embedder"
  openai-embedder:
    model: "text-embedding-3-small"
    api_key_env: "OPENAI_API_KEY"  # Read from environment
```

**Installation**:
```bash
ragged plugin install ragged-plugin-openai-embedder
ragged config set plugins.embedder "openai-embedder"
```

**Priority**: HIGH | **Effort**: Low (4-5h) | **Timeline**: v0.4.5 or v0.5.0

---

##### Plugin: Cohere Embeddings

**Purpose**: Use Cohere's embedding models

**Benefits**:
- Multilingual support
- Specialized models (e.g., `embed-english-light-v3.0`)
- Competitive pricing

**Implementation**: Similar to OpenAI plugin (3-4 hours)

**Priority**: MEDIUM | **Effort**: Low (3-4h) | **Timeline**: v0.5.0

---

##### Plugin: Local LLM Embeddings (LLaMA, Mistral)

**Purpose**: Run embedding models locally with llama.cpp

**Benefits**:
- 100% privacy (no API calls)
- No API costs
- Support for Llama 2, Mistral, etc.

**Implementation** (estimated 8-10 hours):
```python
from llama_cpp import Llama
import numpy as np

class LlamaCppEmbedder(EmbedderPlugin):
    """Embeddings using llama.cpp for local LLMs."""

    name = "llamacpp-embedder"
    version = "1.0.0"

    def __init__(self, model_path: str, n_gpu_layers: int = 0):
        """
        Initialize llama.cpp embedder.

        Args:
            model_path: Path to GGUF model file
            n_gpu_layers: Number of layers to offload to GPU
        """
        self.llm = Llama(
            model_path=model_path,
            embedding=True,
            n_gpu_layers=n_gpu_layers
        )

    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings locally."""
        embeddings = [self.llm.embed(text) for text in texts]
        return np.array(embeddings)
```

**Priority**: HIGH (privacy-conscious users) | **Effort**: Medium (8-10h) | **Timeline**: v0.5.0

---

**Category 2: Advanced Retrievers**

**Priority**: HIGH (retrieval quality is critical)

**Plugins to Develop**:

##### Plugin: Hybrid Search (BM25 + Vector)

**Purpose**: Combine keyword search (BM25) with vector search

**Benefits**:
- Better recall (catches exact matches)
- More robust to query variations
- State-of-the-art retrieval

**Implementation** (estimated 12-15 hours):
```python
from ragged.plugins.retriever import RetrieverPlugin
from rank_bm25 import BM25Okapi
import numpy as np

class HybridRetriever(RetrieverPlugin):
    """Hybrid BM25 + vector search retriever."""

    name = "hybrid-retriever"
    version = "1.0.0"

    def __init__(self, alpha: float = 0.5):
        """
        Initialize hybrid retriever.

        Args:
            alpha: Weight for vector search (1-alpha for BM25)
                   0.0 = pure BM25, 1.0 = pure vector
        """
        self.alpha = alpha
        self.bm25 = None
        self.documents = []

    def index(self, documents: List[Dict], embeddings: np.ndarray):
        """Build both BM25 and vector indexes."""
        self.documents = documents

        # Build BM25 index
        tokenized_docs = [doc["text"].lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)

        # Store embeddings for vector search
        self.embeddings = embeddings

    def retrieve(self, query: str, query_embedding: np.ndarray,
                 top_k: int = 10) -> List[Dict]:
        """
        Retrieve using hybrid search.

        Args:
            query: User query text
            query_embedding: Query embedding vector
            top_k: Number of results

        Returns:
            Top-k documents by hybrid score
        """
        # BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Vector similarity scores
        vector_scores = np.dot(self.embeddings, query_embedding)

        # Normalize scores to [0, 1]
        bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min())
        vector_scores = (vector_scores - vector_scores.min()) / (vector_scores.max() - vector_scores.min())

        # Hybrid score
        hybrid_scores = self.alpha * vector_scores + (1 - self.alpha) * bm25_scores

        # Get top-k
        top_indices = np.argsort(hybrid_scores)[-top_k:][::-1]
        return [self.documents[i] for i in top_indices]
```

**Priority**: HIGH | **Effort**: Medium (12-15h) | **Timeline**: v0.5.0

---

##### Plugin: Reranker (Cross-Encoder)

**Purpose**: Rerank top-k results with cross-encoder for better precision

**Benefits**:
- Improved ranking quality
- Better relevance at top positions
- Minimal latency cost (<50ms for 20 documents)

**Implementation** (estimated 8-10 hours):
```python
from sentence_transformers import CrossEncoder

class RerankerPlugin(RetrieverPlugin):
    """Rerank results with cross-encoder."""

    name = "cross-encoder-reranker"
    version = "1.0.0"

    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.reranker = CrossEncoder(model)

    def rerank(self, query: str, candidates: List[Dict],
               top_k: int = 10) -> List[Dict]:
        """
        Rerank candidate documents.

        Args:
            query: User query
            candidates: Candidate documents from initial retrieval
            top_k: Final number of results

        Returns:
            Reranked top-k documents
        """
        # Create query-document pairs
        pairs = [(query, doc["text"]) for doc in candidates]

        # Score with cross-encoder
        scores = self.reranker.predict(pairs)

        # Sort by score
        scored_docs = list(zip(candidates, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, score in scored_docs[:top_k]]
```

**Priority**: HIGH | **Effort**: Medium (8-10h) | **Timeline**: v0.5.0

---

**Category 3: Document Processors**

**Priority**: MEDIUM (extends document support)

**Plugins to Develop**:

##### Plugin: PDF Processor (with Layout)

**Purpose**: Extract text from PDFs preserving layout/structure

**Benefits**:
- Better handling of tables, figures
- Preserve document structure
- Support scanned PDFs (OCR)

**Tools**: `pdfplumber`, `PyMuPDF`, `Tesseract` (OCR)

**Priority**: HIGH | **Effort**: Medium (10-12h) | **Timeline**: v0.5.0

---

##### Plugin: Web Scraper

**Purpose**: Ingest content from websites

**Benefits**:
- Keep documentation up-to-date
- Monitor news sources
- Build knowledge bases from web content

**Tools**: `requests`, `BeautifulSoup`, `playwright` (for JavaScript sites)

**Priority**: MEDIUM | **Effort**: Medium (8-10h) | **Timeline**: v0.5.0 or v0.5.1

---

##### Plugin: Code Analyzer

**Purpose**: Parse and index source code intelligently

**Benefits**:
- Better code search (function/class-aware)
- Understand code structure
- Support multiple languages

**Tools**: `tree-sitter`, language-specific parsers

**Priority**: MEDIUM | **Effort**: High (15-20h) | **Timeline**: v0.5.1

---

**Category 4: Custom Commands**

**Priority**: LOW (nice-to-have convenience)

**Plugins to Develop**:

##### Plugin: Export Commands

**Purpose**: Export data in various formats

**Commands**:
- `ragged export markdown <query>` - Export results as Markdown
- `ragged export pdf <query>` - Export results as PDF
- `ragged export csv <query>` - Export results as CSV

**Priority**: LOW | **Effort**: Low (4-6h) | **Timeline**: v0.5.1

---

##### Plugin: Scheduled Updates

**Purpose**: Automatically update knowledge base

**Commands**:
- `ragged schedule add "update-docs" --cron "0 2 * * *" --source https://docs.example.com`
- `ragged schedule list`

**Priority**: LOW | **Effort**: Medium (10-12h) | **Timeline**: v0.5.2

---

### Phase 3: Community Plugins (v0.5.0+)

**Goal**: Enable third-party developers to contribute

**Strategy**:

#### 1. Plugin Development Kit (SDK)

**Components**:
- Plugin template generator
- Testing utilities
- CI/CD templates
- Packaging scripts

**CLI Command**:
```bash
# Create new plugin from template
ragged plugin create my-embedder --type embedder

# Output:
# Created plugin scaffold:
#   my-embedder/
#   ├── src/my_embedder/
#   │   ├── __init__.py
#   │   └── plugin.py
#   ├── tests/
#   │   └── test_plugin.py
#   ├── pyproject.toml
#   ├── README.md
#   └── .github/workflows/ci.yml
```

**Priority**: HIGH | **Effort**: Medium (12-15h) | **Timeline**: v0.5.0

---

#### 2. Plugin Testing Framework

**Purpose**: Help developers test plugins rigorously

**Features**:
- Contract tests (plugin implements interface correctly)
- Integration tests (works with ragged)
- Performance tests (meets latency requirements)

**CLI Command**:
```bash
# Test plugin locally
ragged plugin test ./my-plugin/

# Output:
# Running plugin tests:
#   ✅ Contract tests (5/5 passed)
#   ✅ Integration tests (12/12 passed)
#   ✅ Performance tests (3/3 passed)
#   ✅ Security scan (no issues)
#
# Plugin ready for publication!
```

**Priority**: HIGH | **Effort**: Medium (10-12h) | **Timeline**: v0.5.0

---

#### 3. Plugin Documentation Generator

**Purpose**: Auto-generate plugin documentation

**Features**:
- API reference from docstrings
- Configuration examples
- Usage tutorials

**CLI Command**:
```bash
# Generate plugin documentation
ragged plugin docs ./my-plugin/ --output docs/

# Output:
# Generated documentation:
#   docs/
#   ├── index.md
#   ├── api-reference.md
#   ├── configuration.md
#   └── usage-examples.md
```

**Priority**: MEDIUM | **Effort**: Medium (8-10h) | **Timeline**: v0.5.1

---

### Phase 4: Plugin Marketplace (v0.5.x)

**Goal**: Centralised plugin discovery and distribution

**Components**:

#### 1. Plugin Registry

**Purpose**: Centralised catalog of available plugins

**Features**:
- Browse plugins by category
- Search plugins by keywords
- View plugin details (description, author, downloads, ratings)
- Security badges (signed, verified, official)

**Implementation Options**:

**Option A: PyPI-based** (simplest)
- Use PyPI as registry
- Plugins named `ragged-plugin-{name}`
- Search: `pip search ragged-plugin-*`
- Install: `pip install ragged-plugin-openai-embedder`

**Option B: Dedicated Registry** (more control)
- Custom registry server (`registry.ragged.dev`)
- API for plugin submission, search, installation
- Better curation and quality control

**Recommendation**: Start with **Option A** (PyPI), migrate to **Option B** if ecosystem grows large

**Priority**: MEDIUM | **Effort**: Low (PyPI) or High (custom) | **Timeline**: v0.5.1 (PyPI) or v0.6.0 (custom)

---

#### 2. Plugin Marketplace Website

**Purpose**: Web interface for plugin discovery

**URL**: `https://plugins.ragged.dev`

**Pages**:
- **Home**: Featured plugins, categories
- **Browse**: All plugins with filters (category, rating, downloads)
- **Plugin Detail**: Description, installation, configuration, examples
- **Submit**: Plugin submission form

**Tech Stack**: Static site (Hugo/Jekyll) or dynamic (FastAPI + React)

**Priority**: LOW | **Effort**: High (40-50h) | **Timeline**: v0.6.0

---

#### 3. Plugin Analytics

**Purpose**: Track plugin adoption and usage

**Metrics**:
- Downloads per plugin
- Active installations
- Plugin ratings/reviews
- Common configurations

**Privacy**: Aggregate only, no user-identifying data

**Priority**: LOW | **Effort**: Medium (12-15h) | **Timeline**: v0.5.2 or v0.6.0

---

### Phase 5: Plugin Quality & Security (v0.5.x)

**Goal**: Ensure plugin ecosystem maintains high quality and security

**Initiatives**:

#### 1. Plugin Certification Program

**Levels**:

**Bronze** (Basic Quality):
- ✅ All tests passing
- ✅ Documentation complete
- ✅ No security vulnerabilities

**Silver** (Verified):
- ✅ Code review by ragged team
- ✅ Performance benchmarks meet standards
- ✅ Code signed with developer key

**Gold** (Official):
- ✅ Maintained by ragged team
- ✅ Priority support
- ✅ Featured in marketplace

**Badges**: Display certification level in marketplace

**Priority**: MEDIUM | **Effort**: Medium (documentation + process) | **Timeline**: v0.5.2

---

#### 2. Automated Plugin Review

**Purpose**: Automated checks before plugin publication

**Checks**:
- Security scan (bandit, safety)
- Dependency audit (no known CVEs)
- License compatibility (GPL-3.0 compatible)
- Code quality (ruff, mypy)
- Performance tests (latency requirements)

**CI/CD Integration**:
```yaml
# .github/workflows/plugin-review.yml
- name: Automated Plugin Review
  run: ragged plugin review ./my-plugin/

# Output:
# Plugin Review Results:
#   ✅ Security scan: PASSED
#   ✅ Dependency audit: PASSED
#   ✅ License check: PASSED (MIT)
#   ✅ Code quality: PASSED
#   ⚠️  Performance: WARNING (latency 150ms, recommended <100ms)
#
# Overall: APPROVED (with warnings)
```

**Priority**: HIGH | **Effort**: Medium (12-15h) | **Timeline**: v0.5.0

---

#### 3. Security Disclosure for Plugins

**Purpose**: Process for reporting plugin vulnerabilities

**Process**:
1. Security researcher reports plugin vulnerability
2. Plugin author notified privately
3. Author has 30 days to fix
4. Public disclosure after fix (or 90 days, whichever first)
5. Vulnerable plugin versions marked in registry

**Priority**: MEDIUM | **Effort**: Low (process documentation) | **Timeline**: v0.5.1

---

## Plugin Developer Resources

### Documentation

**Required Documentation**:

#### 1. Plugin Development Guide

**Location**: `docs/plugins/development-guide.md`

**Sections**:
- Plugin architecture overview
- Creating your first plugin
- Plugin types (embedder, retriever, processor, command)
- Testing plugins
- Publishing plugins
- Best practices

**Priority**: HIGH | **Timeline**: v0.4.0 (with plugin architecture)

---

#### 2. Plugin API Reference

**Location**: `docs/plugins/api-reference.md`

**Sections**:
- Base plugin interfaces
- Hook system
- Configuration management
- Error handling
- Logging

**Priority**: HIGH | **Timeline**: v0.4.0

---

#### 3. Plugin Examples Repository

**Location**: `github.com/ragged/plugin-examples`

**Contents**:
- Simple embedder plugin
- Simple retriever plugin
- Simple processor plugin
- Simple command plugin
- Advanced: Hybrid retriever (combines multiple approaches)

**Priority**: HIGH | **Timeline**: v0.4.0 or v0.4.5

---

### Developer Tools

#### 1. Plugin Validator

**Purpose**: Validate plugin before publication

**CLI Command**:
```bash
ragged plugin validate ./my-plugin/

# Checks:
# - Plugin structure correct
# - Required files present (pyproject.toml, README.md)
# - Tests exist and pass
# - Documentation complete
# - Security scan passed
# - License declared
```

**Priority**: HIGH | **Effort**: Medium (6-8h) | **Timeline**: v0.5.0

---

#### 2. Plugin Performance Profiler

**Purpose**: Profile plugin performance

**CLI Command**:
```bash
ragged plugin profile ./my-plugin/ --workload benchmark-queries.json

# Output:
# Performance Profile:
#   Avg latency: 45ms
#   P95 latency: 120ms
#   P99 latency: 250ms
#   Memory usage: 150 MB
#   CPU usage: 15%
#
# Recommendations:
#   - Consider caching (45ms > 25ms target)
#   - Optimise hot path (function `embed` takes 80% of time)
```

**Priority**: MEDIUM | **Effort**: Medium (8-10h) | **Timeline**: v0.5.1

---

## Community Engagement

### Plugin Developer Community

**Initiatives**:

#### 1. Plugin Developer Forum

**Platform**: GitHub Discussions or Discord

**Channels**:
- `#plugin-dev-general` - General discussion
- `#plugin-dev-help` - Help requests
- `#plugin-showcase` - Show off plugins
- `#plugin-feedback` - Feedback on plugin system

**Priority**: MEDIUM | **Effort**: Low (setup) | **Timeline**: v0.5.0

---

#### 2. Plugin Development Bounties

**Purpose**: Incentivise high-priority plugins

**Process**:
1. Community votes on desired plugins
2. Bounties placed on high-demand plugins
3. Developers build and submit
4. Bounty awarded on acceptance

**Example Bounties**:
- $500: Hybrid retriever plugin
- $300: PDF processor with OCR
- $200: Code analyzer plugin

**Funding**: Sponsorships, grants, or community crowdfunding

**Priority**: LOW | **Effort**: Medium (process + platform) | **Timeline**: v0.6.0+

---

#### 3. Plugin of the Month

**Purpose**: Highlight excellent community plugins

**Criteria**:
- Code quality
- Documentation quality
- User adoption
- Innovation

**Reward**: Featured in blog, newsletter, marketplace homepage

**Priority**: LOW | **Effort**: Low (editorial) | **Timeline**: v0.5.2+

---

## Plugin Ecosystem Metrics

**Track These Metrics**:

### Growth Metrics
- Total plugins available
- New plugins per month
- Plugin downloads
- Active plugin developers

### Quality Metrics
- Plugin ratings (if ratings system exists)
- Plugin test coverage
- Plugin documentation completeness
- Security scan pass rate

### Usage Metrics
- Most popular plugins
- Plugin categories (distribution)
- Average plugins per user
- Plugin churn rate

**Dashboard**: `https://stats.ragged.dev/plugins`

---

## Plugin Monetization (Future)

**Considerations for v1.0+**:

### Model 1: Freemium Plugins

- Free tier: Basic functionality
- Paid tier: Advanced features, priority support
- Revenue split: 70% developer, 30% platform

### Model 2: Plugin Marketplace Fees

- Free: Open-source plugins
- Paid: 5% transaction fee for paid plugins
- Revenue funds platform development

### Model 3: Sponsorship

- Companies sponsor plugin development
- Plugins remain open-source
- Sponsors get priority feature requests

**Decision**: Defer to v1.0+ (establish ecosystem first)

---

## Implementation Roadmap

### v0.4.0 (Foundation)
- ✅ Plugin architecture
- ✅ Sample plugins
- ✅ Developer documentation

### v0.4.5 - v0.5.0 (Official Plugins)
- Develop 3-5 official plugins (OpenAI embedder, hybrid retriever, reranker)
- Plugin testing framework
- Plugin SDK

### v0.5.1 (Community Enablement)
- Plugin certification program
- Automated plugin review
- Plugin documentation generator

### v0.5.2 (Discovery)
- PyPI-based plugin registry
- Plugin marketplace website (basic)
- Plugin analytics

### v0.6.0+ (Ecosystem Maturity)
- Custom plugin registry (if needed)
- Advanced marketplace features
- Plugin monetization (if demand exists)

---

## Success Metrics

**v0.5.0 Goals**:
- 10+ official plugins
- 5+ community plugins
- Plugin development guide complete
- 100+ plugin downloads

**v0.6.0 Goals**:
- 25+ total plugins
- 15+ community plugins
- 1,000+ plugin downloads
- Plugin marketplace launched

**v1.0 Goals**:
- 50+ total plugins
- 40+ community plugins
- Active plugin developer community (50+ developers)
- 10,000+ plugin downloads

---

## Related Documentation

- [v0.4.0 Plugin Architecture](v0.4.0.md) - Foundation implementation
- [Security Enhancements](security-enhancements.md) - Plugin sandboxing and code signing
- [Testing Guide](testing-guide.md) - Plugin testing standards

---

**Status**: Strategy documented (ready for execution)
