# Permission Troubleshooting

Resolve file access, ownership, and security permission issues.

---

## Permission Denied Errors

### Cannot Create Directory

**Symptom:**
```
Error: Permission denied: '/Users/username/.ragged/'
```

**Cause:**
- Directory owned by root (installed with sudo)
- Parent directory not writable
- Disk quota exceeded

**Solution:**

**Fix ownership (Linux/macOS):**
```bash
# Take ownership of ragged directory
sudo chown -R $USER:$(id -gn) ~/.ragged

# Fix permissions
chmod 700 ~/.ragged
```

**Windows:**
```powershell
# Take ownership
takeown /F "$HOME\.ragged" /R /D Y

# Reset permissions
icacls "$HOME\.ragged" /reset /T
```

---

### Cannot Write to Documents

**Symptom:**
```
Error: Permission denied writing to ~/.ragged/documents/
```

**Solution:**
```bash
# Check current permissions
ls -la ~/.ragged/

# Fix permissions
chmod 750 ~/.ragged/documents
chmod 640 ~/.ragged/documents/*
```

---

### Cannot Read Configuration

**Symptom:**
```
Error: Permission denied reading ~/.ragged/config.yaml
```

**Solution:**
```bash
# Check permissions
ls -la ~/.ragged/config.yaml

# Fix permissions (should be readable by owner only)
chmod 600 ~/.ragged/config.yaml
```

---

## Ownership Issues

### Wrong Owner After sudo Install

**Symptom:**
Files owned by root, not current user.

**Solution:**
```bash
# Never use sudo for ragged commands!
# Fix ownership:
sudo chown -R $USER:$(id -gn) ~/.ragged

# Verify
ls -la ~/.ragged/
```

---

### Docker Volume Ownership

**Symptom:**
```
Error: Permission denied in Docker volume
```

**Solution:**
```bash
# Check Docker volume permissions
docker run --rm -v ragged_data:/data busybox ls -la /data

# Fix by running container as current user
docker run --rm -u $(id -u):$(id -g) -v ragged_data:/data busybox chmod -R 755 /data
```

---

## SELinux Issues (RHEL/Fedora)

### Docker Container Blocked

**Symptom:**
```
Error: SELinux is preventing Docker from accessing files
```

**Solution:**

**Quick fix (testing only):**
```bash
sudo setenforce 0
```

**Permanent fix:**
```bash
# Allow Docker container access
sudo setsebool -P container_manage_cgroup on

# Add SELinux context to volumes
sudo chcon -Rt svirt_sandbox_file_t ~/.ragged
```

**Check SELinux denials:**
```bash
sudo ausearch -m avc -ts recent
```

---

### Ollama Blocked by SELinux

**Symptom:**
Ollama fails to start with permission errors.

**Solution:**
```bash
# Create SELinux policy for Ollama
sudo ausearch -c 'ollama' --raw | audit2allow -M ollama
sudo semodule -i ollama.pp
```

---

## AppArmor Issues (Ubuntu)

### Docker Profile Issues

**Symptom:**
```
Error: AppArmor blocks Docker operations
```

**Solution:**
```bash
# Check AppArmor status
sudo aa-status

# Disable for Docker (temporary)
sudo aa-complain /etc/apparmor.d/docker

# Or create exception profile
sudo vim /etc/apparmor.d/local/docker
# Add: /{,var/}run/docker.sock rw,
sudo systemctl reload apparmor
```

---

## Gatekeeper Issues (macOS)

### App Cannot Be Opened

**Symptom:**
```
"Docker.app" cannot be opened because it is from an unidentified developer.
```

**Solution:**

**Via System Settings:**
1. Open System Settings → Privacy & Security
2. Scroll to "Security"
3. Click "Open Anyway" next to blocked app

**Via Terminal:**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine /Applications/Docker.app
xattr -d com.apple.quarantine /Applications/Ollama.app
```

---

### Full Disk Access

**Symptom:**
```
Error: Operation not permitted
```

**Solution:**
1. Open System Settings → Privacy & Security → Full Disk Access
2. Click "+" and add:
   - Terminal.app
   - Docker.app
   - Ollama.app
3. Restart the applications

---

## Windows UAC Issues

### Administrator Required

**Symptom:**
```
Error: Access is denied. Run as administrator.
```

**Solution:**

**Don't use admin for ragged commands.** Admin is only needed for:
- Initial Docker Desktop installation
- Initial Ollama installation

For regular use:
```powershell
# Run as normal user
ragged health
```

If files were created as admin:
```powershell
# Fix ownership
icacls "$HOME\.ragged" /grant "$env:USERNAME:(OI)(CI)F" /T
```

---

## File System Issues

### Read-Only File System

**Symptom:**
```
Error: Read-only file system
```

**Solution:**
```bash
# Check mount status
mount | grep "home"

# Remount as read-write (if applicable)
sudo mount -o remount,rw /home
```

---

### Disk Quota Exceeded

**Symptom:**
```
Error: Disk quota exceeded
```

**Solution:**
```bash
# Check quota
quota -s

# Clean up space
ragged cache clear
rm -rf ~/.ragged/logs/*.old

# Or request quota increase from admin
```

---

## Verification

After fixing permissions:

```bash
# Test write access
touch ~/.ragged/test.txt && rm ~/.ragged/test.txt

# Run ragged diagnostics
ragged diagnose

# Check permissions
ls -la ~/.ragged/
```

---

## Related Documentation

- [Resources Troubleshooting](./resources.md)
- [Platform-Specific Issues](./platform-specific.md)
- [Linux Installation](../installation/linux.md)

---
