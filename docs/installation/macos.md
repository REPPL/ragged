# macOS Installation Guide

Complete guide to installing ragged on macOS 11 (Big Sur) and later.

## Prerequisites

Before installing ragged, ensure your system meets these requirements:

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| macOS Version | 11.0 (Big Sur) | 14.0 (Sonoma) |
| RAM | 8 GB | 16 GB |
| Disk Space | 10 GB | 50 GB |
| Chip | Intel or Apple Silicon | Apple Silicon (M1+) |
| Internet | Required | Required |

### Software Requirements

| Software | Required | Notes |
|----------|----------|-------|
| Xcode CLI Tools | Required | `xcode-select --install` |
| Homebrew | Recommended | Simplifies installation |
| Docker Desktop | Required | For ChromaDB |

## Installation Methods

Choose the method that best fits your needs:

| Method | Best For | Time |
|--------|----------|------|
| [One-Command Install](#one-command-installation) | Most users | 5-10 min |
| [Homebrew Installation](#homebrew-installation) | Homebrew users | 5-10 min |
| [Manual Installation](#manual-installation) | Advanced users | 15-20 min |

---

## One-Command Installation

The fastest way to install ragged on macOS.

### Step 1: Open Terminal

Press `Cmd + Space`, type "Terminal", and press Enter.

### Step 2: Run the Installer

```bash
curl -sSL https://install.ragged.ai | sh
```

### Step 3: Follow the Prompts

The installer will:
1. Install Xcode Command Line Tools (if needed)
2. Install Homebrew (if needed)
3. Install Docker Desktop (if needed)
4. Install Ollama
5. Download and configure ragged
6. Start all services

### Step 4: Verify Installation

```bash
ragged health
```

Expected output:
```
╭─────────────────────────────────────────────────────╮
│              Ragged Health Status                    │
├─────────────────────────────────────────────────────┤
│  ✅ Python 3.12.0                                   │
│  ✅ Docker Desktop 4.25.0                           │
│  ✅ Ollama 0.1.17                                   │
│  ✅ ChromaDB (healthy)                              │
│  ✅ API Server (localhost:8000)                     │
│  ✅ WebUI (localhost:5173)                          │
╰─────────────────────────────────────────────────────╯
```

---

## Homebrew Installation

For users who prefer managing packages with Homebrew.

### Step 1: Install Homebrew (if needed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies

```bash
# Install Docker Desktop
brew install --cask docker

# Install Ollama
brew install ollama

# Install Python 3.12
brew install python@3.12
```

### Step 3: Start Docker Desktop

Open Docker Desktop from Applications or:
```bash
open -a Docker
```

Wait for Docker to initialise (whale icon in menu bar becomes stable).

### Step 4: Install ragged

```bash
pip3 install ragged
ragged install
```

---

## Manual Installation

For advanced users who prefer manual control.

### Step 1: Install Xcode Command Line Tools

```bash
xcode-select --install
```

Click "Install" when prompted.

### Step 2: Install Docker Desktop

1. Download from https://docker.com/products/docker-desktop/
2. Open the `.dmg` file
3. Drag Docker to Applications
4. Open Docker from Applications
5. Follow the setup wizard
6. Wait for Docker to initialise

Verify:
```bash
docker --version
docker compose version
```

### Step 3: Install Ollama

1. Download from https://ollama.ai/download/mac
2. Open the `.dmg` file
3. Drag Ollama to Applications
4. Open Ollama from Applications

Or via command line:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

Verify:
```bash
ollama --version
```

### Step 4: Install Python 3.12

Using Homebrew:
```bash
brew install python@3.12
```

Or download from https://python.org/downloads/macos/

Verify:
```bash
python3 --version
```

### Step 5: Install ragged

```bash
pip3 install ragged
ragged install
```

---

## Apple Silicon (M1/M2/M3) Notes

Ragged is fully compatible with Apple Silicon. Some notes:

### Docker Desktop

- Use Docker Desktop 4.3+ for native Apple Silicon support
- Rosetta 2 is not required
- Performance is excellent on Apple Silicon

### Ollama

- Native Apple Silicon support
- Excellent performance with Metal acceleration
- llama3.2:8b runs smoothly on 16GB M1/M2

### Memory Considerations

Apple Silicon has unified memory, which means:
- 8GB models: Use llama3.2:3b
- 16GB models: Use llama3.2:8b
- 32GB+ models: Can run larger models

---

## Post-Installation Configuration

### Configure Ollama Model

Pull your preferred model:

```bash
# Lightweight (3GB, fast)
ollama pull llama3.2:3b

# Balanced (8GB, recommended)
ollama pull llama3.2:8b

# Powerful (40GB+)
ollama pull llama3:70b
```

Set as default:
```bash
ragged config set llm.model llama3.2:8b
```

### Start Services

```bash
# Start all services
ragged start

# Check status
ragged status
```

### Access the WebUI

Open your browser to: http://localhost:5173

---

## Troubleshooting

### Gatekeeper Blocks Application

**Symptom:** "Cannot be opened because it is from an unidentified developer"

**Solution:**
1. Open System Settings → Privacy & Security
2. Click "Open Anyway" for the blocked application
3. Or run:
   ```bash
   xattr -d com.apple.quarantine /Applications/Docker.app
   xattr -d com.apple.quarantine /Applications/Ollama.app
   ```

### Permission Denied Errors

**Symptom:** "Permission denied" when accessing files

**Solutions:**

1. **Grant Terminal Full Disk Access:**
   - Open System Settings → Privacy & Security → Full Disk Access
   - Add Terminal.app

2. **Fix file permissions:**
   ```bash
   chmod -R u+rwX ~/.ragged
   ```

### Docker Desktop Won't Start

**Symptom:** Docker Desktop hangs or crashes

**Solutions:**

1. **Reset Docker Desktop:**
   - Click Docker icon → Troubleshoot → Reset to factory defaults

2. **Remove and reinstall:**
   ```bash
   rm -rf ~/Library/Group\ Containers/group.com.docker
   rm -rf ~/Library/Containers/com.docker.docker
   rm -rf ~/.docker
   # Reinstall Docker Desktop
   ```

### Port Already in Use

**Symptom:** "Port 8000 already in use"

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use alternative port
ragged config set server.port 8080
ragged restart
```

### Rosetta 2 Issues (Intel Emulation)

**Symptom:** Errors on Apple Silicon related to x86 binaries

**Solution:**
```bash
# Install Rosetta 2 (if needed)
softwareupdate --install-rosetta

# Use native Apple Silicon versions where possible
```

---

## Uninstallation

To completely remove ragged:

```bash
# Stop services
ragged stop

# Uninstall ragged
ragged uninstall --full

# Or manually
pip3 uninstall ragged
rm -rf ~/.ragged
```

To also remove dependencies:
```bash
# Remove via Homebrew
brew uninstall ollama
brew uninstall --cask docker
```

---

## Related Documentation

- [Quick Start](../quick-start.md) - Get running in 5 minutes
- [Troubleshooting](../troubleshooting/README.md) - Resolve issues
- [FAQ](../faq.md) - Common questions
- [Video Tutorials](../videos/README.md) - Visual guides

---
