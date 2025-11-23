# Troubleshooting Guide

This guide covers common issues when installing and running ragged, especially with Docker-based deployments.

---

## Installation Issues

### "ModuleNotFoundError: No module named 'ragged'"

**Symptoms:**
- Docker containers fail with import errors
- Running `python ragged` fails
- Containers restart continuously

**Causes:**
1. Package not installed in Docker container
2. Package not installed locally (for non-Docker usage)
3. Docker volume mounts conflicting with installed package

**Solutions:**

**For Docker:**
```bash
# Rebuild containers from scratch
docker compose down
docker compose build --no-cache
docker compose up -d

# Check container logs
docker compose logs ragged-api
```

**For Local Installation:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Verify installation
ragged --version
```

---

### "ragged: command not found"

**Symptoms:**
- Typing `ragged` in terminal shows "command not found"
- Package appears to be installed but command doesn't work

**Causes:**
1. Virtual environment not activated
2. Package not installed
3. Shell not refreshed after installation

**Solutions:**

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 2. Install package
pip install -e .

# 3. Verify installation
ragged --version

# 4. If still not working, check pip show
pip show ragged
```

---

### "No requirements.txt file found"

**Symptoms:**
- Looking for `requirements.txt` but only finding `requirements-dev.txt`
- CI/CD pipeline expecting `requirements.txt`

**Explanation:**
ragged uses modern Python packaging with `pyproject.toml` as the single source of truth for dependencies.

**Solutions:**

```bash
# Install from pyproject.toml (recommended)
pip install -e .

# Or install specific groups
pip install -e ".[dev]"  # Development dependencies
```

**Why no requirements.txt?**
- `pyproject.toml` is the modern standard (PEP 621)
- Single source of truth (no duplication)
- All dependencies defined in lines 26-93 of pyproject.toml
- If you need requirements.txt for CI/CD:
  ```bash
  pip install pip-tools
  pip-compile pyproject.toml -o requirements.txt
  ```

---

## Docker Issues

### "Container ragged-api is unhealthy"

**Symptoms:**
```
ragged-api       Restarting (1) Less than a second ago   unhealthy
ragged-ui        Created
chromadb         Up (healthy)
```

**Common Causes:**
1. Import errors (most common)
2. Port conflicts
3. Missing environment variables
4. Service connectivity issues

**Diagnostic Steps:**

```bash
# 1. Check container logs
docker compose logs ragged-api --tail=50

# 2. Check container status
docker compose ps

# 3. Inspect container
docker inspect ragged-api

# 4. Try to run commands inside container
docker compose exec ragged-api python -c "import ragged; print(ragged.__version__)"
```

**Solutions:**

```bash
# Full rebuild (fixes most issues)
docker compose down
docker compose build --no-cache
docker compose up -d

# Check health endpoint
curl http://localhost:8000/api/health
```

---

### "Cannot connect to Docker daemon"

**Symptoms:**
```
unable to get image 'ragged-ragged-ui': Cannot connect to the Docker daemon
```

**Causes:**
- Docker Desktop not running
- Docker daemon not started
- Permission issues

**Solutions:**

**macOS/Windows:**
```bash
# Start Docker Desktop
# Wait for Docker icon in system tray to show "running"

# Verify Docker is running
docker ps
```

**Linux:**
```bash
# Start Docker daemon
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add user to docker group (requires logout)
sudo usermod -aG docker $USER
```

---

### "Address already in use" (Port Conflicts)

**Symptoms:**
```
Error: listen tcp 127.0.0.1:11434: bind: address already in use
Error: listen tcp 127.0.0.1:8000: bind: address already in use
```

**Causes:**
- Ollama already running on port 11434
- Another service using ports 8000, 7860, or 8001

**Diagnostic:**

```bash
# Check what's using the port
lsof -i :11434  # Ollama
lsof -i :8000   # ragged-api
lsof -i :7860   # ragged-ui
lsof -i :8001   # ChromaDB
```

**Solutions:**

**Option 1: Stop Conflicting Service**
```bash
# Find and stop the process
lsof -i :8000
kill -9 <PID>
```

**Option 2: Change Ports**
```bash
# Edit .env file
RAGGED_API_PORT=8001
RAGGED_UI_PORT=7861
CHROMA_PORT=8002

# Restart containers
docker compose down
docker compose up -d
```

---

### "dependency failed to start: container ragged-api is unhealthy"

**Symptoms:**
- ChromaDB starts successfully
- ragged-api fails health checks
- ragged-ui doesn't start (waits for ragged-api)

**Causes:**
- ragged-api not passing health checks
- Health check endpoint not responding
- Startup taking longer than timeout

**Solutions:**

```bash
# 1. Check ragged-api logs
docker compose logs ragged-api

# 2. Increase health check timeout in docker-compose.yml
# Edit start_period: 60s  # Was 40s

# 3. Test health endpoint manually
docker compose exec ragged-api curl http://localhost:8000/api/health

# 4. Rebuild if import errors
docker compose build --no-cache ragged-api
docker compose up -d
```

---

## Service Connection Issues

### ChromaDB Connection Failed

**Symptoms:**
```
ConnectionError: Could not connect to ChromaDB at http://localhost:8001
```

**Diagnostic:**

```bash
# Check ChromaDB container
docker compose ps chromadb

# Check ChromaDB logs
docker compose logs chromadb

# Test ChromaDB directly
curl http://localhost:8001/api/v1/heartbeat
```

**Solutions:**

```bash
# Restart ChromaDB
docker compose restart chromadb

# Full restart
docker compose down
docker compose up chromadb -d

# Check .env file has correct URL
CHROMA_URL=http://chromadb:8001  # For Docker
RAGGED_CHROMA_URL=http://localhost:8001  # For local
```

---

### Ollama Connection Failed

**Symptoms:**
```
ConnectionError: Could not connect to Ollama at http://localhost:11434
ollama.OllamaError: Ollama is not running
```

**Diagnostic:**

```bash
# Check Ollama is running
ollama list

# Check Ollama serve
curl http://localhost:11434/api/tags
```

**Solutions:**

```bash
# Start Ollama
ollama serve

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text

# Check .env configuration
OLLAMA_URL=http://host.docker.internal:11434  # For Docker
RAGGED_OLLAMA_URL=http://localhost:11434  # For local
```

---

## Environment Variable Issues

### Missing or Incorrect .env File

**Symptoms:**
- Containers start but can't connect to services
- Default ports don't work
- Services can't find each other

**Solution:**

```bash
# Create .env from example
cp .env.example .env

# Verify critical variables
cat .env | grep -E "(OLLAMA_URL|CHROMA_URL|RAGGED_API_URL)"

# Expected values for Docker:
# OLLAMA_URL=http://host.docker.internal:11434
# CHROMA_URL=http://chromadb:8001
# RAGGED_API_URL=http://ragged-api:8000
```

---

## Package & Dependency Issues

### "pip install -e ." Fails

**Symptoms:**
```
ERROR: File "setup.py" not found
error: invalid command 'egg_info'
```

**Causes:**
- Old pip version
- Missing build tools

**Solutions:**

```bash
# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# Try installation again
pip install -e .

# If still failing, check Python version
python --version  # Should be 3.12
```

---

### Import Errors After Installation

**Symptoms:**
```python
>>> import ragged
ImportError: No module named 'ragged'
```

**Diagnostic:**

```bash
# Check package is installed
pip list | grep ragged

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check site-packages
pip show ragged
```

**Solutions:**

```bash
# Reinstall
pip uninstall ragged
pip install -e .

# Verify
python -c "import ragged; print(ragged.__file__)"
```

---

## Logs and Debugging

### Viewing All Container Logs

```bash
# All services
docker compose logs

# Follow logs (real-time)
docker compose logs -f

# Specific service
docker compose logs ragged-api

# Last N lines
docker compose logs --tail=100 ragged-api

# Since specific time
docker compose logs --since=10m
```

### Debugging Inside Containers

```bash
# Start a shell in running container
docker compose exec ragged-api bash

# Run Python interactively
docker compose exec ragged-api python

# Check environment variables
docker compose exec ragged-api env | grep RAGGED

# Test imports
docker compose exec ragged-api python -c "from ragged.web.api import app; print('OK')"
```

### System Information for Bug Reports

```bash
# Gather system information
ragged env-info

# Or manually:
docker --version
docker compose version
python --version
ollama --version

# Check container health
docker compose ps
```

---

## Still Having Issues?

1. **Check the logs** first: `docker compose logs --tail=100`
2. **Rebuild from scratch**:
   ```bash
   docker compose down --volumes
   docker compose build --no-cache
   docker compose up -d
   ```
3. **Review documentation**:
   - [Installation Guide](../tutorials/installation.md)
   - [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md)
4. **Get help**:
   - Search [existing issues](https://github.com/REPPL/ragged/issues)
   - File a [new issue](https://github.com/REPPL/ragged/issues/new) with:
     - Output of `ragged env-info`
     - Relevant log excerpts
     - Steps to reproduce

---

## Related Documentation

- [Installation Guide](../tutorials/installation.md) - Complete installation instructions
- [Complete Beginner's Guide](../tutorials/complete-beginners-guide.md) - Step-by-step tutorial
- [README.md](../../README.md) - Quick start guide
