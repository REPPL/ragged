"""Storage analytics module.

Provides storage usage analysis, growth projections, and cleanup
recommendations for ragged data directories.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StorageItem:
    """A single storage item (file or directory).

    Attributes:
        path: Item path
        name: Item name
        size_bytes: Size in bytes
        file_count: Number of files (if directory)
        item_type: Type of item (file, directory)
        category: Storage category (documents, embeddings, cache, etc.)
        last_modified: Last modification time
    """

    path: str
    name: str
    size_bytes: int
    file_count: int = 1
    item_type: str = "file"
    category: str = "other"
    last_modified: datetime | None = None

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "name": self.name,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 2),
            "size_gb": round(self.size_gb, 3),
            "file_count": self.file_count,
            "item_type": self.item_type,
            "category": self.category,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


@dataclass
class StorageCategory:
    """A category of storage usage.

    Attributes:
        name: Category name
        description: Category description
        path: Base path for category
        size_bytes: Total size
        file_count: Number of files
        items: Individual items in category
    """

    name: str
    description: str
    path: str
    size_bytes: int = 0
    file_count: int = 0
    items: list[StorageItem] = field(default_factory=list)

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 2),
            "size_gb": round(self.size_gb, 3),
            "file_count": self.file_count,
            "percentage": 0,  # Set by caller
        }


@dataclass
class StorageReport:
    """Complete storage analysis report.

    Attributes:
        total_size_bytes: Total storage used
        categories: Breakdown by category
        largest_items: Largest individual items
        old_items: Items not modified recently
        growth_projection: Projected growth
        recommendations: Cleanup recommendations
        computed_at: When report was generated
    """

    total_size_bytes: int
    categories: list[StorageCategory]
    largest_items: list[StorageItem] = field(default_factory=list)
    old_items: list[StorageItem] = field(default_factory=list)
    growth_projection: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    computed_at: datetime = field(default_factory=datetime.now)

    @property
    def total_size_mb(self) -> float:
        """Total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)

    @property
    def total_size_gb(self) -> float:
        """Total size in gigabytes."""
        return self.total_size_bytes / (1024 * 1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        # Calculate percentages
        category_dicts = []
        for cat in self.categories:
            cat_dict = cat.to_dict()
            cat_dict["percentage"] = (
                (cat.size_bytes / self.total_size_bytes * 100)
                if self.total_size_bytes > 0
                else 0
            )
            category_dicts.append(cat_dict)

        return {
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": round(self.total_size_mb, 2),
            "total_size_gb": round(self.total_size_gb, 3),
            "categories": category_dicts,
            "largest_items": [i.to_dict() for i in self.largest_items],
            "old_items": [i.to_dict() for i in self.old_items],
            "growth_projection": self.growth_projection,
            "recommendations": self.recommendations,
            "computed_at": self.computed_at.isoformat(),
        }


class StorageScanner:
    """Scans filesystem for storage usage."""

    # Default ragged storage locations
    DEFAULT_PATHS = {
        "documents": {
            "path": "~/.ragged/documents",
            "description": "Ingested documents and text files",
        },
        "embeddings": {
            "path": "~/.ragged/chromadb",
            "description": "ChromaDB vector database",
        },
        "cache": {
            "path": "~/.ragged/cache",
            "description": "Temporary cache files",
        },
        "logs": {
            "path": "~/.ragged/logs",
            "description": "Application log files",
        },
        "conversations": {
            "path": "~/.ragged/conversations",
            "description": "Conversation history",
        },
        "models": {
            "path": "~/.ollama/models",
            "description": "Ollama model files",
        },
    }

    def __init__(self, custom_paths: dict[str, dict[str, str]] | None = None) -> None:
        """Initialise storage scanner.

        Args:
            custom_paths: Custom path definitions to override defaults
        """
        self.paths = {**self.DEFAULT_PATHS}
        if custom_paths:
            self.paths.update(custom_paths)

    def scan_directory(self, path: Path) -> tuple[int, int, datetime | None]:
        """Scan a directory for total size and file count.

        Args:
            path: Directory path to scan

        Returns:
            Tuple of (total_bytes, file_count, last_modified)
        """
        total_size = 0
        file_count = 0
        last_modified: datetime | None = None

        if not path.exists():
            return 0, 0, None

        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        stat = item.stat()
                        total_size += stat.st_size
                        file_count += 1

                        item_mtime = datetime.fromtimestamp(stat.st_mtime)
                        if last_modified is None or item_mtime > last_modified:
                            last_modified = item_mtime
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning {path}: {e}")

        return total_size, file_count, last_modified

    def get_largest_files(
        self,
        path: Path,
        limit: int = 10,
        min_size_mb: float = 1.0,
    ) -> list[StorageItem]:
        """Get the largest files in a directory.

        Args:
            path: Directory to scan
            limit: Maximum files to return
            min_size_mb: Minimum size in MB to include

        Returns:
            List of largest files
        """
        files: list[StorageItem] = []
        min_size_bytes = int(min_size_mb * 1024 * 1024)

        if not path.exists():
            return files

        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        stat = item.stat()
                        if stat.st_size >= min_size_bytes:
                            files.append(
                                StorageItem(
                                    path=str(item),
                                    name=item.name,
                                    size_bytes=stat.st_size,
                                    item_type="file",
                                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                                )
                            )
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

        # Sort by size descending
        files.sort(key=lambda f: f.size_bytes, reverse=True)
        return files[:limit]

    def get_old_files(
        self,
        path: Path,
        days_old: int = 30,
        limit: int = 20,
    ) -> list[StorageItem]:
        """Get files not modified recently.

        Args:
            path: Directory to scan
            days_old: Consider files older than this many days
            limit: Maximum files to return

        Returns:
            List of old files
        """
        files: list[StorageItem] = []
        cutoff = datetime.now() - timedelta(days=days_old)

        if not path.exists():
            return files

        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        stat = item.stat()
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        if mtime < cutoff:
                            files.append(
                                StorageItem(
                                    path=str(item),
                                    name=item.name,
                                    size_bytes=stat.st_size,
                                    item_type="file",
                                    last_modified=mtime,
                                )
                            )
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

        # Sort by size descending (prioritise large old files)
        files.sort(key=lambda f: f.size_bytes, reverse=True)
        return files[:limit]


class GrowthProjector:
    """Projects storage growth based on historical data."""

    def __init__(self, history_days: int = 30) -> None:
        """Initialise growth projector.

        Args:
            history_days: Days of history to analyse
        """
        self.history_days = history_days
        self._history: list[tuple[datetime, int]] = []

    def record_size(self, size_bytes: int, timestamp: datetime | None = None) -> None:
        """Record a size measurement.

        Args:
            size_bytes: Current total size
            timestamp: Measurement timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self._history.append((timestamp, size_bytes))

        # Trim old history
        cutoff = datetime.now() - timedelta(days=self.history_days)
        self._history = [(t, s) for t, s in self._history if t >= cutoff]

    def project(
        self,
        current_size_bytes: int,
        available_space_bytes: int | None = None,
    ) -> dict[str, Any]:
        """Project future storage usage.

        Args:
            current_size_bytes: Current storage size
            available_space_bytes: Available disk space

        Returns:
            Projection data
        """
        projection = {
            "current_size_bytes": current_size_bytes,
            "daily_growth_bytes": 0,
            "weekly_growth_bytes": 0,
            "monthly_growth_bytes": 0,
            "days_until_full": None,
            "projected_30_day_bytes": current_size_bytes,
        }

        if len(self._history) < 2:
            return projection

        # Calculate growth rate
        sorted_history = sorted(self._history, key=lambda x: x[0])
        first = sorted_history[0]
        last = sorted_history[-1]

        days_elapsed = (last[0] - first[0]).total_seconds() / 86400
        if days_elapsed <= 0:
            return projection

        size_change = last[1] - first[1]
        daily_growth = size_change / days_elapsed

        projection["daily_growth_bytes"] = int(daily_growth)
        projection["weekly_growth_bytes"] = int(daily_growth * 7)
        projection["monthly_growth_bytes"] = int(daily_growth * 30)
        projection["projected_30_day_bytes"] = int(current_size_bytes + daily_growth * 30)

        # Calculate days until disk full
        if available_space_bytes is not None and daily_growth > 0:
            days_until_full = available_space_bytes / daily_growth
            projection["days_until_full"] = int(days_until_full)

        return projection


class CleanupRecommender:
    """Generates storage cleanup recommendations."""

    def recommend(
        self,
        report: StorageReport,
        available_space_gb: float | None = None,
    ) -> list[str]:
        """Generate cleanup recommendations.

        Args:
            report: Storage analysis report
            available_space_gb: Available disk space in GB

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for low disk space
        if available_space_gb is not None:
            if available_space_gb < 5:
                recommendations.append(
                    f"⚠️ Low disk space: Only {available_space_gb:.1f}GB remaining"
                )

        # Check cache size
        for cat in report.categories:
            if cat.name == "cache" and cat.size_gb > 1:
                recommendations.append(
                    f"Clear cache to free {cat.size_gb:.1f}GB "
                    "(ragged cache clear --all)"
                )

            if cat.name == "logs" and cat.size_gb > 0.5:
                recommendations.append(
                    f"Remove old logs to free {cat.size_gb:.1f}GB "
                    "(logs older than 30 days)"
                )

        # Check for old files
        if report.old_items:
            total_old_size = sum(i.size_bytes for i in report.old_items)
            old_size_gb = total_old_size / (1024 * 1024 * 1024)
            if old_size_gb > 0.1:
                recommendations.append(
                    f"Review {len(report.old_items)} files not modified in 30+ days "
                    f"({old_size_gb:.1f}GB)"
                )

        # Check for large files
        large_files = [i for i in report.largest_items if i.size_gb > 0.5]
        if large_files:
            recommendations.append(
                f"Review {len(large_files)} large files (>500MB each)"
            )

        # Growth projection warning
        if report.growth_projection.get("days_until_full"):
            days = report.growth_projection["days_until_full"]
            if days < 30:
                recommendations.append(
                    f"⚠️ At current growth rate, disk may be full in {days} days"
                )

        # Model cleanup for Ollama
        for cat in report.categories:
            if cat.name == "models" and cat.size_gb > 10:
                recommendations.append(
                    f"Consider removing unused Ollama models to free space "
                    f"(ollama list, ollama rm <model>)"
                )

        if not recommendations:
            recommendations.append("✓ Storage usage is healthy")

        return recommendations


class StorageAnalytics:
    """High-level storage analytics interface."""

    def __init__(self) -> None:
        """Initialise storage analytics."""
        self.scanner = StorageScanner()
        self.projector = GrowthProjector()
        self.recommender = CleanupRecommender()

    def analyze(
        self,
        include_ollama: bool = True,
        check_disk_space: bool = True,
    ) -> StorageReport:
        """Perform comprehensive storage analysis.

        Args:
            include_ollama: Include Ollama model storage
            check_disk_space: Check available disk space

        Returns:
            Complete storage report
        """
        categories: list[StorageCategory] = []
        total_size = 0
        all_large_items: list[StorageItem] = []
        all_old_items: list[StorageItem] = []

        for cat_name, cat_config in self.scanner.paths.items():
            if cat_name == "models" and not include_ollama:
                continue

            path = Path(cat_config["path"]).expanduser()
            size, file_count, last_modified = self.scanner.scan_directory(path)

            category = StorageCategory(
                name=cat_name,
                description=cat_config["description"],
                path=str(path),
                size_bytes=size,
                file_count=file_count,
            )
            categories.append(category)
            total_size += size

            # Collect large and old files
            large = self.scanner.get_largest_files(path, limit=5)
            for item in large:
                item.category = cat_name
            all_large_items.extend(large)

            old = self.scanner.get_old_files(path, days_old=30, limit=10)
            for item in old:
                item.category = cat_name
            all_old_items.extend(old)

        # Sort and limit large/old items
        all_large_items.sort(key=lambda x: x.size_bytes, reverse=True)
        all_old_items.sort(key=lambda x: x.size_bytes, reverse=True)

        # Get growth projection
        self.projector.record_size(total_size)
        available_space = None
        if check_disk_space:
            try:
                stat = os.statvfs(Path.home())
                available_space = stat.f_frsize * stat.f_bavail
            except (OSError, AttributeError):
                pass

        projection = self.projector.project(total_size, available_space)

        # Generate report
        report = StorageReport(
            total_size_bytes=total_size,
            categories=categories,
            largest_items=all_large_items[:10],
            old_items=all_old_items[:20],
            growth_projection=projection,
        )

        # Generate recommendations
        available_gb = available_space / (1024**3) if available_space else None
        report.recommendations = self.recommender.recommend(report, available_gb)

        return report

    def get_category_breakdown(self) -> dict[str, dict[str, Any]]:
        """Get storage breakdown by category.

        Returns:
            Dictionary of category name to size info
        """
        breakdown = {}
        for cat_name, cat_config in self.scanner.paths.items():
            path = Path(cat_config["path"]).expanduser()
            size, file_count, _ = self.scanner.scan_directory(path)
            breakdown[cat_name] = {
                "path": str(path),
                "size_bytes": size,
                "size_mb": size / (1024 * 1024),
                "size_gb": size / (1024 * 1024 * 1024),
                "file_count": file_count,
            }
        return breakdown


# Module-level convenience functions
_analytics: StorageAnalytics | None = None


def get_storage_analytics() -> StorageAnalytics:
    """Get global storage analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = StorageAnalytics()
    return _analytics
