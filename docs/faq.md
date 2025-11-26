# Frequently Asked Questions

Answers to the most common questions about ragged.

---

## Installation Questions

### Do I need to install Docker Desktop?

**For most users, yes.** Docker Desktop provides Docker and Docker Compose, which ragged uses to run ChromaDB (the vector database).

**Exceptions:**
- Linux users can use Docker Engine instead of Docker Desktop
- Future versions may support embedded mode without Docker

---

### Which Ollama model should I choose?

Depends on your available RAM:

| RAM | Recommended Model | Command |
|-----|-------------------|---------|
| < 8GB | llama3.2:3b | `ollama pull llama3.2:3b` |
| 8-16GB | llama3.2:8b | `ollama pull llama3.2:8b` |
| 16GB+ | mistral or larger | `ollama pull mistral` |

Start with a smaller model and upgrade if needed:
```bash
ragged config set llm.model llama3.2:8b
```

---

### Can I install ragged without admin/sudo?

**Yes!** Ragged installs to your user directory (`~/.ragged/`) and doesn't require admin rights.

However, installing dependencies (Docker, Ollama) may require admin rights initially.

---

### How long does installation take?

Typically **5-10 minutes**, depending on:
- Internet speed (downloading Docker, Ollama, models)
- Whether dependencies are already installed
- System performance

---

### Can I install ragged offline?

**Yes.** See the [Offline Installation Guide](./installation/offline.md).

You'll need to pre-download all dependencies on a machine with internet access, then transfer them.

---

### Where is ragged installed?

```
~/.ragged/
├── documents/    # Your uploaded documents
├── cache/        # Embeddings and model cache
├── logs/         # Application logs
├── data/         # ChromaDB data
└── config.yaml   # Configuration file
```

---

## Configuration Questions

### How do I change the default model?

```bash
ragged config set llm.model llama3.2:8b
```

Or edit `~/.ragged/config.yaml` directly.

---

### How do I change the server port?

```bash
ragged config set server.port 8080
ragged restart
```

---

### Can I use ragged without the WebUI?

**Yes!** Ragged has a full-featured CLI:

```bash
ragged ingest document.pdf
ragged query "What is this about?"
ragged list
```

Install without WebUI:
```bash
ragged install --no-webui
```

---

### How do I reset to default configuration?

```bash
ragged config reset
```

This preserves your documents but resets all settings.

---

### How do I backup my data?

```bash
ragged export --all --output backup.zip
```

To restore:
```bash
ragged import backup.zip
```

---

## Usage Questions

### What file types are supported?

| Format | Extensions |
|--------|------------|
| PDF | .pdf |
| Microsoft Word | .docx, .doc |
| Plain Text | .txt |
| Markdown | .md |
| HTML | .html, .htm |
| Rich Text | .rtf |

---

### How many documents can I upload?

There's no hard limit. Practical limits depend on:
- Available disk space
- RAM for processing
- Query performance with very large collections

Thousands of documents work well on typical hardware.

---

### How do I delete a document?

```bash
ragged remove document.pdf
```

Or use the WebUI to delete from your library.

---

### Can I query across multiple documents?

**Yes!** By default, ragged searches all your documents:

```bash
ragged query "Compare the approaches in these papers"
```

To query specific documents:
```bash
ragged query "What does this say?" --filter "filename:report.pdf"
```

---

### How accurate are the answers?

Accuracy depends on:
- **Document quality**: Clear text produces better results
- **Question clarity**: Specific questions get better answers
- **Model size**: Larger models are generally more accurate

Ragged always shows sources so you can verify answers.

---

## Troubleshooting Questions

### Installation failed with "Port 8000 already in use"

Another application is using port 8000:

```bash
# Find the process
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Either stop that process, or use a different port:
ragged config set server.port 8080
```

---

### Docker Desktop won't start on Windows

Common causes:
1. **WSL 2 not installed**: Run `wsl --install` in PowerShell (admin)
2. **Virtualisation disabled**: Enable VT-x/AMD-V in BIOS
3. **Hyper-V conflicts**: Disable VirtualBox or VMware

See [Windows Troubleshooting](./troubleshooting/platform-specific.md#windows).

---

### "Permission denied" errors

Usually caused by running installation with sudo:

```bash
# Fix ownership
sudo chown -R $USER:$(id -gn) ~/.ragged

# Fix permissions
chmod 700 ~/.ragged
```

---

### Queries are very slow

Try these optimisations:

1. **Use a smaller model**:
   ```bash
   ragged config set llm.model llama3.2:3b
   ```

2. **Reduce context size**:
   ```bash
   ragged config set retrieval.top_k 3
   ```

3. **Check available memory**:
   Close other applications or add more RAM.

---

### How do I view logs?

```bash
ragged logs --tail 50
```

Log files are in `~/.ragged/logs/`.

---

## Privacy Questions

### Is my data sent to the cloud?

**No.** Ragged runs entirely on your local machine:
- Documents stay on your disk
- AI processing is local (via Ollama)
- No telemetry or usage tracking

---

### Can I use ragged in an air-gapped environment?

**Yes.** See [Offline Installation](./installation/offline.md).

---

### Is my data encrypted?

- **At rest**: Documents are stored as-is on your local disk
- **In transit**: All local communication uses HTTP (no external network)
- **Optional**: Enable encryption in config for sensitive deployments

---

## Advanced Questions

### Can I use a different LLM provider?

Currently, ragged uses Ollama for local inference. Support for other providers (OpenAI, Anthropic, etc.) may be added in future versions.

---

### Can I use my own embeddings model?

Yes, configure in `config.yaml`:

```yaml
embeddings:
  model: sentence-transformers/all-MiniLM-L6-v2
```

---

### Is there an API I can use?

**Yes!** Ragged exposes a REST API at `http://localhost:8000`.

See [API Reference](./reference/api.md) for documentation.

---

### Can I run ragged in Docker?

Yes:
```bash
docker run -p 8000:8000 -v ~/.ragged:/data ragged/ragged
```

See [Docker Guide](./guides/docker.md) for details.

---

## Getting Help

### Where can I report bugs?

GitHub Issues: [https://github.com/ragged/ragged/issues](https://github.com/ragged/ragged/issues)

Please include:
- ragged version (`ragged --version`)
- Operating system
- Steps to reproduce
- Error messages

---

### Where can I ask questions?

- GitHub Discussions: [https://github.com/ragged/ragged/discussions](https://github.com/ragged/ragged/discussions)
- Documentation: This site

---

### How can I contribute?

See [Contributing Guide](./development/contributing.md).

---
