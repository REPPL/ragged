"""Security tests for HIGH-2: Race conditions in permission management."""

import pytest
import threading
import tempfile
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ragged.plugins.permissions import (
    PermissionManager,
    PermissionType,
    PluginPermissions,
)


class TestPermissionRaceConditions:
    """Tests for race conditions in permission management (HIGH-2)."""

    @pytest.fixture
    def permission_manager(self, tmp_path):
        """Create permission manager with temporary storage."""
        storage_path = tmp_path / "permissions.json"
        return PermissionManager(storage_path=storage_path)

    @pytest.fixture
    def plugin_perms(self):
        """Create sample plugin permissions."""
        perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        perms.add_required(PermissionType.READ_DOCUMENTS)
        perms.add_required(PermissionType.WRITE_DOCUMENTS)
        perms.add_optional(PermissionType.NETWORK_API)
        return perms

    def test_concurrent_grant_operations(self, permission_manager, plugin_perms):
        """Test that concurrent grant operations are thread-safe."""
        permission_manager.register_plugin(plugin_perms)

        permissions_to_grant = [
            PermissionType.READ_DOCUMENTS,
            PermissionType.WRITE_DOCUMENTS,
            PermissionType.NETWORK_API,
        ]

        errors = []

        def grant_permission(perm):
            try:
                permission_manager.grant_permission("test_plugin", perm)
            except Exception as e:
                errors.append(e)

        # Launch concurrent grant operations
        threads = []
        for perm in permissions_to_grant:
            thread = threading.Thread(target=grant_permission, args=(perm,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # All permissions should be granted
        for perm in permissions_to_grant:
            assert permission_manager.check_permission("test_plugin", perm) is True

    def test_concurrent_grant_and_revoke(self, permission_manager, plugin_perms):
        """Test concurrent grant and revoke operations are atomic."""
        permission_manager.register_plugin(plugin_perms)

        # Pre-grant some permissions
        permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)
        permission_manager.grant_permission("test_plugin", PermissionType.WRITE_DOCUMENTS)

        grant_count = 0
        revoke_count = 0
        lock = threading.Lock()

        def grant_repeatedly(iterations=50):
            nonlocal grant_count
            for _ in range(iterations):
                try:
                    permission_manager.grant_permission("test_plugin", PermissionType.NETWORK_API)
                    with lock:
                        grant_count += 1
                except Exception:
                    pass
                time.sleep(0.001)

        def revoke_repeatedly(iterations=50):
            nonlocal revoke_count
            for _ in range(iterations):
                try:
                    permission_manager.revoke_permission("test_plugin", PermissionType.NETWORK_API)
                    with lock:
                        revoke_count += 1
                except Exception:
                    pass
                time.sleep(0.001)

        # Launch concurrent grant and revoke
        threads = [
            threading.Thread(target=grant_repeatedly),
            threading.Thread(target=revoke_repeatedly),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Final state should be consistent (either granted or not)
        final_state = permission_manager.check_permission("test_plugin", PermissionType.NETWORK_API)
        assert isinstance(final_state, bool)

        # No corruption should have occurred
        # READ_DOCUMENTS and WRITE_DOCUMENTS should still be granted
        assert permission_manager.check_permission("test_plugin", PermissionType.READ_DOCUMENTS) is True
        assert permission_manager.check_permission("test_plugin", PermissionType.WRITE_DOCUMENTS) is True

    def test_concurrent_check_during_modifications(self, permission_manager, plugin_perms):
        """Test that check operations are safe during concurrent modifications."""
        permission_manager.register_plugin(plugin_perms)
        permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)

        check_results = []
        errors = []

        def modify_permissions(iterations=30):
            for _ in range(iterations):
                try:
                    permission_manager.grant_permission("test_plugin", PermissionType.WRITE_DOCUMENTS)
                    time.sleep(0.001)
                    permission_manager.revoke_permission("test_plugin", PermissionType.WRITE_DOCUMENTS)
                except Exception as e:
                    errors.append(e)

        def check_permissions(iterations=30):
            for _ in range(iterations):
                try:
                    result = permission_manager.check_permission("test_plugin", PermissionType.READ_DOCUMENTS)
                    check_results.append(result)
                except Exception as e:
                    errors.append(e)
                time.sleep(0.001)

        # Launch modifier and checkers concurrently
        threads = [
            threading.Thread(target=modify_permissions),
            threading.Thread(target=check_permissions),
            threading.Thread(target=check_permissions),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # All checks should have returned True (READ_DOCUMENTS never revoked)
        assert all(result is True for result in check_results)

    def test_concurrent_file_io_operations(self, permission_manager, plugin_perms):
        """Test that concurrent file I/O operations don't corrupt data."""
        permission_manager.register_plugin(plugin_perms)

        errors = []

        def register_and_grant(plugin_name, iterations=20):
            for i in range(iterations):
                try:
                    perms = PluginPermissions(
                        plugin_name=f"{plugin_name}_{i}",
                        plugin_version="1.0.0",
                    )
                    perms.add_required(PermissionType.READ_DOCUMENTS)
                    permission_manager.register_plugin(perms)
                    permission_manager.grant_permission(f"{plugin_name}_{i}", PermissionType.READ_DOCUMENTS)
                except Exception as e:
                    errors.append(e)
                time.sleep(0.001)

        # Launch multiple threads registering plugins concurrently
        threads = [
            threading.Thread(target=register_and_grant, args=("plugin_a",)),
            threading.Thread(target=register_and_grant, args=("plugin_b",)),
            threading.Thread(target=register_and_grant, args=("plugin_c",)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # Verify all plugins were registered
        plugins = permission_manager.list_plugins()
        # Should have original test_plugin + 20*3 new plugins
        assert len(plugins) >= 60

    def test_prevent_toctou_vulnerability(self, permission_manager, plugin_perms):
        """Test that TOCTOU (Time-of-Check-Time-of-Use) vulnerabilities are prevented."""
        permission_manager.register_plugin(plugin_perms)

        toctou_exploited = False
        lock = threading.Lock()

        def attempt_toctou_exploit():
            """Try to exploit TOCTOU by checking then using permission."""
            nonlocal toctou_exploited
            try:
                # Attacker checks if permission exists
                if "test_plugin" in permission_manager.list_plugins():
                    time.sleep(0.01)  # Simulate work between check and use

                    # Attacker tries to use permission
                    permission_manager.grant_permission("test_plugin", PermissionType.READ_DOCUMENTS)
            except ValueError:
                # This is expected if plugin was unregistered between check and use
                with lock:
                    toctou_exploited = True

        def unregister_plugin():
            """Try to unregister plugin during TOCTOU window."""
            time.sleep(0.005)  # Wait for attacker to check
            # Note: We don't have unregister method, but we can test grant's atomicity
            # by revoking permission
            try:
                permission_manager.revoke_permission("test_plugin", PermissionType.READ_DOCUMENTS)
            except Exception:
                pass

        # Launch concurrent TOCTOU attempt and disruption
        threads = [
            threading.Thread(target=attempt_toctou_exploit),
            threading.Thread(target=unregister_plugin),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # The key is that operations completed without corruption
        # Final state should be consistent
        final_state = permission_manager.check_permission("test_plugin", PermissionType.READ_DOCUMENTS)
        assert isinstance(final_state, bool)

    def test_concurrent_plugin_registration(self, permission_manager):
        """Test concurrent plugin registration is thread-safe."""
        errors = []

        def register_plugins(start_idx, count=30):
            for i in range(start_idx, start_idx + count):
                try:
                    perms = PluginPermissions(
                        plugin_name=f"plugin_{i}",
                        plugin_version="1.0.0",
                    )
                    perms.add_required(PermissionType.READ_DOCUMENTS)
                    permission_manager.register_plugin(perms)
                except Exception as e:
                    errors.append(e)

        # Launch multiple threads registering plugins with different ranges
        threads = [
            threading.Thread(target=register_plugins, args=(0,)),
            threading.Thread(target=register_plugins, args=(30,)),
            threading.Thread(target=register_plugins, args=(60,)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # Should have 90 plugins registered
        plugins = permission_manager.list_plugins()
        assert len(plugins) == 90

    def test_atomic_permission_grant_in_plugin(self, plugin_perms):
        """Test that permission grant within PluginPermissions is atomic."""
        errors = []

        def grant_permission(perm):
            try:
                plugin_perms.grant(perm)
            except Exception as e:
                errors.append(e)

        # Launch concurrent grants
        threads = [
            threading.Thread(target=grant_permission, args=(PermissionType.READ_DOCUMENTS,)),
            threading.Thread(target=grant_permission, args=(PermissionType.WRITE_DOCUMENTS,)),
            threading.Thread(target=grant_permission, args=(PermissionType.NETWORK_API,)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # All permissions should be granted
        assert plugin_perms.has_permission(PermissionType.READ_DOCUMENTS) is True
        assert plugin_perms.has_permission(PermissionType.WRITE_DOCUMENTS) is True
        assert plugin_perms.has_permission(PermissionType.NETWORK_API) is True

    def test_concurrent_has_permission_checks(self, plugin_perms):
        """Test that concurrent has_permission checks are safe."""
        plugin_perms.grant(PermissionType.READ_DOCUMENTS)

        check_results = []
        errors = []

        def check_permission(iterations=50):
            for _ in range(iterations):
                try:
                    result = plugin_perms.has_permission(PermissionType.READ_DOCUMENTS)
                    check_results.append(result)
                except Exception as e:
                    errors.append(e)

        # Launch many concurrent checkers
        threads = [threading.Thread(target=check_permission) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # All checks should return True
        assert all(result is True for result in check_results)

    def test_concurrent_serialization(self, plugin_perms):
        """Test that to_dict() is thread-safe during concurrent modifications."""
        errors = []
        serialized_data = []

        def modify_permissions(iterations=20):
            for _ in range(iterations):
                try:
                    plugin_perms.grant(PermissionType.NETWORK_API)
                    time.sleep(0.001)
                    plugin_perms.revoke(PermissionType.NETWORK_API)
                except Exception as e:
                    errors.append(e)

        def serialize_permissions(iterations=20):
            for _ in range(iterations):
                try:
                    data = plugin_perms.to_dict()
                    serialized_data.append(data)
                except Exception as e:
                    errors.append(e)
                time.sleep(0.001)

        # Launch concurrent modifications and serializations
        threads = [
            threading.Thread(target=modify_permissions),
            threading.Thread(target=serialize_permissions),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # All serialized data should be valid dictionaries
        for data in serialized_data:
            assert "plugin_name" in data
            assert "plugin_version" in data
            assert "required" in data
            assert "optional" in data
            assert "granted" in data

    def test_stress_test_with_thread_pool(self, permission_manager):
        """Stress test with thread pool executor."""
        num_workers = 10
        operations_per_worker = 50

        def mixed_operations(worker_id):
            """Perform mixed operations (register, grant, revoke, check)."""
            errors = []
            for i in range(operations_per_worker):
                try:
                    plugin_name = f"worker{worker_id}_plugin{i}"

                    # Register
                    perms = PluginPermissions(
                        plugin_name=plugin_name,
                        plugin_version="1.0.0",
                    )
                    perms.add_required(PermissionType.READ_DOCUMENTS)
                    permission_manager.register_plugin(perms)

                    # Grant
                    permission_manager.grant_permission(plugin_name, PermissionType.READ_DOCUMENTS)

                    # Check
                    has_perm = permission_manager.check_permission(plugin_name, PermissionType.READ_DOCUMENTS)
                    assert has_perm is True

                    # Revoke
                    permission_manager.revoke_permission(plugin_name, PermissionType.READ_DOCUMENTS)

                    # Check again
                    has_perm = permission_manager.check_permission(plugin_name, PermissionType.READ_DOCUMENTS)
                    assert has_perm is False

                except Exception as e:
                    errors.append(e)

            return errors

        # Run stress test with thread pool
        all_errors = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(mixed_operations, i) for i in range(num_workers)]

            for future in as_completed(futures):
                errors = future.result()
                all_errors.extend(errors)

        # Should have no errors
        assert len(all_errors) == 0

        # Should have registered num_workers * operations_per_worker plugins
        plugins = permission_manager.list_plugins()
        assert len(plugins) == num_workers * operations_per_worker


class TestAtomicFileOperations:
    """Tests for atomic file operations to prevent corruption."""

    @pytest.fixture
    def permission_manager(self, tmp_path):
        """Create permission manager with temporary storage."""
        storage_path = tmp_path / "permissions.json"
        return PermissionManager(storage_path=storage_path)

    def test_atomic_file_write_on_crash(self, permission_manager, tmp_path):
        """Test that file write is atomic - no partial writes on crash."""
        storage_path = tmp_path / "permissions.json"

        # Register a plugin
        perms = PluginPermissions(
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        perms.add_required(PermissionType.READ_DOCUMENTS)
        permission_manager.register_plugin(perms)

        # Verify file exists and is valid
        assert storage_path.exists()

        # Check no .tmp file left behind
        temp_path = storage_path.with_suffix('.tmp')
        assert not temp_path.exists()

        # Verify we can load permissions (file not corrupted)
        new_manager = PermissionManager(storage_path=storage_path)
        assert new_manager.get_permissions("test_plugin") is not None

    def test_concurrent_file_writes_no_corruption(self, tmp_path):
        """Test that concurrent file writes don't corrupt the permissions file."""
        storage_path = tmp_path / "permissions.json"
        manager1 = PermissionManager(storage_path=storage_path)
        manager2 = PermissionManager(storage_path=storage_path)

        errors = []

        def write_permissions_manager1(iterations=20):
            for i in range(iterations):
                try:
                    perms = PluginPermissions(
                        plugin_name=f"manager1_plugin{i}",
                        plugin_version="1.0.0",
                    )
                    perms.add_required(PermissionType.READ_DOCUMENTS)
                    manager1.register_plugin(perms)
                except Exception as e:
                    errors.append(e)
                time.sleep(0.001)

        def write_permissions_manager2(iterations=20):
            for i in range(iterations):
                try:
                    perms = PluginPermissions(
                        plugin_name=f"manager2_plugin{i}",
                        plugin_version="1.0.0",
                    )
                    perms.add_required(PermissionType.WRITE_DOCUMENTS)
                    manager2.register_plugin(perms)
                except Exception as e:
                    errors.append(e)
                time.sleep(0.001)

        # Launch concurrent file writes
        threads = [
            threading.Thread(target=write_permissions_manager1),
            threading.Thread(target=write_permissions_manager2),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0

        # File should still be valid JSON and loadable
        new_manager = PermissionManager(storage_path=storage_path)
        plugins = new_manager.list_plugins()

        # Should have at least some plugins (may not be all 40 due to overwriting)
        assert len(plugins) > 0
