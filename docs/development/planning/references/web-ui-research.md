# Web UI Research for RAG Systems (2025)

**Purpose**: Document research into state-of-the-art web interfaces for RAG systems

---

## Overview

This document captures the research conducted to inform ragged's web interface design. It covers modern RAG system UIs, technology choices, UX patterns, and design decisions for serving both non-technical and technical users.

## Leading RAG System UIs (2025)

### 1. Kotaemon

**URL**: https://github.com/Cinnamon/kotaemon

**Architecture**:
- Gradio-based interface
- Document-centric design
- Visual document preview
- Clean, minimal UI

**Strengths**:
- Rapid prototyping with Gradio
- Good citation visualisation
- Document preview with highlighting
- Minimal learning curve

**Limitations**:
- Limited customization
- Gradio constraints for advanced features
- Not optimal for production deployment

**Lessons for ragged**:
- Use Gradio for v0.2-v0.4 (prototyping phase)
- Prioritize citation clarity
- Document preview is valuable for users

### 2. Open WebUI

**URL**: https://github.com/open-webui/open-webui

**Architecture**:
- SvelteKit frontend
- FastAPI backend
- Markdown rendering
- Plugin architecture

**Strengths**:
- Production-quality UI
- Excellent performance (Svelte)
- Clean separation of concerns
- Extensible plugin system

**Limitations**:
- More complex to develop
- Longer initial development time
- Requires frontend expertise

**Lessons for ragged**:
- Svelte is ideal for production (v0.5+)
- Plugin architecture enables extensibility
- Progressive enhancement is key

### 3. Verba (Weaviate)

**URL**: https://github.com/weaviate/Verba

**Architecture**:
- React frontend
- Modern chat interface
- Source attribution
- Visual chunking display

**Strengths**:
- Professional UI/UX
- Clear source attribution
- Chunk visualisation helpful for debugging
- Good responsive design

**Limitations**:
- React bundle size larger than Svelte
- Requires more JavaScript expertise
- Complex build pipeline

**Lessons for ragged**:
- Chunk visualisation valuable for technical users
- Progressive disclosure needed (hide complexity by default)
- Mobile responsiveness important

## Technology Evaluation

### Frontend Framework Decision

**Evaluated**: Gradio, React, Vue, Svelte, HTMX

**Decision**: Gradio (v0.2-v0.4) → Svelte/SvelteKit (v0.5-v1.0)

**Rationale**:

1. **Gradio (Early Versions)**:
   - ✅ Rapid prototyping
   - ✅ Python-native (no separate frontend repo)
   - ✅ Built-in SSE streaming support
   - ✅ Zero frontend expertise needed
   - ❌ Limited customization
   - ❌ Not production-grade
   - **Use case**: Get working UI fast for testing and feedback

2. **Svelte/SvelteKit (Production)**:
   - ✅ Smallest bundle size (1.6KB runtime)
   - ✅ Best performance (compiled, no virtual DOM)
   - ✅ Clean, readable code
   - ✅ Excellent SSR support
   - ✅ Growing ecosystem (2025)
   - ❌ Longer development time
   - ❌ Requires frontend knowledge
   - **Use case**: Production-quality UI with optimal performance

**Why not React?**
- Larger bundle size (42KB React + 2KB ReactDOM)
- More complex mental model (hooks, virtual DOM)
- Overkill for ragged's UI needs

**Why not Vue?**
- Smaller than React but larger than Svelte
- Less performance advantage
- Composition API adds complexity

**Why not HTMX?**
- Great for simple server-rendered apps
- Challenging for complex state management
- Streaming tokens more complex
- Limited for graph visualisations

### Backend Framework Decision

**Evaluated**: Flask, Django, FastAPI

**Decision**: FastAPI

**Rationale**:
- ✅ Async/await support (essential for streaming)
- ✅ Auto-generated OpenAPI/Swagger docs
- ✅ Type hints and validation (Pydantic)
- ✅ WebSocket and SSE support
- ✅ Fast performance (Starlette/Uvicorn)
- ✅ Modern Python 3.10+ features

**Why not Flask?**
- No native async support
- Manual API documentation
- Limited built-in validation

**Why not Django?**
- Too heavyweight for API-only backend
- Django ORM not needed (ChromaDB/Qdrant handle storage)
- Slower than FastAPI

### Streaming Technology Decision

**Evaluated**: Server-Sent Events (SSE), WebSockets

**Decision**: Server-Sent Events (SSE)

**Rationale**:

**SSE Advantages**:
- ✅ One-way communication (perfect for LLM tokens)
- ✅ Automatic reconnection
- ✅ Native browser EventSource API
- ✅ Works over HTTP/2
- ✅ Simpler than WebSockets
- ✅ Better for RAG use case (server → client only)

**WebSockets Advantages**:
- ✅ Bi-directional communication
- ✅ Lower latency
- ✅ Binary data support

**Why SSE for ragged?**
- RAG streaming is primarily one-way (server sends tokens)
- User input happens via separate HTTP POST
- Simpler implementation and debugging
- Better fallback behaviour

**WebSocket use cases** (not needed for ragged):
- Real-time collaborative editing
- Gaming
- Chat with multiple participants
- Low-latency trading applications

## UX Patterns

### Progressive Disclosure

**Definition**: Reveal complexity gradually as users need it.

**4-Level Hierarchy for ragged**:

1. **Simple Mode** (default, 90% of users)
   - Single search box
   - Basic chat interface
   - Auto-selected best settings
   - Citations shown inline

2. **Advanced Mode** (toggle, 8% of users)
   - Adjustable retrieval settings (top-k, similarity threshold)
   - Model selection
   - Collection filtering
   - Temperature/max tokens

3. **Developer Mode** (toggle, 1.5% of users)
   - Query analysis (rewrites, decomposition)
   - Retrieved chunks with scores
   - Timing breakdown
   - Self-RAG confidence scores

4. **Expert Mode** (advanced settings, 0.5% of users)
   - Custom prompts
   - Embedding model selection
   - Chunking strategy overrides
   - Direct API access

**Implementation**:
- Start with Simple Mode only (v0.2)
- Add Advanced Mode (v0.3)
- Add Developer Mode (v0.4)
- Add Expert Mode (v1.0)

### Citation Patterns

**Research findings**:

1. **Inline citations** (like academic papers):
   - Best for narrative answers
   - Example: "The study found X [1] and Y [2]."
   - Users prefer numbers or superscripts

2. **Highlighted sources**:
   - Show which document chunks were used
   - Visual highlighting in source preview
   - Confidence scores for each chunk

3. **Expandable details**:
   - Click citation to see full context
   - Preview document page
   - Jump to source location

**ragged implementation**:
- v0.2: Basic inline citations with numbers
- v0.3: Enhanced citations with confidence scores
- v0.4: Retrieval details view (developer mode)
- v0.5: Document preview with highlights
- v1.0: Full citation management

### Streaming Response Patterns

**Best practices**:

1. **Visual feedback**:
   - Show typing indicator immediately
   - Stream tokens as they arrive
   - Indicate completion clearly

2. **Interruptibility**:
   - Allow users to stop generation
   - Save partial results if stopped
   - Clear "Stop" button during generation

3. **Error handling**:
   - Graceful degradation if streaming fails
   - Fall back to non-streaming
   - Clear error messages

**Implementation timeline**:
- v0.2: Basic streaming with EventSource
- v0.3: Add stop generation
- v0.4: Advanced error handling
- v1.0: Offline support with service workers

## Privacy-First Web Design

### Principles

1. **No CDN dependencies**:
   - Bundle all assets locally
   - No external JavaScript/CSS
   - Self-host fonts

2. **No telemetry**:
   - No analytics (Google Analytics, etc.)
   - No error tracking (Sentry, etc.)
   - No usage metrics sent externally

3. **Local storage only**:
   - IndexedDB for browser storage
   - No cookies (except session if auth enabled)
   - No localStorage of sensitive data

4. **Offline-first**:
   - Progressive Web App (PWA)
   - Service workers for caching
   - Works without internet (v1.0)

### Implementation

**v0.2-v0.4 (Gradio)**:
- Limited privacy controls
- Gradio analytics can be disabled
- Runs on localhost only

**v0.5-v1.0 (Svelte)**:
- Full privacy compliance
- No external requests
- PWA with offline support
- Self-hosted everything

## Performance Targets

### Bundle Size

**Target**: < 500KB total bundle (gzipped)

**Comparison**:
- React app: ~200KB (React + ReactDOM + typical deps)
- Vue app: ~100KB (Vue + Vue Router + Vuex)
- Svelte app: ~50KB (Svelte + SvelteKit + minimal deps)
- ragged target: **< 500KB** including:
  - Svelte runtime (~1.6KB)
  - Components (~100KB)
  - Dependencies (D3 for graphs, etc. ~200KB)
  - Assets (fonts, icons ~100KB)

**Strategy**:
- Lazy load graph visualisation (only load when needed)
- Tree-shaking to remove unused code
- Code splitting by route

### Lighthouse Score

**Target**: > 90 across all categories

**Categories**:
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 90 (if applicable)

**Optimisation**:
- v0.5: Initial Lighthouse audit
- v1.0: Optimised to > 90

### Time to Interactive (TTI)

**Target**: < 3 seconds on average hardware

**Strategy**:
- Minimize JavaScript bundle
- Optimise critical rendering path
- Lazy load non-essential features

## Accessibility

### WCAG 2.1 Compliance

**Target**: AA level minimum, AAA where possible

**Key requirements**:

1. **Keyboard Navigation**:
   - All features accessible via keyboard
   - Visible focus indicators
   - Logical tab order

2. **Screen Reader Support**:
   - ARIA labels for all interactive elements
   - Semantic HTML (proper heading hierarchy)
   - Alt text for images/icons

3. **Color Contrast**:
   - Minimum 4.5:1 for normal text
   - Minimum 3:1 for large text
   - Dark mode support

4. **Responsive Design**:
   - Works on mobile (320px width minimum)
   - Touch targets ≥ 44×44 pixels
   - Readable on all screen sizes

**Implementation timeline**:
- v0.2: Basic accessibility (keyboard nav, semantic HTML)
- v0.3: ARIA labels, improved contrast
- v0.4: Screen reader testing
- v1.0: Full WCAG 2.1 AA compliance

## Mobile Support

### Responsive Breakpoints

**Target devices**:
- Mobile: 320px - 767px
- Tablet: 768px - 1023px
- Desktop: 1024px+

**Mobile-first approach**:
1. Design for mobile first
2. Enhance for larger screens
3. Progressive enhancement

**v0.2-v0.4 (Gradio)**:
- Limited mobile support (Gradio responsive but not optimal)

**v0.5-v1.0 (Svelte)**:
- Full responsive design
- Touch-optimised interface
- Mobile-friendly graph visualisation

## Dark Mode

### Implementation Strategy

**User preference detection**:
```javascript
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
```

**Color palette**:
- Light mode: Default
- Dark mode: OLED-friendly blacks (for battery savings)

**Storage**:
- Save preference in localStorage
- Respect system preference by default
- Manual toggle available

**Timeline**:
- v0.3: Basic dark mode
- v0.5: Refined dark mode with Svelte
- v1.0: OLED-optimised dark mode

## Design System

### Component Library

**v0.5-v1.0**: Custom Svelte components

**Core components**:
- Button
- Input (text, textarea)
- Checkbox, Radio
- Select/Dropdown
- Modal/Dialog
- Tabs
- Accordion (for progressive disclosure)
- Toast/Notification
- Loading indicators
- Badge (for citations)

### Styling Approach

**Chosen**: Tailwind CSS

**Rationale**:
- Utility-first (no unused CSS)
- Excellent tree-shaking
- Consistent design tokens
- Dark mode support built-in
- Small bundle with purging

**Alternatives considered**:
- **CSS Modules**: Too manual, no design system
- **Styled Components**: Adds runtime overhead
- **Sass/SCSS**: Requires build step, larger bundles
- **Vanilla CSS**: No design tokens, hard to maintain

## Research Sources

### Academic Papers

1. **"Design Patterns for Conversational User Interfaces"** (2024)
   - Progressive disclosure in chat UIs
   - Citation visualisation techniques

2. **"Privacy-Preserving Web Applications"** (2024)
   - Offline-first architectures
   - Local-only processing patterns

### Industry Best Practices

1. **Open WebUI** (https://github.com/open-webui/open-webui)
   - Svelte/SvelteKit production patterns
   - FastAPI integration

2. **Verba** (https://github.com/weaviate/Verba)
   - RAG-specific UX patterns
   - Source attribution

3. **Kotaemon** (https://github.com/Cinnamon/kotaemon)
   - Gradio for rapid prototyping
   - Document-centric design

### Framework Documentation

1. **SvelteKit** (https://kit.svelte.dev/)
   - SSR and streaming
   - Service workers

2. **FastAPI** (https://fastapi.tiangolo.com/)
   - SSE implementation
   - WebSocket alternatives

3. **Tailwind CSS** (https://tailwindcss.com/)
   - Design system
   - Dark mode

## Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend (v0.2-v0.4) | Gradio | Rapid prototyping, Python-native |
| Frontend (v0.5-v1.0) | Svelte/SvelteKit | Performance, bundle size, production quality |
| Backend | FastAPI | Async, streaming, auto-docs |
| Streaming | SSE | One-way, simpler, auto-reconnect |
| Styling | Tailwind CSS | Utility-first, tree-shaking, dark mode |
| Offline | PWA + Service Workers | Privacy, offline-first |
| Accessibility | WCAG 2.1 AA | Legal compliance, inclusivity |
| Mobile | Responsive + Mobile-first | Universal access |
| Bundle Target | < 500KB gzipped | Fast load times |
| Lighthouse Target | > 90 all categories | Quality assurance |

## Timeline Integration

| Version | Web UI Features | Research Applied |
|---------|----------------|------------------|
| v0.1 | None (CLI only) | N/A |
| v0.2 | Basic Gradio UI | SSE streaming, simple mode |
| v0.3 | Enhanced Gradio | Progressive disclosure, citations |
| v0.4 | Developer mode | UX patterns for technical users |
| v0.5 | Svelte rebuild | Performance, responsive, graphs |
| v1.0 | Production PWA | Accessibility, offline, monitoring |

---

**Conclusion**: This research informed a pragmatic approach—use Gradio for fast iteration (v0.2-v0.4), then rebuild with Svelte for production (v0.5-v1.0). This balances development speed with long-term quality.

**Next Steps**: Implement v0.2 basic Gradio interface to validate UX patterns with real users before committing to Svelte rebuild.
