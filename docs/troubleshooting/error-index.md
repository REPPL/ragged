# Error Message Index

Find solutions by searching for your error message.

---

## How to Use

1. **Copy your error message** from the terminal
2. **Search this page** (Ctrl+F / Cmd+F)
3. **Click the link** to go to the solution

---

## Error Index

### A

| Error Message | Solution |
|---------------|----------|
| `Access denied` | [Permission Denied](./permissions.md#permission-denied-errors) |
| `Address already in use` | [Port Already in Use](./network.md#port-already-in-use) |
| `AppArmor blocks Docker` | [AppArmor Issues](./permissions.md#apparmor-issues-ubuntu) |
| `Authentication required` | [Proxy Authentication](./network.md#proxy-authentication) |

### C

| Error Message | Solution |
|---------------|----------|
| `Cannot allocate memory` | [Out of Memory](./resources.md#out-of-memory) |
| `Cannot connect to Docker daemon` | [Docker Not Running](./prerequisites.md#docker-not-running) |
| `Cannot create directory` | [Permission Denied](./permissions.md#cannot-create-directory) |
| `Cannot open file` | [Permission Denied](./permissions.md#permission-denied-errors) |
| `Cannot resolve host` | [DNS Issues](./network.md#dns-resolution-issues) |
| `ChromaDB connection failed` | [Services Not Starting](./services.md) |
| `Connection refused` | [Service Not Running](./network.md#port-already-in-use) |
| `Connection timed out` | [Connection Timeouts](./network.md#connection-timeouts) |

### D

| Error Message | Solution |
|---------------|----------|
| `Disk quota exceeded` | [Disk Quota](./permissions.md#disk-quota-exceeded) |
| `Docker daemon not running` | [Docker Not Running](./prerequisites.md#docker-not-running) |
| `Docker not found` | [Docker Not Installed](./prerequisites.md#docker-not-installed) |
| `Docker permission denied` | [Docker Permission](./prerequisites.md#docker-permission-denied) |

### E

| Error Message | Solution |
|---------------|----------|
| `EACCES permission denied` | [Permission Denied](./permissions.md#permission-denied-errors) |
| `EADDRINUSE` | [Port Already in Use](./network.md#port-already-in-use) |
| `ECONNREFUSED` | [Connection Refused](./network.md#port-already-in-use) |
| `ENOSPC` | [Disk Full](./resources.md#disk-full-during-installation) |

### F

| Error Message | Solution |
|---------------|----------|
| `Failed to start API server` | [Port Already in Use](./network.md#port-8000-api-server) |
| `Failed to start WebUI` | [Port Already in Use](./network.md#port-5173-webui) |
| `Firewall blocking` | [Firewall Issues](./network.md#firewall-blocking-connections) |

### G

| Error Message | Solution |
|---------------|----------|
| `Gatekeeper blocked` | [Gatekeeper Issues](./permissions.md#gatekeeper-issues-macos) |
| `GPU not detected` | [GPU Issues](./resources.md#gpu-not-detected) |

### H

| Error Message | Solution |
|---------------|----------|
| `Hardware virtualization required` | [Virtualisation Error](./prerequisites.md#docker-desktop-virtualisation-error) |

### I

| Error Message | Solution |
|---------------|----------|
| `Insufficient disk space` | [Disk Space](./resources.md#insufficient-disk-space) |
| `Invalid configuration` | [Configuration Issues](./services.md) |

### M

| Error Message | Solution |
|---------------|----------|
| `Model not found` | [Ollama Model Not Found](./prerequisites.md#ollama-model-not-found) |
| `Memory allocation failed` | [Out of Memory](./resources.md#out-of-memory) |

### N

| Error Message | Solution |
|---------------|----------|
| `Network unreachable` | [Network Issues](./network.md) |
| `No space left on device` | [Disk Full](./resources.md#disk-full-during-installation) |
| `Not a directory` | [Path Issues](./permissions.md) |

### O

| Error Message | Solution |
|---------------|----------|
| `Ollama connection refused` | [Ollama Issues](./prerequisites.md#ollama-connection-refused) |
| `Ollama not found` | [Ollama Not Installed](./prerequisites.md#ollama-not-installed) |
| `OOM killer` | [Out of Memory](./resources.md#out-of-memory) |
| `Operation not permitted` | [Permission Denied](./permissions.md#permission-denied-errors) |
| `Out of memory` | [Memory Issues](./resources.md#out-of-memory) |

### P

| Error Message | Solution |
|---------------|----------|
| `Permission denied` | [Permission Denied](./permissions.md#permission-denied-errors) |
| `pip not found` | [pip Not Found](./prerequisites.md#pip-not-found) |
| `Port already in use` | [Port Conflicts](./network.md#port-already-in-use) |
| `Proxy authentication required` | [Proxy Issues](./network.md#proxy-authentication) |
| `Python not found` | [Python Not Found](./prerequisites.md#python-not-found) |
| `Python version too old` | [Python Version](./prerequisites.md#python-version-too-old) |

### R

| Error Message | Solution |
|---------------|----------|
| `Read-only file system` | [Read-Only FS](./permissions.md#read-only-file-system) |
| `Resource temporarily unavailable` | [Resource Issues](./resources.md) |

### S

| Error Message | Solution |
|---------------|----------|
| `SELinux blocking` | [SELinux Issues](./permissions.md#selinux-issues-rhelfedora) |
| `Service failed to start` | [Service Issues](./services.md) |
| `SSL certificate error` | [SSL Issues](./network.md#ssltls-issues) |

### T

| Error Message | Solution |
|---------------|----------|
| `Timeout` | [Connection Timeouts](./network.md#connection-timeouts) |

### U

| Error Message | Solution |
|---------------|----------|
| `Unable to get local issuer certificate` | [SSL Issues](./network.md#certificate-errors) |
| `Unidentified developer` | [Gatekeeper](./permissions.md#gatekeeper-issues-macos) |

### V

| Error Message | Solution |
|---------------|----------|
| `Virtualization not enabled` | [Virtualisation](./prerequisites.md#docker-desktop-virtualisation-error) |

### W

| Error Message | Solution |
|---------------|----------|
| `WSL 2 error` | [WSL 2 Issues](./prerequisites.md#docker-desktop-wsl-2-error-windows) |

---

## Not Finding Your Error?

If your error isn't listed:

1. **Run diagnostics:** `ragged diagnose`
2. **Check logs:** `ragged logs --tail 50`
3. **Search GitHub issues:** [Open Issues](https://github.com/ragged/ragged/issues)
4. **Ask the community:** [Discussions](https://github.com/ragged/ragged/discussions)

---

## Related Documentation

- [Prerequisites](./prerequisites.md)
- [Network](./network.md)
- [Permissions](./permissions.md)
- [Resources](./resources.md)
- [Services](./services.md)
- [Platform-Specific](./platform-specific.md)

---
