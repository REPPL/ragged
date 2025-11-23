# Ragged v1.5 Roadmap - Collaboration & Multi-User

**Status:** Planned

**Duration:** 100-150 hours (AI implementation)

**Focus:** Team collaboration, document sharing, and multi-user workflows

**Breaking Changes:** Database schema changes (migration required)

---

## Overview

Version 1.5 transforms ragged from a personal tool into a team collaboration platform. This addresses the collaboration gap identified in the ecosystem analysis—team features, sharing, and permission management inspired by Onyx/Danswer and AnythingLLM's team capabilities.

**Dependencies:** Requires v0.9 (Web UI completion), v0.7 (authentication foundation)

**Strategic Context:** Enables team use cases whilst maintaining ragged's privacy-first principles through granular permissions and end-to-end encryption.

**Important:** This version represents a significant expansion beyond personal use. Carefully validate demand before implementation.

---

## COLLAB-001: Multi-User Foundation (25-30 hours)

**Problem:** Single-user architecture; no support for multiple users with separate data.

**Inspiration:** Onyx/Danswer's multi-tenant architecture, AnythingLLM's team workspaces.

**Implementation:**
1. Design multi-user database schema [5-6 hours]
2. Implement user registration and profile management [6-8 hours]
3. Create workspace/team abstraction [6-8 hours]
4. Add data isolation and access control [5-6 hours]
5. Implement migration from single-user to multi-user [3-4 hours]

**Multi-user architecture:**
- **Users:** Individual accounts with profiles
- **Workspaces:** Isolated environments for teams or individuals
- **Collections:** Document collections (private, shared, team)
- **Permissions:** Granular access control per collection

**Database schema changes:**
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workspaces (teams)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workspace members
CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES users(id),
    role TEXT NOT NULL, -- owner, admin, member, viewer
    PRIMARY KEY (workspace_id, user_id)
);

-- Collections (document groups with permissions)
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    name TEXT NOT NULL,
    visibility TEXT NOT NULL, -- private, shared, team
    owner_id UUID REFERENCES users(id)
);
```

**Migration strategy:**
- Detect single-user installation
- Create default user and workspace
- Migrate existing documents to default user's collection
- Preserve all data and embeddings

**Files:**
- `src/database/schema_v1.5.sql` (new schema, ~400 lines)
- `src/database/migration_v1.5.py` (migration script, ~300 lines)
- `src/auth/users.py` (user management, ~400 lines)
- `src/workspaces/manager.py` (workspace management, ~350 lines)
- `tests/database/test_multiuser.py` (~300 lines)

**Manual Testing:**
- Migrate single-user installation
- Create multiple users
- Create workspace, invite members
- Verify data isolation between workspaces
- Verify migration preserves all data

**Success:** Multi-user foundation functional; data isolated per workspace; migration seamless

---

## COLLAB-002: Document Sharing & Permissions (20-25 hours)

**Problem:** Documents private to creator; no way to share with team or specific users.

**Inspiration:** Onyx/Danswer's permission mirroring, AnythingLLM's shared collections.

**Implementation:**
1. Design permission model (RBAC + ACL) [4-5 hours]
2. Implement sharing UI (share dialog) [6-8 hours]
3. Add permission enforcement in API and queries [6-8 hours]
4. Create permission inheritance system [3-4 hours]
5. Add audit logging for permission changes [1-2 hours]

**Permission model:**
- **Roles:** Owner, Editor, Commenter, Viewer
- **Permissions:** Read, Write, Delete, Share, Admin
- **Inheritance:** Workspace → Collection → Document

**Sharing options:**
- **Private:** Only owner can access
- **Shared with users:** Specific users with specific roles
- **Shared with workspace:** All workspace members (role-based)
- **Public link:** Anyone with link (viewer only, optional)

**Permission enforcement:**
```python
async def query(user_id: str, query: str) -> QueryResult:
    # Only retrieve documents user has access to
    accessible_docs = await get_accessible_documents(user_id)

    # Filter retrieval to only accessible documents
    results = await hybrid_retrieve(
        query,
        filter={"document_id": {"$in": accessible_docs}}
    )

    return results
```

**Files:**
- `src/permissions/rbac.py` (role-based access control, ~400 lines)
- `src/permissions/acl.py` (access control lists, ~300 lines)
- `src/permissions/enforcement.py` (permission checks, ~350 lines)
- `web-ui/src/lib/components/sharing/ShareDialog.svelte` (~400 lines)
- `tests/permissions/test_sharing.py` (~350 lines)

**Manual Testing:**
- Share document with specific user
- Verify permission enforcement (viewer can't edit)
- Test permission inheritance (workspace → collection)
- Verify query results filtered by permissions
- Test audit log captures permission changes

**Success:** Document sharing functional; permissions enforced consistently; audit trail complete

---

## COLLAB-003: Real-Time Collaboration (30-40 hours)

**Problem:** Multiple users editing same document create conflicts; no real-time updates.

**Inspiration:** Notion's real-time collaboration, Google Docs.

**Implementation:**
1. Research CRDT libraries (Yjs, Automerge) [4-5 hours]
2. Integrate Yjs with block editor (v0.9) [10-12 hours]
3. Implement WebSocket server for real-time sync [8-10 hours]
4. Add presence indicators (who's viewing/editing) [4-5 hours]
5. Create conflict resolution UI [3-4 hours]

**Real-time features:**
- **Collaborative editing:** Multiple users edit same document simultaneously
- **Presence:** See who's currently viewing/editing
- **Cursor tracking:** See other users' cursors and selections
- **Live updates:** Changes appear immediately for all users
- **Offline support:** Queue changes, sync when reconnected

**Technical approach:**
- **CRDT:** Yjs for conflict-free collaborative editing
- **Transport:** WebSocket for real-time sync
- **Persistence:** Save CRDT state to database
- **Awareness:** Track user presence and cursors

**Files:**
- `src/realtime/websocket_server.py` (WebSocket server, ~500 lines)
- `src/realtime/yjs_persistence.py` (CRDT persistence, ~300 lines)
- `web-ui/src/lib/components/editor/CollaborativeEditor.svelte` (~600 lines)
- `web-ui/src/lib/realtime/presence.ts` (presence tracking, ~250 lines)
- `tests/realtime/test_collaboration.py` (~400 lines)

**Manual Testing:**
- Open same document in two browser tabs (different users)
- Edit simultaneously, verify no conflicts
- Disconnect one client, edit, reconnect → verify sync
- Verify presence indicators show active users
- Test cursor tracking

**Success:** Real-time collaboration functional; no data loss; seamless multi-user editing

**Known Risk:** CRDT complexity high; extensive testing required for reliability

---

## COLLAB-004: Team Workflows (15-20 hours)

**Problem:** No team-specific features like shared agents, workflow templates, or team analytics.

**Inspiration:** Quivr's brain marketplace, AnythingLLM's team agent builder.

**Implementation:**
1. Create shared agent/workflow repository per workspace [5-6 hours]
2. Implement workflow templates and sharing [4-5 hours]
3. Add team analytics dashboard [4-5 hours]
4. Create team configuration management [2-3 hours]

**Team features:**
- **Shared agents:** Team-wide agents anyone can use
- **Workflow templates:** Pre-built workflows for common tasks
- **Team analytics:** Usage stats, popular queries, active members
- **Team settings:** Shared configurations, model preferences

**Shared agent repository:**
- Workspace-level agent library
- Version control for agents (track changes)
- Permission-based editing (admin can modify)
- Usage tracking (who's using which agents)

**Files:**
- `src/workspaces/agents.py` (shared agent management, ~300 lines)
- `src/workspaces/templates.py` (workflow templates, ~250 lines)
- `src/analytics/team_analytics.py` (team metrics, ~350 lines)
- `web-ui/src/routes/workspace/agents/+page.svelte` (~400 lines)
- `tests/workspaces/test_team_workflows.py` (~300 lines)

**Manual Testing:**
- Create shared agent in workspace
- Verify all members can use agent
- Create workflow template, share with team
- View team analytics dashboard
- Modify team settings, verify applied for all members

**Success:** Team workflows functional; shared resources accessible; team analytics useful

---

## COLLAB-005: Conversation Sharing (10-15 hours)

**Problem:** Valuable conversations private; no way to share insights with team.

**Inspiration:** Slack threads, Linear issue comments.

**Implementation:**
1. Add conversation persistence (already exists) [1 hour]
2. Implement conversation sharing UI [4-5 hours]
3. Create threaded comments on conversations [3-4 hours]
4. Add conversation search and filtering [2-3 hours]

**Conversation features:**
- **Share conversation:** Share entire query + response thread
- **Comments:** Team members can comment on conversations
- **Tagging:** Tag conversations for organization
- **Search:** Find conversations by content or tags
- **Bookmarking:** Save important conversations

**Files:**
- `src/conversations/sharing.py` (conversation sharing, ~200 lines)
- `src/conversations/comments.py` (threaded comments, ~250 lines)
- `web-ui/src/routes/conversations/[id]/+page.svelte` (~400 lines)
- `tests/conversations/test_sharing.py` (~200 lines)

**Manual Testing:**
- Run query, save conversation
- Share conversation with team member
- Add comment to shared conversation
- Search for conversation by content
- Verify permissions (only shared users can view)

**Success:** Conversation sharing functional; team can collaborate on insights

---

## COLLAB-006: Notifications & Activity Feed (15-20 hours)

**Problem:** No way to know when documents shared, comments added, or team activity happens.

**Implementation:**
1. Design notification system [3-4 hours]
2. Implement activity feed backend [5-6 hours]
3. Create notification UI and preferences [5-6 hours]
4. Add email notifications (optional) [2-3 hours]

**Notification types:**
- **Documents:** Shared with you, document updated
- **Comments:** New comment on your conversation
- **Mentions:** @mentioned in comment
- **Workspace:** Added to workspace, role changed
- **Agents:** Shared agent available

**Notification preferences:**
- In-app notifications (default)
- Email notifications (optional)
- Notification frequency (instant, daily digest)
- Granular control (enable/disable per type)

**Files:**
- `src/notifications/manager.py` (notification system, ~400 lines)
- `src/notifications/email.py` (email delivery, ~250 lines)
- `web-ui/src/lib/components/notifications/NotificationCenter.svelte` (~400 lines)
- `web-ui/src/routes/settings/notifications/+page.svelte` (~300 lines)
- `tests/notifications/test_notifications.py` (~300 lines)

**Manual Testing:**
- Share document, verify recipient notified
- Comment on conversation, verify notification
- @mention user, verify notification
- Configure notification preferences
- Test email notifications (if enabled)

**Success:** Notifications timely and relevant; users stay informed of team activity

---

## COLLAB-007: Privacy-Preserving End-to-End Encryption (Optional) (20-25 hours)

**Problem:** Collaboration introduces risk of data exposure; sensitive documents need extra protection.

**Status:** OPTIONAL - Implement only if strong user demand

**Implementation:**
1. Research E2EE for collaborative systems [4-5 hours]
2. Implement client-side encryption (documents, messages) [8-10 hours]
3. Create key management system (per-workspace keys) [5-6 hours]
4. Add encrypted search (limited functionality) [3-4 hours]

**E2EE architecture:**
- Each workspace has encryption key
- Documents encrypted client-side before upload
- Only workspace members with key can decrypt
- Server cannot read encrypted content
- Trade-off: Limits server-side search and analytics

**Privacy model:**
- **Encrypted:** Documents, conversations, comments
- **Not encrypted:** Metadata (titles, tags), user info
- **Key management:** Per-workspace keys, user-controlled

**Files:**
- `src/encryption/client_encryption.py` (client-side encryption, ~400 lines)
- `src/encryption/key_management.py` (key storage, ~300 lines)
- `web-ui/src/lib/encryption/crypto.ts` (client crypto, ~350 lines)
- `tests/encryption/test_e2ee.py` (~400 lines)

**Manual Testing:**
- Enable E2EE for workspace
- Upload encrypted document, verify server can't read
- Share encrypted document with team member
- Verify only workspace members can decrypt
- Test encrypted search (limited functionality)

**Success:** E2EE optional feature available; strong privacy guarantees; trade-offs documented

**Known Risk:** E2EE limits functionality (search, analytics); may confuse users; defer unless demanded

---

## Success Criteria

**Automated Tests:**
- [ ] Multi-user database schema migration successful
- [ ] Data isolation between workspaces enforced
- [ ] Permission checks prevent unauthorized access
- [ ] Real-time collaboration syncs without conflicts
- [ ] Shared agents accessible to team members
- [ ] Notifications delivered correctly
- [ ] E2EE encrypts/decrypts correctly (if implemented)
- [ ] All existing tests pass

**Manual Testing:**
- [ ] Migrate single-user to multi-user successfully
- [ ] Create workspace, invite 3+ members
- [ ] Share document, verify permission enforcement
- [ ] Edit document collaboratively with 2+ users
- [ ] Create shared agent, verify team can use
- [ ] Share conversation, add comments
- [ ] Receive notifications for team activity
- [ ] Enable E2EE, verify encryption (if implemented)

**Quality Gates:**
- [ ] Migration preserves 100% of existing data
- [ ] Permission checks add <50ms query latency
- [ ] Real-time collaboration supports 10+ concurrent users per document
- [ ] Notification delivery <5 seconds
- [ ] Team analytics update within 1 minute
- [ ] E2EE encryption/decryption <100ms per document (if implemented)
- [ ] Zero permission bypass vulnerabilities

---

## Known Risks

- **Complexity:** Multi-user systems significantly more complex; extensive testing required
- **Performance:** Permission checks may slow queries; optimize carefully
- **Real-time reliability:** WebSocket connections can be unstable; implement reconnection logic
- **Data migration:** Single-user → multi-user migration must be bulletproof; one mistake = data loss
- **E2EE trade-offs:** Encryption limits search and analytics; users may not understand trade-offs
- **Privacy vs collaboration:** Balancing privacy-first principles with team features challenging
- **Adoption:** Team features may not be demanded by primary user base (personal knowledge workers)

**Critical Decision:** Validate demand for collaboration features before full implementation. Consider releasing as optional "Team Edition" to avoid bloating personal use case.

---

## Next Steps

After v1.5 completion:
- **v2.0:** Enterprise & Applications (HIPAA/SOC2 compliance, desktop apps, embeddable widgets)

See: `roadmap/version/v2.0/README.md`

---

## Related Documentation

- [Previous Version](../v0.9/README.md) - Web UI completion
- [Next Version](../v2.0/README.md) - Enterprise and applications
- [Planning](../../planning/version/v1.5/) - Design goals for v1.5 (if exists)
- [Version Overview](../README.md) - Complete version comparison
- [Projects to Learn From](../../../research/projects-to-learn-from.md) - Onyx/Danswer team features, AnythingLLM collaboration

---

**Status:** Planned (subject to demand validation)

**Note:** This version represents a major pivot toward team collaboration. Carefully evaluate user demand and consider optional "Team Edition" packaging to avoid feature bloat for personal users.

---
