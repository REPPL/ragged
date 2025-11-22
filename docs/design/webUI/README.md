# ragged Web UI Design

Design resources for the ragged web interface (v0.6.7+ implementation).

---

## Directory Structure

```
docs/design/webUI/
├── README.md                         # This file
├── webUI.svg                         # High-fidelity Penpot mockup
└── wireframe/
    ├── webUI--wireframe.excalidraw   # Low-fidelity wireframe
    └── webUI--wireframe.svg          # Exported wireframe SVG
```

---

## Files

### wireframe/webUI--wireframe.excalidraw

**Type:** Low-fidelity wireframe
**Tool:** Excalidraw (https://excalidraw.com)
**Dimensions:** 1923x1117px

**Contents:**
- Main application layout with header, sidebar, and main content area
- Sidebar (320px): Library, collection selector, document cards, tag filters, upload zone
- Main area: Large query input, mode tabs (Text/Image/Hybrid), context controls, results
- Annotations explaining UI functionality and interaction patterns

**How to Edit:**
1. Go to https://excalidraw.com
2. Click "Open" → Select `webUI--wireframe.excalidraw`
3. Edit layout, components, annotations
4. Export as PNG/SVG when needed

**Key Features:**
- Collection-based document library
- Library metadata: documents, tags, embeddings
- Multi-modal query interface
- Results with source transparency (document, page, score, model)
- Tag-based filtering
- Drag-and-drop upload zone

---

### webUI.svg

**Type:** High-fidelity production mockup
**Tool:** Penpot (https://penpot.app) - import and edit
**Dimensions:** 1920x1120px
**Status:** Penpot-compatible (no filters, clean SVG elements)

**Contents:**
- Complete production-ready design based on wireframe
- Professional color scheme and typography
- All interactive states and metadata displays

**Design Specifications:**

#### Layout
- **Header:** 1920x72px, dark background (#1e1e1e)
  - Logo: "ragged" + tagline
  - Sidebar toggle (☰)
  - Settings (⚙) and theme toggle (🌙)
- **Sidebar:** 320x1048px, light grey (#f8f9fa)
  - Collection selector with dropdown
  - Library stats (documents, tags, embeddings)
  - Document cards (272x96px each)
  - Tag filter pills
  - Upload zone (272x120px, dashed border)
- **Main Area:** 1560px wide
  - Query input (1500x100px)
  - Query options bar (mode tabs, context, top-k, search button)
  - Results section (expandable cards with metadata)

#### Color Palette
```
Primary:     #4c6ef5  (Blue - buttons, active states)
Background:  #ffffff  (White)
Sidebar:     #f8f9fa  (Light grey)

Text Colors:
- Dark:      #1e1e1e  (Headings)
- Medium:    #495057  (Body text)
- Light:     #868e96  (Secondary text)
- Muted:     #adb5bd  (Hints, placeholders)

Semantic:
- Success:   #2b8a3e  (High scores, positive states)
- Warning:   #fab005  (Medium scores)
- Danger:    #c92a2a  (Low scores, errors)

Borders:
- Light:     #e9ecef  (Cards, dividers)
- Medium:    #dee2e6  (Inputs, controls)
```

#### Typography
```
Headings:    sans-serif, 600-700 weight
Body:        sans-serif, 400-500 weight
Monospace:   monospace (filenames, metadata)

Sizes:
- H1:        24px (section titles)
- H2:        18px (sidebar titles)
- H3:        15px (result headings)
- Body:      14px (main text)
- Small:     12-13px (metadata, labels)
- Tiny:      10-11px (tags, hints)
```

#### Components

**Document Cards:**
- 272x96px, 12px border radius
- Active: 2px blue border (#4c6ef5) + 4px left accent bar
- Inactive: 1px grey border (#e9ecef)
- Content: filename (14px, bold), metadata (11px, grey), date, domain tag

**Domain Tags:**
- Pill-shaped (9px border radius)
- Technical: Blue (#e7f5ff bg, #4c6ef5 text)
- Academic: Yellow (#fff3bf bg, #fab005 text)
- Research: Green (#d3f9d8 bg, #37b24d text)

**Filter Tags:**
- 55x24px pills, 12px border radius
- Red theme (#ffc9c9 bg, #fa5252 border, #c92a2a text)

**Score Badges:**
- 40px diameter circles
- High (90+): Green (#d3f9d8 bg, #2b8a3e text)
- Medium (80-89): Yellow (#fff3bf bg, #f76707 text)
- Low (<80): Red (#ffe3e3 bg, #c92a2a text)

**Mode Tabs:**
- 100x32px, 8px border radius
- Active: Blue background (#4c6ef5), white text
- Inactive: White background, grey text (#495057)
- Icons: 📝 Text, 🖼️ Image, 🔀 Hybrid

**Result Cards:**
- 1500px wide, variable height, 12px border radius
- Expanded: 140px height
- Collapsed: 100px height
- Contains: score badge, metadata bar, content preview, action button

---

## Design Workflow

### Phase 1: Wireframing (Complete)
✅ Low-fidelity Excalidraw wireframe created
✅ Layout structure finalized
✅ Information architecture validated

### Phase 2: High-Fidelity Mockup (Complete)
✅ Production-ready SVG generated from wireframe
✅ Color palette applied
✅ Typography specified
✅ Component states designed
✅ Penpot-compatible (no filters, clean elements)

### Phase 3: Implementation (Next)
- [ ] Import `webUI.svg` to Penpot for refinement
- [ ] Export individual components as SVG
- [ ] Create Svelte component library (v0.6.7)
- [ ] Implement responsive breakpoints (320px, 768px, 1024px)
- [ ] Add dark mode variants
- [ ] Create interactive prototypes

---

## Design Principles

**Ragged UI Guidelines:**
1. **Information Dense**: Show metadata without clutter
2. **Search-First**: Large, prominent query input
3. **Source Transparency**: Always display document source, page, score, model
4. **Multi-Modal Ready**: Equal treatment for text, image, and hybrid queries
5. **Developer-Friendly**: Monospace for technical data, keyboard shortcuts visible

**Inspiration:**
- **Perplexity.ai**: Query interface, results with sources
- **Notion**: Document management, collection organization
- **Linear**: Keyboard shortcuts, clean aesthetics, professional color scheme

---

## How to Use These Files

### For Design Iteration:
1. **Open Excalidraw wireframe** for quick layout changes
2. **Export to SVG** when structure is stable
3. **Import SVG to Penpot** for detailed design work
4. **Refine colors, spacing, states** in Penpot
5. **Export final components** for development

### For Development:
1. **Reference webUI.svg** for exact dimensions, colors, typography
2. **Extract component specs** from this README
3. **Use color palette** as CSS variables
4. **Implement responsive breakpoints** (sidebar collapse at 768px)

### For Stakeholder Review:
1. **Share webUI.svg** (open in browser or Penpot)
2. **Walk through wireframe** to explain interactions
3. **Gather feedback** on layout, information density
4. **Iterate in Excalidraw** → regenerate SVG → import to Penpot

---

## Future Enhancements

### v0.6.8: Knowledge Graph & Monitoring
- Graph visualization component (D3.js)
- GPU metrics dashboard
- Real-time performance monitoring

### v0.6.9: PWA & Accessibility
- PWA install flow UI
- Mobile navigation patterns
- ARIA labels and semantic HTML
- Keyboard navigation enhancements
- Screen reader optimisation

---

## Related Documentation

- [Web UI Planning Specifications](../../development/planning/interfaces/web/) - Written UI specifications and requirements
- [Icon Design Files](./icons/) - Icon assets and specifications
- [Wireframes](./wireframe/) - Layout wireframes and mockups
- [Design Directory Overview](../) - All design assets
- [v0.6.7 Roadmap](../../development/roadmap/version/v0.6/v0.6.7.md) - Web UI implementation plan

---

**Last Updated:** 2024-11-22
**Design Tool:** Excalidraw (wireframe) → SVG → Penpot (high-fidelity)
**Status:** Production mockup ready for implementation
