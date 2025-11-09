# v0.2 Web UI: Basic Gradio Interface

**Timeline**: +1 week to v0.2 implementation
**Technology**: Gradio + FastAPI
**Complexity**: Low-Medium

---

## Goals

Provide a simple web interface for non-technical users to:
- Upload documents
- Query their knowledge base
- View streaming responses
- See basic source citations

## Technology Stack

**Backend**: FastAPI
- `fastapi[all]` - Web framework
- `sse-starlette` - Server-Sent Events for streaming
- `python-multipart` - File upload support

**Frontend**: Gradio
- `gradio` - Python-based UI framework
- No JavaScript knowledge required
- Rapid prototyping

## Features

### Core Features

1. **Chat Interface**
   - Message history display
   - Text input with send button
   - Streaming token display
   - Simple, clean layout

2. **Document Upload**
   - File picker interface
   - Drag-and-drop support (Gradio built-in)
   - Format validation (PDF, TXT, MD, HTML, DOCX)
   - Upload progress feedback

3. **Collection Management**
   - Dropdown selector
   - Shows available collections
   - Create new collection (simple form)

4. **Basic Citations**
   - Document filename
   - Page number (if available)
   - Confidence score
   - Link to original document

### Streaming

**SSE Implementation**:
```python
@app.get("/api/query/stream")
async def stream_query(q: str, collection: str = "default"):
    async def event_generator():
        # Status
        yield {"event": "status", "data": "Retrieving..."}

        # Tokens
        async for token in pipeline.generate_stream(q):
            yield {"event": "token", "data": token}

        # Sources
        yield {"event": "sources", "data": json.dumps(sources)}

    return EventSourceResponse(event_generator())
```

## Implementation Guide

### 1. FastAPI Backend Setup

```python
# ragged/web/app.py
from fastapi import FastAPI, UploadFile
from sse_starlette.sse import EventSourceResponse
import uvicorn

app = FastAPI(title="ragged API")

@app.post("/api/upload")
async def upload_documents(files: List[UploadFile], collection: str):
    """Upload documents to collection."""
    results = []
    for file in files:
        doc_id = await pipeline.ingest(file, collection=collection)
        results.append({"id": doc_id, "filename": file.filename})
    return {"uploaded": len(results), "documents": results}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### 2. Gradio Frontend

```python
# ragged/web/gradio_ui.py
import gradio as gr
import requests

def query_handler(message, history, collection):
    """Handle query with streaming."""
    # SSE streaming to Gradio chat
    url = f"http://localhost:8000/api/query/stream?q={message}&collection={collection}"
    response_text = ""
    sources = []

    # Note: Gradio streaming integration
    # Gradio will handle SSE display

    return response_text, sources

with gr.Blocks(title="ragged") as demo:
    gr.Markdown("# ragged - Ask Your Documents")

    with gr.Row():
        collection = gr.Dropdown(
            choices=["default", "research", "notes"],
            value="default",
            label="Collection"
        )

    chatbot = gr.ChatInterface(
        query_handler,
        additional_inputs=[collection],
        examples=["What is RAG?", "Summarize key findings"]
    )

    with gr.Accordion("Upload Documents", open=False):
        file_upload = gr.Files(label="Select files")
        upload_btn = gr.Button("Upload")

demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
```

## Success Criteria

- [ ] Users can access UI at http://localhost:7860
- [ ] Document upload works for PDF, TXT, MD
- [ ] Query streaming works smoothly
- [ ] Response time < 5 seconds for simple queries
- [ ] Citations display correctly
- [ ] Works offline (localhost only)
- [ ] No external dependencies

## Limitations (Acceptable in v0.2)

- No advanced settings (temperature, top-k)
- No conversation history persistence
- No document preview
- Basic error messages only
- Limited customization

These will be addressed in v0.3+.

## Testing

```bash
# Start backend
python -m ragged.web.app &

# Start Gradio UI
python -m ragged.web.gradio_ui

# Manual testing:
# 1. Visit http://localhost:7860
# 2. Upload a document
# 3. Query the document
# 4. Verify streaming works
# 5. Check citations appear
```

## Timeline

**Week 1**: Backend + Streaming
- Set up FastAPI
- Implement SSE endpoints
- Test streaming

**Week 2**: Gradio Integration
- Build chat interface
- Add file upload
- Test end-to-end
- Documentation

**Total**: +1 week to v0.2 schedule
