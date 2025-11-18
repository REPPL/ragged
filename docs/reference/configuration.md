# Configuration Reference

**Status:** Coming in v0.3

Complete configuration reference documentation is planned for a future release.

## Available Now

For configuration information, please see:

- **[.env.example](../../.env.example)** - Example configuration file with all available settings
- **[CLI Command Reference - Environment Variables](./cli/command-reference.md#environment-variables)** - All RAGGED_* environment variables documented
- **[README.md Configuration](../../README.md#configuration)** - Basic configuration guide

## Configuration Options

Configuration is managed through environment variables. Create a `.env` file in the project root with your settings.

### Key Variables

See the CLI Command Reference for a complete list of environment variables including:
- `RAGGED_DATA_DIR` - Data directory location
- `RAGGED_LLM_MODEL` - Default LLM model
- `RAGGED_EMBEDDING_MODEL` - Embedding model selection
- `RAGGED_OLLAMA_BASE_URL` - Ollama service URL
- `RAGGED_CHROMA_URL` - ChromaDB URL
- `RAGGED_CHUNK_SIZE` - Document chunk size
- `RAGGED_CHUNK_OVERLAP` - Chunk overlap size

## What's Coming

The configuration reference will include:
- Complete specification of all settings
- Default values and valid ranges
- Configuration validation rules
- Advanced configuration examples
- Troubleshooting configuration issues

---

**Status:** Planned for v0.3
