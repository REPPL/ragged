"""
Bootstrap Script Generator.

WIZARD-002: Generates one-command installation scripts for various platforms.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class ScriptFormat(Enum):
    """Output script format."""

    BASH = "bash"
    POWERSHELL = "powershell"
    PYTHON = "python"


@dataclass
class BootstrapOptions:
    """Options for bootstrap script generation."""

    # Installation options
    ragged_home: str = "~/.ragged"
    install_docker: bool = True
    install_ollama: bool = True
    llm_model: str = "llama3.2"
    pull_model: bool = True

    # Server options
    api_port: int = 8000
    webui_port: int = 5173

    # Feature flags
    use_docker_chromadb: bool = True
    enable_auth: bool = False
    start_services: bool = True

    # Script options
    interactive: bool = False
    verbose: bool = False
    dry_run: bool = False


BASH_BOOTSTRAP_TEMPLATE = '''#!/usr/bin/env bash
# ragged Bootstrap Installer
# Generated automatically - do not edit
#
# Usage:
#   curl -fsSL https://ragged.dev/install.sh | bash
#   wget -qO- https://ragged.dev/install.sh | bash

set -e

# Configuration
RAGGED_HOME="${{RAGGED_HOME:-{ragged_home}}}"
RAGGED_VERSION="${{RAGGED_VERSION:-latest}}"
API_PORT="{api_port}"
WEBUI_PORT="{webui_port}"
LLM_MODEL="{llm_model}"
VERBOSE="{verbose}"
DRY_RUN="{dry_run}"

# Colours
RED="\\033[0;31m"
GREEN="\\033[0;32m"
YELLOW="\\033[0;33m"
BLUE="\\033[0;34m"
NC="\\033[0m" # No colour

# Logging
log_info() {{
    echo -e "${{BLUE}}[INFO]${{NC}} $1"
}}

log_success() {{
    echo -e "${{GREEN}}[SUCCESS]${{NC}} $1"
}}

log_warn() {{
    echo -e "${{YELLOW}}[WARN]${{NC}} $1"
}}

log_error() {{
    echo -e "${{RED}}[ERROR]${{NC}} $1"
}}

# Check if command exists
command_exists() {{
    command -v "$1" >/dev/null 2>&1
}}

# Detect OS
detect_os() {{
    case "$(uname -s)" in
        Linux*)     OS="linux";;
        Darwin*)    OS="macos";;
        CYGWIN*|MINGW*|MSYS*) OS="windows";;
        *)          OS="unknown";;
    esac
    echo "$OS"
}}

# Detect package manager
detect_package_manager() {{
    if command_exists apt-get; then
        echo "apt"
    elif command_exists dnf; then
        echo "dnf"
    elif command_exists yum; then
        echo "yum"
    elif command_exists brew; then
        echo "brew"
    elif command_exists pacman; then
        echo "pacman"
    else
        echo "unknown"
    fi
}}

# Install Docker
install_docker() {{
    log_info "Installing Docker..."

    local os=$(detect_os)
    local pm=$(detect_package_manager)

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would install Docker"
        return 0
    fi

    case "$os" in
        macos)
            if command_exists brew; then
                brew install --cask docker
            else
                log_error "Homebrew required to install Docker on macOS"
                log_info "Install from: https://docker.com/products/docker-desktop"
                return 1
            fi
            ;;
        linux)
            case "$pm" in
                apt)
                    sudo apt-get update
                    sudo apt-get install -y docker.io docker-compose-plugin
                    sudo systemctl enable docker
                    sudo systemctl start docker
                    sudo usermod -aG docker "$USER"
                    ;;
                dnf|yum)
                    sudo $pm install -y docker docker-compose-plugin
                    sudo systemctl enable docker
                    sudo systemctl start docker
                    sudo usermod -aG docker "$USER"
                    ;;
                pacman)
                    sudo pacman -S --noconfirm docker docker-compose
                    sudo systemctl enable docker
                    sudo systemctl start docker
                    sudo usermod -aG docker "$USER"
                    ;;
                *)
                    log_error "Unknown package manager: $pm"
                    return 1
                    ;;
            esac
            ;;
        *)
            log_error "Unsupported OS for Docker installation: $os"
            return 1
            ;;
    esac

    log_success "Docker installed"
}}

# Install Ollama
install_ollama() {{
    log_info "Installing Ollama..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would install Ollama"
        return 0
    fi

    curl -fsSL https://ollama.ai/install.sh | sh

    log_success "Ollama installed"
}}

# Install Python package
install_ragged() {{
    log_info "Installing ragged..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would install ragged"
        return 0
    fi

    if [ "$RAGGED_VERSION" = "latest" ]; then
        pip install --user ragged
    else
        pip install --user "ragged==$RAGGED_VERSION"
    fi

    log_success "ragged installed"
}}

# Pull LLM model
pull_model() {{
    log_info "Pulling LLM model: $LLM_MODEL..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would pull model: $LLM_MODEL"
        return 0
    fi

    ollama pull "$LLM_MODEL"

    log_success "Model $LLM_MODEL ready"
}}

# Create directory structure
create_directories() {{
    log_info "Creating ragged home directory..."

    local home_expanded="${{RAGGED_HOME/#\\~/$HOME}}"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would create: $home_expanded"
        return 0
    fi

    mkdir -p "$home_expanded/documents"
    mkdir -p "$home_expanded/logs"
    mkdir -p "$home_expanded/config"
    mkdir -p "$home_expanded/data/chromadb"
    mkdir -p "$home_expanded/data/kuzu"

    log_success "Directories created at $home_expanded"
}}

# Generate configuration
generate_config() {{
    log_info "Generating configuration..."

    local home_expanded="${{RAGGED_HOME/#\\~/$HOME}}"
    local config_file="$home_expanded/config/ragged.yml"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would generate config at: $config_file"
        return 0
    fi

    cat > "$config_file" << EOF
# ragged Configuration
# Generated by bootstrap installer

server:
  host: "127.0.0.1"
  port: $API_PORT
  debug: false

webui:
  port: $WEBUI_PORT

llm:
  provider: "ollama"
  model: "$LLM_MODEL"
  base_url: "http://localhost:11434"

storage:
  documents_path: "$home_expanded/documents"
  chromadb_path: "$home_expanded/data/chromadb"

logging:
  level: "INFO"
  path: "$home_expanded/logs"
EOF

    log_success "Configuration generated"
}}

# Start services
start_services() {{
    log_info "Starting services..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would start services"
        return 0
    fi

    # Start Docker if not running
    if command_exists docker; then
        if ! docker info >/dev/null 2>&1; then
            case "$(detect_os)" in
                macos)
                    open -a Docker
                    sleep 10  # Wait for Docker to start
                    ;;
                linux)
                    sudo systemctl start docker
                    ;;
            esac
        fi
    fi

    # Start Ollama if not running
    if command_exists ollama; then
        if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            ollama serve &
            sleep 3  # Wait for Ollama to start
        fi
    fi

    log_success "Services started"
}}

# Print success message
print_success() {{
    echo ""
    echo -e "${{GREEN}}=============================================${{NC}}"
    echo -e "${{GREEN}}  ragged installation complete!${{NC}}"
    echo -e "${{GREEN}}=============================================${{NC}}"
    echo ""
    echo "Quick start:"
    echo "  ragged start          # Start all services"
    echo "  ragged add <path>     # Add documents"
    echo "  ragged ask <question> # Ask questions"
    echo ""
    echo "Web interface: http://localhost:$WEBUI_PORT"
    echo "API endpoint:  http://localhost:$API_PORT"
    echo ""
    echo "For help: ragged --help"
    echo ""
}}

# Main installation flow
main() {{
    echo ""
    echo -e "${{BLUE}}======================================${{NC}}"
    echo -e "${{BLUE}}  ragged Bootstrap Installer${{NC}}"
    echo -e "${{BLUE}}======================================${{NC}}"
    echo ""

    local os=$(detect_os)
    log_info "Detected OS: $os"

    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        log_info "Install Python 3.10+ and try again"
        exit 1
    fi

    local python_version=$(python3 -c 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")')
    log_info "Python version: $python_version"

    # Install Docker if needed
    {install_docker_block}

    # Install Ollama if needed
    {install_ollama_block}

    # Create directories
    create_directories

    # Install ragged
    install_ragged

    # Generate configuration
    generate_config

    # Pull model
    {pull_model_block}

    # Start services
    {start_services_block}

    print_success
}}

main "$@"
'''


POWERSHELL_BOOTSTRAP_TEMPLATE = '''# ragged Bootstrap Installer for Windows
# Generated automatically - do not edit
#
# Usage:
#   iwr https://ragged.dev/install.ps1 | iex

$ErrorActionPreference = "Stop"

# Configuration
$RaggedHome = if ($env:RAGGED_HOME) {{ $env:RAGGED_HOME }} else {{ "$env:USERPROFILE\\.ragged" }}
$RaggedVersion = if ($env:RAGGED_VERSION) {{ $env:RAGGED_VERSION }} else {{ "latest" }}
$ApiPort = "{api_port}"
$WebuiPort = "{webui_port}"
$LlmModel = "{llm_model}"
$DryRun = ${dry_run_ps}

function Write-Info {{ param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }}
function Write-Success {{ param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }}
function Write-Warn {{ param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }}
function Write-Err {{ param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }}

function Test-Command {{ param($Name) return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }}

function Install-DockerDesktop {{
    Write-Info "Installing Docker Desktop..."

    if ($DryRun) {{
        Write-Info "[DRY RUN] Would install Docker Desktop"
        return
    }}

    if (Test-Command winget) {{
        winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    }} else {{
        Write-Err "winget not found. Please install Docker Desktop manually from:"
        Write-Info "https://docker.com/products/docker-desktop"
        throw "Docker installation failed"
    }}

    Write-Success "Docker Desktop installed (restart may be required)"
}}

function Install-Ollama {{
    Write-Info "Installing Ollama..."

    if ($DryRun) {{
        Write-Info "[DRY RUN] Would install Ollama"
        return
    }}

    if (Test-Command winget) {{
        winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    }} else {{
        $installerUrl = "https://ollama.ai/download/OllamaSetup.exe"
        $installerPath = "$env:TEMP\\OllamaSetup.exe"
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
        Start-Process -FilePath $installerPath -Wait
        Remove-Item $installerPath
    }}

    Write-Success "Ollama installed"
}}

function Install-Ragged {{
    Write-Info "Installing ragged..."

    if ($DryRun) {{
        Write-Info "[DRY RUN] Would install ragged"
        return
    }}

    if ($RaggedVersion -eq "latest") {{
        pip install --user ragged
    }} else {{
        pip install --user "ragged==$RaggedVersion"
    }}

    Write-Success "ragged installed"
}}

function New-RaggedDirectories {{
    Write-Info "Creating ragged home directory..."

    if ($DryRun) {{
        Write-Info "[DRY RUN] Would create: $RaggedHome"
        return
    }}

    $dirs = @(
        "$RaggedHome\\documents",
        "$RaggedHome\\logs",
        "$RaggedHome\\config",
        "$RaggedHome\\data\\chromadb",
        "$RaggedHome\\data\\kuzu"
    )

    foreach ($dir in $dirs) {{
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }}

    Write-Success "Directories created at $RaggedHome"
}}

function New-RaggedConfig {{
    Write-Info "Generating configuration..."

    $configFile = "$RaggedHome\\config\\ragged.yml"

    if ($DryRun) {{
        Write-Info "[DRY RUN] Would generate config at: $configFile"
        return
    }}

    $config = @"
# ragged Configuration
# Generated by bootstrap installer

server:
  host: "127.0.0.1"
  port: $ApiPort
  debug: false

webui:
  port: $WebuiPort

llm:
  provider: "ollama"
  model: "$LlmModel"
  base_url: "http://localhost:11434"

storage:
  documents_path: "$RaggedHome\\documents"
  chromadb_path: "$RaggedHome\\data\\chromadb"

logging:
  level: "INFO"
  path: "$RaggedHome\\logs"
"@

    Set-Content -Path $configFile -Value $config

    Write-Success "Configuration generated"
}}

function Get-OllamaModel {{
    Write-Info "Pulling LLM model: $LlmModel..."

    if ($DryRun) {{
        Write-Info "[DRY RUN] Would pull model: $LlmModel"
        return
    }}

    ollama pull $LlmModel

    Write-Success "Model $LlmModel ready"
}}

function Show-Success {{
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  ragged installation complete!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick start:"
    Write-Host "  ragged start          # Start all services"
    Write-Host "  ragged add <path>     # Add documents"
    Write-Host "  ragged ask <question> # Ask questions"
    Write-Host ""
    Write-Host "Web interface: http://localhost:$WebuiPort"
    Write-Host "API endpoint:  http://localhost:$ApiPort"
    Write-Host ""
    Write-Host "For help: ragged --help"
    Write-Host ""
}}

# Main
Write-Host ""
Write-Host "======================================" -ForegroundColor Blue
Write-Host "  ragged Bootstrap Installer" -ForegroundColor Blue
Write-Host "======================================" -ForegroundColor Blue
Write-Host ""

# Check Python
if (-not (Test-Command python)) {{
    Write-Err "Python is required but not installed"
    Write-Info "Install Python 3.10+ from https://python.org"
    exit 1
}}

$pythonVersion = python -c "import sys; print(f'{{sys.version_info.major}}.{{sys.version_info.minor}}')"
Write-Info "Python version: $pythonVersion"

# Install Docker if needed
{install_docker_block}

# Install Ollama if needed
{install_ollama_block}

# Create directories
New-RaggedDirectories

# Install ragged
Install-Ragged

# Generate configuration
New-RaggedConfig

# Pull model
{pull_model_block}

Show-Success
'''


def generate_bootstrap_script(
    options: BootstrapOptions | None = None,
    format: ScriptFormat = ScriptFormat.BASH,
) -> str:
    """
    Generate a bootstrap installation script.

    Args:
        options: Bootstrap options.
        format: Output script format.

    Returns:
        Generated script as string.
    """
    options = options or BootstrapOptions()

    if format == ScriptFormat.BASH:
        return _generate_bash_script(options)
    elif format == ScriptFormat.POWERSHELL:
        return _generate_powershell_script(options)
    else:
        raise ValueError(f"Unsupported script format: {format}")


def _generate_bash_script(options: BootstrapOptions) -> str:
    """Generate Bash bootstrap script."""
    # Build conditional blocks
    if options.install_docker:
        install_docker_block = """if ! command_exists docker; then
        install_docker
    else
        log_info "Docker already installed"
    fi"""
    else:
        install_docker_block = 'log_info "Skipping Docker installation"'

    if options.install_ollama:
        install_ollama_block = """if ! command_exists ollama; then
        install_ollama
    else
        log_info "Ollama already installed"
    fi"""
    else:
        install_ollama_block = 'log_info "Skipping Ollama installation"'

    if options.pull_model:
        pull_model_block = "pull_model"
    else:
        pull_model_block = 'log_info "Skipping model download"'

    if options.start_services:
        start_services_block = "start_services"
    else:
        start_services_block = 'log_info "Skipping service start"'

    return BASH_BOOTSTRAP_TEMPLATE.format(
        ragged_home=options.ragged_home,
        api_port=options.api_port,
        webui_port=options.webui_port,
        llm_model=options.llm_model,
        verbose="true" if options.verbose else "false",
        dry_run="true" if options.dry_run else "false",
        install_docker_block=install_docker_block,
        install_ollama_block=install_ollama_block,
        pull_model_block=pull_model_block,
        start_services_block=start_services_block,
    )


def _generate_powershell_script(options: BootstrapOptions) -> str:
    """Generate PowerShell bootstrap script."""
    # Build conditional blocks
    if options.install_docker:
        install_docker_block = """if (-not (Test-Command docker)) {
    Install-DockerDesktop
} else {
    Write-Info "Docker already installed"
}"""
    else:
        install_docker_block = 'Write-Info "Skipping Docker installation"'

    if options.install_ollama:
        install_ollama_block = """if (-not (Test-Command ollama)) {
    Install-Ollama
} else {
    Write-Info "Ollama already installed"
}"""
    else:
        install_ollama_block = 'Write-Info "Skipping Ollama installation"'

    if options.pull_model:
        pull_model_block = "Get-OllamaModel"
    else:
        pull_model_block = 'Write-Info "Skipping model download"'

    return POWERSHELL_BOOTSTRAP_TEMPLATE.format(
        api_port=options.api_port,
        webui_port=options.webui_port,
        llm_model=options.llm_model,
        dry_run_ps="$true" if options.dry_run else "$false",
        install_docker_block=install_docker_block,
        install_ollama_block=install_ollama_block,
        pull_model_block=pull_model_block,
    )
