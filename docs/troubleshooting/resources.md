# Resource Troubleshooting

Resolve disk space, memory, and CPU issues.

---

## Disk Space Issues

### Insufficient Disk Space

**Symptom:**
```
Error: Insufficient disk space. Required: 10GB, Available: 2GB
```

**Solution:**

**Check disk usage:**
```bash
# Overall disk usage
df -h

# Ragged disk usage
du -sh ~/.ragged/*
```

**Free up space:**
```bash
# Clear ragged cache
ragged cache clear

# Clear old logs
rm -rf ~/.ragged/logs/*.old

# Clear Docker images/containers
docker system prune -a

# Clear Ollama unused models
ollama list
ollama rm <unused-model>
```

---

### Disk Full During Installation

**Symptom:**
```
Error: No space left on device during installation
```

**Solution:**
```bash
# Clear Docker cache
docker system prune -a

# Clear pip cache
pip cache purge

# Clear temporary files
# Linux/macOS
sudo rm -rf /tmp/*

# Windows
Remove-Item -Recurse -Force $env:TEMP\*
```

---

### Large Log Files

**Symptom:**
Disk filling up over time.

**Solution:**
```bash
# Check log sizes
du -sh ~/.ragged/logs/*

# Configure log rotation
ragged config set logging.max_size "100MB"
ragged config set logging.max_files 5

# Manually clean logs
ragged logs clean --older-than 7d
```

---

## Memory Issues

### Out of Memory

**Symptom:**
```
Error: OOM (out of memory) - cannot allocate memory
```

**Solution:**

**Check memory usage:**
```bash
# System memory
free -h  # Linux
vm_stat  # macOS
```

**Use smaller Ollama model:**
```bash
# Current model requirements
ollama list

# Switch to smaller model
ollama pull llama3.2:3b
ragged config set llm.model llama3.2:3b
```

Model memory requirements:
| Model | RAM Required |
|-------|--------------|
| llama3.2:3b | 4 GB |
| llama3.2:8b | 8 GB |
| mistral:7b | 8 GB |
| llama3:70b | 40 GB |

---

### Docker Memory Limits

**Symptom:**
Docker containers killed unexpectedly.

**Solution:**

**Increase Docker memory (Desktop):**
1. Open Docker Desktop → Settings → Resources
2. Increase Memory slider
3. Click "Apply & Restart"

**Linux (systemd):**
```bash
# Edit Docker service
sudo systemctl edit docker

# Add:
[Service]
MemoryLimit=8G

# Restart
sudo systemctl restart docker
```

---

### Swap Space

**Symptom:**
System becomes slow, OOM killer activates.

**Solution:**

**Add swap space (Linux):**
```bash
# Create 8GB swap file
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**macOS:**
Swap is managed automatically. Consider reducing model size.

---

## CPU Issues

### High CPU Usage

**Symptom:**
System becomes unresponsive during ragged operations.

**Solution:**

**Limit CPU usage:**
```bash
# Limit Ollama CPU threads
ragged config set ollama.num_threads 4

# Limit Docker CPU
docker update --cpus 4 ragged-chromadb
```

**Check what's using CPU:**
```bash
# Linux
top -p $(pgrep -d',' -f ragged)

# macOS
top -pid $(pgrep -d',' -f ragged)
```

---

### Slow Queries

**Symptom:**
Queries take very long to complete.

**Solution:**

**1. Check model size:**
```bash
# Smaller models are faster
ragged config set llm.model llama3.2:3b
```

**2. Reduce chunk size:**
```bash
ragged config set retrieval.chunk_size 500
```

**3. Limit retrieved documents:**
```bash
ragged config set retrieval.top_k 3
```

---

## GPU Issues

### GPU Not Detected

**Symptom:**
Ollama running on CPU instead of GPU.

**Solution:**

**NVIDIA GPU (Linux):**
```bash
# Install NVIDIA drivers
sudo apt install nvidia-driver-535

# Install CUDA toolkit
sudo apt install nvidia-cuda-toolkit

# Verify
nvidia-smi
```

**NVIDIA GPU (Windows):**
1. Download drivers from nvidia.com
2. Install CUDA toolkit
3. Restart Ollama

**Verify GPU usage:**
```bash
# Check Ollama GPU
ollama ps

# Check NVIDIA GPU
nvidia-smi
```

---

### Apple Silicon Acceleration

Apple Silicon (M1/M2/M3) automatically uses Metal acceleration.

**Verify Metal:**
```bash
# Check Metal support
system_profiler SPDisplaysDataType | grep Metal
```

---

## Container Resource Limits

### ChromaDB Container Issues

**Symptom:**
ChromaDB container crashes or slow.

**Solution:**
```bash
# Increase container resources
docker update --memory 4g --cpus 2 ragged-chromadb

# Or in docker-compose.yml:
services:
  chromadb:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## Monitoring Resources

### Check Overall Usage

```bash
# Linux
htop
free -h
df -h

# macOS
top
vm_stat
df -h

# Windows
Get-Process | Sort-Object WorkingSet -Descending | Select -First 10
Get-WmiObject Win32_LogicalDisk
```

### Check Ragged Usage

```bash
# Ragged resource report
ragged status --resources

# Docker container stats
docker stats --no-stream
```

---

## Related Documentation

- [Permissions Troubleshooting](./permissions.md)
- [Services Troubleshooting](./services.md)
- [Platform-Specific Issues](./platform-specific.md)

---
