# ADR-003: Privacy-First Local-Only Design Philosophy

**Status:** Accepted

---

## Context and Problem Statement

Modern RAG systems typically rely on cloud services: hosted vector databases (Pinecone), API-based embeddings (OpenAI), and managed LLM inference (Anthropic, OpenAI). This creates privacy concerns when processing sensitive documents (medical records, legal documents, proprietary business data, personal information).

ragged must decide: follow the cloud-first industry pattern for convenience and performance, or prioritise privacy through local-only operation?

**Key Requirements**:
- Handle sensitive documents without data leakage
- Work offline (no internet dependency for core functionality)
- User trust and transparency
- Compliance with data protection regulations (GDPR, HIPAA concepts)
- Reasonable performance on consumer hardware

**Constraints**:
- Cannot require enterprise infrastructure
- Must work on consumer laptops/desktops
- Development resources limited (open-source project)
- GPU acceleration optional, not mandatory

## Prior Art

**Influences from Other Projects**:
- ✅ Ollama - Local LLM inference philosophy
- ✅ PrivateGPT - Privacy-focused RAG (inspired naming)
- ✅ LocalAI - OpenAI-compatible local inference
- ❌ LangChain - Cloud-first, API-centric (common industry pattern)

**External Inspirations**:
- Privacy-focused software movement (Signal, ProtonMail principles)
- GDPR's data minimisation principle
- Right to data portability and local processing

**Key Differences**: ragged commits to privacy-first as non-negotiable, not optional.

## Decision Drivers

1. **User Trust**: Users must trust ragged with sensitive documents
2. **Data Sovereignty**: Users maintain complete control over their data
3. **Offline Operation**: Must work without internet connectivity
4. **Compliance**: Enable users to meet regulatory requirements
5. **Transparency**: No hidden data transmission or telemetry
6. **Accessibility**: Free from ongoing API costs

## Considered Options

### Option 1: Privacy-First Local-Only (Chosen)

**Description**: All core functionality works entirely locally. No cloud services, no telemetry, no data transmission. Internet only needed for initial setup (downloading models).

**Architecture**:
```
User's Machine (all processing here)
├── ragged CLI/API/UI
├── ChromaDB (local vector storage)
├── Ollama (local LLM inference)
├── ColPali/SentenceTransformers (local embeddings)
└── User documents (never leave machine)
```

**Pros**:
- ✅ **Complete privacy** - no data ever transmitted
- ✅ **Offline operation** - works on air-gapped systems
- ✅ **User trust** - transparent, verifiable privacy
- ✅ **Zero ongoing costs** - no API fees
- ✅ **Data sovereignty** - user controls everything
- ✅ **Regulatory compliance** - simplifies GDPR/HIPAA
- ✅ **No vendor lock-in** - independent of external services

**Cons**:
- ❌ Performance limited by user's hardware
- ❌ Initial setup more complex (download models)
- ❌ No automatic updates for models
- ❌ User responsible for GPU/hardware
- ❌ Slower than cloud-optimised services

**Implementation Effort**: High (requires local-optimised architecture)

### Option 2: Cloud-First with Optional Local

**Description**: Default to cloud APIs (OpenAI embeddings, Anthropic LLMs, Pinecone vector DB) with optional local fallback.

**Pros**:
- ✅ Best performance out-of-box
- ✅ Simpler initial setup
- ✅ Automatic model updates
- ✅ Lower hardware requirements
- ✅ Industry-standard pattern

**Cons**:
- ❌ **Privacy compromised** - documents sent to third parties
- ❌ **Ongoing costs** - API fees per query
- ❌ **Requires internet** - offline operation impossible
- ❌ **Vendor dependencies** - subject to API changes, pricing
- ❌ **Compliance complexity** - data processing agreements needed
- ❌ **User trust issues** - hidden data transmission

**Implementation Effort**: Low (use existing SDKs)

### Option 3: Hybrid with User Choice

**Description**: Support both local and cloud backends. User chooses their privacy/performance trade-off.

**Pros**:
- ✅ Flexibility for different use cases
- ✅ Users can optimise for their needs
- ✅ Progressive enhancement (start cloud, move local)

**Cons**:
- ❌ **High complexity** - maintain two codepaths
- ❌ **Testing burden** - validate both paths
- ❌ **Documentation overhead** - explain two approaches
- ❌ **Privacy ambiguity** - easy to misconfigure
- ❌ **No clear identity** - what is ragged's philosophy?

**Implementation Effort**: Very High (double implementation)

## Decision Outcome

**Chosen Option**: "Privacy-First Local-Only (Option 1)"

**Justification**:

Privacy is **non-negotiable** for ragged's target use cases:

1. **Legal Documents**: Lawyers cannot send client documents to external APIs (attorney-client privilege, confidentiality requirements).

2. **Medical Records**: Healthcare providers face HIPAA compliance. Sending patient data to cloud APIs requires Business Associate Agreements, complexity, and risk.

3. **Business Intelligence**: Companies cannot send proprietary documents, trade secrets, or competitive analysis to external services.

4. **Personal Information**: Users' private journals, financial records, personal documents deserve protection.

5. **Academic Research**: Researchers with unpublished data or sensitive human subjects research need air-gapped processing.

**Privacy enables these use cases. Cloud-first makes them impossible.**

**Performance Trade-Off Accepted**:

Local LLMs (Ollama with Llama 3.2, Mistral) are slower than GPT-4, but acceptable:
- Response time: 2-10 seconds (local) vs 0.5-2 seconds (API)
- For document Q&A, this is acceptable latency
- Users who need <1s latency can use higher-end GPUs or smaller models

**Cost Trade-Off Accepted**:

Hardware investment upfront vs ongoing API costs:
- Local: $0/month after hardware purchase
- Cloud: $10-100/month depending on usage
- Crossover point: 3-12 months

**Philosophy Over Convenience**:

ragged intentionally chooses privacy over ease-of-use. This is a feature, not a bug. Users who want ragged understand and value this trade-off.

**Consequences**:
- **Positive**:
  - Complete user trust - no hidden data transmission
  - Works on air-gapped systems (military, research, high-security)
  - Zero ongoing costs after setup
  - No API rate limits or quotas
  - No vendor dependencies or API changes
  - Simplified compliance (data never leaves user control)
  - Transparent and auditable privacy guarantees
  - Community can verify no telemetry

- **Negative**:
  - Higher hardware requirements (GPU recommended, 16GB RAM minimum)
  - Initial setup more complex (install Ollama, download models)
  - Performance limited by user hardware
  - Model updates require manual download
  - Less convenient than cloud APIs
  - May deter users who want "just works" experience

- **Neutral**:
  - Clear project identity: privacy-first RAG
  - Attracts privacy-conscious users
  - May limit mainstream adoption (acceptable trade-off)

## Implementation Notes

**When**: Core principle since v0.1

**Dependencies**:
- Ollama (local LLM inference)
- ChromaDB (local vector storage)
- SentenceTransformers (local text embeddings)
- ColPali (local vision embeddings, v0.5.0+)

**Migration Strategy**: Not applicable - foundational principle.

**Optional Cloud Features** (allowed as explicit opt-in):
- Users may configure external Ollama server if desired
- No built-in cloud integrations
- Any future cloud features must be:
  - Completely optional
  - Explicitly documented as privacy trade-off
  - Disabled by default

## Validation

**How will we know this was the right decision?**
- Users trust ragged with sensitive documents ✅
- No privacy complaints or data leakage incidents ✅
- Adoption in privacy-sensitive sectors (legal, medical, research) ✅
- Community audits verify no telemetry ✅
- Feature requests align with privacy-first values ✅

**Review Date**: Never - this is a core, immutable principle

**Potential Future Changes**:
- None - privacy-first is ragged's identity
- Any cloud features would create a **new product**, not change ragged
- If cloud integration needed, fork the project rather than compromise this principle

## References

- [Ollama Project](https://ollama.ai/) - Local LLM philosophy
- [PrivateGPT](https://privategpt.io/) - Privacy-focused RAG inspiration
- [GDPR Data Minimisation](https://gdpr.eu/data-minimisation/)
- [ADR-002: ChromaDB Choice](./ADR-002-chromadb-as-vector-database.md)
- [ADR-006: Ollama Integration](./ADR-006-ollama-for-llm-generation.md)

---

## Research Notes

**Sources Consulted**:
- Privacy-focused software projects (Signal, ProtonMail, Tor)
- GDPR, HIPAA, attorney-client privilege requirements
- Local-first software manifesto
- RAG system landscape (LangChain, LlamaIndex, PrivateGPT)

**Key Insights**:
- Many users **cannot** use cloud RAG due to regulatory/professional requirements
- Privacy-first is underserved market niche
- Local-first enables new use cases impossible with cloud
- Performance gap between local/cloud narrowing with better models (Llama 3.2, Mistral)
- Users willing to trade convenience for privacy when documents are sensitive

## Alternatives Not Considered

- **Encrypted cloud processing** - still requires trusting external service
- **On-premises deployment of cloud services** - complex, expensive, defeats purpose
- **Privacy-preserving computation** - academic, not practical for LLMs yet

---

**Supersedes**: N/A (foundational)

**Superseded By**: N/A (immutable principle)
