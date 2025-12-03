# CLI Essentials: Core Commands for Beginners

**What you'll learn**: The 7 essential commands to start using ragged effectively.

**Prerequisites**:
- ragged installed (see [Getting Started](../../tutorials/getting-started.md))
- Ollama running (`ollama serve`)
- ChromaDB running (Docker or in-memory mode)

**Reading time**: 15-20 minutes

---

## The Essential Commands

You can accomplish 90% of common tasks with just these 7 commands:

1. **`ragged health`** - Check if everything is working
2. **`ragged ingest pdf`** - Add documents (v0.5.3+)
3. **`ragged query text`** - Ask questions (v0.5.3+)
4. **`ragged list`** - See what you've added
5. **`ragged config`** - Manage settings
6. **`ragged gpu list`** - Check GPU availability (v0.5.3+)
7. **`ragged interactive`** - Launch interactive REPL shell (v0.8.8+)

Let's learn each one.

---

## 1. ragged health - Check System Status

**Purpose**: Verify that Ollama and ChromaDB are running correctly.

### Basic usage

```bash
ragged health
```

### Expected output (all working)

```
Checking services...

✓ Ollama: Running
  - Base URL: http://localhost:11434
  - Available models: llama3.2:3b

✓ ChromaDB: Running
  - Host: localhost:8000
  - Collections: 2 (text, vision)
  - Total chunks: 247

All services healthy!
```

### When to use

- ✅ Before adding your first document
- ✅ After setup to verify installation
- ✅ When troubleshooting connection issues
- ✅ After changing configuration

### Troubleshooting health check

**Problem**: `✗ Ollama: Not running`

**Solution**:
- **Mac**: Launch Ollama app from Applications
- **Linux/Windows**: Run `ollama serve` in a separate terminal

---

**Problem**: `✗ ChromaDB: Connection refused`

**Solution (Docker)**:
```bash
docker compose ps         # Check status
docker compose up -d      # Start if needed
```

**Solution (in-memory)**:
Check your `.env` file has `CHROMA_IN_MEMORY=true`.

---

## 2. ragged ingest pdf - Add Documents (v0.5.3+)

**Purpose**: Add PDF documents to your knowledge base with optional vision embeddings.

### Basic usage

```bash
# Add a single PDF
ragged ingest pdf document.pdf

# Add with vision embeddings (for image-heavy PDFs)
ragged ingest pdf research-paper.pdf --vision

# Add with specific GPU device
ragged ingest pdf manual.pdf --vision --device cuda:0

# Skip auto-correction for clean PDFs
ragged ingest pdf clean.pdf --no-auto-correct
```

### Advanced options

```bash
# Custom chunking strategy
ragged ingest pdf report.pdf --chunking semantic

# Custom batch size for vision processing
ragged ingest pdf diagrams.pdf --vision --batch-size 8

# Overwrite existing document without prompt
ragged ingest pdf updated.pdf --overwrite
```

### What happens during ingestion

1. **PDF Analysis** (if auto-correct enabled)
   - Detects rotation issues
   - Identifies duplicate pages
   - Checks page ordering
   - Generates quality score

2. **Text Processing**
   - Extracts text content
   - Chunks into semantic units
   - Generates text embeddings (384-dim)

3. **Vision Processing** (if --vision enabled)
   - Converts PDF pages to images
   - Generates vision embeddings (128-dim ColPali)
   - Stores page-level embeddings

4. **Storage**
   - Stores in dual collections (text + vision)
   - Indexes for fast retrieval

### When to use vision embeddings

✅ **Use --vision for**:
- Technical documents with diagrams
- Research papers with figures and charts
- Architectural drawings or schematics
- Any PDF where visual content is important

❌ **Skip --vision for**:
- Plain text documents
- Simple text-only reports
- When GPU isn't available
- When speed is critical

---

## 3. ragged ingest batch - Batch Processing (v0.5.3+)

**Purpose**: Add multiple PDFs from a directory at once.

### Basic usage

```bash
# Ingest all PDFs in a directory
ragged ingest batch ./documents/

# With vision embeddings
ragged ingest batch ./research-papers/ --vision

# Custom pattern matching
ragged ingest batch ./reports/ --pattern "2024-*.pdf"

# Non-recursive (current directory only)
ragged ingest batch ./current/ --no-recursive
```

### Advanced options

```bash
# Limit directory depth
ragged ingest batch ./deep-tree/ --max-depth 2

# Stop on first error
ragged ingest batch ./docs/ --fail-fast

# Don't skip duplicates (prompt for each)
ragged ingest batch ./updates/ --no-skip-duplicates
```

### When to use

- ✅ Adding entire folders of PDFs
- ✅ Migrating existing document collections
- ✅ Periodic bulk imports
- ✅ Automating ingestion workflows

---

## 4. ragged query text - Ask Questions (v0.5.3+)

**Purpose**: Query your documents using natural language.

### Basic usage

```bash
# Simple text query
ragged query text "What are the key findings?"

# Get more results
ragged query text "Explain the methodology" --num-results 10

# Show detailed metadata
ragged query text "database architecture" --show-metadata
```

### Visual content boosting

```bash
# Boost results with diagrams
ragged query text "system architecture" --boost-diagrams

# Boost results with tables
ragged query text "performance metrics" --boost-tables

# Boost both
ragged query text "technical specs" --boost-diagrams --boost-tables
```

### Output formats

```bash
# Human-readable (default)
ragged query text "summary"

# JSON for automation
ragged query text "findings" --format json > results.json
```

### Advanced: Image and Hybrid Queries (v0.5.3+)

```bash
# Image-only visual similarity search
ragged query image architecture-sketch.png

# Hybrid: text + image query
ragged query hybrid "authentication flow" diagram.png

# Custom weights for hybrid
ragged query hybrid "API design" sketch.png --text-weight 0.7 --vision-weight 0.3
```

### Expected output

```
Query: What are the key findings?

Found 5 results (127.3ms):

[1] research-paper-2024
    Score: 0.8934
    Type: text

[2] annual-report
    Score: 0.8721
    Type: vision

[3] technical-memo
    Score: 0.8456
    Type: text
```

### When to use each query mode

**Text query** (`query text`):
- General questions about content
- Semantic understanding required
- Fastest and most versatile

**Image query** (`query image`):
- "Find similar diagrams"
- Visual similarity search
- Requires documents with vision embeddings

**Hybrid query** (`query hybrid`):
- "Find auth diagrams mentioning OAuth"
- Combines text meaning + visual similarity
- Most powerful for visual documents

---

## 5. ragged list - View Documents

**Purpose**: See what documents are in your knowledge base.

### Basic usage

```bash
ragged list
```

### Expected output

```
Documents in knowledge base:

📄 research-paper-2024.pdf
   ID: abc-123-def
   Chunks: 47
   Added: 2024-11-23

📄 technical-manual.pdf
   ID: xyz-456-ghi
   Chunks: 124
   Vision: 45 pages
   Added: 2024-11-22

Total: 2 documents, 171 text chunks, 45 vision pages
```

---

## 6. ragged config - Manage Settings

**Purpose**: View and change ragged configuration.

### View current configuration

```bash
ragged config show
```

### Change settings

```bash
# Set a value
ragged config set top_k 10

# Reset to defaults
ragged config reset

# Interactive model selection
ragged config set-model
```

---

## 7. ragged gpu list - Check GPU Availability (v0.5.3+)

**Purpose**: Verify GPU devices for vision processing.

### Basic usage

```bash
# List available devices
ragged gpu list

# Detailed information
ragged gpu list --verbose
```

### Expected output

```
Available Devices (3):

[0] cuda:0
    Name: NVIDIA RTX 4090
    Memory: 24.00 GB
    Compute Capability: 8.9

[1] mps
    Name: Apple Silicon
    ✓ Optimal device

[2] cpu

Recommended device: mps
```

### When to use

- ✅ Before using --vision flag
- ✅ Troubleshooting vision embedding issues
- ✅ Choosing optimal device for performance

---

## 8. ragged interactive - Interactive REPL Mode (v0.8.8+)

**Purpose**: Launch an interactive shell for conversational RAG workflows.

### Basic usage

```bash
ragged interactive
```

### Welcome screen

```
ragged Interactive Mode v0.8.8
Type 'help' for available commands, 'exit' to quit.

ragged>
```

### Available commands in interactive mode

**Document Management:**
- `add <file>` - Add a document to the library
- `remove <pattern>` - Remove documents matching pattern
- `list` - Show all documents
- `show <document>` - Display document details

**Query & Search:**
- `query <question>` - Ask questions with RAG (LLM generation)
- `search <terms>` - Semantic search (no LLM)

**Configuration:**
- `set <key> <value>` - Change session settings
- `get <key>` - View current setting value
- `config` - Show all configuration

**Session Management:**
- `save session <file.json>` - Save current session state
- `load session <file.json>` - Restore a saved session
- `history` - Show command history
- `status` - Display system status

**Utilities:**
- `help` - Show available commands
- `clear` - Clear screen
- `exit` / `quit` - Exit interactive mode

### Example workflow

```bash
ragged> status
┌─ System Status ──────────────────┐
│ Version: 0.8.8                   │
│ Commands this session: 0         │
│ Configuration changes: 0         │
│                                  │
│ Services:                        │
│   Ollama: ✓ Connected           │
│   ChromaDB: ✓ Connected         │
└──────────────────────────────────┘

ragged> add research-paper.pdf
Processing research-paper.pdf...
Chunking with fixed strategy...
Generating embeddings...
✓ Added 47 chunks from 'research-paper.pdf'

ragged> list
📄 Documents in Library (1 documents, 47 chunks)

  • research-paper.pdf
    Path: /path/to/research-paper.pdf
    Chunks: 47

ragged> query what are the key findings?
Retrieving relevant chunks...
Generating response...

🔍 Answer:
Based on the document, the key findings are...

Sources:
  [1] research-paper.pdf (page 3, score: 0.94)
  [2] research-paper.pdf (page 7, score: 0.89)

ragged> set retrieval.top_k 10
✓ Set retrieval.top_k = 10

ragged> save session my-research.json
✓ Session saved to my-research.json

ragged> exit
Goodbye!
```

### When to use interactive mode

✅ **Use interactive mode for**:
- Exploratory research sessions
- Iterative query refinement
- Building up a knowledge base interactively
- Trying different settings without re-typing commands
- Saving and resuming research sessions

❌ **Use regular CLI for**:
- Scripting and automation
- Single queries
- CI/CD pipelines
- Batch operations

---

## Quick Reference Card

```bash
# Essential workflow
ragged health                                  # 1. Check services
ragged gpu list                                # 2. Check GPU (for vision)
ragged ingest pdf document.pdf --vision        # 3. Add document
ragged query text "your question"              # 4. Ask questions
ragged list                                    # 5. View documents

# Interactive mode
ragged interactive                             # Launch REPL shell
# Then in the shell:
#   add document.pdf                           # Add docs
#   query "what is this about?"                # Ask questions
#   save session work.json                     # Save progress

# Advanced workflow
ragged ingest batch ./docs/ --vision           # Batch ingest
ragged query image sketch.png                  # Visual search
ragged query hybrid "auth" diagram.png         # Multi-modal
ragged storage info                            # Check storage
```

---

## Next Steps

**Beginners**: Move on to [Intermediate Commands](./intermediate.md) to learn about:
- Storage management (`storage info`, `storage vacuum`)
- GPU monitoring (`gpu stats --watch`)
- Advanced query options and filtering

**Advanced users**: See [Advanced CLI](./advanced.md) for:
- GPU benchmarking and optimisation
- Custom retrieval configurations
- Storage migration and maintenance

---

**Related Documentation**:
- [Getting Started Tutorial](../../tutorials/getting-started.md)
- [CLI Features Overview](./cli-features.md)
- [Troubleshooting Guide](../troubleshooting/README.md)
