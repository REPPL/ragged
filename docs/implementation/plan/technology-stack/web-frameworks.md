# Web Framework Choices for ragged

**Last Updated**: 2025-11-08
**Status**: Planning

---

## Overview

This document explains the web framework strategy for ragged across versions v0.2 through v1.0, balancing rapid prototyping with production quality while maintaining privacy-first principles.

## Evolution Strategy: Prototype → Production

### Phase 1: Rapid Prototyping (v0.2-v0.4)
**Framework**: Gradio
**Timeline**: v0.2 through v0.4
**Purpose**: Validate UX and functionality quickly

### Phase 2: Production Quality (v0.5-v1.0)
**Framework**: Svelte/SvelteKit
**Timeline**: v0.5 through v1.0
**Purpose**: Production-ready interface with optimal performance

---

## Backend: FastAPI (v0.2+)

### Why FastAPI?

**Selected for all versions v0.2 onwards**

#### Strengths
1. **Native Async Support**
   - Essential for SSE streaming
   - Handles concurrent requests efficiently
   - Non-blocking LLM inference

2. **Auto-Generated Documentation**
   - Swagger/OpenAPI UI out of the box
   - Interactive API testing
   - Reduces documentation burden

3. **Type Safety**
   - Pydantic integration
   - Request/response validation
   - Better IDE support

4. **SSE Support**
   - Works excellently with sse-starlette
   - Token-by-token streaming for LLMs
   - Better than Flask for streaming

5. **Modern & Fast**
   - Performance comparable to Node.js
   - Growing ecosystem
   - Well-maintained

#### Code Example

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio

app = FastAPI(
    title="ragged API",
    description="Privacy-first local RAG system",
    version="0.2.0"
)

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """Query the RAG system with streaming response."""

    async def event_generator():
        async for token in pipeline.query_stream(request.query):
            yield {
                "event": "token",
                "data": token
            }

        yield {
            "event": "complete",
            "data": json.dumps({"sources": sources})
        }

    return EventSourceResponse(event_generator())
```

#### Alternatives Considered

**Flask**
- ❌ Less modern async support
- ❌ Manual API documentation
- ✅ More mature ecosystem
- **Verdict**: FastAPI better for RAG streaming

**Django**
- ❌ Too heavyweight for our needs
- ❌ Opinionated structure
- ✅ Excellent for complex apps
- **Verdict**: Overkill for ragged

**Starlette** (FastAPI's foundation)
- ✅ Lighter weight
- ❌ No auto-documentation
- ❌ More boilerplate
- **Verdict**: FastAPI provides better DX

---

## Frontend Phase 1: Gradio (v0.2-v0.4)

### Why Gradio for Prototyping?

**Use for**: v0.2, v0.3, v0.4
**Discard in**: v0.5 (clean rebuild)

#### Strengths

1. **Pure Python**
   - No JavaScript knowledge needed
   - Perfect for Python-focused teams
   - Rapid iteration

2. **Built for AI/ML**
   - Native support for streaming
   - File upload components
   - Chat interfaces out of the box

3. **Zero Frontend Complexity**
   - No build tools
   - No npm/package management
   - Single Python file can define entire UI

4. **Fast Development**
   - Simple chat interface: ~50 lines
   - Quick to modify and test
   - Excellent for validation

#### Limitations

1. **Limited Customization**
   - Constrained to Gradio components
   - Hard to create custom layouts
   - Styling options limited

2. **Performance Concerns**
   - Larger bundle than custom solutions
   - Not optimised for production

3. **Advanced Features Difficult**
   - Graph visualization challenging
   - Complex state management awkward
   - Developer tools integration limited

4. **Not Production-Grade**
   - UI polish limited
   - Professional design system needed
   - Mobile experience suboptimal

#### When to Use Gradio

✅ **Good for:**
- Rapid prototyping
- Internal tools
- Proof of concepts
- Python developer audiences
- Quick demos

❌ **Not good for:**
- Production applications
- Custom branding
- Complex UX requirements
- Mobile-first apps

#### Example Implementation

```python
import gradio as gr
from ragged import RAGPipeline

pipeline = RAGPipeline.from_config("config.yaml")

def query_with_sources(message, history, collection):
    """Query handler with chat history."""
    response = pipeline.query(
        message,
        collection=collection,
        context=history
    )

    # Format sources
    sources_text = "\n\n📚 **Sources:**\n"
    for source in response.sources:
        sources_text += f"- {source.document} (score: {source.score:.2f})\n"

    return response.text + sources_text

# Build UI
with gr.Blocks(title="ragged - Local RAG") as demo:
    gr.Markdown("# ragged - Ask Your Documents")

    with gr.Row():
        collection = gr.Dropdown(
            choices=pipeline.list_collections(),
            label="Collection",
            value="default"
        )

    chatbot = gr.ChatInterface(
        query_with_sources,
        additional_inputs=[collection],
        examples=[
            "What is RAG?",
            "Summarize the main findings",
            "Compare approaches mentioned"
        ]
    )

demo.launch(
    server_name="127.0.0.1",
    server_port=7860,
    share=False  # Privacy: never share publicly
)
```

---

## Frontend Phase 2: Svelte/SvelteKit (v0.5-v1.0)

### Why Svelte for Production?

**Use for**: v0.5, v1.0
**Clean rebuild in**: v0.5 (no migration from Gradio)

#### Strengths

1. **Smallest Bundle Size**
   - Svelte runtime: **1.6 KB** (gzipped)
   - React: ~40 KB, Vue: ~30 KB
   - **Privacy benefit**: Less data to download
   - Faster on low-bandwidth connections

2. **Best Performance**
   - Compiles to vanilla JavaScript
   - No virtual DOM overhead
   - Fastest framework in benchmarks
   - Better for older devices

3. **Clean Syntax**
   - Less boilerplate than React
   - Easier to read and maintain
   - Reactive by default
   - Great developer experience

4. **Offline-First**
   - SvelteKit has excellent SSR/SSG
   - Service worker integration
   - Perfect for PWA
   - Aligns with privacy goals

5. **Growing AI Ecosystem**
   - Vercel AI SDK supports Svelte
   - Good streaming components
   - Active community

6. **No Tracking**
   - No telemetry in core framework
   - Privacy-friendly by default
   - No surprise external calls

#### Code Example

```svelte
<!-- QueryInterface.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import type { Message, Source } from '$lib/types';

  let messages: Message[] = [];
  let input = '';
  let sources: Source[] = [];
  let streaming = false;

  async function sendQuery() {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    messages = [...messages, userMessage];
    input = '';
    streaming = true;

    // SSE streaming
    const eventSource = new EventSource(
      `/api/query?q=${encodeURIComponent(userMessage.content)}`
    );

    let assistantMessage = { role: 'assistant', content: '' };
    messages = [...messages, assistantMessage];

    eventSource.addEventListener('token', (e) => {
      assistantMessage.content += e.data;
      messages = messages; // Trigger reactivity
    });

    eventSource.addEventListener('sources', (e) => {
      sources = JSON.parse(e.data);
      streaming = false;
      eventSource.close();
    });
  }
</script>

<div class="chat-container">
  <div class="messages">
    {#each messages as message}
      <div class="message {message.role}">
        {message.content}
      </div>
    {/each}

    {#if streaming}
      <div class="streaming-indicator">●●●</div>
    {/if}
  </div>

  <form on:submit|preventDefault={sendQuery}>
    <input
      bind:value={input}
      placeholder="Ask a question..."
      disabled={streaming}
    />
    <button type="submit" disabled={streaming}>
      Send
    </button>
  </form>

  {#if sources.length > 0}
    <div class="sources">
      <h3>Sources</h3>
      {#each sources as source}
        <div class="source">
          <span class="filename">{source.document}</span>
          <span class="score">{source.score.toFixed(2)}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  /* Scoped styles - no CSS conflicts */
  .chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
  }

  .message {
    padding: 0.75rem;
    margin: 0.5rem 0;
    border-radius: 8px;
  }

  .message.user {
    background: #e3f2fd;
    margin-left: 20%;
  }

  .message.assistant {
    background: #f5f5f5;
    margin-right: 20%;
  }
</style>
```

---

## Framework Comparison Table

| Feature | Gradio | React | Vue | Svelte | HTMX |
|---------|--------|-------|-----|--------|------|
| **Bundle Size** | N/A (Python) | ~40 KB | ~30 KB | **1.6 KB** ✅ | ~10 KB |
| **Performance** | Medium | Good | Good | **Excellent** ✅ | Excellent |
| **Learning Curve** | **Very Easy** ✅ | Medium | Easy | Easy | **Very Easy** ✅ |
| **Python Integration** | **Native** ✅ | External | External | External | Server-side |
| **AI/ML Ecosystem** | **Excellent** ✅ | **Excellent** ✅ | Good | Growing | Limited |
| **Customization** | Limited | **Excellent** ✅ | **Excellent** ✅ | **Excellent** ✅ | Limited |
| **SSE Streaming** | Built-in | Manual | Manual | Manual | Manual |
| **Offline/PWA** | No | Yes | Yes | **Excellent** ✅ | Yes |
| **Production Ready** | No | **Yes** ✅ | **Yes** ✅ | **Yes** ✅ | **Yes** ✅ |
| **Privacy Focus** | Good | Neutral | Neutral | **Excellent** ✅ | **Excellent** ✅ |

### Scoring Summary

**Gradio**: Best for v0.2-v0.4 prototyping
- ✅ Fastest development
- ✅ Python-only
- ❌ Limited production capability

**Svelte**: Best for v0.5-v1.0 production
- ✅ Best performance
- ✅ Smallest bundle (privacy win)
- ✅ Excellent offline support
- ✅ Clean, maintainable code

**React**: Strong alternative
- ✅ Largest ecosystem
- ✅ Most developers know it
- ❌ Larger bundle
- ❌ More boilerplate

**Vue**: Balanced option
- ✅ Good DX
- ✅ Decent ecosystem
- ❌ Smaller than React
- ❌ Larger than Svelte

**HTMX**: Simplicity-focused
- ✅ Minimal JavaScript
- ✅ Server-side rendering
- ❌ Limited for complex UIs
- ❌ Small ecosystem for RAG

---

## Alternative: Stay with Gradio Through v1.0?

### Pros
- ✅ Faster overall development
- ✅ No frontend expertise needed
- ✅ Consistent experience

### Cons
- ❌ Limited customization forever
- ❌ Suboptimal user experience
- ❌ Difficult to attract contributors
- ❌ Not competitive with alternatives

### Recommendation

**No** - Rebuild with Svelte in v0.5

**Rationale**:
1. Gradio limitations become apparent by v0.4
2. GraphRAG visualization needs custom UI
3. Production polish important for v1.0
4. Better user experience attracts users
5. API available for those who prefer custom UIs

---

## Migration Strategy (v0.4 → v0.5)

### Approach: Clean Rebuild (Not Migration)

**Since breaking changes are OK before v1.0:**

1. **Build Svelte UI from scratch**
   - Use lessons learned from Gradio
   - Implement same features, better UX
   - No compatibility shims needed

2. **Run Both Temporarily**
   - Gradio on port 7860 (deprecated)
   - Svelte on port 3000 (new default)
   - Clear communication to users

3. **Remove Gradio in v0.5**
   - Clean removal, no migration code
   - Update documentation
   - API remains for custom UIs

4. **API-First Design**
   - Users preferring Gradio can build their own
   - All functionality available via FastAPI
   - We provide reference implementation

---

## Technology Decision Timeline

| Version | Backend | Frontend | Reason |
|---------|---------|----------|--------|
| **v0.1** | None | CLI only | Core functionality first |
| **v0.2** | FastAPI | Gradio | Rapid prototyping |
| **v0.3** | FastAPI | Gradio | Feature validation |
| **v0.4** | FastAPI | Gradio | Technical features testing |
| **v0.5** | FastAPI | **Svelte** ✅ | Production quality |
| **v1.0** | FastAPI | Svelte | Stable release |

---

## Implementation Checklist

### v0.2: FastAPI + Gradio Setup
- [ ] Install FastAPI, sse-starlette
- [ ] Install Gradio
- [ ] Create basic chat interface
- [ ] Implement SSE streaming endpoint
- [ ] Add document upload
- [ ] Test offline capability (localhost)

### v0.5: Svelte Rebuild
- [ ] Create SvelteKit project
- [ ] Set up TypeScript
- [ ] Implement chat interface
- [ ] Add SSE streaming client
- [ ] Build graph visualization
- [ ] Configure service worker
- [ ] Optimise bundle size
- [ ] Test PWA functionality

---

## Privacy Considerations

### No External Dependencies
```json
// package.json - v0.5+
{
  "dependencies": {
    "@sveltejs/kit": "^1.0.0",
    // NO analytics
    // NO tracking
    // NO CDN dependencies
    // ALL assets bundled
  }
}
```

### Self-Hosted Assets
- No Google Fonts (bundle locally)
- No CDN JavaScript libraries
- No external API calls
- All processing client-side or local server

### Offline Capability
```javascript
// service-worker.js
const CACHE_NAME = 'ragged-v0.5';
const OFFLINE_ASSETS = [
  '/',
  '/assets/bundle.js',
  '/assets/bundle.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(OFFLINE_ASSETS))
  );
});
```

---

## Conclusion

**Strategy Summary:**
1. **v0.2-v0.4**: Prototype with Gradio (speed)
2. **v0.5**: Clean rebuild with Svelte (quality)
3. **v1.0**: Production hardening with Svelte (stability)

**Key Principle**: Breaking changes OK before v1.0 allows us to choose the best tool for each phase without migration burden.

**Next Steps**: See [streaming.md](./streaming.md) for SSE implementation details.
