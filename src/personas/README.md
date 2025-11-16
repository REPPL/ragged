# Persona System

📋 **Status: Planned for v0.3**

This directory will contain the persona system, allowing ragged to adapt its behaviour and responses based on user-selected personas (e.g., Researcher, Developer, Casual).

## Planned Components

### Persona Definitions (`definitions.py`)
- Pre-defined persona configurations
- Persona characteristics (tone, detail level, citation style)
- Custom persona support

### Persona Manager (`manager.py`)
- Load and switch between personas
- Apply persona settings to generation
- Persona-specific prompts and templates

### Persona Adapters (`adapters.py`)
- Adapt retrieval based on persona
- Modify chunk selection strategy
- Adjust response formatting

## Persona Types

### Researcher
- **Characteristics:** Detailed, academic tone, comprehensive citations
- **Retrieval:** Broad context, multiple sources
- **Generation:** Structured, methodical, references research papers
- **Citations:** IEEE format, detailed source attribution

### Developer
- **Characteristics:** Concise, code-focused, practical examples
- **Retrieval:** Code snippets prioritised, API docs
- **Generation:** Step-by-step, includes code blocks
- **Citations:** Link to documentation, line numbers

### Casual
- **Characteristics:** Conversational, simplified explanations
- **Retrieval:** Core concepts, summarised information
- **Generation:** Natural language, analogies, less technical jargon
- **Citations:** Simplified references

### Custom
- **Characteristics:** User-defined settings
- **Retrieval:** Configurable strategy
- **Generation:** Custom prompts
- **Citations:** User preference

## Architecture

```python
# Planned interface (subject to change)

class Persona:
    def __init__(
        self,
        name: str,
        tone: str,
        detail_level: str,
        citation_style: str,
        retrieval_k: int,
        generation_template: str
    ):
        self.name = name
        self.tone = tone
        # ... other attributes

class PersonaManager:
    def __init__(self):
        self.personas = self._load_personas()
        self.current_persona = self.personas["default"]

    def switch_persona(self, persona_name: str) -> None:
        """Switch to a different persona."""
        pass

    def apply_to_retrieval(self, query: str) -> RetrievalStrategy:
        """Get retrieval strategy for current persona."""
        pass

    def apply_to_generation(self, context: str) -> GenerationConfig:
        """Get generation config for current persona."""
        pass
```

## Configuration

Personas configurable via:

```yaml
# ~/.ragged/config.yml
personas:
  default: "researcher"
  custom:
    my_persona:
      tone: "professional"
      detail_level: "high"
      citation_style: "APA"
      retrieval_k: 7
      generation_template: "custom_prompt.txt"
```

## CLI Integration

```bash
# Switch persona
ragged persona set researcher

# List available personas
ragged persona list

# Create custom persona
ragged persona create --name my_persona --template researcher

# Query with specific persona
ragged query "What is RAG?" --persona developer
```

## Persona-Specific Prompts

Each persona will have tailored prompt templates:

```
# researcher.txt
You are a research assistant helping an academic researcher.
Provide comprehensive, well-cited answers with attention to detail.
Include methodology, limitations, and alternative viewpoints where relevant.
Format citations in IEEE style.

Context from documents:
{context}

Question: {question}

Provide a thorough, academic response:
```

## Model Routing

Personas can specify preferred models:

```yaml
researcher:
  preferred_models:
    - "llama3.1:70b"  # Larger model for detailed analysis
    - "qwen2.5:32b"

developer:
  preferred_models:
    - "codellama:34b"  # Code-specialised model
    - "deepseek-coder:33b"

casual:
  preferred_models:
    - "llama3.2:3b"  # Smaller, faster model
```

## Memory Integration

Personas can have separate memory spaces:
- Researcher persona remembers academic discussions
- Developer persona remembers code queries
- Separate context windows per persona

## Testing

- Unit tests for each persona type
- Integration tests for persona switching
- Prompt quality tests
- User preference persistence tests

## See Also

- [v0.3 Roadmap](../../docs/development/roadmaps/version/v0.3.0/)
- [Generation Module](../generation/)
- [Architecture Planning](../../docs/development/planning/architecture/)

---

**Note:** This is a planning directory. Implementation will begin in v0.3 development cycle.
