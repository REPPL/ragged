# CLI Command Reference

Complete technical specification for all ragged CLI commands.

---

## Synopsis

```
ragged [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

## Global Options

These options can be used with any command:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | flag | - | Show version and exit |
| `--verbose`, `-v` | flag | false | Enable verbose logging (INFO level) |
| `--debug` | flag | false | Enable debug logging (DEBUG level) |
| `--quiet`, `-q` | flag | false | Suppress all non-essential output |
| `--help` | flag | - | Show help message and exit |

**Note:** `--debug` takes precedence over `--verbose`, which takes precedence over `--quiet`.

---

## Commands

Commands are listed alphabetically. Use `ragged COMMAND --help` for detailed help on any command.

### add

Ingest document(s) into the system.

**Synopsis:**
```
ragged add PATH [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PATH` | path | yes | File or directory to ingest |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | text | auto-detect | Force document format (pdf, txt, md, html) |
| `--recursive` / `--no-recursive` | flag | true | Scan subdirectories |
| `--max-depth` | integer | unlimited | Maximum directory depth |
| `--fail-fast` | flag | false | Stop on first error instead of continuing |

**Behaviour:**

- Single file: Checks for duplicates, prompts for overwrite if exists
- Directory: Batch processing with automatic duplicate skipping
- Supported formats: PDF, TXT, MD, HTML
- Progress indicators shown during processing

**Exit Codes:**

- `0`: Success
- `1`: Ingestion failed or user cancelled

**Examples:**

```bash
ragged add document.pdf
ragged add /path/to/folder --recursive
ragged add folder --max-depth 2 --fail-fast
ragged add webpage.html --format html
```

---

### cache

Manage caches, temporary files, and system cleanup.

**Synopsis:**
```
ragged cache SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### cache info

Show cache statistics and sizes.

**Synopsis:**
```
ragged cache info [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | choice | table | Output format (table, json, yaml) |

#### cache clear

Clear caches to free disk space.

**Synopsis:**
```
ragged cache clear [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | flag | false | Clear all caches (query history, embeddings, logs) |
| `--query-history` | flag | false | Clear query history only |
| `--embeddings` | flag | false | Clear embeddings cache only |
| `--logs` | flag | false | Clear log files only |
| `--yes`, `-y` | flag | false | Skip confirmation prompt |

**Exit Codes:**

- `0`: Success
- `1`: Clear operation failed

---

### clear

Clear all ingested documents from the database.

**Synopsis:**
```
ragged clear [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force`, `-f` | flag | false | Skip confirmation |

**Exit Codes:**

- `0`: Success, database cleared
- `1`: Operation failed

**Warning:** This operation cannot be undone. All document chunks and embeddings will be deleted.

---

### completion

Install shell completion for ragged CLI.

**Synopsis:**
```
ragged completion [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--shell`, `-s` | choice | auto-detect | Shell type (bash, zsh, fish) |
| `--install`, `-i` | flag | false | Automatically install completion |
| `--show` | flag | false | Show completion script without installing |

**Supported Shells:**

- Bash
- Zsh
- Fish

**Exit Codes:**

- `0`: Success
- `1`: Shell not detected or installation failed

**Examples:**

```bash
ragged completion --show --shell bash >> ~/.bashrc
ragged completion --install
```

---

### config

Manage configuration settings.

**Synopsis:**
```
ragged config SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### config show

Display current configuration.

**Synopsis:**
```
ragged config show
```

**Output:** Table showing all configuration settings including models, chunk sizes, service URLs.

#### config set

Set a configuration value (not yet implemented).

**Synopsis:**
```
ragged config set KEY VALUE
```

**Note:** Currently, configuration must be set via `.env` file.

#### config set-model

Set the LLM model for generation.

**Synopsis:**
```
ragged config set-model [MODEL_NAME] [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `MODEL_NAME` | text | no | Model name (e.g., llama3.2:latest) |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--auto` | flag | false | Automatically select recommended model |

**Behaviour:**

- If no model specified: Interactive selection menu
- If `--auto`: Selects recommended model automatically
- If model specified: Validates and sets model

#### config list-models

List all available Ollama models with RAG suitability scores.

**Synopsis:**
```
ragged config list-models
```

**Output:** Table with model names, families, context lengths, and suitability scores (0-100).

**Exit Codes:**

- `0`: Success
- `1`: Configuration error or Ollama unavailable

---

### env-info

Show environment information for bug reports.

**Synopsis:**
```
ragged env-info [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | choice | text | Output format (text, json, markdown) |
| `--copy`, `-c` | flag | false | Copy output to clipboard (requires pyperclip) |

**Information Displayed:**

- Ragged version
- Python version and implementation
- System information (OS, platform, processor)
- Key package versions
- Configuration settings (non-sensitive)
- Ollama status and available models
- Storage space information

**Exit Codes:**

- `0`: Success

**Examples:**

```bash
ragged env-info
ragged env-info --format markdown > issue.md
ragged env-info --copy
```

---

### export

Export and import data for backup and migration.

**Synopsis:**
```
ragged export SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### export backup

Create a backup of all data.

**Synopsis:**
```
ragged export backup [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output`, `-o` | path | auto-generated | Output file path |
| `--include-embeddings` | flag | true | Include embeddings in export |
| `--include-config` | flag | true | Include configuration in export |
| `--compress`, `-z` | flag | false | Compress output with gzip |

**Output Format:** JSON file containing documents, metadata, embeddings (optional), and configuration.

**Default Filename:** `ragged_backup_YYYYMMDD_HHMMSS.json` (or `.json.gz` if compressed)

#### export import

Import data from backup file (placeholder for future implementation).

**Exit Codes:**

- `0`: Success
- `1`: Export/import failed

**Examples:**

```bash
ragged export backup
ragged export backup --output backup.json --compress
ragged export backup --output backup.json.gz -z
```

---

### health

Check health of all services.

**Synopsis:**
```
ragged health
```

**Services Checked:**

- Ollama: LLM generation service
- ChromaDB: Vector store database

**Output:** Status of each service with descriptive messages.

**Exit Codes:**

- `0`: All services healthy
- `1`: One or more services unavailable

**Examples:**

```bash
ragged health
```

---

### history

Manage query history.

**Synopsis:**
```
ragged history SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### history list

List query history with optional filtering.

**Synopsis:**
```
ragged history list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit`, `-n` | integer | all | Maximum number of entries to show |
| `--search`, `-s` | text | - | Search term to filter queries |
| `--format`, `-f` | choice | text | Output format (text, json, table, csv, markdown, yaml) |

#### history show

Show full details of a specific query.

**Synopsis:**
```
ragged history show QUERY_ID [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY_ID` | integer | yes | Query ID from history list |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | choice | text | Output format (text, json) |

#### history replay

Replay a query from history.

**Synopsis:**
```
ragged history replay QUERY_ID [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY_ID` | integer | yes | Query ID to replay |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--top-k`, `-k` | integer | original | Override number of results |

#### history clear

Clear all query history.

**Synopsis:**
```
ragged history clear [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--yes`, `-y` | flag | false | Skip confirmation prompt |

#### history export

Export query history to JSON file.

**Synopsis:**
```
ragged history export OUTPUT_FILE
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `OUTPUT_FILE` | path | yes | Path to output JSON file |

**Exit Codes:**

- `0`: Success
- `1`: Operation failed or query not found

**Examples:**

```bash
ragged history list --limit 10
ragged history list --search "machine learning"
ragged history show 5
ragged history replay 5 --top-k 10
ragged history clear --yes
ragged history export queries.json
```

---

### list

List all ingested documents.

**Synopsis:**
```
ragged list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | choice | table | Output format (table, json, csv, markdown, yaml) |

**Output:** Collection information including name, total chunks.

**Exit Codes:**

- `0`: Success
- `1`: List operation failed

**Examples:**

```bash
ragged list
ragged list --format json
ragged list --format csv > documents.csv
```

---

### metadata

Manage document metadata.

**Synopsis:**
```
ragged metadata SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### metadata list

List all documents with their metadata.

**Synopsis:**
```
ragged metadata list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit`, `-n` | integer | 100 | Maximum number of documents to list |
| `--format`, `-f` | choice | table | Output format (table, json, csv, markdown, yaml) |

#### metadata show

Show metadata for a specific document.

**Synopsis:**
```
ragged metadata show DOCUMENT_PATH [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `DOCUMENT_PATH` | text | yes | Path of document to show |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | choice | text | Output format (text, json) |

#### metadata update

Update metadata for a document.

**Synopsis:**
```
ragged metadata update DOCUMENT_PATH [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `DOCUMENT_PATH` | text | yes | Path of document to update |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--set`, `-s` | text | - | Set metadata (key=value), can be used multiple times |
| `--delete`, `-d` | text | - | Delete metadata key, can be used multiple times |

**Behaviour:** Updates metadata for all chunks of the specified document.

#### metadata search

Search documents by metadata.

**Synopsis:**
```
ragged metadata search [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--filter`, `-f` | text | - | Filter by metadata (key=value), can be used multiple times |
| `--format`, `-o` | choice | table | Output format (table, json, csv, markdown, yaml) |

**Exit Codes:**

- `0`: Success
- `1`: Operation failed or document not found

**Examples:**

```bash
ragged metadata list --limit 50
ragged metadata show document.pdf
ragged metadata update document.pdf --set category=research --set priority=high
ragged metadata update document.pdf --delete old_key
ragged metadata search --filter category=research --filter priority=high
```

---

### query

Ask a question and get an answer from your documents.

**Synopsis:**
```
ragged query QUERY [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY` | text | yes | Question to ask |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--k`, `-k` | integer | 5 | Number of chunks to retrieve |
| `--show-sources` | flag | false | Show retrieved source chunks |
| `--format`, `-f` | choice | text | Output format (text, json) |
| `--no-history` | flag | false | Don't save this query to history |

**Behaviour:**

- Uses hybrid retrieval (vector + BM25) by default
- Generates answer using configured LLM
- Automatically saves to history (unless `--no-history`)
- Includes IEEE-style references in answer

**Output Formats:**

- `text`: Human-readable with formatting
- `json`: Structured data with query, answer, sources, retrieval metadata

**Exit Codes:**

- `0`: Success
- `1`: Query failed, no documents found, or Ollama unavailable

**Examples:**

```bash
ragged query "What is the main topic?"
ragged query "Explain the process" --show-sources
ragged query "Summary?" --k 10 --format json > result.json
ragged query "Quick check" --no-history
```

---

### search

Advanced search across documents with filtering.

**Synopsis:**
```
ragged search [QUERY] [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY` | text | no* | Semantic search query |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--path`, `-p` | text | - | Filter by document path (supports wildcards) |
| `--metadata`, `-m` | text | - | Filter by metadata (key=value), can be used multiple times |
| `--min-score`, `-s` | float | - | Minimum relevance score (0.0-1.0) |
| `--limit`, `-n` | integer | 10 | Maximum number of results |
| `--show-content`, `-c` | flag | false | Show chunk content preview |
| `--format`, `-f` | choice | text | Output format (text, table, json, csv, markdown, yaml) |

**Note:** At least one of `QUERY`, `--path`, or `--metadata` must be provided.

**Exit Codes:**

- `0`: Success
- `1`: Search failed or no criteria provided

**Examples:**

```bash
ragged search "machine learning concepts"
ragged search "neural networks" --path research.pdf
ragged search "AI" --metadata category=research --metadata priority=high
ragged search "transformers" --show-content --min-score 0.7
ragged search --path document.pdf --limit 100
ragged search "topic" --format json > results.json
```

---

### validate

Validate ragged configuration and environment.

**Synopsis:**
```
ragged validate [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--fix`, `-f` | flag | false | Attempt to automatically fix issues |
| `--verbose`, `-v` | flag | false | Show detailed validation information |

**Checks Performed:**

- Configuration file syntax and required settings
- Directory permissions and accessibility
- Ollama service connectivity
- ChromaDB configuration
- Embedding model availability

**Exit Codes:**

- `0`: Validation passed (all checks successful)
- `1`: Validation failed (critical errors found)

**Examples:**

```bash
ragged validate
ragged validate --fix
ragged validate --verbose
```

---

## Environment Variables

These environment variables affect CLI behaviour:

| Variable | Description | Default |
|----------|-------------|---------|
| `RAGGED_DATA_DIR` | Data directory location | `~/.ragged/data` |
| `RAGGED_LOG_LEVEL` | Logging level | `WARNING` |
| `RAGGED_LLM_MODEL` | Default LLM model | `llama3.2:latest` |
| `RAGGED_EMBEDDING_MODEL` | Embedding model | `nomic-embed-text` |
| `RAGGED_OLLAMA_BASE_URL` | Ollama service URL | `http://localhost:11434` |
| `RAGGED_CHROMA_URL` | ChromaDB URL | `http://localhost:8000` |
| `RAGGED_CHUNK_SIZE` | Document chunk size | `1000` |
| `RAGGED_CHUNK_OVERLAP` | Chunk overlap size | `200` |

See `.env.example` for full list of configuration options.

---

## Exit Codes

Standard exit codes used across all commands:

| Code | Meaning |
|------|---------|
| `0` | Success - command completed successfully |
| `1` | Error - command failed or invalid input |
| `2` | Misuse - incorrect command usage (handled by Click) |

---

## Output Formats

Many commands support multiple output formats via `--format` option:

| Format | Description | Use Case |
|--------|-------------|----------|
| `text` | Plain text, human-readable | Interactive use, piping |
| `table` | Formatted tables with borders | Interactive viewing |
| `json` | Structured JSON | Programmatic access, APIs |
| `csv` | Comma-separated values | Spreadsheet import |
| `markdown` | Markdown tables | Documentation, GitHub |
| `yaml` | YAML format | Configuration, readability |

---

## Tips

### Verbosity Control

```bash
# Quiet mode - only errors
ragged add document.pdf --quiet

# Normal mode - standard output
ragged add document.pdf

# Verbose mode - detailed progress
ragged add document.pdf --verbose

# Debug mode - full logging
ragged add document.pdf --debug
```

### Piping and Scripting

```bash
# Export data
ragged list --format json > documents.json
ragged metadata list --format csv > metadata.csv

# Chain commands
ragged query "topic" --format json | jq '.answer'

# Batch operations
for file in *.pdf; do
    ragged add "$file"
done
```

### Performance

```bash
# Faster folder ingestion (no recursion)
ragged add /folder --no-recursive

# Limit retrieval for faster responses
ragged query "question" --k 3

# Clear caches to free space
ragged cache clear --all --yes
```

---

## Related Documentation

- [CLI Features Guide](../../guides/cli/cli-features.md) - Comprehensive tutorial with examples
- [Getting Started Tutorial](../../tutorials/getting-started.md) - First steps with ragged
- [Configuration Reference](../configuration.md) - Detailed configuration options

---

