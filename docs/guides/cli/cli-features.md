# CLI Features Guide

Comprehensive tutorial for using ragged's command-line interface.

---

## Introduction

This guide covers all features of ragged's CLI, from basic document ingestion to advanced search and metadata management. Each section includes practical examples and best practices.

**Prerequisites:**
- ragged installed (`pip install -e .`)
- Ollama running locally (`ollama serve`)
- ChromaDB accessible (Docker or local)

**Getting Help:**
```bash
ragged --help              # Show all commands
ragged COMMAND --help      # Show help for specific command
```

---

## Quick Start

### First Steps

1. **Check service health:**
```bash
ragged health
```

**Expected output:**
```
Checking services...

✓ Ollama: Running
✓ ChromaDB: Running (0 chunks stored)

All services healthy!
```

2. **Add your first document:**
```bash
ragged add document.pdf
```

3. **Ask a question:**
```bash
ragged query "What is this document about?"
```

That's it! You've completed the basic ragged workflow.

---

## Adding Documents

### Single File Ingestion

Add individual documents with automatic format detection:

```bash
# Add a PDF
ragged add research-paper.pdf

# Add a text file
ragged add notes.txt

# Add a markdown file
ragged add README.md

# Add an HTML file (web page)
ragged add article.html
```

**What happens:**
1. Document loaded and parsed
2. Text extracted (with metadata for PDFs)
3. Document chunked (default 1000 tokens, 200 overlap)
4. Embeddings generated
5. Stored in vector database

**Progress indicators** show each step with status.

### Folder Ingestion

Add entire directories of documents at once:

```bash
# Add all documents in a folder (recursive)
ragged add /path/to/documents/

# Non-recursive (only top-level files)
ragged add /path/to/documents/ --no-recursive

# Limit depth
ragged add /path/to/documents/ --max-depth 2
```

**Folder ingestion features:**
- **Automatic format detection** - Supports PDF, TXT, MD, HTML
- **Recursive scanning** - Processes subdirectories by default
- **Duplicate detection** - Skips already-ingested documents
- **Batch processing** - Efficient embedding generation
- **Progress tracking** - Shows processing status
- **Error handling** - Continues on errors (unless `--fail-fast`)

**Example output:**
```
Scanning: /Users/me/Documents/research
Found 25 documents
Processing... ━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:15

Summary:
  ✓ Successful: 23
  ⊗ Duplicates: 1 (skipped)
  ✗ Failed: 1
  📊 Total chunks: 487
```

### Handling Duplicates

**Single file:**
ragged prompts for confirmation when a duplicate is detected:

```bash
ragged add document.pdf
```

**Output:**
```
⚠ Document already exists:
  Document ID: doc_abc123
  Existing path: /old/path/document.pdf
  Current path:  /new/path/document.pdf
  Chunks: 42

Document already exists. Overwrite? [y/N]:
```

**Folder ingestion:**
Duplicates are automatically skipped in batch mode (no prompts).

### Force Format Detection

Override automatic format detection:

```bash
# Force HTML parsing for a file with wrong extension
ragged add page.txt --format html

# Force plain text for a PDF (no formatting)
ragged add document.pdf --format txt
```

### Error Handling

**Continue on error** (default):
```bash
ragged add /large-folder/
# Processes all files, reports failures at end
```

**Fail fast:**
```bash
ragged add /large-folder/ --fail-fast
# Stops at first error
```

---

## Querying Documents

### Basic Queries

Ask questions and get answers from your documents:

```bash
ragged query "What are the main findings?"
```

**Output:**
```
Question: What are the main findings?

Generating answer...

Answer:
The main findings indicate that... [1] The research shows... [2]

References:
[1] research-paper.pdf (page 5, score: 0.873)
[2] notes.md (score: 0.791)
```

**Features:**
- **Hybrid retrieval** - Combines vector similarity + BM25 keyword matching
- **LLM generation** - Uses configured Ollama model
- **IEEE-style references** - Inline citations with source list
- **Automatic history** - Saves query for later replay

### Retrieving More Context

Adjust the number of chunks retrieved:

```bash
# Default: 5 chunks
ragged query "Explain the methodology"

# Retrieve more context
ragged query "Explain the methodology" --k 10

# Retrieve fewer chunks (faster)
ragged query "Quick summary" --k 3
```

**Guideline:**
- **k=3-5**: Short, focused answers
- **k=5-10**: Balanced (default: 5)
- **k=10-20**: Comprehensive analysis
- **k>20**: Entire document context (slow)

### Showing Source Chunks

See what context was used to generate the answer:

```bash
ragged query "What is RAG?" --show-sources
```

**Output:**
```
Retrieved sources:
  [1] rag-paper.pdf (score: 0.945)
      Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval...
  [2] notes.md (score: 0.823)
      RAG systems use vector databases to store document embeddings which are then...
  [3] article.html (score: 0.798)
      The key advantage of RAG is that it allows LLMs to access up-to-date information...

Answer:
Retrieval-Augmented Generation (RAG) is a technique... [1][2][3]
```

###  JSON Output

Get structured output for programmatic use:

```bash
ragged query "Topic" --format json
```

**Output:**
```json
{
  "query": "Topic",
  "answer": "The topic is...",
  "sources": [
    {
      "document": "document.pdf",
      "score": 0.873,
      "text": "...",
      "page": 5
    }
  ],
  "retrieval_method": "hybrid",
  "top_k": 5
}
```

**Use cases:**
- Piping to `jq` for extraction
- Integration with scripts
- API development
- Data analysis

**Examples:**
```bash
# Extract just the answer
ragged query "question" --format json | jq -r '.answer'

# Get source documents
ragged query "question" --format json | jq -r '.sources[].document'

# Save full result
ragged query "question" --format json > result.json
```

### Disabling History

Prevent a query from being saved to history:

```bash
ragged query "Quick test" --no-history
```

**When to use:**
- Testing queries
- Sensitive questions
- Temporary experiments
- Avoiding history clutter

---

## Configuration Management

### Viewing Configuration

See all current settings:

```bash
ragged config show
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting            ┃ Value                    ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Environment        │ development              │
│ Log Level          │ WARNING                  │
│ Data Directory     │ /Users/me/.ragged/data   │
│ Embedding Model    │ sentence-transformers    │
│ Embedding Model Na │ nomic-embed-text         │
│ LLM Model          │ llama3.2:latest          │
│ Chunk Size         │ 1000                     │
│ Chunk Overlap      │ 200                      │
│ ChromaDB URL       │ http://localhost:8000    │
│ Ollama URL         │ http://localhost:11434   │
└────────────────────┴──────────────────────────┘
```

### Changing the LLM Model

#### Interactive Selection

Choose from available models with suitability scores:

```bash
ragged config set-model
```

**Output:**
```
┏━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ # ┃ Model             ┃ Context ┃ Suitability     ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ 1 │ llama3.2:latest   │ 128k    │ ██████████ (95) │
│ 2 │ mistral:latest    │ 32k     │ ████████ (82)   │
│ 3 │ phi3:latest       │ 128k    │ ██████ (65)      │
└───┴───────────────────┴─────────┴─────────────────┘

Select model [1-3]: 1
✓ Model set to: llama3.2:latest
```

**Suitability score** (0-100) considers:
- Context window size
- RAG performance
- Response quality
- Speed/efficiency balance

#### Direct Model Selection

Set a specific model directly:

```bash
ragged config set-model llama3.2:latest
```

#### Automatic Selection

Let ragged choose the best available model:

```bash
ragged config set-model --auto
```

**Selection logic:**
1. Highest suitability score
2. Largest context window
3. Known RAG performance
4. Falls back to any available model

### Listing Available Models

See all Ollama models with RAG suitability:

```bash
ragged config list-models
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Model             ┃ Family  ┃ Context ┃ RAG Suitability ┃ Status   ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ llama3.2:latest   │ llama   │ 128k to │ ██████████ 95/1 │ ✓ Curren │
│ mistral:latest    │ mistral │ 32k tok │ ████████ 82/100 │          │
│ qwen2:latest      │ qwen    │ 32k tok │ ████████ 80/100 │          │
└───────────────────┴─────────┴─────────┴─────────────────┴──────────┘

Current model: llama3.2:latest

Change model with: ragged config set-model
```

---

## Advanced Search and Filtering

The `search` command provides powerful filtering beyond basic queries.

### Semantic Search

Search by meaning (vector similarity):

```bash
ragged search "machine learning concepts"
```

**Differences from `query`:**
- **search**: Returns matching chunks (no LLM generation)
- **query**: Generates answer from chunks (uses LLM)

**When to use search:**
- Finding specific information quickly
- Exploring what's in your database
- Filtering before querying
- Programmatic chunk retrieval

### Document Path Filtering

Search within specific documents:

```bash
# Single document
ragged search "neural networks" --path research-paper.pdf

# Wildcard matching
ragged search "topic" --path "*.pdf"
ragged search "topic" --path "research/*.md"
```

### Metadata Filtering

Filter by document metadata:

```bash
# Single filter
ragged search "AI" --metadata category=research

# Multiple filters (AND logic)
ragged search "deep learning" --metadata category=research --metadata priority=high
```

### Combined Filtering

Combine semantic search with filters:

```bash
ragged search "transformers" \
  --path "papers/*.pdf" \
  --metadata year=2023 \
  --metadata category=research \
  --min-score 0.7 \
  --limit 20
```

### Showing Content

Preview chunk content in results:

```bash
ragged search "machine learning" --show-content
```

**Output:**
```
Found 8 matches

[1] research-paper.pdf (page 3, score: 0.912)
    Machine learning is a subset of artificial intelligence that enables
    systems to learn and improve from experience...

[2] notes.md (score: 0.867)
    The main machine learning paradigms include supervised learning,
    unsupervised learning, and reinforcement learning...
```

### Listing Document Contents

List all chunks from a document without semantic search:

```bash
ragged search --path document.pdf --limit 100
```

### Exporting Search Results

Export results in various formats:

```bash
# JSON export
ragged search "topic" --format json > results.json

# CSV for spreadsheet analysis
ragged search "topic" --format csv > results.csv

# Markdown table
ragged search "topic" --format markdown > results.md
```

---

## Metadata Management

Metadata allows tagging and organising documents without re-ingestion.

### Listing Documents

See all ingested documents:

```bash
ragged metadata list
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ document           ┃ chunks ┃ pages ┃ file_hash    ┃ ingestion_date   ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ research-paper.pdf │ 42     │ 12    │ abc123...    │ 2024-01-15T10:30 │
│ notes.md           │ 15     │ N/A   │ def456...    │ 2024-01-15T11:00 │
│ article.html       │ 8      │ N/A   │ ghi789...    │ 2024-01-15T11:15 │
└────────────────────┴────────┴───────┴──────────────┴──────────────────┘
```

**Options:**
```bash
# Limit results
ragged metadata list --limit 50

# Export to JSON
ragged metadata list --format json > documents.json
```

### Viewing Document Metadata

See detailed metadata for a specific document:

```bash
ragged metadata show research-paper.pdf
```

**Output:**
```
Document: research-paper.pdf
Chunks: 42

Metadata:
  document_id: doc_abc123
  document_path: /Users/me/Documents/research-paper.pdf
  file_hash: abc123def456...
  ingestion_date: 2024-01-15T10:30:00
  total_pages: 12
  file_size: 2489632
  mime_type: application/pdf
```

**JSON output:**
```bash
ragged metadata show document.pdf --format json
```

### Updating Metadata

Add or modify metadata tags:

```bash
# Add a single tag
ragged metadata update research-paper.pdf --set category=research

# Add multiple tags
ragged metadata update research-paper.pdf \
  --set category=research \
  --set priority=high \
  --set tags=ml,ai,transformers
```

**Updates all chunks** of the document.

**Use cases:**
- Categorisation
- Priority marking
- Project association
- Author tracking
- Date tagging
- Custom fields

### Deleting Metadata

Remove metadata keys:

```bash
ragged metadata update document.pdf --delete old_key
```

### Searching by Metadata

Find documents matching metadata criteria:

```bash
# Single criterion
ragged metadata search --filter category=research

# Multiple criteria (AND logic)
ragged metadata search \
  --filter category=research \
  --filter priority=high
```

**Output format options:**
```bash
# Table view
ragged metadata search --filter category=research

# JSON export
ragged metadata search --filter category=research --format json
```

---

## Query History and Replay

ragged automatically saves query history for analysis and replay.

### Viewing History

List recent queries:

```bash
# Show all history
ragged history list

# Show last 10 queries
ragged history list --limit 10

# Search history
ragged history list --search "machine learning"
```

**Output:**
```
Query History (15 entries)

[1] 2024-01-15 10:30:00
  Query: What are the main findings?
  Top K: 5, Sources: 3
  Answer: The main findings indicate that...

[2] 2024-01-15 11:15:00
  Query: Explain the methodology
  Top K: 5, Sources: 4
  Answer: The methodology involves...
```

### Viewing Query Details

See full details of a specific query:

```bash
ragged history show 5
```

**Output:**
```
Query #5
Timestamp: 2024-01-15 14:23:00

Query: What is RAG?
Top K: 5

Answer:
Retrieval-Augmented Generation (RAG) is a technique that combines
information retrieval with large language models...

Sources (3):
  1. rag-paper.pdf (page 2, score: 0.945)
  2. notes.md (score: 0.823)
  3. article.html (score: 0.798)
```

**JSON format:**
```bash
ragged history show 5 --format json
```

### Replaying Queries

Re-run a previous query:

```bash
# Replay with original parameters
ragged history replay 5

# Replay with different k
ragged history replay 5 --top-k 10
```

**Use cases:**
- Testing with new documents
- Comparing answers over time
- Debugging retrieval
- Demonstrating capabilities

### Exporting History

Save history to JSON file:

```bash
ragged history export queries.json
```

**Use cases:**
- Backup
- Analysis
- Reporting
- Migration

### Clearing History

Remove all history entries:

```bash
# With confirmation
ragged history clear

# Skip confirmation
ragged history clear --yes
```

---

## Export and Import

Backup and migrate your ragged data.

### Creating Backups

Export all data to a JSON file:

```bash
# Auto-generated filename
ragged export backup
# Creates: ragged_backup_20240115_143000.json

# Custom filename
ragged export backup --output my-backup.json

# Compressed backup
ragged export backup --compress
# Creates: ragged_backup_20240115_143000.json.gz
```

**What's included:**
- All document chunks
- Document metadata
- Embeddings (optional)
- Configuration (optional)

**Options:**
```bash
# Without embeddings (smaller, faster)
ragged export backup --output backup.json --no-include-embeddings

# Without configuration
ragged export backup --output backup.json --no-include-config

# Minimal backup (documents and metadata only)
ragged export backup --output backup.json \
  --no-include-embeddings \
  --no-include-config
```

### Backup Best Practices

**Regular backups:**
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
ragged export backup --output "backup_$DATE.json" --compress
```

**Pre-migration backup:**
```bash
# Before major changes
ragged export backup --output pre-upgrade-backup.json --compress
```

**Selective backups:**
```bash
# Fast backup without embeddings
ragged export backup --output quick-backup.json --no-include-embeddings
```

---

## Cache Management

Manage temporary files and free disk space.

### Viewing Cache Information

See cache sizes and locations:

```bash
ragged cache info
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━┓
┃ Cache            ┃ Size     ┃ Path           ┃ Item ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━┩
│ Query History    │ 2.45 MB  │ ~/.ragged/data │ 1    │
│ Embeddings Cache │ 156.7 MB │ ~/.ragged/data │ 523  │
│ Query Cache      │ 8.91 MB  │ ~/.ragged/data │ 127  │
│ Temporary Files  │ 0 B      │ ~/.ragged/data │ 0    │
│ Logs             │ 1.23 MB  │ ~/.ragged/data │ 45   │
└──────────────────┴──────────┴────────────────┴──────┘

Total: 169.3 MB
```

### Clearing Caches

Free up disk space:

```bash
# Clear all caches (with confirmation)
ragged cache clear --all

# Clear specific caches
ragged cache clear --query-history
ragged cache clear --embeddings
ragged cache clear --logs

# Multiple caches
ragged cache clear --query-history --logs

# Skip confirmation
ragged cache clear --all --yes
```

**When to clear:**
- Low disk space
- After major updates
- Performance troubleshooting
- Privacy concerns
- Fresh start needed

---

## Document Management

### Listing Documents

See what's in your database:

```bash
# Table view
ragged list

# JSON export
ragged list --format json > documents.json

# CSV export
ragged list --format csv > documents.csv
```

**Current output:**
Shows collection-level information (total chunks). Document-level listing coming in v0.3.

### Clearing Database

Remove all documents:

```bash
# With confirmation
ragged clear

# Skip confirmation
ragged clear --force
```

**Warning:** This operation cannot be undone. Create a backup first:
```bash
ragged export backup --output pre-clear-backup.json
ragged clear --force
```

---

## Health Checks

### Checking Service Status

Verify all services are running:

```bash
ragged health
```

**Output (healthy):**
```
Checking services...

✓ Ollama: Running
✓ ChromaDB: Running (487 chunks stored)

All services healthy!
```

**Output (unhealthy):**
```
Checking services...

✗ Ollama: Connection refused at http://localhost:11434
✓ ChromaDB: Running (487 chunks stored)

Some services are not available.
```

**Exit codes:**
- `0`: All services healthy
- `1`: One or more services unavailable

**Troubleshooting:**

**Ollama not running:**
```bash
# Start Ollama
ollama serve
```

**ChromaDB not running:**
```bash
# Check Docker container
docker ps | grep chroma

# Start ChromaDB (if using Docker)
docker start chroma
```

---

## Configuration Validation

### Validating Environment

Check configuration and catch issues early:

```bash
ragged validate
```

**Checks performed:**
1. Configuration file syntax
2. Required settings present
3. Directory permissions
4. Ollama connectivity
5. ChromaDB connectivity
6. Embedding model availability

**Output (passing):**
```
Ragged Configuration Validation

1. Configuration File
  ✓ Configuration loaded successfully

2. Directories
  ✓ Data directory accessible
  ✓ Data directory writable

3. Ollama Service
  ✓ Ollama reachable
  ✓ Model available: llama3.2:latest

4. ChromaDB Service
  ✓ ChromaDB reachable
  ✓ Collection accessible

5. Embedding Model
  ✓ Embedding model loaded

✓ All checks passed
```

**Output (failing):**
```
Ragged Configuration Validation

1. Configuration File
  ✓ Configuration loaded successfully

2. Directories
  ✗ Data directory not writable

3. Ollama Service
  ✗ Ollama not reachable at http://localhost:11434

⚠ Issues found:
  ERROR (directories): Data directory not writable: Permission denied
  ERROR (ollama): Ollama service not reachable

2 errors, 0 warnings
```

### Auto-Fixing Issues

Attempt automatic fixes:

```bash
ragged validate --fix
```

**Auto-fixes:**
- Creates missing directories
- Sets correct permissions
- Initialises configuration files

**Note:** Cannot auto-fix service connectivity issues.

### Verbose Validation

See detailed diagnostic information:

```bash
ragged validate --verbose
```

**Use cases:**
- Troubleshooting setup issues
- Pre-deployment checks
- Environment verification
- Documentation for bug reports

---

## Environment Information

### Generating Environment Reports

Get detailed system information:

```bash
ragged env-info
```

**Output:**
```
============================================================
Ragged Environment Information
============================================================

Ragged Version: 0.2.8

Python:
  Version: 3.12.0
  Implementation: CPython
  Executable: /usr/local/bin/python3.12

System:
  OS: Darwin
  Platform: macOS-14.2-arm64-arm-64bit
  Machine: arm64
  Processor: arm

Key Packages:
  chromadb: 0.4.18
  click: 8.1.7
  ollama: 0.1.6
  pydantic: 2.5.2
  rich: 13.7.0
  sentence-transformers: 2.2.2

Configuration:
  embedding_model: sentence-transformers
  embedding_model_name: nomic-embed-text
  llm_model: llama3.2:latest
  chunk_size: 1000
  chunk_overlap: 200

Ollama:
  Status: running
  URL: http://localhost:11434
  Models: 3
    - llama3.2:latest
    - mistral:latest
    - phi3:latest

Storage:
  Data Directory: /Users/me/.ragged/data
  Space: 250.5GB free / 500GB total (50.1% used)

============================================================
```

### Output Formats

**Markdown (for GitHub issues):**
```bash
ragged env-info --format markdown > issue.md
```

**JSON (for programmatic use):**
```bash
ragged env-info --format json > env.json
```

### Copying to Clipboard

```bash
ragged env-info --copy
```

Requires `pyperclip`:
```bash
pip install pyperclip
```

---

## Shell Completion

### Installing Completion

Enable tab completion for ragged commands:

**Bash:**
```bash
ragged completion --shell bash --show >> ~/.bashrc
source ~/.bashrc
```

**Zsh:**
```bash
ragged completion --shell zsh --show >> ~/.zshrc
source ~/.zshrc
```

**Fish:**
```bash
ragged completion --shell fish --show > ~/.config/fish/completions/ragged.fish
```

**Auto-detection:**
```bash
# Detects your shell automatically
ragged completion --install
```

### Using Completion

After installation:
```bash
ragged <TAB>          # Shows all commands
ragged q<TAB>         # Completes to "query"
ragged config <TAB>   # Shows config subcommands
```

---

## Verbosity Control

Control output detail level globally:

### Quiet Mode

Minimal output (errors only):
```bash
ragged add document.pdf --quiet
ragged query "question" --quiet
```

**Use cases:**
- Scripts and automation
- Cron jobs
- CI/CD pipelines
- Log reduction

### Normal Mode

Standard output (default):
```bash
ragged add document.pdf
```

### Verbose Mode

Detailed progress information:
```bash
ragged add document.pdf --verbose
```

**Shows:**
- Detailed progress steps
- INFO-level log messages
- Performance metrics

### Debug Mode

Full diagnostic output:
```bash
ragged add document.pdf --debug
```

**Shows:**
- All log messages
- Internal function calls
- API requests/responses
- Performance timings

**Use cases:**
- Troubleshooting
- Bug reports
- Performance analysis
- Development

---

## Advanced Workflows

### Batch Document Processing

Process multiple documents efficiently:

```bash
#!/bin/bash
# batch-ingest.sh

DOCS_DIR="/path/to/documents"

# Method 1: Folder ingestion (recommended)
ragged add "$DOCS_DIR" --recursive

# Method 2: File-by-file with logging
for file in "$DOCS_DIR"/*.pdf; do
    echo "Processing: $file"
    ragged add "$file" 2>&1 | tee -a ingest.log
done
```

### Automated Question Answering

Script query workflows:

```bash
#!/bin/bash
# qa-batch.sh

QUESTIONS="questions.txt"
OUTPUT_DIR="answers"

mkdir -p "$OUTPUT_DIR"

while IFS= read -r question; do
    filename=$(echo "$question" | tr ' ' '_' | cut -c1-50).json
    echo "Q: $question"
    ragged query "$question" --format json > "$OUTPUT_DIR/$filename"
done < "$QUESTIONS"
```

### Metadata Tagging Workflow

Organise documents with metadata:

```bash
#!/bin/bash
# tag-research-papers.sh

# Tag all papers in research directory
for file in /path/to/research/*.pdf; do
    basename=$(basename "$file")
    ragged metadata update "$file" \
        --set category=research \
        --set project=phd \
        --set year=2024
done

# Verify tagging
ragged metadata search --filter category=research --format table
```

### Daily Backup Routine

Automated backup with rotation:

```bash
#!/bin/bash
# daily-backup.sh

BACKUP_DIR="/backups/ragged"
DATE=$(date +%Y%m%d)
KEEP_DAYS=7

# Create backup
ragged export backup --output "$BACKUP_DIR/backup_$DATE.json.gz" --compress

# Remove old backups
find "$BACKUP_DIR" -name "backup_*.json.gz" -mtime +$KEEP_DAYS -delete

echo "Backup completed: backup_$DATE.json.gz"
```

### Research Pipeline

End-to-end research workflow:

```bash
#!/bin/bash
# research-pipeline.sh

# 1. Ingest new papers
ragged add /incoming/papers/ --recursive --metadata project=survey

# 2. Tag and categorise
ragged metadata update --filter project=survey --set status=pending

# 3. Run research questions
ragged query "What are the key findings?" --format json > findings.json
ragged query "What methodologies are used?" --format json > methods.json
ragged query "What are the limitations?" --format json > limits.json

# 4. Generate report
cat findings.json methods.json limits.json | jq -s '.' > research-summary.json

# 5. Backup
ragged export backup --output research-backup.json
```

---

## Troubleshooting

### No Documents Found

**Symptom:**
```
No relevant documents found. Have you ingested any documents yet?
```

**Solutions:**
1. Check documents are ingested:
   ```bash
   ragged list
   ```

2. Verify ChromaDB is running:
   ```bash
   ragged health
   ```

3. Check data directory:
   ```bash
   ragged config show | grep "Data Directory"
   ```

### Ollama Connection Refused

**Symptom:**
```
✗ Ollama: Connection refused at http://localhost:11434
```

**Solutions:**
1. Start Ollama:
   ```bash
   ollama serve
   ```

2. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Check URL in configuration:
   ```bash
   ragged config show | grep "Ollama URL"
   ```

### ChromaDB Not Reachable

**Symptom:**
```
✗ ChromaDB: Connection refused
```

**Solutions:**
1. Start ChromaDB Docker container:
   ```bash
   docker start chroma
   ```

2. Check Docker status:
   ```bash
   docker ps | grep chroma
   ```

3. Verify URL:
   ```bash
   ragged config show | grep "ChromaDB URL"
   ```

### Duplicate Detection Issues

**Symptom:** Same document detected as duplicate with different path.

**Explanation:** ragged uses content-based hashing (file_hash), not paths.

**Solutions:**
1. Accept overwrite to update path
2. Or skip if truly a duplicate

### Slow Query Performance

**Symptoms:**
- Long wait times for answers
- Timeout errors

**Solutions:**
1. Reduce k parameter:
   ```bash
   ragged query "question" --k 3
   ```

2. Use faster model:
   ```bash
   ragged config set-model phi3:latest
   ```

3. Clear caches:
   ```bash
   ragged cache clear --all
   ```

4. Check system resources:
   ```bash
   ragged env-info
   ```

### Permission Denied Errors

**Symptom:**
```
ERROR: Permission denied: /Users/me/.ragged/data
```

**Solutions:**
1. Check permissions:
   ```bash
   ls -la ~/.ragged/
   ```

2. Fix permissions:
   ```bash
   chmod -R u+rw ~/.ragged/
   ```

3. Run validation with auto-fix:
   ```bash
   ragged validate --fix
   ```

---

## Best Practices

### Document Organisation

**Use metadata extensively:**
```bash
# Tag documents during ingestion
ragged add paper.pdf
ragged metadata update paper.pdf --set category=research --set year=2024

# Use consistent naming
ragged metadata update doc.pdf --set author="Smith,J" --set project="ProjectX"
```

**Folder structure:**
```
documents/
├── research/         # Research papers
├── notes/           # Personal notes
├── articles/        # Web articles
└── reference/       # Reference materials
```

### Query Optimisation

**Start broad, then narrow:**
```bash
# Broad search
ragged search "machine learning" --limit 20

# Narrow based on results
ragged query "machine learning transformers" --k 5
```

**Adjust k based on need:**
```bash
# Quick lookup (k=3)
ragged query "quick fact" --k 3

# Comprehensive analysis (k=15)
ragged query "detailed analysis" --k 15
```

### Regular Maintenance

**Weekly:**
```bash
# Check health
ragged health

# Review query history
ragged history list --limit 20
```

**Monthly:**
```bash
# Backup data
ragged export backup --compress

# Clear old caches
ragged cache clear --logs --yes

# Validate configuration
ragged validate
```

**Before major changes:**
```bash
# Full backup
ragged export backup --output pre-update-backup.json --compress

# Environment snapshot
ragged env-info --format json > pre-update-env.json
```

### Security and Privacy

**Never commit .env files:**
```bash
# .gitignore
.env
.env.local
```

**Backup encrypted backups:**
```bash
# Encrypt backup
ragged export backup --output backup.json
gpg --encrypt --recipient you@email.com backup.json
rm backup.json
```

**Clear sensitive queries:**
```bash
# Use --no-history for sensitive queries
ragged query "sensitive information" --no-history

# Or clear history after
ragged history clear --yes
```

---

## Related Documentation

- [CLI Command Reference](../../reference/cli/command-reference.md) - Complete technical specifications
- [Getting Started Tutorial](../../tutorials/getting-started.md) - First steps with ragged
- [Configuration Guide](../configuration.md) - Detailed configuration options
- [API Reference](../../reference/api/README.md) - Python API documentation

---

**Status:** Complete for v0.2.8
