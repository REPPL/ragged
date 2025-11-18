# Ragged v0.2.7 Roadmap - UX & Performance

**Status:** Planned

**Total Hours:** 137-151 hours (AI implementation)

**Focus:** User experience, performance optimisation, CLI enhancements, quality of life

**Breaking Changes:** Multi-collection system (migration provided)

**Implementation Note:** Due to size (137-151 hours), implement in 5-6 focused sessions of 20-30 hours each

## Overview

Version 0.2.7 transforms ragged from a functional RAG system into a **delightful** one. This release focuses on user experience improvements and performance optimisations that provide immediate, measurable benefits.

**Key Goals**:
- 2-4x faster batch processing (async operations)
- 50-90% faster queries (caching)
- Seamless model switching without restarts
- Multi-collection document organisation
- Better user guidance and feedback
- Comprehensive CLI capabilities (document management, advanced queries, debugging)

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

## Part 2: Performance Optimizations (37 hours)

### PERF-001: Embedding Caching

**Priority**: High
**Estimated Time**: 5 hours
**Impact**: 50-90% faster repeat queries

#### Current State
Every query re-embeds the same text, wasting computation.

#### Solution

**LRU Cache for Query Embeddings**:
```python
# src/embeddings/cache.py (NEW FILE)
"""Embedding caching system."""
from functools import lru_cache
import hashlib
import pickle
from pathlib import Path
from typing import Optional
import numpy as np

class EmbeddingCache:
    """
    Persistent cache for embeddings.

    Stores embeddings on disk to avoid re-computation across sessions.
    """

    def __init__(self, cache_dir: Path = Path("data/cache/embeddings")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text + model combination."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[np.ndarray]:
        """Get cached embedding if exists."""
        key = self.get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.pkl"

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        return None

    def set(self, text: str, model: str, embedding: np.ndarray):
        """Cache an embedding."""
        key = self.get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.pkl"

        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)

    def clear(self):
        """Clear all cached embeddings."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

        logger.info("Cleared embedding cache")
```

**Integration into Embedders**:
```python
# src/embeddings/base.py
from src.embeddings.cache import EmbeddingCache

class BaseEmbedder:
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        if use_cache:
            self.cache = EmbeddingCache()

    def embed(self, text: str) -> np.ndarray:
        """Embed text with caching."""
        # Check cache first
        if self.use_cache:
            cached = self.cache.get(text, self.model_name)
            if cached is not None:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached

        # Compute embedding
        embedding = self._embed_internal(text)

        # Store in cache
        if self.use_cache:
            self.cache.set(text, self.model_name, embedding)

        return embedding
```

#### Testing Requirements
- [ ] Test cache hit/miss behaviour
- [ ] Test cache persistence across sessions
- [ ] Benchmark query speed with/without cache
- [ ] Test cache clearing

#### Files to Create
- `src/embeddings/cache.py` (~150 lines)
- `tests/embeddings/test_cache.py` (~100 lines)

#### Files to Modify
- `src/embeddings/base.py`
- `src/embeddings/sentence_transformer.py`
- `src/embeddings/ollama_embedder.py`

#### Acceptance Criteria
- ✅ 50-90% faster repeat queries
- ✅ Cache persists across sessions
- ✅ Cache can be cleared via CLI

---

### PERF-002-006: Additional Performance Improvements

**PERF-002: Async Document Processing** (12 hours)
- Parallel processing of multiple documents
- 2-4x faster batch ingestion
- Async embedding generation

**PERF-003: Lazy Model Loading** (6 hours)
- Unload models after inactivity timeout
- Reduced memory footprint (400MB → 100MB idle)
- Automatic reload on next use

**PERF-004: BM25 Index Persistence** (3 hours)
- Save/load BM25 index to disk
- Instant startup vs 10-30s rebuild
- Incremental index updates

**PERF-005: Chunking Optimisation** (5 hours)
- Batch token counting
- Estimate-then-verify approach
- 2x faster chunking

**PERF-006: Vector Store Query Optimisation** (6 hours)
- Query batching where possible
- Connection pooling for ChromaDB
- 30% faster multi-query scenarios

---

## Part 3: Configuration Management (10 hours)

### CONFIG-001: Runtime Configuration Updates

**Priority**: Medium
**Estimated Time**: 4 hours

Allow config updates without file editing:
```python
ragged config set chunk_size 600  # Immediate effect
ragged config set retrieval_k 10  # Persists to file
ragged config reset chunk_size   # Back to default
ragged config validate           # Check all settings
```

### CONFIG-002: Configuration Profiles

**Priority**: Medium
**Estimated Time**: 6 hours

Create and switch between config profiles:
```python
ragged config profile create fast
ragged config profile use fast
ragged config set chunk_size 300 --profile fast

ragged query "..." --profile fast
```

---

## Part 4: CLI Enhancements (48-62 hours)

This part adds 11 new CLI capabilities that transform ragged into a comprehensive, production-ready tool. These enhancements focus on usability, document management, and troubleshooting.

**Related Documentation:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md)

---

### CLI-001: Advanced Search & Filtering

**Priority**: High

**Estimated Time**: 3-4 hours

**Impact**: High - Essential for finding documents in large knowledge bases

#### Description
Enhanced search capabilities for finding documents using multiple filter criteria (metadata, content type, date ranges, similarity thresholds).

#### Command Syntax
```bash
# Search by metadata
ragged search --tag python --author "John Doe" --after 2025-01-01

# Search by content type
ragged search --type pdf --min-size 1MB --max-size 10MB

# Search by embedding similarity
ragged search "machine learning" --similarity 0.8

# Combined filters
ragged search --tag research --type pdf --after 2025-01-01 \
  --sort-by date --limit 10
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/search.py` - Enhanced search command
  - `tests/cli/test_search.py` - Comprehensive test suite

- **Files to Modify**:
  - `ragged/core/storage.py` - Add filter query methods
  - `ragged/core/models.py` - Add filter data models

- **Dependencies**: ChromaDB metadata filtering, Click argument parsing, date utilities

#### Testing Requirements
- Unit tests for each filter type
- Integration tests for combined filters
- Edge cases: empty results, invalid dates, missing metadata
- Performance tests with large knowledge bases

#### Acceptance Criteria
- ✅ All filter types work correctly
- ✅ Filters can be combined
- ✅ Results sorted and limited appropriately
- ✅ Clear error messages for invalid filters

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#1-advanced-search--filtering) for full specification

---

### CLI-002: Metadata Management

**Priority**: High

**Estimated Time**: 4-5 hours

**Impact**: High - Manage metadata without re-ingesting documents

#### Description
Commands for viewing, updating, and managing document metadata without re-ingesting documents. Supports individual and batch operations.

#### Command Syntax
```bash
# View metadata
ragged metadata show doc_id_123

# Update metadata
ragged metadata update doc_id_123 \
  --tag "machine-learning" \
  --author "Jane Smith" \
  --custom-field value

# Batch update
ragged metadata update --tag old_tag --replace-tag new_tag

# Delete metadata fields
ragged metadata delete doc_id_123 --field custom_field
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/metadata.py` - New command group
  - `tests/cli/test_metadata.py` - Test suite

- **Files to Modify**:
  - `ragged/core/storage.py` - Metadata CRUD operations
  - `ragged/core/models.py` - Metadata validation models

- **Dependencies**: ChromaDB metadata API, Pydantic validation, Click command groups

#### Testing Requirements
- Unit tests for metadata operations
- Integration tests for batch updates
- Validation tests for metadata schemas
- Rollback tests for failed updates

#### Acceptance Criteria
- ✅ Can view and update individual metadata
- ✅ Batch operations work correctly
- ✅ Validation prevents invalid metadata
- ✅ Changes persist across restarts

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#2-metadata-management) for full specification

---

### CLI-003: Bulk Operations

**Priority**: Medium

**Estimated Time**: 5-6 hours

**Impact**: Medium-High - Essential for large-scale document management

#### Description
Efficient batch operations for ingesting, updating, or deleting multiple documents with parallel processing and progress tracking.

#### Command Syntax
```bash
# Bulk ingest from directory
ragged ingest /path/to/docs --recursive --workers 4

# Bulk delete by filter
ragged delete --tag deprecated --dry-run
ragged delete --tag deprecated --confirm

# Bulk re-embed
ragged re-embed --collection research --model new-model
```

#### Implementation
- **Files to Create**:
  - `ragged/core/processing.py` - Worker pool implementation
  - `tests/core/test_bulk_operations.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/ingest.py` - Add parallel processing
  - `ragged/cli/commands/delete.py` - Add bulk delete
  - `ragged/utils/progress.py` - Enhanced progress bars

- **Dependencies**: Python multiprocessing, Rich/tqdm progress bars, transaction handling

#### Testing Requirements
- Unit tests for worker pool
- Integration tests for parallel ingestion
- Error handling tests (partial failures)
- Performance benchmarks

#### Acceptance Criteria
- ✅ Parallel processing faster than sequential
- ✅ Progress tracking accurate
- ✅ Errors don't crash entire batch
- ✅ --dry-run shows what would happen

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#3-bulk-operations) for full specification

---

### CLI-004: Export/Import Utilities

**Priority**: Medium

**Estimated Time**: 6-8 hours

**Impact**: High - Critical for backup, migration, and sharing

#### Description
Tools for exporting and importing knowledge bases in multiple formats (JSON, CSV, archive), supporting backup, migration, and sharing scenarios.

#### Command Syntax
```bash
# Export entire knowledge base
ragged export backup.tar.gz --format archive

# Export specific collection
ragged export research.json --collection research --format json

# Import knowledge base
ragged import backup.tar.gz --merge
ragged import backup.tar.gz --replace --confirm

# Export metadata only
ragged export metadata.csv --metadata-only --format csv
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/export.py` - Export command
  - `ragged/cli/commands/import.py` - Import command
  - `ragged/core/backup.py` - Backup/restore logic
  - `tests/cli/test_export_import.py` - Test suite

- **Files to Modify**:
  - `ragged/core/storage.py` - Add export methods
  - `ragged/core/models.py` - Serialization models

- **Dependencies**: Archive handling (tarfile, zipfile), JSON/CSV libraries, ChromaDB backup

#### Testing Requirements
- Round-trip tests (export → import)
- Format validation tests
- Merge vs. replace behaviour tests
- Large knowledge base tests

#### Acceptance Criteria
- ✅ Can export and import without data loss
- ✅ Multiple formats supported (JSON, CSV, archive)
- ✅ Merge mode preserves existing data
- ✅ Replace mode with safety confirmation

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#4-exportimport-utilities) for full specification

---

### CLI-005: Output Format Options

**Priority**: High

**Estimated Time**: 3-4 hours

**Impact**: High - Makes query results usable in different contexts

#### Description
Multiple output formats for query results (JSON, CSV, Markdown, plain text, custom templates), supporting different consumption patterns and integrations.

#### Command Syntax
```bash
# JSON output
ragged query "machine learning" --format json

# CSV output
ragged query "machine learning" --format csv --fields id,title,score

# Markdown table
ragged query "machine learning" --format markdown

# Plain text (default)
ragged query "machine learning" --format text

# Custom template
ragged query "machine learning" --template custom.jinja2
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/formatters.py` - Formatting module
  - `ragged/cli/templates/` - Jinja2 templates directory
  - `tests/cli/test_formatters.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/query.py` - Add format options

- **Dependencies**: Jinja2 templating, CSV writer, Rich for formatted output

#### Testing Requirements
- Unit tests for each formatter
- Template rendering tests
- Edge cases: empty results, special characters
- Output validation tests

#### Acceptance Criteria
- ✅ JSON, CSV, Markdown, text formats work
- ✅ Custom templates render correctly
- ✅ Field selection in CSV works
- ✅ Special characters handled properly

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#5-output-format-options) for full specification

---

### CLI-006: Query History & Replay

**Priority**: Medium

**Estimated Time**: 4-5 hours

**Impact**: Medium - Improves iterative query refinement workflow

#### Description
Maintain history of queries for replay, analysis, and iteration. Supports searching history and clearing old queries.

#### Command Syntax
```bash
# View query history
ragged history list

# Replay previous query
ragged history replay 5

# Search history
ragged history search --contains "machine learning"

# Clear history
ragged history clear --before 2025-01-01
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/history.py` - New command group
  - `ragged/core/history.py` - History storage (SQLite)
  - `tests/cli/test_history.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/query.py` - Record queries to history
  - `ragged/config/settings.py` - History configuration

- **Dependencies**: SQLite for history storage, Click command groups, date/time handling

#### Testing Requirements
- Unit tests for history operations
- Integration tests for replay
- Privacy tests (no sensitive data storage)
- Performance tests with large histories

#### Acceptance Criteria
- ✅ Queries automatically saved to history
- ✅ Can replay previous queries
- ✅ Search works across history
- ✅ Clear removes old queries

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#6-query-history--replay) for full specification

---

### CLI-007: Verbose & Quiet Modes

**Priority**: High

**Estimated Time**: 2-3 hours

**Impact**: High - Essential for debugging and automation

#### Description
Global flags for controlling output verbosity across all commands. Supports multiple verbosity levels for detailed debugging.

#### Command Syntax
```bash
# Verbose mode (debug information)
ragged --verbose ingest document.pdf
ragged -v query "machine learning"

# Quiet mode (minimal output)
ragged --quiet ingest document.pdf
ragged -q query "machine learning"

# Very verbose (trace level)
ragged -vv ingest document.pdf
```

#### Implementation
- **Files to Create**:
  - `ragged/utils/logging.py` - Enhanced logging configuration
  - `tests/cli/test_verbosity.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/main.py` - Add global flags
  - All command files - Respect verbosity settings

- **Dependencies**: Python logging module, Click global options, Rich for formatted output

#### Testing Requirements
- Unit tests for log level configuration
- Integration tests across all commands
- Output capture tests
- Performance impact tests

#### Acceptance Criteria
- ✅ -v shows debug information
- ✅ -q suppresses non-essential output
- ✅ -vv shows trace-level logs
- ✅ Works consistently across all commands

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#7-verbose--quiet-modes) for full specification

---

### CLI-008: Configuration Validation

**Priority**: High

**Estimated Time**: 3-4 hours

**Impact**: High - Essential for troubleshooting setup issues

#### Description
Command to validate ragged configuration and diagnose setup issues. Checks embedding models, storage connections, and all configuration values.

#### Command Syntax
```bash
# Validate configuration
ragged config validate

# Check specific configuration
ragged config check --embedding
ragged config check --storage
ragged config check --all

# Show current configuration
ragged config show --format json
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/config.py` - New command group
  - `ragged/config/validation.py` - Validation logic
  - `ragged/core/health.py` - Health check utilities
  - `tests/cli/test_config.py` - Test suite

- **Files to Modify**:
  - `ragged/config/settings.py` - Add validation methods

- **Dependencies**: Pydantic validation, service connectivity checks, configuration schema

#### Testing Requirements
- Unit tests for validation rules
- Integration tests with invalid configs
- Diagnostic message tests
- Edge cases: missing files, invalid values

#### Acceptance Criteria
- ✅ Detects invalid configuration values
- ✅ Checks service connectivity
- ✅ Provides helpful error messages
- ✅ Shows current config in readable format

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#8-configuration-validation) for full specification

---

### CLI-009: Environment Information

**Priority**: Medium

**Estimated Time**: 2-3 hours

**Impact**: Medium - Useful for debugging and support

#### Description
Display system information useful for debugging and support requests. Shows Python version, installed packages, hardware info, and ragged configuration.

#### Command Syntax
```bash
# Show all environment info
ragged info

# Show specific information
ragged info --python
ragged info --embeddings
ragged info --storage

# Export for bug reports
ragged info --format json > bug-report.json
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/info.py` - New command
  - `ragged/utils/system.py` - System information gathering
  - `tests/cli/test_info.py` - Test suite

- **Files to Modify**:
  - `ragged/version.py` - Version information utilities

- **Dependencies**: Python sys/platform modules, package version detection, hardware detection

#### Testing Requirements
- Unit tests for info gathering
- Cross-platform tests (Linux, macOS, Windows)
- Privacy tests (no sensitive data)
- Format validation tests

#### Acceptance Criteria
- ✅ Shows Python and package versions
- ✅ Shows hardware information
- ✅ Shows ragged configuration
- ✅ Can export as JSON for bug reports

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#9-environment-information) for full specification

---

### CLI-010: Cache Management

**Priority**: Medium

**Estimated Time**: 3-4 hours

**Impact**: Medium - Essential for performance tuning and troubleshooting

#### Description
Commands for managing embedding and processing caches. Show statistics, clear caches, and warm caches for better performance.

#### Command Syntax
```bash
# Show cache statistics
ragged cache stats

# Clear all caches
ragged cache clear --all

# Clear specific caches
ragged cache clear --embeddings
ragged cache clear --processed-docs

# Warm cache
ragged cache warm --collection research
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/commands/cache.py` - New command group
  - `ragged/core/cache.py` - Enhanced cache management
  - `tests/cli/test_cache.py` - Test suite

- **Files to Modify**:
  - `ragged/embeddings/cache.py` - Add statistics methods
  - `ragged/config/settings.py` - Cache configuration

- **Dependencies**: File system operations, cache size calculation, ChromaDB cache handling

#### Testing Requirements
- Unit tests for cache operations
- Integration tests for cache clearing
- Performance tests for cache warming
- Edge cases: missing cache directories

#### Acceptance Criteria
- ✅ Shows cache size and hit rate
- ✅ Can clear all or specific caches
- ✅ Cache warming improves performance
- ✅ Statistics accurate and helpful

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#10-cache-management) for full specification

---

### CLI-011: Shell Completion

**Priority**: High

**Estimated Time**: 4-5 hours

**Impact**: High - Significantly improves CLI usability

#### Description
Auto-completion support for bash, zsh, and fish shells. Provides command, option, and dynamic argument completion (e.g., collection names, document IDs).

#### Command Syntax
```bash
# Generate completion script
ragged completion bash > ~/.ragged-completion.bash
ragged completion zsh > ~/.ragged-completion.zsh
ragged completion fish > ~/.config/fish/completions/ragged.fish

# Install completion
ragged completion install --shell bash
```

#### Implementation
- **Files to Create**:
  - `ragged/cli/completion.py` - Completion generation
  - Shell-specific completion files (bash, zsh, fish)
  - `tests/cli/test_completion.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/main.py` - Command registration for completion

- **Dependencies**: Click shell completion, shell detection, file system operations

#### Testing Requirements
- Manual tests in each shell
- Completion generation tests
- Dynamic completion tests (e.g., document IDs)
- Cross-platform tests

#### Acceptance Criteria
- ✅ Bash completion works
- ✅ Zsh completion works
- ✅ Fish completion works
- ✅ Dynamic completions (collections, etc.) work
- ✅ Easy installation process

**See:** [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md#11-shell-completion) for full specification

---

### CLI Enhancements Summary

**Total Enhancements**: 11

**Total Estimated Time**: 48-62 hours

**Priority Distribution**:
- High: 6 enhancements (Search, Metadata, Output Formats, Verbose/Quiet, Config Validation, Shell Completion)
- Medium: 5 enhancements (Bulk Ops, Export/Import, Query History, Env Info, Cache Management)

**Category Breakdown**:
- Document Management: 3 (Search, Metadata, Bulk Ops)
- Query & Retrieval: 2 (Output Formats, Query History)
- User Experience: 2 (Verbose/Quiet, Shell Completion)
- Configuration & Setup: 2 (Config Validation, Env Info)
- Performance & Debugging: 1 (Cache Management)
- Advanced Features: 1 (Export/Import)

**Integration Points**:
- All enhancements integrate with existing command structure
- Consistent error handling and output formatting
- Respect global verbosity flags
- Support all collection operations
- Documented in CLI reference and guides

---

## Summary & Implementation Order

### Recommended Implementation Order

**Session 1: Core UX** (30 hours)
1. UX-001: Model switching (8h)
2. UX-002: Multi-collection support (10h)
3. UX-003: Enhanced progress (4h)
4. PERF-001: Embedding caching (5h)
5. Testing and bug fixes (3h)

**Session 2: Performance** (30 hours)
1. PERF-002: Async processing (12h)
2. PERF-003: Lazy model loading (6h)
3. PERF-004: BM25 persistence (3h)
4. UX-006: Better error messages (6h)
5. Testing and optimisation (3h)

**Session 3: Polish** (30 hours)
1. CONFIG-001: Runtime config (4h)
2. CONFIG-002: Config profiles (6h)
3. UX-004: Query suggestions (6h)
4. UX-005: Query refinement (8h)
5. UX-007: Document preview (4h)
6. Final testing and documentation (2h)

**Session 4: Optimisation & Testing** (20 hours)
1. PERF-005: Chunking optimisation (5h)
2. PERF-006: Query optimisation (6h)
3. Comprehensive testing (6h)
4. Documentation updates (3h)

**Session 5: CLI Foundation** (27 hours)
1. CLI-007: Verbose & quiet modes (3h)
2. CLI-008: Configuration validation (4h)
3. CLI-009: Environment information (3h)
4. CLI-005: Output format options (4h)
5. CLI-011: Shell completion (5h)
6. CLI-010: Cache management (4h)
7. Testing and integration (4h)

**Session 6: CLI Advanced Features** (30 hours)
1. CLI-001: Advanced search & filtering (4h)
2. CLI-002: Metadata management (5h)
3. CLI-003: Bulk operations (6h)
4. CLI-004: Export/import utilities (8h)
5. CLI-006: Query history & replay (5h)
6. Testing and documentation (2h)

### Performance Targets

By end of v0.2.7:
- [ ] Batch ingestion: 2-4x faster (async)
- [ ] Query time: 50-90% faster (caching)
- [ ] Startup time: <2 seconds (BM25 persistence)
- [ ] Memory usage: <100MB idle (lazy loading)
- [ ] Model switching: <2 seconds

### Breaking Changes

**Multi-Collection System**:
- Existing documents auto-migrate to "default" collection
- ChromaDB collection names may change
- Migration script runs on first v0.2.7 startup

**Migration Checklist**:
- [ ] Backup existing data before upgrade
- [ ] Run migration script
- [ ] Verify all documents accessible in "default" collection
- [ ] Test queries work correctly

### Acceptance Criteria

v0.2.7 is successful if:
1. ✅ Model switching works seamlessly
2. ✅ Multi-collection system stable
3. ✅ Performance targets met
4. ✅ User experience significantly improved
5. ✅ Migration from v0.2.5 works flawlessly
6. ✅ All 11 CLI enhancements functional and tested
7. ✅ CLI provides comprehensive document management capabilities
8. ✅ Shell completion works for bash, zsh, and fish
9. ✅ All tests pass with ≥75% coverage

---

## Related Documentation

- [Previous Version](../v0.2.6/README.md) - Documentation & structural improvements
- [Next Version](../v0.3/README.md) - Advanced RAG features
- [Planning](../../planning/version/v0.2/) - Design goals for v0.2 series
- [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md) - Comprehensive CLI specifications
- [Version Overview](../README.md) - Complete version comparison

---

**Next Steps**: After completing v0.2.7, proceed to v0.3 for advanced RAG features.
