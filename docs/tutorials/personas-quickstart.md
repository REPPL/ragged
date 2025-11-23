# Getting Started with Personas

## What are Personas?

Personas allow you to maintain separate user contexts within ragged. Each persona has its own:
- Interaction history
- Knowledge graph of topics and documents
- Focus areas and preferences
- Active projects

This enables seamless context switching for different use cases without cross-contamination of data.

## Why Use Personas?

**Use Cases:**
- **Researcher**: Track academic papers, research queries, and citations
- **Student**: Learning materials, course notes, and study resources
- **Developer**: Code documentation, API references, and technical specs
- **Writer**: Research notes, draft materials, and reference documents

Each persona maintains complete privacy and isolation from others.

## Quick Start

### 1. Create Your First Persona

```bash
ragged persona create researcher \
    --description "ML researcher focused on RAG systems" \
    --focus RAG \
    --focus "Neural Networks" \
    --focus "Information Retrieval"
```

This creates a persona named "researcher" with specific focus areas.

### 2. Switch to the Persona

```bash
ragged persona switch researcher
```

Now all your interactions will be associated with the "researcher" persona.

### 3. Verify Active Persona

```bash
ragged persona active
```

Output:
```
Active Persona: researcher
Description: ML researcher focused on RAG systems
Focus Areas: RAG, Neural Networks, Information Retrieval
Times Used: 1
```

### 4. Use Ragged with Persona Context

When you interact with ragged, your queries and document access are tracked:

```bash
ragged query "What is Retrieval-Augmented Generation?"
```

The system automatically:
- Records the interaction under "researcher" persona
- Tracks topic interest in "RAG"
- Builds knowledge graph connections
- Maintains searchable history

### 5. View Your Interaction History

```bash
ragged memory history --persona researcher --limit 10
```

### 6. View Knowledge Graph

```bash
ragged memory interests --persona researcher
```

Output shows topics you've queried about, with frequency and interest levels:
```
Topics of Interest:
- RAG (interest: 0.9, frequency: 5, last accessed: 2025-11-23)
- Neural Networks (interest: 0.7, frequency: 2, last accessed: 2025-11-23)
```

## Creating Multiple Personas

You can create as many personas as needed:

```bash
# Student persona
ragged persona create student \
    --description "Computer Science student" \
    --focus Python \
    --focus Algorithms \
    --project "CS101 Final Project"

# Developer persona
ragged persona create developer \
    --description "Backend developer" \
    --focus FastAPI \
    --focus PostgreSQL \
    --project "API Migration"
```

## Switching Between Personas

```bash
ragged persona switch student
ragged query "Explain quicksort algorithm"

ragged persona switch developer
ragged query "Best practices for FastAPI authentication"
```

Each persona maintains its own separate history and knowledge graph.

## Managing Personas

### List All Personas

```bash
ragged persona list
```

Output:
```
Personas (3):

1. researcher
   Description: ML researcher focused on RAG systems
   Focus: RAG, Neural Networks, Information Retrieval
   Times Used: 15

2. student
   Description: Computer Science student
   Focus: Python, Algorithms
   Projects: CS101 Final Project
   Times Used: 8

3. developer
   Description: Backend developer
   Focus: FastAPI, PostgreSQL
   Projects: API Migration
   Times Used: 12
```

### View Persona Details

```bash
ragged persona show researcher
```

### Delete a Persona

```bash
ragged persona delete student
```

**Warning:** This permanently deletes all data for the persona, including:
- All interaction history
- Knowledge graph data
- Document access records

You'll be prompted for confirmation unless you use `--yes`.

## Privacy & Data Control

### Export Your Data

Export all persona data in machine-readable JSON format (GDPR Article 20):

```bash
ragged memory export --persona researcher
```

Creates: `~/.ragged/memory/exports/researcher_20251123_143022.json`

### Clear Interaction History

```bash
ragged memory clear --persona researcher
```

Prompts for confirmation before deleting history.

### Complete Data Deletion

To completely remove all data for a persona:

```bash
ragged persona delete researcher
```

This implements GDPR Article 17 (Right to Erasure).

## Best Practices

1. **Use Descriptive Names**: Choose persona names that reflect their purpose
2. **Set Focus Areas**: Help the system understand context and priorities
3. **Track Projects**: Link queries to specific projects for better organisation
4. **Switch Intentionally**: Always verify active persona before querying
5. **Regular Exports**: Periodically export your data for backup

## Common Workflows

### Academic Research Workflow

```bash
# Set up researcher persona
ragged persona create researcher --focus "Machine Learning"

# Switch context
ragged persona switch researcher

# Add papers to knowledge base
ragged add research-papers/*.pdf

# Query with persona context
ragged query "Compare BERT and GPT architectures"

# View research interests over time
ragged memory interests
```

### Learning Workflow

```bash
# Student persona for coursework
ragged persona create student --focus Python --project "Data Structures"

ragged persona switch student

# Add course materials
ragged add course-materials/

# Study queries tracked separately
ragged query "Explain binary search trees"

# Review what you've learned
ragged memory history --limit 20
```

### Multi-Project Development

```bash
# Separate personas for different projects
ragged persona create api-project --focus FastAPI --project "API v2"
ragged persona create frontend --focus React --project "Dashboard UI"

# Context-aware queries
ragged persona switch api-project
ragged query "FastAPI dependency injection patterns"

ragged persona switch frontend
ragged query "React hooks best practices"
```

## Troubleshooting

### No Active Persona

If you see "No active persona set":

```bash
ragged persona switch <persona-name>
```

### Lost Track of Personas

```bash
ragged persona list
```

### Can't Remember What You Queried

```bash
ragged memory history --persona <persona-name>
```

### Want to Start Fresh

```bash
ragged memory clear --persona <persona-name>
```

## Next Steps

- Read the [Memory System User Guide](../guides/memory-system.md) for advanced features
- Explore the [Memory API Reference](../reference/memory-api.md) for programmatic access
- Review [Privacy Documentation](../guides/privacy.md) for data control details

---

**Privacy Note:** All persona data is stored locally in `~/.ragged/memory/` with full user control. No data is sent to external services.
