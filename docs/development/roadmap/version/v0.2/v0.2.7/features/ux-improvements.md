# User Experience Improvements (v0.2.7)

This document details the user experience improvements planned for v0.2.7.

**Total Estimated Time**: 42 hours

**Related Documentation:** [Main v0.2.7 Roadmap](../README.md)

---

## Part 1: User Experience Improvements (42 hours)

### UX-001: Seamless Model Switching

**Priority**: High
**Estimated Time**: 8 hours
**Impact**: High - Users can experiment with different models effortlessly

#### Current Limitation
- Must restart CLI/API to change models
- Requires manual config file editing
- No easy way to compare models
- Single model loaded at a time

#### Improvement

**Runtime Model Selection**:
```python
# CLI commands
ragged query "What is machine learning?" --model llama3.2:70b
ragged query "Quick question" --fast  # Auto-select fast model
ragged query "Complex analysis" --accurate  # Auto-select best model

# Interactive model selection (enhanced)
ragged config set-model --interactive  # Already exists, enhance UI

# List models with performance stats
ragged models list --show-stats
# Output:
# Available Models:
# ┌─────────────────────┬──────────┬───────────┬───────────────┐
# │ Model               │ Size     │ RAG Score │ Avg Speed     │
# ├─────────────────────┼──────────┼───────────┼───────────────┤
# │ llama3.3:70b        │ 42.5 GB  │ 9.5/10    │ 8.2 tok/sec   │
# │ llama3.2:latest     │ 2.0 GB   │ 7.5/10    │ 45.3 tok/sec  │
# │ mistral:latest      │ 4.4 GB   │ 8.0/10    │ 28.1 tok/sec  │
# └─────────────────────┴──────────┴───────────┴───────────────┘
```

**Model Pool (Load Multiple Models)**:
```python
# src/generation/model_pool.py (NEW FILE)
"""Model pool for managing multiple loaded models."""
from typing import Dict, Optional
import time
from collections import defaultdict
from src.generation.ollama_client import OllamaClient

class ModelPool:
    """
    Manage a pool of loaded models with LRU eviction.

    Keeps 2-3 models in memory for fast switching.
    Tracks usage statistics for model selection.
    """

    def __init__(self, max_models: int = 2):
        """
        Initialize model pool.

        Args:
            max_models: Maximum number of models to keep loaded
        """
        self.max_models = max_models
        self.models: Dict[str, OllamaClient] = {}
        self.last_used: Dict[str, float] = {}
        self.stats: Dict[str, dict] = defaultdict(
            lambda: {'queries': 0, 'total_time': 0, 'avg_tokens_per_sec': 0}
        )

    def get_model(self, model_name: str) -> OllamaClient:
        """
        Get model from pool, loading if necessary.

        Args:
            model_name: Name of model to get

        Returns:
            Ollama client for the model
        """
        # Return if already loaded
        if model_name in self.models:
            self.last_used[model_name] = time.time()
            return self.models[model_name]

        # Evict LRU model if pool is full
        if len(self.models) >= self.max_models:
            self._evict_lru_model()

        # Load new model
        logger.info(f"Loading model into pool: {model_name}")
        client = OllamaClient(model=model_name)

        # Warmup with empty request
        client.generate("test", context="test")

        self.models[model_name] = client
        self.last_used[model_name] = time.time()

        return client

    def _evict_lru_model(self):
        """Evict least recently used model from pool."""
        if not self.models:
            return

        # Find LRU model
        lru_model = min(self.last_used.items(), key=lambda x: x[1])[0]

        logger.info(f"Evicting model from pool: {lru_model}")
        del self.models[lru_model]
        del self.last_used[lru_model]

    def record_usage(
        self,
        model_name: str,
        duration: float,
        tokens_generated: int
    ):
        """Record model usage statistics."""
        stats = self.stats[model_name]
        stats['queries'] += 1
        stats['total_time'] += duration
        stats['avg_tokens_per_sec'] = tokens_generated / duration if duration > 0 else 0

    def get_stats(self) -> Dict[str, dict]:
        """Get usage statistics for all models."""
        return dict(self.stats)

    def get_fastest_model(self) -> Optional[str]:
        """Get fastest model based on historical performance."""
        if not self.stats:
            return None

        return max(
            self.stats.items(),
            key=lambda x: x[1]['avg_tokens_per_sec']
        )[0]

    def get_best_model(self) -> Optional[str]:
        """Get best quality model (largest parameter count)."""
        # Simple heuristic: larger models typically better
        # Could enhance with RAG suitability scoring
        from src.config.model_manager import ModelManager
        manager = ModelManager()
        return manager.select_best_model(list(self.models.keys()))
```

**Integration into CLI**:
```python
# src/main.py
from src.generation.model_pool import ModelPool

# Global model pool
model_pool = ModelPool(max_models=2)

@click.option("--model", help="Model to use for this query")
@click.option("--fast", is_flag=True, help="Use fastest available model")
@click.option("--accurate", is_flag=True, help="Use best quality model")
def query(query_text: str, model: str, fast: bool, accurate: bool):
    """Query with flexible model selection."""

    # Determine which model to use
    if model:
        model_name = model
    elif fast:
        model_name = model_pool.get_fastest_model() or settings.model
    elif accurate:
        model_name = model_pool.get_best_model() or settings.model
    else:
        model_name = settings.model

    # Get model from pool (loads if necessary)
    start = time.time()
    ollama_client = model_pool.get_model(model_name)

    # Generate answer
    answer = ollama_client.generate(query_text, context)
    duration = time.time() - start

    # Record usage stats
    tokens = len(answer.split())  # Rough estimate
    model_pool.record_usage(model_name, duration, tokens)

    # Display result
    console.print(f"[dim]Model: {model_name}[/dim]")
    console.print(answer)
```

#### Testing Requirements
- [ ] Test switching between models within same session
- [ ] Test model pool eviction works correctly
- [ ] Test --fast and --accurate flags select appropriate models
- [ ] Test performance stats tracking
- [ ] Benchmark model switching time (should be <2 seconds)

#### Files to Create
- `src/generation/model_pool.py` (~200 lines)
- `tests/generation/test_model_pool.py` (~150 lines)

#### Files to Modify
- `src/main.py` (add model selection flags)
- `src/web/api.py` (use model pool)

#### Acceptance Criteria
- ✅ Can switch models without restart
- ✅ Model pool keeps 2-3 models loaded
- ✅ Stats tracked for model performance
- ✅ --fast and --accurate flags work correctly

---

### UX-002: Multi-Collection Support

**Priority**: High
**Estimated Time**: 10 hours
**Impact**: High - Organise documents by project/topic

#### Current Limitation
- Single "default" collection only
- Can't separate work/personal documents
- No way to organise by project or topic
- Switching contexts requires separate ragged installs

#### Improvement

**Collection Management System**:
```python
# src/collection/manager.py (NEW FILE)
"""Collection management for organising documents."""
from typing import List, Optional, Dict
from pathlib import Path
from src.vectorstore.chroma_store import ChromaStore
from src.config.settings import Settings

class CollectionManager:
    """
    Manage multiple document collections.

    Collections allow organising documents by project, topic, or context.
    Each collection has its own vector store and BM25 index.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.data_dir = Path("data/collections")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create_collection(self, name: str, description: str = "") -> bool:
        """
        Create a new collection.

        Args:
            name: Collection name (alphanumeric, hyphens, underscores)
            description: Optional description

        Returns:
            True if created, False if already exists

        Raises:
            ValueError: If name is invalid
        """
        # Validate name
        if not name.replace('-', '').replace('_', '').isalnum():
            raise ValueError(
                f"Invalid collection name '{name}'. "
                "Use only letters, numbers, hyphens, and underscores."
            )

        # Check if exists
        if self.collection_exists(name):
            return False

        # Create collection directory
        coll_dir = self.data_dir / name
        coll_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata = {
            'name': name,
            'description': description,
            'created_at': str(datetime.now()),
            'document_count': 0
        }

        metadata_file = coll_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Initialize empty vector store
        store = ChromaStore(
            host=self.settings.chroma_host,
            port=self.settings.chroma_port,
            collection_name=name
        )

        logger.info(f"Created collection: {name}")
        return True

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections with metadata.

        Returns:
            List of collection info dictionaries
        """
        collections = []

        for coll_dir in self.data_dir.iterdir():
            if not coll_dir.is_dir():
                continue

            metadata_file = coll_dir / 'metadata.json'
            if not metadata_file.exists():
                continue

            with open(metadata_file) as f:
                metadata = json.load(f)

            # Get current document count
            store = ChromaStore(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                collection_name=metadata['name']
            )
            metadata['document_count'] = store.count()

            collections.append(metadata)

        return sorted(collections, key=lambda x: x['name'])

    def delete_collection(self, name: str, confirm: bool = False) -> bool:
        """
        Delete a collection and all its documents.

        Args:
            name: Collection name
            confirm: Safety confirmation flag

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If confirm is False (safety check)
        """
        if not confirm:
            raise ValueError(
                "Collection deletion requires confirm=True. "
                "This will permanently delete all documents in the collection."
            )

        if not self.collection_exists(name):
            return False

        # Delete from ChromaDB
        store = ChromaStore(
            host=self.settings.chroma_host,
            port=self.settings.chroma_port,
            collection_name=name
        )
        store.delete_collection()

        # Delete local data
        coll_dir = self.data_dir / name
        shutil.rmtree(coll_dir)

        logger.info(f"Deleted collection: {name}")
        return True

    def get_default_collection(self) -> str:
        """Get the default collection name from config."""
        config_file = Path("data/config/default_collection.txt")
        if config_file.exists():
            return config_file.read_text().strip()
        return "default"

    def set_default_collection(self, name: str):
        """Set the default collection."""
        if not self.collection_exists(name):
            raise ValueError(f"Collection '{name}' does not exist")

        config_file = Path("data/config/default_collection.txt")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(name)

        logger.info(f"Set default collection to: {name}")

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        coll_dir = self.data_dir / name
        return coll_dir.exists() and (coll_dir / 'metadata.json').exists()

    def export_collection(self, name: str, output_path: Path, format: str = 'json'):
        """
        Export collection to file.

        Args:
            name: Collection name
            output_path: Where to write export
            format: Export format ('json', 'csv')
        """
        if not self.collection_exists(name):
            raise ValueError(f"Collection '{name}' does not exist")

        # Get all documents from collection
        store = ChromaStore(
            host=self.settings.chroma_host,
            port=self.settings.chroma_port,
            collection_name=name
        )

        documents = store.get_all()

        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(documents, f, indent=2)
        elif format == 'csv':
            # Convert to CSV
            import csv
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['text', 'source', 'page'])
                writer.writeheader()
                for doc in documents:
                    writer.writerow({
                        'text': doc['text'],
                        'source': doc['metadata'].get('source', ''),
                        'page': doc['metadata'].get('page', '')
                    })

        logger.info(f"Exported collection '{name}' to {output_path}")

    def merge_collections(
        self,
        source_names: List[str],
        target_name: str
    ):
        """
        Merge multiple collections into one.

        Args:
            source_names: Collections to merge
            target_name: Name of merged collection
        """
        # Create target if doesn't exist
        if not self.collection_exists(target_name):
            self.create_collection(
                target_name,
                description=f"Merged from: {', '.join(source_names)}"
            )

        # Get target store
        target_store = ChromaStore(
            host=self.settings.chroma_host,
            port=self.settings.chroma_port,
            collection_name=target_name
        )

        # Copy documents from each source
        for source_name in source_names:
            if not self.collection_exists(source_name):
                logger.warning(f"Source collection not found: {source_name}")
                continue

            source_store = ChromaStore(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                collection_name=source_name
            )

            documents = source_store.get_all()

            # Add to target
            for doc in documents:
                target_store.add(
                    texts=[doc['text']],
                    embeddings=[doc['embedding']],
                    metadatas=[doc['metadata']]
                )

        logger.info(f"Merged {len(source_names)} collections into '{target_name}'")
```

**CLI Commands**:
```python
# src/main.py - new command group

@main.group()
def collection():
    """Manage document collections."""
    pass

@collection.command()
@click.argument("name")
@click.option("--description", help="Collection description")
def create(name: str, description: str):
    """Create a new collection."""
    manager = CollectionManager(settings)

    if manager.create_collection(name, description):
        console.print(f"[green]✓[/green] Created collection: {name}")
    else:
        console.print(f"[yellow]![/yellow] Collection already exists: {name}")

@collection.command()
def list():
    """List all collections."""
    manager = CollectionManager(settings)
    collections = manager.list_collections()

    table = Table(title="Collections")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Documents", justify="right")
    table.add_column("Created")

    for coll in collections:
        # Mark default collection
        name = coll['name']
        if name == manager.get_default_collection():
            name = f"{name} [green](default)[/green]"

        table.add_row(
            name,
            coll.get('description', ''),
            str(coll['document_count']),
            coll['created_at'][:10]
        )

    console.print(table)

@collection.command()
@click.argument("name")
def switch(name: str):
    """Set the default collection."""
    manager = CollectionManager(settings)
    manager.set_default_collection(name)
    console.print(f"[green]✓[/green] Switched to collection: {name}")

@collection.command()
@click.argument("name")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete(name: str, yes: bool):
    """Delete a collection."""
    manager = CollectionManager(settings)

    if not yes:
        confirm = click.confirm(
            f"Delete collection '{name}' and all its documents?",
            abort=True
        )

    if manager.delete_collection(name, confirm=True):
        console.print(f"[green]✓[/green] Deleted collection: {name}")
    else:
        console.print(f"[yellow]![/yellow] Collection not found: {name}")

@collection.command()
@click.argument("name")
@click.argument("output", type=click.Path())
@click.option("--format", type=click.Choice(['json', 'csv']), default='json')
def export(name: str, output: str, format: str):
    """Export collection to file."""
    manager = CollectionManager(settings)
    manager.export_collection(name, Path(output), format)
    console.print(f"[green]✓[/green] Exported to: {output}")

@collection.command()
@click.argument("sources", nargs=-1)
@click.option("--into", required=True, help="Target collection name")
def merge(sources: tuple, into: str):
    """Merge multiple collections."""
    manager = CollectionManager(settings)
    manager.merge_collections(list(sources), into)
    console.print(f"[green]✓[/green] Merged into: {into}")

# Update existing commands to support --collection flag
@click.option("--collection", help="Collection to use (default: current default)")
def add(files, collection: str):
    """Add documents to collection."""
    if collection:
        manager = CollectionManager(settings)
        # Temporarily override default collection
        original = manager.get_default_collection()
        manager.set_default_collection(collection)

    # ... existing add logic ...

    if collection:
        # Restore original default
        manager.set_default_collection(original)

@click.option("--collection", help="Collection to query")
def query(query_text, collection: str):
    """Query a specific collection."""
    # Similar temporary override logic
    ...
```

#### Migration Strategy

Auto-migrate existing documents to "default" collection on first run:
```python
# src/collection/migration.py (NEW FILE)
"""Migrate existing documents to collection system."""

def migrate_to_collections():
    """Migrate existing ragged installation to collection system."""
    # Check if already migrated
    migration_flag = Path("data/config/collections_migrated")
    if migration_flag.exists():
        return

    logger.info("Migrating to multi-collection system...")

    # Create default collection
    manager = CollectionManager(settings)
    manager.create_collection(
        "default",
        description="Default collection (migrated from v0.2.5)"
    )

    # All existing documents are already in "default" ChromaDB collection
    # Just need to create metadata

    logger.info("Migration complete")
    migration_flag.parent.mkdir(parents=True, exist_ok=True)
    migration_flag.touch()
```

#### Testing Requirements
- [ ] Test creating collections
- [ ] Test listing collections
- [ ] Test switching between collections
- [ ] Test deleting collections
- [ ] Test exporting collections
- [ ] Test merging collections
- [ ] Test migration from v0.2.5

#### Files to Create
- `src/collection/manager.py` (~400 lines)
- `src/collection/migration.py` (~100 lines)
- `tests/collection/test_manager.py` (~250 lines)

#### Files to Modify
- `src/main.py` (add collection commands and flags)
- `src/web/api.py` (support collection parameter)

#### Acceptance Criteria
- ✅ Can create and manage multiple collections
- ✅ Can switch between collections easily
- ✅ Can add/query specific collections
- ✅ Existing installations migrate smoothly
- ✅ Collection data persists across restarts

---

### UX-003: Enhanced Progress Indicators

**Priority**: Medium
**Estimated Time**: 4 hours
**Impact**: Medium - Better visibility into operations

#### Current State
Basic progress bars with minimal information.

#### Improvement

**Detailed Progress Reporting**:
```python
# src/utils/progress.py (NEW FILE)
"""Enhanced progress reporting."""
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)
from rich.console import Console

class EnhancedProgress:
    """Enhanced progress reporting with detailed feedback."""

    def __init__(self):
        self.console = Console()

    def process_document(self, file_path: Path):
        """Show detailed progress for document processing."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
        ) as progress:

            # Main task
            main_task = progress.add_task(
                f"[cyan]Processing {file_path.name}",
                total=4
            )

            # Step 1: Load
            progress.update(main_task, description=f"[cyan]Loading {file_path.name}")
            doc = load_document(file_path)
            size_mb = file_path.stat().st_size / 1024 / 1024
            pages = doc.metadata.get('page_count', 'N/A')
            self.console.print(f"  ├─ Loaded ({size_mb:.1f} MB, {pages} pages)")
            progress.advance(main_task)

            # Step 2: Chunk
            progress.update(main_task, description=f"[cyan]Chunking {file_path.name}")
            chunks = chunk_document(doc)
            avg_tokens = sum(len(c.text.split()) for c in chunks) // len(chunks)
            self.console.print(f"  ├─ Chunked ({len(chunks)} chunks, avg {avg_tokens} tokens)")
            progress.advance(main_task)

            # Step 3: Embed (with sub-progress)
            progress.update(main_task, description=f"[cyan]Embedding {file_path.name}")
            embed_task = progress.add_task(
                f"  └─ Embedding",
                total=len(chunks)
            )

            embeddings = []
            for chunk in chunks:
                emb = embed(chunk.text)
                embeddings.append(emb)
                progress.advance(embed_task)

            progress.remove_task(embed_task)
            progress.advance(main_task)

            # Step 4: Store
            progress.update(main_task, description=f"[cyan]Storing {file_path.name}")
            start = time.time()
            store_chunks(chunks, embeddings)
            duration = time.time() - start
            self.console.print(f"  └─ Stored (✓ {len(chunks)} chunks in {duration:.1f}s)")
            progress.advance(main_task)

        self.console.print(f"[green]✓[/green] Complete: {file_path.name}\n")

    def batch_process(self, files: List[Path]):
        """Show batch processing progress with ETA."""
        start_time = time.time()
        processed = 0

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Processing documents...",
                total=len(files)
            )

            for i, file in enumerate(files, 1):
                # Update with detailed stats
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta_seconds = (len(files) - processed) / rate if rate > 0 else 0

                progress.update(
                    task,
                    description=(
                        f"[cyan]Processing {i}/{len(files)} "
                        f"({i/len(files)*100:.0f}%) "
                        f"ETA: {eta_seconds//60:.0f}m {eta_seconds%60:.0f}s "
                        f"({rate:.1f} docs/sec)"
                    ),
                    completed=i
                )

                # Process file
                self.process_document(file)
                processed += 1
```

#### Integration

Update batch ingestion:
```python
# src/ingestion/batch.py
from src.utils.progress import EnhancedProgress

def ingest_batch(files: List[Path]):
    progress = EnhancedProgress()
    progress.batch_process(files)
```

#### Testing Requirements
- [ ] Test progress display for single file
- [ ] Test progress display for batch
- [ ] Test ETA calculation accuracy
- [ ] Test progress with errors (should continue)

#### Files to Create
- `src/utils/progress.py` (~150 lines)

#### Files to Modify
- `src/ingestion/batch.py`
- `src/main.py`

#### Acceptance Criteria
- ✅ Detailed progress for each processing step
- ✅ Accurate ETA for batch operations
- ✅ Clear visual feedback

---

### UX-004: Smart Query Suggestions

**Priority**: Low-Medium
**Estimated Time**: 6 hours
**Impact**: Medium - Help users discover capabilities

#### Concept
After ingestion, analyse documents and suggest relevant queries to help users get started.

#### Implementation

```python
# src/query/suggestions.py (NEW FILE)
"""Smart query suggestion system."""
from typing import List
from collections import Counter
import re

class QuerySuggester:
    """Generate query suggestions based on document content."""

    def suggest_queries_for_documents(
        self,
        documents: List[str]
    ) -> List[str]:
        """
        Generate suggested queries based on document corpus.

        Args:
            documents: List of document texts

        Returns:
            List of suggested query strings
        """
        suggestions = []

        # Extract common entities/topics
        topics = self._extract_topics(documents)

        # Generic suggestions
        suggestions.append("What are the main themes in these documents?")
        suggestions.append("Summarize the key findings")

        # Topic-specific suggestions
        for topic in topics[:3]:
            suggestions.append(f"Tell me about {topic}")
            suggestions.append(f"What is the relationship between {topic} and the other topics?")

        # Author-based if metadata available
        authors = self._extract_authors(documents)
        if authors:
            suggestions.append(f"List all work by {authors[0]}")

        return suggestions[:5]  # Top 5 suggestions

    def _extract_topics(self, documents: List[str]) -> List[str]:
        """Extract main topics using TF-IDF or keyword extraction."""
        # Simple implementation: most common noun phrases
        # Could enhance with KeyBERT, spaCy, etc.

        all_text = " ".join(documents)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', all_text)

        counter = Counter(words)
        return [word for word, count in counter.most_common(10)]

    def _extract_authors(self, documents: List[str]) -> List[str]:
        """Extract author names from document metadata or content."""
        # Look for author patterns
        authors = []
        for doc in documents:
            # Simple regex for "by Author Name" or "Author Name (2024)"
            matches = re.findall(r'(?:by|author:)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', doc)
            authors.extend(matches)

        counter = Counter(authors)
        return [author for author, count in counter.most_common(5)]
```

**CLI Integration**:
```python
# src/main.py - after ingestion
def add(files):
    # ... ingestion logic ...

    # Suggest queries
    console.print("\n[cyan]Suggested queries based on your documents:[/cyan]")
    suggester = QuerySuggester()
    suggestions = suggester.suggest_queries_for_documents(document_texts)

    for i, suggestion in enumerate(suggestions, 1):
        console.print(f"  {i}. {suggestion}")

    console.print("\n[dim]Run: ragged query \"<question>\"[/dim]")
```

#### Testing Requirements
- [ ] Test suggestion generation with various document types
- [ ] Test topic extraction accuracy
- [ ] Test author extraction

#### Files to Create
- `src/query/suggestions.py` (~200 lines)
- `tests/query/test_suggestions.py` (~100 lines)

#### Files to Modify
- `src/main.py` (show suggestions after add)

#### Acceptance Criteria
- ✅ Relevant suggestions generated after ingestion
- ✅ Suggestions help users discover capabilities

---

### UX-005-007: Additional UX Improvements

Due to length, I'll summarize the remaining UX improvements:

**UX-005: Interactive Query Refinement** (8 hours)
- Post-query options: more sources, different model, expand answer, citations only
- Conversation mode: `ragged chat` for interactive sessions
- Follow-up question support

**UX-006: Better Error Messages** (6 hours)
- Convert technical errors to user-friendly messages
- Provide actionable fixes
- Link to documentation/troubleshooting

**UX-007: Document Preview Before Ingestion** (4 hours)
- Show file info before ingesting
- Estimated chunks, processing time
- Metadata preview
- Confirmation prompt

---

---

## Related Documentation

- [Main v0.2.7 Roadmap](../README.md)
- [CLI Enhancements](./cli-enhancements.md)
- [Performance Optimisations](./performance-optimisations.md)
- [Configuration Management](./configuration-management.md)

---
