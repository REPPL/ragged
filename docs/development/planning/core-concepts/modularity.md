# Modularity & Extensibility

**Status**: 🚧 Coming Soon
**Last Updated**: 2025-11-09

## Overview

This document describes ragged's modular architecture and extension points for customisation and enhancement.

---

## Coming Soon

This document will cover:

### Design Principles

#### Separation of Concerns
- **Document Processing**: Independent component
- **Embedding Generation**: Swappable providers
- **Vector Storage**: Database-agnostic interface
- **Retrieval**: Strategy pattern for algorithms
- **Generation**: LLM provider abstraction
- **UI**: Decoupled from core logic

#### Interface-Based Design
- Clear contracts between components
- Minimal coupling
- Dependency injection
- Plugin architecture

### Core Components

#### Document Processor
```python
# Abstract interface
class DocumentProcessor:
    def process(file_path) -> Document
    def supports(file_type) -> bool
```

**Implementations**:
- PDFProcessor
- TextProcessor
- MarkdownProcessor
- HTMLProcessor
- (Extensible for custom formats)

#### Embedding Provider
```python
class EmbeddingProvider:
    def embed_text(text) -> Vector
    def embed_batch(texts) -> List[Vector]
```

**Implementations**:
- LocalEmbeddingProvider (sentence-transformers)
- OllamaEmbeddingProvider
- (Optional: OpenAIEmbeddingProvider)

#### Vector Store
```python
class VectorStore:
    def add(vectors, metadata)
    def search(query_vector, k) -> Results
    def delete(ids)
```

**Implementations**:
- ChromaDBStore
- QdrantStore
- (Extensible for other databases)

#### Retrieval Strategy
```python
class RetrievalStrategy:
    def retrieve(query, k) -> List[Chunk]
```

**Implementations**:
- SemanticRetrieval
- KeywordRetrieval
- HybridRetrieval
- AdaptiveRetrieval (v0.4+)

#### LLM Provider
```python
class LLMProvider:
    def generate(prompt, context) -> Response
    def stream(prompt, context) -> Iterator[str]
```

**Implementations**:
- OllamaProvider
- (Optional: OpenAIProvider, AnthropicProvider)

### Extension Points

#### Custom Document Formats
Users can add support for new file formats:
```python
from ragged.processors import DocumentProcessor

class CustomProcessor(DocumentProcessor):
    def supports(self, file_type):
        return file_type == '.custom'

    def process(self, file_path):
        # Custom processing logic
        return Document(...)
```

#### Custom Retrieval Strategies
Implement domain-specific retrieval:
```python
from ragged.retrieval import RetrievalStrategy

class DomainSpecificRetrieval(RetrievalStrategy):
    def retrieve(self, query, k):
        # Custom retrieval logic
        return chunks
```

#### Custom Preprocessing
Add custom document preprocessing:
```python
from ragged.preprocessors import Preprocessor

class DomainNormaliser(Preprocessor):
    def preprocess(self, text):
        # Domain-specific normalisation
        return normalised_text
```

### Plugin System (v0.4+)

#### Plugin Interface
```python
class RaggedPlugin:
    def name(self) -> str
    def version(self) -> str
    def activate(self, ragged_instance)
    def deactivate(self)
```

#### Plugin Types
- **Processors**: New document formats
- **Retrievers**: Custom retrieval strategies
- **Evaluators**: Custom metrics
- **UI Extensions**: Dashboard widgets
- **Integrations**: External services

### Configuration System

#### Modular Configuration
```yaml
# Component selection
components:
  document_processor: default
  embedding_provider: local
  vector_store: chromadb
  retrieval_strategy: hybrid
  llm_provider: ollama

# Component-specific settings
chromadb:
  persist_directory: ./data/vectors

ollama:
  host: localhost
  port: 11434
```

#### Runtime Component Switching
```python
from ragged import Ragged

rag = Ragged()
rag.set_embedding_provider('openai')  # Switch providers
rag.set_retrieval_strategy('semantic')  # Change strategy
```

### Testing & Mocking

#### Component Mocking
Each component is independently testable:
```python
from ragged.testing import MockEmbeddingProvider

# Test with mock embeddings
rag = Ragged(embedding_provider=MockEmbeddingProvider())
```

### Versioning & Compatibility

#### Component Versioning
- Each component has independent version
- Compatibility matrix documented
- Breaking changes communicated

#### Migration Support
- Configuration migration tools
- Data migration utilities
- Backward compatibility where possible

---

## Related Documentation

- **[Architecture](../architecture/README.md)** - Overall system design
- **[Configuration System](../architecture/configuration-system.md)** - Configuration details
- **[Testing Strategy](testing-strategy.md)** - Testing approach
- **[Technology Stack](../technologies/README.md)** - Technology choices

---

*This document will be expanded with detailed component specifications and examples*
