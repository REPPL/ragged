# ADR-0001: Local-Only Processing Architecture

**Status:** Accepted

**Date:** 2025-11-09

**Area:** Architecture, Privacy

**Related:**
- [Privacy Architecture](../development/design/core-concepts/privacy-architecture.md)
- [Product Vision](../vision/product-vision.md)

---

## Context

ragged's core mission is privacy-first local document processing. Users need complete confidence that their documents never leave their machine, especially when dealing with sensitive or confidential information. Many RAG systems rely on external APIs (OpenAI, Anthropic, etc.), which raises privacy concerns and compliance issues.

The fundamental question: Should ragged support external API calls for better quality, or commit to local-only processing?

## Decision

ragged will use **absolutely no external API calls** by default:
- No OpenAI API
- No Anthropic API
- No cloud vector databases
- No external embedding services
- All processing happens on the user's machine

All core functionality must work completely offline with local models and databases.

## Rationale

**Privacy & Trust:**
- User documents never leave their machine
- No third-party data access
- Builds trust through transparency
- Easier compliance with data protection regulations (GDPR, HIPAA, etc.)

**Control & Ownership:**
- Users control all models and data
- No vendor lock-in
- No dependency on external services
- Works without internet connection

**Cost:**
- No per-use API costs
- No monthly subscriptions
- One-time setup, unlimited use

**Philosophy:**
- Aligns with ragged's core values
- Differentiates from cloud-first alternatives
- Enables truly private AI assistance

## Alternatives Considered

**1. Hybrid approach (local + optional cloud)**
- **Pros:** Best-of-both-worlds, user choice
- **Cons:** Adds complexity, dilutes privacy message, risk of accidental data leakage
- **Decision:** Rejected—violates core principle

**2. Cloud-first with local fallback**
- **Pros:** Better default quality
- **Cons:** Opposite of privacy-first philosophy, privacy becomes "opt-in"
- **Decision:** Rejected—wrong priority order

**3. Local-only with explicit cloud plugins**
- **Pros:** Maintains core privacy whilst allowing extensions
- **Cons:** Risk of normalising cloud usage
- **Decision:** Deferred—may consider for v1.0+ as opt-in plugins

## Consequences

### Positive

✅ **Privacy:** True privacy preservation, no data leaves user's machine
✅ **Trust:** Users can verify with network monitoring
✅ **Compliance:** Easier for regulated industries
✅ **Cost:** No ongoing API expenses
✅ **Offline:** Works without internet
✅ **Control:** User owns entire pipeline
✅ **Differentiation:** Clear market position

### Negative

⚠️ **Quality:** Limited by local model capabilities
⚠️ **Performance:** Slower than cloud APIs on lower-end hardware
⚠️ **Setup:** More complex initial setup (Ollama, models, etc.)
⚠️ **Resources:** Requires adequate local compute
⚠️ **Model Size:** Limited by available RAM/disk

### Mitigation Strategies

- Provide clear hardware recommendations
- Support multiple model sizes (small to large)
- Optimise for Apple Silicon and GPU acceleration
- Excellent documentation for setup
- Consider cloud plugins for v1.0+ (opt-in only)

## Implementation Notes

**Services required:**
- Ollama (for LLM generation)
- ChromaDB (local vector database)
- sentence-transformers or Ollama embeddings (local embedding models)

**Configuration:**
- All external APIs disabled by default
- No API key configuration options in v0.1
- Clear error messages if user tries cloud features

**Testing:**
- Network should not be required after initial setup
- Integration tests verify no external calls
- Mock external services for testing setup code

## Future Considerations

**v0.2+:** May introduce **opt-in** cloud plugins with:
- Explicit user consent required
- Clear privacy warnings
- Disabled by default
- Separate documentation

**v1.0+:** Potential plugin system for:
- OpenAI/Anthropic as alternatives (opt-in)
- Cloud vector databases (opt-in)
- Hybrid retrieval (local + cloud)

**Non-Negotiable:** Core ragged will always work 100% locally. Cloud features will always be optional plugins, never required.

---

**Last Updated:** 2025-11-13

**Supersedes:** None

**Superseded By:** None
