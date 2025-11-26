# Quick Start Guide

Get ragged running in 5 minutes or less.

---

## Step 1: Install (2 minutes)

**macOS/Linux:**
```bash
curl -sSL https://install.ragged.ai | sh
```

**Windows (PowerShell as Administrator):**
```powershell
irm https://install.ragged.ai/windows | iex
```

Wait for installation to complete. The installer handles all dependencies automatically.

---

## Step 2: Verify (30 seconds)

```bash
ragged health
```

You should see all services with ✅ status:

```
╭─────────────────────────────────────────────────────╮
│              Ragged Health Status                    │
├─────────────────────────────────────────────────────┤
│  ✅ Python 3.12.0                                   │
│  ✅ Docker Desktop 4.25.0                           │
│  ✅ Ollama 0.1.17                                   │
│  ✅ ChromaDB (healthy)                              │
│  ✅ API Server (localhost:8000)                     │
│  ✅ WebUI (localhost:5173)                          │
╰─────────────────────────────────────────────────────╯
```

---

## Step 3: Upload a Document (1 minute)

```bash
ragged ingest ~/Documents/example.pdf
```

Or drag and drop in the WebUI at http://localhost:5173

---

## Step 4: Ask a Question (30 seconds)

```bash
ragged query "What is this document about?"
```

Or type your question in the WebUI chat.

---

## Step 5: Explore the WebUI (1 minute)

Open your browser: http://localhost:5173

From here you can:
- Upload more documents
- Ask questions
- View document library
- Configure settings

---

## What's Next?

### Learn More
- [Full Installation Guide](./installation/README.md) - Detailed setup instructions
- [CLI Reference](./reference/cli.md) - All available commands
- [Configuration Guide](./guides/configuration.md) - Customise ragged

### Having Problems?
- [Troubleshooting Guide](./troubleshooting/README.md) - Common issues and solutions
- [FAQ](./faq.md) - Frequently asked questions

### Video Tutorials
- [Installation Walkthrough](./videos/README.md) - Visual guides

---

## Quick Troubleshooting

**Installation failed?**
```bash
ragged diagnose
```

**Port in use?**
```bash
ragged config set server.port 8080
ragged restart
```

**Docker not running?**
- Windows/macOS: Open Docker Desktop
- Linux: `sudo systemctl start docker`

**Need more help?**
See the full [Troubleshooting Guide](./troubleshooting/README.md).

---
