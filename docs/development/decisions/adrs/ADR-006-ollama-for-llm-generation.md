# ADR-006: Ollama for LLM Generation

**Status:** Accepted

---

## Context and Problem Statement

ragged needs to generate answers from retrieved context (the "G" in RAG). LLM inference can be done via cloud APIs (OpenAI, Anthropic) or local inference. Given ragged's privacy-first philosophy, local inference is required.

How should ragged run LLMs locally with good UX and reasonable performance?

## Decision Drivers

1. **Privacy Alignment**: Must support local-only inference
2. **User Experience**: Simple setup, no ML expertise required
3. **Model Variety**: Support multiple models (Llama, Mistral, Qwen, etc.)
4. **Performance**: Reasonable speed on consumer hardware
5. **Cross-Platform**: Work on macOS, Linux, Windows

## Considered Options

### Option 1: Ollama (Chosen)

**Description**: Use Ollama as LLM runtime. Users install Ollama separately, ragged communicates via HTTP API.

**Pros**:
- Excellent UX (simple `ollama serve`, `ollama pull llama3.2`)
- Supports 100+ models via unified API
- Cross-platform (macOS, Linux, Windows)
- Active development, strong community
- Automatic GPU detection and utilisation
- Model quantisation handled automatically
- OpenAI-compatible API (easy to use)

**Cons**:
- External dependency (users must install Ollama)
- Separate process to manage

### Option 2: llama.cpp Python Bindings

**Description**: Use llama-cpp-python for direct model loading.

**Pros**:
- Single Python dependency
- No separate process

**Cons**:
- Complex setup (compile with GPU support)
- User responsible for downloading/managing models
- Limited model format support (GGUF only)
- Platform-specific builds
- No automatic GPU detection

### Option 3: Transformers Library Directly

**Description**: Load models with HuggingFace Transformers.

**Pros**:
- Python-native
- Maximum flexibility

**Cons**:
- Huge models in memory (70GB for Llama 70B)
- Slow without quantisation
- User must understand quantisation, model formats
- Complex GPU setup
- 10x worse UX than Ollama

## Decision Outcome

**Chosen Option**: "Ollama"

**Justification**:

Ollama provides best UX for ragged's target users (document workers, not ML engineers):

1. **Simple Setup**:
   ```bash
   # Install Ollama
   curl https://ollama.ai/install.sh | sh

   # Download model
   ollama pull llama3.2

   # Start server
   ollama serve

   # ragged works automatically
   ragged query "What are the main points?"
   ```

2. **Model Management**: Ollama handles quantisation, GPU detection, model download/cache. Users don't need to understand GGUF, AWQ, or GPTQ.

3. **Performance**: Ollama optimised for consumer hardware. Automatic GPU acceleration on CUDA, Metal (Apple Silicon), ROCm.

4. **Flexibility**: Easy to switch models without code changes. Users can try Llama 3.2, Mistral, Qwen, etc.

5. **Privacy Preserved**: Ollama is local-only by default. Aligns with ADR-003 privacy principles.

**Consequences**:
- **Positive**:
  - Best-in-class UX for local LLM inference
  - Users can easily try different models
  - Automatic GPU utilisation
  - Cross-platform consistency
  - Active development/updates
  - OpenAI-compatible API (familiar to developers)

- **Negative**:
  - External dependency (users must install Ollama)
  - Separate process to manage (though simple)
  - Tied to Ollama's model support and API

## Implementation Notes

**When**: Core dependency since v0.1

**Configuration**:
```bash
# Default Ollama endpoint
OLLAMA_HOST=http://localhost:11434

# Override if custom Ollama server
export OLLAMA_HOST=http://custom-server:11434
```

**API Usage**:
```python
import requests

response = requests.post(
    f"{ollama_host}/api/generate",
    json={"model": "llama3.2", "prompt": prompt}
)
```

## References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Ollama Models List](https://ollama.ai/library)
- [ADR-003: Privacy-First Design](./ADR-003-privacy-first-local-only-design.md)

---

**Supersedes**: N/A

**Superseded By**: N/A
