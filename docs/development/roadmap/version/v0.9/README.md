# Ragged v0.9 Roadmap - Web UI Completion

**Status:** Planned

**Duration:** 120-180 hours (AI implementation)

**Focus:** Complete modern web interface with visual workflow editor and advanced features

**Breaking Changes:** None

---

## Overview

Version 0.9 completes the web UI transformation, bringing ragged from basic Gradio to a polished, professional web application. This builds on v0.6's foundation with advanced features inspired by AnythingLLM, RAGFlow, and modern RAG interfaces.

**Dependencies:** Requires v0.6 (Svelte foundation), v0.8 (agent workflows backend)

**Strategic Context:** Achieves AnythingLLM-level UI polish while adding RAGFlow's visual workflow editor and modern web app features (PWA, offline support).

---

## UI-002: Block-Based Editor (30-40 hours)

**Problem:** Text-only search interface inadequate for rich document interaction; users expect modern editing experiences.

**Inspiration:** Notion's block editor, modern note-taking apps.

**Implementation:**
1. Research block editor libraries (TipTap, ProseMirror, Lexical) [4-5 hours]
2. Integrate TipTap editor with Svelte [8-10 hours]
3. Create custom blocks (document, citation, query) [10-12 hours]
4. Implement drag-and-drop block reordering [4-5 hours]
5. Add block persistence and state management [4-5 hours]

**Custom block types:**
- **Query Block:** Inline RAG query with results embedded
- **Document Block:** Reference to ingested document with preview
- **Citation Block:** Automatically generated citation with source link
- **Markdown Block:** Standard markdown editing
- **Code Block:** Syntax-highlighted code snippets
- **Image Block:** Image display (for vision RAG results)
- **Table Block:** Tabular data display

**Block editor features:**
- Drag-and-drop reordering
- Nested blocks (quotes, lists)
- Slash commands (`/query`, `/document`, `/citation`)
- Real-time collaboration (deferred to v1.5)
- Export to markdown/PDF

**Files:**
- `web-ui/src/lib/components/editor/BlockEditor.svelte` (~500 lines)
- `web-ui/src/lib/components/blocks/` (block components, ~1200 lines total)
- `web-ui/src/lib/editor/extensions/` (TipTap extensions, ~800 lines)
- `web-ui/src/lib/stores/editor.ts` (state management, ~300 lines)

**Manual Testing:**
- Create document with mixed blocks
- Drag-and-drop to reorder
- Execute inline query block
- Insert citation from query results
- Export to markdown

**Success:** Block editor functional; users can create rich documents with embedded queries

---

## UI-003: Command Palette (15-20 hours)

**Problem:** No keyboard-driven navigation; users must click through menus.

**Inspiration:** VS Code command palette, Linear's command-K.

**Implementation:**
1. Design command palette UI and hotkey (Cmd/Ctrl+K) [3-4 hours]
2. Implement fuzzy search for commands [4-5 hours]
3. Create command registry and execution [4-5 hours]
4. Add recent commands and favorites [2-3 hours]
5. Integrate with all UI features [2-3 hours]

**Command categories:**
- **Navigation:** "Go to Documents", "Go to Settings", "Go to Workflows"
- **Actions:** "Ingest Document", "Run Query", "Create Agent Workflow"
- **Search:** "Search Documents", "Search Settings"
- **Settings:** "Toggle Dark Mode", "Change Theme"

**Command palette features:**
- Fuzzy search (type "indoc" → "Ingest Document")
- Keyboard shortcuts shown inline
- Recent commands list
- Customizable favorites
- Context-aware (different commands available in different views)

**Files:**
- `web-ui/src/lib/components/CommandPalette.svelte` (~400 lines)
- `web-ui/src/lib/commands/registry.ts` (command definitions, ~300 lines)
- `web-ui/src/lib/commands/search.ts` (fuzzy search, ~200 lines)
- `web-ui/src/lib/stores/commands.ts` (recent commands, ~150 lines)

**Manual Testing:**
- Press Cmd/Ctrl+K to open
- Type partial command name, verify fuzzy matching
- Execute command via palette
- Verify keyboard shortcuts work
- Test context-aware commands

**Success:** Command palette provides fast keyboard-driven navigation and actions

---

## UI-004: Knowledge Graph Visualization (25-30 hours)

**Problem:** Knowledge graph (v0.4.5) accessible only via CLI; no visual exploration.

**Inspiration:** Graph databases' visualization tools, Obsidian's graph view.

**Implementation:**
1. Research graph visualization libraries (D3.js, Cytoscape.js, vis.js) [3-4 hours]
2. Integrate graph library with Svelte [6-8 hours]
3. Fetch graph data from backend API [4-5 hours]
4. Implement interactive features (zoom, pan, click, filter) [6-8 hours]
5. Add graph layout algorithms and styling [4-5 hours]
6. Create sidebar with node/edge details [2-3 hours]

**Graph features:**
- **Layout algorithms:** Force-directed, hierarchical, circular
- **Interactive:** Zoom, pan, click nodes/edges for details
- **Filtering:** Show/hide by relationship type, node type
- **Search:** Find specific entities in graph
- **Clustering:** Group related entities visually
- **Export:** Save graph as image or data

**Graph display:**
- **Nodes:** Documents, entities, topics (sized by importance)
- **Edges:** Relationships, citations, co-occurrences (colored by type)
- **Highlighting:** Hover to highlight connected nodes
- **Details panel:** Click node → show metadata, connections

**Files:**
- `web-ui/src/routes/graph/+page.svelte` (~600 lines)
- `web-ui/src/lib/components/graph/GraphView.svelte` (~500 lines)
- `web-ui/src/lib/graph/layout.ts` (layout algorithms, ~300 lines)
- `web-ui/src/lib/api/graph.ts` (graph API client, ~200 lines)

**Manual Testing:**
- Open graph view with 50+ documents
- Zoom and pan smoothly
- Click node to see details
- Filter by relationship type
- Apply different layout algorithms
- Export graph as PNG

**Success:** Knowledge graph visualized beautifully; users explore connections interactively

---

## UI-005: Visual Workflow Editor (30-40 hours)

**Problem:** Agent workflows (v0.8) require JSON editing; no visual interface.

**Inspiration:** RAGFlow's visual DAG workflow editor—highly requested feature.

**Implementation:**
1. Research flow editor libraries (React Flow, Rete.js, X6) [3-4 hours]
2. Integrate flow library with Svelte [8-10 hours]
3. Create node types for tools and agents [8-10 hours]
4. Implement edge connections and validation [6-8 hours]
5. Add workflow execution and debugging [5-6 hours]

**Node types:**
- **Tool nodes:** Vector Search, BM25 Search, Summarize, Filter, etc.
- **Agent nodes:** Research Agent, QA Agent, Custom Agent
- **Control nodes:** Conditional (if/else), Loop, Parallel
- **Input/Output nodes:** User input, Final output

**Workflow editor features:**
- **Drag-and-drop:** Add nodes from palette to canvas
- **Connect:** Draw edges between nodes
- **Validation:** Prevent invalid connections (type mismatches)
- **Execution:** Run workflow with test data, see results per node
- **Debugging:** Step through execution, inspect intermediate results
- **Save/Load:** Serialize to JSON, load existing workflows

**Workflow canvas:**
- **Minimap:** Overview of large workflows
- **Zoom controls:** Fit to screen, zoom in/out
- **Grid snapping:** Align nodes neatly
- **Undo/redo:** Workflow editing history

**Files:**
- `web-ui/src/routes/workflows/editor/+page.svelte` (~800 lines)
- `web-ui/src/lib/components/workflow/FlowEditor.svelte` (~600 lines)
- `web-ui/src/lib/components/workflow/nodes/` (node components, ~1000 lines)
- `web-ui/src/lib/workflow/validator.ts` (connection validation, ~300 lines)

**Manual Testing:**
- Create workflow with 5+ nodes
- Connect nodes, verify validation
- Execute workflow with test data
- Step through debugging
- Save workflow, reload, verify preservation

**Success:** Visual workflow editor functional; users create agents without code

---

## UI-006: Dark Mode & Theming (10-15 hours)

**Problem:** No dark mode; single theme limits accessibility and user preference.

**Inspiration:** Modern web apps (GitHub, Linear, VS Code) with theme support.

**Implementation:**
1. Design dark mode colour palette [2-3 hours]
2. Implement theme switching system [3-4 hours]
3. Create additional themes (light, dark, high-contrast) [3-4 hours]
4. Add theme persistence (local storage) [2-3 hours]

**Themes:**
- **Light:** Default light theme
- **Dark:** Low-light optimised
- **High Contrast:** Accessibility-focused

**Theme system:**
- CSS variables for all colours
- Automatic OS theme detection
- Manual override via settings or command palette
- Per-component theme customization

**Files:**
- `web-ui/src/lib/styles/themes/` (theme definitions, ~400 lines)
- `web-ui/src/lib/stores/theme.ts` (theme management, ~150 lines)
- `web-ui/src/app.css` (update with CSS variables)

**Manual Testing:**
- Switch between themes
- Verify all components styled correctly in each theme
- Test automatic OS detection
- Verify persistence across sessions

**Success:** Multiple themes available; dark mode polished and fully functional

---

## UI-007: Progressive Web App (PWA) (15-20 hours)

**Problem:** Web app requires internet; no offline support or native-like experience.

**Inspiration:** Modern PWAs (Twitter, Notion) with offline capabilities.

**Implementation:**
1. Set up service worker and manifest [4-5 hours]
2. Implement offline caching strategy [5-6 hours]
3. Add install prompt and app icons [3-4 hours]
4. Create offline fallback UI [3-4 hours]

**PWA features:**
- **Installable:** Add to home screen on mobile/desktop
- **Offline:** View cached documents and queries
- **Background sync:** Queue actions when offline, sync when online
- **Push notifications:** Query completion alerts (optional, privacy consideration)
- **App icons:** Native app appearance

**Caching strategy:**
- **App shell:** Cache UI assets (HTML, CSS, JS)
- **Documents:** Cache document list and content
- **Queries:** Cache recent query results
- **Images:** Cache vision RAG images
- **API responses:** Cache with expiration

**Files:**
- `web-ui/src/service-worker.js` (~400 lines)
- `web-ui/src/lib/offline/cache.ts` (cache management, ~300 lines)
- `web-ui/static/manifest.json` (PWA manifest)
- `web-ui/static/icons/` (app icons, various sizes)

**Manual Testing:**
- Install PWA on desktop/mobile
- Go offline, verify cached content accessible
- Queue action offline, verify sync when online
- Verify push notifications (if enabled)

**Success:** PWA installable; works offline; native-like experience on mobile/desktop

---

## UI-008: Advanced Document Library (15-20 hours)

**Problem:** Basic document list from v0.6; needs advanced features for large libraries.

**Implementation:**
1. Add multi-column sorting and filtering [4-5 hours]
2. Implement faceted search (by date, author, type) [4-5 hours]
3. Create document preview pane [3-4 hours]
4. Add bulk actions (delete, tag, export) [2-3 hours]
5. Implement virtual scrolling for large lists [2-3 hours]

**Document library features:**
- **Sorting:** By date, title, relevance, author
- **Filtering:** Date range, document type, tags, metadata
- **Faceted search:** Filter by multiple criteria simultaneously
- **Preview:** Quick document preview without opening
- **Bulk actions:** Select multiple documents for batch operations
- **Virtual scrolling:** Handle 10,000+ documents smoothly

**Files:**
- `web-ui/src/routes/documents/+page.svelte` (~600 lines)
- `web-ui/src/lib/components/documents/DocumentList.svelte` (~400 lines)
- `web-ui/src/lib/components/documents/FilterPanel.svelte` (~300 lines)
- `web-ui/src/lib/components/documents/PreviewPane.svelte` (~250 lines)

**Manual Testing:**
- Load library with 1,000+ documents
- Sort by different columns
- Apply multiple filters
- Select 100 documents, bulk delete
- Verify virtual scrolling performance

**Success:** Document library handles large collections; advanced filtering and preview functional

---

## UI-009: Mobile Responsive Design (10-15 hours)

**Problem:** v0.6 foundation basic responsive; needs mobile-first optimization.

**Implementation:**
1. Audit mobile UX and identify issues [2-3 hours]
2. Implement mobile navigation (hamburger menu) [3-4 hours]
3. Optimise touch interactions (tap targets, gestures) [3-4 hours]
4. Create mobile-specific layouts for complex views [2-3 hours]

**Mobile optimizations:**
- **Navigation:** Hamburger menu, bottom navigation
- **Touch targets:** Minimum 44x44px for all buttons
- **Gestures:** Swipe to delete, pull to refresh
- **Layouts:** Single column on mobile, responsive grid on tablet
- **Typography:** Larger text for readability

**Files:**
- Update all route components with mobile layouts
- `web-ui/src/lib/components/MobileNav.svelte` (~300 lines)
- `web-ui/src/lib/styles/mobile.css` (~200 lines)

**Manual Testing:**
- Test on iPhone, Android, iPad
- Verify touch targets large enough
- Test gestures (swipe, pinch to zoom)
- Verify text readable without zooming

**Success:** Mobile experience polished; all features accessible on phones and tablets

---

## Success Criteria

**Automated Tests:**
- [ ] Block editor creates and persists blocks
- [ ] Command palette fuzzy search works correctly
- [ ] Graph visualization renders without errors
- [ ] Workflow editor validates connections
- [ ] Theme switching updates all components
- [ ] Service worker caches resources
- [ ] Document library handles 10,000+ items
- [ ] Mobile responsive breakpoints correct

**Manual Testing:**
- [ ] Create rich document with block editor
- [ ] Navigate using command palette (Cmd+K)
- [ ] Explore knowledge graph with 100+ nodes
- [ ] Create multi-step workflow visually
- [ ] Switch between light/dark/high-contrast themes
- [ ] Install PWA, test offline
- [ ] Filter document library with multiple facets
- [ ] Use all features on mobile device

**Quality Gates:**
- [ ] Block editor performance: <100ms per keystroke
- [ ] Graph visualization: Handle 1,000+ nodes smoothly
- [ ] Workflow editor: Support 50+ node workflows
- [ ] PWA: 90+ Lighthouse score
- [ ] Mobile: Touch targets ≥44px, readable text
- [ ] Offline: All cached content accessible
- [ ] Themes: 100% component coverage

---

## Known Risks

- **Performance:** Rich UI features may be slow on older devices; optimize carefully
- **Offline sync:** Conflict resolution complex; defer advanced cases to v1.5
- **Graph visualization:** Large graphs (10,000+ nodes) may require specialized rendering
- **Mobile UX:** Desktop features may not translate well to mobile; prioritize ruthlessly
- **Browser compatibility:** PWA features vary by browser; test extensively
- **Accessibility:** Rich interactions must remain keyboard-navigable and screen-reader friendly

---

## Next Steps

After v0.9 completion:
- **v1.0:** Personal Knowledge Platform (polish, stability, public v1.0 release)
- **v1.5:** Collaboration & Multi-User (team features, sharing, real-time collaboration)

See: `roadmap/version/v1.0/`, `roadmap/version/v1.5/`

---

## Related Documentation

- [Previous Version](../v0.8/README.md) - Agent capabilities
- [Next Version (v1.0)](../../planning/version/v1.0/) - Personal knowledge platform planning
- [Next Version (v1.5)](../v1.5/README.md) - Collaboration features
- [Planning](../../planning/version/v0.9/) - Design goals for v0.9 (if exists)
- [Version Overview](../README.md) - Complete version comparison
- [Projects to Learn From](../../../research/projects-to-learn-from.md) - AnythingLLM UI and RAGFlow workflow inspiration

---
