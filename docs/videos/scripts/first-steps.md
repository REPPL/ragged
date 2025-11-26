# Video Script: First Steps with Ragged

**Duration**: ~7 minutes
**Target Audience**: New users who just installed ragged
**Prerequisites**: Ragged installed and running

---

## Introduction (30 seconds)

**Visual**: Ragged logo, WebUI in background

**Script**:
> "You've installed ragged - now let's use it! In this video, I'll show you how to:
> - Upload your first document
> - Ask questions about it
> - Explore the results
>
> Let's dive in."

---

## Step 1: Open the WebUI (30 seconds)

**Visual**: Browser opening

**Script**:
> "Open your browser and go to localhost:5173"

**Visual**: Show WebUI loading

**Script**:
> "This is the ragged web interface. The main area is for chatting, and the sidebar shows your documents."

---

## Step 2: Upload a Document (1.5 minutes)

**Visual**: WebUI document upload area

**Script**:
> "Let's upload a document. Click the 'Upload' button or drag a file into the upload area.
>
> Ragged supports many formats:
> - PDF documents
> - Word files
> - Text files
> - Markdown
> - And more"

**Visual**: Show file picker, select a PDF

**Script**:
> "I'll upload this sample PDF. Watch the progress bar as ragged processes the document."

**Visual**: Show upload progress

**Script**:
> "Processing includes:
> - Extracting text
> - Breaking it into chunks
> - Creating searchable embeddings
>
> For a typical document, this takes just a few seconds."

**Visual**: Show success message

---

## Step 3: Ask Your First Question (2 minutes)

**Visual**: Chat input area

**Script**:
> "Now for the exciting part - asking questions! Type a question in the chat box at the bottom."

**Visual**: Type question
```
What is this document about?
```

**Script**:
> "Press Enter or click Send."

**Visual**: Show response streaming

**Script**:
> "Watch as ragged:
> 1. Searches your document for relevant sections
> 2. Sends them to the AI model
> 3. Generates a natural language answer
>
> The answer appears in real-time as it's generated."

**Visual**: Show complete response

**Script**:
> "Notice that ragged shows which parts of the document it used to answer. This is called 'sources' or 'citations' - it helps you verify the answer."

---

## Step 4: Ask Follow-up Questions (1 minute)

**Visual**: Chat continuing

**Script**:
> "You can ask follow-up questions. Ragged remembers the conversation context."

**Visual**: Type another question
```
Can you give me more details about the main topic?
```

**Visual**: Show response

**Script**:
> "Each answer includes sources, so you can always check where the information came from."

---

## Step 5: Try the CLI (1 minute)

**Visual**: Terminal window

**Script**:
> "You can also use ragged from the command line. Open Terminal or PowerShell and type:"

**Visual**: Show command
```bash
ragged query "What is this document about?"
```

**Visual**: Show CLI response

**Script**:
> "The CLI is great for scripting and automation. All the same features are available."

---

## Next Steps (30 seconds)

**Visual**: WebUI with multiple documents

**Script**:
> "Now you know the basics! Here's what to try next:
> - Upload more documents
> - Ask complex questions across multiple docs
> - Explore the settings to customise ragged
>
> Check out the other videos for advanced features."

---

## Conclusion (15 seconds)

**Script**:
> "That's your first steps with ragged! If you have questions, check the documentation or join our community.
>
> Thanks for watching, and happy querying!"

**Visual**: End card with links

---

## Recording Notes

- Use a sample PDF that's interesting but not too long
- Choose questions that give good demo answers
- Show the "sources" feature clearly
- Keep energy upbeat but not rushed

---
