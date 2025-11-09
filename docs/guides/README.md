# Guides

**Task-oriented** - Practical solutions to specific problems.

---

## What Are Guides?

Guides are **task-oriented** how-tos that help you solve specific problems. They assume you have basic familiarity with ragged and want to accomplish a particular goal.

**Good for**:
- Users who know what they want to do
- Solving specific use cases
- Step-by-step instructions for common tasks

**Not good for**:
- Learning basics (see [tutorials](../tutorials/))
- Looking up parameters (see [reference](../reference/))
- Understanding architecture (see [explanation](../explanation/))

## Available Guides

### Development Environment

**[Docker Setup Guide](./docker-setup.md)**
How to set up the ragged development environment using Docker with native Ollama for optimal performance on Apple Silicon Macs.

- Prerequisites: Docker Desktop, Ollama
- Architecture: Hybrid (Native Ollama + Containerised Application)
- Topics: GPU acceleration, Metal framework, unified memory

---

### Planned Guides

**Installation & Setup**:
- [ ] Installing ragged on macOS/Linux/Windows
- [ ] Setting up Ollama for local LLMs
- [ ] Configuring GPU acceleration for OCR

**Document Management**:
- [ ] Processing academic papers (PDFs with citations)
- [ ] Importing web articles (Medium, news sites)
- [ ] Handling scanned documents (OCR)
- [ ] Managing document collections

**Customization**:
- [ ] Configuring chunking strategies
- [ ] Choosing embedding models
- [ ] Tuning retrieval parameters
- [ ] Setting up custom pipelines

**Integration**:
- [ ] Using ragged with Jupyter notebooks
- [ ] Building custom UIs with the API
- [ ] Exporting results and citations

**Troubleshooting**:
- [ ] Debugging OCR issues
- [ ] Improving retrieval quality
- [ ] Handling duplicate documents
- [ ] Performance optimization

## Guide Structure

Each guide includes:
1. **Goal** - What you'll accomplish
2. **Prerequisites** - What you need
3. **Steps** - Clear, numbered instructions
4. **Expected Outcome** - How to verify success
5. **Troubleshooting** - Common issues and solutions
6. **Next Steps** - Related guides

## Getting Help

- **Specific Questions**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Request a Guide**: [GitHub Issues](https://github.com/REPPL/ragged/issues)
- **Contribute a Guide**: See [contributing guide](../contributing/README.md)

---

**Status**: Guides will be created during/after v0.1 implementation.

**See Also**:
- [Tutorials](../tutorials/) - Learning-oriented lessons
- [Reference](../reference/) - API and configuration details
- [Explanation](../explanation/) - Why things work the way they do
