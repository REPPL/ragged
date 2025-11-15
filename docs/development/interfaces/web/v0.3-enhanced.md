# v0.3 Web UI: Enhanced Gradio with Progressive Disclosure

**Timeline**: Part of v0.3 (3-4 weeks)
**Technology**: Gradio (enhanced)
**Focus**: Progressive disclosure, better citations, conversation history

---

## Goals

Add progressive disclosure and enhanced features while maintaining simplicity.

## New Features

### 1. Progressive Disclosure

**Advanced Settings Panel** (collapsible):
```python
with gr.Accordion("Advanced Settings", open=False):
    temperature = gr.Slider(0, 1, 0.7, label="Temperature")
    top_k = gr.Slider(1, 20, 5, label="Number of sources")
    search_strategy = gr.Radio(
        ["vector", "keyword", "hybrid"],
        value="hybrid",
        label="Search Strategy"
    )
```

### 2. Enhanced Citations

Display more information:
- Confidence score (0.0-1.0)
- Page number (when available)
- Text snippet (first 100 chars)
- Metadata (author, date if available)

### 3. Conversation History

Store and retrieve previous conversations:
```python
# Save to IndexedDB (client-side)
# or local SQLite database
conversations_db = {
    "id": "conv-123",
    "timestamp": datetime.now(),
    "messages": [...]
}
```

### 4. Collection Management UI

```python
with gr.Tab("Collections"):
    with gr.Row():
        new_collection = gr.Textbox(label="New collection name")
        create_btn = gr.Button("Create")

    collections_list = gr.Dataframe(
        headers=["Name", "Documents", "Created"],
        label="Your Collections"
    )

    rename_collection = gr.Textbox(label="Rename to")
    rename_btn = gr.Button("Rename")
    delete_btn = gr.Button("Delete", variant="stop")
```

## Implementation Highlights

- Progressive disclosure via Gradio Accordion
- Local storage for conversation history
- Enhanced citation formatting
- Collection CRUD operations

## Success Criteria

- [ ] Advanced settings hidden by default
- [ ] Users can find advanced settings easily
- [ ] Conversation history persists
- [ ] Citations show confidence + page numbers
- [ ] Collections manageable via UI

## Timeline

Part of v0.3 3-4 week schedule (no additional time needed).
