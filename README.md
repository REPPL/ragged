# ragged

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Planning](https://img.shields.io/badge/status-planning-yellow.svg)]()

**Your private, intelligent document assistant that runs entirely on your computer**

---

## What is ragged?

**ragged** is a smart question-answering system for your personal documents. Think of it as having a knowledgeable assistant who has read all your PDFs, notes, and documents, and can answer questions about them—without ever sending your data to the cloud.

**Key benefits**:
- 🔒 **Complete Privacy**: Everything stays on your computer. No cloud services, no data sharing.
- 💬 **Natural Conversations**: Ask questions in plain language and get answers from your documents.
- 📚 **Smart Search**: Goes beyond keyword matching—understands context and meaning.
- 🎯 **Accurate Answers**: Shows you exactly where information comes from with citations.

### How it works

Upload your documents (PDFs, text files, web pages), ask questions, and ragged finds the most relevant information to answer you—all running locally on your machine.

![ragged Architecture](docs/assets/img/architecture-diagram.png)

---

## Current Status

**⚠️ Developer Beta - Planning Phase**

ragged is currently in active planning and early development. **There is no usable software yet**, but we're building something special:

- ✅ **Planning Complete**: Comprehensive architecture and roadmap finished
- 🔄 **Development Starting Soon**: Implementation of v0.1 (basic functionality) begins next
- 🎯 **Target**: First usable version (v0.1) in 2-3 weeks

If you're interested in following development, star ⭐ this repository to stay updated!

---

## What ragged will do

### Version 0.1 (Coming Soon - 2-3 weeks)
**Basic document chat**:
- Upload your documents (PDF, TXT, Markdown, HTML)
- Ask questions and get answers
- See sources and citations
- Simple command-line interface

### Version 0.2 (4-5 weeks)
**Better answers + Web interface**:
- More accurate search and retrieval
- Easy-to-use web interface (no command line needed)
- Upload documents through your browser
- Chat interface with streaming responses

### Version 0.3 (3-4 weeks)
**Smarter processing**:
- Better understanding of document structure
- Improved handling of tables and code
- Conversation history
- Document collection management

### Version 0.4 (4-5 weeks)
**Self-improving system**:
- Confidence scoring (ragged tells you when it's uncertain)
- Self-correction capabilities
- Developer mode for technical users
- Performance insights

### Version 0.5 (5-6 weeks)
**Knowledge graphs**:
- Understand relationships between concepts
- Multi-hop reasoning across documents
- Visual knowledge exploration
- Enhanced web interface

### Version 1.0 (4-6 weeks)
**Production ready**:
- Stable, polished interface
- Offline-capable web app
- Performance optimized
- Complete documentation
- **API stability guarantee** (no breaking changes after this)

---

## Technology

ragged is built on state-of-the-art 2025 research in RAG (Retrieval-Augmented Generation):

- **Local LLM**: Uses [Ollama](https://ollama.com/) for running AI models on your computer
- **Smart Search**: Combines multiple search techniques for best results
- **Privacy-First**: No external APIs, no cloud dependencies, no data sharing
- **Modern Web UI**: Simple for casual users, powerful for experts

**System Requirements** (planned):
- Python 3.10 or higher
- 8GB RAM minimum (16GB recommended)
- macOS, Linux, or Windows
- [Ollama](https://ollama.com/) installed

---

## Getting Started

### Right now (Planning Phase)

Since we're still building ragged, you can:

1. **Review the plans**: Check out our [comprehensive implementation plan](docs/implementation/plan/README.md)
2. **Read the architecture**: See the [state-of-the-art design](docs/implementation/plan/architecture/README.md)
3. **Follow development**: Star ⭐ this repo for updates
4. **Join discussions**: Ask questions or share ideas in [GitHub Discussions](https://github.com/REPPL/ragged/discussions)

### When v0.1 is ready (coming soon)

Installation will be as simple as:

```bash
# Clone and install (instructions will be updated when v0.1 is ready)
git clone https://github.com/REPPL/ragged.git
cd ragged
pip install -e .

# Start using ragged
ragged add documents/my-paper.pdf
ragged query "What are the main findings?"
```

**Documentation coming soon**:
- 📖 Setup Guide (v0.1)
- 📖 User Guide (v0.2+)
- 📖 Web Interface Tutorial (v0.2+)

---

## Why "ragged"?

**RAG** (Retrieval-Augmented Generation) is the technology that lets AI systems answer questions using your specific documents. We added **-ged** because:
- It's a friendly, memorable name
- Like "tagged" or "flagged"—your documents become intelligently organised
- It's easier to say than "RAG system" 😊

---

## Privacy & Security

**Your data never leaves your computer**:
- No cloud APIs (unless you explicitly choose to add them)
- No telemetry or tracking
- No data collection
- Open source—you can verify everything

This is especially important if you're working with:
- Personal notes and journals
- Research papers and academic work
- Business documents
- Medical or legal information
- Anything sensitive or private

---

## Project Principles

1. **Privacy First**: 100% local by default. External services only with explicit user consent.
2. **User-Friendly**: Simple for beginners, powerful for experts (progressive disclosure).
3. **Transparent**: Open source, well-documented, educational.
4. **Quality-Focused**: Built-in evaluation and testing from the start.
5. **Continuous Improvement**: Each version adds value while maintaining stability.

**Developer Beta Notice**: Before v1.0, we may make breaking changes to improve the product. After v1.0, we commit to stability and backward compatibility.

---

## Questions?

**As a potential user**:
- "When can I use it?" → v0.1 basic CLI in 2-3 weeks, v0.2 web interface in ~8 weeks
- "Will it work on my computer?" → If you can run Ollama, yes! (macOS, Linux, Windows)
- "Do I need technical skills?" → v0.1 requires command line, v0.2+ has web interface for everyone
- "Is my data safe?" → Yes! Everything runs locally on your computer

**Join the discussion**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)

**Report issues**: [GitHub Issues](https://github.com/REPPL/ragged/issues)

---

## Links for Developers and Contributors

### 📂 For Developers
Interested in the technical details, architecture, or implementation?
- **[Implementation Plan](docs/implementation/plan/README.md)** - Complete roadmap from v0.1 to v1.0
- **[Architecture 2025](docs/implementation/plan/architecture/README.md)** - State-of-the-art RAG architecture
- **[Technology Stack](docs/implementation/plan/technology-stack/)** - Framework and library decisions
- **[Core Concepts](docs/implementation/plan/core-concepts/)** - RAG fundamentals and design principles

### 🤝 For Contributors
Want to contribute to ragged?
- **Contributing Guide**: Coming after v0.1 is complete
- **[GitHub Discussions](https://github.com/REPPL/ragged/discussions)** - Share ideas and ask questions
- **[GitHub Issues](https://github.com/REPPL/ragged/issues)** - Report bugs or request features
- **Code of Conduct**: Be respectful, constructive, and kind

Currently, this is a personal learning project. Contributions will be welcomed after v0.1 implementation is complete.

### 🙏 Acknowledgements

**Research & Inspiration**:
- 2025 RAG research papers (GraphRAG, Self-RAG, Adaptive RAG)
- [LangChain](https://github.com/langchain-ai/langchain) - RAG patterns and component design
- [LlamaIndex](https://github.com/run-llama/llama_index) - Index structures and query engines
- [PrivateGPT](https://github.com/imartinez/privateGPT) - Privacy-first local processing approach
- [Ollama](https://ollama.com/) - Local LLM inference made simple

**AI Development Assistance**:
- **Claude Code** (Anthropic) - Architecture design and planning
- **Model**: claude-sonnet-4-5-20250929
- **Date**: 2025-11-08 to present

**Open Source Community**:
- Ollama project for making local LLMs accessible
- ChromaDB and Qdrant teams for vector storage solutions
- Sentence Transformers community for embedding models
- The entire open source RAG ecosystem

---

## License

This project is licensed under the **GNU General Public License v3.0**.

This means ragged is free and open source software. You can use it, modify it, and share it—as long as you keep it open source too. See the [LICENSE](LICENSE) file for full details.

---

## Star History

If you find ragged interesting, give us a star ⭐ to follow our progress!

---

**Built with privacy and learning in mind** 🔒📚

*Last updated: 2025-11-09 (Planning phase)*
