# ragged Examples

This directory contains examples demonstrating how to use ragged for different use cases.

## Directory Structure

```
examples/
├── basic/              # Simple getting started examples
├── advanced/           # Advanced configuration and usage
├── sample_documents/   # Sample documents for testing
├── configs/            # Example configuration files
└── README.md           # This file
```

## Quick Start

### 1. Basic Usage

See [`basic/quickstart.md`](./basic/quickstart.md) for a complete getting started guide.

```bash
# Ingest a document
ragged ingest path/to/document.pdf

# Query the document
ragged query "What is this document about?"

# Start web UI
ragged web
```

### 2. Sample Documents

Use the provided sample documents in [`sample_documents/`](./sample_documents/) to test ragged:

```bash
# Ingest sample documents
ragged ingest examples/sample_documents/

# Try sample queries
ragged query "What are RAG best practices?"
```

### 3. Configuration Examples

See [`configs/`](./configs/) for example configuration files:

- `basic_config.yml` - Minimal configuration
- `researcher_config.yml` - Configuration for academic research
- `developer_config.yml` - Configuration for software development
- `performance_config.yml` - Optimised for speed

## Examples by Use Case

### Academic Research

**Configuration:** [`configs/researcher_config.yml`](./configs/researcher_config.yml)

```bash
# Use researcher configuration
cp examples/configs/researcher_config.yml ~/.ragged/config.yml

# Ingest research papers
ragged ingest ~/Documents/papers/

# Query with citations
ragged query "What are the main findings on attention mechanisms?"
```

**Features:**
- Larger context window (7 chunks)
- IEEE citation format
- Detailed responses
- Academic tone

### Software Development

**Configuration:** [`configs/developer_config.yml`](./configs/developer_config.yml)

```bash
# Use developer configuration
cp examples/configs/developer_config.yml ~/.ragged/config.yml

# Ingest documentation
ragged ingest ~/Projects/docs/

# Query for code examples
ragged query "Show me how to implement OAuth2"
```

**Features:**
- Code-focused responses
- Smaller, faster model
- Concise answers
- Link-based citations

### Personal Knowledge Base

**Configuration:** [`configs/personal_config.yml`](./configs/personal_config.yml)

```bash
# Ingest various document types
ragged ingest ~/Documents/notes/
ragged ingest ~/Documents/articles/
ragged ingest ~/Downloads/ebooks/

# Natural language queries
ragged query "What did I read about productivity?"
```

**Features:**
- Hybrid search (keyword + semantic)
- Larger document collection
- Flexible chunk sizes
- Conversational tone

## Advanced Examples

### Batch Processing

See [`advanced/batch_processing.py`](./advanced/batch_processing.py)

```python
from ragged import RaggedClient

client = RaggedClient()

# Batch ingest multiple directories
directories = [
    "/path/to/papers",
    "/path/to/books",
    "/path/to/notes"
]

for directory in directories:
    client.ingest_folder(directory, recursive=True)

# Batch queries
queries = [
    "What is RAG?",
    "How does chunking work?",
    "What are embedding models?"
]

for query in queries:
    response = client.query(query)
    print(f"Q: {query}")
    print(f"A: {response}\n")
```

### Custom Chunking Strategy

See [`advanced/custom_chunking.py`](./advanced/custom_chunking.py)

```python
from ragged.chunking import RecursiveChunker

# Configure custom chunking
chunker = RecursiveChunker(
    chunk_size=300,  # Smaller chunks
    chunk_overlap=75,  # More overlap
    separators=["\n\n", "\n", ". ", " "]
)

# Use in ingestion
client.ingest(
    "document.pdf",
    chunker=chunker
)
```

### Hybrid Search

See [`advanced/hybrid_search.py`](./advanced/hybrid_search.py)

```python
from ragged.retrieval import HybridRetriever

# Configure hybrid search
retriever = HybridRetriever(
    vector_weight=0.6,  # 60% vector search
    bm25_weight=0.4,    # 40% keyword search
    k=5
)

# Query with hybrid search
results = retriever.retrieve("machine learning")
```

## Sample Documents

The [`sample_documents/`](./sample_documents/) directory contains example documents for testing:

| Document | Format | Topic | Size |
|----------|--------|-------|------|
| `rag_introduction.md` | Markdown | RAG fundamentals | 2 KB |
| `chunking_strategies.pdf` | PDF | Text chunking | 150 KB |
| `sample_research_paper.pdf` | PDF | Academic paper | 500 KB |
| `api_documentation.html` | HTML | API docs | 50 KB |

These documents cover common RAG topics and demonstrate how ragged handles different formats.

## Configuration Templates

### Basic Configuration

Minimal setup for getting started:

```yaml
# ~/.ragged/config.yml
llm_model: "llama3.2:latest"
embedding_model: "sentence-transformers"
chunk_size: 500
chunk_overlap: 100
retrieval_k: 5
```

### High-Performance Configuration

Optimised for speed:

```yaml
# Focus on speed over accuracy
llm_model: "llama3.2:3b"  # Smaller, faster model
embedding_model: "sentence-transformers"
embedding_model_name: "all-MiniLM-L6-v2"  # Fast embeddings
chunk_size: 400  # Smaller chunks = faster
retrieval_k: 3  # Fewer chunks = faster generation
```

### High-Quality Configuration

Optimised for quality:

```yaml
# Focus on accuracy over speed
llm_model: "llama3.1:70b"  # Larger, better model
embedding_model: "sentence-transformers"
embedding_model_name: "all-mpnet-base-v2"  # Better embeddings
chunk_size: 600  # Larger chunks = more context
retrieval_k: 7  # More chunks = better context
```

## Running Examples

### Python Examples

```bash
# Install ragged first
pip install -e .

# Run Python examples
python examples/advanced/batch_processing.py
python examples/advanced/custom_chunking.py
```

### CLI Examples

All CLI examples can be run directly:

```bash
# See basic examples
cat examples/basic/quickstart.md

# Try the commands
ragged ingest examples/sample_documents/rag_introduction.md
ragged query "What is RAG?"
```

## Contributing Examples

Have a useful example? Please contribute!

1. Create example in appropriate directory (`basic/` or `advanced/`)
2. Add documentation explaining the example
3. Include sample data if needed
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Troubleshooting

### Example doesn't work

Ensure ragged is installed:
```bash
pip install -e .
ragged --version
```

### Missing sample documents

Sample documents will be added in v0.2.3. For now, use your own documents.

### Configuration not loading

Ensure config file is in the right location:
```bash
mkdir -p ~/.ragged
cp examples/configs/basic_config.yml ~/.ragged/config.yml
```

## See Also

- [User Guides](../docs/guides/) - Comprehensive how-to guides
- [Reference Documentation](../docs/reference/) - Technical specifications
- [Architecture Overview](../docs/explanation/architecture-overview.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

---

**Note:** Some examples reference features not yet implemented. Check the roadmap in `docs/development/roadmaps/` to see when features will be available.
