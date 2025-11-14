# ADR-0004: Factory Pattern for Embeddings

**Status:** Accepted

**Date:** 2025-11-09

**Area:** Software Architecture, Design Patterns

**Related:**
- [Embeddings Technology](../development/design/technology-stack/embeddings.md)
- [Modularity Concept](../development/design/core-concepts/modularity.md)

---

## Context

ragged needs to support multiple embedding backends:
- sentence-transformers (local, CPU/GPU)
- Ollama (local, consistent with LLM)
- Future: Other models (OpenAI Ada, Cohere, etc.)

The system must allow users to switch embedding models without changing application code. Each backend has different APIs, initialization patterns, and configuration requirements.

We need a design pattern that provides:
- Runtime selection of embedding backend
- Consistent interface for all backends
- Easy addition of new backends
- Testability (mocking for unit tests)
- Configuration-driven behaviour

## Decision

Implement a **Factory Pattern** with abstract base class:

1. **BaseEmbedder** abstract class defining interface
2. **create_embedder()** factory function for instantiation
3. **get_embedder()** singleton accessor for reuse
4. Configuration-driven backend selection

## Rationale

**Swappability:**
- Change embedding models via configuration
- No code changes needed to switch backends
- Users can experiment with different models

**Consistency:**
- All embedders implement same interface
- Guaranteed method signatures
- Type hints for IDE support

**Extensibility:**
- New backends just implement BaseEmbedder
- No changes to calling code
- Plugin architecture possible in future

**Testability:**
- Easy to mock for unit tests
- Can use fast model for testing
- Dependency injection ready

**Best Practice:**
- Standard GoF design pattern
- Well-understood by developers
- Industry-standard for this use case

## Alternatives Considered

**1. Direct instantiation everywhere**
```python
# Anti-pattern
if config.embedding_backend == "sentence-transformers":
    embedder = SentenceTransformerEmbedder()
else:
    embedder = OllamaEmbedder()
```
- **Pros:** Simple, explicit
- **Cons:** Repeated code, hard to change, not DRY
- **Decision:** Rejected—violates DRY, difficult to maintain

**2. Dependency Injection framework**
```python
# Using dependency injection container
embedder = container.resolve(Embedder)
```
- **Pros:** Very flexible, industry standard for large systems
- **Cons:** Overkill for v0.1, adds complexity, steep learning curve
- **Decision:** Deferred to v0.3+ if needed

**3. Strategy Pattern**
```python
# Strategy pattern
class EmbeddingStrategy:
    def set_embedder(self, embedder):
        self.embedder = embedder
```
- **Pros:** Runtime strategy switching
- **Cons:** More complex than factory, similar benefits
- **Decision:** Factory is simpler for this use case

**4. Import-time selection**
```python
# Module-level conditional import
if config.embedding_backend == "sentence-transformers":
    from .sentence_transformer import embedder
else:
    from .ollama_embedder import embedder
```
- **Pros:** Very simple
- **Cons:** Can't change at runtime, hard to test
- **Decision:** Rejected—not flexible enough

## Consequences

### Positive

✅ **Configuration-Driven:** Users select backend in config file
✅ **No Code Changes:** Switch models without touching code
✅ **Clean Separation:** Clear interface vs. implementation
✅ **Easy Testing:** Mock embedders for unit tests
✅ **Extensible:** New backends trivial to add
✅ **Type Safe:** Abstract base class enforces interface
✅ **Singleton Option:** Reuse embedder instances for efficiency

### Negative

⚠️ **Extra Abstraction:** One more layer of indirection
⚠️ **Slightly More Code:** Abstract class + factory function
⚠️ **Factory Maintenance:** Must update factory for each new backend

### Trade-Offs Accepted

- Abstraction overhead justified by flexibility
- Minimal extra code (~50 lines)
- Factory updates are straightforward

## Implementation

**Abstract base class:**
```python
from abc import ABC, abstractmethod
from typing import List

class BaseEmbedder(ABC):
    """Abstract base class for all embedding backends."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
```

**Factory function:**
```python
from src.config import get_settings

def create_embedder() -> BaseEmbedder:
    """Create embedder based on configuration."""
    settings = get_settings()

    if settings.embedding_backend == "sentence-transformers":
        from .sentence_transformer import SentenceTransformerEmbedder
        return SentenceTransformerEmbedder(
            model_name=settings.embedding_model
        )
    elif settings.embedding_backend == "ollama":
        from .ollama_embedder import OllamaEmbedder
        return OllamaEmbedder(
            model_name=settings.embedding_model
        )
    else:
        raise ValueError(f"Unknown backend: {settings.embedding_backend}")
```

**Singleton accessor:**
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embedder() -> BaseEmbedder:
    """Get singleton embedder instance."""
    return create_embedder()
```

**Usage:**
```python
from src.embeddings import get_embedder

# Get embedder (created once, cached)
embedder = get_embedder()

# Embed documents
embeddings = embedder.embed_documents(["doc1", "doc2"])

# Embed query
query_embedding = embedder.embed_query("search query")
```

## Testing Strategy

**Unit tests:**
```python
from unittest.mock import Mock

def test_retrieval_with_mock_embedder():
    mock_embedder = Mock(spec=BaseEmbedder)
    mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

    # Test with mock
    results = retriever.search(query, embedder=mock_embedder)
```

**Integration tests:**
```python
def test_with_real_embedder():
    embedder = create_embedder()  # Uses actual backend
    embeddings = embedder.embed_documents(["test"])
    assert len(embeddings[0]) == embedder.dimension
```

## Extension Points

**Adding new backend (example: Cohere):**

1. Create new embedder class:
```python
class CohereEmbedder(BaseEmbedder):
    def embed_documents(self, texts):
        # Implementation
        pass
```

2. Update factory:
```python
elif settings.embedding_backend == "cohere":
    from .cohere_embedder import CohereEmbedder
    return CohereEmbedder(api_key=settings.cohere_api_key)
```

3. Update configuration schema:
```python
embedding_backend: Literal["sentence-transformers", "ollama", "cohere"]
```

No other code changes required!

## Future Considerations

**v0.2:**
- Add async embedding support (`async def embed_documents`)
- Batch size configuration
- Caching layer for repeated embeddings

**v0.3:**
- Plugin architecture for third-party embedders
- Embedding model auto-detection
- Multi-model ensemble embeddings

**v1.0:**
- Full dependency injection framework if needed
- Dynamic embedder loading
- Embedder performance profiling

## Design Pattern Benefits

This implementation demonstrates several design principles:

**SOLID Principles:**
- **S**ingle Responsibility: Each embedder handles one backend
- **O**pen/Closed: Open for extension (new backends), closed for modification
- **L**iskov Substitution: All embedders interchangeable
- **I**nterface Segregation: Minimal required interface
- **D**ependency Inversion: Depend on abstraction (BaseEmbedder), not concretions

**Other Principles:**
- **DRY:** Factory eliminates repeated instantiation code
- **Separation of Concerns:** Interface vs. implementation
- **Configuration over Code:** Behavior driven by config

---

**Last Updated:** 2025-11-13

**Supersedes:** None

**Superseded By:** None
