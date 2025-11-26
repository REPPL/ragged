# Video Script: Windows Installation

**Duration**: ~12 minutes
**Target Audience**: Windows users new to ragged
**Prerequisites**: Windows 10/11, internet connection

---

## Introduction (1 minute)

**Visual**: Ragged logo, title card

**Script**:
> "Welcome to this ragged installation guide for Windows. In the next 12 minutes, I'll walk you through installing ragged on your Windows machine, step by step.
>
> By the end of this video, you'll have ragged fully installed and running, ready to process your first document.
>
> Let's get started."

**Visual**: Show prerequisites checklist
- Windows 10 version 1903 or later (or Windows 11)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection

---

## Step 1: Open PowerShell (1 minute)

**Visual**: Screen recording of desktop

**Script**:
> "First, we need to open PowerShell as an Administrator.
>
> Press the Windows key, type 'PowerShell', right-click on 'Windows PowerShell', and select 'Run as administrator'.
>
> Click 'Yes' when Windows asks for permission."

**Visual**: Show PowerShell window opening

**Script**:
> "You should now see a blue PowerShell window. Notice it says 'Administrator' in the title bar - this confirms we have the right permissions."

---

## Step 2: Run the Installer (2 minutes)

**Visual**: PowerShell window

**Script**:
> "Now we'll run the one-command installer. Type or paste this command:"

**Visual**: Show command being typed
```powershell
irm https://install.ragged.ai/windows | iex
```

**Script**:
> "Press Enter to start the installation.
>
> The installer will now check your system and download the required components. This includes Docker Desktop, Ollama for AI processing, and ragged itself.
>
> Let's watch it work..."

**Visual**: Show installer progress (speed up if needed)

**Script**:
> "You can see the progress bars showing each step:
> - Checking system requirements
> - Installing Docker Desktop
> - Installing Ollama
> - Downloading ragged
> - Configuring services"

---

## Step 3: Docker Desktop Setup (3 minutes)

**Visual**: Docker Desktop installation screens

**Script**:
> "The installer is now setting up Docker Desktop. This might take a few minutes.
>
> If Docker Desktop opens, you may see a welcome screen. You can close this - the installer will configure everything automatically."

**Visual**: Show Docker whale icon in system tray

**Script**:
> "Look for the Docker whale icon in your system tray at the bottom right. When it stops animating, Docker is ready.
>
> If you see any firewall prompts, click 'Allow' - this lets Docker communicate on your local network."

---

## Step 4: Ollama Model Download (2 minutes)

**Visual**: Show Ollama download progress

**Script**:
> "Next, the installer downloads an AI model. This is the 'brain' that answers your questions about documents.
>
> The default model is about 4 gigabytes, so this might take a few minutes depending on your internet speed."

**Visual**: Show download completing

**Script**:
> "Once the download completes, you'll see a success message."

---

## Step 5: Verify Installation (2 minutes)

**Visual**: PowerShell window

**Script**:
> "Let's verify everything is working. Type this command:"

**Visual**: Show command
```powershell
ragged health
```

**Script**:
> "You should see a health status screen with green checkmarks for each component."

**Visual**: Show health output with all green checks

**Script**:
> "Perfect! All services are healthy:
> - Python is installed
> - Docker is running
> - Ollama is ready
> - ChromaDB is healthy
> - The API server is running
> - The WebUI is available"

---

## Step 6: Open the WebUI (1 minute)

**Visual**: Browser opening

**Script**:
> "Now let's open the web interface. Open your browser and go to:"

**Visual**: Show URL
```
http://localhost:5173
```

**Visual**: Show WebUI loading

**Script**:
> "This is the ragged web interface. From here, you can:
> - Upload documents
> - Ask questions
> - Manage your document library
> - Configure settings"

---

## Conclusion (30 seconds)

**Visual**: WebUI with document upload highlighted

**Script**:
> "Congratulations! Ragged is now installed on your Windows machine.
>
> In the next video, I'll show you how to upload your first document and ask questions.
>
> If you ran into any problems, check the troubleshooting guide in the video description.
>
> Thanks for watching, and happy document querying!"

**Visual**: End card with links
- Next video: First Steps with Ragged
- Troubleshooting guide link
- Documentation link

---

## Troubleshooting Notes

**Include in video description:**

Common issues:
- **WSL 2 error**: Run `wsl --install` in PowerShell
- **Port in use**: Another app is using port 8000
- **Docker won't start**: Enable virtualisation in BIOS

Full troubleshooting guide: [link]

---

## Recording Notes

- Use clean Windows installation if possible
- Hide personal files/bookmarks
- Use 1080p resolution
- Test audio levels before recording
- Pause at key moments for viewer comprehension

---
