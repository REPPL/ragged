# Personal Notes Guide


This guide will cover using ragged for personal knowledge management, including:
- Organising personal notes and insights
- Building a "second brain"
- Retrieving information from journals, logs, and scattered notes
- Best practices for personal knowledge bases

---

## For Now

While this guide is in development, you can still use ragged effectively for personal notes:

### Quick Start

1. **Add your notes**:
   ```bash
   ragged add ~/Documents/Notes/
   ```

2. **Tag by topic**:
   ```bash
   ragged metadata update journal-2025-11.md --set type=journal --set topic=personal
   ragged metadata update ideas.md --set type=ideas --set topic=projects
   ```

3. **Query your notes**:
   ```bash
   ragged query "What did I learn about meditation?"
   ragged query "What project ideas have I captured?"
   ```

---

## Relevant Features

**See these guides for features useful for personal notes**:

- **[CLI Intermediate: Metadata Management](../cli/intermediate.md#metadata-management-tagging-and-organisation)** - Tag and organise notes by topic, date, or type
- **[CLI Intermediate: Query History](../cli/intermediate.md#query-history-track-your-research-journey)** - Track your thinking over time
- **[CLI Essentials: Interactive Mode](../cli/essentials.md#interactive-mode)** - Conversational exploration of your notes

---

## Related Documentation

- [Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md) - Installation and setup
- [CLI Essentials](../cli/essentials.md) - Core commands
- [CLI Intermediate](../cli/intermediate.md) - Organisation and metadata
- [FAQ](../faq.md) - Common questions

---

**Full guide coming in**: v0.3.0 (see [Version Roadmap](../../development/roadmap/version/README.md))
