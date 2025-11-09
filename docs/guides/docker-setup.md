# Docker Setup Guide for ragged (Hybrid Architecture)

This guide explains how to run ragged using a hybrid architecture that maximises performance on Apple Silicon Macs.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│   macOS Host (Apple Silicon)                    │
│                                                  │
│   ┌───────────────────────────────────┐         │
│   │  Ollama (Native Application)      │         │
│   │  - Metal GPU Acceleration         │         │
│   │  - Unified Memory Access          │         │
│   │  - Port: 11434                    │         │
│   │  - 5-6x faster than Docker        │         │
│   └───────────────────────────────────┘         │
│                    ↑                             │
│                    │ HTTP API                    │
│                    │ host.docker.internal:11434  │
│   ┌────────────────┴──────────────────┐         │
│   │  Docker Containers                │         │
│   │                                   │         │
│   │  ┌──────────────────────────┐    │         │
│   │  │  ragged-app              │    │         │
│   │  │  - FastAPI application   │    │         │
│   │  │  - Port: 8000            │    │         │
│   │  └──────────────────────────┘    │         │
│   │                                   │         │
│   │  ┌──────────────────────────┐    │         │
│   │  │  chromadb                │    │         │
│   │  │  - Vector database       │    │         │
│   │  │  - Port: 8001            │    │         │
│   │  └──────────────────────────┘    │         │
│   └───────────────────────────────────┘         │
└─────────────────────────────────────────────────┘
```

## Why Hybrid Architecture?

**Docker on macOS cannot access Metal GPU** due to Apple's Virtualization.framework limitations. Running Ollama in Docker would result in:
- ❌ CPU-only execution (no GPU acceleration)
- ❌ 5-6x slower inference (e.g., 4 tokens/sec vs 24 tokens/sec)
- ❌ No access to unified memory architecture

**Benefits of hybrid approach:**
- ✅ Full Metal GPU acceleration for Ollama
- ✅ 5-6x faster LLM inference
- ✅ Access to unified memory (up to 192GB on M4 Max)
- ✅ Application remains containerised (isolation, reproducibility)
- ✅ Easy to deploy to cloud with NVIDIA GPUs later

## Prerequisites

### 1. Install Ollama Natively on macOS

Download and install from: https://ollama.ai/download

Or via Homebrew:
```bash
brew install ollama
```

### 2. Verify Ollama Installation

Start Ollama service:
```bash
ollama serve
```

In another terminal, verify it's running:
```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response with available models.

### 3. Pull Required Models

For ragged v0.1 (see `docs/implementation/plan/architecture/README.md` for model selection):
```bash
# Embedding model (required)
ollama pull nomic-embed-text

# LLM for generation (choose based on your hardware)
ollama pull llama3.2:3b      # For Macs with 16GB RAM
ollama pull mistral:7b       # For Macs with 32GB+ RAM
ollama pull qwen2.5:32b      # For Macs with 64GB+ RAM
```

### 4. Verify GPU Acceleration

Check that Ollama is using Metal:
```bash
ollama run llama3.2:3b "Hello"
```

Look for console output showing:
- "Metal" device detection
- GPU memory allocation
- Fast token generation (>20 tokens/sec on M1/M2/M3/M4)

## Starting the Development Environment

### 1. Start Ollama (Native)

In one terminal:
```bash
ollama serve
```

Keep this running in the background.

### 2. Start Docker Containers

In the ragged project directory:
```bash
cd /path/to/ragged
docker-compose up -d
```

This starts:
- `ragged-app`: Main application (port 8000)
- `chromadb`: Vector database (port 8001)

### 3. Verify Services

Check all services are healthy:
```bash
# Ollama (native)
curl http://localhost:11434/api/tags

# ChromaDB (Docker)
curl http://localhost:8001/api/v1/heartbeat

# ragged app (Docker) - once implemented
curl http://localhost:8000/health
```

## Viewing Logs

### Ollama Logs
Ollama logs appear in the terminal where `ollama serve` is running.

### Docker Container Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ragged-app
docker-compose logs -f chromadb
```

## Stopping Services

### Stop Docker Containers
```bash
docker-compose down
```

### Stop Ollama
Press `Ctrl+C` in the terminal running `ollama serve`.

Or if running as background service:
```bash
killall ollama
```

## Troubleshooting

### Issue: "Connection refused" to Ollama

**Symptom**: ragged-app can't connect to Ollama at `host.docker.internal:11434`

**Solutions:**
1. Verify Ollama is running: `curl http://localhost:11434/api/tags`
2. Check Docker's `host.docker.internal` resolution:
   ```bash
   docker run --rm alpine ping -c 1 host.docker.internal
   ```
3. Restart Docker Desktop if needed

### Issue: Slow inference despite native Ollama

**Symptom**: Token generation is slower than expected

**Solutions:**
1. Verify GPU is being used:
   ```bash
   # Check Activity Monitor for "ollama" process
   # GPU usage should be >80% during inference
   ```
2. Check model is fully loaded to GPU:
   ```bash
   ollama ps  # Shows loaded models
   ```
3. Ensure sufficient RAM for model (see model requirements)

### Issue: ChromaDB won't start

**Symptom**: ChromaDB container exits or health check fails

**Solutions:**
1. Check port 8001 isn't in use:
   ```bash
   lsof -i :8001
   ```
2. View ChromaDB logs:
   ```bash
   docker-compose logs chromadb
   ```
3. Reset ChromaDB volume:
   ```bash
   docker-compose down
   docker volume rm ragged-chroma-data
   docker-compose up -d
   ```

### Issue: Docker containers can't see source code

**Symptom**: Application fails because `src/` directory doesn't exist

**Solution:**
The `src/` directory will be created when you begin v0.1 implementation. For now, Docker will mount an empty directory, which is expected during the planning phase.

## Development Workflow

### 1. Daily Startup
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Docker services
cd /path/to/ragged
docker-compose up -d
```

### 2. Code Changes
Code changes in `./src/` are automatically reflected in the container (volume mount).
The Dockerfile runs uvicorn with `--reload` for hot-reloading.

### 3. Adding Dependencies
After updating `requirements-dev.txt`:
```bash
docker-compose build ragged-app
docker-compose up -d ragged-app
```

### 4. Daily Shutdown
```bash
# Stop Docker services
docker-compose down

# Stop Ollama (Ctrl+C in its terminal)
```

## Production Deployment

When deploying to cloud/production:

1. **Replace native Ollama with Docker Ollama + NVIDIA GPU**:
   - Use `ollama/ollama:latest` with GPU passthrough
   - Configure for CUDA/NVIDIA runtime

2. **Use production-grade ChromaDB**:
   - Consider Chroma's hosted service
   - Or self-host with persistent storage

3. **Scale application containers**:
   - Use Kubernetes/Docker Swarm
   - Add load balancers

The hybrid architecture makes local development fast while maintaining deployment flexibility.

## Further Reading

- Ollama documentation: https://github.com/ollama/ollama
- Docker Desktop for Mac: https://docs.docker.com/desktop/mac/
- ragged architecture: `docs/implementation/plan/architecture/README.md`
- Model selection guide: `docs/implementation/plan/core-concepts/model-selection.md`

---

**Last Updated**: 2025-11-09
**Architecture Version**: Hybrid (Native Ollama + Containerised Application)
