# Network Troubleshooting

Resolve port conflicts, firewall issues, and connectivity problems.

---

## Port Already in Use

### Port 8000 (API Server)

**Symptom:**
```
Error: Failed to start API server
Port 8000 is already in use by process 12345 (node)
```

**Solution:**

**Find and stop the conflicting process:**

**Linux/macOS:**
```bash
# Find process
lsof -i :8000

# Output shows:
# COMMAND  PID  USER   FD   TYPE  DEVICE  SIZE/OFF  NODE  NAME
# node    12345  user  22u  IPv4  123456      0t0   TCP  *:8000 (LISTEN)

# Kill process
kill -9 12345
```

**Windows:**
```powershell
# Find process
netstat -ano | findstr :8000

# Output shows:
# TCP  0.0.0.0:8000  0.0.0.0:0  LISTENING  12345

# Kill process
taskkill /PID 12345 /F
```

**Or use alternative port:**
```bash
ragged config set server.port 8080
ragged restart
```

---

### Port 5173 (WebUI)

**Symptom:**
```
Error: Failed to start WebUI
Port 5173 is already in use
```

**Solution:**
```bash
# Find and kill process (same as above)
lsof -i :5173
kill -9 <PID>

# Or change port
ragged config set webui.port 5174
ragged restart
```

---

### Port 11434 (Ollama)

**Symptom:**
```
Error: Cannot connect to Ollama
Port 11434 is already in use
```

**Solution:**
```bash
# Stop existing Ollama
pkill ollama

# Restart Ollama service
ollama serve

# Or use different port
OLLAMA_HOST=127.0.0.1:11435 ollama serve
ragged config set ollama.port 11435
```

---

## Firewall Blocking Connections

### Windows Firewall

**Symptom:**
Cannot connect to ragged from other machines or browser.

**Solution:**
```powershell
# Allow ragged ports through firewall
New-NetFirewallRule -DisplayName "Ragged API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Ragged WebUI" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```

Or use Windows Security settings:
1. Open Windows Security
2. Firewall & network protection
3. Allow an app through firewall
4. Add ragged and Docker

---

### macOS Firewall

**Symptom:**
Firewall prompt appears or connections blocked.

**Solution:**
1. Open System Settings → Network → Firewall
2. Click "Options..."
3. Add ragged to allowed applications
4. Or disable firewall temporarily for testing

---

### Linux Firewall (UFW)

**Symptom:**
Cannot connect from other machines.

**Solution:**
```bash
# Allow ports
sudo ufw allow 8000/tcp comment "Ragged API"
sudo ufw allow 5173/tcp comment "Ragged WebUI"
sudo ufw allow 11434/tcp comment "Ollama"

# Verify
sudo ufw status
```

---

### Linux Firewall (firewalld)

**Solution:**
```bash
# Allow ports
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

---

## DNS Resolution Issues

### Cannot Resolve localhost

**Symptom:**
```
Error: Could not resolve host: localhost
```

**Solution:**

Check `/etc/hosts` (Linux/macOS) or `C:\Windows\System32\drivers\etc\hosts` (Windows):
```
127.0.0.1   localhost
::1         localhost
```

---

### IPv6 Issues

**Symptom:**
Services bind to IPv6 but you're connecting via IPv4.

**Solution:**
```bash
# Force IPv4
ragged config set server.bind "127.0.0.1"

# Or disable IPv6 binding
ragged config set server.ipv6 false
```

---

## Proxy Configuration

### Behind Corporate Proxy

**Symptom:**
```
Error: Connection timed out
```

**Solution:**

**Linux/macOS:**
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1

# Add to ~/.bashrc or ~/.zshrc for persistence
```

**Windows:**
```powershell
# Set system proxy
[Environment]::SetEnvironmentVariable("HTTP_PROXY", "http://proxy.company.com:8080", "User")
[Environment]::SetEnvironmentVariable("HTTPS_PROXY", "http://proxy.company.com:8080", "User")
```

**Docker proxy:**
```json
// ~/.docker/config.json
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.company.com:8080",
      "httpsProxy": "http://proxy.company.com:8080",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
```

---

### Proxy Authentication

**Symptom:**
```
Error: Proxy authentication required
```

**Solution:**
```bash
export HTTP_PROXY=http://username:password@proxy.company.com:8080
export HTTPS_PROXY=http://username:password@proxy.company.com:8080
```

---

## Connection Timeouts

### Slow Network

**Symptom:**
```
Error: Connection timed out after 30 seconds
```

**Solution:**
```bash
# Increase timeout
ragged config set network.timeout 120

# Or for installation
ragged install --timeout 300
```

---

### Docker Network Issues

**Symptom:**
Container cannot reach external services.

**Solution:**
```bash
# Restart Docker networking
docker network prune -f

# Check Docker DNS
docker run --rm busybox nslookup google.com

# Reset Docker networking
# Windows/macOS: Docker Desktop → Settings → Reset
# Linux:
sudo systemctl restart docker
```

---

## SSL/TLS Issues

### Certificate Errors

**Symptom:**
```
Error: SSL certificate problem: unable to get local issuer certificate
```

**Solution:**

**Corporate environment with SSL inspection:**
```bash
# Add corporate CA certificate
# Linux
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain corporate-ca.crt

# Windows
certutil -addstore -f "ROOT" corporate-ca.crt
```

**Temporary bypass (not recommended for production):**
```bash
ragged config set network.verify_ssl false
```

---

## Testing Connectivity

### Quick Checks

```bash
# Test API server
curl http://localhost:8000/health

# Test WebUI
curl http://localhost:5173

# Test Ollama
curl http://localhost:11434/api/version

# Test Docker
docker info

# Test internet
curl https://pypi.org/simple/
```

---

## Related Documentation

- [Permissions Troubleshooting](./permissions.md)
- [Prerequisites Troubleshooting](./prerequisites.md)
- [Platform-Specific Issues](./platform-specific.md)

---
