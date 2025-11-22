# ADR-0017: Code Quality Standards

**Status**: Accepted

**Date**: 2025-11-22

**Context**: v0.4.4 Release

---

## Context

As ragged evolves from experimental prototype to production-ready system, we need consistent code quality standards to ensure maintainability, security, and performance. Version 0.4.4 establishes baseline quality metrics and enforcement mechanisms.

## Decision

We adopt comprehensive code quality standards enforced through automated tooling and CI/CD integration.

## Standards

### 1. Code Style

**Tool**: Ruff (replaces Black + isort + Flake8)

**Configuration**:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
    "S",    # flake8-bandit (security)
]
```

**Rationale**:
- Ruff is 10-100x faster than existing tools
- Single tool replaces multiple formatters/linters
- Built-in security checking (bandit rules)
- Modern Python idioms (pyupgrade)

### 2. Type Safety

**Tool**: mypy (strict mode)

**Requirements**:
- 100% type hint coverage for public APIs
- Strict mode enabled (\`--strict\`)
- No \`Any\` types without justification
- Protocol definitions for duck typing

**Configuration**:
```toml
[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true
warn_return_any = true
strict_equality = true
```

**Rationale**:
- Catches bugs at development time
- Improves code documentation
- Enables better IDE support
- Prevents common runtime errors

### 3. Code Complexity

**Targets**:
- **Cyclomatic complexity**: <10 per function (target: <8)
- **Function length**: <50 lines (target: <30)
- **File length**: <500 lines (target: <300)
- **Nesting depth**: <4 levels (target: <3)

**Measurement**:
```bash
# Radon for complexity metrics
radon cc src/ --min B  # Show complexity B and above
radon mi src/  # Maintainability index
```

**Rationale**:
- Simpler code is easier to test
- Reduces cognitive load for reviewers
- Fewer bugs in simple code
- Easier to refactor and maintain

### 4. Test Coverage

**Tool**: pytest-cov

**Requirements**:
- **Minimum coverage**: 70% overall
- **Target coverage**: 80%+ for core modules
- **Critical paths**: 100% coverage required
- **No coverage decrease**: CI fails if coverage drops

**Configuration**:
```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-report=html"
```

**Rationale**:
- Confidence in refactoring
- Catch regressions early
- Document expected behaviour
- Support safe evolution

### 5. Security Standards

**Tools**:
- Bandit (Python security linter)
- Safety (dependency vulnerability scanner)
- pip-audit (alternative dependency scanner)

**Requirements**:
- **Zero critical vulnerabilities** in code
- **Zero high vulnerabilities** in dependencies
- **Security review** for all plugin code
- **No pickle usage** anywhere in codebase

**Enforcement**:
```bash
# Pre-commit checks
bandit -r src/ --severity-level high
safety check
pip-audit
```

**Rationale**:
- Privacy-first principles require robust security
- Plugin system introduces untrusted code
- Dependencies are common attack vector
- Proactive security cheaper than reactive

### 6. Documentation Standards

**Requirements**:
- **Docstrings**: Google style, all public APIs
- **Type hints**: In docstrings and function signatures
- **Examples**: For complex functions
- **Architecture docs**: Updated with significant changes

**Format** (Google Style):
```python
def process_document(document: Document, options: ProcessOptions | None = None) -> list[Chunk]:
    """Process a document into chunks with contextual enrichment.

    Args:
        document: Document to process
        options: Optional processing options

    Returns:
        List of enriched chunks

    Raises:
        ProcessingError: If document processing fails

    Examples:
        >>> doc = Document(content="text", metadata={})
        >>> chunks = process_document(doc)
        >>> len(chunks) > 0
        True
    """
```

**Rationale**:
- Self-documenting code
- Better IDE support
- Easier onboarding
- Professional presentation

### 7. Import Organisation

**Standard**: isort via Ruff

**Order**:
1. Standard library imports
2. Third-party imports
3. Local application imports

**Format**:
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np
from pydantic import BaseModel

# Local
from src.config import get_settings
from src.utils.logging import get_logger
```

**Rationale**:
- Consistent, readable imports
- Easy to spot missing dependencies
- Reduces merge conflicts

## Quality Metrics

### Baseline (v0.3.4b)

- Linting warnings: ~1800
- Type coverage: ~90%
- Cyclomatic complexity: High in 10-15 functions
- Test coverage: ~75%
- Security: Unknown baseline

### Target (v0.4.4+)

- **Linting**: 0 errors, <158 acceptable warnings
- **Type coverage**: 100% (with allowed exceptions)
- **Cyclomatic complexity**: Reduced 15%+ from baseline
- **Test coverage**: Maintained at 80%+
- **Security**: Zero high/critical vulnerabilities

## Enforcement

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        args: [--strict]
```

### CI/CD Integration

```yaml
# .github/workflows/quality.yml
- name: Lint
  run: ruff check src/

- name: Type Check
  run: mypy src/ --strict

- name: Security Scan
  run: |
    bandit -r src/ --severity-level high
    safety check

- name: Test Coverage
  run: pytest --cov=src --cov-fail-under=70
```

### Development Workflow

1. **Write code** following standards
2. **Pre-commit hooks** run automatically
3. **Fix issues** flagged by hooks
4. **Run tests** locally: \`pytest\`
5. **Push changes** - CI validates
6. **Review** includes quality checks
7. **Merge** only if all checks pass

## Exceptions

### Acceptable Warnings

- **S104** (binding to 0.0.0.0): Web servers need external access
- **ARG001/ARG002** (unused arguments): Interface compliance, future use
- **Import errors**: Third-party library stubs (with \`# type: ignore\`)

### Legacy Code

- **Grandfathered**: Existing code may have tech debt
- **New code**: Must meet all standards
- **Refactoring**: Gradually improve legacy code
- **No degradation**: New code can't make quality worse

## Consequences

### Positive

- **Higher quality codebase**: Fewer bugs, easier maintenance
- **Faster reviews**: Automated checks reduce manual review load
- **Better documentation**: Self-documenting code
- **Security confidence**: Proactive vulnerability detection
- **Performance awareness**: Baseline tracking prevents regressions

### Negative

- **Initial overhead**: Setting up tooling and CI
- **Learning curve**: Developers must learn tools
- **False positives**: Some warnings may be spurious
- **Slower commits**: Pre-commit hooks add time

### Mitigation

- **Gradual adoption**: Don't fix everything at once
- **Clear documentation**: Provide guides and examples
- **Flexible rules**: Allow justified exceptions
- **Fast tools**: Ruff is very fast, minimises overhead

## Related Documentation

- [Security Guidelines](../../guides/security-guidelines.md) - Security standards
- [Performance Tuning Guide](../../guides/performance-tuning.md) - Performance baseline
- [v0.4.4 Roadmap](../../roadmap/version/v0.4/v0.4.4.md) - Code quality release plan

---

**Decision**: Accepted

**Approved By**: ragged development team

**Effective**: v0.4.4

**Review**: v0.5.0 (assess effectiveness, adjust if needed)
