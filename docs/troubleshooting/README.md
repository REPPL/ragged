# Troubleshooting Guide

Comprehensive troubleshooting documentation for ragged installation and operation.

## Quick Diagnosis

Run the diagnostic tool first:

```bash
ragged diagnose
```

This automatically checks:
- System requirements
- Service health
- Network connectivity
- File permissions
- Resource availability

---

## Browse by Category

| Category | Common Issues |
|----------|---------------|
| [Prerequisites](./prerequisites.md) | Docker, Python, Ollama setup |
| [Network](./network.md) | Ports, firewalls, connectivity |
| [Permissions](./permissions.md) | File access, sudo, SELinux |
| [Resources](./resources.md) | Disk space, memory, CPU |
| [Services](./services.md) | Startup, crashes, timeouts |
| [Platform-Specific](./platform-specific.md) | Windows, macOS, Linux |

---

## Search by Error Message

See the [Error Message Index](./error-index.md) to find solutions by error text.

Common errors:
- ["Port already in use"](./network.md#port-already-in-use)
- ["Permission denied"](./permissions.md#permission-denied)
- ["Docker daemon not running"](./prerequisites.md#docker-not-running)
- ["Ollama connection refused"](./prerequisites.md#ollama-connection-refused)
- ["Out of memory"](./resources.md#out-of-memory)

---

## Emergency Recovery

If ragged is completely broken:

```bash
# 1. Stop everything
ragged stop

# 2. Run recovery
ragged recover

# 3. If that fails, reset configuration
ragged config reset

# 4. If still failing, reinstall
ragged install --repair
```

**Data is preserved during repair installation.**

---

## Getting Help

If these guides don't resolve your issue:

1. **Run diagnostics** and save output:
   ```bash
   ragged diagnose > diagnostics.txt
   ```

2. **Collect logs**:
   ```bash
   ragged logs --all > logs.txt
   ```

3. **Check FAQ**: [Frequently Asked Questions](../faq.md)

4. **Search issues**: [GitHub Issues](https://github.com/ragged/ragged/issues)

5. **Ask community**: [Discussions](https://github.com/ragged/ragged/discussions)

---

## Related Documentation

- [Installation Guides](../installation/README.md)
- [FAQ](../faq.md)
- [Video Tutorials](../videos/README.md)

---
