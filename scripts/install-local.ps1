#Requires -Version 5.1
<#
.SYNOPSIS
    ragged Local Installation Script (Windows)

.DESCRIPTION
    This script installs ragged locally for CLI usage without Docker on Windows.

.EXAMPLE
    # From PowerShell (as Administrator):
    irm https://raw.githubusercontent.com/REPPL/ragged/main/scripts/install-local.ps1 | iex

    # OR from cloned repo:
    .\scripts\install-local.ps1

.NOTES
    Requirements:
    - Python 3.12
    - PowerShell 5.1+
    - Git (optional, for cloning)
#>

param(
    [switch]$SkipPathSetup = $false
)

# Configuration
$ErrorActionPreference = "Stop"
$PYTHON_VERSION = "3.12"
$PROJECT_NAME = "ragged"
$REPO_URL = "https://github.com/REPPL/ragged.git"
$INSTALL_DIR = Join-Path $env:USERPROFILE ".ragged"

# Colours
$Colors = @{
    Red    = "Red"
    Green  = "Green"
    Yellow = "Yellow"
    Blue   = "Cyan"
}

# Helper functions
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ  $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓  $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠  $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗  $Message" -ForegroundColor $Colors.Red
}

function Print-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor $Colors.Blue
    Write-Host "║  ragged - Local Installation              ║" -ForegroundColor $Colors.Blue
    Write-Host "║  Privacy-first Multi-modal RAG System     ║" -ForegroundColor $Colors.Blue
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor $Colors.Blue
    Write-Host ""
}

function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-PythonCommand {
    Write-Info "Checking Python $PYTHON_VERSION..."

    # Try python3.12 first
    if (Test-CommandExists "python3.12") {
        $pythonCmd = "python3.12"
    }
    # Try python3
    elseif (Test-CommandExists "python3") {
        $pythonCmd = "python3"
    }
    # Try python
    elseif (Test-CommandExists "python") {
        $pythonCmd = "python"
    }
    else {
        Write-Error "Python not found"
        Write-Error "Install Python $PYTHON_VERSION from: https://www.python.org/downloads/"
        exit 1
    }

    # Verify version
    $versionOutput = & $pythonCmd --version 2>&1
    if ($versionOutput -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]

        if ($major -eq 3 -and $minor -ge 12) {
            Write-Success "Found $versionOutput"
            return $pythonCmd
        }
        else {
            Write-Error "Python $PYTHON_VERSION required, found Python $major.$minor"
            Write-Error "Install from: https://www.python.org/downloads/"
            exit 1
        }
    }
    else {
        Write-Error "Could not determine Python version"
        exit 1
    }
}

function Get-InstallLocation {
    # Check if running from cloned repo
    if ((Test-Path "pyproject.toml") -and (Test-Path "src")) {
        $script:INSTALL_DIR = (Get-Location).Path
        Write-Info "Installing from current directory: $INSTALL_DIR"
        return $true  # FROM_REPO
    }
    else {
        Write-Info "Installing to: $INSTALL_DIR"
        return $false  # Not from repo
    }
}

function Clone-Repository {
    if (Test-Path $INSTALL_DIR) {
        Write-Warning "Directory $INSTALL_DIR already exists"
        $response = Read-Host "Remove and reinstall? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Remove-Item -Path $INSTALL_DIR -Recurse -Force
        }
        else {
            Write-Error "Installation cancelled"
            exit 1
        }
    }

    Write-Info "Cloning repository..."
    if (Test-CommandExists "git") {
        git clone $REPO_URL $INSTALL_DIR
        Write-Success "Repository cloned"
    }
    else {
        Write-Error "git not found. Install git or clone manually:"
        Write-Error "  $REPO_URL"
        exit 1
    }
}

function New-VirtualEnvironment {
    param([string]$PythonCmd)

    Write-Info "Creating virtual environment..."

    Set-Location $INSTALL_DIR

    if (Test-Path ".venv") {
        Write-Warning "Virtual environment already exists"
        $response = Read-Host "Recreate? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Remove-Item -Path ".venv" -Recurse -Force
        }
        else {
            Write-Info "Using existing virtual environment"
            return
        }
    }

    & $PythonCmd -m venv .venv
    Write-Success "Virtual environment created"
}

function Install-Ragged {
    Write-Info "Installing ragged and dependencies..."

    Set-Location $INSTALL_DIR

    # Activate venv and install
    $venvPython = Join-Path $INSTALL_DIR ".venv\Scripts\python.exe"
    $venvPip = Join-Path $INSTALL_DIR ".venv\Scripts\pip.exe"

    # Upgrade pip
    & $venvPip install --quiet --upgrade pip setuptools wheel

    # Install ragged in editable mode
    & $venvPip install --quiet -e ".[dev]"

    Write-Success "ragged installed"
}

function Test-Installation {
    Write-Info "Verifying installation..."

    Set-Location $INSTALL_DIR

    $venvRagged = Join-Path $INSTALL_DIR ".venv\Scripts\ragged.exe"

    try {
        $version = & $venvRagged --version 2>&1
        Write-Success "Installation verified: $version"
    }
    catch {
        Write-Error "Installation verification failed"
        Write-Error "ragged command not working"
        exit 1
    }
}

function Add-ToPath {
    if ($SkipPathSetup) {
        Write-Info "Skipping PATH setup (--SkipPathSetup)"
        return
    }

    Write-Info "Setting up PATH..."

    $binDir = Join-Path $INSTALL_DIR ".venv\Scripts"

    # Check if already in PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -like "*$binDir*") {
        Write-Success "PATH already configured"
        return
    }

    Write-Info "Add $binDir to PATH?"
    Write-Info "This will modify user environment variables"
    $response = Read-Host "Continue? (Y/n)"

    if ($response -ne 'n' -and $response -ne 'N') {
        $newPath = "$currentPath;$binDir"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$binDir"  # Update current session
        Write-Success "PATH configured"
        Write-Info "Restart PowerShell for changes to take effect"
    }
    else {
        Write-Info "Skipped PATH setup"
        Write-Info "To use ragged, activate venv manually:"
        Write-Info "  .\.venv\Scripts\Activate.ps1"
    }
}

function Print-NextSteps {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor $Colors.Green
    Write-Host "║  Installation Complete!                    ║" -ForegroundColor $Colors.Green
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor $Colors.Green
    Write-Host ""
    Write-Success "ragged is installed at: $INSTALL_DIR"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor $Colors.Blue
    Write-Host ""
    Write-Host "1. Activate the virtual environment:"
    Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor $Colors.Yellow
    Write-Host ""
    Write-Host "2. Verify installation:"
    Write-Host "   ragged --version" -ForegroundColor $Colors.Yellow
    Write-Host ""
    Write-Host "3. Check system health:"
    Write-Host "   ragged health" -ForegroundColor $Colors.Yellow
    Write-Host ""
    Write-Host "4. Ingest your first document:"
    Write-Host "   ragged ingest pdf C:\path\to\document.pdf" -ForegroundColor $Colors.Yellow
    Write-Host ""
    Write-Host "5. Query your documents:"
    Write-Host "   ragged query text `"your question`"" -ForegroundColor $Colors.Yellow
    Write-Host ""
    Write-Info "For Docker-based installation (API + UI), use WSL or Docker Desktop"
    Write-Host ""
    Write-Info "Documentation: $INSTALL_DIR\docs\tutorials\installation.md"
    Write-Host ""
}

# Main installation flow
function Main {
    Print-Banner

    $pythonCmd = Get-PythonCommand
    $fromRepo = Get-InstallLocation

    if (-not $fromRepo) {
        Clone-Repository
    }

    New-VirtualEnvironment -PythonCmd $pythonCmd
    Install-Ragged
    Test-Installation
    Add-ToPath
    Print-NextSteps
}

# Run main function
try {
    Main
}
catch {
    Write-Error "Installation failed: $_"
    exit 1
}
