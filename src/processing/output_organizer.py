"""Output organization for processed scanned documents (v0.4.9).

Organizes processed documents into structured directory:
- Semantic naming (Title-Author-Year.pdf)
- Separate locations for originals, corrected PDFs, markdown exports
- Lineage tracking (processing_log.jsonl)
- Duplicate handling

Directory structure:
    ~/.ragged/documents/
    ├── originals/[hash]/original.pdf    # Immutable backups
    ├── corrected/Title-Author-Year.pdf  # Clean, searchable PDFs
    └── markdown/Title-Author-Year.md    # Markdown exports

Usage:
    >>> organizer = OutputOrganizer()
    >>> result = organizer.organize(
    ...     original=Path("messy-scan.pdf"),
    ...     corrected=Path("clean.pdf"),
    ...     markdown=Path("clean.md"),
    ...     metadata={"title": "Book", "author": "Smith", "year": 2024}
    ... )
    >>> print(result.corrected_path)

v0.4.9: Initial output organization implementation
"""
from __future__ import annotations


import hashlib
import json
import logging
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ragged.config.settings import get_settings
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OrganizedOutput:
    """Result of output organization.

    Attributes:
        original_path: Path where original was backed up
        corrected_path: Path to corrected PDF
        markdown_path: Path to markdown export
        metadata: Document metadata
        lineage_id: Unique lineage tracking ID
    """

    original_path: Path
    corrected_path: Path
    markdown_path: Path | None
    metadata: dict[str, Any]
    lineage_id: str


class OutputOrganizer:
    """Organize processed scan outputs into structured directory.

    Features:
        - Semantic file naming (Title-Author-Year.pdf)
        - Organized directory structure (originals, corrected, markdown)
        - Lineage tracking (processing_log.jsonl)
        - Duplicate handling (automatic numbering)
        - Content-based hashing for originals

    Directory structure:
        {output_dir}/
        ├── originals/           # Immutable backups (organized by hash)
        │   └── [content-hash]/
        │       └── original.pdf
        ├── corrected/           # Processed, searchable PDFs
        │   └── Title-Author-Year.pdf
        └── markdown/            # Markdown exports
            └── Title-Author-Year.md

    Example:
        >>> organizer = OutputOrganizer(output_dir=Path("~/.ragged/documents"))
        >>> result = organizer.organize(
        ...     original=Path("scan.pdf"),
        ...     corrected=Path("processed.pdf"),
        ...     markdown=Path("processed.md"),
        ...     metadata={"title": "Book", "author": "Smith", "year": 2024}
        ... )
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        naming_convention: str = "title-author-year",
        keep_originals: bool = True,
        track_lineage: bool = True,
    ) -> None:
        """Initialise output organizer.

        Args:
            output_dir: Root output directory (None = use settings default)
            naming_convention: File naming convention
                - "title-author-year": Title-Author-Year.pdf
                - "hash": Content hash based naming
                - "original": Keep original filename
            keep_originals: Keep backup copies of original files
            track_lineage: Track processing lineage in JSON log
        """
        settings = get_settings()

        # Use configured directory or default
        if output_dir is None:
            self.output_dir = settings.data_dir / "documents"
        else:
            self.output_dir = Path(output_dir).expanduser().resolve()

        self.naming_convention = naming_convention
        self.keep_originals = keep_originals
        self.track_lineage = track_lineage

        # Create directory structure
        self._init_directories()

        logger.info(
            f"OutputOrganizer initialised: dir={self.output_dir}, "
            f"naming={naming_convention}, backup={keep_originals}"
        )

    def _init_directories(self) -> None:
        """Create directory structure if it doesn't exist."""
        self.originals_dir = self.output_dir / "originals"
        self.corrected_dir = self.output_dir / "corrected"
        self.markdown_dir = self.output_dir / "markdown"
        self.metadata_dir = self.output_dir.parent / "metadata"

        for directory in [self.originals_dir, self.corrected_dir, self.markdown_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Directory structure initialised at {self.output_dir}")

    def organize(
        self,
        original: Path,
        corrected: Path,
        markdown: Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OrganizedOutput:
        """Organize processed outputs into structured directory.

        Args:
            original: Original input file path
            corrected: Corrected PDF path
            markdown: Markdown export path (optional)
            metadata: Document metadata (title, author, year, etc.)

        Returns:
            Organized output with final paths

        Raises:
            FileNotFoundError: If input files don't exist
            RuntimeError: If organization fails
        """
        if not corrected.exists():
            raise FileNotFoundError(f"Corrected PDF not found: {corrected}")

        metadata = metadata or {}
        logger.info(f"Organizing outputs for: {original.name}")

        try:
            # Generate semantic filename
            semantic_name = self._generate_filename(original, metadata)

            # Backup original if enabled
            original_backup_path = None
            if self.keep_originals and original.exists():
                original_backup_path = self._backup_original(original)

            # Copy corrected PDF to organized location
            corrected_dest = self._get_unique_path(self.corrected_dir / f"{semantic_name}.pdf")
            shutil.copy2(corrected, corrected_dest)
            logger.info(f"Corrected PDF: {corrected_dest}")

            # Copy markdown if provided
            markdown_dest = None
            if markdown and markdown.exists():
                markdown_dest = self._get_unique_path(self.markdown_dir / f"{semantic_name}.md")
                shutil.copy2(markdown, markdown_dest)
                logger.info(f"Markdown: {markdown_dest}")

            # Track lineage
            lineage_id = self._generate_lineage_id(original)
            if self.track_lineage:
                self._record_lineage(
                    lineage_id=lineage_id,
                    original_path=original,
                    original_backup_path=original_backup_path,
                    corrected_path=corrected_dest,
                    markdown_path=markdown_dest,
                    metadata=metadata,
                )

            return OrganizedOutput(
                original_path=original_backup_path or original,
                corrected_path=corrected_dest,
                markdown_path=markdown_dest,
                metadata=metadata,
                lineage_id=lineage_id,
            )

        except Exception as e:
            logger.error(f"Failed to organize outputs: {e}")
            raise RuntimeError(f"Output organization failed: {e}") from e

    def _generate_filename(self, original: Path, metadata: dict[str, Any]) -> str:
        """Generate semantic filename from metadata.

        Args:
            original: Original file path
            metadata: Document metadata

        Returns:
            Semantic filename (without extension)

        Naming convention:
            - Full metadata: "The-Art-of-RAG-Smith-2024"
            - Partial: "The-Art-of-RAG-Unknown-2024"
            - Fallback: "Scanned-Book-20250123-001"
        """
        if self.naming_convention == "hash":
            # Hash-based naming
            content_hash = self._calculate_file_hash(original)
            return content_hash[:16]

        elif self.naming_convention == "original":
            # Keep original filename (sanitized)
            return self._sanitize_filename(original.stem)

        else:  # title-author-year
            # Semantic naming from metadata
            title = metadata.get("title", "")
            author = metadata.get("author", "Unknown")
            year = metadata.get("year", "")

            if not title:
                # Fallback to timestamped name
                timestamp = datetime.now().strftime("%Y%m%d")
                return f"Scanned-Book-{timestamp}"

            # Build semantic name
            parts = []

            # Title (truncate if too long)
            title_clean = self._sanitize_filename(title)
            if len(title_clean) > 50:
                title_clean = title_clean[:50]
            parts.append(title_clean)

            # Author
            if author and author != "Unknown":
                author_clean = self._sanitize_filename(author)
                # Handle multiple authors (take first)
                if "," in author_clean or " and " in author_clean.lower():
                    author_clean = re.split(r",|\s+and\s+", author_clean, flags=re.IGNORECASE)[0]
                parts.append(author_clean)

            # Year
            if year:
                parts.append(str(year))

            # Combine with hyphens
            semantic_name = "-".join(parts)

            # Final sanitization
            semantic_name = self._sanitize_filename(semantic_name)

            # Truncate if too long (max 100 chars)
            if len(semantic_name) > 100:
                semantic_name = semantic_name[:100]

            return semantic_name

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Raw filename

        Returns:
            Sanitized filename
        """
        # Remove/replace invalid characters
        sanitized = filename

        # Replace spaces with hyphens
        sanitized = sanitized.replace(" ", "-")

        # Remove special characters (keep: letters, numbers, hyphens, dots)
        sanitized = re.sub(r"[^a-zA-Z0-9\-.]", "", sanitized)

        # Remove multiple consecutive hyphens
        sanitized = re.sub(r"-+", "-", sanitized)

        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")

        # Ensure not empty
        if not sanitized:
            sanitized = "untitled"

        return sanitized

    def _get_unique_path(self, path: Path) -> Path:
        """Get unique file path (handle duplicates with numbering).

        Args:
            path: Desired file path

        Returns:
            Unique file path (may have number suffix)

        Example:
            Input: /path/Book-Smith-2024.pdf
            Exists: /path/Book-Smith-2024.pdf
            Output: /path/Book-Smith-2024-001.pdf
        """
        if not path.exists():
            return path

        # File exists, add number suffix
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        counter = 1
        while True:
            new_path = parent / f"{stem}-{counter:03d}{suffix}"
            if not new_path.exists():
                logger.debug(f"Duplicate detected, using: {new_path.name}")
                return new_path
            counter += 1

            # Safety: prevent infinite loop
            if counter > 999:
                raise RuntimeError(f"Too many duplicates for file: {path}")

    def _backup_original(self, original: Path) -> Path:
        """Backup original file to immutable storage.

        Args:
            original: Original file path

        Returns:
            Backup file path

        Storage structure:
            originals/[content-hash]/original.pdf
        """
        # Calculate content hash
        content_hash = self._calculate_file_hash(original)

        # Create hash-based directory
        backup_dir = self.originals_dir / content_hash
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup file with original extension
        backup_path = backup_dir / f"original{original.suffix}"

        # Copy file (if not already backed up)
        if not backup_path.exists():
            shutil.copy2(original, backup_path)
            logger.debug(f"Backed up original: {backup_path}")
        else:
            logger.debug(f"Original already backed up: {backup_path}")

        return backup_path

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content.

        Args:
            file_path: File to hash

        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks for memory efficiency
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _generate_lineage_id(self, original: Path) -> str:
        """Generate unique lineage tracking ID.

        Args:
            original: Original file path

        Returns:
            Unique lineage ID (timestamp + hash prefix)
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_hash = self._calculate_file_hash(original)
        return f"{timestamp}-{file_hash[:8]}"

    def _record_lineage(
        self,
        lineage_id: str,
        original_path: Path,
        original_backup_path: Path | None,
        corrected_path: Path,
        markdown_path: Path | None,
        metadata: dict[str, Any],
    ) -> None:
        """Record processing lineage in JSON log.

        Args:
            lineage_id: Unique lineage ID
            original_path: Original input file path
            original_backup_path: Backup location
            corrected_path: Corrected PDF path
            markdown_path: Markdown export path
            metadata: Document metadata
        """
        log_file = self.metadata_dir / "processing_log.jsonl"

        # Create lineage record
        record = {
            "lineage_id": lineage_id,
            "timestamp": datetime.now().isoformat(),
            "original": {
                "path": str(original_path),
                "backup": str(original_backup_path) if original_backup_path else None,
                "size_bytes": original_path.stat().st_size if original_path.exists() else None,
                "hash": self._calculate_file_hash(original_path)
                if original_path.exists()
                else None,
            },
            "processed": {
                "corrected_pdf": str(corrected_path),
                "markdown": str(markdown_path) if markdown_path else None,
            },
            "metadata": metadata,
            "processor_version": "v0.4.9",
        }

        # Append to JSON Lines file
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            logger.debug(f"Recorded lineage: {lineage_id}")

        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")

    def get_lineage(self, lineage_id: str | None = None) -> list[dict[str, Any]]:
        """Retrieve processing lineage records.

        Args:
            lineage_id: Specific lineage ID (None = all records)

        Returns:
            List of lineage records
        """
        log_file = self.metadata_dir / "processing_log.jsonl"

        if not log_file.exists():
            return []

        records = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if lineage_id is None or record.get("lineage_id") == lineage_id:
                        records.append(record)

            return records

        except Exception as e:
            logger.error(f"Failed to read lineage log: {e}")
            return []

    def search_by_metadata(
        self,
        title: str | None = None,
        author: str | None = None,
        year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search processed documents by metadata.

        Args:
            title: Title to search (partial match)
            author: Author to search (partial match)
            year: Publication year (exact match)

        Returns:
            List of matching lineage records
        """
        all_records = self.get_lineage()

        matching = []
        for record in all_records:
            metadata = record.get("metadata", {})

            # Check filters
            if title and title.lower() not in metadata.get("title", "").lower():
                continue
            if author and author.lower() not in metadata.get("author", "").lower():
                continue
            if year and metadata.get("year") != year:
                continue

            matching.append(record)

        return matching
