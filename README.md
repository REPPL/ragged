[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-red.svg)]()


*This project is my attempt to learn fully AI-based 'vibe' coding and to document my use of AI coding assistants [transparently](./docs/development/methodology/ai-assistance.md). Expect breaking changes before v1.0.*


# `ragged`

## Privacy-First Local RAG System

**Your private, intelligent document assistant that runs entirely on your computer:** `ragged` is a local RAG *(Retrieval-Augmented Generation)* system that lets you ask questions about your documents and get accurate answers with citations - all while keeping your data completely private and local.

### Principles

1. **Privacy First**: 100% local by default. External services only with explicit user consent.
2. **User-Friendly**: Simple for beginners, powerful for experts (progressive disclosure).
3. **Transparent**: Open source, well-documented, educational.
4. **Quality-Focused**: Built-in evaluation and testing from the start.
5. **Continuous Improvement**: Each version adds value while maintaining stability.

### Aspirations

- 📚 **Multi-Format Support**: Ingest PDF, TXT, Markdown, and HTML documents
- 🧠 **Semantic Understanding**: Uses embeddings to understand meaning, not just keywords
- 🔍 **Smart Retrieval**: Finds relevant information across all your documents
- 💬 **Accurate Answers**: Generates natural language responses with source citations
- 🔒 **100% Private**: Everything runs locally - no data leaves your machine
- ⚡ **Hardware Optimised**: Supports CPU, Apple Silicon (MLX), and CUDA (planned)
- 🎨 **Intuitive CLI**: Command-line interface with progress bars and colors

### How It Works

*It's simple:* Upload your documents (PDFs, text files, web pages), ask questions, and `ragged` finds the most relevant information to respond -— all running locally on your machine.

![ragged Architecture](docs/assets/img/architecture-diagram.png)

1. **Ingest**: Add documents to the knowledge base ('library')
2. **Process**: Documents are chunked and embedded for semantic search
3. **Store**: Embeddings are stored in a local vector database
4. **Query**: Ask questions in natural language
5. **Retrieve**: `ragged` finds the most relevant document chunks
6. **Generate**: A local LLM generates an answer with citations (planned)


## Quick Start

### Prerequisites

- Python 3.12
- [Ollama](https://ollama.ai) installed and running (optional for v0.2 web UI)
- ChromaDB (via Docker or pip)

### Installation

```bash
# Clone the repository
git clone https://github.com/REPPL/ragged.git
cd ragged

# Create virtual environment
python3 -m venv .venv/ # or python, depending on your system
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Start services
docker compose up -d  # Starts ChromaDB (if using Docker)
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

`ragged` uses environment variables for configuration. Create a `.env` file:

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

---

## Troubleshooting

**ChromaDB Connection Issues:**

```bash
# Check ChromaDB is running
docker ps | grep chromadb

# Restart ChromaDB
docker-compose restart chromadb
```

**Ollama Issues:**

```bash
# Check Ollama is running
ollama list

# Pull required model
ollama pull llama3.2
ollama pull nomic-embed-text
```

---

## Tests

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

## Acknowledgments

Built with:

- [Ollama](https://ollama.ai) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [sentence-transformers](https://www.sbert.net/) - Embeddings
- [PyMuPDF4LLM](https://github.com/pymupdf/RAG) - PDF processing
- [Click](https://click.palletsprojects.com/) & [Rich](https://rich.readthedocs.io/) - CLI

