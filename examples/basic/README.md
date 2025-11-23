# Basic Examples

**Purpose:** Simple, concise examples for quick reference and getting started

---

## Overview

This directory contains basic, minimal examples that demonstrate ragged's core functionality. These examples are designed for quick reference, copy-paste usage, and understanding fundamental concepts.

---

## Available Examples

### [quickstart.md](./quickstart.md)

**Purpose:** Fastest way to get ragged running

**Contents:**
- 5-minute installation guide
- Minimal Docker setup
- First document ingestion
- First query
- Verification steps

**Audience:** New users who want to see ragged working immediately

**Format:** Step-by-step commands with brief explanations

---

## What Belongs Here

**✅ Include:**
- Minimal working examples (5-15 lines of code)
- Quick reference snippets
- Basic workflow demonstrations
- Copy-pasteable command sequences

**❌ Don't Include:**
- Comprehensive tutorials (goes in `docs/tutorials/`)
- Interactive notebooks (goes in `examples/notebooks/`)
- Configuration examples (goes in `examples/configs/`)
- Advanced use cases (goes in documentation)

---

## Using Basic Examples

### Quick Reference

**Need to see ragged working in 5 minutes?**
→ Read [quickstart.md](./quickstart.md)

**Need detailed learning?**
→ See [Jupyter Notebooks](../notebooks/README.md)

**Need configuration examples?**
→ See [Config Examples](../configs/README.md)

**Need comprehensive guides?**
→ See [Documentation](../../docs/)

### Running Examples

Most basic examples are command-line sequences:

```bash
# Copy commands from example file
cat quickstart.md

# Paste into terminal
# Execute step-by-step

# Verify results
```

---

## Example Standards

### Format

**Markdown files preferred:**
- Clear section headers
- Numbered steps
- Copy-pasteable commands
- Brief explanations (1-2 sentences)

### Code Style

**Keep it simple:**
- No error handling (show happy path)
- Minimal dependencies
- Inline comments for clarity
- British English in all text

### Length

**Target:** 10-30 lines of code maximum per example

**If longer:** Consider moving to:
- `docs/tutorials/` (comprehensive guides)
- `examples/notebooks/` (interactive learning)

---

## Contributing Examples

### Creating a New Basic Example

1. **Identify a simple, common task**
   - Single concept per example
   - Something users do frequently
   - Can be shown in <30 lines

2. **Create markdown file:**
   ```markdown
   # Example: [Clear Title]

   **Purpose:** One sentence description

   ## Prerequisites

   - Bullet list of requirements

   ## Steps

   1. First step with command
      ```bash
      command here
      ```

   2. Second step...

   ## Expected Output

   Show what success looks like.
   ```

3. **Test the example completely:**
   - Fresh environment
   - Copy-paste every command
   - Verify it works

4. **Add to this README** in "Available Examples" section

---

## Related Documentation

- [Quickstart Guide](./quickstart.md) - 5-minute getting started
- [Jupyter Notebooks](../notebooks/README.md) - Interactive tutorials
- [Configuration Examples](../configs/README.md) - Config file templates
- [Installation Guide](../../docs/tutorials/installation.md) - Detailed setup
- [Multi-Modal Tutorial](../../docs/tutorials/multimodal-workflow.md) - Complete workflow

---

**Status**: Active (1 example)
