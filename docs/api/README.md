# API Documentation

This directory contains auto-generated API documentation for ragged's Python modules.

## Purpose

This directory is **auto-generated** by Sphinx using the `autodoc` extension to extract docstrings from the Python source code. The documentation provides detailed API reference for all public modules, classes, and functions.

## What Belongs Here

✅ **Auto-generated content** (do not edit manually):
- Sphinx configuration (`conf.py`)
- API reference files (generated from source docstrings)
- Build artefacts in `_build/`
- Sphinx templates and static files

❌ **What does NOT belong here**:
- Manual documentation (use `docs/guides/` or `docs/reference/`)
- Tutorials (use `docs/tutorials/`)
- Architecture documentation (use `docs/explanation/`)

## Building the Documentation

```bash
# Build HTML documentation
cd docs/api
make html

# View built documentation
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
start _build/html/index.html  # Windows
```

## Directory Structure

```
docs/api/
├── README.md           # This file
├── conf.py             # Sphinx configuration
├── index.rst           # Documentation homepage
├── Makefile            # Build automation
├── _build/             # Generated HTML/PDF (gitignored)
├── _static/            # Static assets for generated docs
└── _templates/         # Sphinx templates
```

## Related Documentation

- [Main Documentation Hub](../README.md) - Overview of all documentation
- [Contributing Guide](../guides/contributing.md) - How to contribute to documentation
- [Documentation Standards](../development/process/methodology/documentation-standards.md) - Documentation guidelines

---

**Note**: This directory follows Sphinx documentation conventions. For manually-written documentation, use the appropriate directory in `docs/`.
