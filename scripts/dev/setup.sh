#!/usr/bin/env bash
# Development environment setup script for ragged
# Run this script to set up your local development environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 is installed"
        return 0
    else
        log_error "$1 is not installed"
        return 1
    fi
}

# Main setup
main() {
    log_info "Setting up ragged development environment..."
    echo

    # Check Python version
    log_info "Checking Python version..."
    if python3 --version | grep -q "3.12"; then
        log_success "Python 3.12 found: $(python3 --version)"
    else
        log_error "Python 3.12 is required (found: $(python3 --version))"
        exit 1
    fi
    echo

    # Check for required commands
    log_info "Checking required commands..."
    MISSING_COMMANDS=0

    if ! check_command "git"; then
        MISSING_COMMANDS=$((MISSING_COMMANDS + 1))
    fi

    if ! check_command "docker"; then
        log_warn "Docker not found - you'll need it to run ChromaDB"
    fi

    if ! check_command "ollama"; then
        log_warn "Ollama not found - you'll need it for LLM generation"
    fi
    echo

    if [ $MISSING_COMMANDS -gt 0 ]; then
        log_error "Missing required commands. Please install them first."
        exit 1
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3.12 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    echo

    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    echo

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    log_success "pip upgraded"
    echo

    # Install dependencies
    log_info "Installing development dependencies..."
    pip install -r requirements-dev.txt --quiet
    log_success "Development dependencies installed"
    echo

    # Install package in editable mode
    log_info "Installing ragged in editable mode..."
    pip install -e . --quiet
    log_success "ragged installed in editable mode"
    echo

    # Set up environment file
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        log_success ".env file created"
        log_warn "Please review and configure .env for your local setup"
    else
        log_info ".env file already exists"
    fi
    echo

    # Set up pre-commit hooks
    log_info "Installing pre-commit hooks..."
    if pip install pre-commit --quiet; then
        pre-commit install
        log_success "Pre-commit hooks installed"
    else
        log_error "Failed to install pre-commit hooks"
    fi
    echo

    # Create data directory
    log_info "Creating ragged data directory..."
    mkdir -p ~/.ragged
    log_success "Data directory created at ~/.ragged"
    echo

    # Start ChromaDB (optional)
    read -p "Do you want to start ChromaDB in Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Starting ChromaDB..."
        docker-compose up -d chromadb
        log_success "ChromaDB started on port 8001"
    fi
    echo

    # Check Ollama
    if check_command "ollama" &> /dev/null; then
        log_info "Checking Ollama status..."
        if ollama list &> /dev/null; then
            log_success "Ollama is running"
            echo "Available models:"
            ollama list
        else
            log_warn "Ollama is installed but not running"
            log_info "Start it with: ollama serve"
        fi
    fi
    echo

    # Run tests to verify setup
    read -p "Do you want to run tests to verify the setup? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Running unit tests..."
        pytest tests/unit/ -v --tb=short
        log_success "Tests completed"
    fi
    echo

    # Summary
    log_success "Development environment setup complete!"
    echo
    echo "Next steps:"
    echo "  1. Activate the virtual environment: source venv/bin/activate"
    echo "  2. Configure .env with your local settings"
    echo "  3. Ensure Ollama is running: ollama serve"
    echo "  4. Pull an LLM model: ollama pull llama3.2"
    echo "  5. Run tests: pytest"
    echo "  6. Start developing: ragged --help"
    echo
    log_info "Happy coding!"
}

# Run main function
main
