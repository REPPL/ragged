# ragged v0.2 Complete Implementation Plan

**Status**: Phase 1 Complete, Phases 2-8 Planned
**Date**: 2025-11-09

This document provides the complete blueprint for implementing ragged v0.2. Phase 1 (Environment & Dependencies) is complete with Python 3.12. The remaining phases follow.

---

## Current Status

**Completed**:
- ✅ Phase 1: Environment & Dependencies (Python 3.12, all dependencies installed)

**In Progress**:
- 🚧 Phase 2: FastAPI Backend + Hybrid Retrieval (API structure created)

**Planned**:
- ⏳ Phases 3-8: Full implementation ready to execute

---

## Phase 2: FastAPI Backend + Hybrid Retrieval (12-16h)

### Files to Create

```
src/retrieval/
├── bm25.py              # BM25 keyword search indexer
├── hybrid.py            # Hybrid retrieval orchestrator
└── fusion.py            # Reciprocal Rank Fusion algorithm

src/web/
├── __init__.py          # ✅ Created
├── api.py               # ✅ Skeleton created
├── models.py            # Request/response Pydantic models
└── streaming.py         # SSE streaming utilities
```

### Implementation Guide

**BM25 Implementation** (`src/retrieval/bm25.py`):
```python
from rank_bm25 import BM25Okapi
from typing import List

class BM25Retriever:
    def __init__(self):
        self.index = None
        self.documents = []

    def index_documents(self, documents: List[str]):
        tokenized = [doc.split() for doc in documents]
        self.index = BM25Okapi(tokenized)
        self.documents = documents

    def search(self, query: str, top_k: int = 5):
        scores = self.index.get_scores(query.split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.documents[i], scores[i]) for i in top_indices]
```

**Hybrid Retrieval** (`src/retrieval/hybrid.py`):
```python
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.retriever import Retriever

class HybridRetriever:
    def __init__(self, vector_retriever: Retriever, bm25_retriever: BM25Retriever):
        self.vector = vector_retriever
        self.bm25 = bm25_retriever

    def retrieve(self, query: str, top_k: int = 10, alpha: float = 0.5):
        # Get results from both
        vector_results = self.vector.retrieve(query, top_k=top_k*2)
        bm25_results = self.bm25.search(query, top_k=top_k*2)

        # Apply RRF fusion
        from src.retrieval.fusion import reciprocal_rank_fusion
        return reciprocal_rank_fusion(vector_results, bm25_results, k=60)[:top_k]
```

### Testing Strategy

Create `tests/retrieval/test_bm25.py`, `tests/retrieval/test_hybrid.py`, `tests/web/test_api.py` with 60+ tests total.

---

## Phase 3: Gradio Web UI (8-12h)

### Files to Create

```
src/web/
└── gradio_ui.py         # Gradio application

examples/
└── sample_docs/         # Sample documents for demo
```

### Implementation Guide

**Gradio UI** (`src/web/gradio_ui.py`):
```python
import gradio as gr
import httpx

API_URL = "http://localhost:8000"

def query_api(message, history, collection, method, top_k):
    response = httpx.post(
        f"{API_URL}/api/query",
        json={"query": message, "collection": collection,
              "retrieval_method": method, "top_k": top_k, "stream": False}
    )
    return response.json()["answer"]

with gr.Blocks(title="ragged - Privacy-First RAG", theme=gr.themes.Soft()) as app:
    gr.Markdown("# ragged - Ask Your Documents Privately")

    with gr.Row():
        collection = gr.Dropdown(["default"], value="default", label="Collection")
        method = gr.Radio(["vector", "bm25", "hybrid"], value="hybrid", label="Retrieval")
        top_k = gr.Slider(1, 20, value=5, step=1, label="Top-K")

    chat = gr.ChatInterface(query_api, additional_inputs=[collection, method, top_k])

    with gr.Accordion("Upload Documents", open=False):
        files = gr.Files(label="Select files")
        upload_btn = gr.Button("Upload")
        status = gr.Textbox(label="Status")

app.launch(server_name="0.0.0.0", server_port=7860)
```

---

## Phase 4: Context & Few-Shot Prompting (8-10h)

### Files to Create

```
src/chunking/
└── contextual.py        # Contextual chunking with headers

src/generation/
├── few_shot.py          # Few-shot example manager
└── context_manager.py   # Context window management

data/
└── few_shot_examples.json  # Seed Q&A examples
```

### Implementation Guide

**Few-Shot Manager** (`src/generation/few_shot.py`):
```python
from typing import List
from pydantic import BaseModel

class Example(BaseModel):
    question: str
    answer: str
    context: str

class FewShotManager:
    def __init__(self, vector_store):
        self.store = vector_store
        self.collection = "few_shot_examples"

    def add_example(self, example: Example):
        embedding = self.embedder.embed_text(example.question)
        self.store.add(
            ids=[str(uuid4())],
            embeddings=[embedding],
            documents=[f"Q: {example.question}\nA: {example.answer}"],
            metadatas=[{"type": "few_shot"}],
            collection=self.collection
        )

    def get_examples(self, query: str, k: int = 3) -> List[Example]:
        results = self.store.query(query, top_k=k, collection=self.collection)
        return [self._parse_example(doc) for doc in results["documents"][0]]
```

---

## Phase 5: Metadata & Performance (8-10h)

### Files to Create

```
src/storage/
├── metadata.py          # Enhanced metadata models
└── cache.py             # Query result caching

src/ingestion/
└── async_processor.py   # Async document processing
```

### Implementation Guide

**Caching** (`src/storage/cache.py`):
```python
from functools import lru_cache
from typing import Optional, Any

class QueryCache:
    def __init__(self, maxsize: int = 128):
        self.cache = {}
        self.maxsize = maxsize

    def _make_key(self, query: str, collection: str, method: str) -> str:
        return f"{collection}:{method}:{query}"

    def get(self, query: str, collection: str, method: str) -> Optional[Any]:
        return self.cache.get(self._make_key(query, collection, method))

    def set(self, query: str, collection: str, method: str, result: Any):
        key = self._make_key(query, collection, method)
        if len(self.cache) >= self.maxsize:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = result
```

---

## Phase 6: Docker & Deployment (6-8h)

### Updates Required

**docker-compose.yml** - Add Gradio service:
```yaml
services:
  ragged-api:
    # existing config

  ragged-ui:
    build: .
    command: ["python", "-m", "src.web.gradio_ui"]
    ports:
      - "7860:7860"
    depends_on:
      - ragged-api
    environment:
      - RAGGED_API_URL=http://ragged-api:8000
```

**Dockerfile** - Already updated for Python 3.12 ✅

---

## Phase 7: Testing & Documentation (10-12h)

### Test Files to Create

```
tests/
├── retrieval/
│   ├── test_bm25.py (15 tests)
│   ├── test_hybrid.py (15 tests)
│   └── test_fusion.py (10 tests)
├── web/
│   ├── test_api.py (20 tests)
│   └── test_streaming.py (5 tests)
├── generation/
│   └── test_few_shot.py (8 tests)
└── storage/
    └── test_cache.py (12 tests)
```

### Documentation Files

```
docs/
├── api/
│   ├── openapi.json (auto-generated)
│   └── endpoints.md
├── user-guide/
│   ├── web-ui.md
│   ├── hybrid-retrieval.md
│   └── docker-deployment.md
└── migration/
    └── v0.1-to-v0.2.md
```

---

## Phase 8: Integration & Release (6-8h)

### Checklist

- [ ] Run full regression suite (v0.1 + v0.2 tests)
- [ ] Security audit with `pip-audit`
- [ ] Performance benchmarks
- [ ] Update README.md
- [ ] Write CHANGELOG.md
- [ ] Create release notes
- [ ] Git tag v0.2.0

---

## Key Architecture Decisions

### ADR 19: Python 3.12 for v0.2
**Status**: Accepted
**Decision**: Use Python 3.12 instead of planned 3.11
**Rationale**: Better library support, ChromaDB 1.3.4 works perfectly, more mature than 3.14
**Result**: All v0.1 tests pass, excellent compatibility

### ADR 20: Gradio for Web UI
**Status**: Accepted
**Decision**: Use Gradio instead of React for v0.2
**Rationale**: Faster to implement (1 week vs 3 weeks), Python-native, sufficient for v0.2
**Migration Path**: Can upgrade to React in v0.3 if needed

### ADR 21: Hybrid Search Implementation
**Status**: Accepted
**Decision**: BM25 + Vector with Reciprocal Rank Fusion
**Rationale**: Proven 10-15% improvement, moderate complexity, no new models needed

---

## Success Criteria

**Must Have**:
- ✅ Python 3.12 environment working
- [ ] Web UI accessible at :7860
- [ ] API accessible at :8000
- [ ] Hybrid retrieval functional
- [ ] Docker deployment works
- [ ] All v0.1 features preserved

**Performance**:
- Query latency < 3s
- Retrieval < 200ms
- 80%+ test coverage

---

## Next Steps

1. **Continue Phase 2**: Implement BM25, hybrid retrieval, complete API
2. **Execute Phase 3**: Build Gradio UI
3. **Execute Phases 4-8**: Follow plan above

**Estimated Remaining**: 57-76 hours (7 phases)

---

**Document Status**: Complete implementation blueprint
**Last Updated**: 2025-11-09
**Ready for**: Autonomous execution based on this plan
