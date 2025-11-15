# ADR-0012: Ollama for LLM Generation

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** LLM, Generation

## Context

Need a local LLM backend for answer generation that:
- Respects privacy-first principle (no external APIs)
- Provides good quality answers
- Supports model flexibility
- Runs efficiently on consumer hardware
- Integrates easily with ragged

## Decision

Use Ollama as the LLM backend with llama3.2 as the default model.

## Rationale

- **Local**: Fully local execution, no external APIs required
- **Simple**: Clean HTTP API, easy integration
- **Model Choice**: Access to llama3.2, mistral, qwen, and many others
- **Active Development**: Regular updates, growing ecosystem, strong community
- **Performance**: Optimised for local inference on various hardware
- **Streaming Support**: Can stream responses for better UX
- **Hardware Optimised**: Metal on macOS, CUDA on Linux/Windows
- **Easy Model Management**: Simple `ollama pull` to add models

## Alternatives Considered

### 1. OpenAI API

**Pros:**
- Highest quality responses
- Simple API
- No local compute needed

**Cons:**
- **Violates privacy-first principle** (external API)
- Documents/queries leave user's machine
- Costs money per request
- Requires internet connection
- No offline operation

**Rejected:** Fundamentally incompatible with ragged's core principles

### 2. llama.cpp

**Pros:**
- Direct integration (no service)
- Very efficient
- Wide model support

**Cons:**
- More complex integration
- Harder to swap models
- Manual model management
- Lower-level API

**Rejected:** More complexity than benefit for v0.1

### 3. LocalAI

**Pros:**
- OpenAI-compatible API
- Drop-in replacement
- Multiple backend support

**Cons:**
- Less mature than Ollama
- Smaller community
- More complex setup

**Rejected:** Ollama has better momentum and simpler UX

### 4. Hugging Face transformers

**Pros:**
- Direct model access
- Wide model selection
- Flexible

**Cons:**
- More complex integration
- Memory-intensive
- Slower inference than optimised solutions
- Manual model management

**Rejected:** Too complex, slower, more resource-intensive

## Implementation

```python
import requests

def generate_answer(prompt: str, context: str) -> str:
    """Generate answer using Ollama."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": f"Context: {context}\n\nQuestion: {prompt}",
            "stream": False
        }
    )
    return response.json()["response"]
```

## Consequences

### Positive

- Fully local processing maintains privacy
- Easy model switching (`ollama pull <model>`)
- Good performance on M-series Macs and modern hardware
- Clean API simplifies integration
- Streaming support available for v0.2+
- Active community and regular updates

### Negative

- Requires Ollama service running separately
- Another dependency/service to manage
- Model quality depends on user's hardware capabilities
- Initial model download can be large (GBs)
- Service must be started before ragged

### Neutral

- Service architecture allows future swappability
- Could support multiple backends in future (llama.cpp, LocalAI)

## Hardware Considerations

Recommended models by hardware:
- **16GB RAM**: llama3.2:3b
- **32GB+ RAM**: mistral:7b
- **64GB+ RAM**: qwen2.5:32b

## Future Enhancements

v0.2+:
- Support for multiple LLM backends (llama.cpp, LocalAI)
- Streaming responses for better UX
- Model configuration per collection

v0.3+:
- Automatic model selection based on hardware
- Multi-model routing (different models for different query types)

## Related

- [ADR-0001: Local-Only Processing](./0001-local-only-processing.md)
- [ADR-0006: Dual Embedding Model Support](./0006-dual-embedding-model-support.md)
- [Core Concepts: Model Selection](../core-concepts/model-selection.md)
- [Docker Setup Guide](../../guides/docker-setup.md)
