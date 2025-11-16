# Quick Start Guide

Get up and running with ragged in 5 minutes!

## Prerequisites

- Python 3.12 installed
- Ollama installed and running
- A document to query (PDF, TXT, MD, or HTML)

## Installation

1. **Clone and install ragged:**

```bash
git clone https://github.com/yourusername/ragged.git
cd ragged
pip install -e .
```

2. **Set up Ollama:**

```bash
# Ensure Ollama is running
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2
```

3. **Start ChromaDB (optional - can run without Docker):**

```bash
docker-compose up -d chromadb
```

## Your First Query

### Step 1: Ingest a Document

```bash
# Ingest a single document
ragged ingest path/to/your/document.pdf

# Or ingest a folder
ragged ingest path/to/documents/
```

**Example output:**
```
📄 Processing: document.pdf
✅ Successfully ingested: document.pdf
   - 15 chunks created
   - 384-dimensional embeddings
   - Stored in ChromaDB
```

### Step 2: Query Your Document

```bash
ragged query "What is this document about?"
```

**Example output:**
```
╭─────────────────────────────────────────────────────────────╮
│ Answer                                                       │
├─────────────────────────────────────────────────────────────┤
│ This document discusses the fundamentals of Retrieval-      │
│ Augmented Generation (RAG), a technique that combines       │
│ document retrieval with large language models to provide    │
│ accurate, grounded responses.                               │
│                                                              │
│ Key topics covered include:                                 │
│ • Vector embeddings and semantic search                     │
│ • Chunking strategies for optimal retrieval                │
│ • Integration with LLMs for generation                     │
╰─────────────────────────────────────────────────────────────╯

📚 Sources:
  [1] document.pdf (page 1, chunk 3)
  [2] document.pdf (page 2, chunk 7)
```

### Step 3: Use the Web UI

```bash
ragged web
```

Then open http://localhost:7860 in your browser.

## Common Commands

### Ingestion

```bash
# Ingest single file
ragged ingest document.pdf

# Ingest folder (non-recursive)
ragged ingest ~/Documents/

# Ingest folder recursively
ragged ingest ~/Documents/ --recursive

# Check status
ragged list
```

### Querying

```bash
# Simple query
ragged query "What is RAG?"

# Interactive mode (coming in v0.3)
ragged query --interactive

# Specify number of sources
ragged query "Explain chunking" --k 7

# Use different model
ragged query "What is this about?" --model llama3.1:8b
```

### Web Interface

```bash
# Start web UI
ragged web

# Custom port
ragged web --port 8080

# API only (no UI)
ragged api
```

### Health Checks

```bash
# Check if services are running
ragged health
```

**Example output:**
```
Checking ragged health...
✅ Ollama: Running (http://localhost:11434)
   Models: llama3.2:latest, llama3.1:8b
✅ ChromaDB: Running (http://localhost:8001)
   Collections: ragged_documents
✅ Embeddings: sentence-transformers (all-MiniLM-L6-v2)
```

## Configuration

### Quick Config

Create `~/.ragged/config.yml`:

```yaml
# Basic configuration
llm_model: "llama3.2:latest"
chunk_size: 500
chunk_overlap: 100
retrieval_k: 5
```

### Environment Variables

Or use environment variables:

```bash
export RAGGED_LLM_MODEL="llama3.1:8b"
export RAGGED_CHUNK_SIZE=600
export RAGGED_RETRIEVAL_K=7

ragged query "test query"
```

## Workflow Examples

### Academic Research Workflow

```bash
# 1. Ingest research papers
ragged ingest ~/Research/papers/

# 2. Query with academic focus
ragged query "What are the main contributions of this work?"

# 3. Get detailed citations
ragged query "How does this relate to previous research?" --k 7
```

### Documentation Search

```bash
# 1. Ingest API documentation
ragged ingest ~/Projects/myproject/docs/

# 2. Search for specific topics
ragged query "How do I authenticate users?"

# 3. Find code examples
ragged query "Show me example API calls"
```

### Personal Knowledge Base

```bash
# 1. Ingest various sources
ragged ingest ~/Documents/notes/
ragged ingest ~/Documents/articles/
ragged ingest ~/Downloads/ebooks/

# 2. Ask questions
ragged query "What did I learn about productivity?"

# 3. Find specific topics
ragged query "Notes on Python async programming"
```

## Tips and Tricks

### 1. Choose the Right Model

- **Fast queries:** Use `llama3.2:3b`
- **Balanced:** Use `llama3.2:latest` (default)
- **Best quality:** Use `llama3.1:70b` (requires powerful hardware)

```bash
ragged query "test" --model llama3.2:3b  # Fast
ragged query "test" --model llama3.1:70b  # Slow but better
```

### 2. Adjust Chunk Size

- **Technical docs:** Use smaller chunks (300-400)
- **Books/articles:** Use larger chunks (500-600)
- **Mixed content:** Use default (500)

```bash
export RAGGED_CHUNK_SIZE=300  # For code documentation
export RAGGED_CHUNK_SIZE=600  # For long-form content
```

### 3. Tune Retrieval

- **Focused answers:** Use fewer chunks (k=3)
- **Comprehensive answers:** Use more chunks (k=7-10)

```bash
ragged query "quick question" --k 3
ragged query "detailed explanation" --k 7
```

### 4. Multiple Models

Pull multiple models for different use cases:

```bash
ollama pull llama3.2:3b      # Fast model
ollama pull llama3.2:latest  # Default model
ollama pull llama3.1:70b     # High-quality model
ollama pull codellama:34b    # Code-focused model
```

Then switch as needed:

```bash
ragged query "code question" --model codellama:34b
```

## Troubleshooting

### Ollama not running

```bash
# Start Ollama
ollama serve

# In another terminal, verify
ollama list
```

### ChromaDB connection error

```bash
# Check if ChromaDB is running
docker ps | grep chroma

# Restart ChromaDB
docker-compose restart chromadb

# Or use in-process mode (slower)
export RAGGED_CHROMA_URL=":memory:"
```

### Model not found

```bash
# Check available models
ollama list

# Pull the model
ollama pull llama3.2
```

### No documents found

```bash
# List ingested documents
ragged list

# Check data directory
ls ~/.ragged/
```

### Slow responses

- Use a smaller model: `--model llama3.2:3b`
- Reduce retrieval chunks: `--k 3`
- Use smaller chunks: `export RAGGED_CHUNK_SIZE=300`

## Next Steps

1. **Read the guides:** See `docs/guides/` for in-depth how-tos
2. **Explore examples:** Check `examples/advanced/` for advanced usage
3. **Configure for your use case:** See `examples/configs/` for templates
4. **Join the community:** See README for contribution guidelines

## Getting Help

- **Documentation:** `docs/`
- **GitHub Issues:** Report bugs or request features
- **Discussions:** Ask questions on GitHub Discussions

---

**Congratulations!** You're now ready to use ragged for your document question-answering needs.

Happy querying! 🚀
