"""Tests for backend migration."""

import pytest
from datetime import timezone

from ragged.backend.migration import BackendMigrator, MigrationResult, MigrationError


class TestBackendMigrator:
    """Test backend migration functionality."""

    def test_migrator_initialisation(self):
        """Test migrator initialises correctly."""
        migrator = BackendMigrator()
        assert migrator.supported_backends == ["chromadb", "leann"]

    def test_validate_backends_valid(self):
        """Test valid backend validation."""
        migrator = BackendMigrator()
        # Should not raise
        migrator._validate_backends("chromadb", "leann")
        migrator._validate_backends("leann", "chromadb")

    def test_validate_backends_invalid_source(self):
        """Test invalid source backend."""
        migrator = BackendMigrator()
        with pytest.raises(ValueError, match="Unsupported source backend"):
            migrator._validate_backends("invalid", "chromadb")

    def test_validate_backends_invalid_target(self):
        """Test invalid target backend."""
        migrator = BackendMigrator()
        with pytest.raises(ValueError, match="Unsupported target backend"):
            migrator._validate_backends("chromadb", "invalid")

    def test_migrate_same_backend_raises(self):
        """Test migrating to same backend raises error."""
        migrator = BackendMigrator()
        with pytest.raises(ValueError, match="Source and target backends must be different"):
            migrator.migrate("chromadb", "chromadb")


class TestMigrationResult:
    """Test migration result dataclass."""

    def test_migration_result_creation(self):
        """Test creating migration result."""
        result = MigrationResult(
            source="chromadb",
            target="leann",
            documents_migrated=1000,
            personas_migrated=["researcher"],
            duration_seconds=45.5,
            verification_passed=True
        )

        assert result.source == "chromadb"
        assert result.target == "leann"
        assert result.documents_migrated == 1000
        assert result.personas_migrated == ["researcher"]
        assert result.duration_seconds == 45.5
        assert result.verification_passed
        assert result.errors == []
        assert result.backup_path is None
