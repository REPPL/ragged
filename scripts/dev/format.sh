#!/usr/bin/env bash
# Auto-format code for ragged
# This script runs all formatters to fix code style

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "========================================="
echo "  ragged Auto-Formatter"
echo "========================================="
echo

# 1. Black formatting
log_info "Formatting with Black..."
black src/ tests/ --line-length 100
log_success "Black formatting complete"
echo

# 2. Ruff auto-fixes
log_info "Auto-fixing with Ruff..."
ruff check --fix src/ tests/
log_success "Ruff fixes applied"
echo

# 3. Import sorting (via Ruff)
log_info "Sorting imports..."
ruff check --select I --fix src/ tests/
log_success "Imports sorted"
echo

log_success "All formatting complete!"
echo
log_info "You may want to run ./scripts/dev/lint.sh to check for remaining issues"
