# Video Script: macOS Installation

**Duration**: ~10 minutes
**Target Audience**: macOS users new to ragged
**Prerequisites**: macOS 11+, internet connection

---

## Introduction (45 seconds)

**Visual**: Ragged logo, title card

**Script**:
> "Welcome to the ragged installation guide for macOS. In about 10 minutes, you'll have ragged fully installed and running on your Mac.
>
> This works on both Intel Macs and Apple Silicon - M1, M2, or M3.
>
> Let's get started."

**Visual**: Show prerequisites
- macOS 11 (Big Sur) or later
- 8GB RAM minimum
- 10GB free disk space

---

## Step 1: Open Terminal (45 seconds)

**Visual**: Screen recording of macOS desktop

**Script**:
> "First, open Terminal. You can do this by pressing Command + Space to open Spotlight, then type 'Terminal' and press Enter."

**Visual**: Show Terminal opening

**Script**:
> "You should see a window with a command prompt. This is where we'll run the installation."

---

## Step 2: Run the Installer (1.5 minutes)

**Visual**: Terminal window

**Script**:
> "Copy and paste this command into Terminal:"

**Visual**: Show command
```bash
curl -sSL https://install.ragged.ai | sh
```

**Script**:
> "Press Enter to start. The installer will ask for your password - this is your Mac login password. Type it and press Enter. Note that you won't see the characters as you type - that's normal for security."

**Visual**: Show password prompt and installation starting

---

## Step 3: Gatekeeper Prompts (1 minute)

**Visual**: Gatekeeper dialog

**Script**:
> "macOS might show a security prompt saying an app is from an unidentified developer. This is normal for new software.
>
> If this happens, open System Settings, go to Privacy & Security, scroll down, and click 'Open Anyway' next to the blocked app."

**Visual**: Show System Settings navigation

---

## Step 4: Docker Desktop (2 minutes)

**Visual**: Docker Desktop installation

**Script**:
> "The installer is setting up Docker Desktop. This runs the database that stores your documents.
>
> You might see the Docker app open - that's fine. Look for the whale icon in your menu bar at the top of the screen."

**Visual**: Show Docker whale icon in menu bar

**Script**:
> "When the whale stops animating, Docker is ready. This usually takes about a minute."

---

## Step 5: Ollama Download (1.5 minutes)

**Visual**: Show download progress

**Script**:
> "Now the installer is downloading the AI model. This is about 4 gigabytes, so it might take a few minutes.
>
> If you're on Apple Silicon, the model will use your Mac's GPU for faster processing."

**Visual**: Speed up download footage

---

## Step 6: Verify Installation (1.5 minutes)

**Visual**: Terminal window

**Script**:
> "Let's check that everything is working. Type:"

**Visual**: Show command
```bash
ragged health
```

**Visual**: Show health output

**Script**:
> "You should see all green checkmarks. This means:
> - Python is ready
> - Docker is running
> - Ollama is configured
> - All services are healthy"

---

## Step 7: Open WebUI (1 minute)

**Visual**: Safari/Chrome opening

**Script**:
> "Open your browser and go to localhost:5173"

**Visual**: Show URL bar

**Script**:
> "This is the ragged web interface. You're ready to start uploading documents and asking questions."

**Visual**: Show WebUI interface

---

## Conclusion (30 seconds)

**Script**:
> "That's it! Ragged is installed on your Mac.
>
> Check out the next video to learn how to upload your first document.
>
> If you had any issues, the troubleshooting link is in the description.
>
> Thanks for watching!"

**Visual**: End card with next steps

---

## Troubleshooting Notes

**Include in video description:**

Common issues:
- **Gatekeeper blocks app**: System Settings → Privacy & Security → Open Anyway
- **Docker won't start**: Restart Mac, try again
- **Slow on Intel Mac**: Intel Macs are slower than Apple Silicon

Full troubleshooting guide: [link]

---
