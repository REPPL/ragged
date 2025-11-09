# ragged - Privacy-First Local RAG System

**Version:** 0.1.0 (In Development)
**Status:** Implementation Phase 2/14
**License:** GPL-3.0

A privacy-first document question-answering system that runs entirely locally using Retrieval-Augmented Generation (RAG) technology. No cloud, no tracking, no compromises.

---

## 🚧 Development Status

**ragged v0.1 is currently under development.** This README reflects the target state. See implementation status below.

### What's Complete ✅

- **Phase 1: Foundation** (100% Complete)
  - Type-safe configuration system (Pydantic)
  - Privacy-safe structured logging
  - Security utilities (path validation, file checks)
  - Document models with validation
  - Test infrastructure (44 tests passing, 96% coverage)

### What's In Progress 🔄

- **Phase 2: Document Ingestion** (Partial)
  - Models complete
  - Loaders needed (PDF, TXT, Markdown, HTML)

### What's Planned 📋

Comprehensive implementation skeletons exist for:
- Phase 3: Chunking System
- Phase 4: Dual Embedding Models (sentence-transformers + Ollama)
- Phase 5: Vector Storage (ChromaDB)
- Phase 6: Retrieval System
- Phase 7: LLM Generation (Ollama)
- Phase 8: CLI Interface
- Phases 9-14: Integration, Docker, Documentation, Security, Release

**See `SKELETON_SUMMARY.md` for complete status.**

---

## 🎯 Project Vision

ragged will be a local RAG system that:

- 📚 **Ingests documents** (PDF, TXT, Markdown, HTML)
- 🧠 **Understands questions** using local AI models
- 🔍 **Finds relevant information** via semantic search
- 💬 **Generates accurate answers** with citations
- 🔒 **Protects your privacy** (100% local, no cloud)
- ⚡ **Runs on your hardware** (Mac Studio M4 Max optimised)

---

## 🏗️ Architecture (Planned)

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
        │                 │
   ┌─────────────────────────┐
   │  Embedding Models       │
   │  - SentenceTransformers │
   │  - Ollama (nomic-embed) │
   └─────────────────────────┘
```

---

## 🚀 Quick Start (When Complete)

### Prerequisites

- Python 3.10+
- Docker Desktop (for ChromaDB)
- Ollama installed and running

### Installation

```bash
# Clone repository
git clone <repo-url>
cd ragged

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start services
docker-compose up -d

# Install Ollama models
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Basic Usage

```bash
# Add documents
ragged add documents/paper.pdf
ragged add documents/notes.md

# Ask questions
ragged query "What are the main findings?"

# List documents
ragged list

# Check health
ragged health
```

---

## 📖 Documentation

### For Developers

- **[SKELETON_SUMMARY.md](SKELETON_SUMMARY.md)** - Overview of all created files
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - How to implement remaining features
- **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)** - Phase-by-phase checklist
- **[PHASE2_COMPLETION.md](PHASE2_COMPLETION.md)** - Next steps guide
- **[docs/development/plans/v0.1-implementation-plan.md](docs/development/plans/v0.1-implementation-plan.md)** - Comprehensive 41-day plan

### For Users (Coming in Phase 11)

- Installation Guide
- Quick Start Tutorial
- CLI Reference
- Configuration Guide
- Troubleshooting

---

## 🔧 Development

### Running Tests

```bash
# All tests
pytest -v

# With coverage
pytest --cov=src

# Specific module
pytest tests/config/ -v

# Watch mode (requires pytest-watch)
ptw
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff src/ tests/

# Type check
mypy src/

# Run all checks
pre-commit run --all-files
```

### Project Structure

```
ragged/
├── src/                    # Source code
│   ├── config/            # ✅ Configuration system
│   ├── ingestion/         # 🔄 Document loading
│   ├── chunking/          # 📝 Text splitting
│   ├── embeddings/        # 📝 Vector embeddings
│   ├── storage/           # 📝 ChromaDB interface
│   ├── retrieval/         # 📝 Semantic search
│   ├── generation/        # 📝 LLM responses
│   ├── utils/             # ✅ Logging, security
│   └── main.py            # 📝 CLI interface
├── tests/                 # Test suite
├── docs/                  # Documentation
└── pyproject.toml         # ✅ Project config
```

**Legend:** ✅ Complete | 🔄 In Progress | 📝 Skeleton/Planned

---

## 🛠️ Technology Stack

### Core
- **Python 3.10+** - Modern Python with type hints
- **Pydantic** - Data validation and settings
- **Click** - CLI framework
- **Rich** - Terminal formatting

### RAG Pipeline
- **tiktoken** - Token counting
- **sentence-transformers** - Local embeddings
- **Ollama** - Local LLM inference
- **ChromaDB** - Vector database

### Document Processing
- **PyMuPDF4LLM** - PDF extraction
- **Trafilatura** - HTML content extraction
- **chardet** - Encoding detection

### Development
- **pytest** - Testing framework
- **black** - Code formatting
- **ruff** - Fast linting
- **mypy** - Type checking
- **pre-commit** - Git hooks

---

## 🔐 Privacy & Security

ragged is built with privacy as the top priority:

- ✅ **100% Local Processing** - No cloud APIs (unless explicitly configured)
- ✅ **No Telemetry** - Zero data collection or tracking
- ✅ **Input Validation** - Path traversal prevention, file size limits
- ✅ **Privacy-Safe Logging** - Automatic PII redaction
- ✅ **Open Source** - Fully auditable code (GPL-3.0)

**Security Features:**
- Path traversal prevention
- File size validation (default 100MB limit)
- MIME type verification
- Safe HTML parsing (XSS prevention)
- Filename sanitization
- Content length limits

---

## 📊 Current Test Coverage

```
Module                      Stmts   Coverage
─────────────────────────────────────────────
src/config/settings.py        60      92%
src/utils/logging.py          56     100%
src/utils/security.py         45     TBD
src/ingestion/models.py       61      97%
─────────────────────────────────────────────
TOTAL (completed modules)    222      96%
```

**Target for v0.1:** 60-70% overall, 90%+ core logic

---

## 🎯 Version 0.1 Goals

When v0.1 is complete, ragged will:

### Functionality
- ✅ Ingest PDF, TXT, Markdown, HTML files
- ✅ Chunk documents intelligently (500 token chunks, 100 overlap)
- ✅ Generate embeddings (choice of 2 models)
- ✅ Store in ChromaDB vector database
- ✅ Retrieve relevant chunks (top-k semantic search)
- ✅ Generate answers with citations (via Ollama)
- ✅ Provide CLI for all operations

### Quality
- ✅ 60-70% test coverage
- ✅ Query latency <5 seconds
- ✅ Retrieval relevance >70%
- ✅ Answer faithfulness >80%
- ✅ Security audit passed

### Future Versions
- **v0.2:** Hybrid retrieval, web UI, RAGAS evaluation
- **v0.3:** Personal memory, personas, semantic chunking
- **v0.4:** Self-RAG, adaptive retrieval
- **v0.5:** GraphRAG, Svelte UI
- **v1.0:** Production ready, PWA, plugins

---

## 🤝 Contributing

ragged is in active development. Once v0.1 is complete:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

**Development Guide:** See `docs/developer/contributing.md` (coming in Phase 11)

---

## 📝 License

GPL-3.0 - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

Built with:
- [Ollama](https://ollama.ai/) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [sentence-transformers](https://www.sbert.net/) - Embedding models
- [Anthropic Claude](https://claude.ai/) - Implementation assistant

---

## 📬 Contact

**Project Status:** Pre-release (v0.1 in development)
**Issues:** See GitHub Issues (when repository is public)
**Discussions:** See GitHub Discussions (when repository is public)

---

## 🗺️ Roadmap

- [x] **Phase 1:** Foundation (Complete)
- [ ] **Phase 2:** Document Ingestion (In Progress)
- [ ] **Phases 3-8:** Core RAG Pipeline
- [ ] **Phases 9-10:** Integration & Docker
- [ ] **Phase 11:** Documentation
- [ ] **Phases 12-14:** Security, Testing, Release
- [ ] **v0.1.0:** First Release! 🎉

**Track Progress:** See `IMPLEMENTATION_CHECKLIST.md`

---

**ragged** - Your documents, your privacy, your AI.
