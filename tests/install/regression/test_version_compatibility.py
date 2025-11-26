"""
Version Compatibility Regression Tests.

INSTALL-TEST-005: Tests for version compatibility issues.
"""

import json
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def test_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test home directory."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    yield home


class TestLegacyConfigFormats:
    """Regression tests for legacy configuration formats."""

    def test_v05_json_config(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of v0.5 JSON config format.

        Regression: v0.5 used JSON, later versions use YAML.
        """
        config = {
            "version": "0.5.0",
            "settings": {
                "auto_update": True,
                "log_level": "INFO",
            },
        }
        (test_home / "config.json").write_text(json.dumps(config))

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # Should not crash, config should be preserved
        assert test_home.exists()
        assert (test_home / "config.json").exists()

    def test_v06_yaml_config(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of v0.6 YAML config format.

        Regression: v0.6 changed config structure.
        """
        config_content = """
version: "0.6.0"
settings:
  auto_update: true
  log_level: INFO
  chromadb:
    persist_directory: ./data/chromadb
"""
        (test_home / "config.yaml").write_text(config_content)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        assert test_home.exists()

    def test_v07_config_with_new_fields(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of v0.7 config with new fields.

        Regression: New fields in config caused validation failures.
        """
        config_content = """
version: "0.7.0"
settings:
  auto_update: true
  telemetry: false
  experimental:
    streaming: true
    batch_processing: true
"""
        (test_home / "config.yaml").write_text(config_content)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        assert test_home.exists()


class TestLegacyDirectoryStructures:
    """Regression tests for legacy directory structures."""

    def test_v05_minimal_structure(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of v0.5 minimal structure.

        Regression: v0.5 had fewer directories.
        """
        # v0.5 only had documents and cache
        (test_home / "documents").mkdir()
        (test_home / "cache").mkdir()

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # Should add missing directories
        assert (test_home / "logs").exists()
        assert (test_home / "data").exists()

    def test_v06_structure_with_chromadb(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of v0.6 structure with ChromaDB.

        Regression: ChromaDB directory was added in v0.6.
        """
        # v0.6 structure
        for dirname in ["documents", "cache", "logs"]:
            (test_home / dirname).mkdir()

        chromadb_dir = test_home / "data" / "chromadb"
        chromadb_dir.mkdir(parents=True)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # ChromaDB directory should be preserved
        assert chromadb_dir.exists()

    def test_preserves_user_data_across_versions(
        self,
        test_home: Path,
    ) -> None:
        """Test user data is preserved during upgrade.

        Regression: Version upgrades deleted user data.
        """
        docs = test_home / "documents"
        docs.mkdir()

        # Create user documents
        for i in range(10):
            (docs / f"important_doc_{i}.txt").write_text(f"Important content {i}")

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # All documents should still exist
        for i in range(10):
            doc = docs / f"important_doc_{i}.txt"
            assert doc.exists()
            assert doc.read_text() == f"Important content {i}"


class TestAPICompatibility:
    """Regression tests for API compatibility."""

    def test_detection_api_stable(
        self,
        test_home: Path,
    ) -> None:
        """Test detection API returns expected structure.

        Regression: API changes broke existing integrations.
        """
        from ragged.install.detection import detect_all_prerequisites

        results = detect_all_prerequisites(test_home)

        # Required keys
        assert "python" in results
        assert "docker" in results
        assert "environment" in results

        # Python result structure
        assert hasattr(results["python"], "installed")
        assert hasattr(results["python"], "version")

    def test_validation_api_stable(
        self,
        test_home: Path,
    ) -> None:
        """Test validation API returns expected structure.

        Regression: Validation result structure changed unexpectedly.
        """
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        create_directory_structure(test_home)
        results = validate_environment(test_home)

        # Should be a list
        assert isinstance(results, list)

        # Each result should have expected attributes
        for result in results:
            assert hasattr(result, "passed")
            assert hasattr(result, "message")

    def test_scaffolding_api_stable(
        self,
        test_home: Path,
    ) -> None:
        """Test scaffolding API behaves as expected.

        Regression: Scaffolding function signature changed.
        """
        from ragged.install.scaffolding import create_directory_structure

        # Should accept Path
        create_directory_structure(test_home)
        assert test_home.exists()


class TestDataMigration:
    """Regression tests for data migration."""

    def test_chromadb_data_preserved(
        self,
        test_home: Path,
    ) -> None:
        """Test ChromaDB data is preserved during upgrade.

        Regression: ChromaDB data was lost during version upgrade.
        """
        chromadb_dir = test_home / "data" / "chromadb"
        chromadb_dir.mkdir(parents=True)

        # Simulate ChromaDB files
        (chromadb_dir / "chroma.sqlite3").write_text("database")
        (chromadb_dir / "index").mkdir()
        (chromadb_dir / "index" / "vector.bin").write_bytes(b"\x00" * 1000)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # All ChromaDB files should be preserved
        assert (chromadb_dir / "chroma.sqlite3").exists()
        assert (chromadb_dir / "index" / "vector.bin").exists()

    def test_cache_preserved_during_upgrade(
        self,
        test_home: Path,
    ) -> None:
        """Test cache is preserved during upgrade.

        Regression: Cache was cleared during upgrade.
        """
        cache = test_home / "cache"
        cache.mkdir()

        # Create cached items
        (cache / "embeddings.pkl").write_bytes(b"\x00" * 500)
        (cache / "model_cache").mkdir()
        (cache / "model_cache" / "model.bin").write_bytes(b"\x00" * 1000)

        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        # Cache should be preserved
        assert (cache / "embeddings.pkl").exists()
        assert (cache / "model_cache" / "model.bin").exists()
