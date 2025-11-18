# Python API Reference

**Status:** Coming in v0.3

Python API reference documentation will be generated from docstrings.

## Available Now

For Python API usage:

- **Source code documentation** - Browse the `src/` directory for inline docstrings
- **[CLI source code](../../../src/cli/)** - Examples of API usage in CLI commands
- **Type hints** - Full type annotation coverage for IDE autocomplete

## API Structure

ragged's Python API is organised into modules:

- `ragged.ingestion` - Document loading and processing
- `ragged.chunking` - Text chunking strategies
- `ragged.embeddings` - Embedding generation
- `ragged.retrieval` - Document retrieval
- `ragged.generation` - Answer generation
- `ragged.storage` - Vector store operations

## What's Coming

The API reference will include:
- Complete function/class documentation auto-generated from docstrings
- Usage examples for each module
- Type signatures and return values
- Common patterns and best practices
- Integration examples

## Current API Usage

Until formal API documentation is available, the best way to understand the API is to:

1. Read the CLI command source code in `src/cli/commands/`
2. Review the docstrings in the source modules
3. Use IDE autocomplete with type hints

---

**Status:** Planned for v0.3 (auto-generated from docstrings with Sphinx)
