# Documentation Images

**Purpose:** Images, screenshots, and visual assets for documentation

**Last Updated:** 2025-11-17

---

## Overview

This directory contains all image assets used in ragged documentation, including screenshots, diagrams, charts, and illustrations.

---

## What Belongs Here

**Screenshots:**
- CLI command examples
- Web UI interfaces
- Configuration screens
- Error messages
- Output examples

**Diagrams:**
- Architecture overviews
- Data flow diagrams
- Component relationships
- Sequence diagrams

**Charts:**
- Performance comparisons
- Benchmark results
- Coverage reports
- Usage statistics

**Illustrations:**
- Conceptual diagrams
- Feature highlights
- Workflow visualisations

---

## What Doesn't Belong Here

- ❌ Videos (use `../videos/` when created)
- ❌ Diagrams source files (`.drawio`) - use `../diagrams/` when created
- ❌ Temporary/test images
- ❌ User-generated content
- ❌ Binary executables

---

## Naming Convention

**Format:** `category-description.ext`

**Examples:**
- `cli-query-command.png` - CLI screenshot
- `web-ui-upload-page.png` - Web UI screenshot
- `architecture-v0.2-overview.svg` - Architecture diagram
- `hybrid-retrieval-flow.png` - Flow diagram
- `benchmark-retrieval-comparison.png` - Benchmark chart

**Rules:**
- Lowercase only
- Hyphens to separate words
- Descriptive, not generic (`query-example.png`, not `screenshot1.png`)
- Include version if version-specific (`v0.2-architecture.svg`)

---

## File Format Guidelines

### PNG (.png)
- **Use for:** Screenshots, UI captures, complex images
- **Optimisation:** Use tools like `optipng` or `pngcrush`
- **Recommended:** Most screenshots

### SVG (.svg)
- **Use for:** Diagrams, logos, vector graphics
- **Benefits:** Scalable, small file size, editable
- **Recommended:** Architecture diagrams, flow charts

### JPG (.jpg)
- **Use for:** Photos, complex images with many colours
- **Avoid for:** Screenshots (use PNG instead)

### WebP (.webp)
- **Use for:** Modern browsers, smaller file sizes
- **Fallback:** Provide PNG alternative for compatibility

---

## Image Optimisation

**Before Committing:**
1. Resize to appropriate dimensions (typically ≤1920px width)
2. Compress images (aim for <500KB per image)
3. Use appropriate format (PNG for screenshots, SVG for diagrams)
4. Verify image displays correctly in documentation

**Tools:**
```bash
# Optimise PNG
optipng -o7 image.png

# Convert to WebP
cwebp -q 80 image.png -o image.webp

# Resize image
convert image.png -resize 1920x image-resized.png
```

---

## Usage in Markdown

**Standard Reference:**
```markdown
![CLI query command](../assets/img/cli-query-command.png)
```

**With Caption:**
```markdown
![Web UI upload page](../assets/img/web-ui-upload-page.png)
*Figure 1: Web UI document upload interface*
```

**Relative Paths from Different Locations:**
- From `docs/`: `assets/img/image.png`
- From `docs/tutorials/`: `../assets/img/image.png`
- From `docs/development/planning/`: `../../assets/img/image.png`

---

## Current Images

*(None yet - images will be added as documentation expands)*

---

## Related Documentation

- [Assets Directory](../README.md) - Parent asset directory
- [Documentation Hub](../../README.md) - Main documentation
- [Guides](../../guides/README.md) - Guides using these images

---

**Maintained By:** ragged development team

**License:** GPL-3.0
