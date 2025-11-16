# Configuration System

The Personal Research Service uses a hierarchical configuration system that allows progressive customization through inheritance.

## Inheritance Hierarchy

```
Global defaults → Role base → Topic profile → Collection config → Runtime overrides
```

### Inheritance Example

Starting with a query using the "research" topic profile:

1. **Global defaults**: System-wide settings
2. **Role base**: `role/wrangler/default.yaml` (base Wrangler settings)
3. **Topic profile**: `topic/research/default.yaml` (academic optimisations)
4. **Collection config**: Collection-specific overrides (if any)
5. **Runtime overrides**: CLI flags (e.g., `--chunk-size 1024`)

Each layer can override settings from previous layers, allowing fine-grained control.

## Configuration Types

### Role Templates

Base configurations for each of the three roles:

- `role/wrangler/default.yaml` - Document processing defaults
- `role/librarian/default.yaml` - Retrieval and indexing defaults
- `role/researcher/default.yaml` - Generation and coordination defaults

**Purpose**: Establish sensible defaults for each role's responsibilities

**Location**: `~/.ragged/profiles/role/`

### Topic Profiles

Bundled configurations for all three roles, optimised for specific domains:

- **research**: Academic documents, comprehensive retrieval, formal citations
- **legal**: Legal documents, precise citations, hybrid search
- **technical**: Technical documentation, code-aware chunking

**Purpose**: Domain-specific optimisation across all roles

**Location**: `~/.ragged/profiles/topic/`

**Example** (`topic/research/default.yaml`):
```yaml
wrangler:
  chunking:
    strategy: semantic
    preserve_sections: true

librarian:
  retrieval:
    strategy: hybrid
    top_k: 15

researcher:
  llm:
    temperature: 0.5
  generation:
    citation_style: academic
```

### Personas

Curated subsets of the Private Vault for different contexts:

- **professional**: Formal, expert-level, detailed
- **student**: Educational, clear explanations
- **executive**: Concise, high-level, actionable

**Purpose**: Context-appropriate communication style

**Location**: `~/.ragged/profiles/persona/`

**Example** (`persona/professional.yaml`):
```yaml
vault_sections:
  - Background.education
  - Background.expertise
  - Background.role
  - Preferences

overrides:
  tone: formal
  complexity: expert
  verbosity: detailed
```

## Configuration Loading Process

### Step 1: Load Base Role Templates
```python
wrangler_config = load_role_template("wrangler", "default")
librarian_config = load_role_template("librarian", "default")
researcher_config = load_role_template("researcher", "default")
```

### Step 2: Apply Topic Profile (if specified)
```python
if topic_profile:
    apply_profile("topic", topic_profile, [wrangler_config, librarian_config, researcher_config])
```

### Step 3: Apply Collection Config (if specified)
```python
if collection_config:
    apply_overrides(collection_config)
```

### Step 4: Apply Runtime Overrides
```python
if cli_args:
    apply_runtime_overrides(cli_args)
```

### Step 5: Load Persona Context (if specified)
```python
if persona:
    persona_config = load_persona(persona)
    vault_context = extract_vault_sections(persona_config.vault_sections)
    apply_overrides(persona_config.overrides)
```

## Usage Examples

### Using a Topic Profile
```bash
ragged add document.pdf --topic research
```
Applies research-optimised settings for all three roles.

### Using a Persona
```bash
ragged query "Explain RAG systems" --persona professional
```
Uses formal tone, expert complexity, references professional background from Vault.

### Combining Topic + Persona
```bash
ragged query "Summarize this legal case" --topic legal --persona executive
```
Combines legal domain expertise with executive communication style.

### Runtime Overrides
```bash
ragged add document.pdf --topic technical --chunk-size 1024
```
Uses technical profile but overrides chunk size.

## Design Rationale

See [ADR-012: Configuration Inheritance](../decisions/adr-012-configuration-inheritance.md) for the full decision record.

**Key Benefits**:
- **Layered Customization**: Start with sensible defaults, override as needed
- **Domain Optimisation**: Topic profiles provide out-of-the-box optimisation
- **Context Awareness**: Personas enable appropriate communication style
- **Flexibility**: Every layer can be customized independently
- **Simplicity**: Simple cases work with defaults, complex cases support deep customization

## Related Documentation

- [Profile Templates](../profile-templates/README.md) - Example configurations
- [Terminology: Profiles vs Personas](../terminology/profiles-vs-personas.md) - Conceptual distinction
- [User Guide: Profiles and Personas](../../user-guides/features/profiles-and-personas.md) - How to use them
