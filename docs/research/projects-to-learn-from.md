# Projects to Learn From: RAG Ecosystem Overview

**Purpose**: Educational guide to the open-source RAG ecosystem, helping users understand different approaches and choose the right tool for their needs.

**Audience**: Users evaluating RAG systems, developers researching architecture patterns, teams planning RAG implementations

---

## Table of Contents

1. [Overview](#overview)
2. [Privacy-First Applications](#privacy-first-applications)
3. [Enterprise Platforms](#enterprise-platforms)
4. [Technical Leaders](#technical-leaders)
5. [Developer Frameworks](#developer-frameworks)
6. [Feature Comparison](#feature-comparison)
7. [Key Insights for Development](#key-insights-for-development)

---

## Overview

The RAG (Retrieval-Augmented Generation) landscape includes diverse approaches serving different needs. Understanding these projects helps contextualize design choices and identify best practices.

### Project Categories

**Privacy-First Applications**
- Full RAG systems prioritising local processing
- No cloud dependencies, complete data sovereignty
- Best for: Individual users, privacy-sensitive use cases

**Enterprise Platforms**
- Team collaboration and data source integration
- Multi-user support, permissions, SSO
- Best for: Organisations, team knowledge management

**Technical Leaders**
- Advanced features (visual workflows, GraphRAG, agents)
- Pushing RAG capabilities forward
- Best for: Complex workflows, research, experimentation

**Developer Frameworks**
- Component libraries for building custom RAG systems
- Modular, extensible architectures
- Best for: Developers building custom solutions

---

## Privacy-First Applications

### PrivateGPT

**GitHub**: [github.com/zylon-ai/private-gpt](https://github.com/zylon-ai/private-gpt) (53k+ stars)

**Architecture**: Dependency injection, Gradio UI, Qdrant vectors, OpenAI API compatibility

**Best For**:
- Drop-in replacement for OpenAI API
- Folder-watched automatic ingestion
- Users wanting familiar OpenAI-compatible interface

**Key Features**:
- **OpenAI API Compatibility** - Same API interface as OpenAI for easy migration
- **Folder Watch Automation** - Monitors directories for new documents, ingests automatically
- **Modular Backends** - Easy swapping of LLMs, embeddings, vector stores via DI
- **Qdrant Integration** - Advanced vector database with hybrid search capabilities

**Key Learnings**:
- API compatibility matters - developers want familiar interfaces
- Automation reduces friction - folder watch eliminates manual ingestion
- Modularity enables experimentation - DI allows easy backend swapping

**Use Cases**:
- Migrating from OpenAI to local processing
- Developers familiar with OpenAI API structure
- Users needing automatic document monitoring

---

### LocalGPT

**GitHub**: [github.com/PromtEngineer/localGPT](https://github.com/PromtEngineer/localGPT) (20k+ stars)

**Architecture**: Structure-aware chunking, domain customisation, FAISS vectors, complete offline operation

**Best For**:
- Completely offline environments (air-gapped systems)
- Regulated industries (healthcare, finance, legal)
- Domain-specific document processing

**Key Features**:
- **Structure-Aware Chunking** - Markdown conversion preserves document hierarchy
- **Domain-Specific Optimisation** - Specialised configurations for industries
- **Complete Offline Operation** - Zero internet dependency after setup
- **Regulatory Compliance Focus** - Designed for HIPAA, financial regulations

**Key Learnings**:
- Structure preservation improves chunking quality
- Domain customisation matters for specialised fields
- Air-gapped operation is critical for some industries

**Use Cases**:
- Healthcare organisations (HIPAA compliance)
- Financial institutions with strict data policies
- Government/defence requiring air-gapped systems
- Legal firms handling confidential documents

---

## Enterprise Platforms

### Onyx (formerly Danswer)

**GitHub**: [github.com/onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) (14k+ stars)

**Architecture**: Vespa search engine, connector framework, permission mirroring, SSO integration

**Best For**:
- Enterprise knowledge management (500+ employees)
- Organisations with strict access controls
- Teams using multiple data sources (Slack, Notion, Google Workspace, Confluence)
- Companies requiring SSO (OIDC, SAML, OAuth2)

**Key Features**:
- **40+ Data Source Connectors** - Slack, Google Drive, Confluence, SharePoint, Notion, GitHub, Jira, etc.
- **Permission Mirroring** - Document access mirrors source system ACLs automatically
- **Deep Research Agents** - Multi-step agentic search for complex queries
- **SSO Integration** - OIDC, SAML, OAuth2 for enterprise authentication
- **Feedback Loops** - Built-in user feedback gathering for continuous quality improvement
- **Vespa Search Engine** - Scales to millions of documents

**Key Learnings**:
- Connector ecosystem is critical for enterprise adoption
- Permission sync solves security concerns (documents inherit source permissions)
- Agentic search handles complex multi-step questions better
- User feedback improves retrieval quality over time

**Use Cases**:
- Large organisations needing unified search across platforms
- Companies with complex permission hierarchies
- Teams scattered across Slack, Notion, Google Workspace
- Enterprises requiring SSO and RBAC

---

### AnythingLLM

**GitHub**: [github.com/Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) (25k+ stars)

**Architecture**: Electron desktop apps, workspace isolation, embeddable widgets, MCP compatibility

**Best For**:
- Non-technical users preferring desktop apps
- Teams wanting workspace isolation
- Developers needing embeddable chat widgets
- Users wanting browser extension integration

**Key Features**:
- **Desktop Applications** - Native Mac/Windows/Linux apps (Electron-based)
- **No-Code AI Agent Builder** - Visual agent creation without programming
- **Embeddable Chat Widgets** - Add RAG chat to any website with JavaScript snippet
- **Browser Extensions** - Chrome/Firefox extensions for web integration
- **MCP Compatibility** - Model Context Protocol for tool integration
- **Workspace Isolation** - Separate collections per project/team

**Key Learnings**:
- Desktop apps provide better UX than web-only for daily-use tools
- No-code builders democratise agent creation
- Embeddable widgets extend RAG to other applications
- Workspace isolation prevents cross-contamination

**Use Cases**:
- Daily use requiring native app feel (faster, offline-capable)
- Non-programmers building AI agents
- Websites/apps needing embedded RAG chat
- Teams wanting isolated project workspaces

---

## Technical Leaders

### RAGFlow

**GitHub**: [github.com/infiniflow/ragflow](https://github.com/infiniflow/ragflow) (23k+ stars)

**Architecture**: Visual DAG editor, template-based chunking, code executor, multi-agent orchestration, GraphRAG

**Best For**:
- Non-programmers building complex RAG workflows
- Research requiring knowledge graph relationships
- Teams needing multi-agent task decomposition
- Organisations wanting visual workflow debugging

**Key Features**:
- **Visual DAG Workflow Editor** - Drag-and-drop pipeline builder (best-in-class)
- **Template-Based Chunking** - Multiple chunking strategies via templates
- **GraphRAG Support** - Knowledge graph-based retrieval for multi-hop reasoning
- **Multi-Agent Orchestration** - Planning, reflection, sub-agents for complex tasks
- **Code Execution Sandbox** - Python/JavaScript execution for tool use
- **Grounded Citations** - Visual text chunking inspection for transparency
- **MCP Support** - Model Context Protocol integration

**Key Learnings**:
- Visual workflow editors enable non-programmers to build complex pipelines
- GraphRAG improves multi-hop reasoning over flat retrieval
- Multi-agent systems decompose complex tasks effectively
- Visual debugging helps understand retrieval decisions

**Use Cases**:
- Business analysts building RAG workflows without coding
- Research requiring relationship extraction (who knows what, when)
- Complex tasks needing planning and multi-step execution
- Teams debugging retrieval pipelines visually

---

### Quivr

**GitHub**: [github.com/QuivrHQ/quivr](https://github.com/QuivrHQ/quivr) (35k+ stars)

**Architecture**: Brain marketplace, Megaparse ingestion, conversation filtering, public link sharing

**Best For**:
- Communities sharing knowledge base configurations
- Users wanting advanced conversation filtering
- Teams needing external conversation sharing

**Key Features**:
- **Brain Marketplace** - Share RAG configurations publicly or within teams
- **Megaparse Integration** - Advanced file ingestion capabilities
- **Conversation History Filtering** - Advanced query filtering and search
- **Public Sharing Links** - Share conversations externally with permissions
- **Cohere Reranking** - Advanced reranking integration for better retrieval

**Key Learnings**:
- Configuration sharing accelerates setup (templates, pre-tuned settings)
- Conversation management matters for daily use
- Public sharing enables collaboration beyond team boundaries

**Use Cases**:
- Communities building shared knowledge bases
- Users wanting pre-configured "brains" for specific domains
- Teams collaborating on research with external partners
- Advanced conversation search and filtering needs

---

## Developer Frameworks

### Haystack

**GitHub**: [github.com/deepset-ai/haystack](https://github.com/deepset-ai/haystack) (17k+ stars)

**Architecture**: Pipeline DAG, component library, evaluation nodes, production observability

**Best For**:
- Developers building custom RAG solutions
- Organisations needing specific integrations not in applications
- Research teams experimenting with RAG architectures
- Production deployments requiring strong observability

**Key Features**:
- **300+ Integrations** - Pre-built components for LLMs, embeddings, vector stores, rerankers
- **Pipeline DAG** - Branching, looping, conditional logic in retrieval workflows
- **Evaluation Nodes** - Built-in RAG quality tracking (RAGAS, faithfulness, relevance)
- **Production Observability** - Prometheus metrics, OpenTelemetry tracing, structured logging
- **Modular Swapping** - Easy component replacement for experimentation
- **Cross-Encoder Reranking** - Advanced reranking for improved retrieval quality

**Key Learnings**:
- Component-based architecture enables rapid experimentation
- Pipeline DAGs provide flexibility beyond simple linear retrieval
- Built-in evaluation accelerates quality improvements
- Production observability is critical for debugging and optimisation

**Use Cases**:
- Custom RAG solutions with specific requirements
- Organisations with unique integrations (internal tools, proprietary systems)
- Research teams comparing retrieval strategies
- Production systems requiring monitoring, alerts, and debugging

---

## Feature Comparison

### Privacy & Security

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **Local Processing** | ★★★★★ | ★★★★★ | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| **Offline Mode** | ★★★★★ | ★★★★★ | ★★★★☆ | ★☆☆☆☆ | ★★★★★ | ★★★☆☆ | ★☆☆☆☆ | ★★★☆☆ |
| **Data Encryption** | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| **GDPR Compliance** | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |

### Multi-Modal & Vision

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **Vision Retrieval** | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **Image Queries** | ★★★★★ | ★☆☆☆☆ | ★★★☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★☆☆☆ | ★★★★☆ | ★★★★☆ |
| **Multi-Modal LLMs** | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ |

### Document Processing

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **PDF Quality Analysis** | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ |
| **Table Extraction** | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ |
| **OCR Support** | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ |

### Retrieval Methods

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **Hybrid Search** | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ |
| **Reranking** | ★★★★★ | ★★★★☆ | ★★☆☆☆ | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★★★★★ | ★★★★★ |
| **Query Expansion** | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ |
| **Knowledge Graphs** | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | ★★★★☆ |

### User Interface

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **CLI** | ★★★★★ | ★★★☆☆ | ★☆☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★★☆☆ |
| **Web UI** | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★☆☆☆ | ★★★★★ | ★★★★★ | ★★☆☆☆ |
| **Desktop App** | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★★ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ |
| **Visual Workflow** | ★★☆☆☆ | ★☆☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★★ | ★★★★☆ |

### Collaboration

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **Multi-User** | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★☆ | ★★★★★ | ★☆☆☆☆ | ★★★★☆ | ★★☆☆☆ | ★★☆☆☆ |
| **SSO/RBAC** | ★☆☆☆☆ | ★☆☆☆☆ | ★★★☆☆ | ★★★★★ | ★☆☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ |
| **Document Sharing** | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★☆ | ★★★★★ | ★☆☆☆☆ | ★★★★☆ | ★★☆☆☆ | ★★☆☆☆ |

### Enterprise Features

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **Audit Logging** | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ |
| **Data Connectors** | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ |
| **Monitoring** | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ |

### Agent & Workflow

| Feature | ragged | PrivateGPT | AnythingLLM | Onyx | LocalGPT | Quivr | RAGFlow | Haystack |
|---------|--------|------------|-------------|------|----------|-------|---------|----------|
| **AI Agents** | ★★☆☆☆ | ★☆☆☆☆ | ★★★★★ | ★★★★☆ | ★☆☆☆☆ | ★★☆☆☆ | ★★★★★ | ★★★★★ |
| **Workflow Builder** | ★★☆☆☆ | ★☆☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★★ | ★★★★★ |
| **Tool Calling** | ★★★★☆ | ★★☆☆☆ | ★★★★☆ | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ |

---

## Key Insights for Development

### 1. Desktop Applications Matter (AnythingLLM)

**Insight**: Native desktop apps provide better UX than web-only for daily-use knowledge management tools.

**Why It Matters**:
- Faster startup and response (no browser overhead)
- Offline capability (web requires connection)
- Better system integration (filesystem access, notifications)
- User preference for "app feel" vs browser tab

**Application**: Consider desktop app for future versions (Electron or Tauri)

---

### 2. Visual Workflow Builders (RAGFlow)

**Insight**: Non-programmers benefit tremendously from visual DAG editors for building retrieval pipelines.

**Why It Matters**:
- Democratises complex workflow creation
- Visual debugging helps understand retrieval decisions
- Drag-and-drop faster than code for experimentation
- Business analysts can build without developer assistance

**Application**: Visual pipeline builder could differentiate from CLI-first tools

---

### 3. Data Source Connectors (Onyx)

**Insight**: Enterprise adoption requires integrations with common tools (Google Drive, Slack, Notion, Confluence).

**Why It Matters**:
- Most knowledge lives in SaaS tools, not local files
- Permission sync solves security concerns (documents inherit source ACLs)
- Automatic ingestion reduces manual work
- Teams use 5-10 different knowledge sources

**Application**: Connector framework critical for team/enterprise use cases

---

### 4. Agent Capabilities (RAGFlow, Haystack, AnythingLLM)

**Insight**: Multi-step workflows and tool calling are becoming standard RAG features, not advanced extras.

**Why It Matters**:
- Complex questions require multiple retrieval steps
- Tool integration expands RAG beyond document search
- Planning and reflection improve answer quality
- Users expect "AI assistant" capabilities, not just search

**Application**: Agent capabilities planned for future versions

---

### 5. Team Collaboration (Onyx, AnythingLLM)

**Insight**: Even small teams need multi-user support, document sharing, and workspace isolation.

**Why It Matters**:
- Knowledge management is inherently collaborative
- Teams want to share findings, not duplicate work
- Permission management prevents accidental data leaks
- Activity feeds keep teams aligned

**Application**: Multi-user support prioritised for future versions

---

### 6. Observability & Monitoring (Haystack, Onyx)

**Insight**: Production deployments require Prometheus metrics, structured logging, and distributed tracing.

**Why It Matters**:
- Debugging retrieval issues requires visibility into pipeline
- Performance regressions need automated detection
- SLAs require latency tracking (p50, p95, p99)
- Compliance audits need detailed logs

**Application**: Observability planned for enterprise readiness

---

### 7. Configuration Sharing (Quivr)

**Insight**: Pre-configured "brains" or templates accelerate setup for specific domains.

**Why It Matters**:
- New users don't know optimal settings
- Domain experts can share tuned configurations
- Templates reduce trial-and-error
- Community contributions improve ecosystem

**Application**: Configuration export/import for sharing best practices

---

### 8. Folder Watch Automation (PrivateGPT)

**Insight**: Automatic ingestion from monitored directories eliminates manual document upload friction.

**Why It Matters**:
- Users forget to manually ingest new documents
- Automation ensures knowledge base stays current
- Integration with document workflows (save to folder = auto-indexed)
- Reduces cognitive load

**Application**: Folder watch planned for data connectivity milestone

---

## Related Documentation

- [ragged Architecture Overview](../explanation/architecture-overview.md) - ragged's design principles
- [Version Roadmap](../development/roadmap/version/README.md) - Planned features and milestones
- [Privacy Design](../explanation/privacy-design.md) - Privacy-by-design architecture
- Vision RAG Guide - Multi-modal document understanding

---
