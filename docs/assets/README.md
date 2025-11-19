# Documentation Assets

**Purpose:** Static assets for documentation (images, diagrams, videos)

---

## Overview

This directory contains all static assets referenced in ragged documentation, organised by type for easy maintenance and reference.

---

## Directory Structure

```
assets/
├── README.md           # This file
├── img/                # Images and screenshots
├── diagrams/           # Architecture diagrams (future)
└── videos/             # Demo videos (future)
```

---

## What Belongs Here

**Images:**
- Screenshots of UI/CLI
- Architecture diagrams
- Flow charts
- Comparison charts
- Banner images

**Naming Convention:**
- Descriptive names: `web-ui-query-interface.png`
- Version-specific: `v0.2-architecture-diagram.svg`
- Lowercase with hyphens: `hybrid-retrieval-flow.png`

**Supported Formats:**
- Images: `.png`, `.jpg`, `.svg`, `.webp`
- Diagrams: `.svg`, `.drawio`, `.mermaid`
- Videos: `.mp4`, `.webm`, `.gif`

---

## What Doesn't Belong Here

- ❌ Code files
- ❌ Temporary/scratch files
- ❌ User-uploaded content
- ❌ Generated runtime assets

---

## Usage in Documentation

**Markdown Reference:**
```markdown
![Alt text](../assets/img/screenshot.png)
```

**Relative Paths:**
- From `docs/`: `assets/img/screenshot.png`
- From `docs/tutorials/`: `../assets/img/screenshot.png`
- From `docs/development/`: `../assets/img/screenshot.png`

---

## Asset Guidelines

### Images
- **Size**: Optimise for web (typically <500KB)
- **Resolution**: Retina-ready (2x) for important visuals
- **Alt Text**: Always provide descriptive alt text
- **Copyright**: Only use GPL-3.0 compatible or own assets

### Diagrams
- **Source Files**: Keep editable sources (`.drawio`, `.svg`) in repo
- **Exports**: Export PNG for compatibility if needed
- **Consistency**: Use standard colours and fonts

---

## Subdirectories

- [img/](./img/README.md) - Images and screenshots

---

## Related Documentation

- [Documentation Hub](../README.md) - Main documentation index
- [Guides](../guides/README.md) - How-to guides using these assets
- [Tutorials](../tutorials/README.md) - Learning materials using these assets

---
