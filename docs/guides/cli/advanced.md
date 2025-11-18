# CLI Advanced Guide: Power User Features

**What you'll learn**: System maintenance, backups, validation, shell completion, and advanced configuration for power users.

**Prerequisites**:
- Completed [CLI Essentials](./essentials.md) and [CLI Intermediate](./intermediate.md)
- Comfortable with terminal/shell concepts
- Have a production or heavy-use ragged setup

**Reading time**: 15-20 minutes

---

## Who Needs Advanced Features?

Advanced features are for:
- **Power users** running ragged daily with large collections
- **System administrators** maintaining ragged for teams
- **Developers** integrating ragged into workflows
- **Users** who want maximum performance and control

If you're casually using ragged for 10-50 documents, you probably don't need these features yet.

---

## Cache Management: Performance and Disk Space

**What is caching?** Storing frequently used data to avoid recomputing it.

**ragged caches**:
- Query embeddings (your questions converted to vectors)
- Model outputs (some AI responses)
- Temporary processing files

**Why manage cache?**
- Free up disk space
- Clear stale data
- Troubleshoot performance issues

---

### View cache information

```bash
ragged cache info
```

**Output**:
```
Cache Information:

Query Cache:
  Location: ./ragged_data/cache/queries/
  Size: 15.8 MB
  Entries: 247
  Oldest entry: 2025-10-15
  Newest entry: 2025-11-18

Embedding Cache:
  Location: ./ragged_data/cache/embeddings/
  Size: 8.2 MB
  Entries: 1,453
  Hit rate: 73.4% (saves re-computation)

Temporary Files:
  Location: ./ragged_data/tmp/
  Size: 2.1 MB
  Files: 12

Total cache size: 26.1 MB
```

---

### Clear specific caches

**Clear query cache**:
```bash
ragged cache clear --query-cache
```

Removes cached query embeddings. Next queries will recompute (slightly slower).

---

**Clear embedding cache**:
```bash
ragged cache clear --embedding-cache
```

Removes cached document embeddings. Document re-processing will be needed if you re-add them.

---

**Clear temporary files**:
```bash
ragged cache clear --temp
```

Removes temporary processing files (safe to delete).

---

**Clear all caches**:
```bash
ragged cache clear --all
```

**Warning**: This removes all cached data. Queries might be slightly slower until caches rebuild.

---

### Clear old entries

**Remove cache entries older than 30 days**:
```bash
ragged cache clear --older-than 30d
```

**Supported units**: `d` (days), `w` (weeks), `m` (months)

**Examples**:
```bash
ragged cache clear --older-than 7d   # Older than 1 week
ragged cache clear --older-than 2w   # Older than 2 weeks
ragged cache clear --older-than 3m   # Older than 3 months
```

---

### Cache best practices

**1. Clear cache when troubleshooting**

If you get unexpected results or errors:
```bash
ragged cache clear --all
# Then try your operation again
```

Stale cache entries can sometimes cause issues.

---

**2. Periodic cleanup for long-running setups**

If you use ragged heavily for months:
```bash
# Monthly cleanup
ragged cache clear --older-than 30d
```

Prevents cache from growing indefinitely.

---

**3. Clear cache before major upgrades**

Before upgrading ragged to a new version:
```bash
ragged cache clear --all
```

Ensures compatibility with new cache formats.

---

## Export and Backup: Protect Your Data

**What gets backed up**:
- All document chunks
- All embeddings
- All metadata
- Configuration
- Indices

**What doesn't get backed up**:
- Original documents (ragged doesn't store them, only processes them)
- Query history (optional, can be backed up separately)

---

### Create a backup

```bash
ragged export backup
```

**Output**:
```
Creating backup...
✓ Exporting documents (42 files)
✓ Exporting embeddings (1,247 chunks)
✓ Exporting metadata
✓ Exporting configuration

Backup saved to: ragged_backup_2025-11-18_14-32-18.json
Size: 124.7 MB
```

---

### Custom backup location and compression

**Specify output file**:
```bash
ragged export backup --output my-backup.json
```

---

**Compress backup** (recommended for large collections):
```bash
ragged export backup --output backup.json.gz --compress
```

**Compression ratio**: Typically 70-80% smaller (124MB → 25MB).

---

**Include query history**:
```bash
ragged export backup --include-history
```

Adds your query history to the backup (normally excluded).

---

### Verify backup integrity

```bash
ragged export backup --output backup.json --verify
```

After creating backup, ragged verifies:
- File is readable
- JSON structure is valid
- All required fields present
- Checksums match

---

### Backup strategies

**1. Regular automated backups**

Create a cron job (Linux/Mac) or scheduled task (Windows):

```bash
#!/bin/bash
# backup-ragged.sh

DATE=$(date +%Y-%m-%d)
ragged export backup --output "/backups/ragged-$DATE.json.gz" --compress

# Keep only last 30 days
find /backups/ragged-*.json.gz -mtime +30 -delete
```

**Cron entry** (daily at 2 AM):
```
0 2 * * * /path/to/backup-ragged.sh
```

---

**2. Before major changes**

Always backup before:
- Upgrading ragged
- Bulk deletions (`ragged clear --all`)
- Configuration changes
- Moving data directories

```bash
ragged export backup --output pre-upgrade-backup.json.gz --compress
```

---

**3. Off-site backups**

For critical collections, store backups off-site:

```bash
# Backup and upload to cloud storage
ragged export backup --output backup.json.gz --compress
rsync backup.json.gz user@remote-server:/backups/
# Or use cloud CLI tools (aws s3 cp, gcloud storage cp, etc.)
```

---

### Restore from backup (future feature)

**Note**: Import functionality is planned for v0.2.9.

**Future usage**:
```bash
ragged import backup.json.gz
```

**Current workaround**:
1. Save your `.env` configuration
2. Delete `ragged_data/` directory
3. Reinstall ragged
4. Re-add all documents manually

**Why backup is still valuable**: Backup file documents what you had, even if import isn't available yet.

---

## Configuration Validation: Catch Issues Early

**Problem**: Configuration mistakes cause cryptic errors later.

**Solution**: Validate before running.

---

### Basic validation

```bash
ragged validate
```

**Output (all good)**:
```
Validating configuration...

✓ Configuration file exists (.env)
✓ All required variables set
✓ Ollama URL is valid
✓ Ollama is reachable
✓ Ollama has required model: llama3.2:3b
✓ ChromaDB settings valid
✓ ChromaDB is reachable
✓ Data directory exists and is writable
✓ Embedding model configured correctly
✓ Chunk settings are valid
✓ No deprecated settings found

Configuration is valid!
No issues found.
```

---

**Output (issues found)**:
```
Validating configuration...

✓ Configuration file exists
✗ OLLAMA_MODEL not set (required)
⚠ CHUNK_SIZE is 5000 (recommended max: 2000)
✗ Data directory doesn't exist: /invalid/path/ragged_data
✗ ChromaDB connection failed: Connection refused

Issues found:
  Errors: 3 (must fix)
  Warnings: 1 (should review)

Run 'ragged validate --fix' to attempt automatic fixes.
```

---

### Auto-fix common issues

```bash
ragged validate --fix
```

**What gets auto-fixed**:
- Missing directories are created
- Default values set for required variables
- Permissions corrected on data directory
- Deprecated settings migrated to new format

**What isn't auto-fixed** (requires manual intervention):
- Service connectivity issues (Ollama not running)
- Invalid URLs or model names
- Insufficient disk space

---

### Verbose validation

```bash
ragged validate --verbose
```

**Output**:
```
Validating configuration...

[CHECK] .env file exists
  Location: /Users/you/ragged/.env
  Status: ✓ Found
  Size: 1.2 KB

[CHECK] Required variables
  OLLAMA_BASE_URL: ✓ Set (http://localhost:11434)
  OLLAMA_MODEL: ✓ Set (llama3.2:3b)
  EMBEDDING_MODEL: ✓ Set (nomic-embed-text)
  CHROMA_HOST: ✓ Set (localhost)
  CHROMA_PORT: ✓ Set (8000)
  DATA_DIR: ✓ Set (./ragged_data)

[CHECK] Ollama connectivity
  Testing connection to http://localhost:11434...
  Status: ✓ Connected
  Response time: 23ms

[CHECK] Ollama model availability
  Checking for model: llama3.2:3b
  Status: ✓ Found
  Model size: 2.0GB
  Model family: llama

[CHECK] ChromaDB connectivity
  Testing connection to localhost:8000...
  Status: ✓ Connected
  Response time: 12ms
  Collections: 1

[CHECK] Data directory
  Path: ./ragged_data
  Status: ✓ Exists
  Writable: ✓ Yes
  Free space: 458.2 GB
  Current usage: 124.7 MB

All checks passed!
```

---

### Validation best practices

**1. Validate after setup**

After initial installation:
```bash
ragged validate --verbose
```

Ensures everything is configured correctly before adding documents.

---

**2. Validate after configuration changes**

After editing `.env`:
```bash
ragged validate
```

Catch mistakes immediately.

---

**3. Validate when troubleshooting**

If ragged isn't working:
```bash
ragged validate --verbose
```

Often reveals the root cause.

---

**4. Include in deployment scripts**

For automated deployments:
```bash
#!/bin/bash
ragged validate || exit 1
# Continue with deployment if validation passes
```

---

## Environment Information: Debug and Report Issues

**Purpose**: Gather system information for troubleshooting and bug reports.

---

### Basic environment info

```bash
ragged env-info
```

**Output**:
```
ragged Environment Information:

ragged:
  Version: 0.2.8
  Installation: /Users/you/ragged
  Configuration: .env
  Python: 3.12.0

System:
  OS: macOS 13.6.1
  Architecture: arm64 (Apple Silicon)
  CPU: Apple M2 (8 cores)
  RAM: 16.0 GB
  Disk space: 458.2 GB free

Ollama:
  Status: Running
  Version: 0.1.17
  Models:
    - llama3.2:1b (1.3 GB)
    - llama3.2:3b (2.0 GB)
    - llama3.2:8b (4.7 GB)

ChromaDB:
  Status: Running
  Host: localhost:8000
  Collections: 1
  Total chunks: 1,247

Dependencies:
  sentence-transformers: 2.2.2
  chromadb: 0.4.18
  ollama: 0.1.5
  [12 other packages]
```

---

### Markdown format (for GitHub issues)

```bash
ragged env-info --format markdown
```

**Output** (ready to paste in GitHub issue):
```markdown
## Environment Information

**ragged version**: 0.2.8
**Python version**: 3.12.0
**OS**: macOS 13.6.1 (arm64)
**CPU**: Apple M2 (8 cores)
**RAM**: 16 GB

**Ollama**: Running (version 0.1.17)
**ChromaDB**: Running (localhost:8000)

**Installed models**:
- llama3.2:3b (2.0 GB)

**Collection stats**:
- 42 documents
- 1,247 chunks
```

---

### Copy to clipboard

```bash
ragged env-info --copy
```

Automatically copies output to clipboard (requires `pbcopy` on Mac, `xclip` on Linux, or `clip` on Windows).

---

### JSON format (for automation)

```bash
ragged env-info --format json > env.json
```

**Use cases**:
- Automated monitoring
- System inventory
- Pre-deployment checks

---

### When to use env-info

✅ **When reporting bugs**: Include `ragged env-info --format markdown` output in GitHub issues

✅ **When asking for help**: Share env-info with supporters

✅ **Before major changes**: Document your working configuration

✅ **For system inventory**: Track ragged deployments across multiple machines

---

## Shell Completion: Faster Command Entry

**Problem**: Typing long commands is slow and error-prone.

**Solution**: Tab completion for bash, zsh, and fish shells.

---

### Install completion

**Auto-detect shell and install**:
```bash
ragged completion --install
```

**Output**:
```
Detected shell: zsh
Installing completion for zsh...
✓ Created completion file: ~/.zsh/completions/_ragged
✓ Updated ~/.zshrc

Restart your shell or run: source ~/.zshrc
```

---

**Manual installation for specific shell**:
```bash
# Bash
ragged completion --shell bash --install

# Zsh
ragged completion --shell zsh --install

# Fish
ragged completion --shell fish --install
```

---

### Show completion script (don't install)

```bash
ragged completion --shell bash --show
```

Displays the completion script without installing. Useful for custom installations.

---

### Using completion

After installation, press `Tab` for suggestions:

```bash
ragged [Tab]
# Shows: add, query, list, clear, config, health, metadata, search, history, export, cache, validate, env-info, completion

ragged m[Tab]
# Autocompletes to: ragged metadata

ragged metadata [Tab]
# Shows: update, show, list, search

ragged query --[Tab]
# Shows: --k, --min-score, --path, --metadata, --format, --stream, --interactive
```

---

### Completion features

**Command completion**:
```bash
ragged qu[Tab]  →  ragged query
```

**Subcommand completion**:
```bash
ragged metadata sh[Tab]  →  ragged metadata show
```

**Option completion**:
```bash
ragged query --fo[Tab]  →  ragged query --format
```

**File path completion**:
```bash
ragged add ~/Doc[Tab]  →  ragged add ~/Documents/
```

---

### Benefits

- **Speed**: 50% faster command entry
- **Accuracy**: No typos in command names
- **Discovery**: See available options without checking docs
- **Professional**: Feels like native system commands

---

## Advanced Configuration Techniques

### Multiple ragged installations

**Use case**: Different collections for different projects.

**Setup**:
```bash
# Project 1
cd ~/projects/research
git clone https://github.com/REPPL/ragged.git ragged-research
cd ragged-research
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# Configure .env for this project

# Project 2
cd ~/projects/work
git clone https://github.com/REPPL/ragged.git ragged-work
cd ragged-work
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# Configure .env for this project
```

Each installation is independent with separate:
- Document collections
- Configurations
- Data directories

---

### Remote Ollama

**Use case**: Run Ollama on a powerful server, access from lightweight client.

**Server (192.168.1.100)**:
```bash
# Run Ollama with network binding
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Client (.env)**:
```
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

**Benefit**: Use large models (70B) without needing powerful local hardware.

**Security note**: Only do this on trusted networks. Ollama has no built-in authentication.

---

### Custom embedding models

**Use case**: You want multilingual support or domain-specific embeddings.

**Change model in .env**:
```
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

**Re-embed existing documents**:
```bash
# Remove old embeddings
ragged cache clear --embedding-cache

# Re-add documents (will use new model)
ragged add ./documents/ --force
```

**Trade-offs**:
- Larger models = better quality but slower and more storage
- Multilingual models = work across languages but slightly worse for English
- Domain-specific models = better for specific fields (legal, medical) but worse for general use

---

### Performance tuning

**Increase chunk size** (fewer chunks, faster search):
```
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
```

**Trade-off**: Less precise retrieval.

---

**Decrease chunk size** (more chunks, more precise):
```
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```

**Trade-off**: Slower search, more storage.

---

**Adjust generation parameters** (in .env):
```
GENERATION_TEMPERATURE=0.1  # More deterministic (recommended for factual)
GENERATION_MAX_TOKENS=2000  # Longer answers allowed
```

---

## Troubleshooting Advanced Issues

### Performance degradation over time

**Symptoms**: Queries that used to take 5 seconds now take 30 seconds.

**Diagnoses**:
1. **Check collection size**:
   ```bash
   ragged list --stats
   ```
   Very large collections (10,000+ documents) slow down search.

2. **Check cache**:
   ```bash
   ragged cache info
   ```
   Cache over 500MB might slow things down.

3. **Check disk space**:
   ```bash
   ragged env-info
   ```
   Low disk space affects performance.

**Solutions**:
- Clear old cache: `ragged cache clear --older-than 30d`
- Remove unused documents: `ragged clear old-docs`
- Split collection into multiple focused collections

---

### Inconsistent results

**Symptoms**: Same query gives different answers each time.

**Causes**:
1. Temperature too high
2. Different chunks retrieved each time
3. Stale cache

**Solutions**:
```bash
# Lower temperature (more deterministic)
ragged config --set GENERATION_TEMPERATURE=0.0

# Clear cache
ragged cache clear --all

# Verify configuration
ragged validate --verbose
```

---

### Memory issues

**Symptoms**: Out of memory errors, system freezing.

**Solutions**:
1. **Use smaller model**:
   ```bash
   ollama pull llama3.2:1b
   ragged config --set OLLAMA_MODEL=llama3.2:1b
   ```

2. **Reduce chunk retrieval**:
   ```bash
   ragged query "question" --k 3  # Instead of default 5
   ```

3. **Add swap space** (Linux):
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## Related Documentation

- [CLI Essentials](./essentials.md) - Core commands and basic usage
- [CLI Intermediate](./intermediate.md) - Metadata and advanced search
- [Personal Notes Guide](../use-cases/personal-notes.md) - Personal knowledge management workflows
- [Research Papers Guide](../use-cases/research-papers.md) - Academic literature workflows
- [Architecture Overview](../../explanation/architecture-overview.md) - Understanding ragged's internals
- [Contributing Guide](../../CONTRIBUTING.md) - Help improve ragged
- [API Reference](../../reference/api/README.md) - Programmatic usage (v0.3+)

---

## Quick Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `ragged cache info` | View cache stats | `ragged cache info` |
| `ragged cache clear` | Clear caches | `ragged cache clear --all` |
| `ragged export backup` | Create backup | `ragged export backup --compress` |
| `ragged validate` | Check configuration | `ragged validate --verbose` |
| `ragged env-info` | System information | `ragged env-info --format markdown` |
| `ragged completion` | Shell completion | `ragged completion --install` |

---

**You're now a ragged power user!** You have the tools to maintain, optimise, and troubleshoot ragged for production use. Use these features to build robust, long-term RAG workflows.

Happy power-using! ⚡
