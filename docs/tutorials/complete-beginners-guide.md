# Complete Beginner's Guide to ragged

**What you'll learn**: How to install ragged and ask your first question in under 30 minutes.

**Who this is for**: Complete beginners with no prior RAG experience. If you've never heard of "embeddings" or "vector databases", you're in the right place.

**What you'll need**:
- A Mac, Linux, or Windows computer
- 30 minutes of focused time
- Basic comfort with terminal/command line

---

## What is ragged?

**ragged is like having a conversation with your documents.**

Instead of searching through files manually, you ask questions in plain English and ragged finds the relevant information and generates answers.

**Example**:
- You have 50 PDF research papers
- You ask: "What methods were used to measure learning outcomes?"
- ragged searches all 50 papers, finds relevant sections, and gives you a summary

**Key difference from ChatGPT**: Your documents never leave your computer. Everything runs locally for complete privacy.

---

## What you'll accomplish today

By the end of this guide, you'll:
1. ✅ Install ragged and its requirements
2. ✅ Add your first document
3. ✅ Ask a question and get an answer
4. ✅ Understand what happened behind the scenes

**Time required**: 20-30 minutes

---

## Before you start: Understanding the pieces

ragged needs four things to work. Don't worry - we'll install them all together.

### 1. Python 3.12
**What it is**: The programming language ragged is written in.
**Why you need it**: To run ragged on your computer.
**What you'll do**: Install Python 3.12 (not 3.11, not 3.13 - specifically 3.12).

### 2. Ollama
**What it is**: Software that runs AI language models on your computer.
**Why you need it**: ragged uses Ollama to understand your questions and generate answers.
**What you'll do**: Install Ollama and download one AI model (about 4GB).

### 3. ChromaDB
**What it is**: A database for storing your documents in a searchable format.
**Why you need it**: ragged needs somewhere to store processed documents.
**What you'll do**: Either install Docker to run ChromaDB, or use ragged's built-in mode (simpler).

### 4. ragged itself
**What it is**: The software that ties everything together.
**Why you need it**: This is the main programme you'll interact with.
**What you'll do**: Download and install ragged.

---

## Installation: Step by step

### Step 1: Check your Python version

Open your terminal (Mac/Linux) or Command Prompt (Windows).

**Mac/Linux**:
```bash
python3 --version
```

**Windows**:
```bash
python --version
```

**What you're looking for**: `Python 3.12.x` (x can be any number).

**If you see Python 3.12.x**: ✅ Great! Continue to Step 2.

**If you see a different version** (3.11, 3.13, etc.):
- **Mac**: Install Python 3.12 from [python.org](https://www.python.org/downloads/macos/)
- **Windows**: Install Python 3.12 from [python.org](https://www.python.org/downloads/windows/)
- **Linux**: `sudo apt install python3.12` (Ubuntu/Debian) or equivalent for your distribution

---

### Step 2: Install Ollama

**What we're doing**: Installing the AI model software.

**For all operating systems**:
1. Go to [ollama.com](https://ollama.com)
2. Click "Download" for your operating system
3. Install the application (Mac: drag to Applications; Windows: run installer)

**Verify installation**:
```bash
ollama --version
```

You should see a version number like `0.1.x`.

**Download a language model** (required):
```bash
ollama pull llama3.2:3b
```

**What this does**: Downloads a 3-billion parameter AI model (about 4GB). This will take 5-10 minutes depending on your internet speed.

**Why this model**: It's small enough to run on most computers but powerful enough for good answers.

---

### Step 3: Install ragged

**What we're doing**: Installing ragged itself.

#### Create a folder for ragged

**Mac/Linux**:
```bash
cd ~
mkdir ragged-setup
cd ragged-setup
```

**Windows**:
```bash
cd %USERPROFILE%
mkdir ragged-setup
cd ragged-setup
```

#### Clone the ragged repository

```bash
git clone https://github.com/REPPL/ragged.git
cd ragged
```

**Don't have git?** Install it:
- **Mac**: Install Xcode Command Line Tools: `xcode-select --install`
- **Windows**: Download from [git-scm.com](https://git-scm.com)
- **Linux**: `sudo apt install git` (Ubuntu/Debian)

#### Create a Python virtual environment

**What is a virtual environment?** A isolated space for ragged's dependencies. This keeps ragged separate from other Python programmes on your computer.

**Mac/Linux**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**:
```bash
python -m venv .venv
.venv\Scripts\activate
```

**What you should see**: Your terminal prompt now starts with `(.venv)`.

#### Install ragged

```bash
pip install -e .
```

**What this does**: Installs ragged and all its dependencies. This takes 2-3 minutes.

**Verify installation**:
```bash
ragged --version
```

You should see: `ragged 0.2.8` (or higher).

✅ **Success!** ragged is installed.

---

### Step 4: Choose your ChromaDB option

You have two choices for running ChromaDB:

#### Option A: Docker (Recommended if you have Docker)

**If you already have Docker installed**:

1. Create a `docker-compose.yml` file in the ragged directory:

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
EOF
```

2. Start ChromaDB:

```bash
docker compose up -d
```

3. Verify it's running:

```bash
docker compose ps
```

You should see `chromadb` with status `Up`.

#### Option B: Built-in mode (Simpler for beginners)

**If you don't have Docker** or want a simpler setup:

ragged includes a built-in ChromaDB mode. No additional setup needed!

**Note**: We'll configure this in the next step.

---

### Step 5: Configure ragged

**What we're doing**: Telling ragged where to find Ollama and ChromaDB.

Create a configuration file:

```bash
cat > .env << 'EOF'
# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Embedding settings
EMBEDDING_MODEL=nomic-embed-text

# ChromaDB settings (choose based on your Step 4 choice)
# For Docker (Option A), use:
CHROMA_HOST=localhost
CHROMA_PORT=8000

# For built-in mode (Option B), comment out the above and use:
# CHROMA_HOST=localhost
# CHROMA_PORT=8000
# CHROMA_IN_MEMORY=true

# Data directory
DATA_DIR=./ragged_data
EOF
```

**For Windows users**: Create a file called `.env` in the ragged directory and copy the text above into it using Notepad.

**What these settings mean**:
- `OLLAMA_MODEL`: The AI model you downloaded in Step 2
- `EMBEDDING_MODEL`: How documents are processed for searching
- `CHROMA_HOST/PORT`: Where ChromaDB is running
- `DATA_DIR`: Where ragged stores your documents

---

### Step 6: Start Ollama

Ollama needs to be running for ragged to work.

**Mac**: Ollama should start automatically. Check your menu bar for the Ollama icon.

**Linux/Windows**:
```bash
ollama serve
```

**Leave this terminal window open** and open a new terminal window for the next steps.

---

### Step 7: Verify everything works

Run ragged's health check:

```bash
ragged health
```

**What you should see**:
```
Ollama Service:    ✓ Connected
ChromaDB Service:  ✓ Connected
Configuration:     ✓ Valid
```

**If you see errors**:
- **Ollama not connected**: Make sure `ollama serve` is running (Step 6)
- **ChromaDB not connected**:
  - Docker users: Check `docker compose ps` shows ChromaDB running
  - Built-in users: Make sure `CHROMA_IN_MEMORY=true` is in your `.env` file

---

## Your first query: Adding a document

Now for the exciting part - let's add a document and ask a question!

### Create a sample document

Let's create a simple text file to practise with:

**Mac/Linux**:
```bash
cat > sample.txt << 'EOF'
The Capital of Knowledge Project

Overview:
The Capital of Knowledge is a three-year research initiative examining how cities develop and maintain their status as centres of learning and innovation. The project focuses on five major cities: London, Boston, Singapore, Berlin, and Melbourne.

Key Findings:
1. University density is the strongest predictor of knowledge capital
2. Cities with strong public transport see 40% higher collaboration rates
3. Affordable housing within 30 minutes of universities is critical

Methodology:
We surveyed 5,000 researchers across the five cities and analysed patent filings, academic publications, and startup formation rates over a 10-year period.

Conclusions:
Knowledge capitals are not born but built through deliberate policy decisions around education, housing, and transport infrastructure.
EOF
```

**Windows** (create `sample.txt` in Notepad and paste):
```
The Capital of Knowledge Project

Overview:
The Capital of Knowledge is a three-year research initiative examining how cities develop and maintain their status as centres of learning and innovation. The project focuses on five major cities: London, Boston, Singapore, Berlin, and Melbourne.

Key Findings:
1. University density is the strongest predictor of knowledge capital
2. Cities with strong public transport see 40% higher collaboration rates
3. Affordable housing within 30 minutes of universities is critical

Methodology:
We surveyed 5,000 researchers across the five cities and analysed patent filings, academic publications, and startup formation rates over a 10-year period.

Conclusions:
Knowledge capitals are not born but built through deliberate policy decisions around education, housing, and transport infrastructure.
```

### Add the document to ragged

```bash
ragged add sample.txt
```

**What you'll see**:
```
Processing sample.txt...
✓ Extracted 1 document
✓ Created 5 chunks
✓ Generated embeddings
✓ Stored in vector database
Successfully added: sample.txt
```

**What just happened?**
1. ragged read your document
2. Split it into smaller "chunks" (pieces of text)
3. Converted each chunk into a mathematical representation (an "embedding")
4. Stored everything in ChromaDB so you can search it

**Time taken**: 5-10 seconds (depending on document size).

---

### Ask your first question

Now let's query the document:

```bash
ragged query "What cities were studied in the research?"
```

**What you'll see**:
```
Searching for relevant information...
✓ Found 3 relevant chunks
✓ Generating answer...

Answer:
The research studied five major cities: London, Boston, Singapore, Berlin, and Melbourne. These cities were chosen as the focus of the Capital of Knowledge project, which examined how cities develop and maintain their status as centres of learning and innovation.

Sources:
- sample.txt (chunks 1, 2)
```

**🎉 Congratulations!** You just performed your first RAG query.

---

## Understanding what happened

Let's break down what ragged did behind the scenes:

### Step 1: Understanding your question
ragged converted your question "What cities were studied?" into a mathematical representation (an embedding).

### Step 2: Searching the database
ragged compared your question's embedding against all the chunk embeddings stored in ChromaDB. It found the 3 most similar chunks.

### Step 3: Generating an answer
ragged sent those 3 chunks plus your question to Ollama (the AI model). Ollama read the relevant chunks and generated a natural language answer.

### Step 4: Showing you the result
ragged displayed the answer and told you which document it came from.

**Key insight**: The AI never "remembers" your document. Every time you query, ragged searches for relevant chunks and sends them to the AI. This is why it's called "Retrieval-Augmented Generation" (RAG).

---

## Try a few more queries

Now that you understand the process, try these queries:

```bash
# Ask about methodology
ragged query "How was the research conducted?"

# Ask about findings
ragged query "What factors contribute to knowledge capital?"

# Ask something not in the document
ragged query "What is the population of London?"
```

**Notice**: The last query will say "No relevant information found" because that information isn't in your document. ragged only answers based on what you've added.

---

## Adding more documents

You can add multiple documents:

```bash
# Add a PDF
ragged add research-paper.pdf

# Add multiple files
ragged add paper1.pdf paper2.pdf notes.txt

# Add an entire folder
ragged add ./my-research-papers/
```

**Supported formats**:
- PDF (`.pdf`)
- Text (`.txt`)
- Markdown (`.md`)
- Word (`.docx`)
- HTML (`.html`)

---

## Checking what you've added

See all your documents:

```bash
ragged list
```

**Output**:
```
Documents in collection:

sample.txt
- Chunks: 5
- Added: 2025-11-18 10:30:45
```

Remove a document:

```bash
ragged clear sample.txt
```

---

## Common beginner questions

### "How long does adding a document take?"

**Rough guide**:
- Small text file (1-2 pages): 5-10 seconds
- PDF paper (10-20 pages): 20-40 seconds
- Book (300 pages): 2-4 minutes

**What takes time**: Generating embeddings (mathematical representations) for each chunk.

### "How many documents can I add?"

**Limits**:
- No hard limit
- Depends on your available disk space
- Most users: 100-1000 documents works well

**Storage guide**:
- 100 PDFs (~10 pages each): ~50MB of embeddings
- 1000 PDFs: ~500MB of embeddings

### "Will queries get slower with more documents?"

**Short answer**: Slightly, but not noticeably until you have thousands of documents.

**Why**: ChromaDB uses efficient vector similarity search. Searching 10 documents vs 1000 documents adds only 1-2 seconds.

### "Can I use this without internet?"

**Yes!** Once Ollama models are downloaded, ragged works completely offline. Your documents never leave your computer.

### "What if I get a bad answer?"

Common reasons and fixes:

1. **Relevant information not in your documents**
   - **Fix**: Add more documents covering the topic

2. **Information spread across multiple chunks**
   - **Fix**: Use `ragged query "your question" --k 10` to retrieve more chunks (default is 5)

3. **Question too vague**
   - **Fix**: Be more specific. Instead of "What does it say?", ask "What methodology was used?"

4. **Model too small**
   - **Fix**: Try a larger model: `ollama pull llama3.2` (8B parameters, better quality, needs more RAM)

### "How do I change the AI model?"

1. Download a different model:
   ```bash
   ollama pull llama3.2  # Larger, better quality
   ```

2. Update your `.env` file:
   ```
   OLLAMA_MODEL=llama3.2
   ```

3. Query again - ragged will use the new model.

---

## Next steps

Now that you're set up, explore these features:

### 1. Interactive mode
Ask multiple questions in a conversation:
```bash
ragged query --interactive
```

Type your questions, see answers, refine your questions - all in one session.

### 2. Search without generating answers
Just find relevant chunks without asking Ollama:
```bash
ragged search "knowledge capital"
```

**Use case**: Quick look-up without waiting for AI generation.

### 3. Organise with metadata
Tag your documents:
```bash
ragged metadata update sample.txt --set category=research --set year=2023
```

Search by tags:
```bash
ragged metadata search --filter category=research
```

### 4. View your history
See past queries:
```bash
ragged history list
```

Replay a previous query:
```bash
ragged history replay 1
```

---

## Troubleshooting

### "ragged: command not found"

**Cause**: Your virtual environment isn't activated.

**Fix**:
- **Mac/Linux**: `source .venv/bin/activate`
- **Windows**: `.venv\Scripts\activate`

You should see `(.venv)` at the start of your prompt.

### "Ollama connection failed"

**Cause**: Ollama isn't running.

**Fix**:
- **Mac**: Check menu bar for Ollama icon
- **Linux/Windows**: Run `ollama serve` in a separate terminal

### "ChromaDB connection failed"

**Docker users**:
```bash
docker compose ps  # Check if running
docker compose up -d  # Start if not running
```

**Built-in mode users**: Make sure `.env` has `CHROMA_IN_MEMORY=true`.

### "Model not found"

**Cause**: The model specified in `.env` isn't downloaded.

**Fix**:
```bash
ollama list  # See what you have
ollama pull llama3.2:3b  # Download the model
```

Make sure `.env` matches: `OLLAMA_MODEL=llama3.2:3b`

### "Out of memory" errors

**Cause**: Your computer doesn't have enough RAM for the model.

**Fix**: Use a smaller model:
```bash
ollama pull llama3.2:1b  # Smallest, needs ~2GB RAM
```

Update `.env`: `OLLAMA_MODEL=llama3.2:1b`

---

## What you've learned

✅ What RAG is and how it works
✅ How to install ragged and its requirements
✅ How to add documents and ask questions
✅ What happens behind the scenes
✅ How to troubleshoot common issues

---

## Related Documentation

- [CLI Essentials](../guides/cli/essentials.md) - Master the 5 core commands
- [Understanding RAG](../explanation/rag-for-users.md) - Conceptual overview of how RAG works
- [User Glossary](../reference/terminology/user-glossary.md) - Plain English definitions of technical terms
- [FAQ](../guides/faq.md) - Answers to common questions
- [Personal Notes Guide](../guides/use-cases/personal-notes.md) - Using ragged for personal knowledge management
- [Research Papers Guide](../guides/use-cases/research-papers.md) - Managing academic literature
- [Troubleshooting Guide](../guides/troubleshooting/setup-issues.md) - Solutions to common setup problems

---

## Getting Help

**Found a bug?** [Report it on GitHub](https://github.com/REPPL/ragged/issues)

**Have a question?** Check the [FAQ](../guides/faq.md) or open a [GitHub discussion](https://github.com/REPPL/ragged/discussions)

**Want to contribute?** See [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**You're ready to use ragged!** Start adding your documents and asking questions. The more you use it, the more comfortable you'll become.

Happy querying! 🚀
