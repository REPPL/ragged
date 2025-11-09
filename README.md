# ragged - Privacy-First Local RAG System

**Version:** 0.1.0
**License:** GPL-3.0

A privacy-first document question-answering system that runs entirely locally using Retrieval-Augmented Generation (RAG) technology. No cloud, no tracking, no compromises.

---

## What is ragged?

ragged is a local RAG (Retrieval-Augmented Generation) system that lets you ask questions about your documents and get accurate answers with citations - all while keeping your data completely private and local.

### Key Features

- 📚 **Multi-Format Support**: Ingest PDF, TXT, Markdown, and HTML documents
- 🧠 **Semantic Understanding**: Uses embeddings to understand meaning, not just keywords
- 🔍 **Smart Retrieval**: Finds relevant information across all your documents
- 💬 **Accurate Answers**: Generates natural language responses with source citations
- 🔒 **100% Private**: Everything runs locally - no data leaves your machine
- ⚡ **Hardware Optimized**: Supports CPU, CUDA, and Apple Silicon (MPS)
- 🎨 **Beautiful CLI**: Intuitive command-line interface with progress bars and colors

### How It Works

1. **Ingest**: Add documents to ragged's knowledge base
2. **Process**: Documents are chunked and embedded for semantic search
3. **Store**: Embeddings are stored in a local vector database
4. **Query**: Ask questions in natural language
5. **Retrieve**: ragged finds the most relevant document chunks
6. **Generate**: A local LLM generates an answer with citations

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  CLI Interface (Click + Rich)                           │
│  - ragged add <file>                                    │
│  - ragged query "<question>"                            │
│  - ragged list / clear / config / health                │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌─────────┐      ┌──────────┐     ┌──────────┐
   │Document │      │Retrieval │     │Generation│
   │Ingestion│      │ System   │     │  System  │
   └─────────┘      └──────────┘     └──────────┘
        │                 │                 │
        │                 │                 │
   ┌─────────┐      ┌──────────┐     ┌──────────┐
   │Chunking │      │ Vector   │     │  Ollama  │
   │ System  │      │  Store   │     │   LLM    │
   └─────────┘      │(ChromaDB)│     └──────────┘
        │           └──────────┘
        ▼
   ┌─────────┐
   │Embedding│
   │ Models  │
   └─────────┘
```

**Core Components:**

- **Document Ingestion**: Loads and converts documents to a common format
- **Chunking System**: Splits documents into semantic chunks with overlap
- **Embedding Models**: Converts text to vectors (sentence-transformers or Ollama)
- **Vector Store**: ChromaDB for semantic similarity search
- **Retrieval System**: Finds relevant chunks using cosine similarity
- **Generation System**: Ollama LLM generates answers with citations
- **CLI Interface**: User-friendly command-line tool

---

## Quick Start

### Prerequisites

- Python 3.14+ (or 3.11+)
- [Ollama](https://ollama.ai) installed and running
- ChromaDB (via Docker or pip)

### Installation

```bash
# Clone the repository
git clone https://github.com/REPPL/ragged.git
cd ragged

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Start services
docker-compose up -d  # Starts ChromaDB (if using Docker)
ollama serve          # Start Ollama (in separate terminal)
```

### Basic Usage

```bash
# Add documents to your knowledge base
ragged add /path/to/document.pdf
ragged add /path/to/notes.txt

# Ask questions
ragged query "What are the key findings?"
ragged query "Explain the methodology"

# Manage your knowledge base
ragged list    # Show collection statistics
ragged clear   # Clear all documents

# Check configuration and health
ragged config show
ragged health
```

---

## Configuration

ragged uses environment variables for configuration. Create a `.env` file:

```bash
# Environment
RAGGED_ENVIRONMENT=development
RAGGED_LOG_LEVEL=INFO

# Embedding Model
RAGGED_EMBEDDING_MODEL=sentence-transformers  # or: ollama
RAGGED_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# LLM
RAGGED_LLM_MODEL=llama3.2

# Chunking
RAGGED_CHUNK_SIZE=500
RAGGED_CHUNK_OVERLAP=100

# Services
RAGGED_CHROMA_URL=http://localhost:8001
RAGGED_OLLAMA_URL=http://localhost:11434
```

### Embedding Models

Two embedding backends are supported:

1. **sentence-transformers** (default)
   - Runs locally on CPU/GPU
   - Model: `all-MiniLM-L6-v2` (384 dimensions)
   - No external service required

2. **Ollama**
   - Requires Ollama service
   - Model: `nomic-embed-text` (768 dimensions)
   - Consistent with LLM backend

---

## Privacy & Security

ragged is designed with privacy as a core principle:

- ✅ **100% Local Processing**: No data leaves your machine
- ✅ **No External APIs**: All models run locally
- ✅ **No Telemetry**: No tracking, analytics, or phone-home
- ✅ **PII Filtering**: Automatic filtering in logs
- ✅ **Secure File Handling**: Path validation and size limits
- ✅ **Open Source**: GPL-3.0 licensed, fully auditable

### Security Features

- Path traversal protection
- File size validation (100MB limit)
- MIME type checking
- Input sanitization
- No hardcoded credentials
- Secure defaults

---

## Development

### Project Structure

```
ragged/
├── src/                    # Source code
│   ├── config/            # Configuration system
│   ├── ingestion/         # Document loading
│   ├── chunking/          # Text splitting
│   ├── embeddings/        # Embedding generation
│   ├── storage/           # Vector database
│   ├── retrieval/         # Semantic search
│   ├── generation/        # LLM integration
│   ├── utils/             # Utilities
│   └── main.py            # CLI entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
└── pyproject.toml         # Project metadata
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/integration/
pytest tests/unit/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Troubleshooting

### ChromaDB Connection Issues

```bash
# Check ChromaDB is running
docker ps | grep chromadb

# Restart ChromaDB
docker-compose restart chromadb
```

### Ollama Issues

```bash
# Check Ollama is running
ollama list

# Pull required model
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Performance

- For faster embeddings, use a GPU (CUDA or MPS)
- Reduce `RAGGED_CHUNK_SIZE` for better precision
- Increase `RAGGED_CHUNK_SIZE` for better recall

---

## FAQ

**Q: Does ragged send my data to the cloud?**
A: No. Everything runs 100% locally on your machine.

**Q: What file formats are supported?**
A: PDF, TXT, Markdown (.md), and HTML.

**Q: Can I use my own LLM?**
A: Yes! ragged uses Ollama, which supports many models (llama, mistral, etc.)

**Q: How much RAM do I need?**
A: Minimum 8GB recommended. More for larger document collections.

**Q: Can I use this commercially?**
A: Check the GPL-3.0 license terms. Commercial use permitted with source disclosure.

---

## Roadmap

### v0.1 (Current)
- ✅ Core RAG pipeline
- ✅ Multi-format document support
- ✅ Dual embedding backends
- ✅ CLI interface
- ✅ Privacy-first architecture

### v0.2 (Planned)
- [ ] Web UI (FastAPI + React)
- [ ] Enhanced retrieval (reranking, context windows)
- [ ] Few-shot prompting
- [ ] Document metadata management
- [ ] Performance optimizations
- [ ] Docker improvements

### v0.3 (Future)
- [ ] Multi-modal support (images, tables)
- [ ] Knowledge graph integration
- [ ] Advanced query processing
- [ ] Collaborative filtering

---

## Contributing

Contributions welcome! Please see `docs/development/` for development guidelines.

---

## License

GPL-3.0 License - see LICENSE file for details.

---

## Acknowledgments

Built with:
- [Ollama](https://ollama.ai) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [sentence-transformers](https://www.sbert.net/) - Embeddings
- [PyMuPDF4LLM](https://github.com/pymupdf/RAG) - PDF processing
- [Click](https://click.palletsprojects.com/) & [Rich](https://rich.readthedocs.io/) - CLI

---

## Contact

For development documentation, see `docs/development/devlog/v0.1/README.md`

**Created by REPPL** | **Powered by Claude Code**
