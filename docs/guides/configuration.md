# Configuration Guide


A comprehensive configuration guide is planned for a future release.

## Available Now

For configuration guidance, please see:

- **[README.md Configuration](../../README.md#configuration)** - Basic configuration setup
- **[Configuration Reference](../reference/configuration.md)** - All available settings
- **[CLI validate command](../reference/cli/command-reference.md#validate)** - Validate your configuration

## Quick Configuration

Create a `.env` file:

```bash
# Environment
RAGGED_ENVIRONMENT=development
RAGGED_LOG_LEVEL=INFO

# Embedding Model
RAGGED_EMBEDDING_MODEL=sentence-transformers
RAGGED_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# LLM
RAGGED_LLM_MODEL=llama3.2

# Chunking
RAGGED_CHUNK_SIZE=500
RAGGED_CHUNK_OVERLAP=100

# Services
RAGGED_CHROMA_URL=http://localhost:8001
RAGGED_OLLAMA_URL=http://localhost:11434
```

## What's Coming

The configuration guide will include:
- Step-by-step configuration walkthrough
- Common configuration patterns
- Performance tuning recommendations
- Environment-specific configurations (development, production)
- Troubleshooting configuration problems

---


---

## Related Documentation

- [Pydantic Configuration (ADR-0002)](../development/decisions/adrs/0002-pydantic-for-configuration.md) - Configuration design
- [Settings Reference](../reference/configuration/) - All settings
- [Installation Tutorial](../tutorials/installation.md) - Getting started

---
