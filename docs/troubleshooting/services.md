# Service Troubleshooting

Resolve issues with ragged services starting, running, and communicating.

---

## Service Won't Start

### API Server Won't Start

**Symptom:**
```
Error: Failed to start API server
```

**Common Causes & Solutions:**

1. **Port in use:**
   ```bash
   # Check port
   lsof -i :8000

   # Use alternative
   ragged config set server.port 8080
   ```

2. **Configuration error:**
   ```bash
   # Validate config
   ragged config validate

   # Reset to defaults
   ragged config reset
   ```

3. **Missing dependencies:**
   ```bash
   # Reinstall
   pip install --upgrade ragged
   ```

---

### WebUI Won't Start

**Symptom:**
```
Error: Failed to start WebUI on port 5173
```

**Solutions:**

1. **Check if API is running first:**
   ```bash
   ragged status
   # API must be healthy before WebUI
   ```

2. **Port conflict:**
   ```bash
   ragged config set webui.port 5174
   ragged restart
   ```

3. **Node.js issues (if applicable):**
   ```bash
   # Check Node version
   node --version
   # Requires Node 18+
   ```

---

### ChromaDB Won't Start

**Symptom:**
```
Error: ChromaDB container failed to start
```

**Solutions:**

1. **Docker not running:**
   ```bash
   # Start Docker
   # Windows/macOS: Open Docker Desktop
   # Linux:
   sudo systemctl start docker
   ```

2. **Port conflict:**
   ```bash
   # ChromaDB uses port 8000 by default
   # Check for conflicts
   lsof -i :8000
   ```

3. **Container stuck:**
   ```bash
   # Remove and recreate
   docker rm -f ragged-chromadb
   ragged start
   ```

4. **Volume corruption:**
   ```bash
   # Backup and recreate volume
   docker volume rm ragged_chromadb_data
   ragged start
   # Note: This deletes indexed documents!
   ```

---

### Ollama Won't Start

**Symptom:**
```
Error: Cannot connect to Ollama service
```

**Solutions:**

1. **Start Ollama:**
   ```bash
   # Linux
   sudo systemctl start ollama

   # macOS/Windows
   ollama serve
   ```

2. **Check if running:**
   ```bash
   curl http://localhost:11434/api/version
   ```

3. **Reinstall:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

---

## Service Crashes

### API Server Crashes

**Symptom:**
Server starts but crashes during operation.

**Diagnosis:**
```bash
# Check logs
ragged logs --service api --tail 100

# Check for crash dumps
ls ~/.ragged/logs/crash_*
```

**Common Causes:**

1. **Out of memory:**
   - Use smaller model
   - Increase system RAM
   - Add swap space

2. **Unhandled exception:**
   - Check logs for Python traceback
   - Report bug if reproducible

3. **Configuration issue:**
   ```bash
   ragged config validate
   ```

---

### ChromaDB Container Crashes

**Symptom:**
ChromaDB container exits unexpectedly.

**Diagnosis:**
```bash
# Check container logs
docker logs ragged-chromadb --tail 100

# Check container status
docker ps -a | grep chromadb
```

**Solutions:**

1. **Memory limit:**
   ```bash
   # Increase container memory
   docker update --memory 4g ragged-chromadb
   ```

2. **Disk full:**
   ```bash
   # Check disk space
   df -h

   # Clean up
   docker system prune
   ```

3. **Corrupted data:**
   ```bash
   # Reset ChromaDB (loses data!)
   docker volume rm ragged_chromadb_data
   ragged start
   ```

---

## Service Communication Issues

### API Cannot Connect to ChromaDB

**Symptom:**
```
Error: Connection refused to ChromaDB
```

**Solutions:**

1. **Check ChromaDB is running:**
   ```bash
   docker ps | grep chromadb
   ```

2. **Check network:**
   ```bash
   # Test connection
   curl http://localhost:8000/api/v1/heartbeat
   ```

3. **Docker network issue:**
   ```bash
   # Recreate network
   docker network rm ragged_network
   ragged start
   ```

---

### API Cannot Connect to Ollama

**Symptom:**
```
Error: Ollama connection refused
```

**Solutions:**

1. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/version
   ```

2. **Check configuration:**
   ```bash
   ragged config get ollama.host
   ragged config get ollama.port
   ```

3. **Firewall blocking:**
   ```bash
   # Allow Ollama port
   sudo ufw allow 11434/tcp
   ```

---

### WebUI Cannot Connect to API

**Symptom:**
WebUI shows "Cannot connect to backend"

**Solutions:**

1. **Check API is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **CORS issues:**
   ```bash
   # Check CORS configuration
   ragged config get server.cors_origins

   # Allow WebUI origin
   ragged config set server.cors_origins '["http://localhost:5173"]'
   ```

3. **Wrong API URL:**
   - Check browser console for errors
   - Verify API URL in WebUI settings

---

## Service Timeouts

### Query Timeouts

**Symptom:**
```
Error: Query timed out after 30 seconds
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   ragged config set query.timeout 120
   ```

2. **Use smaller model:**
   ```bash
   ragged config set llm.model llama3.2:3b
   ```

3. **Reduce context:**
   ```bash
   ragged config set retrieval.top_k 3
   ```

---

### Startup Timeouts

**Symptom:**
Services take too long to start.

**Solutions:**

1. **Check system resources:**
   ```bash
   # CPU/Memory usage
   top
   ```

2. **Increase startup timeout:**
   ```bash
   ragged config set startup.timeout 120
   ```

3. **Start services individually:**
   ```bash
   ragged start --service chromadb
   ragged start --service api
   ragged start --service webui
   ```

---

## Health Check Failures

### Running Health Check

```bash
ragged health
```

### Interpreting Results

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ | Service healthy | None needed |
| ⚠️ | Service degraded | Check logs |
| ❌ | Service failed | Restart service |
| ⏳ | Service starting | Wait |

### Fixing Failed Services

```bash
# Restart failed service
ragged restart --service <name>

# Restart all services
ragged restart

# Full reset
ragged stop
ragged start
```

---

## Related Documentation

- [Prerequisites](./prerequisites.md)
- [Network](./network.md)
- [Resources](./resources.md)
- [Platform-Specific](./platform-specific.md)

---
