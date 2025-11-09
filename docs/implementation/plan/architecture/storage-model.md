# Storage Model

The Personal Research Service uses two distinct storage systems with different ownership and purposes.

## Library (Librarian's Domain)

**Location**: `~/.ragged/library/`

The Library uses a collection-based architecture for organizing documents.

### Directory Structure

```
~/.ragged/
├── library/
│   ├── collections/
│   │   ├── default/
│   │   │   ├── index.json          # Collection metadata & hash index
│   │   │   └── documents/
│   │   │       └── [doc-id].json   # Individual document metadata
│   │   ├── research/
│   │   │   ├── index.json
│   │   │   └── documents/
│   │   └── projects/
│   │       ├── index.json
│   │       └── documents/
│   └── library.json                # Library-level metadata
└── chroma/                          # Vector embeddings (ChromaDB)
    └── chroma.sqlite3              # Internal ChromaDB storage
```

### Key Features

**Collections**: Logical grouping of related documents (e.g., 'research', 'projects')

**Document Metadata**: Each document has rich metadata including:
- Display name (smart-extracted from content)
- Original filename (preserved)
- Content hash (for duplicate detection)
- Chunk count and statistics

**Hash Index**: Fast duplicate detection using SHA256 content hashing

**Duplicate Detection**: Two-tier system
1. Exact hash matching (fast)
2. Similarity search (catches near-duplicates)

**Smart Naming**: Automatic extraction of meaningful names from:
1. PDF metadata titles
2. First headings (Markdown/HTML)
3. First substantial line
4. Sanitized filename (fallback)

### Ownership

- **Populated by**: Wrangler (processes and adds documents)
- **Managed by**: Librarian (indexes, retrieves, organizes)
- **Nature**: Shareable, can be backed up and transferred

## Private Vault (User's Domain)

**Location**: `~/.ragged/vault/private.yaml`

The Vault stores user's personal context, preferences, and background information.

### Structure

```yaml
Background:
  education: "PhD in Computer Science"
  expertise: ["Machine Learning", "NLP"]
  role: "Senior Research Scientist"

Preferences:
  tone: formal
  complexity: expert
  verbosity: concise

Output:
  citation_style: "APA 7th"
  code_style: "Google Python Style Guide"

Domain:
  primary_field: "AI Research"
  interests: ["RAG systems", "LLMs", "Knowledge Graphs"]

WorkingStyle:
  approach: "systematic and thorough"
  priorities: ["accuracy", "reproducibility"]

Privacy:
  data_retention: "minimal"
  external_api: false
```

### Dot Notation Access

Users can add/modify vault entries using dot notation:

```bash
ragged vault add "Background.education: PhD in AI"
ragged vault add "Preferences.tone: formal"
ragged vault add "Domain.interests: [RAG, LLMs]"
```

### Ownership

- **Owned by**: User (private, not shared)
- **Referenced by**: Personas (subsets for different contexts)
- **Nature**: Private, local only, never transmitted without permission

## Library vs Vault Distinction

| Aspect | Library | Vault |
|--------|---------|-------|
| **Content** | Documents, papers, data | User context, preferences |
| **Populated by** | Wrangler | User directly |
| **Managed by** | Librarian | User |
| **Used by** | Researcher (via Librarian) | Researcher (via Personas) |
| **Shareable** | Yes (can export) | No (private) |
| **Backed up** | Yes | User's choice |
| **Location** | `~/.ragged/library/` | `~/.ragged/vault/` |

## Design Rationale

See [ADR-008: Library vs Private Vault](../decisions/adr-008-library-vs-vault.md) for the full decision record.

**Key Benefits**:
- **Privacy**: User context never mixed with documents
- **Portability**: Library can be shared without exposing personal info
- **Flexibility**: Documents and user context evolve independently
- **Security**: Clear boundary for what's private vs shareable

## Related Documentation

- [Three-Role System](./three-role-system.md) - How roles interact with storage
- [Terminology: Library vs Vault](../terminology/library-vs-vault.md) - Conceptual distinction
- [Profile Templates](../profile-templates/README.md) - Examples of persona/vault usage
