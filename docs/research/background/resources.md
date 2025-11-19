# RAG Resources & References

Curated collection of papers, articles, tools, and resources for building RAG systems.

## Foundational Papers

### RAG Core Concepts
- **"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"** (Lewis et al., 2020)
  - Original RAG paper from Facebook AI
  - Link: https://arxiv.org/abs/2005.11401

- **"Dense Passage Retrieval for Open-Domain Question Answering"** (Karpukhin et al., 2020)
  - Dense retrieval fundamentals
  - Link: https://arxiv.org/abs/2004.04906

### Context & Chunking
- **"Lost in the Middle: How Language Models Use Long Contexts"** (Liu et al., 2023)
  - Important for understanding context window usage
  - Link: https://arxiv.org/abs/2307.03172

- **"Precise Zero-Shot Dense Retrieval without Relevance Labels"** (Gao et al., 2022)
  - HyDE (Hypothetical Document Embeddings)
  - Link: https://arxiv.org/abs/2212.10496

### Advanced RAG Techniques
- **"Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"** (Asai et al., 2023)
  - Self-reflective RAG
  - Link: https://arxiv.org/abs/2310.11511

- **"In-Context Retrieval-Augmented Language Models"** (Ram et al., 2023)
  - In-context learning with RAG
  - Link: https://arxiv.org/abs/2302.00083

## Embedding Models

### Popular Models
- **Sentence Transformers**: https://www.sbert.net/
  - all-MiniLM-L6-v2 (small, fast)
  - all-mpnet-base-v2 (better quality)
  - Documentation and model cards

- **BGE (BAAI General Embedding)**: https://huggingface.co/BAAI
  - bge-small-en-v1.5
  - bge-base-en-v1.5
  - State-of-the-art quality

- **OpenAI Embeddings**: text-embedding-3-small/large
  - Excellent quality but requires API

### Embedding Evaluation
- **MTEB Leaderboard**: https://huggingface.co/spaces/mteb/leaderboard
  - Massive Text Embedding Benchmark
  - Compare embedding models

## Vector Databases

### Embedded/Local
- **ChromaDB**: https://www.trychroma.com/
  - Python-native, embedded
  - What we use by default

- **FAISS**: https://github.com/facebookresearch/faiss
  - Facebook AI Similarity Search
  - Very fast, in-memory

### Production-Grade
- **Qdrant**: https://qdrant.tech/
  - Written in Rust, fast and scalable
  - Rich filtering capabilities

- **Weaviate**: https://weaviate.io/
  - GraphQL API, hybrid search
  - Good for production

- **Milvus**: https://milvus.io/
  - Distributed, cloud-native
  - Enterprise-scale

- **Pinecone**: https://www.pinecone.io/
  - Fully managed, cloud-only
  - Easy to use but not local

## LLM Backends

### Local LLM Runners
- **Ollama**: https://ollama.com/
  - What we use by default
  - Easiest setup, growing ecosystem

- **LM Studio**: https://lmstudio.ai/
  - User-friendly GUI
  - Good for non-technical users

- **llama.cpp**: https://github.com/ggerganov/llama.cpp
  - Direct C++ implementation
  - Maximum performance

- **LocalAI**: https://localai.io/
  - OpenAI-compatible API
  - Multiple model formats

### Model Sources
- **Hugging Face**: https://huggingface.co/models
  - Largest model repository
  - GGUF models for llama.cpp/Ollama

- **Ollama Library**: https://ollama.com/library
  - Pre-configured models for Ollama
  - Mistral, Llama, CodeLlama, etc.

## Document Processing

### Python Libraries
- **PyPDF2**: https://github.com/py-pdf/pypdf
  - PDF parsing

- **pdfplumber**: https://github.com/jsvine/pdfplumber
  - Better PDF extraction (tables, etc.)

- **python-docx**: https://python-docx.readthedocs.io/
  - DOCX file processing

- **BeautifulSoup**: https://www.crummy.com/software/BeautifulSoup/
  - HTML parsing

- **Unstructured**: https://github.com/Unstructured-IO/unstructured
  - Unified document processing

## RAG Frameworks & Tools

### Frameworks
- **LangChain**: https://github.com/langchain-ai/langchain
  - Most popular RAG framework
  - Lots of integrations

- **LlamaIndex**: https://github.com/jerryjliu/llama_index
  - Specialised for RAG and indexing
  - Good documentation

- **Haystack**: https://haystack.deepset.ai/
  - Production-ready NLP framework
  - Strong enterprise focus

### Similar Projects
- **PrivateGPT**: https://github.com/imartinez/privateGPT
  - Similar privacy-focused approach
  - Uses LangChain

- **LocalGPT**: https://github.com/PromtEngineer/localGPT
  - Another local RAG system
  - GPU-focused

- **Quivr**: https://github.com/QuivrHQ/quivr
  - "Second brain" RAG app
  - More feature-rich

## Evaluation & Benchmarks

### RAG Evaluation
- **RAGAS**: https://github.com/explodinggradients/ragas
  - RAG Assessment framework
  - Metrics for faithfulness, relevance

- **TruLens**: https://github.com/truera/trulens
  - LLM application evaluation
  - RAG-specific metrics

### Benchmarks
- **BEIR**: https://github.com/beir-cellar/beir
  - Benchmark for retrieval
  - Standard evaluation suite

- **KILT**: https://ai.meta.com/tools/kilt/
  - Knowledge-intensive language tasks
  - RAG benchmark

## Articles & Tutorials

### Guides
- **Pinecone's RAG Guide**: https://www.pinecone.io/learn/retrieval-augmented-generation/
  - Comprehensive overview

- **LangChain RAG Tutorial**: https://python.langchain.com/docs/use_cases/question_answering/
  - Practical implementation

- **Weaviate RAG Best Practices**: https://weaviate.io/blog
  - Search for RAG-related articles

### Blogs to Follow
- **r/LocalLLaMA**: https://reddit.com/r/LocalLLaMA
  - Active community for local LLMs

- **Hugging Face Blog**: https://huggingface.co/blog
  - Latest developments in embeddings and LLMs

- **Ollama Blog**: https://ollama.com/blog
  - Updates on local LLM running

## Communities

- **Ollama Discord**: https://discord.gg/ollama
- **LangChain Discord**: https://discord.gg/langchain
- **Hugging Face Forums**: https://discuss.huggingface.co/
- **r/MachineLearning**: https://reddit.com/r/MachineLearning

## Tools & Utilities

### Development
- **LangSmith**: https://smith.langchain.com/
  - Debug and monitor LLM applications

- **Weights & Biases**: https://wandb.ai/
  - Experiment tracking

- **Promptfoo**: https://github.com/promptfoo/promptfoo
  - Prompt evaluation and testing

### Testing
- **Pytest**: https://pytest.org/
  - Python testing framework

- **DeepEval**: https://github.com/confident-ai/deepeval
  - LLM application testing

---


**Note**: Add new resources as you discover them during development.
