# Three-Role System

The Personal Research Service architecture is built around three specialised roles, each with distinct responsibilities and configuration templates.

## Wrangler (Document Processing)

**Responsibility**: Prepare documents for the Library

### Capabilities
- Load documents from various formats
- Normalize to markdown
- Extract tables and structure
- Chunk documents intelligently
- Track quality metrics

### Configuration
**Template**: `WranglerTemplate`

Configures:
- Processing settings (OCR, tables, chunking)
- Quality assurance rules
- Metadata extraction
- Performance tuning

### Typical Settings
```yaml
processing:
  ocr: true
  table_extraction: advanced
  markdown_normalization: true

chunking:
  strategy: semantic
  max_chunk_size: 512
  overlap: 50

quality:
  min_chunk_quality: 0.7
  track_metrics: true
```

## Librarian (Organisation & Retrieval)

**Responsibility**: Manage the Library and retrieve context

### Capabilities
- Index documents in vector store
- Generate embeddings
- Retrieve relevant context
- Organise collections
- Apply metadata filtering

### Configuration
**Template**: `LibrarianTemplate`

Configures:
- Embedding model settings
- Vector store configuration
- Retrieval strategy (semantic, keyword, hybrid)
- Reranking options
- Context assembly rules

### Typical Settings
```yaml
embeddings:
  model: sentence-transformers/all-MiniLM-L6-v2

retrieval:
  strategy: hybrid
  top_k: 10
  similarity_threshold: 0.7

reranking:
  enabled: true
  model: cross-encoder/ms-marco-MiniLM-L-6-v2
```

## Researcher (Coordination & Generation)

**Responsibility**: Coordinate research and generate responses

### Capabilities
- Process user briefs (queries)
- Coordinate with Librarian for retrieval
- Integrate persona context from Vault
- Generate responses using LLM
- Track quality and manage projects

### Configuration
**Template**: `ResearcherTemplate`

Configures:
- LLM settings (model, temperature, etc.)
- Brief processing strategy
- Response generation rules
- Quality tracking
- Project management

### Typical Settings
```yaml
llm:
  model: llama3.2:latest
  temperature: 0.7
  max_tokens: 2048

generation:
  citation_style: academic
  response_format: markdown
  include_sources: true

quality:
  track_citations: true
  verify_context_usage: true
```

## Role Interactions

### Document Ingestion Flow
```
User adds document
  ↓
Wrangler processes (load, normalize, chunk)
  ↓
Librarian indexes (embed, store)
  ↓
Document available in Library
```

### Query Processing Flow
```
User submits brief
  ↓
Researcher coordinates:
  ├─ Requests context from Librarian
  ├─ Retrieves persona from Vault (if specified)
  ├─ Builds prompt with context + persona
  └─ Generates response with LLM
  ↓
Response returned to user
```

## Design Rationale

See [ADR-007: Role-Based System](../decisions/adr-007-role-based-system.md) for the full decision record.

**Key Benefits**:
- **Separation of Concerns**: Each role has a focused responsibility
- **Configurability**: Independent tuning for each role
- **Scalability**: Roles can be optimized independently
- **Maintainability**: Clear boundaries reduce complexity
- **Testability**: Roles can be tested in isolation

## Related Documentation

- [Storage Model](./storage-model.md) - Where each role stores data
- [Configuration System](./configuration-system.md) - How roles are configured
- [Profile Templates](../profile-templates/README.md) - Example role configurations
