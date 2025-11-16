# ragged Development Scripts

This directory contains scripts to help with development, maintenance, and deployment of ragged.

## Directory Structure

```
scripts/
├── dev/          # Development tools
├── maintenance/  # Maintenance and migration scripts
└── README.md     # This file
```

## Development Scripts (`dev/`)

### `setup.sh`

Sets up the development environment from scratch.

**Usage:**
```bash
./scripts/dev/setup.sh
```

**What it does:**
- Checks Python 3.12 installation
- Creates virtual environment
- Installs dependencies
- Sets up .env file
- Installs pre-commit hooks
- Optionally starts ChromaDB
- Verifies setup with tests

**First time setup:** Run this script when setting up the project for the first time.

---

### `test.sh`

Runs the test suite with various options.

**Usage:**
```bash
./scripts/dev/test.sh [unit|integration|all|coverage]
```

**Options:**
- `unit` (default) - Run unit tests only (fast, no services required)
- `integration` - Run integration tests (requires ChromaDB)
- `all` - Run all tests
- `coverage` - Run with coverage report and generate HTML report

**Examples:**
```bash
# Quick unit tests
./scripts/dev/test.sh

# All tests with coverage
./scripts/dev/test.sh coverage

# Integration tests only
./scripts/dev/test.sh integration
```

**Requirements:**
- Unit tests: None
- Integration tests: ChromaDB running on port 8001
- Coverage: Generates `htmlcov/` directory

---

### `lint.sh`

Runs all code quality checks.

**Usage:**
```bash
./scripts/dev/lint.sh [--fix]
```

**What it checks:**
1. **Black** - Code formatting (line length 100)
2. **Ruff** - Linting (comprehensive rules)
3. **MyPy** - Type checking (strict mode)
4. **Bandit** - Security scanning
5. **Common issues** - Debugger statements, print() calls, TODOs

**Options:**
- `--fix` - Automatically fix issues where possible

**Examples:**
```bash
# Check without fixing
./scripts/dev/lint.sh

# Check and auto-fix
./scripts/dev/lint.sh --fix
```

**Exit codes:**
- `0` - All checks passed
- `1` - Some checks failed

---

### `format.sh`

Auto-formats code to match project standards.

**Usage:**
```bash
./scripts/dev/format.sh
```

**What it does:**
1. Runs Black formatter (line length 100)
2. Applies Ruff auto-fixes
3. Sorts imports

**When to use:**
- Before committing code
- After making significant changes
- When linter reports formatting issues

**Note:** This modifies files in place. Commit your changes first if you want to review the formatting changes separately.

---

## Maintenance Scripts (`maintenance/`)

### `migrate-config.py`

Migrates configuration files between versions.

**Status:** 📋 Planned for v0.3+

**Future usage:**
```bash
python scripts/maintenance/migrate-config.py --from 0.2 --to 0.3
```

Will handle breaking changes in configuration schema between versions.

---

## Making Scripts Executable

Before running any script, make it executable:

```bash
chmod +x scripts/dev/*.sh
chmod +x scripts/maintenance/*.py
```

Or make all scripts executable at once:

```bash
find scripts/ -type f -name "*.sh" -o -name "*.py" | xargs chmod +x
```

---

## Development Workflow

### Daily Development

1. **Start your session:**
   ```bash
   source venv/bin/activate
   docker-compose up -d chromadb  # If needed
   ```

2. **Before committing:**
   ```bash
   ./scripts/dev/format.sh        # Format code
   ./scripts/dev/lint.sh          # Check for issues
   ./scripts/dev/test.sh unit     # Quick unit tests
   ```

3. **Before creating PR:**
   ```bash
   ./scripts/dev/lint.sh --fix    # Fix all auto-fixable issues
   ./scripts/dev/test.sh all      # Run all tests
   ./scripts/dev/test.sh coverage # Check coverage
   ```

### Pre-commit Hooks

The setup script installs pre-commit hooks that automatically run on `git commit`:

- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Python syntax checking
- Black formatting
- Ruff linting
- MyPy type checking
- Bandit security scanning

**Bypass hooks** (not recommended):
```bash
git commit --no-verify
```

---

## CI/CD Integration

These scripts are used by GitHub Actions workflows:

- `.github/workflows/ci.yml` - Runs `lint.sh` and `test.sh` on every PR
- Coverage reports are generated and uploaded
- Build artifacts are created

See `.github/workflows/` for CI/CD configuration.

---

## Adding New Scripts

When adding new scripts:

1. **Naming:** Use descriptive names with `.sh` or `.py` extension
2. **Shebang:** Start with `#!/usr/bin/env bash` or `#!/usr/bin/env python3`
3. **Error handling:** Use `set -euo pipefail` in bash scripts
4. **Documentation:** Add description and usage to this README
5. **Executable:** Make it executable with `chmod +x`
6. **Idempotent:** Scripts should be safe to run multiple times

---

## Troubleshooting

### Permission Denied

```bash
chmod +x scripts/dev/setup.sh
./scripts/dev/setup.sh
```

### Script Not Found

Ensure you're in the project root directory:
```bash
cd /path/to/ragged
./scripts/dev/test.sh
```

### Dependencies Missing

Run setup script to install all dependencies:
```bash
./scripts/dev/setup.sh
```

### ChromaDB Not Running

Start ChromaDB:
```bash
docker-compose up -d chromadb

# Or check status
docker-compose ps
```

---

## Platform-Specific Notes

### macOS

- Scripts use bash-specific features
- Some commands may need Homebrew packages
- Docker Desktop recommended for ChromaDB

### Linux

- Scripts should work out of the box
- May need to install Docker separately
- Use native package manager for system deps

### Windows

- Use Git Bash or WSL2
- Native Windows support coming in future versions
- Docker Desktop recommended

---

## Questions?

See main project documentation in `docs/` or the [CONTRIBUTING.md](../../CONTRIBUTING.md) guide.
