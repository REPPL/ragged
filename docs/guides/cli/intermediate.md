# CLI Intermediate Guide: Organisation and Power Features

**What you'll learn**: How to organise large document collections, use advanced search, and track your query history.

**Prerequisites**:
- Completed [CLI Essentials](./essentials.md)
- Comfortable with basic commands (add, query, list)
- Have at least 20-30 documents in your collection

**Reading time**: 15-20 minutes

---

## What Makes This "Intermediate"?

The essential commands get you started. These intermediate features help you:
- **Scale** to hundreds or thousands of documents
- **Organise** without manual folder management
- **Search** more precisely
- **Track** your research journey

You don't need all these features immediately, but they become valuable as your collection grows.

---

## Metadata Management: Tagging and Organisation

**Problem**: You have 200 research papers. Some are about neuroscience, some about machine learning, some about both. How do you search only the relevant subset?

**Solution**: Metadata - tags you add to documents for filtering.

### Understanding metadata

**Metadata** = information about your documents that isn't in the content.

**Examples**:
- `category=research`
- `year=2023`
- `author=Smith`
- `project=thesis`
- `priority=high`
- `status=read`

**Benefits**:
- Filter searches to specific subsets
- Organise without moving files
- Track document attributes
- Remember why you added documents

---

### Adding metadata to documents

**After adding a document**:
```bash
ragged add paper.pdf
ragged metadata update paper.pdf --set category=research --set year=2023
```

**Or during ingestion** (future feature - v0.3).

---

### View document metadata

```bash
ragged metadata show paper.pdf
```

**Output**:
```
Metadata for: paper.pdf

Document information:
  Path: /Users/you/papers/paper.pdf
  Added: 2025-11-18 09:24:15
  Chunks: 28
  Size: 342 KB

Custom metadata:
  category: research
  year: 2023
  author: Smith
  priority: high
```

---

### Search by metadata

**Find all research papers from 2023**:
```bash
ragged metadata search --filter category=research --filter year=2023
```

**Output**:
```
Found 12 documents matching filters:

┌─────────────────────────────────────┬────────────────────────────┐
│ Document                            │ Metadata                   │
├─────────────────────────────────────┼────────────────────────────┤
│ neural-networks-2023.pdf            │ category=research,         │
│                                     │ year=2023, author=Smith    │
│ machine-learning-survey-2023.pdf    │ category=research,         │
│                                     │ year=2023, author=Jones    │
│ ...                                 │                            │
└─────────────────────────────────────┴────────────────────────────┘
```

---

### List all metadata keys and values

```bash
ragged metadata list
```

**Output**:
```
Metadata summary across all documents:

category:
  - research (45 documents)
  - personal (12 documents)
  - work (8 documents)

year:
  - 2023 (32 documents)
  - 2022 (18 documents)
  - 2021 (15 documents)

author:
  - Smith (12 documents)
  - Jones (8 documents)
  - [15 other authors]

priority:
  - high (10 documents)
  - medium (25 documents)
  - low (30 documents)
```

**Use case**: See what metadata you've already used before adding more.

---

### Update metadata

**Add new metadata**:
```bash
ragged metadata update paper.pdf --set status=reviewed --set notes="Key findings on page 15"
```

**Change existing metadata**:
```bash
ragged metadata update paper.pdf --set priority=low
```

**Remove metadata**:
```bash
ragged metadata update paper.pdf --remove priority
```

---

### Query with metadata filters

**Only search documents tagged as "research" from 2023**:
```bash
ragged query "What are the key findings?" --metadata category=research --metadata year=2023
```

**Why useful**: Narrows search scope, improves relevance, speeds up queries.

---

### Metadata best practices

**1. Establish conventions early**

❌ Inconsistent: `Category=Research`, `category=research`, `cat=research`
✅ Consistent: `category=research` (always lowercase)

**2. Use common keys across documents**

Good keys to standardise:
- `category` - Type of document (research, personal, work)
- `year` - Publication/creation year
- `author` - Author or creator
- `project` - Which project this relates to
- `status` - read/unread, reviewed/pending
- `priority` - high/medium/low

**3. Keep values simple**

❌ `category=research paper about neural networks`
✅ `category=research`, `topic=neural-networks`

**4. Use metadata for attributes, not content**

❌ `summary=This paper discusses...` (put this in the document)
✅ `reviewed=yes`, `rating=5` (attributes about the document)

---

### Example: Organising a research library

**Initial state**: 150 unsorted PDFs.

**Step 1: Bulk categorisation**
```bash
# Research papers
ragged metadata update paper1.pdf --set category=research
ragged metadata update paper2.pdf --set category=research
# ... (or write a script)

# Personal notes
ragged metadata update notes*.md --set category=personal

# Work documents
ragged metadata update report*.pdf --set category=work
```

**Step 2: Add temporal metadata**
```bash
ragged metadata update *2023*.pdf --set year=2023
ragged metadata update *2022*.pdf --set year=2022
```

**Step 3: Tag by topic**
```bash
ragged metadata update *neural*.pdf --set topic=neural-networks
ragged metadata update *machine-learning*.pdf --set topic=ml
```

**Step 4: Query with precision**
```bash
# Only recent research papers on neural networks
ragged query "What are recent advances?" \
  --metadata category=research \
  --metadata year=2023 \
  --metadata topic=neural-networks
```

---

## Advanced Search: Beyond Basic Querying

**Problem**: Sometimes you want to find information without generating a full AI answer. Or you need more control over search parameters.

**Solution**: `ragged search` - semantic search without AI generation.

---

### Basic search usage

```bash
ragged search "machine learning"
```

**Output**:
```
Searching for: "machine learning"

Found 18 relevant chunks:

Score: 0.94 | Document: intro-to-ml.pdf
"Machine learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming. The core idea..."

Score: 0.89 | Document: neural-networks.pdf
"Traditional machine learning algorithms like decision trees and SVMs differ from deep learning approaches. Machine learning has evolved..."

Score: 0.87 | Document: practical-ml.pdf
"In practical machine learning applications, feature engineering plays a crucial role. Machine learning models require..."

[15 more results]
```

---

### Difference between `query` and `search`

| Feature | `ragged query` | `ragged search` |
|---------|----------------|-----------------|
| **Purpose** | Get AI-generated answer | Find relevant chunks |
| **Output** | Natural language answer | List of matching chunks |
| **Time** | 10-20 seconds | 1-3 seconds |
| **AI involved** | Yes (Ollama) | No (just similarity search) |
| **Use when** | Need synthesised answer | Quick lookup, exploration |

---

### When to use `search` instead of `query`

✅ **Use `search` when**:
- You want quick results without waiting for AI
- You're exploring what's in your documents
- You want to see exact text snippets
- You're checking if information exists

✅ **Use `query` when**:
- You want a synthesised, coherent answer
- You need information from multiple sources combined
- You want natural language explanation

---

### Search with filters

**Limit number of results**:
```bash
ragged search "quantum computing" --k 10
```

**Minimum relevance score**:
```bash
ragged search "quantum computing" --min-score 0.8
```

Only shows chunks with similarity ≥ 0.8 (very relevant).

---

**Filter by document path**:
```bash
# Only search PDFs in research folder
ragged search "methodology" --path "research/*.pdf"

# Only markdown files
ragged search "notes" --path "**/*.md"
```

---

**Filter by metadata**:
```bash
ragged search "findings" --metadata category=research --metadata year=2023
```

---

**Combine all filters**:
```bash
ragged search "neural networks" \
  --k 15 \
  --min-score 0.75 \
  --path "research/*.pdf" \
  --metadata category=research
```

---

### Search output formats

**Default (text)**:
```bash
ragged search "topic"
```

Shows human-readable results.

---

**JSON** (for scripts/automation):
```bash
ragged search "topic" --format json > results.json
```

**Output structure**:
```json
{
  "query": "topic",
  "results": [
    {
      "chunk_id": "abc123",
      "document": "paper.pdf",
      "score": 0.94,
      "text": "...",
      "metadata": {"category": "research"}
    }
  ]
}
```

---

**Markdown** (for documentation):
```bash
ragged search "topic" --format markdown > results.md
```

---

**CSV** (for spreadsheets):
```bash
ragged search "topic" --format csv > results.csv
```

Open in Excel/Google Sheets for analysis.

---

### Search best practices

**1. Use search for exploration**

Before formulating a complex query, do a quick search to see what's available:
```bash
ragged search "neural networks"
# See what chunks exist
# Then formulate specific query based on results
```

---

**2. Adjust score thresholds based on query type**

- **Specific terms**: Use high threshold (--min-score 0.8)
  ```bash
  ragged search "GPT-4" --min-score 0.8
  ```

- **Broad concepts**: Use lower threshold (--min-score 0.6)
  ```bash
  ragged search "artificial intelligence" --min-score 0.6
  ```

---

**3. Use path filters for focused searches**

If you know the information is in a specific set of documents:
```bash
ragged search "conclusion" --path "papers/neuroscience/*.pdf"
```

Faster and more accurate than searching everything.

---

## Query History: Track Your Research Journey

**Problem**: You asked a great question yesterday but can't remember exactly how you phrased it. Or you want to replay a query after adding new documents.

**Solution**: Query history tracking.

---

### View query history

```bash
ragged history list
```

**Output**:
```
Query History (last 10):

┌────┬─────────────────────────────────────┬───────────────┬─────────────────────┐
│ ID │ Query                               │ Documents     │ Date                │
├────┼─────────────────────────────────────┼───────────────┼─────────────────────┤
│ 10 │ What are the key findings?          │ 5 sources     │ 2025-11-18 14:32:18 │
│ 9  │ What methodology was used?          │ 3 sources     │ 2025-11-18 13:15:42 │
│ 8  │ How do neural networks work?        │ 8 sources     │ 2025-11-18 11:47:03 │
│ 7  │ What is deep learning?              │ 4 sources     │ 2025-11-17 16:22:15 │
│ 6  │ Compare CNNs and RNNs               │ 6 sources     │ 2025-11-17 15:10:33 │
│ ...│                                     │               │                     │
└────┴─────────────────────────────────────┴───────────────┴─────────────────────┘
```

---

### Show full query details

```bash
ragged history show 10
```

**Output**:
```
Query #10: What are the key findings?
Date: 2025-11-18 14:32:18
Model: llama3.2:3b
Parameters: k=5, min_score=0.5

Answer:
The key findings indicate three main themes: 1) Neural networks outperformed traditional algorithms by 23% on average...

Sources:
- research-2023.pdf (chunks 12, 15)
- findings-summary.pdf (chunks 3, 8, 9)

Generation time: 12.4 seconds
```

---

### Replay a query

**Use case**: You've added new documents since running a query. Re-run it to see if the answer changes.

```bash
ragged history replay 10
```

**Output**:
```
Replaying query #10: "What are the key findings?"

Searching with current document collection...
✓ Found 7 relevant chunks (was 5 last time)
✓ Generating answer...

Answer:
[New answer incorporating recently added documents]

Note: 2 new sources found since original query
```

---

### Search query history

Find past queries about a specific topic:

```bash
ragged history list --search "neural networks"
```

**Output**:
```
Found 5 queries matching "neural networks":

┌────┬─────────────────────────────────────┬─────────────────────┐
│ ID │ Query                               │ Date                │
├────┼─────────────────────────────────────┼─────────────────────┤
│ 15 │ How do neural networks learn?       │ 2025-11-18 16:45:12 │
│ 8  │ How do neural networks work?        │ 2025-11-18 11:47:03 │
│ 3  │ Compare neural nets and SVMs        │ 2025-11-15 10:22:08 │
│ ...│                                     │                     │
└────┴─────────────────────────────────────┴─────────────────────┘
```

---

### Export query history

**JSON export** (for analysis):
```bash
ragged history export --format json > query-history.json
```

**CSV export** (for spreadsheets):
```bash
ragged history export --format csv > query-history.csv
```

**Use cases**:
- Track research questions over time
- Analyse query patterns
- Share research process with team
- Include in research methodology documentation

---

### Clear query history

**Clear old queries** (keep last N):
```bash
ragged history clear --keep 50
```

Keeps the 50 most recent queries, deletes older ones.

---

**Clear all history**:
```bash
ragged history clear --all
```

**Warning**: This is permanent. Export first if you want a backup.

---

### Query history best practices

**1. Use history for iterative research**

Common pattern:
1. Ask broad question: "What is machine learning?"
2. See what sources are used
3. Ask follow-up based on sources: "Explain supervised learning in more detail"
4. Repeat

Use `ragged history list` to see your progression.

---

**2. Replay queries after major additions**

After adding significant new documents:
```bash
# Check which past queries might have better answers now
ragged history list
ragged history replay 5
ragged history replay 8
ragged history replay 12
```

---

**3. Export history for research documentation**

For academic work, export your query history to demonstrate systematic literature review:
```bash
ragged history export --format csv > research-queries-2025-11.csv
```

Include in methodology appendix.

---

## Verbosity Control: Adjust Output Detail

**Problem**: Sometimes you want detailed logs. Sometimes you want minimal output.

**Solution**: Global verbosity flags.

---

### Quiet mode (errors only)

```bash
ragged add document.pdf --quiet
```

**Output** (only if error):
```
Error: File not found: document.pdf
```

No output on success.

**Use case**: Scripting, automation, cron jobs.

---

### Normal mode (default)

```bash
ragged add document.pdf
```

**Output**:
```
Processing document.pdf...
✓ Created 24 chunks
Successfully added: document.pdf
```

Concise success messages.

---

### Verbose mode (detailed info)

```bash
ragged add document.pdf --verbose
```

**Output**:
```
[INFO] Processing document.pdf
[INFO] Document type detected: PDF
[INFO] Extracting text from 23 pages
[INFO] Extracted 18,542 words
[INFO] Creating chunks (size=1000, overlap=200)
[INFO] Created 24 chunks
[INFO] Generating embeddings using nomic-embed-text
[INFO] Generated 24 embeddings
[INFO] Storing in ChromaDB collection 'ragged_documents'
[INFO] Successfully added: document.pdf
[INFO] Time elapsed: 38.2 seconds
```

Shows every step.

**Use case**: Understanding what ragged is doing, troubleshooting performance.

---

### Debug mode (maximum detail)

```bash
ragged query "question" --debug
```

**Output**:
```
[DEBUG] Loading configuration from .env
[DEBUG] Ollama URL: http://localhost:11434
[DEBUG] Model: llama3.2:3b
[DEBUG] Converting query to embedding
[DEBUG] Embedding model: nomic-embed-text
[DEBUG] Embedding dimensions: 768
[DEBUG] Searching ChromaDB for k=5 chunks
[DEBUG] Found 5 chunks with scores: [0.94, 0.89, 0.87, 0.85, 0.82]
[DEBUG] Retrieving chunk texts from database
[DEBUG] Building prompt with 5 chunks (total tokens: 1,247)
[DEBUG] Sending to Ollama for generation
[DEBUG] Temperature: 0.1, max_tokens: 2000
[DEBUG] Generation complete in 12.4 seconds
[DEBUG] Answer length: 342 words
```

Full internals exposed.

**Use case**: Debugging issues, understanding performance bottlenecks, development.

---

### Verbosity in scripts

For automation, use `--quiet` and check exit codes:

```bash
#!/bin/bash
ragged add document.pdf --quiet
if [ $? -eq 0 ]; then
  echo "Success"
else
  echo "Failed"
fi
```

---

## Practical Workflows

### Workflow 1: Organising a Large Research Collection

**Scenario**: You have 200 PDFs to add and want them organised.

```bash
# Step 1: Add all documents
ragged add ./research-papers/

# Step 2: Tag by year (using filename pattern)
for file in ./research-papers/*2023*.pdf; do
  ragged metadata update "$file" --set year=2023
done

for file in ./research-papers/*2022*.pdf; do
  ragged metadata update "$file" --set year=2022
done

# Step 3: Tag by category
ragged metadata update *neural*.pdf --set topic=neural-networks
ragged metadata update *nlp*.pdf --set topic=nlp
ragged metadata update *vision*.pdf --set topic=computer-vision

# Step 4: Query with filters
ragged query "What are recent advances?" \
  --metadata year=2023 \
  --metadata topic=neural-networks
```

---

### Workflow 2: Exploratory Research

**Scenario**: Exploring a new topic, not sure what questions to ask yet.

```bash
# Step 1: Add documents
ragged add quantum-computing/*.pdf

# Step 2: Use search to explore what's there
ragged search "quantum" --k 20

# Step 3: See key topics that appear
ragged search "qubit"
ragged search "superposition"
ragged search "entanglement"

# Step 4: Formulate specific queries based on exploration
ragged query "How does quantum entanglement work?"
ragged query "What are the challenges in building quantum computers?"

# Step 5: Review query history to see research progression
ragged history list
```

---

### Workflow 3: Comparative Analysis

**Scenario**: Comparing approaches across multiple papers.

```bash
# Step 1: Tag papers by methodology
ragged metadata update paper1.pdf --set method=supervised
ragged metadata update paper2.pdf --set method=unsupervised
ragged metadata update paper3.pdf --set method=reinforcement

# Step 2: Query each methodology separately
ragged query "What are the results?" --metadata method=supervised > supervised-results.txt
ragged query "What are the results?" --metadata method=unsupervised > unsupervised-results.txt
ragged query "What are the results?" --metadata method=reinforcement > reinforcement-results.txt

# Step 3: Compare outputs manually or use diff tools
diff supervised-results.txt unsupervised-results.txt
```

---

## Related Documentation

- [CLI Essentials](./essentials.md) - Core commands and basic usage
- [CLI Advanced](./advanced.md) - Caching, backups, and validation
- [Personal Notes Guide](../use-cases/personal-notes.md) - Organising personal knowledge
- [Research Papers Guide](../use-cases/research-papers.md) - Academic literature management
- [Understanding RAG](../../explanation/rag-for-users.md) - Conceptual overview
- [FAQ](../faq.md) - Common questions answered
- [Troubleshooting Guide](../troubleshooting/setup-issues.md) - Problem solutions

---

## Quick Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `ragged metadata update` | Add tags | `ragged metadata update file.pdf --set category=research` |
| `ragged metadata show` | View tags | `ragged metadata show file.pdf` |
| `ragged metadata search` | Find by tags | `ragged metadata search --filter year=2023` |
| `ragged search` | Find chunks | `ragged search "topic" --k 10` |
| `ragged history list` | View past queries | `ragged history list --search "neural"` |
| `ragged history replay` | Re-run query | `ragged history replay 5` |

---

**You're now an intermediate ragged user!** These features help you scale to large collections and conduct systematic research. Practice with your own documents to see which features fit your workflow.

Happy organising! 📚
