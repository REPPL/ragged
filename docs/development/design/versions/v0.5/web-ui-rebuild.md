# v0.5 Web UI: Svelte/SvelteKit Rebuild

**Timeline**: 5-6 weeks (no additional time for migration)
**Technology**: **Svelte/SvelteKit** (clean rebuild)
**Approach**: Fresh start, not migration

---

## Goals

Rebuild UI with production framework, optimised for:
- GraphRAG visualization
- Better performance
- Production polish
- Full customization

## Why Rebuild (Not Migrate)?

**Breaking changes OK before v1.0** means we can:
- Start fresh with lessons learned
- No compatibility shims
- Cleaner codebase
- Better architecture

## Technology Stack

**Frontend**: Svelte/SvelteKit
- Smallest bundle size (1.6KB)
- Best performance
- Clean, readable code
- Offline-first with service workers

**Backend**: FastAPI (unchanged)
- Same API endpoints
- Enhanced for new features
- Better documentation

## New Features

### 1. Graph Visualization

For GraphRAG (v0.5 adds knowledge graphs):
```svelte
<script>
  import { ForceGraph } from '$lib/components';
  import type { GraphData } from '$lib/types';

  export let graphData: GraphData;
</script>

<ForceGraph
  nodes={graphData.entities}
  edges={graphData.relationships}
  onNodeClick={handleNodeClick}
/>
```

### 2. Document Preview with Highlights

Split-view interface:
```
┌──────────────────┬─────────────────┐
│                  │                 │
│   Chat           │  Document       │
│   Interface      │  Preview        │
│                  │  (highlighted)  │
│                  │                 │
└──────────────────┴─────────────────┘
```

### 3. Advanced Filtering

```svelte
<FilterPanel>
  <DateRange />
  <DocumentType />
  <Confidence min={0.7} />
  <Tags selected={['research', 'papers']} />
</FilterPanel>
```

### 4. Production Design System

- Tailwind CSS for styling
- Consistent component library
- Responsive design
- Dark mode support
- Accessibility (ARIA labels, keyboard nav)

## Implementation Strategy

### Phase 1: Core Rebuild (Weeks 1-2)

Recreate v0.4 features in Svelte:
- Chat interface
- Document upload
- Basic query flow
- SSE streaming client

**Feature parity with Gradio version**

### Phase 2: New Features (Weeks 3-4)

Add Svelte-specific features:
- Graph visualization
- Document preview
- Split-view interface
- Advanced filtering

**Beyond Gradio capabilities**

### Phase 3: Polish (Weeks 5-6)

Production readiness:
- Performance optimisation
- Bundle size optimisation
- Lighthouse score > 90
- Comprehensive testing

## Bundle Optimisation

```javascript
// vite.config.js
export default {
  build: {
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte'],
          graph: ['d3', 'graphology']  // Lazy load
        }
      }
    }
  }
}
```

Target: < 500KB total bundle

## Breaking Changes

- **Gradio UI completely removed**
- **URL structure changes**
- **No migration path for UI customizations**
- **API unchanged** - CLI and programmatic access still work

Users must:
- Use v0.4 (unsupported) if need Gradio
- Migrate to Svelte UI
- Or build custom UI using our API

## Success Criteria

- [ ] Feature parity with v0.4
- [ ] Graph visualization functional
- [ ] Document preview with highlights works
- [ ] Bundle size < 500KB
- [ ] Lighthouse score > 90
- [ ] Offline PWA setup (preparation for v1.0)

## Timeline

5-6 weeks total (no change from original v0.5 estimate).
Clean rebuild is faster than careful migration.
