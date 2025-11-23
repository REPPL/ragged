# ragged project justfile
# https://just.systems/
#
# Common development tasks for ragged project
# Run `just` or `just --list` to see all available commands

# Default recipe (show help)
default:
    @just --list

# === Setup & Installation ===

# Install ragged in development mode with all dependencies
install:
    python3.12 -m venv .venv
    .venv/bin/pip install --upgrade pip setuptools wheel
    .venv/bin/pip install -e ".[dev]"
    @echo "✓ Installation complete. Activate venv with: source .venv/bin/activate"

# Complete project setup (venv + Docker + direnv)
setup: install docker-up
    @echo "✓ Setup complete!"
    @echo "  • Virtual environment: .venv"
    @echo "  • Docker services: running"
    @echo "  • Run 'direnv allow' to enable auto-activation"

# Clean build artifacts and caches
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    rm -rf .pytest_cache/
    rm -rf .mypy_cache/
    rm -rf .ruff_cache/
    rm -rf htmlcov/
    find . -type d -name '__pycache__' -exec rm -rf {} +
    find . -type f -name '*.pyc' -delete
    @echo "✓ Cleaned build artifacts"

# === Docker Commands ===

# Start Docker services (API, UI, ChromaDB)
docker-up:
    docker compose up -d
    @echo "✓ Docker services started"
    @echo "  • API: http://localhost:8000"
    @echo "  • UI:  http://localhost:7860"

# Stop Docker services
docker-down:
    docker compose down
    @echo "✓ Docker services stopped"

# View Docker service logs
docker-logs service="":
    #!/usr/bin/env bash
    if [ -z "{{service}}" ]; then
        docker compose logs -f
    else
        docker compose logs -f {{service}}
    fi

# Rebuild Docker images without cache
docker-rebuild:
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    @echo "✓ Docker services rebuilt and restarted"

# Show Docker service status
docker-status:
    docker compose ps

# === ragged CLI Commands ===

# Run ragged CLI with arguments (auto-activates venv)
ragged *args:
    .venv/bin/ragged {{args}}

# Show ragged version
version:
    .venv/bin/ragged --version

# Run ragged health check
health:
    .venv/bin/ragged health

# Ingest a PDF document
ingest-pdf path:
    .venv/bin/ragged ingest pdf {{path}}

# Query ragged with text
query text:
    .venv/bin/ragged query text "{{text}}"

# === Testing ===

# Run all tests
test:
    .venv/bin/pytest

# Run tests with coverage report
test-cov:
    .venv/bin/pytest --cov=src --cov-report=html --cov-report=term
    @echo "✓ Coverage report: htmlcov/index.html"

# Run specific test file or directory
test-file path:
    .venv/bin/pytest {{path}}

# Run tests matching a keyword
test-match keyword:
    .venv/bin/pytest -k {{keyword}}

# Run only unit tests (fast)
test-unit:
    .venv/bin/pytest -m unit

# Run integration tests
test-integration:
    .venv/bin/pytest -m integration

# Run tests in watch mode (requires pytest-watch)
test-watch:
    .venv/bin/ptw

# === Code Quality ===

# Format code with black
format:
    .venv/bin/black src/ tests/
    @echo "✓ Code formatted"

# Lint code with ruff
lint:
    .venv/bin/ruff check src/ tests/

# Fix linting issues automatically
lint-fix:
    .venv/bin/ruff check --fix src/ tests/

# Type check with mypy
typecheck:
    .venv/bin/mypy src/

# Run all quality checks (format + lint + typecheck)
check: format lint typecheck
    @echo "✓ All quality checks passed"

# === Documentation ===

# Serve documentation locally
docs-serve:
    .venv/bin/mkdocs serve

# Build documentation
docs-build:
    .venv/bin/mkdocs build

# === Git & Release ===

# Show git status
status:
    git status

# Create a new git branch
branch name:
    git checkout -b {{name}}

# Commit changes with conventional commit message
commit type message:
    #!/usr/bin/env bash
    git add .
    git commit -m "{{type}}: {{message}}"

# Push current branch to origin
push:
    git push -u origin $(git branch --show-current)

# === Maintenance ===

# Update Python dependencies
update-deps:
    .venv/bin/pip install --upgrade pip setuptools wheel
    .venv/bin/pip install --upgrade -e ".[dev]"
    @echo "✓ Dependencies updated"

# Security audit of dependencies
audit:
    .venv/bin/pip-audit

# Show outdated packages
outdated:
    .venv/bin/pip list --outdated

# === Utility Commands ===

# Open Python REPL with ragged imported
repl:
    .venv/bin/ipython -c "import ragged; from ragged import *"

# Show environment information
env-info:
    @echo "Python: $(python3.12 --version)"
    @echo "Virtual env: .venv"
    @echo "ragged version: $(.venv/bin/ragged --version 2>&1 || echo 'not installed')"
    @echo "Docker status:"
    @docker compose ps 2>/dev/null || echo "  Docker not running"

# Open project in default editor
edit:
    $EDITOR .

# Show this help
help:
    @just --list
