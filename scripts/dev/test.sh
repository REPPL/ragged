#!/usr/bin/env bash
# Run tests with coverage for ragged
# Usage: ./scripts/dev/test.sh [options]
# Options:
#   unit         - Run unit tests only (default)
#   integration  - Run integration tests
#   all          - Run all tests
#   coverage     - Run with coverage report (HTML)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Default to unit tests
TEST_TYPE="${1:-unit}"

# Base pytest command
PYTEST_CMD="pytest -v --tb=short"

# Set up environment
export RAGGED_ENVIRONMENT=testing
export RAGGED_CHROMA_URL=http://localhost:8001

case "$TEST_TYPE" in
    unit)
        log_info "Running unit tests..."
        $PYTEST_CMD tests/unit/
        ;;

    integration)
        log_info "Running integration tests..."
        log_warn "This requires ChromaDB to be running on port 8001"
        $PYTEST_CMD tests/integration/ -m "not requires_ollama"
        ;;

    all)
        log_info "Running all tests..."
        log_warn "This requires ChromaDB to be running on port 8001"
        $PYTEST_CMD tests/ -m "not requires_ollama"
        ;;

    coverage)
        log_info "Running tests with coverage..."
        pytest \
            --cov=src \
            --cov-report=html \
            --cov-report=term \
            --cov-report=xml \
            -v \
            -m "not requires_ollama"

        log_success "Coverage report generated in htmlcov/"

        # Open coverage report (macOS)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open htmlcov/index.html
        fi

        # Show coverage summary
        echo
        log_info "Coverage summary:"
        coverage report --skip-empty
        echo

        # Check against threshold
        COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
        THRESHOLD=68

        if (( $(echo "$COVERAGE >= $THRESHOLD" | bc -l) )); then
            log_success "Coverage ($COVERAGE%) meets minimum threshold ($THRESHOLD%)"
        else
            log_warn "Coverage ($COVERAGE%) is below threshold ($THRESHOLD%)"
        fi
        ;;

    *)
        echo "Usage: $0 [unit|integration|all|coverage]"
        echo
        echo "Options:"
        echo "  unit         - Run unit tests only (fast)"
        echo "  integration  - Run integration tests (requires services)"
        echo "  all          - Run all tests"
        echo "  coverage     - Run with coverage report"
        exit 1
        ;;
esac

log_success "Tests completed!"
