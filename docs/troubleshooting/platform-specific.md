# Platform-Specific Troubleshooting

Resolve issues specific to Windows, macOS, and Linux.

---

## Windows Issues

### WSL 2 Problems

**Symptom:**
```
Error: WSL 2 installation is incomplete
```

**Solution:**
```powershell
# Install/update WSL
wsl --install

# Update to latest
wsl --update

# Set WSL 2 as default
wsl --set-default-version 2

# Restart Docker Desktop
```

---

### Docker Desktop Won't Start

**Symptom:**
Docker Desktop hangs on startup or shows errors.

**Solutions:**

1. **Enable virtualisation in BIOS:**
   - Restart computer
   - Enter BIOS (F2/F12/Del)
   - Enable Intel VT-x or AMD-V
   - Save and exit

2. **Disable conflicting software:**
   - VirtualBox
   - VMware
   - Windows Sandbox

3. **Reset Docker Desktop:**
   - Settings → Troubleshoot → Reset to factory defaults

4. **Reinstall:**
   ```powershell
   # Uninstall
   winget uninstall Docker.DockerDesktop

   # Reinstall
   winget install Docker.DockerDesktop
   ```

---

### PowerShell Execution Policy

**Symptom:**
```
Error: Running scripts is disabled on this system
```

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Windows Defender Blocking

**Symptom:**
Files quarantined or operations blocked.

**Solution:**
1. Open Windows Security
2. Virus & threat protection → Manage settings
3. Add exclusions:
   - `%USERPROFILE%\.ragged`
   - Docker Desktop installation folder

---

### Long Path Issues

**Symptom:**
```
Error: The filename or extension is too long
```

**Solution:**
```powershell
# Enable long paths (requires admin)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

---

### Windows Firewall

**Symptom:**
Cannot connect to services from other machines.

**Solution:**
```powershell
# Allow ragged ports
New-NetFirewallRule -DisplayName "Ragged" -Direction Inbound -LocalPort 8000,5173,11434 -Protocol TCP -Action Allow
```

---

## macOS Issues

### Gatekeeper Blocks Application

**Symptom:**
```
"Application" cannot be opened because it is from an unidentified developer
```

**Solution:**

Via System Settings:
1. System Settings → Privacy & Security
2. Click "Open Anyway" for blocked app

Via Terminal:
```bash
xattr -d com.apple.quarantine /Applications/Docker.app
xattr -d com.apple.quarantine /Applications/Ollama.app
```

---

### Full Disk Access Required

**Symptom:**
```
Error: Operation not permitted
```

**Solution:**
1. System Settings → Privacy & Security → Full Disk Access
2. Add Terminal.app (or your terminal emulator)
3. Restart terminal

---

### Rosetta 2 (Intel Emulation)

**Symptom:**
Errors about x86_64 binaries on Apple Silicon.

**Solution:**
```bash
# Install Rosetta 2
softwareupdate --install-rosetta

# Verify
/usr/bin/pgrep -q oahd && echo "Rosetta installed"
```

---

### Keychain Access

**Symptom:**
```
Error: Could not unlock keychain
```

**Solution:**
```bash
# Unlock keychain
security unlock-keychain ~/Library/Keychains/login.keychain-db
```

---

### macOS Firewall

**Symptom:**
Firewall prompts or blocked connections.

**Solution:**
1. System Settings → Network → Firewall → Options
2. Add ragged to allowed applications
3. Or temporarily disable for testing

---

### Docker Desktop Memory (Apple Silicon)

**Symptom:**
High memory usage or crashes on M1/M2/M3.

**Solution:**
1. Docker Desktop → Settings → Resources
2. Reduce memory allocation
3. Or use Docker's `--memory` flag:
   ```bash
   docker run --memory 4g ...
   ```

---

## Linux Issues

### Docker Permission Denied

**Symptom:**
```
Error: permission denied while trying to connect to the Docker daemon
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply immediately
newgrp docker

# Or log out and back in
```

---

### SELinux Blocking

**Symptom:**
Permission denied errors on Fedora/RHEL.

**Diagnosis:**
```bash
# Check SELinux status
getenforce

# Check audit log
sudo ausearch -m avc -ts recent
```

**Solutions:**

1. **Temporary (testing):**
   ```bash
   sudo setenforce 0
   ```

2. **Permanent fix:**
   ```bash
   # Allow container access
   sudo setsebool -P container_manage_cgroup on

   # Fix file contexts
   sudo chcon -Rt svirt_sandbox_file_t ~/.ragged
   ```

---

### AppArmor Issues (Ubuntu)

**Symptom:**
Docker operations blocked by AppArmor.

**Solution:**
```bash
# Check status
sudo aa-status

# Set to complain mode
sudo aa-complain /etc/apparmor.d/docker

# Or disable for docker
sudo ln -s /etc/apparmor.d/docker /etc/apparmor.d/disable/
sudo apparmor_parser -R /etc/apparmor.d/docker
```

---

### systemd Service Issues

**Symptom:**
Services fail to start or stay running.

**Diagnosis:**
```bash
# Check service status
sudo systemctl status ragged
sudo systemctl status docker
sudo systemctl status ollama

# View logs
sudo journalctl -u ragged -f
```

**Solutions:**

1. **Enable service:**
   ```bash
   sudo systemctl enable ragged
   sudo systemctl start ragged
   ```

2. **Reload after changes:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart ragged
   ```

---

### Firewall (UFW)

**Symptom:**
Cannot connect from other machines.

**Solution:**
```bash
# Allow ports
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp
sudo ufw allow 11434/tcp

# Check status
sudo ufw status
```

---

### Firewall (firewalld)

**Solution:**
```bash
# Allow ports
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

---

### Snap/Flatpak Conflicts

**Symptom:**
Conflicts between snap/flatpak Docker and native Docker.

**Solution:**
```bash
# Remove snap Docker
sudo snap remove docker

# Install native Docker
curl -fsSL https://get.docker.com | sh
```

---

### GPU Access (NVIDIA)

**Symptom:**
Ollama not using GPU on Linux.

**Solution:**
```bash
# Install NVIDIA drivers
sudo apt install nvidia-driver-535

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Verify
nvidia-smi
```

---

## Cross-Platform Issues

### Time Zone Problems

**Symptom:**
Timestamps appear incorrect.

**Solution:**
```bash
# Check system time
date

# Sync time
# Linux
sudo timedatectl set-ntp true

# macOS
sudo sntp -sS time.apple.com
```

---

### Locale Issues

**Symptom:**
```
Error: 'ascii' codec can't encode character
```

**Solution:**
```bash
# Set UTF-8 locale
export LC_ALL=en_GB.UTF-8
export LANG=en_GB.UTF-8

# Add to shell profile
echo 'export LC_ALL=en_GB.UTF-8' >> ~/.bashrc
```

---

### File System Case Sensitivity

**Symptom:**
Files not found due to case mismatch.

**Note:**
- Windows: Case-insensitive
- macOS: Case-insensitive (default)
- Linux: Case-sensitive

Ensure consistent casing in paths and imports.

---

## Related Documentation

- [Prerequisites](./prerequisites.md)
- [Permissions](./permissions.md)
- [Installation Guides](../installation/README.md)

---
