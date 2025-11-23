#!/usr/bin/env bash
#
# ragged Automated Setup Script
#
# This script automates the Docker-based installation of ragged.
# It checks prerequisites, sets up configuration, and starts all services.
#
# Usage: ./scripts/setup.sh
#

set -e  # Exit on error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup
main() {
    print_header "ragged Docker Setup"

    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"

    if command_exists docker; then
        print_success "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed"
        print_info "Install from: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi

    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose is available"
        if command_exists docker-compose; then
            docker-compose --version
        else
            docker compose version
        fi
    else
        print_error "Docker Compose is not available"
        print_info "Install Docker Desktop which includes Docker Compose"
        exit 1
    fi

    # Check if Docker daemon is running
    if docker ps >/dev/null 2>&1; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        print_info "Start Docker Desktop and wait for it to be ready"
        exit 1
    fi

    if command_exists ollama; then
        print_success "Ollama is installed"
        ollama --version
    else
        print_warning "Ollama is not installed (optional but recommended)"
        print_info "Install from: https://ollama.ai"
    fi

    # Step 2: Setup environment file
    print_header "Step 2: Environment Configuration"

    if [ -f .env ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
        else
            print_info "Keeping existing .env file"
        fi
    else
        cp .env.example .env
        print_success "Created .env from .env.example"
    fi

    print_info "Review .env file to customise ports and settings"

    # Step 3: Check for Ollama and start if needed
    print_header "Step 3: Ollama Service"

    if command_exists ollama; then
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_success "Ollama is running"
        else
            print_warning "Ollama is not running"
            print_info "Start Ollama in a separate terminal with: ollama serve"
            read -p "Press Enter when Ollama is running (or Ctrl+C to continue without Ollama)..."
        fi

        # Check for required models
        print_info "Checking for required Ollama models..."
        if ollama list | grep -q "llama3.2"; then
            print_success "llama3.2 model found"
        else
            print_warning "llama3.2 model not found"
            print_info "Pull with: ollama pull llama3.2"
        fi
    fi

    # Step 4: Build Docker images
    print_header "Step 4: Building Docker Images"

    print_info "This may take several minutes on first run..."
    if docker compose build; then
        print_success "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        exit 1
    fi

    # Step 5: Start containers
    print_header "Step 5: Starting Containers"

    if docker compose up -d; then
        print_success "Containers started"
    else
        print_error "Failed to start containers"
        print_info "Check logs with: docker compose logs"
        exit 1
    fi

    # Step 6: Wait for health checks
    print_header "Step 6: Waiting for Services"

    print_info "Waiting for containers to be healthy (up to 60 seconds)..."

    TIMEOUT=60
    ELAPSED=0
    INTERVAL=2

    while [ $ELAPSED -lt $TIMEOUT ]; do
        CHROMADB_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ragged-chromadb 2>/dev/null || echo "unknown")
        API_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ragged-api 2>/dev/null || echo "unknown")

        if [ "$CHROMADB_HEALTH" = "healthy" ] && [ "$API_HEALTH" = "healthy" ]; then
            print_success "All services are healthy!"
            break
        fi

        echo -n "."
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done
    echo

    if [ $ELAPSED -ge $TIMEOUT ]; then
        print_warning "Health check timeout - some services may still be starting"
        print_info "Check status with: docker compose ps"
        print_info "View logs with: docker compose logs"
    fi

    # Step 7: Verify installation
    print_header "Step 7: Verification"

    ./scripts/verify-install.sh

    # Step 8: Summary
    print_header "Setup Complete!"

    echo -e "${GREEN}ragged is now running!${NC}\n"
    echo "Services available at:"
    echo "  • API:        http://localhost:8000"
    echo "  • API Docs:   http://localhost:8000/docs"
    echo "  • Web UI:     http://localhost:7860"
    echo "  • ChromaDB:   http://localhost:8001"
    echo ""
    echo "Useful commands:"
    echo "  • View logs:         docker compose logs -f"
    echo "  • Check status:      docker compose ps"
    echo "  • Stop services:     docker compose down"
    echo "  • Restart services:  docker compose restart"
    echo ""
    echo "Troubleshooting:"
    echo "  • Full guide:        docs/guides/troubleshooting.md"
    echo "  • Rebuild:           docker compose down && docker compose build --no-cache && docker compose up -d"
    echo ""
}

# Run main function
main "$@"
