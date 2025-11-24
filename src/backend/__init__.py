"""Backend management and migration.

This module provides:
- Vector backend abstraction
- Backend migration between ChromaDB and LEANN
- Backend comparison and selection

Part of v0.4.12 Backend Optimisation & Migration.
"""

from ragged.backend.migration import BackendMigrator, MigrationResult

__all__ = ["BackendMigrator", "MigrationResult"]
