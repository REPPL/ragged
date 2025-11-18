# Research Papers Guide

**Status**: Coming in v0.3.0

This guide will cover using ragged for academic literature management, including:
- Organising research papers and academic literature
- Citation workflows and source tracking
- Literature review processes
- Systematic research methodologies

---

## For Now

While this guide is in development, you can still use ragged effectively for research papers:

### Quick Start

1. **Add your papers**:
   ```bash
   ragged add ~/Research/Papers/
   ```

2. **Tag by field and year**:
   ```bash
   ragged metadata update smith-2023.pdf --set category=research --set year=2023 --set field=neuroscience
   ragged metadata update jones-2022.pdf --set category=research --set year=2022 --set field=ml
   ```

3. **Query by topic**:
   ```bash
   ragged query "What methodologies were used in neuroscience studies?"
   ragged query "What are the key findings about neural networks?" --metadata field=ml
   ```

---

## Relevant Features

**See these guides for features useful for research**:

- **[CLI Intermediate: Metadata Management](../cli/intermediate.md#metadata-management-tagging-and-organisation)** - Tag papers by author, year, topic, methodology
- **[CLI Intermediate: Advanced Search](../cli/intermediate.md#advanced-search-beyond-basic-querying)** - Find relevant papers quickly
- **[CLI Intermediate: Query History](../cli/intermediate.md#query-history-track-your-research-journey)** - Track your research questions and evolution
- **[CLI Advanced: Backup](../cli/advanced.md#export-and-backup-protect-your-data)** - Protect your research database

---

## Coming Features for Research

**Planned for v0.3.0**:
- Citation extraction and tracking
- Page number references in answers
- BibTeX integration
- Cross-paper concept mapping

---

## Related Documentation

- [Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md) - Installation and setup
- [CLI Essentials](../cli/essentials.md) - Core commands
- [CLI Intermediate](../cli/intermediate.md) - Organisation and advanced search
- [FAQ](../faq.md) - Common research-related questions

---

**Full guide coming in**: v0.3.0 (see [Version Roadmap](../../development/roadmap/version/README.md))
