# Frequently Asked Questions (FAQ)

Quick answers to common questions about ragged. For detailed information, follow the links to full guides.

---

## Getting Started

### What is ragged?

**Short answer**: RAG software that lets you ask questions about your personal documents using AI - completely locally and privately.

**Longer**: ragged (Retrieval-Augmented Generation) searches your documents, finds relevant information, and uses a local AI model to generate natural language answers. Everything runs on your computer - no cloud, no data sharing.

**Learn more**: [Understanding RAG](../explanation/rag-for-users.md)

---

### Is ragged free?

**Yes, completely free and open source** (GPL-3.0 licence).

No subscriptions, no usage limits, no hidden costs. You only need your own computer.

---

### Do I need to know how to code?

**No.** ragged has a command-line interface (CLI) but you don't need programming knowledge.

If you can open a terminal and type commands like `ragged add file.pdf`, you're ready to use ragged.

**New to terminals?** [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md) walks you through everything.

---

### How long does setup take?

**Typical time: 20-30 minutes** for first-time setup including:
- Installing Python 3.12 (5 min)
- Installing Ollama + downloading a model (10-15 min)
- Installing ragged (5 min)
- Adding your first document and testing (5 min)

**Follow**: [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md)

---

### What's the quickest way to try ragged?

**Three commands after setup**:
```bash
ragged add your-document.pdf    # Add a document
ragged query "your question?"   # Ask a question
ragged list                     # See what you've added
```

That's it. Start with one document and one question.

**Full walkthrough**: [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md)

---

## Privacy and Security

### Is my data really private?

**Yes, absolutely.** ragged is designed for complete privacy:
- ✅ All processing happens on your computer
- ✅ Documents never leave your device
- ✅ No internet connection needed after setup
- ✅ No telemetry or usage tracking
- ✅ No cloud services involved

**How we ensure privacy**: [Privacy Design Documentation](../explanation/privacy-design.md)

---

### What data is stored and where?

**Stored locally in `ragged_data/`**:
- Document chunks (text from your documents)
- Embeddings (mathematical representations)
- Metadata (tags, dates you added)
- Query history (optional, can be cleared)

**Not stored**:
- Your original documents (ragged reads them but doesn't copy them)
- Sensitive parts you don't add

**Location**: Everything in the `ragged_data` directory. Delete this folder and all traces are gone.

---

### Can ragged be used for sensitive documents?

**Yes**, that's a primary use case. Because everything is local:
- Medical records
- Legal documents
- Financial information
- Confidential business files
- Personal journals

**Recommendation**: Keep ragged's data directory (`ragged_data/`) on an encrypted drive for extra security.

---

### Does ragged send any data to external servers?

**No, never.**

The only internet usage is during initial setup (downloading Ollama models). After that, ragged works completely offline.

No analytics, no crash reports, no "anonymous telemetry" - nothing leaves your computer.

---

## System Requirements

### What operating systems does ragged support?

**Fully supported**:
- ✅ macOS (Intel and Apple Silicon)
- ✅ Linux (Ubuntu, Debian, Fedora, Arch, and derivatives)
- ✅ Windows 10/11

**Requirements**: Python 3.12 specifically (not 3.11 or 3.13).

---

### What are the minimum hardware requirements?

**Absolute minimum**:
- 8GB RAM (can run 1B-3B parameter models)
- 10GB free disk space
- Any modern CPU (past 5 years)

**Recommended**:
- 16GB RAM (can run 8B parameter models comfortably)
- 50GB free disk space (for models and document storage)
- SSD (faster than HDD)

**Optimal**:
- 32GB+ RAM (can run larger 70B models)
- 100GB+ free disk space
- Modern CPU with many cores

---

### Can I run ragged on a laptop?

**Yes!** Most modern laptops (2019+) work fine with smaller models.

**MacBook Air M1/M2**: Works excellently (8GB RAM sufficient for 3B models)
**Windows laptops**: 16GB RAM recommended
**Battery usage**: Queries use significant CPU, expect faster battery drain

**Tip**: Start with `llama3.2:3b` - it's small enough for most laptops but still gives good answers.

---

### Do I need a GPU?

**No, ragged works fine on CPU only.**

Ollama can use GPUs if available (NVIDIA, AMD, or Apple Silicon), but it's not required. CPU-only is a bit slower but perfectly usable.

**Performance difference**:
- With GPU: 5-10 seconds per query
- CPU only: 10-20 seconds per query

Still faster than reading documents manually!

---

### How much disk space do I need?

**Depends on your usage**:

**Just ragged**:
- ragged software: ~500MB
- Ollama: ~500MB
- One language model (3B): ~2-4GB
- **Total: ~4-5GB**

**With documents**:
- 100 PDFs (10 pages each): ~50MB of embeddings
- 1000 PDFs: ~500MB of embeddings
- **Add 50-100GB** if you plan to store many large documents

**Budget**: 10-20GB minimum, 50-100GB comfortable.

---

## Features and Capabilities

### What file formats does ragged support?

**Fully supported**:
- PDF (`.pdf`)
- Plain text (`.txt`)
- Markdown (`.md`)
- Microsoft Word (`.docx`)
- HTML (`.html`)

**Planned** (future versions):
- PowerPoint (`.pptx`)
- Excel (`.xlsx`)
- Images with OCR (`.jpg`, `.png`)

**Currently unsupported**:
- Encrypted PDFs (must unlock first)
- Scanned documents without OCR text layer

---

### Can ragged handle multiple languages?

**Mostly English-optimised** but can work with other languages:

**Good support**:
- English (best)
- Major European languages (Spanish, French, German, Italian)

**Limited support**:
- Other languages work but answer quality varies
- Embedding model (`nomic-embed-text`) is English-centric

**Future**: Multilingual models planned for v0.4+.

---

### How many documents can I add?

**No hard limit.** Tested with:
- ✅ 100 documents: Works excellently
- ✅ 1,000 documents: Works well
- ⚠️ 10,000+ documents: Works but search slows slightly

**Practical limit**: Depends on your disk space and patience during ingestion.

**Tip**: Start small (10-20 documents), add more as needed.

---

### Can I use ragged for real-time Q&A?

**Response time**: 5-20 seconds per query depending on model size and hardware.

**Not instant** like Google search, but reasonable for thoughtful questions where you want quality answers.

**Best for**: Research, analysis, summarisation.
**Not ideal for**: Time-critical lookups where sub-second response is needed.

---

### Can ragged cite sources?

**Yes**, ragged shows which documents and chunks were used:

```bash
Answer: [Generated answer text]

Sources:
- research-paper.pdf (chunks 3, 7)
- notes.txt (chunk 12)
```

**Future**: Exact page numbers and quotes (planned for v0.3).

---

## Comparison with Alternatives

### How is ragged different from ChatGPT?

| Feature | ragged | ChatGPT |
|---------|--------|---------|
| **Privacy** | 100% local | Cloud-based |
| **Custom documents** | Works with your files | Doesn't know your files |
| **Cost** | Free (hardware only) | Subscription for GPT-4 |
| **Internet required** | No (after setup) | Yes (always) |
| **Answer quality** | Good (depends on model) | Excellent (GPT-4) |
| **Response time** | 10-20 sec | 2-5 sec |

**Use ragged when**: Privacy matters, working with personal documents.
**Use ChatGPT when**: General knowledge questions, creative writing.

---

### How is ragged different from Google?

**Google**: Searches the entire web, returns links to pages.
**ragged**: Searches YOUR documents, returns generated answers.

**Google is better for**: Current events, broad topics, finding websites.
**ragged is better for**: Personal documents, private information, synthesised answers from your own knowledge base.

---

### How does ragged compare to Notion AI or Evernote AI?

| Feature | ragged | Notion AI | Evernote AI |
|---------|--------|-----------|-------------|
| **Local/cloud** | 100% local | Cloud | Cloud |
| **Cost** | Free | $10/month | Included in paid plans |
| **Privacy** | Complete | Limited | Limited |
| **File formats** | PDF, DOCX, TXT, MD, HTML | Notion pages only | Notes only |
| **Custom AI models** | Yes (switch models) | No | No |

**Use ragged when**: You want privacy, work with various file formats, need full control.
**Use Notion/Evernote AI when**: You already use those platforms and don't need strict privacy.

---

### Is ragged better than manual searching?

**ragged advantages**:
- Understands semantics (finds "vehicle" when you search "car")
- Searches across hundreds of documents instantly
- Synthesises information from multiple sources
- Saves time on repetitive questions

**Manual searching advantages**:
- 100% accurate (no AI hallucination risk)
- Can spot nuances AI might miss
- No setup required

**Best approach**: Use ragged for initial exploration, verify critical information manually.

---

## Usage and Workflow

### How do I organise many documents?

**Option 1: No organisation needed** (ragged finds relevant content automatically)

**Option 2: Use metadata** (tags):
```bash
ragged metadata update paper.pdf --set category=research --set year=2023
```

Then filter searches:
```bash
ragged metadata search --filter category=research --filter year=2023
```

**Option 3: Separate collections** (advanced, future feature).

**Recommendation**: Start without organisation, add metadata if you feel overwhelmed.

---

### Can I update documents after adding them?

**Currently**: Remove old version, add new version.
```bash
ragged clear old-document.pdf
ragged add updated-document.pdf
```

**Future**: Automatic update detection (v0.3 planned).

---

### What happens if I ask about something not in my documents?

ragged will say: **"No relevant information found in your documents"** or generate an answer with a disclaimer.

**Example**:
```bash
> ragged query "What is the capital of France?"
> No relevant information found in your documents.
```

**ragged only answers based on what you've added.** It doesn't use general knowledge from the model's training (by design).

---

### Can I use ragged collaboratively?

**Currently**: Single-user, local-only.

**Workaround for teams**:
1. One person maintains the document collection
2. Export queries and share results
3. Everyone runs own ragged instance (duplicates storage)

**Future**: Multi-user features planned for v1.0+.

---

### How do I back up my ragged data?

**Method 1: Copy the data directory**
```bash
cp -r ragged_data ragged_data_backup
```

**Method 2: Use ragged's export command**
```bash
ragged export backup --output backup.json.gz
```

**What's backed up**: All chunks, embeddings, metadata, configuration.

**Not backed up**: Original documents (ragged doesn't store them).

**Restore**: Copy the backup back to `ragged_data/` or use future import command (v0.2.9+).

---

## Troubleshooting

### Why are my answers poor quality?

**Common causes**:

1. **Model too small**
   - **Fix**: Try larger model (`ollama pull llama3.2:8b`)

2. **Relevant information not in documents**
   - **Fix**: Add more documents covering the topic

3. **Question too vague**
   - **Fix**: Be more specific ("What methodology?" not "What does it say?")

4. **Not enough chunks retrieved**
   - **Fix**: Increase K value (`--k 10` instead of default 5)

**Detailed guide**: [Troubleshooting FAQ](./troubleshooting/setup-issues.md)

---

### Why is ragged slow?

**Normal speeds**:
- Adding document: 5-60 sec depending on size
- Query response: 10-20 sec depending on model

**If slower than this**:

1. **Model too large for your hardware**
   - **Fix**: Use smaller model (3B instead of 70B)

2. **CPU-only (no GPU)**
   - **Expected**: 2-3x slower than GPU, but still usable

3. **Too many chunks retrieved**
   - **Fix**: Reduce K value (`--k 3`)

4. **Disk I/O bottleneck**
   - **Fix**: Move `ragged_data` to SSD if on HDD

---

### "Command not found: ragged"

**Cause**: Virtual environment not activated or ragged not installed.

**Fix**:
```bash
cd /path/to/ragged
source .venv/bin/activate  # Mac/Linux
# or
.venv\Scripts\activate  # Windows

pip install -e .
```

---

### "Ollama connection failed"

**Cause**: Ollama service not running.

**Fix**:
- **Mac**: Check menu bar for Ollama icon, launch Ollama app
- **Linux/Windows**: Run `ollama serve` in separate terminal

**Verify**: `ollama list` should show installed models.

---

### "ChromaDB connection failed"

**Docker users**:
```bash
docker compose ps         # Check if running
docker compose up -d      # Start if needed
```

**In-memory users**: Check `.env` has `CHROMA_IN_MEMORY=true`.

---

### How do I completely uninstall ragged?

**Remove ragged**:
```bash
cd ragged
pip uninstall ragged
```

**Remove data**:
```bash
rm -rf ragged_data/      # All your document data
rm -rf chroma_data/      # ChromaDB storage (Docker)
```

**Remove Ollama**: Uninstall Ollama app (optional, you might want to keep it).

**Result**: All traces removed. You can reinstall fresh anytime.

---

## Advanced Topics

### Can I customise the AI models?

**Yes**, switch models easily:

1. Download new model: `ollama pull mistral`
2. Update `.env`: `OLLAMA_MODEL=mistral`
3. Query: ragged uses new model automatically

**Available models**: See [Ollama library](https://ollama.com/library).

**Recommendation**: llama3.2 (3B or 8B) for most users.

---

### Can I run ragged on a server?

**Yes** (experimental). ragged includes optional web UI:
```bash
ragged ui
```

Access at `http://localhost:8080` in your browser.

**Caution**: Doesn't include authentication. Only use on trusted networks.

**Future**: Production-ready server deployment (v0.7+).

---

### How does ragged handle PDFs with images?

**Currently**: Extracts text only, ignores images.

**Images with text**: If PDF has OCR text layer, that text is extracted.

**Scanned PDFs**: Not supported yet. Run OCR first (e.g., Adobe Acrobat, Tesseract).

**Future**: Native OCR and image understanding (v0.5+).

---

### Can I programmatically use ragged (Python API)?

**Yes**, ragged is a Python package:

```python
from src.ingestion import add_document
from src.retrieval import query_documents

# Add document
add_document("paper.pdf")

# Query
results = query_documents("What is the methodology?")
```

**Documentation**: [API Reference](../reference/api/README.md) (v0.3+).

**Currently**: Best documentation is reading CLI source code in `src/cli/`.

---

## Getting Help

### Where can I get support?

**Documentation** (start here):
- [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md)
- [Understanding RAG](../explanation/rag-for-users.md)
- [CLI Essentials](./cli/essentials.md)

**Community**:
- [GitHub Discussions](https://github.com/REPPL/ragged/discussions) - Ask questions
- [GitHub Issues](https://github.com/REPPL/ragged/issues) - Report bugs

**Include in bug reports**: Output of `ragged env-info` (shows your system configuration).

---

### How can I contribute?

**Ways to contribute**:
- Report bugs: [GitHub Issues](https://github.com/REPPL/ragged/issues)
- Suggest features: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- Improve documentation: Pull requests welcome
- Write code: See [CONTRIBUTING.md](../../CONTRIBUTING.md)

**No coding needed**: Documentation improvements, bug reports, and feature ideas are valuable contributions.

---

### Is there a roadmap?

**Yes!** See [Version Roadmap](../development/roadmap/version/README.md).

**Upcoming highlights**:
- **v0.2.9**: Performance optimisation (4-30x faster embedding)
- **v0.3.0**: Citations with page numbers, configuration UI
- **v0.4.0**: Multilingual support, PDF improvements
- **v0.5.0**: Vision (images), OCR
- **v1.0**: Production-ready with API stability

---

## Still have questions?

**Can't find your answer here?**

1. Check the [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md)
2. Search [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
3. Ask a new question in Discussions
4. For bugs: [Open an issue](https://github.com/REPPL/ragged/issues)

We're here to help! 🚀

---

## Related Documentation

- [Troubleshooting Guide](./troubleshooting.md) - Common issues
- [Installation Tutorial](../tutorials/installation.md) - Setup instructions
- [RAG Fundamentals](../explanation/rag-fundamentals.md) - Understanding RAG

---
