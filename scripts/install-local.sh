#!/usr/bin/env bash
#
# ragged Local Installation Script (Linux/macOS)
# https://github.com/REPPL/ragged
#
# This script installs ragged locally for CLI usage without Docker.
#
# Usage:
#   curl -sSf https://raw.githubusercontent.com/REPPL/ragged/main/scripts/install-local.sh | bash
#   # OR from cloned repo:
#   ./scripts/install-local.sh
#
# Requirements:
#   - Python 3.12
#   - bash 4.0+
#   - curl or wget

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# Configuration
PYTHON_VERSION="3.12"
REQUIRED_PYTHON="python3.12"
PROJECT_NAME="ragged"
REPO_URL="https://github.com/REPPL/ragged.git"
INSTALL_DIR="${HOME}/.ragged"

# Helper functions
info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

success() {
    echo -e "${GREEN}✓${NC} $*"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

error() {
    echo -e "${RED}✗${NC} $*" >&2
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print banner
print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ragged - Local Installation              ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  Privacy-first Multi-modal RAG System     ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check Python version
check_python() {
    info "Checking Python ${PYTHON_VERSION}..."

    if command_exists ${REQUIRED_PYTHON}; then
        PYTHON_CMD=${REQUIRED_PYTHON}
        success "Found $(${PYTHON_CMD} --version)"
    elif command_exists python3; then
        local version=$(python3 --version 2>&1 | awk '{print $2}')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)

        if [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; then
            PYTHON_CMD=python3
            success "Found Python $version (compatible)"
        else
            error "Python ${PYTHON_VERSION} required, found Python $version"
            error "Install Python ${PYTHON_VERSION}: https://www.python.org/downloads/"
            exit 1
        fi
    else
        error "Python ${PYTHON_VERSION} not found"
        error "Install from: https://www.python.org/downloads/"
        exit 1
    fi
}

# Determine installation location
determine_install_location() {
    if [ -f "pyproject.toml" ] && [ -d "src" ]; then
        # Running from within cloned repo
        INSTALL_DIR="$(pwd)"
        info "Installing from current directory: ${INSTALL_DIR}"
        FROM_REPO=true
    else
        # Installing to ~/.ragged
        info "Installing to: ${INSTALL_DIR}"
        FROM_REPO=false
    fi
}

# Clone repository if needed
clone_repository() {
    if [ "$FROM_REPO" = false ]; then
        if [ -d "${INSTALL_DIR}" ]; then
            warning "Directory ${INSTALL_DIR} already exists"
            read -p "Remove and reinstall? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "${INSTALL_DIR}"
            else
                error "Installation cancelled"
                exit 1
            fi
        fi

        info "Cloning repository..."
        if command_exists git; then
            git clone "${REPO_URL}" "${INSTALL_DIR}"
            success "Repository cloned"
        else
            error "git not found. Install git or clone manually:"
            error "  ${REPO_URL}"
            exit 1
        fi
    fi
}

# Create virtual environment
create_venv() {
    info "Creating virtual environment..."

    cd "${INSTALL_DIR}"

    if [ -d ".venv" ]; then
        warning "Virtual environment already exists"
        read -p "Recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .venv
        else
            info "Using existing virtual environment"
            return 0
        fi
    fi

    ${PYTHON_CMD} -m venv .venv
    success "Virtual environment created"
}

# Install ragged
install_ragged() {
    info "Installing ragged and dependencies..."

    cd "${INSTALL_DIR}"

    # Upgrade pip
    .venv/bin/pip install --quiet --upgrade pip setuptools wheel

    # Install ragged in editable mode
    .venv/bin/pip install --quiet -e ".[dev]"

    success "ragged installed"
}

# Verify installation
verify_installation() {
    info "Verifying installation..."

    cd "${INSTALL_DIR}"

    local version=$(.venv/bin/ragged --version 2>&1 || echo "error")

    if [[ "$version" == "error" ]]; then
        error "Installation verification failed"
        error "ragged command not working"
        exit 1
    fi

    success "Installation verified: ${version}"
}

# Setup direnv (optional)
setup_direnv() {
    info "Checking for direnv..."

    if command_exists direnv; then
        success "direnv found"

        cd "${INSTALL_DIR}"

        if [ ! -f ".envrc" ]; then
            warning ".envrc not found (should exist in repo)"
            return 0
        fi

        info "Allowing direnv for this directory..."
        direnv allow .
        success "direnv configured"

        info ""
        info "direnv will automatically activate the virtual environment"
        info "when you cd into ${INSTALL_DIR}"
    else
        warning "direnv not found (optional)"
        info "Install direnv for automatic venv activation:"
        info "  macOS:  brew install direnv"
        info "  Linux:  apt install direnv  (or equivalent)"
        info "  Then add to ~/.bashrc or ~/.zshrc:"
        info "    eval \"\$(direnv hook bash)\"  # or zsh"
    fi
}

# Add to PATH
setup_path() {
    info "Setting up PATH..."

    local bin_dir="${INSTALL_DIR}/.venv/bin"
    local shell_rc=""

    # Determine shell config file
    if [ -n "${BASH_VERSION:-}" ]; then
        shell_rc="${HOME}/.bashrc"
    elif [ -n "${ZSH_VERSION:-}" ]; then
        shell_rc="${HOME}/.zshrc"
    else
        warning "Unknown shell, skipping PATH setup"
        return 0
    fi

    # Check if already in PATH
    if echo "${PATH}" | grep -q "${bin_dir}"; then
        success "PATH already configured"
        return 0
    fi

    info "Add ${bin_dir} to PATH? This will modify ${shell_rc}"
    read -p "Continue? (Y/n): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "" >> "${shell_rc}"
        echo "# ragged CLI" >> "${shell_rc}"
        echo "export PATH=\"${bin_dir}:\$PATH\"" >> "${shell_rc}"
        success "PATH configured in ${shell_rc}"
        info "Reload shell or run: source ${shell_rc}"
    else
        info "Skipped PATH setup"
        info "To use ragged, activate venv manually:"
        info "  source ${INSTALL_DIR}/.venv/bin/activate"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  Installation Complete!                    ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    success "ragged is installed at: ${INSTALL_DIR}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo ""
    echo "1. Activate the virtual environment:"
    echo -e "   ${YELLOW}source ${INSTALL_DIR}/.venv/bin/activate${NC}"
    echo ""
    echo "2. Verify installation:"
    echo -e "   ${YELLOW}ragged --version${NC}"
    echo ""
    echo "3. Check system health:"
    echo -e "   ${YELLOW}ragged health${NC}"
    echo ""
    echo "4. Ingest your first document:"
    echo -e "   ${YELLOW}ragged ingest pdf /path/to/document.pdf${NC}"
    echo ""
    echo "5. Query your documents:"
    echo -e "   ${YELLOW}ragged query text \"your question\"${NC}"
    echo ""
    info "For Docker-based installation (API + UI), run:"
    echo -e "   ${YELLOW}cd ${INSTALL_DIR} && ./scripts/setup.sh${NC}"
    echo ""
    info "Documentation: ${INSTALL_DIR}/docs/tutorials/installation.md"
    echo ""
}

# Main installation flow
main() {
    print_banner

    check_python
    determine_install_location
    clone_repository
    create_venv
    install_ragged
    verify_installation
    setup_direnv
    setup_path
    print_next_steps
}

# Run main function
main "$@"
