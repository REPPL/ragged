#!/usr/bin/env bash
#
# ragged Installation Verification Script
#
# This script verifies that ragged is installed and configured correctly.
# It checks Docker containers, service connectivity, and configuration.
#
# Usage: ./scripts/verify-install.sh
#

set -e  # Exit on error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_test() {
    echo -e "\n${BLUE}Testing:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}  ✓ PASS${NC} $1"
    PASSED=$((PASSED + 1))
}

print_fail() {
    echo -e "${RED}  ✗ FAIL${NC} $1"
    FAILED=$((FAILED + 1))
}

print_warn() {
    echo -e "${YELLOW}  ⚠ WARN${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

print_info() {
    echo -e "${BLUE}  ℹ INFO${NC} $1"
}

# Main verification
main() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}ragged Installation Verification${NC}"
    echo -e "${BLUE}======================================${NC}"

    # Test 1: Docker containers
    print_test "Docker Containers"

    if docker ps --format '{{.Names}}' | grep -q "ragged-chromadb"; then
        CHROMADB_STATUS=$(docker inspect --format='{{.State.Status}}' ragged-chromadb)
        CHROMADB_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ragged-chromadb 2>/dev/null || echo "none")

        if [ "$CHROMADB_STATUS" = "running" ]; then
            if [ "$CHROMADB_HEALTH" = "healthy" ]; then
                print_pass "ChromaDB container is running and healthy"
            else
                print_warn "ChromaDB container running but health status: $CHROMADB_HEALTH"
            fi
        else
            print_fail "ChromaDB container status: $CHROMADB_STATUS"
        fi
    else
        print_fail "ChromaDB container not found"
    fi

    if docker ps --format '{{.Names}}' | grep -q "ragged-api"; then
        API_STATUS=$(docker inspect --format='{{.State.Status}}' ragged-api)
        API_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ragged-api 2>/dev/null || echo "none")

        if [ "$API_STATUS" = "running" ]; then
            if [ "$API_HEALTH" = "healthy" ]; then
                print_pass "ragged-api container is running and healthy"
            else
                print_warn "ragged-api container running but health status: $API_HEALTH"
                print_info "Check logs: docker compose logs ragged-api"
            fi
        else
            print_fail "ragged-api container status: $API_STATUS"
            print_info "Check logs: docker compose logs ragged-api"
        fi
    else
        print_fail "ragged-api container not found"
    fi

    if docker ps --format '{{.Names}}' | grep -q "ragged-ui"; then
        UI_STATUS=$(docker inspect --format='{{.State.Status}}' ragged-ui)
        UI_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ragged-ui 2>/dev/null || echo "none")

        if [ "$UI_STATUS" = "running" ]; then
            if [ "$UI_HEALTH" = "healthy" ]; then
                print_pass "ragged-ui container is running and healthy"
            else
                print_warn "ragged-ui container running but health status: $UI_HEALTH"
            fi
        else
            print_fail "ragged-ui container status: $UI_STATUS"
        fi
    else
        print_fail "ragged-ui container not found"
    fi

    # Test 2: Service connectivity
    print_test "Service Connectivity"

    if curl -s http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; then
        print_pass "ChromaDB accessible at http://localhost:8001"
    else
        print_fail "Cannot reach ChromaDB at http://localhost:8001"
        print_info "Check: docker compose logs chromadb"
    fi

    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        print_pass "ragged API accessible at http://localhost:8000"
    else
        print_fail "Cannot reach ragged API at http://localhost:8000"
        print_info "Check: docker compose logs ragged-api"
    fi

    if curl -s http://localhost:7860 >/dev/null 2>&1; then
        print_pass "ragged UI accessible at http://localhost:7860"
    else
        print_fail "Cannot reach ragged UI at http://localhost:7860"
        print_info "Check: docker compose logs ragged-ui"
    fi

    # Test 3: Ollama (optional)
    print_test "Ollama (Optional)"

    if command -v ollama >/dev/null 2>&1; then
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_pass "Ollama is running at http://localhost:11434"

            if ollama list | grep -q "llama3.2"; then
                print_pass "llama3.2 model is available"
            else
                print_warn "llama3.2 model not found"
                print_info "Pull with: ollama pull llama3.2"
            fi
        else
            print_warn "Ollama installed but not running"
            print_info "Start with: ollama serve"
        fi
    else
        print_warn "Ollama not installed (optional)"
        print_info "Install from: https://ollama.ai"
    fi

    # Test 4: Configuration
    print_test "Configuration"

    if [ -f .env ]; then
        print_pass ".env file exists"

        # Check critical variables
        if grep -q "OLLAMA_URL" .env; then
            print_pass "OLLAMA_URL configured"
        else
            print_warn "OLLAMA_URL not found in .env"
        fi

        if grep -q "CHROMA_URL" .env; then
            print_pass "CHROMA_URL configured"
        else
            print_warn "CHROMA_URL not found in .env"
        fi
    else
        print_fail ".env file not found"
        print_info "Create from example: cp .env.example .env"
    fi

    # Test 5: Package imports (inside container)
    print_test "Package Imports"

    if docker compose exec -T ragged-api python -c "import ragged" 2>/dev/null; then
        print_pass "ragged package imports successfully"
    else
        print_fail "ragged package import failed"
        print_info "Rebuild containers: docker compose build --no-cache"
    fi

    if docker compose exec -T ragged-api python -c "from ragged.web.api import app" 2>/dev/null; then
        print_pass "ragged.web.api imports successfully"
    else
        print_fail "ragged.web.api import failed"
        print_info "Check: docker compose logs ragged-api"
    fi

    # Summary
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}Verification Summary${NC}"
    echo -e "${BLUE}======================================${NC}\n"

    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All critical tests passed!${NC}"
        echo
        echo "ragged is ready to use:"
        echo "  • API:        http://localhost:8000"
        echo "  • API Docs:   http://localhost:8000/docs"
        echo "  • Web UI:     http://localhost:7860"
        echo
        return 0
    else
        echo -e "${RED}✗ Some tests failed. See above for details.${NC}"
        echo
        echo "Troubleshooting:"
        echo "  • View logs:      docker compose logs"
        echo "  • Rebuild:        docker compose down && docker compose build --no-cache && docker compose up -d"
        echo "  • Full guide:     docs/guides/troubleshooting.md"
        echo
        return 1
    fi
}

# Run main function
main "$@"
