# Troubleshooting

Common issues and solutions for ragged.

---

## Available Guides

- **[Setup Issues](./setup-issues.md)** - Installation and configuration problems
  - Service connectivity (Ollama, ChromaDB)
  - Python environment issues
  - Platform-specific problems
  - Configuration errors

---

## Quick Troubleshooting

### Check Service Status

```bash
ragged health
```

This reveals 90% of common issues (Ollama not running, ChromaDB not connected).

### Validate Configuration

```bash
ragged validate --verbose
```

Catches configuration mistakes and provides fix suggestions.

### Get System Information

```bash
ragged env-info
```

Useful for bug reports and understanding your setup.

---

## Common Quick Fixes

### "ragged: command not found"

```bash
# Activate virtual environment
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows
```

### "Ollama connection failed"

```bash
# Mac: Launch Ollama app from Applications
# Linux/Windows: Run in separate terminal
ollama serve
```

### "ChromaDB connection failed"

```bash
# Docker users
docker compose ps         # Check status
docker compose up -d      # Start if needed
```

---

## Related Documentation

- [Setup Issues Guide](./setup-issues.md) - Detailed troubleshooting
- [CLI Essentials: Health Checks](../cli/essentials.md#1-ragged-health---check-system-status) - Service verification
- [CLI Advanced: Environment Info](../cli/advanced.md#environment-information-debug-and-report-issues) - Debug information
- [FAQ](../faq.md) - Common questions and answers

---

## Getting Help

If you can't solve your issue:

1. **Check the FAQ**: [Frequently Asked Questions](../faq.md)
2. **Search GitHub Issues**: [Existing issues](https://github.com/REPPL/ragged/issues)
3. **Ask on Discussions**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
4. **Report a bug**: [New issue](https://github.com/REPPL/ragged/issues/new)

**Include `ragged env-info` output** when reporting issues!
