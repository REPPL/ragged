# User Glossary: RAG and ragged Terms in Plain English

**Purpose**: Quick reference for technical terms you'll encounter while using ragged.

**How to use**: Look up any unfamiliar term. Each entry includes a plain English definition and practical example.

---

## Core RAG Concepts

### RAG (Retrieval-Augmented Generation)
**Plain English**: A method where an AI searches your documents for relevant information, then uses that information to generate answers.

**Example**: Instead of asking ChatGPT (which doesn't know your documents), RAG searches your personal files and generates answers based on what it finds.

**Why it matters**: The foundation of how ragged works.

---

### Retrieval
**Plain English**: The process of finding relevant information from your documents.

**Example**: When you ask "What is photosynthesis?", retrieval finds sections in your biology notes that discuss photosynthesis.

**How ragged does it**: Uses vector similarity search to find semantically related content.

---

### Generation
**Plain English**: Creating a natural language answer using an AI model.

**Example**: After retrieval finds relevant chunks, an AI model (like Llama) reads them and writes a coherent answer in complete sentences.

**What does the generating**: Ollama (running a large language model).

---

### Augmented
**Plain English**: Enhanced or improved with additional information.

**Example**: The AI is "augmented" with your specific documents. It doesn't just rely on its training - it uses your actual files.

**Why this is powerful**: The AI can answer questions about content it was never trained on.

---

## Documents and Processing

### Chunk / Chunking
**Plain English**: Breaking a large document into smaller pieces (typically 500-1000 words each).

**Example**: A 50-page PDF is split into ~50-100 chunks. Each chunk is processed and stored separately.

**Why it's needed**: AI models have limits on how much text they can read at once. Chunking makes documents fit within these limits.

**What you control**: Chunk size in configuration (`CHUNK_SIZE` setting).

---

### Chunk Overlap
**Plain English**: How much text is repeated between consecutive chunks.

**Example**: If chunk 1 ends with "...the results showed improvement" and chunk 2 starts with "the results showed improvement in both...", that's overlap.

**Why it's useful**: Prevents important information from being split awkwardly across chunk boundaries.

**Typical setting**: 50-200 words of overlap.

---

### Document Processing
**Plain English**: The one-time setup when you add a document: extracting text → chunking → embedding → storing.

**Example**: Running `ragged add paper.pdf` processes the PDF so it's searchable.

**Time required**: 5-60 seconds per document depending on size.

---

### Ingestion
**Plain English**: Another word for adding documents to ragged's database.

**Example**: "Ingesting 100 PDFs" means adding 100 PDFs to ragged.

**Command**: `ragged add document.pdf`

---

## Embeddings and Vectors

### Embedding
**Plain English**: Converting text into a list of numbers (a vector) that represents its meaning.

**Example**:
- "The cat sat on the mat" → [0.23, -0.54, 0.81, ..., 0.42] (384 numbers)
- "The dog lay on the rug" → [0.25, -0.52, 0.79, ..., 0.40] (similar numbers because similar meaning)

**Why it's needed**: Numbers can be compared mathematically. Similar meanings have similar numbers.

**What creates embeddings**: An embedding model (like `nomic-embed-text`).

---

### Embedding Model
**Plain English**: A specialised AI model that converts text into vectors (embeddings).

**Example**: `nomic-embed-text` (ragged's default) or `sentence-transformers`.

**Difference from LLM**: Embedding models don't generate text - they just convert text to numbers for searching.

**How to change**: Set `EMBEDDING_MODEL` in your `.env` file.

---

### Vector
**Plain English**: A list of numbers representing meaning. Same as an embedding.

**Example**: [0.23, -0.54, 0.81, ..., 0.42] (typically 384 or 768 numbers).

**Why called "vector"**: Mathematical term for a list of numbers with direction and magnitude.

**What you need to know**: Ragged handles all vector operations automatically. You don't need to understand the maths.

---

### Vector Similarity
**Plain English**: How close two vectors (meanings) are to each other mathematically.

**Example**:
- "automobile" and "car" have high similarity (0.95)
- "automobile" and "banana" have low similarity (0.15)

**How ragged uses it**: Finds chunks with highest similarity to your question.

**The maths**: Usually cosine similarity (don't worry about this).

---

### Vector Database
**Plain English**: A specialised database for storing and searching vectors efficiently.

**Example**: ChromaDB stores all your document embeddings and quickly finds similar ones when you query.

**Difference from normal database**: Traditional databases find exact matches. Vector databases find similar meanings.

**ragged uses**: ChromaDB.

---

## Search and Retrieval

### Semantic Search
**Plain English**: Searching by meaning rather than exact keywords.

**Example**:
- **Query**: "How do plants make food?"
- **Finds**: Chunks about photosynthesis, even if they don't contain the words "plants", "make", or "food"

**Contrast with keyword search**: Keyword search only finds exact word matches.

**Why better**: Understands synonyms, related concepts, different phrasings.

---

### Keyword Search / BM25
**Plain English**: Traditional search that finds exact word matches (like Ctrl+F).

**Example**: Searching "machine learning" finds only text containing those exact words.

**Used in ragged**: Combined with semantic search for "hybrid retrieval".

**When it's better**: Very specific terms (model numbers, names, dates).

---

### Hybrid Retrieval
**Plain English**: Combining semantic search (meaning) and keyword search (exact words).

**Example**: Looking for "GPT-4 performance" uses:
- Semantic: finds concepts about model performance
- Keyword: ensures "GPT-4" appears (not GPT-3 or other models)

**Benefit**: Gets the best of both approaches.

**ragged's approach**: Automatically uses hybrid retrieval when appropriate.

---

### Top-K Retrieval
**Plain English**: How many chunks to retrieve for each query.

**Example**: `--k 5` means "retrieve the 5 most relevant chunks".

**Default in ragged**: k=5

**When to adjust**:
- Complex questions: increase K (--k 10)
- Simple questions: decrease K (--k 3)

**Trade-off**: More chunks = more context but slower generation and higher cost.

---

### Relevance Score
**Plain English**: A number (0.0 to 1.0) indicating how well a chunk matches your query.

**Example**:
- 0.95 = extremely relevant
- 0.70 = moderately relevant
- 0.40 = weakly relevant

**How ragged uses it**: Can filter out chunks below a threshold (`--min-score 0.7`).

---

## AI and Generation

### LLM (Large Language Model)
**Plain English**: An AI model trained to understand and generate human language.

**Examples**: Llama, GPT, Claude, Mistral.

**What it does in RAG**: Reads retrieved chunks and generates natural language answers.

**ragged uses**: Ollama to run LLMs locally.

---

### Ollama
**Plain English**: Software that runs large language models (LLMs) on your local computer.

**What it does**:
- Downloads AI models
- Runs them locally (no internet needed after download)
- Provides an interface for ragged to use

**Models available**: Llama, Mistral, Phi, and many others.

**Why needed**: ragged needs an LLM for answer generation. Ollama provides this locally.

---

### Model Parameters
**Plain English**: The size of an AI model, measured in billions of parameters (B).

**Examples**:
- llama3.2:1b = 1 billion parameters (small, fast, needs ~2GB RAM)
- llama3.2:3b = 3 billion parameters (medium, good balance)
- llama3.2:70b = 70 billion parameters (large, best quality, needs ~64GB RAM)

**Trade-off**: Larger = better answers but slower and more RAM needed.

**Recommendation**: Start with 3B, upgrade to 8B if answers are poor.

---

### Context Window
**Plain English**: How much text an LLM can read at once.

**Example**: A model with 8K context window can read ~8,000 words (4-5 chunks).

**Why it matters for RAG**: Limits how many chunks you can send to the model.

**Typical sizes**: 4K, 8K, 32K, 128K tokens.

---

### Token
**Plain English**: A piece of text that the AI processes (roughly 3/4 of a word).

**Example**: "Hello world" = ~2 tokens; "I am learning RAG" = ~5 tokens.

**Why it matters**: Model limits and costs are measured in tokens.

**Rough conversion**: 100 tokens ≈ 75 words.

---

### Prompt
**Plain English**: The input you give to an AI model, including your question and retrieved chunks.

**Example for ragged**:
```
Context: [chunk 1] [chunk 2] [chunk 3]
Question: What is photosynthesis?
Answer:
```

**Why it matters**: Good prompts lead to better answers. ragged handles prompting automatically.

---

### Temperature
**Plain English**: How creative or random the AI's answers are (0.0 = deterministic, 1.0 = creative).

**Example**:
- Temperature 0.0: Always gives the same answer for the same question
- Temperature 0.7: Varies the phrasing and style slightly
- Temperature 1.0: More creative but sometimes off-topic

**ragged's default**: Usually 0.1-0.3 (factual, consistent).

---

## Storage and Databases

### ChromaDB
**Plain English**: The vector database ragged uses to store and search document embeddings.

**What it does**:
- Stores embeddings for all your document chunks
- Searches for similar embeddings when you query
- Remembers metadata (tags, dates, etc.)

**How to run it**: Either via Docker or in-memory mode.

**Data stored**: Embeddings, chunk text, metadata (not original documents).

---

### Collection
**Plain English**: A group of documents stored together in ChromaDB.

**Example**: You might have a "research-papers" collection and a "personal-notes" collection.

**ragged's approach**: Uses one default collection for all documents (unless you configure multiple).

---

### Persistent Storage
**Plain English**: Data saved to disk so it survives when you restart your computer.

**Example**: Once you add documents, they stay in ChromaDB even after rebooting.

**Contrast with in-memory**: In-memory storage disappears when the programme closes.

**ragged's default**: Persistent (saves to `./chroma_data/` directory).

---

### Metadata
**Plain English**: Additional information about a document (tags, categories, dates, etc.).

**Example**:
- Document: `research-paper.pdf`
- Metadata: `category=research, year=2023, author=Smith`

**How to add in ragged**:
```bash
ragged metadata update paper.pdf --set category=research
```

**Why useful**: Filter searches to specific subsets of documents.

---

## Performance and Configuration

### Latency
**Plain English**: How long something takes to complete (usually in seconds or milliseconds).

**Example**:
- Query latency: Time from asking a question to seeing the answer (5-15 seconds typical)
- Ingestion latency: Time to add a document (5-60 seconds)

**What affects it**: Model size, number of chunks, hardware speed.

---

### Throughput
**Plain English**: How many operations you can do per second or minute.

**Example**: "Ragged can ingest 10 documents per minute" or "Process 4 queries per minute".

**Less important for personal use**: Mostly matters for high-volume applications.

---

### Cache / Caching
**Plain English**: Storing frequently used results to avoid recomputing them.

**Example**: If you query the same document repeatedly, ragged might cache embeddings to speed up future queries.

**Command**: `ragged cache info` shows cache status.

**When to clear**: If you're running low on disk space (`ragged cache clear`).

---

### Environment Variables
**Plain English**: Configuration settings stored in a `.env` file that ragged reads on startup.

**Example**:
```
OLLAMA_MODEL=llama3.2:3b
CHUNK_SIZE=1000
EMBEDDING_MODEL=nomic-embed-text
```

**Why used**: Easy to change settings without editing code.

**Where stored**: `.env` file in ragged's directory.

---

## ragged-Specific Terms

### CLI (Command-Line Interface)
**Plain English**: Interacting with ragged by typing commands in a terminal rather than clicking buttons in an app.

**Example**: `ragged add paper.pdf` is a CLI command.

**Why CLI**: Faster for power users, easy to automate, works everywhere.

---

### Interactive Mode
**Plain English**: A conversational interface where you can ask multiple questions in one session.

**Example**:
```bash
ragged query --interactive
> What is photosynthesis?
[Answer shown]
> How does it relate to respiration?
[Answer shown]
```

**Exit**: Type `exit` or press `Ctrl+D`.

---

### Streaming
**Plain English**: Showing the answer as it's being generated, word by word, rather than waiting for the complete answer.

**Example**: Like ChatGPT's typing effect - you see words appear in real-time.

**In ragged**: `ragged query "question" --stream`

**Why useful**: Gives immediate feedback that something is happening.

---

### Dry Run
**Plain English**: Simulating an operation without actually doing it.

**Example**: `ragged add document.pdf --dry-run` shows what would happen without actually adding the document.

**Why useful**: Check if a command will work before committing to it.

---

## Quick Reference Table

| Term | Category | One-Sentence Definition |
|------|----------|-------------------------|
| RAG | Core | Search documents + AI-generate answers |
| Chunk | Processing | Piece of a document (~500-1000 words) |
| Embedding | Search | Text converted to numbers (vector) |
| Vector Database | Storage | Database for searching by similarity |
| Semantic Search | Search | Search by meaning, not keywords |
| LLM | Generation | AI that generates natural language |
| Ollama | Tool | Runs LLMs locally on your computer |
| ChromaDB | Tool | Stores and searches document embeddings |
| Top-K | Search | Number of chunks to retrieve (default: 5) |
| Metadata | Organisation | Tags and labels for documents |
| Latency | Performance | How long operations take |

---

## Common Confusion Clarified

### "Embedding" vs "Embedding Model"
- **Embedding**: The vector (list of numbers) representing text
- **Embedding Model**: The AI that creates embeddings

**Analogy**: Photo vs Camera

---

### "Vector" vs "Vector Database"
- **Vector**: A single list of numbers
- **Vector Database**: Where all vectors are stored

**Analogy**: Number vs Spreadsheet

---

### "LLM" vs "Embedding Model"
- **LLM**: Generates text (answers questions)
- **Embedding Model**: Converts text to vectors (no generation)

**Analogy**: Author vs Librarian

---

### "Chunk" vs "Document"
- **Document**: Your original file (PDF, .txt, .docx)
- **Chunk**: One small piece of that document after splitting

**Analogy**: Book vs Chapter

---

### "Semantic" vs "Keyword"
- **Semantic**: Understands meaning (finds "car" when you search "vehicle")
- **Keyword**: Exact matches only

**Analogy**: Understanding vs Matching

---

## Related Documentation

- **[Understanding RAG](../../explanation/rag-for-users.md)** - Conceptual overview of how RAG works
- **[Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md)** - Get started with ragged
- **[CLI Essentials](../../guides/cli/essentials.md)** - Learn core commands
- **[FAQ](../../guides/faq.md)** - Common questions answered

---

**Pro tip**: Bookmark this page for quick reference when you encounter unfamiliar terms in ragged's documentation.
