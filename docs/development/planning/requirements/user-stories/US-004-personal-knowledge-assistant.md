# US-004: Personal Knowledge Assistant

**ID**: US-004
**Title**: Personal Knowledge Assistant
**Status**: ✅ Active
**Priority**: Medium
**Personas**: Casual (primary)
**Versions**: v0.2 - v1.0

---

## Overview

**As a** person managing everyday knowledge and information
**I want** a simple, fast local assistant that helps me organise notes, save web articles, and quickly find information
**So that** I can maintain a personal knowledge base without complexity, subscriptions, or privacy concerns

---

## Acceptance Criteria

### Simple Information Capture

#### AC-001: Quick Note Taking (v0.2)
**Given** a thought or piece of information
**When** I want to save it
**Then** the system should:
- ✅ Capture notes in < 3 seconds
- ✅ Require minimal formatting
- ✅ Support plain text
- ✅ Auto-save without prompting

**Test Coverage**: `tests/integration/test_quick_capture.py`

**Success Metric**: < 3 seconds from thought to saved note

---

#### AC-002: Web Article Archiving (v0.3)
**Given** interesting web articles
**When** I save a URL
**Then** the system should:
- ✅ Extract main content from webpage
- ✅ Remove ads and clutter
- ✅ Save in readable format
- ✅ Preserve links and images (optional)
- ✅ Store offline copy

**Test Coverage**: `tests/integration/test_web_archiving.py`

---

#### AC-003: Voice Notes (v0.5 - deferred to v1.1)
**Given** quick ideas while mobile
**When** I speak
**Then** the system should:
- 🚧 Transcribe voice to text
- 🚧 Store as searchable note
- 🚧 Support basic voice commands

**Deferred**: Voice features moved to v1.1+ based on complexity

---

### Effortless Organisation

#### AC-004: Auto-Tagging (v0.2)
**Given** saved notes and articles
**When** content is processed
**Then** the system should:
- ✅ Automatically suggest tags
- ✅ Categorise by topic
- ✅ Allow one-click tag acceptance
- ✅ Learn tagging preferences over time

**Test Coverage**: `tests/integration/test_auto_tagging.py`

**Success Metric**: 80%+ tag suggestion acceptance rate

---

#### AC-005: Smart Folders (v0.3)
**Given** growing collection of notes
**When** organising content
**Then** the system should:
- ✅ Create smart folders based on topics
- ✅ Auto-file notes to appropriate folders
- ✅ Support nested folder structure
- ✅ Allow drag-and-drop reorganisation

**Test Coverage**: `tests/integration/test_smart_folders.py`

---

#### AC-006: Minimal Configuration (v0.2)
**Given** initial setup
**When** starting to use ragged
**Then** the system should:
- ✅ Work with sensible defaults
- ✅ Require < 5 minutes to configure
- ✅ Auto-detect optimal settings
- ✅ Provide simple UI/CLI

**Test Coverage**: `tests/e2e/test_initial_setup.py`

---

### Fast Information Retrieval

#### AC-007: Instant Search (v0.2)
**Given** saved information
**When** I search
**Then** the system should:
- ✅ Return results in < 2 seconds
- ✅ Understand natural language
- ✅ Show relevant snippets
- ✅ Highlight matching terms

**Test Coverage**: `tests/performance/test_search_speed.py`

**Success Metric**: 95%+ of searches < 2 seconds

---

#### AC-008: Simple Filters (v0.2)
**Given** search results
**When** I want to narrow down
**Then** the system should support:
- ✅ Filter by date range
- ✅ Filter by tag
- ✅ Filter by source (note/web/document)
- ✅ One-click filters (no complex syntax)

**Test Coverage**: `tests/integration/test_search_filters.py`

---

#### AC-009: "I Remember..." Queries (v0.4)
**Given** vague memory of information
**When** I describe what I remember
**Then** the system should:
- ✅ Handle imprecise queries ("that article about cats I saved last month")
- ✅ Use temporal hints ("around March")
- ✅ Use contextual clues ("about gardening")
- ✅ Suggest likely matches

**Test Coverage**: `tests/e2e/test_fuzzy_memory_queries.py`

**Success Metric**: 75%+ success rate on vague queries

---

### Everyday Use Cases

#### AC-010: Recipe Management (v0.3)
**Given** saved recipes
**When** cooking
**Then** I can:
- ✅ Search for recipes by ingredients
- ✅ Tag recipes (quick, vegetarian, dessert, etc.)
- ✅ Save from web with one click
- ✅ View in clean, readable format

**Test Coverage**: `tests/e2e/test_recipe_management.py`

---

#### AC-011: Reading List (v0.3)
**Given** articles to read later
**When** saving content
**Then** the system should:
- ✅ Maintain "to read" queue
- ✅ Track what's been read
- ✅ Suggest reading based on interests
- ✅ Estimate reading time

**Test Coverage**: `tests/integration/test_reading_list.py`

---

#### AC-012: Personal Wiki (v0.4)
**Given** interconnected information
**When** creating notes
**Then** I can:
- ✅ Link notes together
- ✅ Create simple wiki-style pages
- ✅ Navigate between related notes
- ✅ View relationship graph (optional)

**Test Coverage**: `tests/integration/test_personal_wiki.py`

---

### Privacy & Simplicity

#### AC-013: Local-Only Storage (v0.2)
**Given** privacy concerns
**When** using the system
**Then** it must:
- ✅ Store all data locally
- ✅ Never connect to cloud services
- ✅ Provide clear data location
- ✅ Enable easy data export

**Test Coverage**: `tests/security/test_local_only.py`

---

#### AC-014: Simple Backup (v0.3)
**Given** valuable personal information
**When** backing up
**Then** the system should:
- ✅ One-click backup to folder
- ✅ Automatic scheduled backups (optional)
- ✅ Simple restore process
- ✅ Export to standard formats (Markdown, PDF)

**Test Coverage**: `tests/integration/test_backup.py`

---

#### AC-015: No Technical Knowledge Required (v0.2)
**Given** non-technical users
**When** using ragged
**Then** it should:
- ✅ Use plain language (no jargon)
- ✅ Provide helpful error messages
- ✅ Include simple tutorials
- ✅ Work without configuration

**Test Coverage**: User testing, documentation review

---

## Technical Constraints

### Platform Requirements
- ✅ Offline-first (v0.2)
- ✅ Local LLM (small, fast models)
- ✅ Minimal system requirements
- ✅ Simple installation

### Performance Requirements
- ✅ Note capture < 3 seconds (v0.2)
- ✅ Search results < 2 seconds (v0.2)
- ✅ Startup time < 5 seconds (v0.3)

### Usability Requirements
- ✅ Setup time < 5 minutes (v0.2)
- ✅ Zero configuration to start (v0.2)
- ✅ Clear, simple UI/CLI (v0.2)

---

## Success Metrics

### Quantitative
- **Note capture speed**: < 3 seconds
- **Search response time**: < 2 seconds
- **Setup time**: < 5 minutes
- **Tag suggestion acceptance**: > 80%
- **Vague query success**: > 75%

### Qualitative
- **Non-technical user satisfaction**: 4.5+ / 5
- **Daily usage rate**: 70%+ of users use daily
- **Recommendation rate**: 80%+ would recommend
- **Perceived simplicity**: "Very easy to use" rating > 85%

---

## Feature Roadmap

### v0.2 - Initial Release (Weeks 4-7)
**Completion**: 40% of US-004

**Features**:
- ✅ Quick note taking
- ✅ Auto-tagging
- ✅ Instant search
- ✅ Simple filters
- ✅ Local-only storage
- ✅ Minimal configuration

**Acceptance Criteria**: AC-001, AC-004, AC-006, AC-007, AC-008, AC-013, AC-015

---

### v0.3 - Enhanced Features (Weeks 8-11)
**Completion**: 65% of US-004

**Features**:
- ✅ Web article archiving
- ✅ Smart folders
- ✅ Recipe management
- ✅ Reading list
- ✅ Simple backup

**Acceptance Criteria**: AC-002, AC-005, AC-010, AC-011, AC-014

---

### v0.4 - Advanced Organisation (Weeks 12-15)
**Completion**: 85% of US-004

**Features**:
- ✅ "I remember..." fuzzy queries
- ✅ Personal wiki linking
- ✅ Improved organisation
- ✅ Usage learning

**Acceptance Criteria**: AC-009, AC-012

---

### v1.0 - Production (Weeks 16-20)
**Completion**: 100% of US-004

**Features**:
- ✅ Production performance
- ✅ Complete documentation
- ✅ User tutorials
- ✅ All features polished

**Acceptance Criteria**: All AC complete

---

## Related Personas

### Primary: Casual
**Definition**: [Casual Persona](../../core-concepts/personal-memory-personas.md#casual-persona)

**Characteristics**:
- Non-technical user
- Wants simple, fast tools
- Values ease of use over features
- Needs minimal setup
- Privacy-conscious but not paranoid

**Configuration**:
```yaml
persona: casual
response_style: conversational
detail_level: concise
preferred_model_tier: fast
memory_scope: shared
auto_features:
  tagging: enabled
  filing: enabled
  suggestions: enabled
```

---

## Cross-References

### Implementation
- [Casual Persona](../../core-concepts/personal-memory-personas.md#casual-persona)
- [Fast Tier Models](../../core-concepts/hardware-optimisation.md#performance-tiers)

### Architecture
- [Simple UI/CLI](../../architecture/README.md)
- [Web Content Extraction](../../core-concepts/)

### Testing
- [User Experience Testing](../../core-concepts/testing-strategy.md)
- [Performance Testing](../../core-concepts/testing-strategy.md#performance-testing)

---

## Implementation Notes

### Web Content Extraction

```python
class WebArchiver:
    """Extract and save web articles"""

    def archive_url(self, url: str) -> Document:
        """
        Archive web page for offline reading

        Uses readability.js approach to extract main content
        """
        # Fetch page
        response = requests.get(url)

        # Extract main content
        doc = readability.Document(response.text)

        return Document(
            content=doc.summary(),
            metadata={
                'title': doc.title(),
                'url': url,
                'archived_date': datetime.now(),
                'source': 'web'
            }
        )
```

### Fast Search Optimisation

```python
class CasualSearchEngine:
    """Optimised for casual persona (speed over sophistication)"""

    def __init__(self):
        # Use fast tier model
        self.model = "llama3.2:8b"
        # Simple embedding model
        self.embedder = "nomic-embed-text"

    def search(self, query: str, filters: dict = None) -> list[Result]:
        """
        Fast search optimised for casual use

        Target: < 2 seconds
        """
        # Quick embedding
        query_vector = self.embedder.embed(query)

        # Fast vector search
        results = self.vector_store.search(
            query_vector,
            top_k=10,
            filters=filters
        )

        # Minimal re-ranking for speed
        return results[:5]
```

---

## Dependencies

### External
- **readability-lxml**: Web content extraction
- **Ollama**: Fast tier models (8B)
- **ChromaDB**: Simple vector storage

### Internal
- Casual persona (v0.2)
- Fast tier routing (v0.2)
- Document processing (v0.2)

---

## Risks & Mitigations

### Risk 1: User Complexity
**Risk**: Features may become too complex for casual users
**Impact**: High - Core value proposition
**Mitigation**:
- User testing with non-technical users
- Progressive disclosure of features
- Simple defaults, advanced options hidden
- Regular UX reviews

### Risk 2: Performance on Lower-End Hardware
**Risk**: May be slow on older computers
**Impact**: Medium - User experience
**Mitigation**:
- Use smallest viable models (7B-8B)
- Optimise database queries
- Test on mid-range hardware
- Provide performance tuning guide

### Risk 3: Web Content Extraction Quality
**Risk**: Some websites may not extract cleanly
**Impact**: Medium - Web archiving feature
**Mitigation**:
- Use proven extraction library (readability)
- Manual fallback for problem sites
- Allow saving full HTML as backup
- User can edit extracted content

---

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-09 | 1.0 | Initial user story creation for Casual persona | Claude |

---

**Status**: ✅ Active
**Next Review**: v0.2 milestone
**Owner**: Product/Requirements
