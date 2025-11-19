# Cross-Platform Validation Checklist

**Purpose:** Validate ragged functionality across macOS, Linux, and Windows platforms.

**Estimated Time:** 1-2 hours (across all platforms)

**Last Updated:** 2025-11-19

---

## Test Matrix

| Test | macOS | Linux | Windows |
|------|-------|-------|---------|
| Installation | ☐ | ☐ | ☐ |
| Core CLI | ☐ | ☐ | ☐ |
| File paths | ☐ | ☐ | ☐ |
| Shell completion | ☐ | ☐ | ☐ |
| Docker | ☐ | ☐ | ☐ |

---

## 1. Installation

### Test Case 1.1: macOS Installation

**Platform:** macOS 13+ (Ventura, Sonoma)

**Steps:**
```bash
python3.12 -m pip install ragged
ragged --version
```

**Expected Result:**
- Installs successfully
- All dependencies resolve
- Command available in PATH
- Version displays correctly

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

**Python Version:** ____________________
**macOS Version:** ____________________

---

### Test Case 1.2: Linux Installation

**Platform:** Ubuntu 22.04, Debian 12, Fedora 39, or similar

**Steps:**
```bash
python3.12 -m pip install ragged
ragged --version
```

**Expected Result:**
- Installs successfully
- Dependencies install correctly
- Works with system Python
- No permission issues

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

**Distribution:** ____________________
**Python Version:** ____________________

---

### Test Case 1.3: Windows Installation

**Platform:** Windows 10/11

**Steps:**
```powershell
python -m pip install ragged
ragged --version
```

**Expected Result:**
- Installs without errors
- Dependencies resolve
- Command works in PowerShell and CMD
- PATH configured correctly

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

**Windows Version:** ____________________
**Python Version:** ____________________

---

## 2. Path Handling

### Test Case 2.1: Unix Paths (macOS/Linux)

**Steps:**
```bash
ragged add /home/user/documents/test.pdf
ragged add ~/documents/test.pdf
ragged add ./relative/path/test.pdf
```

**Expected Result:**
- Absolute paths work
- Home directory (~) expansion works
- Relative paths work
- Symlinks followed correctly

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.2: Windows Paths

**Steps:**
```powershell
ragged add C:\Users\username\Documents\test.pdf
ragged add .\relative\path\test.pdf
ragged add ~\Documents\test.pdf
```

**Expected Result:**
- Drive letters work (C:\, D:\, etc.)
- Backslashes handled correctly
- Forward slashes also work
- UNC paths work (\\server\share)

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.3: Spaces in Paths

**Platform:** All

**Steps:**
```bash
ragged add "/path/with spaces/file.pdf"
ragged add "C:\Path With Spaces\file.pdf"
```

**Expected Result:**
- Quoted paths work
- Spaces handled correctly
- No escaping issues

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 3. Shell Completion

### Test Case 3.1: Bash Completion (Linux/macOS)

**Steps:**
```bash
ragged completion --install bash
source ~/.bashrc  # or ~/.bash_profile
ragged <TAB>
```

**Expected Result:**
- Installation successful
- Commands complete
- File paths complete
- Works after shell restart

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.2: Zsh Completion (macOS/Linux)

**Steps:**
```zsh
ragged completion --install zsh
# Restart shell
ragged <TAB>
```

**Expected Result:**
- Installation works
- Completion functional
- Descriptions shown

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.3: Fish Completion (macOS/Linux)

**Steps:**
```fish
ragged completion --install fish
ragged <TAB>
```

**Expected Result:**
- Installation successful
- Completion works
- Fish-specific features work

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.4: PowerShell Completion (Windows)

**Steps:**
```powershell
ragged completion --install powershell
# Restart PowerShell
ragged <TAB>
```

**Expected Result:**
- Installation works
- Tab completion functional
- Parameters complete

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 4. Configuration Files

### Test Case 4.1: Config Location (macOS)

**Expected Location:** `~/.config/ragged/config.yaml`

**Steps:**
1. Check config file location
2. Verify settings persist

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.2: Config Location (Linux)

**Expected Location:** `~/.config/ragged/config.yaml` or `$XDG_CONFIG_HOME/ragged/`

**Steps:**
1. Check config file location
2. Verify XDG compliance

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.3: Config Location (Windows)

**Expected Location:** `%APPDATA%\ragged\config.yaml`

**Steps:**
1. Check config file location
2. Verify settings persist

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 5. Service Integration

### Test Case 5.1: Ollama on macOS

**Steps:**
1. Install Ollama for macOS
2. Start Ollama service
3. Test ragged integration

**Expected Result:**
- Service starts correctly
- ragged connects successfully
- Queries work

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 5.2: Ollama on Linux

**Steps:**
1. Install Ollama for Linux
2. Start service
3. Test integration

**Expected Result:**
- Systemd service works (if applicable)
- Connection successful
- No permission issues

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 5.3: Ollama on Windows

**Steps:**
1. Install Ollama for Windows
2. Start service
3. Test integration

**Expected Result:**
- Windows service works
- Firewall doesn't block
- Connection successful

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 6. Docker Support

### Test Case 6.1: Docker Compose (macOS)

**Steps:**
```bash
docker-compose up -d
ragged health
```

**Expected Result:**
- Services start correctly
- ChromaDB accessible
- Volumes mount properly

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 6.2: Docker Compose (Linux)

**Steps:**
```bash
docker-compose up -d
ragged health
```

**Expected Result:**
- Services start
- Permissions correct
- Networking works

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 6.3: Docker Compose (Windows)

**Steps:**
```powershell
docker-compose up -d
ragged health
```

**Expected Result:**
- Docker Desktop works
- WSL2 integration works (if applicable)
- Services accessible

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 7. Character Encoding

### Test Case 7.1: UTF-8 Support (All Platforms)

**Steps:**
1. Add document with UTF-8 content (Unicode, emoji, etc.)
2. Query for that content

**Expected Result:**
- Encoding handled correctly on all platforms
- No mojibake or corruption
- Searchable and retrievable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 8. Performance Comparison

### Test Case 8.1: Ingestion Speed

**Test:** Ingest 100 mixed documents

**Results:**
- macOS: ______ seconds
- Linux: ______ seconds
- Windows: ______ seconds

**Notes:** ____________________

---

### Test Case 8.2: Query Latency

**Test:** Run 10 identical queries

**Results:**
- macOS p95: ______ ms
- Linux p95: ______ ms
- Windows p95: ______ ms

**Notes:** ____________________

---

## 9. Platform-Specific Issues

### macOS-Specific

**Tested:** ☐ Apple Silicon (M1/M2/M3) ☐ Intel

**Issues:**
- [ ] Rosetta 2 compatibility (if applicable)
- [ ] Gatekeeper warnings
- [ ] Code signing
- [ ] Permissions (Full Disk Access if needed)

**Notes:** ____________________

---

### Linux-Specific

**Tested:** ☐ Debian-based ☐ Red Hat-based ☐ Arch-based

**Issues:**
- [ ] systemd vs other init systems
- [ ] SELinux/AppArmor conflicts
- [ ] Dependencies availability
- [ ] Different Python versions

**Notes:** ____________________

---

### Windows-Specific

**Tested:** ☐ PowerShell ☐ CMD ☐ Git Bash ☐ WSL

**Issues:**
- [ ] Path length limitations (260 char limit)
- [ ] Case sensitivity differences
- [ ] Line ending differences (CRLF vs LF)
- [ ] Windows Defender interference

**Notes:** ____________________

---

## Summary

### Platform Support Matrix

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| Installation | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail |
| Core functionality | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail |
| Path handling | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail |
| Shell completion | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail |
| Docker support | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail |
| Performance | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail | ☐ Pass ☐ Fail |

---

### Platform-Specific Issues

| Platform | Issue | Workaround | Status |
|----------|-------|------------|--------|
| macOS | | | ☐ Open ☐ Fixed |
| Linux | | | ☐ Open ☐ Fixed |
| Windows | | | ☐ Open ☐ Fixed |

---

### Recommendations

**Officially Supported:**
- [ ] macOS 13+ (Ventura, Sonoma)
- [ ] Ubuntu 22.04 LTS, Debian 12
- [ ] Windows 10/11

**Tested But Not Officially Supported:**
- [ ] Fedora 39
- [ ] Arch Linux
- [ ] WSL2

---

**Tested By:** ____________________
**Date:** ____________________
**Platforms Tested:** ____________________

---

**Maintained By:** ragged development team
