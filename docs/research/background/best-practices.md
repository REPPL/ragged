# RAG Best Practices

Best practices and proven patterns for building RAG systems, extracted from research and industry standards.

## Document Processing

### Chunking Best Practices

**Recommended Baseline**:
- Strategy: Recursive character splitting
- Chunk size: 400-500 tokens
- Overlap: 15-20% (75-100 tokens)
- Respect document structure

**Key Principles**:
1. **Never mix content across sections** - Preserve authorial intent and topical coherence
2. **Use hierarchical separators** - Iterate through `["\n\n", "\n", ". ", " ", ""]`
3. **Respect syntax boundaries** - For code, use language-specific splitters
4. **Preserve context** - Include section headings in metadata

**Document-Specific Strategies**:

**PDFs**:
- Convert to markdown first (PyMuPDF4llm)
- Split on headers to maintain structure
- Extract tables separately (see Tables section)

**Code Repositories**:
- Use language-specific splitters
- Smaller chunks: ~100 tokens with 15-token overlap
- Respect function/class boundaries

**Structured Documents**:
- Use "by title" chunking (Unstructured)
- Maintain hierarchy in metadata
- Link chunks to their parent sections

### Table Handling

**Best Practice**: Extract and process separately

1. **Extract**: Use pdfplumber or Docling for table detection
2. **Convert**: Transform to structured format (CSV/HTML)
3. **Chunk**: Treat as distinct chunks with descriptive metadata
4. **Link**: Connect to surrounding context via metadata

**Why Separate**:
- Tables have different semantic structure
- Standard chunking often breaks table coherence
- Enables table-specific retrieval strategies

### Metadata Extraction

**Document-Level Metadata**:
- Title
- Author
- Creation date
- Document type
- Source path

**Chunk-Level Metadata**:
- Page number
- Section heading
- Chunk type (text, table, code)
- Word count
- Parent document reference

**Extraction Approaches**:

1. **Structured PDFs**: Extract from PDF metadata
2. **Inconsistent Formats**: Use LLM extraction (GPT-4/Claude)
3. **Complex Layouts**: Use vision LLMs for filled forms, signatures, etc.

**Usage**: Implement as searchable filters in vector database
- Example: "financial reports from CFO in Q4 2024"
- Reduces irrelevant results without reranking overhead

## Retrieval Strategies

### Hybrid Search

**Why Hybrid**:
- Vector embeddings struggle with: exact keywords, abbreviations, product codes, proper names
- Keyword search misses: semantic relationships, synonyms, context
- **12-30% accuracy improvement** on domain-specific tasks

**Implementation**:
1. **Parallel Retrieval**: Run BM25 (lexical) and vector search simultaneously
2. **Result Fusion**: Use Reciprocal Rank Fusion or weighted combination
3. **Weighting**: Start with alpha=0.7 (favoring vectors), tune for your domain

**When to Use**:
- Technical queries with specific terms
- Domain-specific terminology
- Mixed semantic and keyword requirements

### Retrieval Parameters

**Starting Points**:
- `top_k`: 10-15 candidates
- `similarity_threshold`: 0.7
- `reranking`: Enable for quality-critical applications

**Tuning Approach**:
1. Start with defaults
2. Measure retrieval quality (see Evaluation)
3. Adjust based on precision/recall needs
4. Consider query type (factual vs conceptual)

### Context Assembly

**Principles**:
1. **Include source metadata** - Enable citation and verification
2. **Maintain chunk order** - Preserve document flow when possible
3. **Add section headings** - Provide context for isolated chunks
4. **Limit total context** - Balance coverage vs focus

**Context Window Management**:
- Small windows (4K-8K tokens): Aggressive retrieval, more focused
- Large windows (32K-128K tokens): Selective retrieval, more comprehensive

## Generation

### Prompt Engineering

**Structure**:
```
[System Instructions]
[Retrieved Context with Citations]
[Persona Context (if applicable)]
[User Query]
```

**Best Practices**:
1. **Clear instructions** - Tell the model to use provided context
2. **Citation requirements** - Specify citation style and format
3. **Fallback behaviour** - What to do if context insufficient
4. **Tone and style** - Set via persona or explicit instructions

### Response Quality

**Ensure**:
- Responses supported by retrieved context (faithfulness)
- Answers address the query (relevance)
- Sources properly cited
- Hallucinations minimized

**Monitor**:
- Context usage (are retrieved chunks actually used?)
- Citation accuracy (do sources support claims?)
- User feedback (thumbs up/down, corrections)

## Configuration and Architecture

### Modular Design

**Six Core Modules**:
1. **Indexing**: Chunking, structure organisation
2. **Pre-Retrieval**: Query expansion, transformation
3. **Retrieval**: Vector search, algorithm selection
4. **Post-Retrieval**: Reranking, compression
5. **Generation**: LLM inference, output validation
6. **Orchestration**: Routing, scheduling, fusion

**Benefits**:
- Independent scaling of components
- A/B testing per module
- Swap implementations without cascading changes

### Configuration-Driven Design

**Principle**: Experiments shouldn't require code changes

**Implementation**:
- YAML/JSON specifications for pipeline behaviour
- Profile system for domain-specific optimisations
- Runtime overrides via CLI flags

**Example**:
```yaml
# profiles/topic/legal/default.yaml
wrangler:
  chunking:
    strategy: document-aware
    preserve_citations: true

librarian:
  retrieval:
    strategy: hybrid
    weighting: 0.5  # Equal keyword/semantic for legal

researcher:
  generation:
    citation_style: bluebook
```

### Progressive Enhancement

**Start Simple**:
1. Linear pipeline: Index → Retrieve → Generate
2. Single embedding model
3. Basic chunking

**Add Complexity Where Measured**:
1. Hybrid search (if keyword matching important)
2. Reranking (if precision critical)
3. Query transformation (if queries poorly formed)
4. Graph integration (if relationships matter)

**Measurement First**: Every enhancement should improve measurable metrics

## Evaluation and Monitoring

### Evaluation Metrics

**Retrieval Quality**:
- Context precision: Usefulness of retrieved chunks
- Context recall: Coverage of necessary information
- Retrieval latency

**Generation Quality**:
- Faithfulness: Response supported by context
- Answer relevancy: Response addresses query
- Citation accuracy: Sources correctly attributed

**System Metrics**:
- End-to-end latency
- Token usage
- Throughput (queries/second)
- Error rates

### Evaluation Frameworks

**RAGAS** (Recommended for starting):
- Reference-free evaluation
- LLM-as-judge methodology
- Integrates with LangChain, LlamaIndex
- Open source

**TruLens** (For debugging):
- Component-level tracing
- Step visualisation
- Latency tracking per stage

**Phoenix** (For observability):
- Visual process architecture
- Hallucination detection
- Production monitoring

### Continuous Monitoring

**Track**:
1. Query patterns (what users ask)
2. Retrieval failures (low similarity scores)
3. Generation quality (user feedback)
4. System performance (latency, errors)

**Act On**:
- Retrieval failures → Improve chunking or embeddings
- Poor generation → Adjust prompts or model
- High latency → Optimise retrieval or reduce context

## Memory and Performance

### M4 Max Optimisation

**Unified Memory Advantages**:
- Zero-copy operations between components
- Multiple models simultaneously in memory
- No CPU-GPU transfer overhead

**Memory Budget** (128GB M4 Max):
- macOS + applications: 8-12GB
- Vector database: 2-10GB (depends on collection size)
- Embedding model: 1-2GB
- LLM weights: 4-40GB (depends on model)
- Context/KV cache: 5-20GB (scales with context window)

**Example Configurations**:

**Balanced** (21GB total):
- Mistral Small 24B: 13GB
- Qwen3-4B embeddings: 2.5GB
- Vector DB: 5GB
- = 100GB remaining for context

**Quality** (55GB total):
- Llama 3.3 70B: 40GB
- Qwen3-8B embeddings: 4.5GB
- Vector DB: 10GB
- = 70GB for context

**Speed** (8GB total):
- Qwen 2.5 7B: 4GB
- Qwen3-0.6B embeddings: 900MB
- Vector DB: 3GB
- = 115GB remaining

### Scalability

**Vector Database Capacity** (M4 Max 128GB):

**Without Optimisation**:
- 15-20 million vectors (1536 dimensions)
- Sub-50ms query latency

**With Optimisation**:
- Scalar quantization: 4x memory reduction
- Disk offloading: Hot data in RAM, cold on SSD
- 50-100 million vectors possible
- Query latency: 50-200ms (with disk offloading)

**Indexing Strategies**:
- Hierarchical indexing for large corpora
- Parent-child node relationships
- Per-node summaries for fast traversal

## Production Deployment

### Architecture Pattern

**Microservices Approach**:

**Ingestion Service**:
- Document parsing
- Chunking
- Embedding generation
- Vector indexing

**Query Service**:
- Pre-processing (query transformation)
- Retrieval (vector search ± graph)
- Post-processing (reranking)
- Generation (LLM)

**Benefits**:
- Independent scaling
- Isolated failures
- Easier testing
- Clear boundaries

### API Design

**Streaming Responses**:
- Dramatically improves UX for long-form generation
- Start rendering within 1-2 seconds vs 15-20 second wait
- Implement via Server-Sent Events or WebSockets

**Async Processing**:
- Message queues (Redis, RabbitMQ) for batch ingestion
- Background indexing without blocking queries
- Load management during spikes

### Observability

**Deploy Early**:
- OpenTelemetry for distributed tracing
- Prometheus for metrics collection
- Grafana for visualisation

**Monitor Both**:
- Technical metrics (latency, errors, throughput)
- Quality metrics (retrieval scores, user feedback)

**Alert On**:
- Error rate spikes
- Latency degradation
- Quality metric drops
- Resource exhaustion

## Advanced Patterns

### Multi-Modal RAG

**Representation Strategies**:

1. **Unified Embedding Space**: CLIP-like models embed all modalities together
2. **Ground to Text**: Caption images (GPT-4V), transcribe audio (Whisper), then use text embeddings
3. **Separate Stores**: Per-modality vector stores with multi-modal reranker

**Recommended** (Production):
- Use vision LLMs (GPT-4V, LLaVA) for preprocessing
- Generate descriptions for images, charts, diagrams
- Store as text chunks with links to original media
- Retrieve text context + present original visuals

### Graph Integration

**When to Use**:
- Entity relationships matter as much as semantic similarity
- Domains: cybersecurity, supply chain, healthcare, finance
- Knowledge-intensive applications

**Architecture**:
- Maintain entity IDs synchronized between vector DB and Neo4j
- Semantic search first, then graph traversal for context
- Gather entity relationships before generation

**Trade-off**: Additional complexity (two databases, entity extraction) vs richer context

### Agentic RAG

**Beyond Simple Retrieve-Generate**:
- Autonomous decisions about when/what to retrieve
- Multi-step reasoning with tool usage
- Self-correction mechanisms

**Patterns**:
- **Self-RAG**: Self-reflection on retrieval necessity and output quality
- **Corrective RAG**: Fallback strategies when context insufficient
- **Adaptive RAG**: Dynamic retrieval timing based on confidence

**Foundation**: Modular architecture with routing, scheduling, fusion modules

## Development Workflow

### Start Simple, Measure, Add Complexity

**Phase 1**: Baseline
- Linear pipeline
- Single model
- Basic chunking
- **Measure everything**

**Phase 2**: Identify Bottlenecks
- Where does retrieval fail?
- What queries perform poorly?
- Which chunks never retrieved?

**Phase 3**: Targeted Improvements
- Add complexity only where metrics justify
- A/B test changes
- Validate improvements

**Phase 4**: Production Hardening
- Add monitoring
- Implement error handling
- Optimise hot paths
- Plan scaling strategy

### Key Success Factors

1. **Measure First**: Establish baseline metrics before optimising
2. **Start Simple**: Linear pipeline, proven components
3. **Modular Design**: Independent component evolution
4. **Configuration-Driven**: Experiments without code changes
5. **Quality Monitoring**: Track both technical and quality metrics
6. **Iterative Improvement**: Add complexity where validated by data

## References

See [RAG Research](./rag.md) for detailed technical background and [Resources](./resources.md) for papers, tools, and communities.
