# Ragged v0.6 Roadmap - Data Connectivity & UI Foundation

**Status:** Planned

**Duration:** 80-120 hours (AI implementation)

**Focus:** Expand data source connectivity and establish modern web UI foundation

**Breaking Changes:** None

---

## Overview

Version 0.6 expands ragged beyond local files with cloud connectors and folder automation, while laying the foundation for a modern web interface. This addresses key gaps identified in the RAG ecosystem analysis—automated ingestion and professional UI.

**Dependencies:** Requires v0.5.x completion (vision RAG, GPU management)

**Strategic Context:** Brings ragged in line with PrivateGPT's folder watch automation and begins UI modernisation toward AnythingLLM-level polish.

---

## CONNECT-001: Google Drive Connector (20-25 hours)

**Problem:** Users cannot ingest documents from Google Drive, requiring manual download and local ingestion.

**Inspiration:** Onyx/Danswer's 40+ connectors demonstrate value of integrated cloud access.

**Implementation:**
1. Research Google Drive API and authentication [3-4 hours]
2. Implement OAuth2 authentication flow [6-8 hours]
3. Create Drive document listing and filtering [5-6 hours]
4. Add incremental sync (only new/modified files) [4-5 hours]
5. Implement metadata preservation (author, created date, shared status) [2-3 hours]

**Supported file types:**
- Google Docs (export as PDF)
- Google Sheets (export as PDF)
- PDF files
- Image files (for vision RAG)

**CLI commands:**
```bash
ragged connect google-drive auth            # Authenticate
ragged connect google-drive list            # List folders
ragged ingest google-drive <folder_id>      # Ingest folder
ragged connect google-drive sync <folder_id> # Incremental sync
```

**Files:**
- `src/connectors/google_drive.py` (new, ~350 lines)
- `src/connectors/auth/oauth.py` (new, ~200 lines)
- `src/connectors/base.py` (new abstract base, ~150 lines)
- `tests/connectors/test_google_drive.py` (~250 lines)

**Manual Testing:**
- Authenticate with Google account
- List Drive folders and files
- Ingest folder with mixed file types
- Verify incremental sync updates only changed files
- Confirm metadata preserved in ChromaDB

**Success:** Users can ingest and auto-sync Google Drive folders without manual downloads

---

## CONNECT-002: Dropbox Connector (15-20 hours)

**Problem:** No Dropbox integration for personal knowledge workers who use Dropbox as primary storage.

**Implementation:**
1. Implement Dropbox OAuth2 authentication [4-5 hours]
2. Create folder browsing and file listing [4-5 hours]
3. Add incremental sync with cursor-based pagination [4-5 hours]
4. Implement metadata extraction [2-3 hours]
5. Add conflict resolution for modified files [1-2 hours]

**CLI commands:**
```bash
ragged connect dropbox auth
ragged connect dropbox list
ragged ingest dropbox <path>
ragged connect dropbox sync <path>
```

**Files:**
- `src/connectors/dropbox.py` (new, ~300 lines)
- Reuses `src/connectors/auth/oauth.py` (OAuth flow generic)
- `tests/connectors/test_dropbox.py` (~200 lines)

**Manual Testing:**
- Authenticate with Dropbox
- Ingest shared folder
- Verify sync detects file changes

**Success:** Dropbox folders ingest and sync automatically

---

## CONNECT-003: Notion Connector (25-30 hours)

**Problem:** Knowledge workers increasingly use Notion for notes; no way to ingest without manual export.

**Inspiration:** Onyx/Danswer's Notion connector is highly requested feature.

**Implementation:**
1. Research Notion API (blocks, pages, databases) [4-5 hours]
2. Implement Notion authentication [5-6 hours]
3. Create recursive page traversal (handle nested pages) [6-8 hours]
4. Convert Notion blocks to markdown or plain text [6-8 hours]
5. Preserve structure (headings, lists, code blocks) [3-4 hours]
6. Add database query support [1-2 hours]

**Challenges:**
- Notion's block-based structure requires custom parsing
- Handle nested pages and databases
- Preserve formatting and structure

**CLI commands:**
```bash
ragged connect notion auth
ragged connect notion list-pages
ragged ingest notion <page_id>
ragged ingest notion-database <database_id>
```

**Files:**
- `src/connectors/notion.py` (new, ~450 lines)
- `src/connectors/notion_parser.py` (block → text conversion, ~300 lines)
- `tests/connectors/test_notion.py` (~250 lines)

**Manual Testing:**
- Authenticate with Notion workspace
- Ingest nested page hierarchies
- Verify block formatting preserved
- Ingest database as structured documents

**Success:** Notion pages and databases ingest with structure preserved

---

## CONNECT-004: Folder Watch Automation (20-25 hours)

**Problem:** Users must manually re-ingest documents when files change; no automatic monitoring.

**Inspiration:** PrivateGPT's folder watch feature enables "set it and forget it" document management.

**Implementation:**
1. Research file system event monitoring (watchdog library) [2-3 hours]
2. Implement folder monitoring daemon [6-8 hours]
3. Add debouncing for rapid file changes [4-5 hours]
4. Create ingestion queue and batch processing [4-5 hours]
5. Implement conflict resolution (delete, update, new) [3-4 hours]
6. Add CLI and configuration for watched folders [1-2 hours]

**Folder watch features:**
- Monitor local directories for changes
- Auto-ingest new files
- Update embeddings when files modified
- Remove embeddings when files deleted
- Batch processing to avoid rapid re-ingestion

**CLI commands:**
```bash
ragged watch add <folder_path>              # Start watching folder
ragged watch list                           # List watched folders
ragged watch remove <folder_path>           # Stop watching
ragged watch status                         # Show watch daemon status
```

**Background daemon:**
- Runs as systemd service (Linux) or launchd (macOS)
- Logs all ingestion events
- Configurable file type filters

**Files:**
- `src/watch/folder_watcher.py` (new, ~400 lines)
- `src/watch/daemon.py` (service management, ~250 lines)
- `src/watch/queue.py` (ingestion queue, ~200 lines)
- `systemd/ragged-watch.service` (new)
- `tests/watch/test_folder_watcher.py` (~300 lines)

**Manual Testing:**
- Add watched folder
- Create new file → verify auto-ingestion
- Modify file → verify embedding update
- Delete file → verify removal from ChromaDB
- Restart daemon → verify watch persistence

**Success:** Folders monitor continuously; changes sync automatically within 30 seconds

---

## UI-001: Svelte UI Foundation (30-40 hours)

**Problem:** Current Gradio UI is basic and not suitable for daily use; users expect modern web applications.

**Inspiration:** AnythingLLM's polished UI demonstrates importance of professional interface design.

**Strategic Goal:** Establish foundation for v0.9's full Web UI completion.

**Implementation:**
1. Set up SvelteKit project structure [4-5 hours]
2. Design component architecture and routing [6-8 hours]
3. Create REST API client library [5-6 hours]
4. Implement authentication UI (if RBAC in v0.7) [6-8 hours]
5. Build document library interface (basic) [6-8 hours]
6. Add search interface (basic) [3-4 hours]

**UI pages (v0.6 foundation):**
- **Home:** Quick search, recent documents
- **Documents:** Library view with filtering
- **Search:** Simple search interface
- **Settings:** Basic configuration

**Technology stack:**
- **Framework:** SvelteKit (SSR, routing, fast)
- **Styling:** TailwindCSS (utility-first, consistent design)
- **Components:** shadcn-svelte (accessible, customisable)
- **API:** REST client with type safety

**Files:**
- `web-ui/` (new directory)
  - `src/routes/` (SvelteKit routes)
  - `src/lib/components/` (reusable components)
  - `src/lib/api/` (API client)
  - `src/app.html`, `svelte.config.js`, etc.
- `docker-compose.yml` (add web-ui service)
- ~2000 lines total (foundation only)

**Manual Testing:**
- Navigate all pages
- Verify API integration works
- Test responsive design (mobile, tablet, desktop)
- Verify authentication flow (if implemented)

**Success:** Modern web UI foundation deployed; basic document browsing and search functional

---

## API-001: REST API Stabilisation (15-20 hours)

**Problem:** REST API lacks formal specification; versioning unclear; breaking changes possible.

**Implementation:**
1. Create OpenAPI 3.1 specification [6-8 hours]
2. Add API versioning (`/api/v1/`) [4-5 hours]
3. Implement request/response validation [3-4 hours]
4. Add comprehensive API documentation [2-3 hours]

**API endpoints to formalise:**
- `POST /api/v1/documents/ingest`
- `POST /api/v1/query`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `DELETE /api/v1/documents/{id}`
- `GET /api/v1/health`

**OpenAPI spec features:**
- Request/response schemas
- Authentication requirements
- Error response codes
- Example requests/responses

**Files:**
- `docs/api/openapi.yaml` (new, ~500 lines)
- `src/web/api.py` (add versioning middleware)
- `src/web/validation.py` (request validation, ~200 lines)

**Manual Testing:**
- Import OpenAPI spec into Postman/Insomnia
- Test all endpoints
- Verify validation errors return correct codes
- Generate API client from spec

**Success:** OpenAPI spec complete; API versioned; breaking changes prevented

---

## Success Criteria

**Automated Tests:**
- [ ] Google Drive authentication and sync working
- [ ] Dropbox authentication and sync working
- [ ] Notion page parsing preserves structure
- [ ] Folder watch detects file changes correctly
- [ ] Folder watch debounces rapid changes
- [ ] API validation enforces schemas
- [ ] All existing tests pass

**Manual Testing:**
- [ ] Authenticate with Google Drive, ingest folder
- [ ] Sync Google Drive folder detects new files
- [ ] Authenticate with Dropbox, ingest folder
- [ ] Authenticate with Notion, ingest nested pages
- [ ] Watch folder auto-ingests new file within 30s
- [ ] Watch folder updates modified file
- [ ] Watch folder removes deleted file
- [ ] Svelte UI loads and navigation works
- [ ] API endpoints work via OpenAPI client

**Quality Gates:**
- [ ] Folder watch latency <30 seconds for file changes
- [ ] Cloud connectors handle 100+ files efficiently
- [ ] Incremental sync faster than full re-ingestion
- [ ] UI responsive on mobile and desktop
- [ ] API specification complete and accurate
- [ ] Zero breaking API changes
- [ ] Documentation complete for all connectors

---

## Known Risks

- **OAuth complexity:** Google/Dropbox/Notion authentication requires careful security handling
- **Rate limiting:** Cloud APIs have rate limits; large folders may hit limits
- **Notion structure:** Complex block parsing may not preserve all formatting
- **Folder watch reliability:** File system events may be missed on some platforms
- **UI scope creep:** Foundation only—defer advanced features to v0.9
- **API changes:** Stabilising API may require refactoring existing endpoints

---

## Next Steps

After v0.6 completion:
- **v0.7:** Enterprise Foundation (authentication, RBAC, monitoring) - keep existing plan
- **v0.8:** Agent Capabilities (agentic workflows, tool use)
- **v0.9:** Web UI Completion (block editor, visual DAG, PWA)

See: `roadmap/version/v0.7/README.md`, `roadmap/version/v0.8/README.md`

---

## Related Documentation

- [Previous Version](../v0.5/README.md) - Vision RAG and GPU management
- [Next Version](../v0.7/README.md) - Enterprise foundation
- [Planning](../../planning/version/v0.6/) - Design goals for v0.6 (if exists)
- [Version Overview](../README.md) - Complete version comparison
- [Projects to Learn From](../../../research/projects-to-learn-from.md) - Ecosystem analysis informing this roadmap

---
