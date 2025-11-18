# Understanding RAG: A User's Guide

**What you'll learn**: What Retrieval-Augmented Generation (RAG) is, how it works, and why it's useful - all in plain English.

**Reading time**: 10 minutes

---

## The problem RAG solves

Imagine you have 100 research papers on your computer. You need to find papers that discuss a specific methodology, but:
- Searching for keywords misses papers that use different terminology
- Reading all 100 papers would take days
- AI chatbots like ChatGPT have never seen your specific papers

**What you need**: A way to search your documents using natural language and get AI-generated answers based on your specific content.

**This is what RAG does.**

---

## What is RAG?

**RAG** stands for **Retrieval-Augmented Generation**.

Let's break that down:

### Retrieval
**Finding the relevant information from your documents.**

Instead of exact keyword matching, RAG uses "semantic search" - it understands meaning. Search for "car" and it will also find "vehicle", "automobile", "motor", etc.

### Augmented
**Enhancing the AI with your specific information.**

The AI doesn't need to remember everything. You give it relevant excerpts from your documents when needed.

### Generation
**Creating natural language answers.**

An AI language model reads the relevant excerpts and generates a coherent answer to your question.

---

## How RAG works: A simple analogy

Think of RAG like a library with an expert assistant:

### Traditional search (like Google)
You tell the librarian: "Find books with the word 'photosynthesis'."
They return every book that contains that exact word.

### RAG
You ask: "How do plants make energy?"
The assistant:
1. Understands you're asking about plant energy production
2. Finds relevant sections in botany books (even if they don't say "energy")
3. Reads those sections
4. Explains the answer in simple terms

**That's RAG**: Understand → Find → Read → Explain

---

## The RAG process in ragged

Here's what happens when you use ragged:

### Step 1: Adding documents (one-time setup)

```
Your document → ragged → Stored in searchable format
```

**What ragged does**:
1. **Chunks**: Splits your document into smaller pieces (typically 500-1000 words each)
2. **Embeds**: Converts each chunk into a mathematical representation (a vector)
3. **Stores**: Saves these vectors in a database (ChromaDB)

**Why chunks?** AI models have limits on how much text they can read at once. Chunks are bite-sized pieces that fit these limits.

**Why vectors?** Mathematical representations allow similarity search. Similar content has similar vectors.

**Time**: 5-60 seconds per document depending on size.

### Step 2: Asking a question

```
Your question → ragged → Answer + Sources
```

**What ragged does**:
1. **Embed your question**: Converts it into a vector (same process as documents)
2. **Search**: Finds the 5 chunks with the most similar vectors
3. **Retrieve**: Pulls the actual text of those chunks
4. **Generate**: Sends chunks + question to AI (Ollama)
5. **Answer**: AI reads the chunks and generates a response

**Time**: 5-15 seconds per query.

---

## Visualising the RAG flow

```
┌─────────────────────────────────────────────────────┐
│ SETUP PHASE (Once per document)                    │
└─────────────────────────────────────────────────────┘

Document (PDF, .txt, .docx)
         ↓
[Chunking] Split into pieces
         ↓
[Embedding] Convert to vectors
         ↓
[Storage] Save in ChromaDB
         ↓
  Ready for querying


┌─────────────────────────────────────────────────────┐
│ QUERY PHASE (Every time you ask)                   │
└─────────────────────────────────────────────────────┘

Your Question: "What methods were used?"
         ↓
[Embedding] Convert question to vector
         ↓
[Search] Find 5 most similar chunks
         ↓
[Retrieve] Get actual text of chunks
         ↓
[Generate] AI reads chunks + question
         ↓
Your Answer: "Three methods were used:
              1. Surveys...
              2. Interviews...
              3. Observations..."
         ↓
Sources: document.pdf (chunks 3, 7, 12)
```

---

## Why RAG vs other approaches?

### RAG vs Traditional search (Google, Ctrl+F)

**Traditional search**:
- ❌ Finds exact keyword matches only
- ❌ Returns entire documents or pages
- ❌ You must read and synthesise information yourself

**RAG**:
- ✅ Understands meaning, not just keywords
- ✅ Returns synthesised answers, not raw text
- ✅ Shows you where the answer came from

**Example**:
- **Search query**: "machine learning"
- **Traditional**: Returns documents containing "machine learning"
- **RAG query**: "What is machine learning?"
- **RAG**: "Machine learning is a subset of artificial intelligence where... [generates explanation from your documents]"

### RAG vs ChatGPT/Claude (Cloud AI)

**ChatGPT/Claude**:
- ❌ Doesn't know about your specific documents
- ❌ Sends your data to external servers (privacy risk)
- ❌ Can't cite sources from your files
- ✅ Good general knowledge

**RAG (ragged)**:
- ✅ Works with your specific documents
- ✅ Everything stays on your computer (private)
- ✅ Cites exact sources from your files
- ⚠️ Only knows what you've added

**Example**:
- **Your question**: "What did the 2023 Q3 financial report say about revenue?"
- **ChatGPT**: "I don't have access to your company's financial reports."
- **ragged**: "Q3 2023 revenue was £2.4M, up 15% from Q2... [Source: financial-report-2023-q3.pdf]"

### RAG vs Manual organisation

**Manual organisation** (folders, tags, notes):
- ❌ Time-consuming to categorise everything
- ❌ Hard to find information spread across files
- ❌ Rigid categories don't fit complex questions

**RAG**:
- ✅ Just add documents, no organisation needed
- ✅ Automatically finds relevant information across all files
- ✅ Flexible: can answer questions you didn't anticipate

**Example**:
- **Question**: "What papers discuss both neural networks AND education?"
- **Manual**: Check "neural-networks" folder, check "education" folder, read both
- **RAG**: Searches all documents, finds relevant sections combining both topics

---

## Is RAG right for you?

RAG is excellent for:

### ✅ Research and academic work
- Literature reviews
- Finding citations
- Comparing methodologies across papers
- Summarising findings

### ✅ Personal knowledge management
- Searching through years of notes
- Remembering insights from books you've read
- Finding that article you saved months ago

### ✅ Professional documentation
- Company policies and procedures
- Technical documentation
- Meeting notes and project files
- Legal documents and contracts

### ✅ Learning and study
- Textbook question-answering
- Exam preparation
- Course notes consolidation

---

## When RAG isn't the answer

RAG is not ideal for:

### ❌ Real-time information
RAG only knows about documents you've added. It won't have today's news or current events.

**Use instead**: Web search, news sites

### ❌ Creative writing
RAG retrieves existing content. It doesn't create entirely new creative work.

**Use instead**: Creative writing AI tools like ChatGPT

### ❌ Mathematical computations
RAG can explain concepts but won't perform complex calculations.

**Use instead**: Calculators, Wolfram Alpha, spreadsheets

### ❌ Very small document collections
If you only have 2-3 documents, traditional search might be faster.

**Use instead**: Ctrl+F / Command+F

---

## Common misconceptions

### "RAG remembers my documents"
**False**. RAG searches your documents every single time you query. It doesn't "remember" anything - it looks up relevant chunks fresh each time.

**Why this matters**: You can add new documents and immediately query them. No "retraining" needed.

### "Bigger AI models are always better"
**Not necessarily**. Larger models (like llama3.2:70b) give more nuanced answers but:
- Require significantly more RAM (64GB+)
- Take much longer to respond (30-60 seconds vs 5-10 seconds)
- May be overkill for simple queries

**Best practice**: Start with smaller models (3B or 8B parameters). Upgrade if answers are consistently poor.

### "I need to organise my documents first"
**False**. RAG works on unorganised collections. Just add everything - ragged figures out what's relevant.

**However**: Adding metadata (tags) can improve filtering if you want to search specific subsets.

### "RAG replaces reading"
**Not quite**. RAG summarises and finds information quickly, but:
- Important nuances might be missed
- You should verify critical information by reading sources
- Think of RAG as a research assistant, not a replacement for deep reading

---

## Key concepts explained

### Embeddings
**Plain English**: Converting text into numbers that capture meaning.

Similar meanings have similar numbers. Example:
- "dog" and "puppy" have similar embeddings
- "dog" and "computer" have very different embeddings

**Why it matters**: This is how RAG understands that "automobile" and "car" are related.

### Vector database
**Plain English**: A database optimised for finding similar embeddings.

Traditional database: "Find exact matches for 'cat'"
Vector database: "Find the 5 most similar things to this concept"

**ragged uses**: ChromaDB (a vector database)

### Chunks
**Plain English**: Pieces of a document, typically 500-1000 words.

**Why chunk?** AI models can only read limited text at once. A 50-page document must be split into manageable pieces.

**Trade-off**: Smaller chunks = more precise retrieval but less context. Larger chunks = more context but less precise.

### Top-K retrieval
**Plain English**: How many chunks to retrieve for each query.

Default: K=5 (retrieve 5 chunks)

**When to adjust**:
- Complex questions spanning multiple topics: increase K (--k 10)
- Simple questions: decrease K (--k 3) for faster responses

### Semantic search
**Plain English**: Search by meaning, not exact words.

Traditional search: "contains the word 'happy'"
Semantic search: "concepts related to happiness (joyful, pleased, content, satisfied)"

**How RAG does it**: Compares embedding vectors for similarity.

---

## Decision tree: Should you use RAG?

```
Do you have documents you want to query?
├─ YES → Continue
└─ NO → RAG isn't for you yet

Is the information already easily searchable online?
├─ YES → Maybe just use Google
└─ NO → Continue

Do you need answers based on YOUR specific documents?
├─ YES → Continue
└─ NO → Use ChatGPT for general knowledge

Do you care about privacy (keeping data local)?
├─ YES → RAG is perfect for you! ✅
└─ NO → Could use cloud RAG, but local works too

Are you willing to spend 30 minutes setting up?
├─ YES → Get started with ragged! ✅
└─ NO → Wait until you have time

Do you have a computer with at least 8GB RAM?
├─ YES → You're all set! ✅
└─ NO → You'll need to use smaller models
```

---

## Next steps

Now that you understand RAG:

1. **[Complete Beginner's Guide](../tutorials/complete-beginners-guide.md)** - Get ragged installed and running
2. **[User Glossary](../reference/terminology/user-glossary.md)** - Look up specific terms
3. **[CLI Essentials](../guides/cli/essentials.md)** - Learn the core commands
4. **[FAQ](../guides/faq.md)** - Answers to common questions

---

## Summary

**RAG is**:
- A method for querying your personal documents using AI
- Private (everything runs locally)
- Flexible (works with unorganised collections)
- Semantic (understands meaning, not just keywords)

**RAG works by**:
1. Converting documents to searchable vectors (one-time)
2. Converting your question to a vector
3. Finding similar vectors (relevant chunks)
4. Having AI read those chunks and generate an answer

**RAG is best for**:
- Research, knowledge management, professional docs, learning

**RAG is not ideal for**:
- Real-time information, creative writing, calculations

---

## Related Documentation

- [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md) - Installation and first steps with ragged
- [User Glossary](../reference/terminology/user-glossary.md) - Plain English definitions of key concepts
- [CLI Essentials](../guides/cli/essentials.md) - Learn the 5 core commands
- [FAQ](../guides/faq.md) - Common questions answered
- [CLI Intermediate](../guides/cli/intermediate.md) - Advanced features for growing collections

---

**Ready to try it?** Head to the [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md) to get started.
