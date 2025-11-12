# Data Flow

This document describes how data flows through the Personal Research Service for the two primary operations: adding documents and querying.

## Adding Documents

### High-Level Flow

```
User adds document
  ↓
Wrangler processes (load, normalise, chunk)
  ↓
Librarian indexes (embed, store in vectors)
  ↓
Document available for retrieval
```

### Detailed Process

#### 1. User Initiates Addition
```bash
ragged add document.pdf --collection research --topic research
```

#### 2. Wrangler Processing

**Step 2.1**: Load document
- Detect format (PDF, Markdown, HTML, etc.)
- Apply appropriate loader
- Extract raw content

**Step 2.2**: Normalise
- Convert to markdown
- Extract tables (if enabled)
- Apply OCR (if needed for images/scanned PDFs)
- Clean and structure content

**Step 2.3**: Chunk document
- Apply chunking strategy (semantic, fixed-size, etc.)
- Respect chunk size and overlap settings
- Preserve section boundaries (if configured)
- Generate chunk metadata

**Step 2.4**: Track quality
- Calculate quality metrics per chunk
- Log processing statistics
- Identify potential issues

#### 3. Librarian Indexing

**Step 3.1**: Generate embeddings
- Use configured embedding model
- Create vector representations for each chunk
- Batch process for efficiency

**Step 3.2**: Store in vector database
- Add to ChromaDB collection
- Store chunk text and metadata
- Create searchable index

**Step 3.3**: Update Library metadata
- Generate document display name (smart extraction)
- Calculate content hash (SHA256)
- Check for duplicates (hash-based, then similarity)
- Update collection index
- Save document metadata

#### 4. Completion
Document is now:
- Searchable by semantic similarity
- Retrievable by metadata filters
- Available for query operations

## Querying Documents

### High-Level Flow

```
User submits brief
  ↓
Researcher receives brief
  ├─ Retrieves context via Librarian
  ├─ Gets persona context from Vault (if specified)
  ├─ Builds prompt with context + persona
  └─ Generates response with LLM
  ↓
Response returned to user
```

### Detailed Process

#### 1. User Initiates Query
```bash
ragged query "What are the key findings on RAG systems?" --persona professional
```

#### 2. Researcher Coordination

**Step 2.1**: Parse brief
- Extract query intent
- Identify key terms
- Determine context requirements

**Step 2.2**: Request context from Librarian
- Send query to Librarian
- Specify retrieval parameters (top_k, filters, etc.)
- Apply collection filters (if specified)

#### 3. Librarian Retrieval

**Step 3.1**: Embed query
- Use same embedding model as documents
- Generate query vector

**Step 3.2**: Search vector database
- Semantic search in ChromaDB
- Apply metadata filters
- Retrieve top_k candidates

**Step 3.3**: Apply reranking (if enabled)
- Use cross-encoder model
- Refine relevance scores
- Select final chunks

**Step 3.4**: Assemble context
- Collect selected chunks
- Include source metadata
- Format for prompt injection

#### 4. Researcher Generation

**Step 4.1**: Get persona context (if specified)
- Load persona configuration
- Extract referenced Vault sections
- Apply persona overrides (tone, complexity, etc.)

**Step 4.2**: Build prompt
- Combine system instructions
- Inject retrieved context
- Include persona context (if any)
- Add user brief

**Step 4.3**: Generate response
- Send to LLM (Ollama)
- Apply generation settings (temperature, max_tokens, etc.)
- Stream or batch response

**Step 4.4**: Format output
- Apply citation style
- Include source references
- Format as markdown (or specified format)

#### 5. Return Response
Response includes:
- Generated text
- Source citations
- Metadata (model used, chunks retrieved, etc.)

## Project-Based Context (Planned)

For project-based workflows (ADR-011), the flow will be extended:

### Project Context Accumulation
```
User submits brief to project
  ↓
Researcher retrieves:
  ├─ Library context (via Librarian)
  ├─ Previous project briefs and responses
  └─ Persona context (if specified)
  ↓
Response considers conversation history
  ↓
Brief and response saved to project
```

This enables:
- Conversational interaction
- Context building across queries
- Follow-up questions
- Iterative refinement

## Quality Feedback Loop (Planned)

For the quality audit system (ADR-009):

### Audit and Improvement Flow
```
Researcher detects low-quality retrieval
  ↓
Logs audit finding (chunk quality, relevance issues)
  ↓
Wrangler analyses audit patterns
  ↓
Wrangler optimises processing (chunking, normalisation)
  ↓
Future documents processed with improvements
```

This enables:
- Continuous improvement
- Automatic optimisation
- Quality monitoring
- No user intervention required

## Design Rationale

The data flow is designed to ensure:

1. **Clear Separation**: Each role handles its domain
2. **Modularity**: Steps can be optimised independently
3. **Traceability**: Every step is logged and traceable
4. **Configurability**: Each step respects configuration hierarchy
5. **Quality**: Multiple quality checks throughout the flow

## Related Documentation

- [Three-Role System](./three-role-system.md) - Role responsibilities
- [Storage Model](./storage-model.md) - Where data is stored
- [Configuration System](./configuration-system.md) - How flow is configured
