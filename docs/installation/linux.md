# Linux Installation Guide

Complete guide to installing ragged on Linux distributions.

## Supported Distributions

| Distribution | Version | Status |
|-------------|---------|--------|
| Ubuntu | 20.04+ | ✅ Fully Supported |
| Debian | 11+ | ✅ Fully Supported |
| Fedora | 37+ | ✅ Fully Supported |
| RHEL/CentOS | 8+ | ✅ Fully Supported |
| Arch Linux | Rolling | ✅ Fully Supported |
| openSUSE | Tumbleweed | ✅ Supported |
| Other | - | ⚠️ Manual Install |

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Kernel | 5.4+ | 6.0+ |
| RAM | 8 GB | 16 GB |
| Disk Space | 10 GB | 50 GB |
| CPU | 4 cores | 8+ cores |
| Internet | Required | Required |

### Software Requirements

| Software | Required | Notes |
|----------|----------|-------|
| Python 3.12+ | Required | Or 3.10+ |
| Docker Engine | Required | Not Desktop |
| curl | Required | For installer |

## Installation Methods

| Method | Best For | Time |
|--------|----------|------|
| [One-Command Install](#one-command-installation) | Most users | 5-10 min |
| [Distribution-Specific](#distribution-specific-installation) | Native packages | 5-10 min |
| [Docker-Only Mode](#docker-only-installation) | Minimal install | 5 min |
| [Manual Installation](#manual-installation) | Advanced users | 15-20 min |

---

## One-Command Installation

Works on all supported distributions.

### Step 1: Open Terminal

Open your terminal emulator (Konsole, GNOME Terminal, etc.)

### Step 2: Run the Installer

```bash
curl -sSL https://install.ragged.ai | sh
```

### Step 3: Follow the Prompts

The installer will:
1. Detect your distribution
2. Install Docker Engine (if needed)
3. Install Ollama
4. Download and configure ragged
5. Start all services

### Step 4: Verify Installation

```bash
ragged health
```

---

## Distribution-Specific Installation

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install prerequisites
sudo apt install -y curl python3 python3-pip python3-venv

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Log out and back in for group changes
# Then install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install ragged
pip3 install ragged
ragged install
```

### Fedora/RHEL/CentOS

```bash
# Install prerequisites
sudo dnf install -y curl python3 python3-pip

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Log out and back in for group changes
# Then install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install ragged
pip3 install ragged
ragged install
```

### Arch Linux

```bash
# Install prerequisites
sudo pacman -S python python-pip docker

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Log out and back in for group changes
# Install Ollama from AUR
yay -S ollama

# Install ragged
pip install ragged
ragged install
```

### openSUSE

```bash
# Install prerequisites
sudo zypper install -y python3 python3-pip curl

# Install Docker
sudo zypper install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install ragged
pip3 install ragged
ragged install
```

---

## Docker-Only Installation

For minimal dependency installations:

```bash
# Install Docker only
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Log out and back in

# Install ragged with Docker mode
pip3 install ragged
ragged install --mode docker-only
```

This mode runs Ollama and ChromaDB inside Docker containers.

---

## Manual Installation

### Step 1: Install Docker Engine

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

Verify:
```bash
docker --version
docker compose version
```

### Step 2: Install Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama
```

Verify:
```bash
ollama --version
```

### Step 3: Install Python 3.12

```bash
# Ubuntu/Debian
sudo apt install -y python3.12 python3.12-venv python3-pip

# Or use pyenv for any distribution
curl https://pyenv.run | bash
pyenv install 3.12.0
pyenv global 3.12.0
```

Verify:
```bash
python3 --version
```

### Step 4: Install ragged

```bash
pip3 install ragged
ragged install
```

---

## Systemd Service Setup

To run ragged as a system service:

```bash
# Create service file
sudo tee /etc/systemd/system/ragged.service > /dev/null <<EOF
[Unit]
Description=Ragged RAG Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/ragged start --foreground
ExecStop=/usr/local/bin/ragged stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ragged
sudo systemctl start ragged
```

Check status:
```bash
sudo systemctl status ragged
```

---

## Troubleshooting

### Docker Permission Denied

**Symptom:** "permission denied while trying to connect to the Docker daemon"

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (or log out and back in)
newgrp docker

# Verify
docker ps
```

### SELinux Blocking Docker

**Symptom:** "permission denied" errors on RHEL/Fedora

**Solutions:**

1. **Temporary (testing):**
   ```bash
   sudo setenforce 0
   ```

2. **Permanent (recommended):**
   ```bash
   # Allow container access
   sudo setsebool -P container_manage_cgroup on

   # Or use Docker SELinux policy
   sudo dnf install -y container-selinux
   ```

### Firewall Blocking Ports

**Symptom:** Cannot access services from other machines

**Solution:**
```bash
# UFW (Ubuntu)
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp
sudo ufw allow 11434/tcp

# firewalld (Fedora/RHEL)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

### Ollama Service Not Starting

**Symptom:** "ollama: command not found" or service fails

**Solutions:**

1. **Check service status:**
   ```bash
   sudo systemctl status ollama
   ```

2. **Start manually:**
   ```bash
   ollama serve
   ```

3. **Reinstall:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

### Port Already in Use

**Symptom:** "Port 8000 already in use"

**Solution:**
```bash
# Find process
sudo lsof -i :8000
# or
sudo ss -tlnp | grep 8000

# Kill process
sudo kill -9 <PID>

# Or use alternative port
ragged config set server.port 8080
ragged restart
```

### Low Memory (OOM Killer)

**Symptom:** Processes killed unexpectedly

**Solutions:**

1. **Use smaller model:**
   ```bash
   ollama pull llama3.2:3b
   ragged config set llm.model llama3.2:3b
   ```

2. **Add swap space:**
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## Uninstallation

```bash
# Stop services
ragged stop

# Uninstall ragged
ragged uninstall --full

# Or manually
pip3 uninstall ragged
rm -rf ~/.ragged

# Optionally remove Docker and Ollama
sudo apt remove docker-ce docker-ce-cli containerd.io  # Ubuntu/Debian
sudo dnf remove docker-ce docker-ce-cli containerd.io  # Fedora
```

---

## Related Documentation

- [Quick Start](../quick-start.md) - Get running in 5 minutes
- [Troubleshooting](../troubleshooting/README.md) - Resolve issues
- [FAQ](../faq.md) - Common questions
- [Enterprise Installation](./enterprise.md) - Multi-user setup

---
