"""Tests for GDPR compliance toolkit.

v0.2.11 FEAT-PRIV-004: GDPR Compliance Toolkit

Tests for GDPR user rights implementation (Articles 15, 17, 20).
"""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.privacy.gdpr import GDPRToolkit, get_gdpr_toolkit


class TestGDPRToolkit:
    """Test suite for GDPR compliance toolkit."""

    def test_toolkit_initialization(self, tmp_path: Path) -> None:
        """Test GDPR toolkit initialisation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        assert toolkit.data_dir == tmp_path

    def test_toolkit_initialization_default_dir(self) -> None:
        """Test toolkit with default data directory."""
        toolkit = GDPRToolkit()

        assert toolkit.data_dir == Path.home() / ".ragged"

    def test_export_user_data_structure(self, tmp_path: Path) -> None:
        """Test export user data returns correct structure."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        export = toolkit.export_user_data()

        assert "export_metadata" in export
        assert "query_history" in export
        assert "sessions" in export
        assert "cached_queries" in export
        assert "settings" in export

    def test_export_user_data_metadata(self, tmp_path: Path) -> None:
        """Test export metadata contains required fields."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        export = toolkit.export_user_data(session_id="test123")

        metadata = export["export_metadata"]
        assert "timestamp" in metadata
        assert "session_id" in metadata
        assert metadata["session_id"] == "test123"
        assert "version" in metadata
        assert "gdpr_article" in metadata
        assert "Article 15" in metadata["gdpr_article"]
        assert "Article 20" in metadata["gdpr_article"]

    def test_export_user_data_timestamp_format(self, tmp_path: Path) -> None:
        """Test export timestamp is ISO format."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        export = toolkit.export_user_data()

        timestamp_str = export["export_metadata"]["timestamp"]
        # Should be able to parse as ISO datetime
        timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(timestamp, datetime)

    def test_export_user_data_all_sessions(self, tmp_path: Path) -> None:
        """Test exporting data for all sessions."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        export = toolkit.export_user_data(session_id=None)

        assert export["export_metadata"]["session_id"] is None

    def test_export_user_data_specific_session(self, tmp_path: Path) -> None:
        """Test exporting data for specific session."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        export = toolkit.export_user_data(session_id="abc123")

        assert export["export_metadata"]["session_id"] == "abc123"

    def test_export_user_data_to_file(self, tmp_path: Path) -> None:
        """Test exporting user data to file."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        output_path = tmp_path / "export.json"
        export = toolkit.export_user_data(output_path=output_path)

        # File should exist
        assert output_path.exists()

        # File should be valid JSON
        with open(output_path, "r", encoding="utf-8") as f:
            loaded_export = json.load(f)

        # Should match returned export
        assert loaded_export == export

    def test_export_user_data_file_encoding(self, tmp_path: Path) -> None:
        """Test export file uses UTF-8 encoding."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        output_path = tmp_path / "export.json"
        toolkit.export_user_data(output_path=output_path)

        # Read and verify UTF-8
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0

    def test_delete_user_data_requires_confirmation(self, tmp_path: Path) -> None:
        """Test that deletion requires explicit confirmation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Without confirm=True, should not delete
        deleted = toolkit.delete_user_data(session_id="test123")

        assert deleted == 0

    def test_delete_user_data_with_confirmation(self, tmp_path: Path) -> None:
        """Test deletion with explicit confirmation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # With confirm=True, should proceed
        deleted = toolkit.delete_user_data(session_id="test123", confirm=True)

        assert isinstance(deleted, int)
        assert deleted >= 0

    def test_delete_user_data_creates_backup(self, tmp_path: Path) -> None:
        """Test that deletion creates backup by default."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        toolkit.delete_user_data(session_id="test123", confirm=True, backup=True)

        # Backup directory should exist
        backup_dir = tmp_path / "backups"
        assert backup_dir.exists()

        # Should contain backup file
        backup_files = list(backup_dir.glob("deletion_backup_*.json"))
        assert len(backup_files) > 0

    def test_delete_user_data_backup_format(self, tmp_path: Path) -> None:
        """Test deletion backup file format."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        toolkit.delete_user_data(session_id="test123", confirm=True, backup=True)

        backup_files = list((tmp_path / "backups").glob("deletion_backup_*.json"))
        assert len(backup_files) > 0

        # Backup should be valid JSON
        with open(backup_files[0], "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        assert "export_metadata" in backup_data

    def test_delete_user_data_no_backup(self, tmp_path: Path) -> None:
        """Test deletion without backup."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        deleted = toolkit.delete_user_data(session_id="test123", confirm=True, backup=False)

        # Backup directory should not exist or be empty
        backup_dir = tmp_path / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("deletion_backup_*.json"))
            assert len(backup_files) == 0

    def test_delete_user_data_all_sessions(self, tmp_path: Path) -> None:
        """Test deleting all user data (no session_id)."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        deleted = toolkit.delete_user_data(session_id=None, confirm=True)

        assert isinstance(deleted, int)

    def test_delete_user_data_specific_session(self, tmp_path: Path) -> None:
        """Test deleting data for specific session."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        deleted = toolkit.delete_user_data(session_id="abc123", confirm=True)

        assert isinstance(deleted, int)

    def test_get_data_inventory_structure(self, tmp_path: Path) -> None:
        """Test data inventory returns correct structure."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        inventory = toolkit.get_data_inventory()

        assert "query_history_entries" in inventory
        assert "active_sessions" in inventory
        assert "cached_queries" in inventory
        assert "total_size_bytes" in inventory

    def test_get_data_inventory_all_sessions(self, tmp_path: Path) -> None:
        """Test inventory for all sessions."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        inventory = toolkit.get_data_inventory(session_id=None)

        assert isinstance(inventory, dict)
        assert all(isinstance(v, int) for v in inventory.values())

    def test_get_data_inventory_specific_session(self, tmp_path: Path) -> None:
        """Test inventory for specific session."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        inventory = toolkit.get_data_inventory(session_id="test123")

        assert isinstance(inventory, dict)

    def test_anonymise_data(self, tmp_path: Path) -> None:
        """Test data anonymisation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        anonymised = toolkit.anonymise_data(session_id="test123")

        assert isinstance(anonymised, int)
        assert anonymised >= 0

    def test_verify_deletion_after_delete(self, tmp_path: Path) -> None:
        """Test deletion verification after deleting data."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Delete data
        toolkit.delete_user_data(session_id="test123", confirm=True)

        # Verify deletion
        is_deleted = toolkit.verify_deletion(session_id="test123")

        # Should be True (no data for this session)
        assert is_deleted is True

    def test_verify_deletion_returns_boolean(self, tmp_path: Path) -> None:
        """Test that verify_deletion returns boolean."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        result = toolkit.verify_deletion(session_id="test123")

        assert isinstance(result, bool)

    def test_verify_deletion_checks_inventory(self, tmp_path: Path) -> None:
        """Test that verify_deletion uses inventory."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Get inventory to ensure method works
        inventory = toolkit.get_data_inventory(session_id="test123")

        # Verify deletion
        is_deleted = toolkit.verify_deletion(session_id="test123")

        # Should correlate with inventory
        total_items = sum(v for k, v in inventory.items() if k != "total_size_bytes")
        assert is_deleted == (total_items == 0)


class TestGDPRToolkitSingleton:
    """Test suite for GDPR toolkit singleton."""

    def test_get_gdpr_toolkit_creates_instance(self, tmp_path: Path) -> None:
        """Test that get_gdpr_toolkit creates instance."""
        # Reset global instance
        import src.privacy.gdpr as gdpr_module

        gdpr_module._gdpr_toolkit = None

        toolkit = get_gdpr_toolkit(data_dir=tmp_path)

        assert toolkit is not None
        assert isinstance(toolkit, GDPRToolkit)

    def test_get_gdpr_toolkit_singleton(self, tmp_path: Path) -> None:
        """Test that get_gdpr_toolkit returns same instance."""
        # Reset global instance
        import src.privacy.gdpr as gdpr_module

        gdpr_module._gdpr_toolkit = None

        toolkit1 = get_gdpr_toolkit(data_dir=tmp_path)
        toolkit2 = get_gdpr_toolkit(data_dir=tmp_path)

        assert toolkit1 is toolkit2


class TestGDPRCompliance:
    """Test suite for GDPR compliance requirements."""

    def test_right_of_access_article_15(self, tmp_path: Path) -> None:
        """Test GDPR Article 15 (Right of Access) implementation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        export = toolkit.export_user_data()

        # Should provide access to all user data
        assert export is not None
        assert isinstance(export, dict)
        # Should reference Article 15
        assert "Article 15" in export["export_metadata"]["gdpr_article"]

    def test_right_to_erasure_article_17(self, tmp_path: Path) -> None:
        """Test GDPR Article 17 (Right to Erasure) implementation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Should allow deletion
        deleted = toolkit.delete_user_data(session_id="test123", confirm=True)

        assert isinstance(deleted, int)

    def test_right_to_data_portability_article_20(self, tmp_path: Path) -> None:
        """Test GDPR Article 20 (Data Portability) implementation."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        output_path = tmp_path / "portable_export.json"
        export = toolkit.export_user_data(output_path=output_path)

        # Should export in machine-readable format (JSON)
        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert data == export
        # Should reference Article 20
        assert "Article 20" in export["export_metadata"]["gdpr_article"]

    def test_gdpr_export_is_machine_readable(self, tmp_path: Path) -> None:
        """Test that GDPR export is in machine-readable format."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        output_path = tmp_path / "export.json"
        toolkit.export_user_data(output_path=output_path)

        # Should be valid JSON (machine-readable)
        with open(output_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, dict)

    def test_gdpr_deletion_safety(self, tmp_path: Path) -> None:
        """Test that deletion has safety measures."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Should require confirmation
        deleted_without_confirm = toolkit.delete_user_data(session_id="test123")
        assert deleted_without_confirm == 0

        # Should create backup by default
        toolkit.delete_user_data(session_id="test123", confirm=True)
        assert (tmp_path / "backups").exists()

    def test_gdpr_data_minimisation(self, tmp_path: Path) -> None:
        """Test data minimisation principle (GDPR Article 5)."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        inventory = toolkit.get_data_inventory()

        # Inventory should track data amounts
        assert "query_history_entries" in inventory
        assert "cached_queries" in inventory
        assert all(isinstance(v, int) for v in inventory.values())

    def test_gdpr_anonymisation_alternative(self, tmp_path: Path) -> None:
        """Test anonymisation as alternative to deletion (Recital 26)."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Anonymisation should be available
        anonymised = toolkit.anonymise_data(session_id="test123")

        assert isinstance(anonymised, int)


class TestGDPRIntegration:
    """Integration tests for GDPR toolkit."""

    def test_full_gdpr_workflow(self, tmp_path: Path) -> None:
        """Test complete GDPR workflow."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # 1. Get inventory
        inventory = toolkit.get_data_inventory(session_id="test123")
        assert isinstance(inventory, dict)

        # 2. Export data
        export_path = tmp_path / "my_data.json"
        export = toolkit.export_user_data(
            session_id="test123", output_path=export_path
        )
        assert export_path.exists()

        # 3. Delete data
        deleted = toolkit.delete_user_data(session_id="test123", confirm=True)
        assert isinstance(deleted, int)

        # 4. Verify deletion
        is_deleted = toolkit.verify_deletion(session_id="test123")
        assert isinstance(is_deleted, bool)

    def test_export_then_delete_workflow(self, tmp_path: Path) -> None:
        """Test export before delete workflow."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Export first
        export = toolkit.export_user_data(session_id="user123")
        assert export is not None

        # Then delete
        deleted = toolkit.delete_user_data(session_id="user123", confirm=True)

        # Backup should exist (automatic)
        backups = list((tmp_path / "backups").glob("deletion_backup_*.json"))
        assert len(backups) > 0

    def test_multiple_sessions_independence(self, tmp_path: Path) -> None:
        """Test that GDPR operations on sessions are independent."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Export different sessions
        export1 = toolkit.export_user_data(session_id="session1")
        export2 = toolkit.export_user_data(session_id="session2")

        # Should have different session IDs
        assert export1["export_metadata"]["session_id"] == "session1"
        assert export2["export_metadata"]["session_id"] == "session2"

    def test_gdpr_audit_trail(self, tmp_path: Path) -> None:
        """Test that GDPR operations create audit trail."""
        toolkit = GDPRToolkit(data_dir=tmp_path)

        # Deletion should create backup (audit record)
        toolkit.delete_user_data(session_id="test123", confirm=True, backup=True)

        # Backup exists as audit trail
        backups = list((tmp_path / "backups").glob("deletion_backup_*.json"))
        assert len(backups) > 0

        # Backup contains metadata
        with open(backups[0], "r") as f:
            backup = json.load(f)

        assert "export_metadata" in backup
        assert "timestamp" in backup["export_metadata"]


# Mark all tests as privacy tests
pytestmark = pytest.mark.privacy
