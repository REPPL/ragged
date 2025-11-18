# Version Lifecycle Workflow

**Purpose:** Define the standard workflow for version documentation through its lifecycle

**Last Updated:** 2025-11-18

---

## Overview

This document defines how version documentation transitions through states (planned → in-progress → complete/skipped) using **stable filenames** and **in-file status tracking only**.

**Core Principle:** Filenames never change based on status. Status is tracked exclusively through in-file headers.

---

## Lifecycle States

Version documentation progresses through these states:

| State | Emoji | Description |
|-------|-------|-------------|
| Planned | 📅 | Version planning complete, not yet started |
| In Progress | 🔄 | Active development underway |
| Complete | ✅ | Version released and documented |
| Skipped | ⏭️ | Version intentionally not implemented |

---

## Phase 1: Planning

### When

- High-level design goals established
- Features identified
- Success criteria defined

### Actions

**Create roadmap document:**
```
Location: docs/development/roadmap/version/vX.X.Y/README.md
Status: **Status**: 📅 PLANNED
```

**Example:**
```markdown
# Ragged v0.2.9 Roadmap - Stability & Performance

**Status:** 📅 PLANNED - Next target after v0.2.7-v0.2.8 complete

**Total Hours:** 42-53 hours (estimated)

**Focus:** Performance optimisation, stability improvements, production readiness

## Overview
[Planning content...]
```

### Checklist

- [ ] Roadmap created at `roadmap/version/vX.X.Y/README.md`
- [ ] Status set to `📅 PLANNED`
- [ ] Effort estimated in hours
- [ ] Success criteria defined
- [ ] Dependencies documented
- [ ] Master roadmap updated (`roadmap/version/README.md`)

---

## Phase 2: Development Starts

### When

- Development begins on planned version
- First code committed

### Actions

**Create implementation record:**
```
Location: docs/development/implementation/version/vX.X/vX.X.Y.md
Status: **Status**: 🔄 IN PROGRESS
```

**Update roadmap status:**
```
Location: docs/development/roadmap/version/vX.X.Y/README.md
Status: **Status**: 🔄 IN PROGRESS (Current Version)
```

**Example:**
```markdown
# v0.2.8 Implementation Record

**Status:** 🔄 IN PROGRESS (Current Version)

**Actual Hours:** TBD (estimated 40-60h)

**Started:** 2025-11-18

## Overview
[Implementation progress...]

## Completed Features
- ✅ Feature A (8h actual)
- 🔄 Feature B (in progress)
- 📅 Feature C (planned)
```

### Checklist

- [ ] Implementation record created at `implementation/version/vX.X/vX.X.Y.md`
- [ ] Status set to `🔄 IN PROGRESS` in both roadmap and implementation
- [ ] Started date recorded
- [ ] Roadmap linked to implementation record
- [ ] Implementation record linked to roadmap
- [ ] Master roadmap updated

---

## Phase 3: Development Completes

### When

- All planned features implemented
- Tests passing
- Documentation complete
- Version ready for release

### Actions

**Update implementation record:**
```
Status: **Status**: ✅ COMPLETE (Released YYYY-MM-DD)
```

**Update roadmap status:**
```
Status: **Status**: ✅ COMPLETE (Released YYYY-MM-DD)
```

**Example:**
```markdown
# v0.2.7 Implementation Record

**Status:** ✅ COMPLETE (Released 2025-11-17)

**Actual Hours:** 87h (estimated 80-100h)

**Started:** 2025-11-10
**Completed:** 2025-11-17

## Overview
Version 0.2.7 successfully refactored the CLI...

## Completed Features
- ✅ CLI Modularisation (14h actual)
- ✅ Folder Ingestion (8h actual)
- ✅ HTML Processing (12h actual)
[...]

## Lessons Learned
[...]
```

### Checklist

- [ ] Status updated to `✅ COMPLETE` in both roadmap and implementation
- [ ] Release date added
- [ ] Actual hours recorded
- [ ] All features marked complete
- [ ] Lessons learned documented
- [ ] Master roadmap updated
- [ ] CHANGELOG.md updated
- [ ] Git tag created

**IMPORTANT:** No file renaming occurs. The file stays as `vX.X.Y.md`.

---

## Phase 4: Version Skipped

### When

- Version intentionally not implemented
- Features deferred to later version
- Requirements changed

### Actions

**Update implementation record:**
```
Status: **Status**: ⏭️ SKIPPED - [Reason]
```

**Update roadmap status:**
```
Status: **Status**: ⏭️ SKIPPED - [Reason]
```

**Example:**
```markdown
# v0.2.6 Implementation Record

**Status:** ⏭️ SKIPPED - Critical bugs resolved in subsequent versions

**Reason:** The primary goals of v0.2.6 (bug fixes and stability) were addressed through patches in v0.2.7 and v0.2.8, making a dedicated v0.2.6 release unnecessary.

## Planned Features (Deferred)
- Performance optimisations → Moved to v0.2.9
- Additional testing → Integrated into v0.2.7

## Alternative Actions Taken
- Emergency patches applied directly to v0.2.5
- Enhanced testing added to v0.2.7 roadmap
```

### Checklist

- [ ] Status updated to `⏭️ SKIPPED` with clear reason
- [ ] Deferred features documented
- [ ] Alternative actions explained
- [ ] Master roadmap updated

---

## File Naming Conventions

### Stable Naming Pattern

**Roadmap:** `docs/development/roadmap/version/vX.X.Y/README.md`
**Implementation:** `docs/development/implementation/version/vX.X/vX.X.Y.md`

**Never:**
- ❌ `vX.X.Y-planned.md`
- ❌ `vX.X.Y-in-progress.md`
- ❌ `vX.X.Y-complete.md`
- ❌ `vX.X.Y-release-notes.md`
- ❌ `vX.X.Y-skipped.md`

**Always:**
- ✅ `vX.X.Y.md` (status tracked in-file only)

### Rationale

1. **Stable References:** Links never break when status changes
2. **Git History:** File history preserved through renames
3. **Simplicity:** Single source of truth for status (in-file header)
4. **Consistency:** Same pattern across all versions

---

## Status Tracking

### Single Source of Truth

Status is tracked in **three locations** but only **one is authoritative**:

1. **Individual file header** (authoritative)
   ```markdown
   **Status:** 🔄 IN PROGRESS
   ```

2. **Master roadmap** (`roadmap/version/README.md`)
   - Aggregates status from all versions
   - Updated when individual files change

3. **Implementation README** (`implementation/version/vX.X/README.md`)
   - Aggregates status for minor versions
   - Updated when individual files change

### Update Sequence

When status changes:
1. Update individual file first (authoritative source)
2. Update master roadmap second
3. Update implementation README third

---

## Cross-References

### Required Links

**In Roadmap:**
```markdown
**See:** [v0.2.7 Implementation Record](../../implementation/version/v0.2/v0.2.7.md)
```

**In Implementation:**
```markdown
**See:** [v0.2.7 Roadmap](../../roadmap/version/v0.2.7/README.md)
```

### Bi-directional Linking

Always maintain bi-directional links between:
- Roadmap ↔ Implementation
- Planning ↔ Roadmap
- Implementation ↔ Planning (via lineage.md)

---

## Examples

### New Version (v0.3.0)

**Step 1: Create Roadmap**
```bash
# Create directory
mkdir -p docs/development/roadmap/version/v0.3.0

# Create README.md
cat > docs/development/roadmap/version/v0.3.0/README.md << 'EOF'
# Ragged v0.3.0 Roadmap - Advanced RAG Features

**Status:** 📅 PLANNED

**Total Hours:** 50-65 hours (estimated)
[...]
EOF
```

**Step 2: Start Development**
```bash
# Create implementation record
cat > docs/development/implementation/version/v0.3/v0.3.0.md << 'EOF'
# v0.3.0 Implementation Record

**Status:** 🔄 IN PROGRESS

**Started:** 2025-11-20
[...]
EOF
```

**Step 3: Complete Version**
```bash
# Update status in both files
# roadmap/version/v0.3.0/README.md:
**Status:** ✅ COMPLETE (Released 2025-12-01)

# implementation/version/v0.3/v0.3.0.md:
**Status:** ✅ COMPLETE (Released 2025-12-01)
```

**No file renaming at any stage!**

---

## Related Documentation

- [Master Roadmap](../../../roadmap/version/README.md) - All version statuses
- [Implementation Records](../../../implementation/version/) - Completed work
- [Development Process](../) - Methodology overview
- [Time Logging](../../time-logs/README.md) - Actual hours tracking

---

## Migration from Old Pattern

**Old Pattern (Deprecated):**
```
implementation/version/v0.2/
├── v0.2.7-in-progress.md    ❌
└── v0.2.8-in-progress.md    ❌
```

**New Pattern (Current):**
```
implementation/version/v0.2/
├── v0.2.7.md  ✅ (Status: 🔄 IN PROGRESS)
└── v0.2.8.md  ✅ (Status: 🔄 IN PROGRESS)
```

**Migration Steps:**
1. Rename files to remove status suffix
2. Add `**Status**` header to file
3. Update all cross-references
4. Update master roadmap

---

**License:** GPL-3.0
