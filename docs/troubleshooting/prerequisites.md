# Prerequisite Troubleshooting

Resolve issues with Docker, Python, and Ollama installation.

---

## Docker Issues

### Docker Not Installed

**Symptom:**
```
Error: Docker not found. Please install Docker Desktop.
```

**Solution:**

**Windows:**
```powershell
# Download and install Docker Desktop
Start-Process "https://desktop.docker.com/win/stable/Docker Desktop Installer.exe"
```

**macOS:**
```bash
# Using Homebrew
brew install --cask docker

# Or download from docker.com
open "https://docker.com/products/docker-desktop"
```

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in
```

---

### Docker Not Running

**Symptom:**
```
Error: Cannot connect to Docker daemon. Is Docker running?
```

**Solution:**

**Windows:**
1. Open Docker Desktop from Start Menu
2. Wait for whale icon to stabilise in system tray
3. If it doesn't start:
   - Right-click Docker icon → Restart
   - Or: Settings → Reset → Reset to factory defaults

**macOS:**
1. Open Docker from Applications
2. Wait for whale icon in menu bar
3. If stuck: `killall Docker && open -a Docker`

**Linux:**
```bash
# Start Docker service
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

---

### Docker Permission Denied

**Symptom:**
```
Error: permission denied while trying to connect to the Docker daemon socket
```

**Solution (Linux):**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply immediately (or log out/in)
newgrp docker

# Verify
docker ps
```

---

### Docker Desktop WSL 2 Error (Windows)

**Symptom:**
```
Error: WSL 2 installation is incomplete
```

**Solution:**
```powershell
# Install WSL 2
wsl --install

# If already installed, update
wsl --update

# Set WSL 2 as default
wsl --set-default-version 2

# Restart Docker Desktop
```

---

### Docker Desktop Virtualisation Error

**Symptom:**
```
Error: Hardware assisted virtualization and data execution protection must be enabled
```

**Solution:**
1. Restart computer
2. Enter BIOS (F2, F12, or Del during boot)
3. Find CPU/Virtualisation settings
4. Enable:
   - Intel: "Intel VT-x" or "Intel Virtualization Technology"
   - AMD: "AMD-V" or "SVM Mode"
5. Save and exit BIOS
6. Start Docker Desktop

---

## Python Issues

### Python Not Found

**Symptom:**
```
Error: Python 3.12+ required. Current: not found
```

**Solution:**

**Windows:**
```powershell
# Download Python 3.12
Start-Process "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
# During install: Check "Add Python to PATH"
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.12

# Or download from python.org
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# Fedora
sudo dnf install python3.12

# Or use pyenv
curl https://pyenv.run | bash
pyenv install 3.12.0
pyenv global 3.12.0
```

---

### Python Version Too Old

**Symptom:**
```
Error: Python 3.12+ required. Current: 3.9.7
```

**Solution:**
Install Python 3.12+ alongside existing version, then:

```bash
# Use specific version
python3.12 -m pip install ragged

# Or update PATH to prioritise new version
export PATH="/usr/local/bin:$PATH"  # macOS Homebrew
```

---

### pip Not Found

**Symptom:**
```
Error: pip: command not found
```

**Solution:**
```bash
# Ensure pip is installed
python3 -m ensurepip --upgrade

# Or install directly
curl https://bootstrap.pypa.io/get-pip.py | python3
```

---

## Ollama Issues

### Ollama Not Installed

**Symptom:**
```
Error: Ollama not found. Please install Ollama.
```

**Solution:**

**All platforms:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS (Homebrew):**
```bash
brew install ollama
```

**Windows:**
Download from https://ollama.ai/download/windows

---

### Ollama Connection Refused

**Symptom:**
```
Error: Connection refused to Ollama at localhost:11434
```

**Solution:**

**Start Ollama service:**
```bash
# Linux
sudo systemctl start ollama

# macOS/Windows - Ollama should auto-start
# If not, run manually:
ollama serve
```

**Check if running:**
```bash
curl http://localhost:11434/api/version
```

---

### Ollama Model Not Found

**Symptom:**
```
Error: Model 'llama3.2:8b' not found
```

**Solution:**
```bash
# Pull the model
ollama pull llama3.2:8b

# List available models
ollama list

# Use a different model
ragged config set llm.model llama3.2:3b
```

---

### Ollama Out of Memory

**Symptom:**
```
Error: OOM (out of memory) loading model
```

**Solution:**

Use a smaller model:
```bash
# List available models by size
ollama list

# Use smaller model
ollama pull llama3.2:3b
ragged config set llm.model llama3.2:3b
```

Model size requirements:
| Model | Minimum RAM |
|-------|-------------|
| llama3.2:3b | 4 GB |
| llama3.2:8b | 8 GB |
| llama3:70b | 40 GB |

---

## Verification

After fixing issues, verify installation:

```bash
# Check all prerequisites
ragged diagnose

# Or check individually
docker --version
python3 --version
ollama --version
```

---

## Related Documentation

- [Network Troubleshooting](./network.md)
- [Permission Troubleshooting](./permissions.md)
- [Installation Guides](../installation/README.md)

---
