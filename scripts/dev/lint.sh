#!/usr/bin/env bash
# Run all linters and code quality checks for ragged
# Usage: ./scripts/dev/lint.sh [--fix]

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if --fix flag is passed
FIX_MODE=false
if [[ "${1:-}" == "--fix" ]]; then
    FIX_MODE=true
    log_info "Running in fix mode - will automatically fix issues where possible"
fi

FAILED_CHECKS=0

echo "========================================="
echo "  ragged Code Quality Checks"
echo "========================================="
echo

# 1. Black - Code formatting
log_info "1. Checking code formatting with Black..."
if [ "$FIX_MODE" = true ]; then
    if black src/ tests/ --line-length 100; then
        log_success "Black: Code formatted"
    else
        log_error "Black: Formatting failed"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
else
    if black --check --line-length 100 src/ tests/; then
        log_success "Black: Code is properly formatted"
    else
        log_error "Black: Code formatting issues found"
        log_info "Run with --fix to automatically format"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi
echo

# 2. Ruff - Linting
log_info "2. Linting with Ruff..."
if [ "$FIX_MODE" = true ]; then
    if ruff check --fix src/ tests/; then
        log_success "Ruff: Issues fixed"
    else
        log_error "Ruff: Some issues could not be auto-fixed"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
else
    if ruff check src/ tests/; then
        log_success "Ruff: No linting issues"
    else
        log_error "Ruff: Linting issues found"
        log_info "Run with --fix to automatically fix some issues"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi
echo

# 3. MyPy - Type checking
log_info "3. Type checking with MyPy..."
if mypy src/; then
    log_success "MyPy: No type errors"
else
    log_warn "MyPy: Type errors found (not blocking)"
    # Don't increment FAILED_CHECKS for MyPy warnings
fi
echo

# 4. Bandit - Security checks
log_info "4. Security scanning with Bandit..."
if bandit -r src/ -ll --quiet; then
    log_success "Bandit: No security issues"
else
    log_warn "Bandit: Potential security issues found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo

# 5. Check for common issues
log_info "5. Checking for common issues..."

# Check for debugger statements
if grep -r "import pdb\|breakpoint()" src/ tests/ 2>/dev/null; then
    log_error "Found debugger statements - please remove them"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    log_success "No debugger statements found"
fi

# Check for TODO comments without issue references
TODO_COUNT=$(grep -r "TODO\|FIXME" src/ tests/ 2>/dev/null | grep -v "#.*TODO.*#[0-9]" | wc -l || true)
if [ "$TODO_COUNT" -gt 0 ]; then
    log_warn "Found $TODO_COUNT TODO/FIXME comments without issue references"
    log_info "Please link TODOs to GitHub issues: # TODO: Fix this #123"
fi

# Check for print statements (should use logging)
PRINT_COUNT=$(grep -r "print(" src/ 2>/dev/null | grep -v "test_\|__pycache__" | wc -l || true)
if [ "$PRINT_COUNT" -gt 0 ]; then
    log_warn "Found $PRINT_COUNT print() statements in src/"
    log_info "Consider using logging instead"
fi

echo

# Summary
echo "========================================="
if [ $FAILED_CHECKS -eq 0 ]; then
    log_success "All quality checks passed!"
    echo "========================================="
    exit 0
else
    log_error "$FAILED_CHECKS check(s) failed"
    echo "========================================="
    if [ "$FIX_MODE" = false ]; then
        log_info "Run with --fix to automatically fix some issues"
    fi
    exit 1
fi
