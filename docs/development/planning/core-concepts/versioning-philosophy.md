# Versioning Philosophy for ragged

**Status:** Planning

---

## Overview

This document defines ragged's versioning strategy, clarifying when breaking changes are acceptable and how we transition to API stability.

## Core Principle

**Breaking changes are encouraged before v1.0. Stability begins at v1.0.**

---

## Pre-1.0: Developer Beta

### Version Range: v0.1 through v0.9

**Status:** 🚧 **Developer Beta** - Expect breaking changes

#### What This Means

**Breaking changes are:**
- ✅ Expected
- ✅ Encouraged
- ✅ Necessary for rapid iteration
- ✅ Not a problem

**We can freely change:**
- API endpoints and parameters
- CLI command syntax
- Configuration file formats
- Database schemas
- UI components
- Internal architecture
- Dependencies

**Without:**
- Migration scripts
- Backward compatibility layers
- Deprecation warnings
- Version negotiation
- Supporting old versions

#### Why This Approach?

1. **Faster Development**
   - No backward compatibility burden
   - Focus on forward progress
   - Cleaner code without legacy support
   - Rapid experimentation

2. **Better Final Product**
   - Learn from mistakes early
   - Pivot when needed
   - Adopt better patterns
   - Avoid technical debt

3. **Honest Communication**
   - Clear expectations
   - No false stability promises
   - Transparent development
   - Community understands risks

4. **Academic Integrity**
   - Document what changed and why
   - Learn from evolution
   - Compare plan vs actual
   - Transparent process

---

## Version Numbering (Pre-1.0)

### Format: v0.X.Y

**v0.X** = Major feature milestone
- v0.1: MVP/Foundation
- v0.2: Enhanced Retrieval
- v0.3: Advanced Chunking
- v0.4: Adaptive Systems
- v0.5: Knowledge Graphs

**v0.X.Y** = Minor updates within milestone
- v0.2.0: Initial v0.2 release
- v0.2.1: Bug fixes
- v0.2.2: Small improvements

### Breaking Changes by Version

| Version | Expected Breaking Changes |
|---------|---------------------------|
| **v0.1 → v0.2** | CLI args, API endpoints, config format |
| **v0.2 → v0.3** | Config schema, chunking parameters |
| **v0.3 → v0.4** | API structure, response formats |
| **v0.4 → v0.5** | **Major**: Complete UI rebuild (Gradio → Svelte) |
| **v0.5 → v1.0** | Final breaking changes, then freeze |

---

## Communication Strategy

### Developer Beta Badge

**All documentation displays:**

```markdown
🚧 **Developer Beta** (v0.X)

Breaking changes expected. Not recommended for production use.
Pin to specific versions if using APIs.

v1.0 will be the first stable release.
```

**In README.md:**
```markdown
[![Status: Developer Beta](https://img.shields.io/badge/status-developer%20beta-yellow.svg)]()
```

### Release Notes Format

```markdown
# v0.3.0 Release Notes

## 🚨 Breaking Changes

### Configuration Format Changed
**Impact**: High
**Migration**: Manual config update required

Old format:
```yaml
chunking:
  size: 500
  overlap: 100
```

New format:
```yaml
chunking:
  strategy: "recursive"
  params:
    chunk_size: 500
    chunk_overlap: 100
```

**Why**: More flexible for multiple chunking strategies

### API Endpoint Renamed
**Impact**: Medium
**Migration**: Update client code

- Old: `POST /query`
- New: `POST /api/v0/query`

**Why**: Preparing for versioned API in v1.0

## ✨ New Features
[...]

## 🐛 Bug Fixes
[...]
```

### Deprecation Notices (Optional)

**For features we plan to remove:**

```python
import warnings

def old_function():
    warnings.warn(
        "old_function() is deprecated and will be removed in v0.4. "
        "Use new_function() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

**But**: Not required before v1.0. We can just remove things.

---

## User Recommendations

### For Early Adopters

**If you're using ragged pre-1.0:**

1. **Pin to specific versions**
   ```bash
   pip install ragged==0.2.0  # Exact version
   ```

2. **Expect to update code**
   - Read release notes carefully
   - Test upgrades in dev environment
   - Don't auto-upgrade in production

3. **Provide feedback**
   - Report breaking changes that hurt
   - Suggest better APIs
   - Help shape v1.0

4. **Don't use in production**
   - Wait for v1.0 if stability needed
   - Or pin versions and accept risk

### For API Consumers

**If building on ragged's API:**

```python
# Good: Pin to specific version
import ragged  # v0.2.0

# Defensive: Check version
if ragged.__version__ != "0.2.0":
    raise RuntimeError(f"Incompatible ragged version: {ragged.__version__}")

# Safe: Use version-specific imports
from ragged.v0_2 import RAGPipeline  # If we provide versioned modules
```

---

## v1.0: Stability Commitment

### Version 1.0.0 Milestone

**Status:** 🎯 **Stable Release** - Breaking changes require major version bump

#### What Changes at v1.0

**Before v1.0:**
- ❌ No API stability guarantees
- ❌ Breaking changes anytime
- ❌ No migration tools required

**At v1.0:**
- ✅ API stability promise
- ✅ Semantic versioning begins
- ✅ Migration guides provided
- ✅ Backward compatibility maintained
- ✅ Deprecation warnings before removal

#### Semantic Versioning (v1.0+)

**Format**: vMAJOR.MINOR.PATCH

**MAJOR** (v1.0.0 → v2.0.0)
- Breaking API changes
- Incompatible updates
- Major architecture changes
- **Requires** migration guide

**MINOR** (v1.0.0 → v1.1.0)
- New features
- Backward compatible additions
- Deprecations (with warnings)
- **No breaking changes**

**PATCH** (v1.0.0 → v1.0.1)
- Bug fixes only
- Security patches
- Documentation updates
- **Fully compatible**

---

## Migration Strategy (v1.0+)

### Deprecation Process

**Timeline**: 2 minor versions minimum

```
v1.0: Feature X current implementation
v1.1: Feature X deprecated (warnings added), Y introduced
v1.2: Feature X still works (warnings continue)
v2.0: Feature X removed, Y is standard
```

### Example Migration

```python
# v1.0: Old API
pipeline = RAGPipeline(config_file="config.yaml")
result = pipeline.query("question")

# v1.1: Deprecation warning added
pipeline = RAGPipeline.from_config("config.yaml")  # New way
result = pipeline.query("question")

# Old way still works but warns:
pipeline = RAGPipeline(config_file="config.yaml")
# DeprecationWarning: `config_file` parameter is deprecated.
# Use `RAGPipeline.from_config()` instead.
# This will be removed in v2.0.

# v2.0: Old way removed
pipeline = RAGPipeline.from_config("config.yaml")  # Only way
```

### Migration Tools (v1.0+)

**Provide migration scripts:**

```bash
# Automatic config migration
ragged migrate config v1.0 v2.0

# Database schema migration
ragged migrate database v1.5 v2.0

# API compatibility check
ragged check-compatibility --from v1.9 --to v2.0
```

---

## Breaking Change Categories

### High Impact (Requires Migration)

**Examples:**
- API endpoint structure changes
- Configuration file format changes
- Database schema changes
- CLI command syntax changes

**Required:**
- Migration guide
- Migration script (if possible)
- Clear changelog entry
- Version-specific documentation

### Medium Impact (Code Changes Needed)

**Examples:**
- Function signature changes
- Return value format changes
- Default behaviour changes
- Removed features

**Required:**
- Clear changelog entry
- Code examples (before/after)
- Deprecation warning (v1.0+)

### Low Impact (Transparent)

**Examples:**
- Internal refactoring
- Dependency updates
- Performance improvements
- Bug fixes that don't change behaviour

**Required:**
- Changelog mention
- No migration needed

---

## Version Support Policy

### Pre-1.0 Support

**Active Support:**
- Only latest v0.X version
- No backports to old versions
- No security patches for old versions

**Example:**
- v0.3.2 released → v0.2.x unsupported
- Security fix? Only in v0.3.3
- Want fix in v0.2? Upgrade to v0.3

### Post-1.0 Support

**Active Support:**
- Latest major version (v2.x)
- Previous major version (v1.x) for 6 months

**Security Support:**
- Latest major version: Ongoing
- Previous major version: 1 year
- Older versions: Community patches only

**Example (Future):**
```
v3.0 released:
├─ v3.x: Full support (new features, bug fixes, security)
├─ v2.x: Security patches only (6 months)
└─ v1.x: End of life (community patches welcome)
```

---

## Documentation Versioning

### Pre-1.0 Documentation

**Single version:**
- Docs reflect current code
- Old versions documented in git history
- No version selector needed

**Format:**
```
docs/
├── README.md                    # Current version
├── implementation/
│   ├── plan/                    # Planning docs
│   └── actual/                  # What was built
└── project-setup/               # Concepts
```

### Post-1.0 Documentation (Future)

**Multiple versions:**
```
docs/
├── latest/                      # Latest stable (v2.x)
├── v2/                          # v2.x docs
├── v1/                          # v1.x docs (archived)
└── dev/                         # Development version
```

**Version selector in UI:**
```
Viewing docs for: [v2.3 ▼]
                   └─ v2.3 (latest stable)
                   └─ v2.2
                   └─ v2.1
                   └─ v1.5 (LTS)
                   └─ dev (unstable)
```

---

## Git Tagging Strategy

### Pre-1.0 Tags

```bash
# Version tags
git tag -a v0.1.0 -m "v0.1.0: MVP Foundation"
git tag -a v0.2.0 -m "v0.2.0: Enhanced Retrieval + Web UI"
git tag -a v0.3.0 -m "v0.3.0: Advanced Chunking"

# Planning tags (documentation milestones)
git tag -a v0.0-plan-complete -m "Implementation plan complete"
git tag -a v0.2-plan -m "v0.2 planning complete"
```

### Post-1.0 Tags

```bash
# Stable releases
git tag -a v1.0.0 -m "v1.0.0: First Stable Release"
git tag -a v1.1.0 -m "v1.1.0: New features (backward compatible)"
git tag -a v1.1.1 -m "v1.1.1: Bug fixes"

# Pre-releases
git tag -a v1.2.0-beta.1 -m "v1.2.0 Beta 1"
git tag -a v1.2.0-rc.1 -m "v1.2.0 Release Candidate 1"
```

---

## Examples of Breaking Changes

### v0.4 → v0.5: UI Rebuild (Major Breaking Change)

**What Breaks:**
- Entire Gradio UI removed
- New Svelte UI is incompatible
- URL structure changes
- No migration path for UI customizations

**Communication:**
```markdown
# v0.5.0 Release Notes

## 🚨 MAJOR BREAKING CHANGE: UI Rebuilt

The entire web interface has been rebuilt using Svelte.

**Gradio UI is removed.** If you relied on Gradio:
1. Use v0.4.x (unsupported)
2. Build custom UI using our API
3. Migrate to new Svelte UI

**No automatic migration** - this is a clean rebuild.

**Why:** Gradio limitations prevented advanced features (GraphRAG
visualisation, developer mode, production polish).

**API unchanged** - CLI and programmatic access still work.
```

### v0.2 → v0.3: Config Format Change

**What Breaks:**
```yaml
# v0.2 config.yaml
chunking:
  size: 500
  overlap: 100

# v0.3 config.yaml
chunking:
  strategy: recursive
  params:
    chunk_size: 500
    chunk_overlap: 100
```

**Communication:**
```markdown
## 🚨 Breaking Change: Config Format

Configuration file structure changed to support multiple
chunking strategies.

**Migration:**
Update your `config.yaml` manually:
- Rename `size` → `params.chunk_size`
- Rename `overlap` → `params.chunk_overlap`
- Add `strategy: recursive`

**Why:** Preparing for semantic chunking in v0.3.
```

---

## FAQ

### Q: Can I use ragged in production before v1.0?

**A**: Not recommended. Breaking changes will happen. If you must:
1. Pin to exact version
2. Don't auto-upgrade
3. Test thoroughly before upgrading
4. Have rollback plan

### Q: Will you provide migration scripts?

**A**: Not before v1.0. Breaking changes are part of development.

At v1.0: Yes, migration tools will be provided.

### Q: How do I know what changed?

**A**: Read release notes carefully. All breaking changes will be documented.

### Q: Can you keep old APIs working?

**A**: No, not before v1.0. That would slow development.

At v1.0: Yes, deprecated APIs will continue working with warnings.

### Q: What if I built on v0.2 API?

**A**: You took the risk. Pin to v0.2.0 or update your code.

This is why we have the "Developer Beta" status.

---

## Principles Summary

### Pre-1.0 (Developer Beta)

1. **Break early, break often**
2. **No backward compatibility required**
3. **Focus on best final design**
4. **Communicate changes clearly**
5. **Document everything**

### Post-1.0 (Stable)

1. **API stability promise**
2. **Semantic versioning strictly**
3. **Migration guides always**
4. **Deprecation before removal**
5. **Long-term support**

---

## Timeline

| Phase | Version | Status | Breaking Changes |
|-------|---------|--------|------------------|
| **Planning** | v0.0 | Complete | N/A |
| **Phase 1** | v0.1 | Not started | N/A (first version) |
| **Phase 2** | v0.2 | Not started | ✅ Expected |
| **Phase 3** | v0.3 | Not started | ✅ Expected |
| **Phase 4** | v0.4 | Not started | ✅ Expected |
| **Phase 5** | v0.5 | Not started | ✅ Major (UI rebuild) |
| **Stable** | v1.0 | Not started | ❌ **Last breaking changes** |
| **Future** | v2.0+ | Future | Only on major versions |

---

## Conclusion

**ragged's versioning philosophy:**

**Pre-1.0:** Fast iteration, breaking changes welcome
- Allows us to build the best system
- Clear communication to users
- Academic transparency

**v1.0+:** Stability and trust
- API freeze
- Semantic versioning
- Migration support

**Current Status:** v0.0 (planning)
- Breaking changes will happen
- This is expected and encouraged
- v1.0 will be worth the wait

**Next**: See version-specific implementation guides.
