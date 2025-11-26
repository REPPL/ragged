# Offline Installation Guide

Install ragged in air-gapped or offline environments.

## Overview

Offline installation requires pre-downloading all dependencies on a machine with internet access, then transferring them to the target system.

### What You'll Need

1. **Online machine** - To download packages
2. **Transfer medium** - USB drive, network share, or similar
3. **Offline machine** - Target system for installation

### Package Size

| Component | Size |
|-----------|------|
| ragged package | ~50 MB |
| Python dependencies | ~500 MB |
| Docker images | ~2 GB |
| Ollama models | 3-40 GB |
| **Total (minimum)** | **~5 GB** |

---

## Step 1: Download on Online Machine

### Download ragged and Dependencies

```bash
# Create download directory
mkdir -p ~/ragged-offline/packages

# Download ragged with all dependencies
pip download ragged -d ~/ragged-offline/packages

# Or download specific version
pip download ragged==0.8.7 -d ~/ragged-offline/packages
```

### Download Docker Images

```bash
# Pull images
docker pull chromadb/chroma:latest
docker pull ollama/ollama:latest

# Save to files
docker save chromadb/chroma:latest | gzip > ~/ragged-offline/chromadb.tar.gz
docker save ollama/ollama:latest | gzip > ~/ragged-offline/ollama.tar.gz
```

### Download Ollama Models

```bash
# Pull model
ollama pull llama3.2:8b

# Export model (Linux/macOS)
# Models stored in ~/.ollama/models/
cp -r ~/.ollama/models ~/ragged-offline/ollama-models
```

### Download Installer Scripts

```bash
# Download installer
curl -o ~/ragged-offline/install.sh https://install.ragged.ai
chmod +x ~/ragged-offline/install.sh
```

### Create Verification Checksums

```bash
cd ~/ragged-offline
sha256sum * packages/* > checksums.txt
```

---

## Step 2: Transfer to Offline Machine

### USB Drive

```bash
# Mount USB drive
sudo mount /dev/sdb1 /mnt/usb

# Copy files
cp -r ~/ragged-offline/* /mnt/usb/

# Unmount
sudo umount /mnt/usb
```

### Network Share

```bash
# Mount network share
sudo mount -t cifs //server/share /mnt/share -o guest

# Copy files
cp -r ~/ragged-offline/* /mnt/share/

# Unmount
sudo umount /mnt/share
```

---

## Step 3: Install on Offline Machine

### Verify Files

```bash
cd /path/to/ragged-offline
sha256sum -c checksums.txt
```

### Install Python Dependencies

```bash
# Install from local packages
pip install --no-index --find-links=/path/to/ragged-offline/packages ragged
```

### Load Docker Images

```bash
# Load ChromaDB
gunzip -c /path/to/ragged-offline/chromadb.tar.gz | docker load

# Load Ollama (if using Docker)
gunzip -c /path/to/ragged-offline/ollama.tar.gz | docker load
```

### Install Ollama Models

```bash
# Copy models to Ollama directory
cp -r /path/to/ragged-offline/ollama-models/* ~/.ollama/models/
```

### Run Installation

```bash
# Run ragged installation
ragged install --offline

# Or with configuration
ragged install --offline --config /path/to/config.yaml
```

---

## Offline Configuration

### config.yaml for Offline Mode

```yaml
installation:
  mode: offline
  skip_updates: true
  skip_internet_check: true

services:
  ollama:
    host: localhost
    port: 11434
    # No model downloading
    auto_pull_models: false

  chromadb:
    # Use local Docker image
    image: chromadb/chroma:latest
    pull_policy: never

updates:
  # Disable all update checks
  check_for_updates: false
  auto_update: false
```

---

## Platform-Specific Instructions

### Windows Offline Install

```powershell
# Transfer files to Windows machine

# Install Python packages
pip install --no-index --find-links=D:\ragged-offline\packages ragged

# Load Docker images
docker load -i D:\ragged-offline\chromadb.tar.gz
docker load -i D:\ragged-offline\ollama.tar.gz

# Run installation
ragged install --offline
```

### macOS Offline Install

```bash
# Transfer files via USB or network

# Install Python packages
pip3 install --no-index --find-links=/Volumes/USB/ragged-offline/packages ragged

# Load Docker images
gunzip -c /Volumes/USB/ragged-offline/chromadb.tar.gz | docker load

# Run installation
ragged install --offline
```

### Linux Offline Install

```bash
# Mount transfer medium
sudo mount /dev/sdb1 /mnt/usb

# Install Python packages
pip3 install --no-index --find-links=/mnt/usb/ragged-offline/packages ragged

# Load Docker images
gunzip -c /mnt/usb/ragged-offline/chromadb.tar.gz | docker load

# Copy Ollama models
cp -r /mnt/usb/ragged-offline/ollama-models/* ~/.ollama/models/

# Run installation
ragged install --offline
```

---

## Updating Offline Installation

To update an offline installation:

1. **On online machine:**
   ```bash
   pip download ragged==<new_version> -d ~/ragged-update/packages
   ```

2. **Transfer update files**

3. **On offline machine:**
   ```bash
   pip install --no-index --find-links=/path/to/update/packages --upgrade ragged
   ragged upgrade --offline
   ```

---

## Troubleshooting

### Package Hash Mismatch

**Symptom:** "Hash mismatch" during pip install

**Solution:**
```bash
# Re-download packages with hashes
pip download ragged --require-hashes -d ~/ragged-offline/packages
```

### Docker Image Load Failed

**Symptom:** "Error loading image"

**Solution:**
```bash
# Verify image file
file /path/to/chromadb.tar.gz
# Should show: gzip compressed data

# Try loading uncompressed
gunzip /path/to/chromadb.tar.gz
docker load -i /path/to/chromadb.tar
```

### Ollama Model Not Found

**Symptom:** "Model not found" error

**Solution:**
```bash
# Verify model location
ls ~/.ollama/models/

# Ensure correct permissions
chmod -R 755 ~/.ollama/models/
```

### Dependency Conflict

**Symptom:** "Version conflict" during installation

**Solution:**
```bash
# Download with all dependencies resolved
pip download ragged --platform linux_x86_64 --only-binary=:all: -d ~/ragged-offline/packages
```

---

## Creating an Offline Bundle

For easier distribution, create a single archive:

```bash
# Create bundle
cd ~
tar czvf ragged-offline-bundle.tar.gz ragged-offline/

# Include checksum
sha256sum ragged-offline-bundle.tar.gz > ragged-offline-bundle.tar.gz.sha256
```

---

## Related Documentation

- [Enterprise Installation](./enterprise.md)
- [Troubleshooting](../troubleshooting/README.md)
- [Security](../reference/security.md)

---
