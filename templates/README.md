# ragged Templates

This directory contains Jinja2 templates for repeatable RAG workflows.

## Usage

```bash
# List available templates
ragged template list -d templates/examples

# Validate a template
ragged template validate templates/examples/simple_summary.j2

# Render a template
ragged template render templates/examples/simple_summary.j2 \
  -v document="research.pdf" \
  -v topic="Machine Learning" \
  -v status="Complete"

# Show template source
ragged template show templates/examples/simple_summary.j2
```

## Template Variables

Templates support standard Jinja2 syntax with these custom filters:

- `truncate_words(n)` - Truncate text to N words
- `chunk_text(size)` - Split text into chunks of size characters

## Example Templates

- `simple_summary.j2` - Basic document summary with variables
- More templates coming in future releases

## Creating Templates

Templates use `.j2` extension and standard Jinja2 syntax:

```jinja2
# My Template

{{ variable_name }}

{% for item in items %}
- {{ item }}
{% endfor %}
```

For advanced features (query, retrieve, summarise functions), see the template engine documentation.
