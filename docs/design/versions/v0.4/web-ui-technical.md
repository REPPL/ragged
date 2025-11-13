# v0.4 Web UI: Developer Mode & Technical Features

**Timeline**: Part of v0.4 (4-5 weeks)
**Technology**: Gradio (with developer mode)
**Focus**: Query debugging, performance metrics, technical visibility

---

## Goals

Provide deep system visibility for developers and technical users.

## New Features

### 1. Developer Mode Toggle

```python
developer_mode = gr.Checkbox(label="🔍 Developer Mode", value=False)

@gr.render(inputs=[developer_mode])
def show_developer_panel(enabled):
    if enabled:
        with gr.Column():
            gr.Markdown("### Query Analysis")
            query_details = gr.JSON(label="Query Rewriting")

            gr.Markdown("### Retrieved Chunks")
            chunks_table = gr.Dataframe(
                headers=["Rank", "Document", "Score", "Reranked", "Preview"],
                label="Top Chunks"
            )

            gr.Markdown("### Performance Metrics")
            timing_chart = gr.BarPlot(label="Latency Breakdown")
```

### 2. Query Inspector

Display:
- Original query
- Rewritten queries (if query expansion used)
- Query decomposition (for complex queries)
- Strategy selection reasoning (Adaptive RAG)

### 3. Retrieval Details View

Show for each retrieved chunk:
- Document source
- Chunk index
- Initial score (vector/keyword)
- Reranked score
- Text preview
- Metadata

### 4. Performance Dashboard

Display timing breakdown:
- Query processing: Xms
- Vector retrieval: Xms
- Keyword retrieval: Xms (if hybrid)
- Reranking: Xms
- LLM generation: Xms
- **Total**: Xms

### 5. Self-RAG Visualization (when enabled)

- Iteration count
- Confidence progression
- Retrieval decisions
- Self-assessment results

## Backend Changes

Enhanced debug info in responses:
```python
@app.get("/api/query/stream")
async def stream_query(q: str, debug: bool = False):
    if debug:
        # Include debug information
        yield {
            "event": "debug_query",
            "data": json.dumps({
                "original": q,
                "rewritten": rewritten_queries,
                "strategy": "adaptive"
            })
        }

        yield {
            "event": "debug_chunks",
            "data": json.dumps(chunks_with_scores)
        }

        yield {
            "event": "debug_timing",
            "data": json.dumps(timing_breakdown)
        }
```

## Success Criteria

- [ ] Developer mode toggleable
- [ ] Query inspector shows rewrites
- [ ] Retrieval details display scores
- [ ] Performance metrics accurate
- [ ] Timing overhead < 10ms
- [ ] All debug info visible when enabled

## Timeline

Part of v0.4 4-5 week schedule.
