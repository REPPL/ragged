# LLM Backends

**Status:** 🚧 Coming Soon

## Overview

This document covers the selection and integration of Large Language Model (LLM) backends for ragged's answer generation capabilities.

---

## Coming Soon

This document will cover:

### LLM Requirements

#### Functional Requirements
- **Text Generation**: Answer synthesis from context
- **Instruction Following**: Respect prompts and formats
- **Citation Generation**: Accurate source attribution
- **Streaming**: Real-time response output
- **Context Handling**: Support long contexts (8k+ tokens)

#### Non-Functional Requirements
- **Privacy**: Local inference by default
- **Performance**: <5s for typical queries
- **Resource Efficiency**: Run on consumer hardware
- **Quality**: Coherent, accurate responses
- **Flexibility**: Swappable backends

### Backend Options

#### Ollama (Default - v0.1)
**Primary local LLM backend**

**Pros**:
- ✅ Easy setup and model management
- ✅ Optimised for local inference
- ✅ Wide model selection
- ✅ Active community
- ✅ OpenAI-compatible API
- ✅ 100% privacy preserving

**Cons**:
- ⚠️ Performance depends on hardware
- ⚠️ Model size limitations

**Recommended Models**:
- **llama2-7b**: Balanced performance
- **mistral-7b**: Better quality, similar speed
- **llama2-13b**: Higher quality (requires more RAM)
- **mixtral-8x7b**: Excellent quality (high-end hardware)

**Integration**:
```python
import ollama

response = ollama.chat(
    model='mistral',
    messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': query_with_context}
    ],
    stream=True
)

for chunk in response:
    print(chunk['message']['content'], end='')
```

#### OpenAI API (Optional)
**Cloud-based high-quality option**

**Pros**:
- ✅ Excellent quality
- ✅ Fast inference
- ✅ Large context windows (128k+)
- ✅ Well-documented API

**Cons**:
- ❌ Requires internet
- ❌ Privacy concerns (opt-in only)
- ❌ Usage costs
- ❌ API key required

**Models**:
- **gpt-4o-mini**: Cost-effective, good quality
- **gpt-4o**: Highest quality
- **gpt-3.5-turbo**: Fast, cheaper

**Use Case**: Opt-in for users prioritising quality over privacy

#### Anthropic Claude (Optional)
**Alternative cloud option**

**Pros**:
- ✅ Excellent reasoning
- ✅ Long context (200k tokens)
- ✅ Strong safety

**Cons**:
- ❌ Cloud-based (privacy concerns)
- ❌ API costs
- ❌ Requires API key

**Use Case**: Premium opt-in option

#### Local Alternatives

**llama.cpp**:
- Direct integration possible
- More control, more complexity
- Consider for advanced users (v0.4+)

**LocalAI**:
- Ollama alternative
- OpenAI-compatible API
- Consider if needed

### Implementation Architecture

#### LLM Provider Abstraction
```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(prompt, context, **kwargs) -> str

    @abstractmethod
    def stream(prompt, context, **kwargs) -> Iterator[str]

    @abstractmethod
    def is_available() -> bool

class OllamaProvider(LLMProvider):
    # Default local implementation

class OpenAIProvider(LLMProvider):
    # Optional cloud implementation
```

#### Configuration
```yaml
llm:
  provider: ollama  # or openai, anthropic

  ollama:
    host: localhost
    port: 11434
    model: mistral
    temperature: 0.1

  openai:  # Optional
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o-mini
    temperature: 0.1
```

### Prompt Engineering

#### System Prompts
```
You are a helpful assistant that answers questions based on provided context.
Rules:
- Only use information from the provided context
- Cite sources using [1], [2] notation
- If the answer is not in the context, say so
- Be concise and accurate
```

#### Query Templates
```
Context:
{context_chunks}

Question: {user_query}

Answer with citations:
```

#### Response Formatting
- Citation markers: [1], [2]
- Confidence indicators: "Based on the context..." vs "I'm not certain..."
- Structured responses when appropriate

### Quality Optimisation

#### Model Parameters
- **Temperature**: 0.1-0.3 for factual responses
- **Top-p**: 0.9-0.95 for diversity
- **Max tokens**: Configurable based on needs
- **Stop sequences**: Control output format

#### Prompt Techniques
- Few-shot examples
- Chain-of-thought prompting
- Self-consistency checking (v0.4+)
- Retrieval-aware prompting

#### Context Management
- Chunk selection and ordering
- Context window management
- Truncation strategies
- Metadata integration

### Performance Optimisation

#### Local Inference
- **Model Quantisation**: GGUF 4-bit, 8-bit models
- **Batch Processing**: When streaming not required
- **Caching**: Common queries/responses
- **Hardware Acceleration**: GPU, Metal (Apple Silicon)

#### Response Streaming
- Immediate user feedback
- Reduced perceived latency
- Progressive rendering
- Cancellation support

### Evaluation

#### Quality Metrics
- **Faithfulness**: Answer grounded in context
- **Relevance**: Addresses the question
- **Coherence**: Well-structured response
- **Citation Accuracy**: Correct source attribution

#### Performance Metrics
- **Time to First Token**: Streaming latency
- **Total Generation Time**: Complete response
- **Throughput**: Tokens per second
- **Resource Usage**: RAM, GPU memory

### Version Roadmap

#### v0.1: Ollama Foundation
- Basic Ollama integration
- Simple prompting
- Streaming responses
- Citation generation

#### v0.2: Enhanced Prompting
- Improved prompt templates
- Better citation formatting
- User-configurable models

#### v0.3: Multi-Backend Support
- OpenAI integration (optional)
- Provider abstraction
- Automatic fallback

#### v0.4: Advanced Features
- Self-consistency
- Confidence scoring
- Multi-hop reasoning

#### v1.0: Production Optimisation
- Optimal default models
- Comprehensive benchmarks
- Cost optimisation (cloud providers)

---

## Related Documentation

- **[Model Selection](../core-concepts/model-selection.md)** - Selection criteria
- **[Streaming](streaming.md)** - Streaming implementation
- **[Offline Capability](offline-capability.md)** - Local-first design
- **[Technology Comparisons](../../../research/background/technology-comparisons.md)** - Detailed comparisons

---

*This document will be expanded with specific model benchmarks and prompt examples*
