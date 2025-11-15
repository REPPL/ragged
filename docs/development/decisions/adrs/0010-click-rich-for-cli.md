# ADR-0010: Click + Rich for CLI

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** CLI Interface

## Context

Need a user-friendly, professional command-line interface with:
- Clear command structure
- Progress feedback for long operations
- Good error handling and messages
- Professional appearance
- Easy testing

## Decision

Use Click for CLI framework and Rich for terminal formatting.

- **Click**: Handles commands, arguments, options, validation
- **Rich**: Provides beautiful terminal output, tables, progress bars, syntax highlighting

## Rationale

- **Click**: Industry-standard CLI framework with clean API and excellent documentation
- **Rich**: Beautiful terminal output builds user trust and improves usability
- **Separation of Concerns**: Click handles command logic, Rich handles presentation
- **User Experience**: Progress bars and colours significantly improve perceived responsiveness
- **Professional**: Polished appearance builds trust in the tool
- **Developer Experience**: Easy to build and test CLIs
- **Testing**: CliRunner makes testing straightforward

## Alternatives Considered

### 1. argparse + print

**Pros:**
- Standard library (no dependencies)
- Familiar to Python developers
- Lightweight

**Cons:**
- Verbose implementation
- Ugly plain text output
- No progress indicators
- More code for same functionality

**Rejected:** Poor user experience, more development effort

### 2. typer

**Pros:**
- Type hints for CLI definitions
- Based on Click (proven foundation)
- Modern Python approach

**Cons:**
- Extra layer of abstraction
- Less mature than Click
- Smaller community

**Rejected:** Unnecessary abstraction for v0.1

### 3. docopt

**Pros:**
- Declarative CLI from docstrings
- Minimal code

**Cons:**
- Less flexible for complex CLIs
- Harder to test programmatically
- Smaller community

**Rejected:** Too limited for future growth

### 4. Click Alone (No Rich)

**Pros:**
- Single dependency
- Still good CLI framework

**Cons:**
- Plain text output only
- No progress bars
- Less professional appearance

**Rejected:** Progress bars are essential for user experience during ingestion

## Implementation

```python
import click
from rich.console import Console
from rich.progress import Progress

console = Console()

@click.group()
def cli():
    """ragged - Privacy-first local RAG system."""
    pass

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--verbose', is_flag=True)
def ingest(path: str, verbose: bool):
    """Ingest documents from PATH."""
    with Progress() as progress:
        task = progress.add_task("Ingesting...", total=100)
        # ... ingestion logic ...
```

## Consequences

### Positive

- Excellent developer experience (easy to add commands)
- Beautiful, professional output
- Progress bars for long operations improve perceived responsiveness
- Easy to test with CliRunner
- Good error messages with formatting
- Colours and tables improve readability
- Users appreciate the polished interface

### Negative

- Two dependencies instead of stdlib only
- Rich adds ~1MB to install size
- Some learning curve for contributors unfamiliar with Click/Rich
- Terminal compatibility issues on some older systems

### Neutral

- Slightly heavier than stdlib solutions but worth the UX improvement
- Industry-standard tools reduce onboarding friction

## User Feedback

Early testing shows users significantly appreciate:
- Progress bars during long ingestion operations
- Coloured error messages (red for errors, yellow for warnings)
- Tables for listing ingested documents
- Professional appearance builds trust

## Related

- [UI Design: CLI Interface](../../planning/interfaces/cli/)
- [User Stories](../../planning/requirements/user-stories/README.md)
