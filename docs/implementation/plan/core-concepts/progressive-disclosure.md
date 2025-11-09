# Progressive Disclosure in ragged

**Last Updated**: 2025-11-08
**Status**: Planning

---

## Overview

Progressive disclosure is a UX pattern that presents only essential information by default while making advanced features available when needed. This allows ragged to serve both non-technical users and technical experts with the same interface.

## Core Principle

**Simple by default. Powerful when needed.**

---

## Four-Level UI Hierarchy

### Level 1: Simple (Default UX)

**Target Audience**: Non-technical users, beginners
**What They See**: Clean, minimal interface
**When**: Always visible by default

#### Features

**Core Interface:**
```
┌─────────────────────────────────────────┐
│  💬 ragged                              │
├─────────────────────────────────────────┤
│  📁 My Documents        [Upload Files]  │
├─────────────────────────────────────────┤
│                                         │
│  Chat History:                          │
│  ┌───────────────────────────────────┐ │
│  │ Q: What is RAG?                   │ │
│  │ A: Retrieval-Augmented            │ │
│  │    Generation...                  │ │
│  │    📄 intro.pdf (page 2)          │ │
│  └───────────────────────────────────┘ │
│                                         │
├─────────────────────────────────────────┤
│  Ask a question...          [Send]      │
└─────────────────────────────────────────┘
```

**Available Actions:**
- Upload documents (drag & drop)
- Select collection (dropdown)
- Type question and send
- View responses with basic citations
- See conversation history

**Hidden:**
- All advanced settings
- Technical details
- Performance metrics
- Debug information

**Implementation (v0.2):**
```python
# Gradio simple interface
with gr.Blocks() as demo:
    gr.Markdown("# Ask Your Documents")

    collection = gr.Dropdown(
        choices=get_collections(),
        label="Collection"
    )

    chatbot = gr.ChatInterface(
        query_handler,
        examples=["What is RAG?", "Summarize the findings"]
    )

    with gr.Accordion("Upload Documents", open=False):
        file_upload = gr.File(file_count="multiple")
        upload_btn = gr.Button("Upload")
```

---

### Level 2: Advanced (Optional Toggle)

**Target Audience**: Intermediate users, power users
**What They See**: Additional controls in expandable panels
**When**: User clicks "Advanced Settings" or similar

#### Features

**Expandable Advanced Panel:**
```
┌─────────────────────────────────────────┐
│  ⚙️ Advanced Settings        [Hide ▲]   │
├─────────────────────────────────────────┤
│  Model                                  │
│  ┌─────────────────────────┐           │
│  │ llama2              ▼   │           │
│  └─────────────────────────┘           │
│                                         │
│  Temperature                            │
│  [====|-------------]  0.7              │
│  More focused ← → More creative         │
│                                         │
│  Number of sources (k)                  │
│  [1] [3] [5*] [10] [20]                │
│                                         │
│  Search Strategy                        │
│  • Vector only                          │
│  • Keyword only                         │
│  • Hybrid (recommended) ✓               │
│                                         │
│  Response Style                         │
│  • Concise                              │
│  • Detailed ✓                           │
│  • Technical                            │
└─────────────────────────────────────────┘
```

**Available Controls:**
- Model selection (if multiple models available)
- Temperature slider (0.0 - 1.0)
- Top-k chunks (how many sources to use)
- Search strategy (vector, keyword, hybrid)
- Response style/tone
- Max response length
- Collection management (create/rename/delete)

**Still Hidden:**
- Query internals
- Retrieval scores
- Performance metrics
- Debug information

**Implementation (v0.3):**
```python
with gr.Accordion("Advanced Settings", open=False):
    model = gr.Dropdown(choices=get_models(), label="Model")
    temperature = gr.Slider(0, 1, value=0.7, label="Temperature")
    top_k = gr.Slider(1, 20, value=5, step=1, label="Sources")

    search_strategy = gr.Radio(
        choices=["vector", "keyword", "hybrid"],
        value="hybrid",
        label="Search Strategy"
    )
```

---

### Level 3: Developer (Debug Mode)

**Target Audience**: Technical users, developers, researchers
**What They See**: Query internals, retrieval details, performance data
**When**: User enables "Developer Mode" toggle

#### Features

**Developer Dashboard:**
```
┌─────────────────────────────────────────┐
│  🔍 Developer Mode           [Hide ▼]   │
├─────────────────────────────────────────┤
│  Query Analysis                         │
│  ┌───────────────────────────────────┐ │
│  │ Original: "What is RAG?"          │ │
│  │ Rewritten:                        │ │
│  │   • "RAG definition"              │ │
│  │   • "retrieval augmented generation"│
│  │   • "RAG system architecture"     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Retrieved Chunks (top 5)               │
│  ┌───────────────────────────────────┐ │
│  │ 1. intro.pdf (p.2)                │ │
│  │    Score: 0.94 | Reranked: 0.98   │ │
│  │    "RAG is a technique..."        │ │
│  │                                   │ │
│  │ 2. paper.pdf (p.15)               │ │
│  │    Score: 0.89 | Reranked: 0.91   │ │
│  │    "The architecture consists..." │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Performance Metrics                    │
│  ┌───────────────────────────────────┐ │
│  │ Total: 342ms                      │ │
│  │ ├─ Query Expansion: 23ms          │ │
│  │ ├─ Vector Retrieval: 87ms         │ │
│  │ ├─ Reranking: 145ms               │ │
│  │ └─ Generation: 87ms               │ │
│  │                                   │ │
│  │ Tokens: 156 (prompt) + 89 (output)│ │
│  │ Cache Hit: No                     │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Available Information:**
- Query rewriting/expansion details
- Retrieved chunks with scores
- Reranking before/after comparison
- Timing breakdown by stage
- Token usage statistics
- Cache hit/miss information
- Confidence scores (Self-RAG)
- Strategy selection reasoning (Adaptive RAG)

**Implementation (v0.4):**
```svelte
<!-- DeveloperPanel.svelte -->
<script>
  export let debugInfo;
  export let visible = false;
</script>

{#if visible}
  <div class="developer-panel">
    <h3>Query Analysis</h3>
    <div class="query-details">
      <strong>Original:</strong> {debugInfo.originalQuery}
      <strong>Rewritten:</strong>
      <ul>
        {#each debugInfo.rewrittenQueries as rq}
          <li>{rq}</li>
        {/each}
      </ul>
    </div>

    <h3>Retrieved Chunks</h3>
    {#each debugInfo.chunks as chunk, i}
      <div class="chunk-detail">
        <span class="rank">{i + 1}.</span>
        <span class="source">{chunk.source}</span>
        <span class="score">Score: {chunk.score.toFixed(2)}</span>
        {#if chunk.rerankedScore}
          <span class="reranked">Reranked: {chunk.rerankedScore.toFixed(2)}</span>
        {/if}
        <p class="preview">{chunk.text.substring(0, 100)}...</p>
      </div>
    {/each}

    <h3>Performance</h3>
    <div class="timing-breakdown">
      <div class="metric">
        <span>Total:</span>
        <span>{debugInfo.timing.total}ms</span>
      </div>
      {#each Object.entries(debugInfo.timing.stages) as [stage, time]}
        <div class="metric sub">
          <span>├─ {stage}:</span>
          <span>{time}ms</span>
        </div>
      {/each}
    </div>
  </div>
{/if}
```

---

### Level 4: Expert (Power Features)

**Target Audience**: Researchers, ML engineers, system administrators
**What They See**: Evaluation metrics, A/B testing, system configuration
**When**: User navigates to "Expert Tools" section

#### Features

**Expert Dashboard:**
```
┌─────────────────────────────────────────┐
│  🧪 Expert Tools                        │
├─────────────────────────────────────────┤
│  Evaluation Metrics (RAGAS)             │
│  ┌───────────────────────────────────┐ │
│  │ Collection: research-papers       │ │
│  │                                   │ │
│  │ Faithfulness:      0.87           │ │
│  │ Answer Relevancy:  0.92           │ │
│  │ Context Recall:    0.79           │ │
│  │ Context Precision: 0.84           │ │
│  │                                   │ │
│  │ [View Details] [Export Report]    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  A/B Testing                            │
│  ┌───────────────────────────────────┐ │
│  │ Compare Configurations:           │ │
│  │                                   │ │
│  │ Config A (current):               │ │
│  │  • Hybrid search + Cross-encoder  │ │
│  │  • Avg Score: 0.89                │ │
│  │                                   │ │
│  │ Config B (test):                  │ │
│  │  • Vector only + MMR              │ │
│  │  • Avg Score: 0.82                │ │
│  │                                   │ │
│  │ Winner: Config A (+7.8%)          │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Custom Chunking                        │
│  ┌───────────────────────────────────┐ │
│  │ Strategy: [Custom ▼]              │ │
│  │ Chunk Size: [500]                 │ │
│  │ Overlap: [100]                    │ │
│  │ Separators: [Custom...]           │ │
│  │                                   │ │
│  │ [Test Strategy] [Apply]           │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Embedding Model Comparison             │
│  ┌───────────────────────────────────┐ │
│  │ Current: all-MiniLM-L6-v2         │ │
│  │ Alternative: Qwen3-4B             │ │
│  │                                   │ │
│  │ Accuracy: 0.87 vs 0.91 (+4.6%)    │ │
│  │ Speed: 87ms vs 142ms (-38%)       │ │
│  │ Size: 80MB vs 4GB                 │ │
│  │                                   │ │
│  │ [Switch Model]                    │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Available Tools:**
- RAGAS evaluation dashboard
- A/B testing configuration comparison
- Custom chunking strategy definition
- Embedding model comparison
- Reranking strategy selection
- Performance optimization tools
- System monitoring (Prometheus/Grafana integration)

**Implementation (v1.0):**
```svelte
<!-- ExpertTools.svelte -->
<script>
  import RAGASMetrics from './RAGASMetrics.svelte';
  import ABTesting from './ABTesting.svelte';
  import ChunkingConfig from './ChunkingConfig.svelte';
  import ModelComparison from './ModelComparison.svelte';
</script>

<div class="expert-tools">
  <section>
    <h2>Evaluation Metrics</h2>
    <RAGASMetrics />
  </section>

  <section>
    <h2>A/B Testing</h2>
    <ABTesting />
  </section>

  <section>
    <h2>Configuration Tuning</h2>
    <ChunkingConfig />
    <ModelComparison />
  </section>
</div>
```

---

## Mode Switching

### Toggle Pattern

```svelte
<!-- ModeSelector.svelte -->
<script>
  import { writable } from 'svelte/store';

  export const uiMode = writable('simple');

  const modes = [
    { id: 'simple', label: 'Simple', icon: '😊' },
    { id: 'advanced', label: 'Advanced', icon: '⚙️' },
    { id: 'developer', label: 'Developer', icon: '🔍' },
    { id: 'expert', label: 'Expert', icon: '🧪' }
  ];
</script>

<div class="mode-selector">
  <label>Interface Mode:</label>
  <div class="mode-buttons">
    {#each modes as mode}
      <button
        class:active={$uiMode === mode.id}
        on:click={() => uiMode.set(mode.id)}
      >
        <span class="icon">{mode.icon}</span>
        <span>{mode.label}</span>
      </button>
    {/each}
  </div>
</div>
```

### Conditional Rendering

```svelte
<!-- QueryInterface.svelte -->
<script>
  import { uiMode } from './ModeSelector.svelte';
  import DeveloperPanel from './DeveloperPanel.svelte';
  import ExpertTools from './ExpertTools.svelte';
</script>

<!-- Always visible: Simple mode -->
<div class="chat-container">
  <ChatInterface />
</div>

<!-- Level 2: Advanced settings -->
{#if $uiMode !== 'simple'}
  <AdvancedSettings />
{/if}

<!-- Level 3: Developer mode -->
{#if $uiMode === 'developer' || $uiMode === 'expert'}
  <DeveloperPanel />
{/if}

<!-- Level 4: Expert tools -->
{#if $uiMode === 'expert'}
  <ExpertTools />
{/if}
```

---

## Progressive Disclosure Benefits

### For Non-Technical Users

✅ **Simple, unintimidating interface**
- No overwhelming options
- Clear, focused workflow
- Familiar chat interface
- Easy to understand

✅ **Lower learning curve**
- Can use immediately
- No configuration needed
- Sensible defaults
- Gradual feature discovery

### For Technical Users

✅ **Access to power features**
- Query debugging available when needed
- Performance optimization tools
- Configuration flexibility
- System visibility

✅ **No artificial limitations**
- All functionality accessible
- Can tune every parameter
- Deep system introspection
- Professional tooling

### For ragged Project

✅ **Broader appeal**
- Serves multiple audiences
- Lower barrier to entry
- Doesn't alienate experts
- Scales with user expertise

✅ **Reduced support burden**
- Beginners aren't overwhelmed
- Experts can self-serve
- Clear UI progression
- Feature discovery built-in

---

## Implementation Strategy

### v0.2: Foundation (Simple Mode Only)

```python
# Gradio - just the basics
with gr.Blocks() as demo:
    chatbot = gr.ChatInterface(query_handler)
    file_upload = gr.File()
```

**No modes yet** - establish baseline UX

### v0.3: Add Advanced Settings

```python
# Gradio - add collapsible advanced panel
with gr.Blocks() as demo:
    chatbot = gr.ChatInterface(query_handler)

    with gr.Accordion("Advanced Settings", open=False):
        temperature = gr.Slider(0, 1, 0.7)
        top_k = gr.Slider(1, 20, 5)
```

**2 levels**: Simple + Advanced

### v0.4: Add Developer Mode

```python
# Gradio - add debug toggle
with gr.Blocks() as demo:
    developer_mode = gr.Checkbox(label="Developer Mode", value=False)

    chatbot = gr.ChatInterface(query_handler)

    @gr.render(inputs=[developer_mode])
    def show_debug(enabled):
        if enabled:
            return gr.JSON(label="Debug Info")
```

**3 levels**: Simple + Advanced + Developer

### v0.5: Full Svelte Rebuild

```svelte
<!-- All 4 levels with clean mode switching -->
<script>
  import { uiMode } from '$lib/stores';
</script>

<ModeSelector />

<SimpleInterface />

{#if $uiMode !== 'simple'}
  <AdvancedSettings />
{/if}

{#if $uiMode === 'developer' || $uiMode === 'expert'}
  <DeveloperPanel />
{/if}

{#if $uiMode === 'expert'}
  <ExpertTools />
{/if}
```

**4 levels**: Complete hierarchy

---

## Design Patterns

### Accordions for Advanced Settings

```svelte
<details>
  <summary>Advanced Settings ⚙️</summary>
  <div class="advanced-panel">
    <!-- Settings here -->
  </div>
</details>
```

### Collapsible Panels with Icons

```svelte
<button on:click={() => expanded = !expanded}>
  {#if expanded}
    Hide Advanced ▲
  {:else}
    Show Advanced ▼
  {/if}
</button>

{#if expanded}
  <div class="panel">
    <!-- Content -->
  </div>
{/if}
```

### Tab Switching for Modes

```svelte
<div class="tabs">
  <button class:active={mode === 'simple'} on:click={() => mode = 'simple'}>
    Simple
  </button>
  <button class:active={mode === 'developer'} on:click={() => mode = 'developer'}>
    Developer
  </button>
</div>
```

---

## User Research & Testing

### Metrics to Track (v1.0)

**Feature Discovery:**
- % users who find advanced settings
- Time to first mode switch
- Most popular mode
- Feature usage by mode

**User Satisfaction:**
- Confusion rate (support tickets)
- Task completion rate
- Time to complete tasks
- User feedback scores

**Mode Distribution:**
```
Simple:    60% (most users)
Advanced:  25% (power users)
Developer: 10% (technical users)
Expert:    5%  (researchers)
```

---

## Conclusion

**Progressive disclosure makes ragged accessible to everyone:**

- ✅ Non-technical users: Simple, approachable interface
- ✅ Intermediate users: Advanced controls when needed
- ✅ Developers: Deep system visibility
- ✅ Researchers: Professional evaluation tools

**Implementation timeline:**
- v0.2: Simple mode only
- v0.3: + Advanced settings
- v0.4: + Developer mode
- v0.5-v1.0: Complete 4-level hierarchy

**Next**: See [versioning-philosophy.md](./versioning-philosophy.md) for development approach.
