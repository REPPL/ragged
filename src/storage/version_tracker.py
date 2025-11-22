"""
Document version tracking using SQLite.

Provides version detection, storage, and retrieval for document updates.
Enables version-specific queries and version comparison.

v0.3.7a: Initial version tracking implementation.
"""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DocumentVersion:
    """
    Represents a specific version of a document.

    Attributes:
        version_id: Unique identifier for this version
        doc_id: Identifier for the document (consistent across versions)
        content_hash: SHA-256 hash of document content
        page_hashes: List of per-page hashes
        version_number: Sequential version number (1, 2, 3, ...)
        created_at: Timestamp when version was created
        file_path: Path to the document file
        metadata: Additional metadata (file size, page count, etc.)
    """
    version_id: str
    doc_id: str
    content_hash: str
    page_hashes: list[str]
    version_number: int
    created_at: datetime
    file_path: str
    metadata: dict[str, Any]


class VersionTracker:
    """
    SQLite-based document version tracking.

    Tracks document versions using content hashing, detects updates,
    and enables version-specific queries.

    Example:
        >>> tracker = VersionTracker()
        >>>
        >>> # Index a document
        >>> version = tracker.track_document(
        ...     file_path="report.pdf",
        ...     content_hash="abc123...",
        ...     page_hashes=["page1_hash", "page2_hash"]
        ... )
        >>> print(f"Version {version.version_number} tracked")
        >>>
        >>> # Check if document changed
        >>> is_new = tracker.is_new_version(
        ...     file_path="report.pdf",
        ...     content_hash="def456..."
        ... )
        >>>
        >>> # Get specific version
        >>> v2 = tracker.get_version(doc_id=version.doc_id, version_number=2)
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize version tracker with SQLite database.

        Args:
            db_path: Path to SQLite database file.
                     Defaults to ~/.ragged/versions.db
        """
        if db_path is None:
            from src.config.settings import get_settings
            settings = get_settings()
            db_path = settings.config_dir / "versions.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        logger.info(f"Version tracker initialized at {self.db_path}")

    def _init_database(self) -> None:
        """Create database schema if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    version_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    page_hashes TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    file_path TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
                    UNIQUE(doc_id, version_number)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_versions (
                    chunk_id TEXT NOT NULL,
                    version_id TEXT NOT NULL,
                    page_number INTEGER,
                    chunk_sequence INTEGER,
                    FOREIGN KEY (version_id) REFERENCES versions(version_id),
                    PRIMARY KEY (chunk_id, version_id)
                )
            """)

            # Indices for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_versions_doc_id
                ON versions(doc_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_versions_content_hash
                ON versions(content_hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunk_versions_version_id
                ON chunk_versions(version_id)
            """)

            conn.commit()

    def calculate_content_hash(
        self,
        content: bytes,
        page_contents: list[bytes] | None = None
    ) -> tuple[str, list[str]]:
        """
        Calculate hierarchical hash for document.

        Args:
            content: Full document content (bytes)
            page_contents: Optional list of per-page content

        Returns:
            Tuple of (document_hash, page_hashes)
        """
        # Calculate per-page hashes if provided
        page_hashes = []
        if page_contents:
            page_hashes = [
                hashlib.sha256(page).hexdigest()
                for page in page_contents
            ]

        # Calculate document hash
        if page_hashes:
            # Hash from concatenated page hashes (consistent)
            content_hash = hashlib.sha256(
                "".join(page_hashes).encode()
            ).hexdigest()
        else:
            # Hash entire content
            content_hash = hashlib.sha256(content).hexdigest()

        return content_hash, page_hashes

    def track_document(
        self,
        file_path: str,
        content_hash: str,
        page_hashes: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> DocumentVersion:
        """
        Track a new document version.

        Args:
            file_path: Path to document file
            content_hash: SHA-256 hash of document content
            page_hashes: Optional list of per-page hashes
            metadata: Additional metadata

        Returns:
            DocumentVersion instance

        Raises:
            ValueError: If document with same hash already exists
        """
        import json

        file_path_str = str(Path(file_path).absolute())
        page_hashes = page_hashes or []
        metadata = metadata or {}

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Check if document exists
            existing_doc = conn.execute(
                "SELECT doc_id FROM documents WHERE file_path = ?",
                (file_path_str,)
            ).fetchone()

            if existing_doc:
                doc_id = existing_doc["doc_id"]

                # Check if this exact version exists
                existing_version = conn.execute(
                    "SELECT version_id FROM versions WHERE content_hash = ? AND doc_id = ?",
                    (content_hash, doc_id)
                ).fetchone()

                if existing_version:
                    logger.info(f"Document {file_path_str} already tracked with hash {content_hash[:8]}")
                    return self.get_version_by_id(existing_version["version_id"])

                # Get next version number
                max_version = conn.execute(
                    "SELECT MAX(version_number) as max_ver FROM versions WHERE doc_id = ?",
                    (doc_id,)
                ).fetchone()
                version_number = (max_version["max_ver"] or 0) + 1

                # Update document timestamp
                conn.execute(
                    "UPDATE documents SET updated_at = ? WHERE doc_id = ?",
                    (datetime.now().isoformat(), doc_id)
                )
            else:
                # Create new document
                doc_id = str(uuid4())
                version_number = 1

                now = datetime.now().isoformat()
                conn.execute(
                    "INSERT INTO documents (doc_id, file_path, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (doc_id, file_path_str, now, now)
                )

            # Create new version
            version_id = str(uuid4())
            version_created_at = datetime.now()
            conn.execute(
                """
                INSERT INTO versions
                (version_id, doc_id, content_hash, page_hashes, version_number, created_at, file_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    doc_id,
                    content_hash,
                    json.dumps(page_hashes),
                    version_number,
                    version_created_at.isoformat(),
                    file_path_str,
                    json.dumps(metadata)
                )
            )

            conn.commit()

            logger.info(
                f"Tracked version {version_number} of {file_path_str} "
                f"(hash: {content_hash[:8]}...)"
            )

            return DocumentVersion(
                version_id=version_id,
                doc_id=doc_id,
                content_hash=content_hash,
                page_hashes=page_hashes,
                version_number=version_number,
                created_at=version_created_at,
                file_path=file_path_str,
                metadata=metadata
            )

    def is_new_version(self, file_path: str, content_hash: str) -> bool:
        """
        Check if content hash represents a new version.

        Args:
            file_path: Path to document file
            content_hash: SHA-256 hash of document content

        Returns:
            True if this is a new version, False if already tracked
        """
        file_path_str = str(Path(file_path).absolute())

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find document
            doc = conn.execute(
                "SELECT doc_id FROM documents WHERE file_path = ?",
                (file_path_str,)
            ).fetchone()

            if not doc:
                return True  # New document

            # Check if hash exists for this document
            existing = conn.execute(
                "SELECT version_id FROM versions WHERE doc_id = ? AND content_hash = ?",
                (doc["doc_id"], content_hash)
            ).fetchone()

            return existing is None

    def get_version(
        self,
        doc_id: str,
        version_number: int | None = None
    ) -> DocumentVersion | None:
        """
        Get specific version of a document.

        Args:
            doc_id: Document identifier
            version_number: Version number (defaults to latest)

        Returns:
            DocumentVersion if found, None otherwise
        """
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if version_number:
                row = conn.execute(
                    """
                    SELECT * FROM versions
                    WHERE doc_id = ? AND version_number = ?
                    """,
                    (doc_id, version_number)
                ).fetchone()
            else:
                # Get latest version
                row = conn.execute(
                    """
                    SELECT * FROM versions
                    WHERE doc_id = ?
                    ORDER BY version_number DESC
                    LIMIT 1
                    """,
                    (doc_id,)
                ).fetchone()

            if not row:
                return None

            return DocumentVersion(
                version_id=row["version_id"],
                doc_id=row["doc_id"],
                content_hash=row["content_hash"],
                page_hashes=json.loads(row["page_hashes"]),
                version_number=row["version_number"],
                created_at=datetime.fromisoformat(row["created_at"]),
                file_path=row["file_path"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )

    def get_version_by_id(self, version_id: str) -> DocumentVersion | None:
        """
        Get version by version ID.

        Args:
            version_id: Version identifier

        Returns:
            DocumentVersion if found, None otherwise
        """
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                "SELECT * FROM versions WHERE version_id = ?",
                (version_id,)
            ).fetchone()

            if not row:
                return None

            return DocumentVersion(
                version_id=row["version_id"],
                doc_id=row["doc_id"],
                content_hash=row["content_hash"],
                page_hashes=json.loads(row["page_hashes"]),
                version_number=row["version_number"],
                created_at=datetime.fromisoformat(row["created_at"]),
                file_path=row["file_path"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )

    def get_version_by_hash(self, content_hash: str) -> DocumentVersion | None:
        """
        Get version by content hash.

        Args:
            content_hash: SHA-256 content hash

        Returns:
            DocumentVersion if found, None otherwise
        """
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                "SELECT * FROM versions WHERE content_hash = ?",
                (content_hash,)
            ).fetchone()

            if not row:
                return None

            return DocumentVersion(
                version_id=row["version_id"],
                doc_id=row["doc_id"],
                content_hash=row["content_hash"],
                page_hashes=json.loads(row["page_hashes"]),
                version_number=row["version_number"],
                created_at=datetime.fromisoformat(row["created_at"]),
                file_path=row["file_path"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )

    def list_versions(self, doc_id: str) -> list[DocumentVersion]:
        """
        List all versions of a document.

        Args:
            doc_id: Document identifier

        Returns:
            List of DocumentVersion instances, ordered by version number
        """
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                """
                SELECT * FROM versions
                WHERE doc_id = ?
                ORDER BY version_number ASC
                """,
                (doc_id,)
            ).fetchall()

            return [
                DocumentVersion(
                    version_id=row["version_id"],
                    doc_id=row["doc_id"],
                    content_hash=row["content_hash"],
                    page_hashes=json.loads(row["page_hashes"]),
                    version_number=row["version_number"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    file_path=row["file_path"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
                for row in rows
            ]

    def find_document_by_path(self, file_path: str) -> str | None:
        """
        Find document ID by file path.

        Args:
            file_path: Path to document file

        Returns:
            Document ID if found, None otherwise
        """
        file_path_str = str(Path(file_path).absolute())

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                "SELECT doc_id FROM documents WHERE file_path = ?",
                (file_path_str,)
            ).fetchone()

            return row["doc_id"] if row else None

    def link_chunk_to_version(
        self,
        chunk_id: str,
        version_id: str,
        page_number: int | None = None,
        chunk_sequence: int | None = None
    ) -> None:
        """
        Link a chunk ID to a specific version.

        Args:
            chunk_id: Chunk identifier (from ChromaDB)
            version_id: Version identifier
            page_number: Optional page number
            chunk_sequence: Optional chunk sequence within page
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunk_versions
                (chunk_id, version_id, page_number, chunk_sequence)
                VALUES (?, ?, ?, ?)
                """,
                (chunk_id, version_id, page_number, chunk_sequence)
            )
            conn.commit()

    def get_chunk_version(self, chunk_id: str) -> DocumentVersion | None:
        """
        Get version associated with a chunk.

        Args:
            chunk_id: Chunk identifier

        Returns:
            DocumentVersion if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                """
                SELECT version_id FROM chunk_versions
                WHERE chunk_id = ?
                """,
                (chunk_id,)
            ).fetchone()

            if not row:
                return None

            return self.get_version_by_id(row["version_id"])
