"""Unit tests for storage analytics module."""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

from ragged.analytics.storage_analytics import (
    StorageItem,
    StorageCategory,
    StorageReport,
    StorageScanner,
    GrowthProjector,
    CleanupRecommender,
    StorageAnalytics,
    get_storage_analytics,
)


class TestStorageItem:
    """Tests for StorageItem dataclass."""

    def test_create_item(self):
        """Test creating a storage item."""
        item = StorageItem(
            path="/home/user/file.txt",
            name="file.txt",
            size_bytes=1024 * 1024,  # 1 MB
            file_count=1,
            item_type="file",
            category="documents",
        )
        assert item.name == "file.txt"
        assert item.size_bytes == 1024 * 1024
        assert item.category == "documents"

    def test_size_conversions(self):
        """Test size unit conversions."""
        item = StorageItem(
            path="/test",
            name="test",
            size_bytes=1024 * 1024 * 1024,  # 1 GB
        )
        assert item.size_mb == 1024.0
        assert item.size_gb == 1.0

    def test_to_dict(self):
        """Test item serialisation."""
        item = StorageItem(
            path="/test/file.txt",
            name="file.txt",
            size_bytes=1048576,  # 1 MB
            last_modified=datetime(2024, 1, 1, 12, 0),
        )
        d = item.to_dict()
        assert d["path"] == "/test/file.txt"
        assert d["size_mb"] == 1.0
        assert d["last_modified"] == "2024-01-01T12:00:00"


class TestStorageCategory:
    """Tests for StorageCategory dataclass."""

    def test_create_category(self):
        """Test creating a storage category."""
        category = StorageCategory(
            name="documents",
            description="Document files",
            path="/home/user/.ragged/documents",
            size_bytes=1024 * 1024 * 100,  # 100 MB
            file_count=50,
        )
        assert category.name == "documents"
        assert category.file_count == 50

    def test_size_conversions(self):
        """Test size unit conversions."""
        category = StorageCategory(
            name="test",
            description="Test",
            path="/test",
            size_bytes=1024 * 1024 * 512,  # 512 MB
        )
        assert category.size_mb == 512.0
        assert category.size_gb == 0.5

    def test_to_dict(self):
        """Test category serialisation."""
        category = StorageCategory(
            name="cache",
            description="Cache files",
            path="/cache",
            size_bytes=1024 * 1024 * 10,
            file_count=100,
        )
        d = category.to_dict()
        assert d["name"] == "cache"
        assert d["file_count"] == 100
        assert "percentage" in d


class TestStorageReport:
    """Tests for StorageReport dataclass."""

    def test_create_report(self):
        """Test creating a storage report."""
        categories = [
            StorageCategory("docs", "Documents", "/docs", 1024 * 1024 * 100, 10),
            StorageCategory("cache", "Cache", "/cache", 1024 * 1024 * 50, 20),
        ]
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 150,
            categories=categories,
        )
        assert report.total_size_bytes == 1024 * 1024 * 150
        assert len(report.categories) == 2

    def test_size_conversions(self):
        """Test size unit conversions."""
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 1024 * 2,  # 2 GB
            categories=[],
        )
        assert report.total_size_mb == 2048.0
        assert report.total_size_gb == 2.0

    def test_to_dict_with_percentages(self):
        """Test that percentages are calculated in to_dict."""
        categories = [
            StorageCategory("docs", "Documents", "/docs", 75, 1),
            StorageCategory("cache", "Cache", "/cache", 25, 1),
        ]
        report = StorageReport(
            total_size_bytes=100,
            categories=categories,
        )
        d = report.to_dict()

        assert d["categories"][0]["percentage"] == 75.0
        assert d["categories"][1]["percentage"] == 25.0


class TestStorageScanner:
    """Tests for StorageScanner."""

    @pytest.fixture
    def scanner(self):
        """Create a storage scanner."""
        return StorageScanner()

    def test_scan_nonexistent_directory(self, scanner):
        """Test scanning a directory that doesn't exist."""
        path = Path("/nonexistent/path/that/does/not/exist")
        size, count, mtime = scanner.scan_directory(path)

        assert size == 0
        assert count == 0
        assert mtime is None

    def test_scan_empty_directory(self, scanner):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            size, count, mtime = scanner.scan_directory(path)

            assert size == 0
            assert count == 0

    def test_scan_directory_with_files(self, scanner):
        """Test scanning a directory with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            # Create some files
            for i in range(3):
                file_path = path / f"file{i}.txt"
                file_path.write_text("x" * 100)  # 100 bytes each

            size, count, mtime = scanner.scan_directory(path)

            assert size == 300
            assert count == 3
            assert mtime is not None

    def test_scan_nested_directories(self, scanner):
        """Test scanning nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            # Create nested structure
            (path / "subdir1").mkdir()
            (path / "subdir2").mkdir()
            (path / "subdir1" / "file1.txt").write_text("a" * 50)
            (path / "subdir2" / "file2.txt").write_text("b" * 100)

            size, count, mtime = scanner.scan_directory(path)

            assert size == 150
            assert count == 2

    def test_get_largest_files(self, scanner):
        """Test getting largest files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            # Create files of different sizes
            (path / "small.txt").write_text("x" * 100)
            (path / "medium.txt").write_text("x" * 1000)
            (path / "large.txt").write_text("x" * 10000)

            # Get largest with low threshold
            large_files = scanner.get_largest_files(path, limit=2, min_size_mb=0)

            assert len(large_files) == 2
            assert large_files[0].name == "large.txt"
            assert large_files[1].name == "medium.txt"

    def test_get_largest_files_empty(self, scanner):
        """Test getting largest files from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            large_files = scanner.get_largest_files(path, limit=10)
            assert large_files == []

    def test_get_old_files(self, scanner):
        """Test getting old files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            # Create a file
            file_path = path / "old_file.txt"
            file_path.write_text("content")

            # Modify the timestamp to be old
            old_time = datetime.now() - timedelta(days=60)
            os.utime(file_path, (old_time.timestamp(), old_time.timestamp()))

            old_files = scanner.get_old_files(path, days_old=30, limit=10)

            assert len(old_files) == 1
            assert old_files[0].name == "old_file.txt"

    def test_custom_paths(self):
        """Test scanner with custom paths."""
        custom_paths = {
            "custom": {
                "path": "/custom/path",
                "description": "Custom storage location",
            }
        }
        scanner = StorageScanner(custom_paths=custom_paths)

        assert "custom" in scanner.paths
        assert scanner.paths["custom"]["path"] == "/custom/path"


class TestGrowthProjector:
    """Tests for GrowthProjector."""

    @pytest.fixture
    def projector(self):
        """Create a growth projector."""
        return GrowthProjector(history_days=30)

    def test_project_without_history(self, projector):
        """Test projection without enough history."""
        result = projector.project(
            current_size_bytes=1024 * 1024 * 100,
            available_space_bytes=1024 * 1024 * 1024,
        )

        assert result["current_size_bytes"] == 1024 * 1024 * 100
        assert result["daily_growth_bytes"] == 0
        assert result["days_until_full"] is None

    def test_project_with_growth(self, projector):
        """Test projection with historical growth."""
        # Record historical sizes
        now = datetime.now()
        projector.record_size(1000, now - timedelta(days=10))
        projector.record_size(2000, now)  # Doubled in 10 days

        result = projector.project(
            current_size_bytes=2000,
            available_space_bytes=10000,
        )

        # 1000 bytes growth over 10 days = 100 bytes/day
        assert result["daily_growth_bytes"] == 100
        assert result["weekly_growth_bytes"] == 700
        assert result["monthly_growth_bytes"] == 3000

    def test_project_days_until_full(self, projector):
        """Test days until full calculation."""
        now = datetime.now()
        projector.record_size(0, now - timedelta(days=10))
        projector.record_size(1000, now)  # 100 bytes/day

        result = projector.project(
            current_size_bytes=1000,
            available_space_bytes=1000,  # Same as daily growth * 10
        )

        assert result["days_until_full"] == 10

    def test_history_trimming(self, projector):
        """Test that old history is trimmed."""
        now = datetime.now()

        # Record old data
        projector.record_size(100, now - timedelta(days=40))
        # Record recent data
        projector.record_size(200, now)

        # Old data should be trimmed (history_days=30)
        assert len(projector._history) == 1


class TestCleanupRecommender:
    """Tests for CleanupRecommender."""

    @pytest.fixture
    def recommender(self):
        """Create a cleanup recommender."""
        return CleanupRecommender()

    def test_healthy_storage(self, recommender):
        """Test recommendations for healthy storage."""
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 100,  # 100 MB
            categories=[
                StorageCategory("docs", "Documents", "/docs", 1024 * 1024 * 50, 10),
                StorageCategory("cache", "Cache", "/cache", 1024 * 1024 * 10, 5),
            ],
        )

        recommendations = recommender.recommend(report, available_space_gb=100)

        assert any("healthy" in r.lower() for r in recommendations)

    def test_low_disk_space_warning(self, recommender):
        """Test warning for low disk space."""
        report = StorageReport(
            total_size_bytes=1024 * 1024,
            categories=[],
        )

        recommendations = recommender.recommend(report, available_space_gb=3)

        assert any("low disk space" in r.lower() for r in recommendations)

    def test_large_cache_recommendation(self, recommender):
        """Test recommendation for large cache."""
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 1024 * 2,
            categories=[
                StorageCategory(
                    "cache",
                    "Cache",
                    "/cache",
                    1024 * 1024 * 1024 * 1.5,  # 1.5 GB cache
                    100,
                ),
            ],
        )

        recommendations = recommender.recommend(report)

        assert any("cache" in r.lower() for r in recommendations)

    def test_large_logs_recommendation(self, recommender):
        """Test recommendation for large logs."""
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 1024,
            categories=[
                StorageCategory(
                    "logs",
                    "Logs",
                    "/logs",
                    1024 * 1024 * 600,  # 600 MB logs
                    1000,
                ),
            ],
        )

        recommendations = recommender.recommend(report)

        assert any("log" in r.lower() for r in recommendations)

    def test_old_files_recommendation(self, recommender):
        """Test recommendation for old files."""
        old_items = [
            StorageItem(
                f"/path/file{i}.txt",
                f"file{i}.txt",
                1024 * 1024 * 50,  # 50 MB each
                last_modified=datetime.now() - timedelta(days=60),
            )
            for i in range(5)
        ]
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 250,
            categories=[],
            old_items=old_items,
        )

        recommendations = recommender.recommend(report)

        assert any("30+ days" in r for r in recommendations)

    def test_large_files_recommendation(self, recommender):
        """Test recommendation for large files."""
        large_items = [
            StorageItem(
                "/path/huge.bin",
                "huge.bin",
                1024 * 1024 * 1024,  # 1 GB
            ),
        ]
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 1024,
            categories=[],
            largest_items=large_items,
        )

        recommendations = recommender.recommend(report)

        assert any("large file" in r.lower() for r in recommendations)

    def test_disk_full_warning(self, recommender):
        """Test warning when disk will be full soon."""
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 1024,
            categories=[],
            growth_projection={"days_until_full": 20},
        )

        recommendations = recommender.recommend(report)

        assert any("full in" in r.lower() for r in recommendations)

    def test_ollama_models_recommendation(self, recommender):
        """Test recommendation for large Ollama models."""
        report = StorageReport(
            total_size_bytes=1024 * 1024 * 1024 * 15,
            categories=[
                StorageCategory(
                    "models",
                    "Ollama models",
                    "~/.ollama/models",
                    1024 * 1024 * 1024 * 12,  # 12 GB models
                    10,
                ),
            ],
        )

        recommendations = recommender.recommend(report)

        assert any("ollama" in r.lower() for r in recommendations)


class TestStorageAnalytics:
    """Tests for StorageAnalytics."""

    @pytest.fixture
    def analytics(self):
        """Create storage analytics instance."""
        return StorageAnalytics()

    def test_analyze_returns_report(self, analytics):
        """Test that analyze returns a StorageReport."""
        # This will scan actual directories (which may not exist)
        report = analytics.analyze(include_ollama=False, check_disk_space=False)

        assert isinstance(report, StorageReport)
        assert report.computed_at is not None
        assert isinstance(report.categories, list)
        assert isinstance(report.recommendations, list)

    def test_analyze_excludes_ollama(self, analytics):
        """Test that Ollama can be excluded from analysis."""
        report = analytics.analyze(include_ollama=False)

        category_names = [c.name for c in report.categories]
        assert "models" not in category_names

    def test_get_category_breakdown(self, analytics):
        """Test getting category breakdown."""
        breakdown = analytics.get_category_breakdown()

        assert isinstance(breakdown, dict)
        for cat_name, cat_info in breakdown.items():
            assert "path" in cat_info
            assert "size_bytes" in cat_info
            assert "size_mb" in cat_info
            assert "file_count" in cat_info

    def test_report_to_dict(self, analytics):
        """Test that report can be serialised."""
        report = analytics.analyze(include_ollama=False, check_disk_space=False)
        d = report.to_dict()

        assert "total_size_bytes" in d
        assert "categories" in d
        assert "recommendations" in d
        assert "computed_at" in d

    def test_get_storage_analytics_singleton(self):
        """Test the global singleton function."""
        analytics1 = get_storage_analytics()
        analytics2 = get_storage_analytics()
        assert analytics1 is analytics2

