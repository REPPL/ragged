# Setup Issues and Solutions

Common problems during installation and first-time setup, with step-by-step solutions.

---

## Service Connectivity Issues

### Ollama Connection Failed

**Symptoms**:
- `ragged health` shows "✗ Ollama: Not running"
- Queries fail with "Connection refused" error

**Solutions**:

**Mac**:
1. Launch Ollama app from Applications folder
2. Check menu bar for Ollama icon
3. If not installed: Download from [ollama.com](https://ollama.com)

**Linux/Windows**:
```bash
# Run in separate terminal
ollama serve
```

**Verify**:
```bash
ollama list  # Should show installed models
```

**If still failing**:
- Check firewall isn't blocking port 11434
- Verify OLLAMA_BASE_URL in `.env` is correct: `http://localhost:11434`

---

### ChromaDB Connection Failed

**Symptoms**:
- `ragged health` shows "✗ ChromaDB: Connection refused"
- Adding documents fails

**Solutions (Docker users)**:

```bash
# Check if ChromaDB is running
docker compose ps

# If not running, start it
docker compose up -d

# Check logs if still failing
docker compose logs chromadb
```

**Common Docker issues**:

1. **Port already in use**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000  # Mac/Linux
   netstat -ano | findstr :8000  # Windows

   # Change port in docker-compose.yml and .env
   ```

2. **Docker not installed**:
   - Mac: Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
   - Linux: `sudo apt install docker.io docker-compose`
   - Windows: Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

**Solutions (Built-in mode users)**:

Check your `.env` file has:
```
CHROMA_IN_MEMORY=true
```

No additional setup needed for built-in mode.

---

## Python Environment Issues

### "ragged: command not found"

**Cause**: Virtual environment not activated or ragged not installed.

**Solutions**:

1. **Activate virtual environment**:
   ```bash
   cd /path/to/ragged

   # Mac/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

   You should see `(.venv)` at start of prompt.

2. **If .venv doesn't exist, create it**:
   ```bash
   python3 -m venv .venv  # Mac/Linux
   python -m venv .venv   # Windows
   ```

3. **Install ragged**:
   ```bash
   pip install -e .
   ```

4. **Verify**:
   ```bash
   ragged --version
   ```

---

### Python Version Mismatch

**Symptoms**:
- "Python 3.12 required" error
- Import errors for type hints

**Solution**:

```bash
# Check your version
python3 --version  # Mac/Linux
python --version   # Windows

# Should show: Python 3.12.x
```

**If wrong version**:
- **Mac**: Install Python 3.12 from [python.org](https://python.org)
- **Windows**: Install Python 3.12 from [python.org](https://python.org)
- **Linux**: `sudo apt install python3.12`

**Create new venv with correct version**:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

### Module Import Errors

**Symptoms**:
- "ModuleNotFoundError: No module named 'chromadb'"
- "ModuleNotFoundError: No module named 'sentence_transformers'"

**Cause**: Dependencies not installed.

**Solution**:
```bash
# Ensure venv is activated
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -e .

# If that fails, try upgrade
pip install --upgrade pip
pip install -e .
```

---

## Configuration Issues

### ".env file not found"

**Symptoms**:
- ragged starts but uses wrong settings
- Can't find models or services

**Solution**:

1. **Check if .env exists**:
   ```bash
   ls -la .env  # Mac/Linux
   dir .env     # Windows
   ```

2. **If missing, create it**:
   ```bash
   # Mac/Linux
   cat > .env << 'EOF'
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:3b
   EMBEDDING_MODEL=nomic-embed-text
   CHROMA_HOST=localhost
   CHROMA_PORT=8000
   DATA_DIR=./ragged_data
   EOF
   ```

   **Windows**: Create `.env` file in Notepad with content above.

3. **Verify**:
   ```bash
   ragged config show
   ```

---

### "Model not found" Error

**Symptoms**:
- `ragged query` fails with "Model 'llama3.2:3b' not found"

**Solution**:

1. **Check installed models**:
   ```bash
   ollama list
   ```

2. **Download the model**:
   ```bash
   ollama pull llama3.2:3b
   ```

   This downloads ~2GB, takes 5-10 minutes.

3. **Verify in .env**:
   ```bash
   grep OLLAMA_MODEL .env
   # Should match model you downloaded
   ```

4. **Update if needed**:
   ```bash
   ragged config --set OLLAMA_MODEL=llama3.2:3b
   ```

---

### Invalid Configuration Values

**Symptoms**:
- `ragged validate` shows errors
- Strange behaviour when running commands

**Solution**:

```bash
# Check for issues
ragged validate --verbose

# Auto-fix common problems
ragged validate --fix

# If still broken, reset to defaults
ragged config --reset
# Warning: This overwrites .env, backup first!
```

---

## Document Processing Issues

### "Unsupported file format"

**Supported formats**:
- ✅ PDF (`.pdf`)
- ✅ Text (`.txt`)
- ✅ Markdown (`.md`)
- ✅ Word (`.docx`)
- ✅ HTML (`.html`)

**Not supported** (yet):
- ❌ PowerPoint (`.pptx`)
- ❌ Excel (`.xlsx`)
- ❌ Images (`.jpg`, `.png`) without text

**Solution**:
Convert unsupported formats to PDF or text first.

---

### "PDF is encrypted"

**Symptoms**:
- "Cannot extract text from encrypted PDF"

**Solution**:

1. **Unlock PDF** using:
   - Adobe Acrobat
   - Preview (Mac)
   - Online tools (if not sensitive data)

2. **Save unlocked version**

3. **Add to ragged**:
   ```bash
   ragged add unlocked-document.pdf
   ```

---

### "Out of memory" During Ingestion

**Symptoms**:
- Process crashes
- System freezes
- "MemoryError" or "Killed"

**Solutions**:

1. **Use smaller embedding model** (if available in future)

2. **Process documents in batches**:
   ```bash
   # Instead of adding 100 at once
   ragged add document-1.pdf
   ragged add document-2.pdf
   # ...
   ```

3. **Increase swap space** (Linux):
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

4. **Close other applications** to free RAM

---

## Performance Issues

### Queries Take Too Long

**Normal speeds**:
- 3B model: 5-15 seconds per query
- 8B model: 10-20 seconds per query
- 70B model: 30-60 seconds per query

**If slower than this**:

**Solution 1: Use smaller model**
```bash
ollama pull llama3.2:3b
ragged config --set OLLAMA_MODEL=llama3.2:3b
```

**Solution 2: Reduce chunks retrieved**
```bash
ragged query "question" --k 3  # Instead of default 5
```

**Solution 3: Check disk speed**
```bash
# Move data to SSD if on HDD
mv ragged_data /path/to/ssd/ragged_data
# Update DATA_DIR in .env
```

---

### Adding Documents Is Slow

**Normal speeds**:
- Small doc (1-2 pages): 5-10 seconds
- Medium doc (10-20 pages): 20-40 seconds
- Large doc (100+ pages): 2-5 minutes

**If significantly slower**:

1. **Check CPU usage**: Embedding is CPU-intensive, this is normal

2. **Process in background**:
   ```bash
   ragged add large-folder/ &
   # Continue working while it processes
   ```

3. **Monitor progress with verbose flag**:
   ```bash
   ragged add folder/ --verbose
   ```

---

## Platform-Specific Issues

### macOS

**"Permission denied" when running ragged**:
```bash
chmod +x $(which ragged)
```

**Apple Silicon (M1/M2) performance**:
- Should run fast natively
- No special configuration needed

---

### Linux

**"libGL.so.1: cannot open shared object"**:
```bash
# Ubuntu/Debian
sudo apt install libgl1-mesa-glx

# Fedora
sudo dnf install mesa-libGL
```

**Docker permission denied**:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

---

### Windows

**PowerShell execution policy error**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"python: command not found"**:
- Use `python` instead of `python3`
- Or add Python to PATH during installation

**Activate script won't run**:
```powershell
# Use this instead
.venv\Scripts\Activate.ps1
```

---

## Advanced Troubleshooting

### Enable Debug Logging

```bash
ragged query "question" --debug
```

Shows detailed logs of every step.

---

### Check System Requirements

```bash
ragged env-info --verbose
```

Displays:
- Python version
- OS details
- Available RAM
- Disk space
- Installed models
- Service status

Include this output when reporting bugs!

---

### Verify Data Integrity

```bash
# Check if data directory is healthy
ls -lh ragged_data/

# Check cache sizes
ragged cache info

# Validate configuration
ragged validate --verbose
```

---

### Nuclear Option: Fresh Start

If nothing works:

```bash
# 1. Backup your documents (ragged doesn't store originals, just indexes)
cp -r original-documents/ backup/

# 2. Remove ragged data
rm -rf ragged_data/

# 3. Reinstall ragged
pip uninstall ragged
pip install -e .

# 4. Recreate .env
ragged config --reset

# 5. Re-add documents
ragged add original-documents/
```

---

## Getting Help

### Before Asking for Help

1. **Run diagnostics**:
   ```bash
   ragged health
   ragged validate --verbose
   ragged env-info > my-env.txt
   ```

2. **Check existing issues**: [GitHub Issues](https://github.com/REPPL/ragged/issues)

3. **Search FAQ**: [Frequently Asked Questions](../faq.md)

---

### How to Report Bugs

**Include in your bug report**:
1. Output of `ragged env-info --format markdown`
2. Exact command that failed
3. Complete error message
4. What you expected to happen

**Report here**: [GitHub Issues](https://github.com/REPPL/ragged/issues/new)

---

### Community Support

- **GitHub Discussions**: [Ask questions](https://github.com/REPPL/ragged/discussions)
- **FAQ**: [Common answers](../faq.md)

---

## Related Documentation

- [Complete Beginner's Guide: Troubleshooting](../../tutorials/complete-beginners-guide.md#troubleshooting) - Setup issues
- [CLI Essentials: Health Checks](../cli/essentials.md#1-ragged-health---check-system-status) - Service verification
- [CLI Advanced: Configuration Validation](../cli/advanced.md#configuration-validation-catch-issues-early) - Config checking
- [CLI Advanced: Environment Info](../cli/advanced.md#environment-information-debug-and-report-issues) - System diagnostics
- [FAQ](../faq.md) - Quick answers

---

**Most issues** can be resolved by checking service status (`ragged health`) and validating configuration (`ragged validate --verbose`). Start there!
