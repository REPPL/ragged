# Contributing to ragged

Thank you for considering contributing to ragged! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Commit Guidelines](#commit-guidelines)
- [AI Assistance Transparency](#ai-assistance-transparency)
- [Questions and Support](#questions-and-support)

## Code of Conduct

ragged is a privacy-first, learning-focused project. We expect all contributors to:

- Be respectful and inclusive in all interactions
- Focus on constructive feedback and collaboration
- Prioritise privacy and security in all contributions
- Help others learn and understand the codebase
- Document decisions and reasoning transparently

## Ways to Contribute

### Code Contributions

- **Bug fixes**: Fix issues in the current implementation
- **Features**: Implement planned features from the roadmap
- **Refactoring**: Improve code quality and architecture
- **Performance**: Optimise existing functionality
- **Tests**: Add or improve test coverage

### Documentation Contributions

- **User guides**: Help users understand how to use ragged
- **Tutorials**: Create learning-oriented content
- **Architecture docs**: Document design decisions
- **Code comments**: Improve code documentation
- **Examples**: Add usage examples

### Other Contributions

- **Bug reports**: Report issues you encounter
- **Feature requests**: Propose new features (check roadmap first)
- **Design feedback**: Review and comment on architecture proposals
- **Testing**: Help test new releases
- **Research**: Share relevant RAG research and papers

## Development Setup

### Prerequisites

- **Python 3.12** (strictly required - see `pyproject.toml`)
- **Ollama** (running locally or accessible via network)
- **ChromaDB** (can run via Docker)
- **Git** for version control

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ragged.git
   cd ragged
   ```

2. **Create virtual environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt

   # Install package in editable mode
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env with your local configuration
   # For native development, use:
   # RAGGED_OLLAMA_URL=http://localhost:11434
   # RAGGED_CHROMA_URL=http://localhost:8001
   ```

5. **Start required services**
   ```bash
   # Option 1: Using Docker Compose (recommended)
   docker-compose up -d chromadb

   # Option 2: Run ChromaDB natively
   chroma run --path ~/.ragged/chroma

   # Ensure Ollama is running
   ollama serve
   ```

6. **Verify installation**
   ```bash
   # Run tests
   pytest

   # Run ragged CLI
   ragged --help
   ```

### Development Tools Setup (Coming in v0.2.4)

Once the scripts directory is added:

```bash
# Run development setup script
./scripts/dev/setup.sh

# Run linters
./scripts/dev/lint.sh

# Run tests with coverage
./scripts/dev/test.sh
```

## Code Standards

### Code Style

ragged uses strict code quality tools:

- **Black** (line length 100) for code formatting
- **Ruff** for linting (comprehensive rule set)
- **MyPy** for type checking (strict mode)

**Run before committing:**
```bash
# Format code
black src/ tests/ --line-length 100

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### Type Safety

- Use **type hints** for all function signatures
- Use **Pydantic** models for data validation
- Avoid `Any` types unless absolutely necessary
- Use `Optional[T]` for nullable values

**Example:**
```python
from typing import Optional
from pydantic import BaseModel

def process_document(
    file_path: str,
    chunk_size: int = 500,
    metadata: Optional[dict] = None
) -> list[Chunk]:
    """Process a document into chunks."""
    # Implementation
```

### Code Organisation

- Follow the modular architecture in `src/`
- One class per file for substantial classes
- Group related functionality in modules
- Use clear, descriptive names
- Avoid deep nesting (max 4 levels)

### Error Handling

- Use specific exception types
- Provide informative error messages
- Log errors appropriately (privacy-safe)
- Don't swallow exceptions silently

**Example:**
```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

try:
    document = load_document(path)
except FileNotFoundError:
    logger.error(f"Document not found: {path}")
    raise
except Exception as e:
    logger.error(f"Failed to load document: {e}")
    raise
```

### Security and Privacy

- **Never log sensitive data** (file contents, API keys, user data)
- **Validate all inputs** using Pydantic models
- **Sanitise file paths** to prevent directory traversal
- **Use secure defaults** (e.g., local-only processing)
- **Document privacy implications** in code comments

## Testing Requirements

### Test Coverage

- **Target**: 85% code coverage for v1.0 (currently 68%)
- **Minimum for PR**: Don't decrease coverage
- **New features**: Must include tests

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests (70%)
├── integration/    # Multi-component tests (20%)
└── e2e/           # End-to-end tests (10%)
```

### Writing Tests

**Use pytest markers:**
```python
import pytest

@pytest.mark.unit
def test_chunk_splitting():
    """Test basic chunk splitting."""
    # Test implementation

@pytest.mark.integration
@pytest.mark.requires_ollama
def test_full_pipeline():
    """Test complete RAG pipeline."""
    # Test implementation
```

**Run tests:**
```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# With coverage
pytest --cov=src --cov-report=html

# Specific module
pytest tests/unit/chunking/
```

### Test Quality

- Test edge cases and error conditions
- Use meaningful test names (describe what's being tested)
- Keep tests simple and focused (one concept per test)
- Use fixtures for common setup
- Mock external dependencies (Ollama, ChromaDB)

## Documentation Standards

### Language

**British English** throughout:
- "organise" not "organize"
- "behaviour" not "behavior"
- "colour" not "color"

### Documentation Types

1. **Code Comments**
   - Explain **why**, not what
   - Document complex algorithms
   - Note privacy/security considerations
   - Reference ADRs for architectural decisions

2. **Docstrings**
   - Use Google-style docstrings
   - Document all parameters and return values
   - Include usage examples for complex functions

**Example:**
```python
def retrieve_chunks(
    query: str,
    k: int = 5,
    use_hybrid: bool = True
) -> list[Chunk]:
    """
    Retrieve relevant chunks for a query.

    Args:
        query: The user's question
        k: Number of chunks to retrieve (must be > 0)
        use_hybrid: Whether to use hybrid search (BM25 + vector)

    Returns:
        List of retrieved chunks, ranked by relevance

    Raises:
        ValueError: If k <= 0

    Example:
        >>> chunks = retrieve_chunks("What is RAG?", k=3)
        >>> print(len(chunks))
        3
    """
```

3. **Documentation Files**
   - Follow Diátaxis framework (tutorials, guides, reference, explanation)
   - Use status indicators (✅ 🚧 📋 🔬 ⚠️)
   - Include version information
   - Link to related documentation

### Status Indicators

Use consistent indicators:
- ✅ **Implemented** - Available in current version
- 🚧 **In Progress** - Being actively developed
- 📋 **Planned** - Designed and scheduled
- 🔬 **Research** - Exploratory phase
- ⚠️ **Deprecated** - Will be removed

## Pull Request Process

### Before Creating a PR

1. **Check the roadmap**: Ensure your contribution aligns with project goals
2. **Create an issue**: Discuss significant changes before implementing
3. **Branch off main**: Create a feature branch from latest main
4. **Write tests**: Ensure adequate test coverage
5. **Run quality checks**: Black, Ruff, MyPy, tests must pass
6. **Update documentation**: Add/update relevant documentation
7. **Review your changes**: Self-review the diff before submitting

### Branch Naming

Use descriptive branch names:

```
feature/add-semantic-chunking
fix/logger-import-bug
docs/update-contributing-guide
refactor/split-cli-commands
test/add-retrieval-tests
```

### PR Title and Description

**Title format:**
```
type: Brief description (50 chars max)
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Examples:**
- `feat: Add semantic chunking support`
- `fix: Resolve logger import in settings.py`
- `docs: Add status indicators to planning docs`

**Description should include:**
- What changed and why
- Link to related issue
- Breaking changes (if any)
- Testing performed
- Screenshots (for UI changes)

**Example:**
```markdown
## Summary
Fixes #123 - Add semantic chunking as an alternative to recursive chunking

## Changes
- Added `SemanticChunker` class in `src/chunking/semantic.py`
- Integrated with embedding model for boundary detection
- Added 15 unit tests with 95% coverage
- Updated documentation in `docs/reference/chunking.md`

## Testing
- All existing tests pass
- New tests cover edge cases (empty documents, single sentences)
- Manual testing with various document types

## Breaking Changes
None

## Related
- Part of v0.3 roadmap: `docs/development/roadmaps/version/v0.3.0/`
```

### Review Process

1. **Automated checks**: CI/CD runs tests, linting, type checking
2. **Code review**: Maintainer reviews code quality and architecture
3. **Documentation review**: Check docs are updated and clear
4. **Discussion**: Address feedback and questions
5. **Approval**: Once approved, maintainer will merge

## Commit Guidelines

### Commit Message Format

Follow conventional commits:

```
type(scope): Brief description

Longer explanation if needed. Explain why this change was made,
not just what changed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**
```
feat(chunking): Add semantic chunking strategy

Implements semantic chunking using embedding-based boundary detection.
This provides better context preservation than fixed-size chunking.

Closes #45

---

fix(config): Resolve logger import circular dependency

Moved logger import inside model_post_init to avoid circular import
between settings.py and logging.py.

Fixes #67
```

### Commit Practices

- **Atomic commits**: One logical change per commit
- **Meaningful messages**: Explain the "why"
- **Reference issues**: Link to GitHub issues
- **Sign commits**: Use GPG signing (recommended)

## AI Assistance Transparency

ragged embraces AI-assisted development with transparency:

### If You Use AI Tools

**Please disclose:**
- Which AI tool was used (e.g., Claude Code, GitHub Copilot, ChatGPT)
- What AI generated vs. what you wrote manually
- That you reviewed and understood all AI-generated code

**In commits:**
```
feat(retrieval): Add BM25 keyword search

Implements BM25 algorithm for keyword-based retrieval to complement
vector search in hybrid mode.

AI-assisted: Claude Code generated initial implementation
Reviewed and modified for project standards
```

**In PRs:**
```markdown
## AI Assistance
- Claude Code generated initial implementation of BM25Retriever
- Manual modifications for integration with existing retrieval interface
- All code reviewed and understood before submission
```

### Why We Do This

- **Reproducibility**: Others can understand how code was created
- **Transparency**: Honest about development process
- **Learning**: Distinguish AI assistance from human expertise
- **Research**: Document AI impact on development velocity

See: [AI Assistance Guidelines](docs/development/process/methodology/ai-assistance.md)

## Questions and Support

### Getting Help

- **Documentation**: Check `docs/` for guides and reference
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact project maintainers (see README)

### Reporting Issues

**Bug Reports:**
Include:
- ragged version (`ragged --version`)
- Python version
- Operating system
- Steps to reproduce
- Expected vs. actual behaviour
- Error messages and logs (redact sensitive info)

**Feature Requests:**
Include:
- Use case and motivation
- Proposed solution
- Alternatives considered
- Check roadmap first (`docs/development/roadmaps/`)

---

## Current Project Status

**Version:** v0.2.2 (Developer Beta)

**Breaking changes expected** before v1.0 - see [Versioning Philosophy](docs/development/planning/versions/versioning-philosophy.md)

**Active development focus:**
- v0.2.3-v0.2.7: Incremental improvements
- v0.3.0: Advanced chunking, memory, personas
- v1.0: Production-ready release

**Roadmap:** See `docs/development/roadmaps/version/`

---

## License

By contributing to ragged, you agree that your contributions will be licensed under the GPL-3.0 licence.

---

Thank you for contributing to ragged! Your efforts help build a better privacy-first RAG system for everyone.
