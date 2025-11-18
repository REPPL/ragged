# CLI Essentials: Core Commands for Beginners

**What you'll learn**: The 5 essential commands to start using ragged effectively.

**Prerequisites**:
- ragged installed (see [Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md))
- Ollama running (`ollama serve`)
- ChromaDB running (Docker or in-memory mode)

**Reading time**: 10-15 minutes

---

## The Essential Five Commands

You can accomplish 90% of common tasks with just these 5 commands:

1. **`ragged health`** - Check if everything is working
2. **`ragged add`** - Add documents
3. **`ragged query`** - Ask questions
4. **`ragged list`** - See what you've added
5. **`ragged config`** - Manage settings

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
  - Collections: 1
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

## 2. ragged add - Add Documents

**Purpose**: Add documents to your knowledge base so you can query them.

### Basic usage

```bash
# Add a single file
ragged add document.pdf

# Add multiple files
ragged add paper1.pdf paper2.pdf notes.txt

# Add an entire folder
ragged add ./my-documents/
```

### What happens when you add a document

1. **Load**: ragged reads your file
2. **Parse**: Text is extracted (PDFs, DOCX, HTML, etc.)
3. **Chunk**: Document is split into smaller pieces (~1000 words each)
4. **Embed**: Each chunk is converted to a mathematical representation
5. **Store**: Embeddings and chunks are saved to ChromaDB

**Time**: 5-60 seconds depending on document size.

### Supported formats

- ✅ PDF (`.pdf`)
- ✅ Text (`.txt`)
- ✅ Markdown (`.md`)
- ✅ Microsoft Word (`.docx`)
- ✅ HTML (`.html`)

### Examples

**Add a research paper**:
```bash
ragged add research-paper.pdf
```

**Output**:
```
Processing research-paper.pdf...
✓ Loaded document (23 pages)
✓ Extracted 18,542 words
✓ Created 24 chunks
✓ Generated embeddings
✓ Stored in vector database

Successfully added: research-paper.pdf
Time: 38.2 seconds
```

---

**Add multiple documents**:
```bash
ragged add paper1.pdf paper2.pdf paper3.pdf
```

**Output**:
```
Processing 3 documents...

[1/3] paper1.pdf ━━━━━━━━━━━━━━━━━━━━━━━ 100% ✓ Complete
[2/3] paper2.pdf ━━━━━━━━━━━━━━━━━━━━━━━ 100% ✓ Complete
[3/3] paper3.pdf ━━━━━━━━━━━━━━━━━━━━━━━ 100% ✓ Complete

Successfully added 3 documents in 94.5 seconds
```

---

**Add a folder of documents**:
```bash
ragged add ./research-papers/
```

**Output**:
```
Scanning directory: ./research-papers/
Found 47 files (42 supported formats)

Processing documents...
[42/42] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Successfully added:
  - 35 PDFs
  - 5 text files
  - 2 Word documents

Total: 42 documents
Total chunks: 1,247
Time: 18.3 minutes
```

---

### Folder ingestion options

**Non-recursive** (only top-level files):
```bash
ragged add ./documents/ --no-recursive
```

**Limit depth**:
```bash
ragged add ./documents/ --max-depth 2
```

**Filter by file pattern**:
```bash
# Only PDFs
ragged add ./documents/ --pattern "*.pdf"

# Only markdown files
ragged add ./documents/ --pattern "*.md"
```

---

### Common issues when adding documents

**Problem**: "Unsupported file format"

**Solution**: ragged supports PDF, TXT, MD, DOCX, HTML. Convert other formats first.

---

**Problem**: "PDF is encrypted"

**Solution**: Unlock the PDF first using Adobe Acrobat or similar tool, then add it.

---

**Problem**: "Out of memory"

**Solution**: Your computer doesn't have enough RAM for the embedding model. Options:
1. Use a smaller embedding model
2. Add documents in smaller batches
3. Increase swap space (advanced)

---

**Problem**: "Document already exists"

**Current behaviour**: ragged skips documents with the same name.

**To update a document**:
```bash
ragged clear old-version.pdf
ragged add new-version.pdf
```

---

## 3. ragged query - Ask Questions

**Purpose**: Ask natural language questions and get AI-generated answers based on your documents.

### Basic usage

```bash
ragged query "What is the main conclusion of the paper?"
```

### What happens during a query

1. **Embed question**: Your question is converted to a vector
2. **Search**: ragged finds the 5 most relevant chunks
3. **Retrieve**: The actual text of those chunks is retrieved
4. **Generate**: Ollama reads the chunks and generates an answer
5. **Display**: Answer and sources are shown

**Time**: 5-20 seconds depending on model and hardware.

### Examples

**Simple question**:
```bash
ragged query "What is photosynthesis?"
```

**Output**:
```
Searching documents...
✓ Found 3 relevant chunks
✓ Generating answer...

Answer:
Photosynthesis is the process by which plants convert light energy into chemical energy. Plants use chlorophyll in their leaves to capture sunlight, which is then used to convert carbon dioxide and water into glucose and oxygen. This process is fundamental to life on Earth as it produces the oxygen we breathe and forms the base of most food chains.

Sources:
- biology-textbook.pdf (chunks 12, 15)
- plant-science.pdf (chunk 7)

Generation time: 8.3 seconds
```

---

**Complex question spanning multiple concepts**:
```bash
ragged query "How do neural networks differ from traditional machine learning algorithms?"
```

---

**Question with specific context**:
```bash
ragged query "What methodology did the researchers use in the 2023 study?"
```

---

### Query options

**Retrieve more chunks** (for complex questions):
```bash
ragged query "Complex question?" --k 10
```

Default is `--k 5`. Increase for questions that span multiple topics.

---

**Filter by document path**:
```bash
# Only search in research papers
ragged query "What methods were used?" --path "research/*.pdf"
```

---

**Filter by metadata** (if you've tagged documents):
```bash
ragged query "What are the findings?" --metadata category=research --metadata year=2023
```

---

**Set minimum relevance score**:
```bash
ragged query "What is quantum computing?" --min-score 0.7
```

Only uses chunks with similarity score ≥ 0.7 (range: 0.0-1.0).

---

**Different output formats**:
```bash
# JSON (for programmatic use)
ragged query "What is AI?" --format json

# Markdown (for documentation)
ragged query "What is AI?" --format markdown
```

---

### Interactive mode

Ask multiple questions in one session:

```bash
ragged query --interactive
```

**Usage**:
```
ragged interactive mode
Type 'exit' to quit, 'help' for commands

> What is machine learning?
[Answer shown]

> Can you explain that in simpler terms?
[Answer shown]

> What are some applications?
[Answer shown]

> exit
```

**Benefits**:
- Faster (model stays loaded)
- Conversational feel
- Easy to refine questions

---

### Streaming mode

See answers as they're generated (word by word):

```bash
ragged query "What is the solar system?" --stream
```

**Output**:
```
The solar system consists of the Sun and all objects that orbit it...
[Words appear in real-time as AI generates them]
```

**Why use streaming**: Provides immediate feedback that ragged is working, especially useful for slow models.

---

### Understanding query results

**Relevance scores**: Each source chunk has a score (0.0-1.0):
- 0.9-1.0: Extremely relevant
- 0.7-0.9: Highly relevant
- 0.5-0.7: Moderately relevant
- < 0.5: Weakly relevant

**Chunk numbers**: Show which parts of the document were used. Future versions will show page numbers.

**Multiple sources**: ragged synthesises information from all relevant chunks into a coherent answer.

---

### Tips for better query results

**1. Be specific**

❌ "What does it say?"
✅ "What methodology did the researchers use?"

❌ "Tell me about the paper"
✅ "What were the main findings of the 2023 climate study?"

---

**2. Ask focused questions**

Better to ask 3 focused questions than 1 broad question.

❌ "Explain everything about neural networks"
✅ Question 1: "What are neural networks?"
✅ Question 2: "How are neural networks trained?"
✅ Question 3: "What are common applications of neural networks?"

---

**3. Increase K for complex questions**

If your question requires information from multiple sections:
```bash
ragged query "Compare the methodologies used across all papers" --k 15
```

---

**4. Use metadata filters for large collections**

If you have 1000 documents but only want to search a subset:
```bash
ragged query "What are the findings?" --metadata category=neuroscience --metadata year=2023
```

---

**5. Rephrase if the answer is poor**

Try different wording:
- "What causes X?" vs "What are the causes of X?"
- "How does Y work?" vs "Explain the mechanism of Y"

---

### Common query issues

**Problem**: "No relevant information found"

**Causes**:
1. Information genuinely not in your documents (most common)
2. Question too vague
3. Terminology mismatch (you said "car", document says "automobile")

**Solutions**:
1. Add more documents covering the topic
2. Be more specific in your question
3. Try alternative phrasing

---

**Problem**: Answer is vague or generic

**Causes**:
1. Model too small (1B-3B parameters)
2. Not enough relevant chunks retrieved
3. Retrieved chunks don't contain the information

**Solutions**:
1. Use larger model: `ollama pull llama3.2:8b` and update `.env`
2. Increase K: `--k 10`
3. Verify information is in your documents

---

**Problem**: Answer contradicts itself

**Cause**: Retrieved chunks contain conflicting information from different documents.

**Solutions**:
1. Filter by metadata to search specific documents
2. Reduce K to fewer, more relevant chunks
3. Ask more specific questions

---

## 4. ragged list - View Documents

**Purpose**: See what documents you've added and their statistics.

### Basic usage

```bash
ragged list
```

### Example output

```
Documents in collection: 42

Recent documents:
┌─────────────────────────────────────┬────────┬──────────────┬─────────────────────┐
│ Document                            │ Chunks │ Size (KB)    │ Added               │
├─────────────────────────────────────┼────────┼──────────────┼─────────────────────┤
│ neural-networks-2023.pdf            │ 28     │ 342          │ 2025-11-18 09:24:15 │
│ machine-learning-intro.pdf          │ 15     │ 189          │ 2025-11-18 09:15:42 │
│ research-methodology.docx           │ 12     │ 76           │ 2025-11-17 14:33:07 │
│ meeting-notes-2025-11.md            │ 3      │ 18           │ 2025-11-16 16:45:23 │
│ ...                                 │        │              │                     │
└─────────────────────────────────────┴────────┴──────────────┴─────────────────────┘

Total chunks: 1,247
Total storage: 124.7 MB
```

---

### List options

**Show all documents** (not just recent):
```bash
ragged list --all
```

---

**Filter by pattern**:
```bash
# Only PDFs
ragged list --pattern "*.pdf"

# Only documents from 2023
ragged list --pattern "*2023*"
```

---

**Sort by different criteria**:
```bash
# By date (newest first)
ragged list --sort date

# By size (largest first)
ragged list --sort size

# By number of chunks
ragged list --sort chunks
```

---

**Different formats**:
```bash
# JSON (for scripts)
ragged list --format json

# CSV (for spreadsheets)
ragged list --format csv > documents.csv
```

---

### Understanding document statistics

**Chunks**: How many pieces the document was split into.
- Small docs (1-5 pages): 3-8 chunks
- Medium docs (10-20 pages): 15-30 chunks
- Large docs (100+ pages): 100+ chunks

**Size**: Disk space used by embeddings (not original document size).

**Added date**: When you ran `ragged add` on this document.

---

### Remove documents

Remove a specific document:

```bash
ragged clear document.pdf
```

**Output**:
```
Removing document: document.pdf
✓ Removed 24 chunks
✓ Freed 2.8 MB

Successfully removed: document.pdf
```

---

**Remove multiple documents**:
```bash
ragged clear paper1.pdf paper2.pdf notes.txt
```

---

**Remove all documents** (careful!):
```bash
ragged clear --all
```

**Warning**: This deletes your entire collection. You'll need to re-add all documents.

**Confirmation required**:
```
⚠ This will remove ALL 42 documents and 1,247 chunks.
Are you sure? [y/N]: y
```

---

### View detailed statistics

```bash
ragged list --stats
```

**Output**:
```
Collection Statistics:

Documents: 42
Chunks: 1,247
Average chunks per document: 29.7
Smallest document: meeting-notes.txt (2 chunks)
Largest document: thesis-final.pdf (127 chunks)

Storage:
  Embeddings: 124.7 MB
  Metadata: 2.1 MB
  Cache: 15.8 MB
  Total: 142.6 MB

Most recent addition: 2025-11-18 09:24:15
Oldest document: 2025-09-03 14:12:08
```

---

## 5. ragged config - Manage Configuration

**Purpose**: View and update ragged's settings interactively.

### View current configuration

```bash
ragged config show
```

**Output**:
```
ragged Configuration:

Ollama:
  Base URL: http://localhost:11434
  Model: llama3.2:3b
  Temperature: 0.1

Embeddings:
  Model: nomic-embed-text
  Dimensions: 768

Chunking:
  Chunk size: 1000 tokens
  Chunk overlap: 200 tokens

ChromaDB:
  Host: localhost
  Port: 8000
  Collection: ragged_documents

Storage:
  Data directory: ./ragged_data
  Cache enabled: true
```

---

### Interactive model selection

Change the AI model used for generation:

```bash
ragged config
```

**Interactive menu**:
```
Select an Ollama model:

Available models:
  1. llama3.2:1b (fastest, least RAM)
  2. llama3.2:3b (balanced) [current]
  3. llama3.2:8b (better quality)
  4. mistral:7b (alternative)

Enter number (1-4): 3

✓ Updated model to llama3.2:8b
✓ Configuration saved to .env
```

---

### Update specific settings

**Change chunk size**:
```bash
ragged config --set CHUNK_SIZE=1500
```

**Change embedding model**:
```bash
ragged config --set EMBEDDING_MODEL=sentence-transformers
```

**Change Ollama URL** (if running remotely):
```bash
ragged config --set OLLAMA_BASE_URL=http://192.168.1.100:11434
```

---

### Validate configuration

Check if your configuration is correct:

```bash
ragged config --validate
```

**Output (all good)**:
```
Validating configuration...

✓ .env file exists and readable
✓ All required variables set
✓ Ollama URL valid
✓ ChromaDB settings valid
✓ Data directory writable

Configuration is valid!
```

---

**Output (issues found)**:
```
Validating configuration...

✓ .env file exists
✗ OLLAMA_MODEL not set
✗ Data directory doesn't exist: /invalid/path

Issues found: 2
Run 'ragged config --fix' to auto-fix.
```

---

### Reset to defaults

```bash
ragged config --reset
```

**Warning**: This overwrites your `.env` file with defaults. Make a backup first if you have custom settings.

---

## Putting It All Together: A Complete Workflow

Here's a typical session using the essential commands:

### 1. Start your session

```bash
# Verify services are running
ragged health
```

### 2. Add documents

```bash
# Add some research papers
ragged add ./research-papers/
```

### 3. Check what was added

```bash
# See the documents
ragged list
```

### 4. Query your collection

```bash
# Ask questions
ragged query "What are the main themes in these papers?"

ragged query "What methodologies were commonly used?"

ragged query "What were the key findings about neural networks?"
```

### 5. Refine your collection

```bash
# Remove irrelevant documents
ragged clear outdated-paper.pdf

# Add more relevant documents
ragged add new-research.pdf
```

### 6. Adjust configuration if needed

```bash
# Switch to a larger model for better answers
ragged config
# Select llama3.2:8b
```

---

## Best Practices for Beginners

### 1. Start small

Add 5-10 documents first, not hundreds. Learn the workflow with a manageable collection.

---

### 2. Run health checks when troubleshooting

If anything doesn't work:
```bash
ragged health
```

This reveals 90% of common issues (Ollama not running, ChromaDB not connected).

---

### 3. Use descriptive file names

❌ `doc1.pdf`, `paper.pdf`, `notes.txt`
✅ `smith-2023-neural-networks.pdf`, `meeting-notes-2025-11-18.md`

Descriptive names make `ragged list` output more useful and help you identify sources.

---

### 4. Experiment with query phrasing

If you don't get good answers, try rephrasing your question differently. Small wording changes can significantly affect results.

---

### 5. Keep your documents organised (outside ragged)

ragged doesn't replace your file organisation. Keep originals organised in folders. ragged creates a searchable index, not a file manager.

---

## Related Documentation

- [Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md) - Installation and first-time setup
- [CLI Intermediate](./intermediate.md) - Metadata management and advanced search
- [CLI Advanced](./advanced.md) - Caching, backups, and power user features
- [Use Case Guides](../use-cases/) - Specific workflows for different purposes
- [Troubleshooting Guide](../troubleshooting/setup-issues.md) - Solutions to common problems
- [FAQ](../faq.md) - Quick answers to frequently asked questions
- [User Glossary](../../reference/terminology/user-glossary.md) - Plain English definitions

---

## Quick Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `ragged health` | Check services | `ragged health` |
| `ragged add` | Add documents | `ragged add file.pdf` |
| `ragged query` | Ask questions | `ragged query "What is X?"` |
| `ragged list` | View documents | `ragged list` |
| `ragged clear` | Remove documents | `ragged clear file.pdf` |
| `ragged config` | View/change settings | `ragged config show` |

---

**You're ready to use ragged!** These 5 commands cover the vast majority of everyday use cases. Practice with a small collection, then expand as you become comfortable.

Happy querying! 🚀
