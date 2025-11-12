# Streaming Technology for ragged

**Last Updated**: 2025-11-08
**Status**: Planning

---

## Overview

This document explains the streaming strategy for ragged's web interface, covering real-time token streaming from LLMs and progress updates during document processing.

## Technology Choice: Server-Sent Events (SSE)

**Selected**: SSE (Server-Sent Events)
**Alternative**: WebSockets
**Decision**: SSE is the better fit for RAG systems

---

## SSE vs WebSockets Comparison

### Server-Sent Events (SSE) ✅

#### Strengths

1. **One-Way Communication**
   - Server → Client streaming
   - Perfect for LLM token streaming
   - Simpler than bidirectional

2. **Native Browser Support**
   - No additional libraries needed
   - Works in all modern browsers
   - Built-in reconnection logic

3. **Simpler Protocol**
   - HTTP-based (no protocol upgrade)
   - Works with existing infrastructure
   - Easier to debug (standard HTTP tools)

4. **Better for RAG Use Case**
   - LLM generates, client receives
   - Progress updates flow one way
   - No need for client → server during streaming

5. **Automatic Reconnection**
   - Browser handles reconnects
   - Configurable retry intervals
   - More robust for long responses

#### Limitations

1. **One-Way Only**
   - Can't send during active stream
   - Need separate endpoint for new queries
   - Not an issue for RAG

2. **HTTP/1.1 Connection Limits**
   - Browser limit: ~6 concurrent connections per domain
   - Rarely an issue in practice
   - HTTP/2 solves this

3. **Text-Only**
   - No binary streaming
   - Not needed for tokens/JSON

#### When to Use SSE

✅ **Perfect for:**
- LLM token streaming
- Progress updates
- Server → Client notifications
- Long-running processes
- **RAG systems** ✅

❌ **Not ideal for:**
- Real-time chat (bidirectional)
- Gaming
- Live collaboration
- Binary data streaming

---

### WebSockets

#### Strengths

1. **Bidirectional**
   - Client ↔ Server communication
   - Full-duplex channel
   - Good for interactive apps

2. **Binary Support**
   - Can send binary data
   - More efficient for some use cases

3. **Lower Latency**
   - Single persistent connection
   - No HTTP overhead per message

#### Limitations

1. **More Complex**
   - Protocol upgrade required
   - More implementation complexity
   - Harder to debug

2. **No Automatic Reconnection**
   - Must implement yourself
   - More code to maintain
   - Potential for bugs

3. **Overkill for RAG**
   - Bidirectional not needed
   - Added complexity without benefit

#### When to Use WebSockets

✅ **Good for:**
- Real-time chat
- Gaming
- Live collaboration
- Interactive agents with actions

❌ **Not needed for:**
- One-way streaming
- **Simple RAG** ✅

---

## SSE Implementation with FastAPI

### Backend Implementation

```python
# ragged/web/streaming.py
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
from ragged import RAGPipeline
import asyncio
import json

app = FastAPI()
pipeline = RAGPipeline.from_config()

@app.get("/api/query/stream")
async def stream_query(q: str, collection: str = "default"):
    """Stream RAG response with token-by-token generation."""

    async def event_generator():
        """Generate SSE events for streaming response."""

        # Phase 1: Retrieval
        yield {
            "event": "status",
            "data": json.dumps({
                "stage": "retrieval",
                "message": "Searching documents..."
            })
        }

        # Get relevant chunks
        results = await pipeline.retrieve(q, collection=collection)

        yield {
            "event": "retrieval_complete",
            "data": json.dumps({
                "num_chunks": len(results),
                "top_score": results[0].score if results else 0
            })
        }

        # Phase 2: Generation with streaming
        yield {
            "event": "status",
            "data": json.dumps({
                "stage": "generation",
                "message": "Generating response..."
            })
        }

        full_response = ""

        async for token in pipeline.generate_stream(q, results):
            # Stream individual tokens
            yield {
                "event": "token",
                "data": token
            }
            full_response += token

            # Small delay to prevent overwhelming client
            await asyncio.sleep(0.01)

        # Phase 3: Send sources
        sources = [
            {
                "document": r.chunk.document_id,
                "score": r.score,
                "text": r.chunk.text[:200],
                "metadata": r.chunk.metadata
            }
            for r in results[:5]
        ]

        yield {
            "event": "sources",
            "data": json.dumps(sources)
        }

        # Phase 4: Complete
        yield {
            "event": "complete",
            "data": json.dumps({
                "total_tokens": len(full_response.split()),
                "duration_ms": 1234  # TODO: actual timing
            })
        }

    return EventSourceResponse(event_generator())
```

### Frontend Implementation (Vanilla JS)

```javascript
// For Gradio (v0.2-v0.4) - embedded in Python
function queryWithStreaming(query, collection) {
  const eventSource = new EventSource(
    `/api/query/stream?q=${encodeURIComponent(query)}&collection=${collection}`
  );

  let responseText = '';
  let sources = [];

  eventSource.addEventListener('status', (e) => {
    const data = JSON.parse(e.data);
    updateStatus(data.stage, data.message);
  });

  eventSource.addEventListener('token', (e) => {
    responseText += e.data;
    updateResponse(responseText);
  });

  eventSource.addEventListener('sources', (e) => {
    sources = JSON.parse(e.data);
    displaySources(sources);
  });

  eventSource.addEventListener('complete', (e) => {
    const data = JSON.parse(e.data);
    console.log(`Completed in ${data.duration_ms}ms`);
    eventSource.close();
  });

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
    showError('Connection lost. Please try again.');
  };
}
```

### Frontend Implementation (Svelte - v0.5+)

```svelte
<!-- QueryStream.svelte -->
<script lang="ts">
  import { onDestroy } from 'svelte';

  export let query: string;
  export let collection: string = 'default';

  let responseText = '';
  let sources: Source[] = [];
  let status = '';
  let streaming = false;
  let eventSource: EventSource | null = null;

  async function startStreaming() {
    streaming = true;
    responseText = '';
    sources = [];

    const url = `/api/query/stream?q=${encodeURIComponent(query)}&collection=${collection}`;
    eventSource = new EventSource(url);

    eventSource.addEventListener('status', (e) => {
      const data = JSON.parse(e.data);
      status = data.message;
    });

    eventSource.addEventListener('token', (e) => {
      responseText += e.data;
    });

    eventSource.addEventListener('sources', (e) => {
      sources = JSON.parse(e.data);
    });

    eventSource.addEventListener('complete', (e) => {
      streaming = false;
      status = 'Complete';
      eventSource?.close();
    });

    eventSource.onerror = () => {
      streaming = false;
      status = 'Error occurred';
      eventSource?.close();
    };
  }

  onDestroy(() => {
    eventSource?.close();
  });
</script>

<div class="stream-container">
  <div class="status">{status}</div>

  <div class="response">
    {responseText}
    {#if streaming}
      <span class="cursor">▊</span>
    {/if}
  </div>

  {#if sources.length > 0}
    <div class="sources">
      <h3>Sources ({sources.length})</h3>
      {#each sources as source}
        <div class="source">
          <strong>{source.document}</strong>
          <span class="score">{source.score.toFixed(2)}</span>
          <p>{source.text}...</p>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .cursor {
    animation: blink 1s infinite;
  }

  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
</style>
```

---

## SSE Event Types for ragged

### Standard Events

| Event | Data | Purpose |
|-------|------|---------|
| `status` | `{stage, message}` | Progress updates |
| `token` | `string` | Individual LLM tokens |
| `sources` | `Source[]` | Retrieved chunks |
| `complete` | `{total_tokens, duration_ms}` | Stream finished |
| `error` | `{code, message}` | Error occurred |

### Extended Events (v0.4+)

| Event | Data | Purpose |
|-------|------|---------|
| `query_rewrite` | `{original, rewritten[]}` | Show query expansion |
| `retrieval_scores` | `{chunk_id, score}[]` | Chunk scores |
| `reranking` | `{before[], after[]}` | Reranking changes |
| `confidence` | `{score, threshold}` | Self-RAG confidence |

---

## Error Handling

### Connection Lost

```javascript
let reconnectAttempts = 0;
const MAX_RECONNECTS = 3;

eventSource.onerror = (error) => {
  if (reconnectAttempts < MAX_RECONNECTS) {
    reconnectAttempts++;
    console.log(`Reconnecting... (${reconnectAttempts}/${MAX_RECONNECTS})`);

    setTimeout(() => {
      // Retry connection
      eventSource = new EventSource(url);
    }, 1000 * reconnectAttempts);
  } else {
    console.error('Max reconnection attempts reached');
    showError('Unable to connect. Please refresh and try again.');
    eventSource.close();
  }
};
```

### Server Errors

```python
# Backend error handling
async def event_generator():
    try:
        # Normal streaming...
        async for token in pipeline.generate_stream(q, results):
            yield {"event": "token", "data": token}

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({
                "code": "GENERATION_ERROR",
                "message": str(e)
            })
        }
```

---

## Progressive Updates

### Document Upload Progress

```python
@app.post("/api/upload/stream")
async def stream_upload(files: List[UploadFile]):
    """Stream progress during document processing."""

    async def upload_progress():
        total = len(files)

        for i, file in enumerate(files):
            # Processing update
            yield {
                "event": "processing",
                "data": json.dumps({
                    "current": i + 1,
                    "total": total,
                    "filename": file.filename
                })
            }

            # Process file
            await pipeline.ingest_document(file)

            # Completion update
            yield {
                "event": "file_complete",
                "data": json.dumps({
                    "filename": file.filename,
                    "chunks": 42,  # TODO: actual count
                    "status": "success"
                })
            }

        yield {
            "event": "complete",
            "data": json.dumps({"total_processed": total})
        }

    return EventSourceResponse(upload_progress())
```

---

## Performance Considerations

### Token Batching

```python
# Instead of one token at a time (expensive)
async for token in llm.generate():
    yield {"event": "token", "data": token}  # Many small events

# Batch tokens for efficiency
buffer = []
BATCH_SIZE = 5

async for token in llm.generate():
    buffer.append(token)

    if len(buffer) >= BATCH_SIZE:
        yield {
            "event": "token",
            "data": "".join(buffer)
        }
        buffer = []

# Send remaining
if buffer:
    yield {"event": "token", "data": "".join(buffer)}
```

### Connection Limits

```javascript
// Limit concurrent streams
class StreamManager {
  constructor(maxStreams = 2) {
    this.activeStreams = 0;
    this.maxStreams = maxStreams;
    this.queue = [];
  }

  async startStream(query) {
    if (this.activeStreams >= this.maxStreams) {
      // Queue or reject
      throw new Error('Too many active streams');
    }

    this.activeStreams++;
    try {
      await doStream(query);
    } finally {
      this.activeStreams--;
    }
  }
}
```

---

## Testing Streaming

### Manual Testing

```bash
# Test SSE endpoint with curl
curl -N http://localhost:8000/api/query/stream?q=test

# Should see:
# event: status
# data: {"stage":"retrieval","message":"Searching..."}
#
# event: token
# data: The
#
# event: token
# data:  answer
# ...
```

### Automated Testing

```python
# tests/test_streaming.py
import pytest
from fastapi.testclient import TestClient
from ragged.web import app

def test_sse_stream():
    client = TestClient(app)

    with client.stream("GET", "/api/query/stream?q=test") as response:
        events = []

        for line in response.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                events.append((event_type, data))

        # Verify event sequence
        assert events[0][0] == "status"
        assert events[-1][0] == "complete"
        assert any(e[0] == "token" for e in events)
```

---

## Browser Compatibility

### SSE Support

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Since Chrome 6 |
| Firefox | ✅ Full | Since Firefox 6 |
| Safari | ✅ Full | Since Safari 5 |
| Edge | ✅ Full | Since Edge 79 |
| IE | ❌ None | Use polyfill or fallback |

### Polyfill for Old Browsers

```javascript
// Use event-source-polyfill for IE11
import { EventSourcePolyfill } from 'event-source-polyfill';

const EventSource = window.EventSource || EventSourcePolyfill;
```

---

## Privacy Considerations

### No External Connections

```python
# All streaming is local
SSE_ENDPOINT = "http://127.0.0.1:8000/api/query/stream"

# Never:
# - Stream to external services
# - Send tokens to analytics
# - Log user queries externally
```

### HTTPS for Production

```python
# v1.0: Enable HTTPS for localhost
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert.pem', 'key.pem')

uvicorn.run(app, host="127.0.0.1", port=8443, ssl=ssl_context)
```

---

## Comparison: SSE vs Long Polling vs WebSockets

| Feature | SSE | Long Polling | WebSockets |
|---------|-----|--------------|------------|
| **Latency** | Low | Medium | **Lowest** |
| **Efficiency** | High | Low | **Highest** |
| **Simplicity** | **Easiest** | Easy | Complex |
| **Bidirectional** | No | No | **Yes** |
| **Reconnection** | **Automatic** | Manual | Manual |
| **Browser Support** | **Excellent** | Universal | Good |
| **RAG Suitability** | **Perfect** ✅ | Poor | Overkill |

**Winner for ragged**: **SSE** ✅

---

## Implementation Timeline

### v0.2: Basic SSE
- [ ] Install sse-starlette
- [ ] Implement token streaming endpoint
- [ ] Add status updates
- [ ] Test with Gradio frontend

### v0.3: Enhanced Streaming
- [ ] Add retrieval progress events
- [ ] Implement error handling
- [ ] Add reconnection logic
- [ ] Test with slow connections

### v0.4: Debug Streaming
- [ ] Add query rewrite events
- [ ] Add reranking events
- [ ] Add confidence score events
- [ ] Stream timing data

### v0.5: Production Streaming
- [ ] Optimise token batching
- [ ] Add Svelte SSE client
- [ ] Implement connection pooling
- [ ] Add comprehensive error handling

---

## Conclusion

**SSE is the optimal choice for ragged because:**

1. ✅ Perfect for one-way LLM streaming
2. ✅ Simpler than WebSockets
3. ✅ Native browser support
4. ✅ Automatic reconnection
5. ✅ Works well with FastAPI

**Implementation priority**: v0.2 (essential for good UX)

**Next Steps**: See [offline-capability.md](./offline-capability.md) for PWA implementation.
