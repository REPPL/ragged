# Incremental Index Operations

**Phase**: 2 | **Effort**: 5-6h | **Priority**: MUST-HAVE

**Current**: BM25 full rebuild only (`src/retrieval/bm25.py`)

**Enhancement**: Differential updates, atomic swap, background compaction

**Implementation**:
```python
class BM25RetrieverIncremental(BM25Retriever):
    def add_documents(self, documents, doc_ids):
        """Add documents without full rebuild."""
        # Append to corpus
        # Update index incrementally
        # Atomic swap when complete

    def remove_documents(self, doc_ids):
        """Remove documents and compact index."""
        # Mark for deletion
        # Background compaction task

    def rebuild_if_needed(self):
        """Rebuild if fragmentation >50%."""
        if self.fragmentation_ratio() > 0.5:
            self.rebuild_index()
```

**Success**: 10-100x faster for large collections

**Timeline**: 5-6h
