# CLI Features Guide: Choose Your Path

Welcome to ragged's command-line interface (CLI) documentation. This guide helps you find the right resources for your skill level.

---

## Quick Navigation

**New to ragged?** → [CLI Essentials](./essentials.md)

**Have 20+ documents and want to organise them?** → [CLI Intermediate](./intermediate.md)

**Running ragged in production or want advanced features?** → [CLI Advanced](./advanced.md)

---

## The Three-Part Series

We've split CLI documentation into three progressive guides:

### 1. CLI Essentials (Beginners)

**Who it's for**: New ragged users who want to get started quickly.

**What you'll learn**:
- The 5 core commands (health, add, query, list, config)
- Basic document ingestion
- Simple querying
- Viewing your collection
- Managing configuration

**Time to complete**: 10-15 minutes reading

**Start here**: **[CLI Essentials Guide →](./essentials.md)**

---

### 2. CLI Intermediate (Organisation & Power Features)

**Who it's for**: Users with growing collections who need better organisation.

**What you'll learn**:
- Metadata management (tagging documents)
- Advanced search without AI generation
- Query history tracking and replay
- Verbosity control
- Practical workflows for research and organisation

**Prerequisites**: Comfortable with essentials

**Time to complete**: 15-20 minutes reading

**Continue here**: **[CLI Intermediate Guide →](./intermediate.md)**

---

### 3. CLI Advanced (Power Users)

**Who it's for**: Power users, system administrators, and developers.

**What you'll learn**:
- Cache management for performance
- Backup and restore operations
- Configuration validation
- Environment information for debugging
- Shell completion
- Advanced configuration techniques
- Troubleshooting complex issues

**Prerequisites**: Comfortable with essentials and intermediate features

**Time to complete**: 15-20 minutes reading

**Master it here**: **[CLI Advanced Guide →](./advanced.md)**

---

## Complete Command List

All ragged CLI commands organised by category:

### Core Operations
- `ragged add` - Add documents ([Essentials](./essentials.md#2-ragged-add---add-documents))
- `ragged query` - Ask questions ([Essentials](./essentials.md#3-ragged-query---ask-questions))
- `ragged list` - View documents ([Essentials](./essentials.md#4-ragged-list---view-documents))
- `ragged clear` - Remove documents ([Essentials](./essentials.md#remove-documents))
- `ragged health` - Check service status ([Essentials](./essentials.md#1-ragged-health---check-system-status))
- `ragged config` - Manage configuration ([Essentials](./essentials.md#5-ragged-config---manage-configuration))

### Organisation (Intermediate)
- `ragged metadata` - Tag and organise documents ([Intermediate](./intermediate.md#metadata-management-tagging-and-organisation))
  - `ragged metadata update` - Add/change tags
  - `ragged metadata show` - View document tags
  - `ragged metadata list` - See all metadata
  - `ragged metadata search` - Find by tags
- `ragged search` - Search without AI generation ([Intermediate](./intermediate.md#advanced-search-beyond-basic-querying))
- `ragged history` - Query history tracking ([Intermediate](./intermediate.md#query-history-track-your-research-journey))
  - `ragged history list` - View past queries
  - `ragged history show` - Show query details
  - `ragged history replay` - Re-run a query
  - `ragged history export` - Export history
  - `ragged history clear` - Clear history

### System Maintenance (Advanced)
- `ragged cache` - Manage caches ([Advanced](./advanced.md#cache-management-performance-and-disk-space))
  - `ragged cache info` - View cache stats
  - `ragged cache clear` - Clear caches
- `ragged export` - Export and backup ([Advanced](./advanced.md#export-and-backup-protect-your-data))
  - `ragged export backup` - Create backup
- `ragged validate` - Validate configuration ([Advanced](./advanced.md#configuration-validation-catch-issues-early))
- `ragged env-info` - Environment information ([Advanced](./advanced.md#environment-information-debug-and-report-issues))
- `ragged completion` - Shell completion ([Advanced](./advanced.md#shell-completion-faster-command-entry))

---

## Learning Paths

### Path 1: Quick Start (Beginners)

**Goal**: Get ragged working and ask your first question.

**Steps**:
1. Complete [installation](../../tutorials/complete-beginners-guide.md#installation-step-by-step)
2. Learn [5 essential commands](./essentials.md)
3. Add your first 5-10 documents
4. Practice querying

**Time**: 1-2 hours total

---

### Path 2: Research Workflow (Intermediate)

**Goal**: Manage 50-200 research documents effectively.

**Steps**:
1. Master [CLI Essentials](./essentials.md)
2. Learn [metadata management](./intermediate.md#metadata-management-tagging-and-organisation)
3. Use [query history](./intermediate.md#query-history-track-your-research-journey)
4. Follow [Research Papers Guide](../use-cases/research-papers.md)

**Time**: 3-4 hours total

---

### Path 3: Power User (Advanced)

**Goal**: Production-ready setup with backups and optimisation.

**Steps**:
1. Complete Essentials and Intermediate
2. Set up [automated backups](./advanced.md#backup-strategies)
3. Configure [shell completion](./advanced.md#shell-completion-faster-command-entry)
4. Implement [cache management](./advanced.md#cache-management-performance-and-disk-space)
5. Tune [performance settings](./advanced.md#performance-tuning)

**Time**: 5-6 hours total

---

## Quick Reference by Task

**I want to...**

### ...add documents
- **Single file**: [Essentials: Adding Documents](./essentials.md#2-ragged-add---add-documents)
- **Folder**: [Essentials: Folder Ingestion](./essentials.md#folder-ingestion-options)
- **With metadata**: [Intermediate: Metadata Management](./intermediate.md#adding-metadata-to-documents)

### ...ask questions
- **Simple query**: [Essentials: Querying](./essentials.md#3-ragged-query---ask-questions)
- **With filters**: [Intermediate: Advanced Search](./intermediate.md#advanced-search-beyond-basic-querying)
- **Interactive mode**: [Essentials: Interactive Mode](./essentials.md#interactive-mode)

### ...organise my collection
- **Tag documents**: [Intermediate: Metadata Management](./intermediate.md#metadata-management-tagging-and-organisation)
- **Search by tags**: [Intermediate: Search by Metadata](./intermediate.md#search-by-metadata)
- **View organisation**: [Intermediate: List Metadata](./intermediate.md#list-all-metadata-keys-and-values)

### ...track my research
- **View query history**: [Intermediate: Query History](./intermediate.md#view-query-history)
- **Replay queries**: [Intermediate: Replay a Query](./intermediate.md#replay-a-query)
- **Export history**: [Intermediate: Export Query History](./intermediate.md#export-query-history)

### ...maintain my system
- **Backup data**: [Advanced: Export and Backup](./advanced.md#create-a-backup)
- **Clear cache**: [Advanced: Cache Management](./advanced.md#clear-specific-caches)
- **Validate setup**: [Advanced: Configuration Validation](./advanced.md#basic-validation)
- **Debug issues**: [Advanced: Environment Information](./advanced.md#basic-environment-info)

### ...improve performance
- **Shell completion**: [Advanced: Install Completion](./advanced.md#install-completion)
- **Cache tuning**: [Advanced: Cache Best Practices](./advanced.md#cache-best-practices)
- **Performance tuning**: [Advanced: Performance Tuning](./advanced.md#performance-tuning)

---

## Common Questions

### Which guide should I start with?

**If you've never used ragged**: Start with [CLI Essentials](./essentials.md). Don't skip ahead - the essentials are critical foundations.

**If you can already add/query/list**: Move to [CLI Intermediate](./intermediate.md) when you have 20+ documents and need organisation.

**If you're running ragged daily**: Read [CLI Advanced](./advanced.md) for backups, caching, and optimisation.

---

### Do I need to read all three guides?

**No.** Most users only need Essentials.

**Intermediate** features become useful as your collection grows (50+ documents).

**Advanced** features are for power users, production deployments, and heavy daily use.

Read what you need when you need it.

---

### What if I'm stuck?

1. **Check the relevant guide**: Essentials/Intermediate/Advanced
2. **Try the FAQ**: [Frequently Asked Questions](../faq.md)
3. **Troubleshooting guide**: [Setup Issues](../troubleshooting/setup-issues.md)
4. **Ask for help**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)

---

### Can I use ragged without reading any guides?

**Yes**, but you'll learn faster with the guides.

**Absolute minimum**:
1. Read [Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md) (30 min)
2. Run these commands:
   ```bash
   ragged health
   ragged add document.pdf
   ragged query "What is this about?"
   ```

That's enough to be productive. Learn more features as needed.

---

## Additional Resources

### Before you start
- **[Complete Beginner's Guide](../../tutorials/complete-beginners-guide.md)** - Installation and first steps
- **[Understanding RAG](../../explanation/rag-for-users.md)** - How ragged works conceptually
- **[User Glossary](../../reference/terminology/user-glossary.md)** - Technical terms explained

### Use case guides
- **[Personal Notes Guide](../use-cases/personal-notes.md)** - Organise personal knowledge
- **[Research Papers Guide](../use-cases/research-papers.md)** - Academic literature management

### Reference
- **[Command Reference](../../reference/cli/command-reference.md)** - Complete technical specification
- **[Configuration Guide](../configuration.md)** - All settings explained
- **[FAQ](../faq.md)** - Common questions answered

### Getting help
- **[Troubleshooting Guide](../troubleshooting/setup-issues.md)** - Fix common problems
- **[GitHub Issues](https://github.com/REPPL/ragged/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/REPPL/ragged/discussions)** - Ask questions

---

## Version Information

**Current version**: 0.2.8

These guides document features available in ragged v0.2.8. Some features mentioned as "future" or "planned" will arrive in upcoming versions:

- **v0.2.9** (next): Embedder caching, batch optimisation, performance improvements
- **v0.3.0**: Citations with page numbers, import functionality, configuration UI
- **v0.4.0**: Multilingual support, advanced PDF processing
- **v0.5.0**: Vision support, OCR, image understanding

See the [Version Roadmap](../../development/roadmap/version/README.md) for details.

---

## Feedback

Found an error in these guides? Have a suggestion?

- **Documentation issues**: [Report on GitHub](https://github.com/REPPL/ragged/issues)
- **Feature requests**: [Discuss on GitHub](https://github.com/REPPL/ragged/discussions)
- **Pull requests**: [Contributing Guide](../../CONTRIBUTING.md)

---

**Ready to start?** Choose your guide:

- 🟢 **[CLI Essentials](./essentials.md)** - Start here if you're new
- 🟡 **[CLI Intermediate](./intermediate.md)** - Level up your organisation
- 🔴 **[CLI Advanced](./advanced.md)** - Master advanced features

Happy querying! 🚀
