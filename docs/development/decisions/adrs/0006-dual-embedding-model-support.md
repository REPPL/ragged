# ADR-0006: Dual Embedding Model Support

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Embeddings

## Context

Users may prefer different embedding models based on:
- Hardware capabilities (GPU vs CPU)
- Accuracy needs (dimension count)
- Local vs API preferences
- Consistency with LLM backend choice

ragged needs to support multiple embedding backends while maintaining a simple, consistent interface.

## Decision

Support two embedding backends via factory pattern:

1. **sentence-transformers**
   - Model: all-MiniLM-L6-v2
   - Dimensions: 384
   - Backend: Local PyTorch

2. **Ollama**
   - Model: nomic-embed-text
   - Dimensions: 768
   - Backend: Ollama service

Users select via configuration file (`embedding_model` setting).

## Rationale

- **Flexibility**: Users choose based on their specific needs
- **Offline Support**: sentence-transformers works fully offline without any service
- **Accuracy**: nomic-embed-text provides higher dimensions for potentially better retrieval
- **Hardware**: sentence-transformers supports GPU acceleration when available
- **Consistency**: Ollama users can keep same backend for both embeddings and LLM generation
- **Future-Proof**: Easy to add more backends later (OpenAI, Cohere, custom models)

## Alternatives Considered

### 1. sentence-transformers only

**Pros:**
- Simpler implementation
- Fewer dependencies
- Works offline guaranteed
- No service required

**Cons:**
- No choice for users
- Locks into one model family
- Can't leverage Ollama ecosystem

**Rejected:** Too restrictive, doesn't serve diverse user needs

### 2. Ollama only

**Pros:**
- Single backend for embeddings + LLM
- Consistent experience
- Leverage Ollama ecosystem

**Cons:**
- Requires Ollama service always running
- No offline fallback
- Higher barrier to entry

**Rejected:** Forces dependency on Ollama service

### 3. OpenAI embeddings

**Pros:**
- Very high quality
- Simple API
- No local computation

**Cons:**
- **Violates privacy-first principle** (external API)
- Costs money
- Requires internet
- Documents leave user's machine

**Rejected:** Fundamentally incompatible with ragged's core principles

## Implementation

Factory pattern in `src/embeddings/factory.py`:

```python
def create_embedder(config: Settings) -> BaseEmbedder:
    """Create embedder based on configuration."""
    if config.embedding_model == "sentence-transformers":
        return SentenceTransformerEmbedder(config)
    elif config.embedding_model == "ollama":
        return OllamaEmbedder(config)
    else:
        raise ValueError(f"Unknown embedding model: {config.embedding_model}")

def get_embedder() -> BaseEmbedder:
    """Get singleton embedder instance."""
    # Singleton pattern for performance
```

Abstract base class ensures consistency:

```python
class BaseEmbedder(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed single text string."""

    @abstractmethod
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed batch of documents."""
```

## Consequences

### Positive

- User choice and flexibility
- Can switch models without code changes (just config)
- Future backends easy to add (implement BaseEmbedder)
- Testing can use faster model for speed
- Each backend optimised for its use case

### Negative

- More code to maintain (2 implementations + factory)
- **Dimension mismatch risk**: If user switches models, existing embeddings are incompatible
- Need to document trade-offs for users
- Two backends means two potential failure modes

### Neutral

- Factory pattern adds abstraction layer
- Slightly more complex than single backend

## User Guidance

Documentation must explain trade-offs:

**Use sentence-transformers when:**
- Want guaranteed offline operation
- Have limited storage (smaller model)
- Don't use Ollama for LLM
- Want faster embedding on CPU

**Use Ollama when:**
- Already using Ollama for LLM generation
- Want higher embedding dimensions (768 vs 384)
- Have Ollama service running anyway
- Want consistency across backends

## Migration Path

If switching embedding models:
1. Must re-ingest all documents (dimension mismatch)
2. Clear vector database
3. Update configuration
4. Run ingestion again

**Future:** Consider supporting multiple models simultaneously with separate collections.

## Related

- [ADR-0004: Factory Pattern for Embedders](./0004-factory-pattern-for-embedders.md)
- [ADR-0012: Ollama for LLM Generation](./0012-ollama-for-generation.md)
- [Technology Evaluation: Embeddings](../../planning/technologies/embeddings.md)

---

## Related Documentation

- [Factory Pattern (ADR-0004)](./0004-factory-pattern-for-embedders.md) - Embedder abstraction
- [Embedding Models](../../planning/technologies/) - Model choices
- [Embedding Architecture](../../planning/architecture/) - System design

---
