# Plugin System

📋 **Status: Planned for v1.0**

This directory will contain the plugin system, allowing users to extend ragged with custom functionality without modifying core code.

## Planned Components

### Plugin Interface (`interface.py`)
- Abstract base classes for plugin types
- Plugin lifecycle hooks (load, initialize, unload)
- Plugin metadata and versioning
- Dependency management

### Plugin Loader (`loader.py`)
- Discover plugins from directories
- Validate plugin compatibility
- Load and register plugins
- Handle plugin errors gracefully

### Plugin Registry (`registry.py`)
- Central registry of installed plugins
- Plugin configuration storage
- Enable/disable plugins
- Plugin update management

### Plugin Types (`types/`)
- Document loaders
- Embedding models
- Retrievers
- Re-rankers
- LLM backends
- Output formatters

## Plugin Types

### Document Loader Plugins

Load custom document formats:

```python
from ragged.plugins import DocumentLoaderPlugin

class CustomLoaderPlugin(DocumentLoaderPlugin):
    name = "custom-format-loader"
    version = "1.0.0"
    supported_formats = [".xyz"]

    def load(self, file_path: Path) -> Document:
        """Load custom format and return Document."""
        # Custom loading logic
        return Document(content=content, metadata=metadata)

    def validate(self, file_path: Path) -> bool:
        """Check if file can be loaded."""
        return file_path.suffix == ".xyz"
```

### Embedding Model Plugins

Add custom embedding models:

```python
from ragged.plugins import EmbeddingPlugin

class CustomEmbeddingPlugin(EmbeddingPlugin):
    name = "custom-embedder"
    version = "1.0.0"

    def __init__(self, config: dict):
        self.model = load_custom_model(config)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        return self.model.encode(texts)

    def embed_query(self, query: str) -> list[float]:
        """Generate query embedding."""
        return self.model.encode([query])[0]
```

### Retriever Plugins

Implement custom retrieval strategies:

```python
from ragged.plugins import RetrieverPlugin

class CustomRetrieverPlugin(RetrieverPlugin):
    name = "custom-retriever"
    version = "1.0.0"

    def retrieve(
        self,
        query: str,
        k: int = 5,
        **kwargs
    ) -> list[Chunk]:
        """Custom retrieval logic."""
        # Implementation
        return chunks
```

### LLM Backend Plugins

Add support for new LLM providers:

```python
from ragged.plugins import LLMPlugin

class CustomLLMPlugin(LLMPlugin):
    name = "custom-llm-provider"
    version = "1.0.0"
    supported_models = ["custom-model-7b", "custom-model-13b"]

    def generate(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> str:
        """Generate response using custom LLM."""
        # Call custom LLM API
        return response
```

### Output Formatter Plugins

Custom output formatting:

```python
from ragged.plugins import FormatterPlugin

class MarkdownFormatterPlugin(FormatterPlugin):
    name = "markdown-formatter"
    version = "1.0.0"

    def format(
        self,
        response: str,
        sources: list[Source],
        **kwargs
    ) -> str:
        """Format response with markdown."""
        # Add markdown formatting
        return formatted_response
```

## Plugin Discovery

Plugins discovered from multiple locations:

```
~/.ragged/plugins/          # User plugins
/usr/local/ragged/plugins/  # System plugins
./plugins/                  # Project-local plugins
```

Plugin structure:

```
my-plugin/
├── plugin.toml            # Plugin metadata
├── __init__.py            # Plugin entry point
├── loader.py              # Implementation
└── requirements.txt       # Plugin dependencies
```

`plugin.toml`:
```toml
[plugin]
name = "my-custom-loader"
version = "1.0.0"
author = "Your Name"
description = "Loads XYZ format documents"
ragged_version = ">=0.3.0,<2.0.0"

[plugin.entry_points]
document_loaders = ["my_plugin.loader:XYZLoader"]

[plugin.dependencies]
packages = ["custom-lib>=1.0.0"]
```

## Plugin Management CLI

```bash
# List installed plugins
ragged plugins list

# Install plugin from directory
ragged plugins install ./my-plugin

# Install from PyPI (if published)
ragged plugins install ragged-plugin-xyz

# Enable/disable plugin
ragged plugins enable my-custom-loader
ragged plugins disable my-custom-loader

# Update plugin
ragged plugins update my-custom-loader

# Remove plugin
ragged plugins remove my-custom-loader

# Show plugin info
ragged plugins info my-custom-loader
```

## Plugin Configuration

Plugins configurable via ragged config:

```yaml
# ~/.ragged/config.yml
plugins:
  enabled:
    - my-custom-loader
    - custom-embedder

  configs:
    custom-embedder:
      model_path: "/path/to/model"
      batch_size: 32

    my-custom-loader:
      encoding: "utf-8"
      chunk_on_load: true
```

## Plugin API

Full plugin API:

```python
from ragged.plugins import Plugin

class MyPlugin(Plugin):
    # Required metadata
    name: str = "my-plugin"
    version: str = "1.0.0"
    description: str = "Plugin description"
    author: str = "Your Name"

    # Lifecycle hooks
    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        pass

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass

    # Configuration
    def configure(self, config: dict) -> None:
        """Apply configuration to plugin."""
        pass

    def get_default_config(self) -> dict:
        """Return default configuration."""
        return {}

    # Validation
    def validate(self) -> bool:
        """Validate plugin integrity."""
        return True

    def check_compatibility(self, ragged_version: str) -> bool:
        """Check if compatible with ragged version."""
        return True
```

## Plugin Security

Security considerations:

1. **Sandboxing**: Plugins run in isolated environment
2. **Permission system**: Plugins declare required permissions
3. **Code review**: Official plugins reviewed before publishing
4. **Signature verification**: Verify plugin authenticity
5. **Dependency scanning**: Check for vulnerabilities

```toml
[plugin.permissions]
filesystem = ["read"]  # read, write, execute
network = ["external"]  # external, local, none
system = ["environment"]  # environment, processes
```

## Plugin Testing

Plugin testing framework:

```python
from ragged.plugins.testing import PluginTestCase

class TestMyPlugin(PluginTestCase):
    plugin_class = MyPlugin

    def test_load(self):
        """Test plugin loads correctly."""
        plugin = self.load_plugin()
        assert plugin.name == "my-plugin"

    def test_functionality(self):
        """Test plugin functionality."""
        # Plugin-specific tests
        pass
```

## Plugin Marketplace (Future)

Potential plugin marketplace:

- Browse available plugins
- User ratings and reviews
- Automatic updates
- Dependency resolution
- Security scanning

## Example Plugins

Built-in example plugins to ship with v1.0:

1. **Markdown Exporter** - Export results to markdown
2. **JSON API** - REST API for programmatic access
3. **Slack Notifier** - Send results to Slack
4. **Web Scraper** - Load content from URLs
5. **Code Highlighter** - Syntax highlighting for code chunks

## Architecture

```
ragged core
    ↓
Plugin Manager
    ↓
Plugin Registry
    ↓
    ├── Document Loader Plugins
    ├── Embedding Plugins
    ├── Retriever Plugins
    ├── LLM Plugins
    └── Formatter Plugins
```

## See Also

- [v1.0 Roadmap](../../docs/development/roadmaps/version/) (TBD)
- [Modularity Principles](../../docs/development/planning/core-concepts/modularity.md)
- [Architecture Planning](../../docs/development/planning/architecture/)

---

**Note:** This is a planning directory. Implementation will begin in v1.0 development cycle.
