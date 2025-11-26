# Windows Installation Guide

Complete guide to installing ragged on Windows 10 and Windows 11.

## Prerequisites

Before installing ragged, ensure your system meets these requirements:

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Windows Version | Windows 10 (1903+) | Windows 11 |
| RAM | 8 GB | 16 GB |
| Disk Space | 10 GB | 50 GB |
| CPU | 4 cores | 8+ cores |
| Internet | Required | Required |

### Software Requirements

| Software | Required | Notes |
|----------|----------|-------|
| PowerShell | 5.1+ | Pre-installed on Windows 10/11 |
| Docker Desktop | 4.0+ | Installer will guide you |
| WSL 2 | Required | For Docker Desktop |

## Installation Methods

Choose the method that best fits your needs:

| Method | Best For | Time |
|--------|----------|------|
| [One-Command Install](#one-command-installation) | Most users | 5-10 min |
| [Manual Installation](#manual-installation) | Advanced users | 15-20 min |
| [Offline Installation](#offline-installation) | Air-gapped systems | 20-30 min |

---

## One-Command Installation

The fastest way to install ragged on Windows.

### Step 1: Open PowerShell as Administrator

1. Press `Win + X`
2. Select "Windows Terminal (Admin)" or "PowerShell (Admin)"
3. Click "Yes" when prompted by User Account Control

### Step 2: Run the Installer

```powershell
irm https://install.ragged.ai/windows | iex
```

### Step 3: Follow the Prompts

The installer will:
1. Check system requirements
2. Install Docker Desktop (if needed)
3. Install WSL 2 (if needed)
4. Install Ollama
5. Download and configure ragged
6. Start all services

### Step 4: Verify Installation

```powershell
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

## Manual Installation

For advanced users who prefer manual control.

### Step 1: Install WSL 2

```powershell
# Run as Administrator
wsl --install
```

Restart your computer when prompted.

### Step 2: Install Docker Desktop

1. Download Docker Desktop from https://docker.com/products/docker-desktop/
2. Run the installer
3. During installation, ensure "Use WSL 2 instead of Hyper-V" is selected
4. Start Docker Desktop after installation
5. Wait for Docker to initialise (whale icon in system tray becomes stable)

Verify Docker:
```powershell
docker --version
docker compose version
```

### Step 3: Install Ollama

1. Download Ollama from https://ollama.ai/download/windows
2. Run the installer
3. Ollama starts automatically as a system service

Verify Ollama:
```powershell
ollama --version
```

### Step 4: Install Python 3.12

1. Download Python 3.12 from https://python.org/downloads/
2. Run the installer
3. **Important:** Check "Add Python to PATH"
4. Select "Install Now"

Verify Python:
```powershell
python --version
```

### Step 5: Install ragged

```powershell
pip install ragged
ragged install
```

---

## Post-Installation Configuration

### Configure Ollama Model

Pull your preferred model:

```powershell
# Lightweight (3GB, fast)
ollama pull llama3.2:3b

# Balanced (8GB, recommended)
ollama pull llama3.2:8b

# Powerful (40GB+)
ollama pull llama3:70b
```

Set as default:
```powershell
ragged config set llm.model llama3.2:8b
```

### Start Services

Services start automatically, but you can control them:

```powershell
# Start all services
ragged start

# Stop all services
ragged stop

# Restart services
ragged restart

# Check status
ragged status
```

### Access the WebUI

Open your browser to: http://localhost:5173

---

## Troubleshooting

### Docker Desktop Won't Start

**Symptom:** Docker Desktop fails to start or shows error.

**Solutions:**

1. **Enable WSL 2:**
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

2. **Enable Virtualisation in BIOS:**
   - Restart computer
   - Enter BIOS (usually F2, F12, or Del during boot)
   - Enable "Intel VT-x" or "AMD-V"
   - Save and exit

3. **Disable conflicting software:**
   - VirtualBox
   - VMware
   - Windows Sandbox

   These may conflict with Hyper-V used by Docker.

### Port Already in Use

**Symptom:** Error message "Port 8000 already in use"

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace 12345 with actual PID)
taskkill /PID 12345 /F

# Or use alternative port
ragged config set server.port 8080
ragged restart
```

### Permission Denied Errors

**Symptom:** Error "Access is denied" or "Permission denied"

**Solutions:**

1. **Run PowerShell as Administrator**
2. **Check folder ownership:**
   ```powershell
   icacls "$HOME\.ragged"
   ```
3. **Reset permissions:**
   ```powershell
   takeown /F "$HOME\.ragged" /R /D Y
   icacls "$HOME\.ragged" /reset /T
   ```

### WSL 2 Errors

**Symptom:** WSL errors during Docker or installation

**Solutions:**

1. **Update WSL:**
   ```powershell
   wsl --update
   ```

2. **Reset WSL:**
   ```powershell
   wsl --shutdown
   wsl
   ```

3. **Reinstall WSL:**
   ```powershell
   wsl --unregister Ubuntu
   wsl --install
   ```

### Firewall Blocking Connections

**Symptom:** Cannot connect to services or timeouts

**Solution:**
```powershell
# Allow ragged through Windows Firewall
New-NetFirewallRule -DisplayName "Ragged API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Ragged WebUI" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```

---

## Uninstallation

To completely remove ragged:

```powershell
# Stop services
ragged stop

# Uninstall ragged
ragged uninstall --full

# Or manually
pip uninstall ragged
Remove-Item -Recurse -Force "$HOME\.ragged"
```

---

## Related Documentation

- [Quick Start](../quick-start.md) - Get running in 5 minutes
- [Troubleshooting](../troubleshooting/README.md) - Resolve issues
- [FAQ](../faq.md) - Common questions
- [Video Tutorials](../videos/README.md) - Visual guides

---
