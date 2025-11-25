#!/usr/bin/env python3
"""Test plugin that attempts to access filesystem outside allowed paths.

This plugin is designed to test filesystem restriction enforcement in the
sandbox. It attempts to read/write files in various locations to verify
that only allowed paths are accessible.

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import os
import sys
import tempfile
from pathlib import Path


def test_read_system_file():
    """Attempt to read a sensitive system file.

    Returns:
        bool: True if read succeeded, False otherwise
    """
    test_files = [
        "/etc/passwd",  # Unix systems
        "/etc/shadow",  # Unix systems (requires root, but let's try)
        "C:\\Windows\\System32\\config\\SAM",  # Windows
    ]

    for filepath in test_files:
        if not Path(filepath).exists():
            continue

        print(f"Testing read of {filepath}...")
        try:
            with open(filepath, 'r') as f:
                content = f.read(100)
            print(f"SUCCESS: Read {len(content)} bytes from {filepath}")
            return True
        except PermissionError as e:
            print(f"BLOCKED: Permission denied for {filepath}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"BLOCKED: Could not read {filepath}: {e}", file=sys.stderr)

    return False


def test_write_system_location():
    """Attempt to write to a system location.

    Returns:
        bool: True if write succeeded, False otherwise
    """
    test_paths = [
        "/tmp/ragged_test_write.txt",
        "/var/tmp/ragged_test_write.txt",
        "C:\\Windows\\Temp\\ragged_test_write.txt",
    ]

    for filepath in test_paths:
        parent = Path(filepath).parent
        if not parent.exists():
            continue

        print(f"Testing write to {filepath}...")
        try:
            with open(filepath, 'w') as f:
                f.write("test content")
            print(f"SUCCESS: Wrote to {filepath}")

            # Clean up
            try:
                os.remove(filepath)
            except Exception:
                pass

            return True
        except PermissionError as e:
            print(f"BLOCKED: Permission denied for {filepath}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"BLOCKED: Could not write {filepath}: {e}", file=sys.stderr)

    return False


def test_read_home_directory():
    """Attempt to read files from user's home directory.

    Returns:
        bool: True if read succeeded, False otherwise
    """
    home = Path.home()
    test_files = [
        home / ".bashrc",
        home / ".bash_history",
        home / ".ssh" / "id_rsa",
        home / ".ssh" / "known_hosts",
    ]

    for filepath in test_files:
        if not filepath.exists():
            continue

        print(f"Testing read of {filepath}...")
        try:
            with open(filepath, 'r') as f:
                content = f.read(100)
            print(f"SUCCESS: Read {len(content)} bytes from {filepath}")
            return True
        except PermissionError as e:
            print(f"BLOCKED: Permission denied for {filepath}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"BLOCKED: Could not read {filepath}: {e}", file=sys.stderr)

    return False


def test_traverse_filesystem():
    """Attempt to traverse filesystem to find sensitive files.

    Returns:
        bool: True if traversal succeeded, False otherwise
    """
    print("Testing filesystem traversal...")

    try:
        # Try to list /etc directory
        etc_contents = list(Path("/etc").iterdir())
        print(f"SUCCESS: Listed /etc directory ({len(etc_contents)} items)")
        return True
    except PermissionError as e:
        print(f"BLOCKED: Permission denied for /etc: {e}", file=sys.stderr)
    except Exception as e:
        print(f"BLOCKED: Could not list /etc: {e}", file=sys.stderr)

    return False


def test_access_allowed_temp():
    """Test that we CAN access allowed temporary directory.

    Returns:
        bool: True if access succeeded (expected), False otherwise
    """
    print("Testing access to allowed temp directory...")

    try:
        # Use Python's tempfile which should be allowed
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            f.write("test content from plugin")

        # Verify we can read it back
        with open(temp_path, 'r') as f:
            content = f.read()

        # Clean up
        os.remove(temp_path)

        print(f"SUCCESS: Temp file access worked (expected behavior)")
        return True
    except Exception as e:
        print(f"ERROR: Could not access temp directory: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for file accessor test plugin."""
    print("File accessor starting: attempting various filesystem operations")
    print(f"Platform: {sys.platform}")
    print(f"CWD: {os.getcwd()}")
    print(f"Home: {Path.home()}")

    # Try different filesystem operations
    results = {
        "read_system": test_read_system_file(),
        "write_system": test_write_system_location(),
        "read_home": test_read_home_directory(),
        "traverse": test_traverse_filesystem(),
        "allowed_temp": test_access_allowed_temp(),
    }

    print("\n--- Results ---")
    for test_name, success in results.items():
        status = "SUCCEEDED" if success else "BLOCKED"
        print(f"{test_name}: {status}")

    # We want allowed_temp to succeed, but all others to be blocked
    unauthorized_success = any(
        results[key] for key in ["read_system", "write_system", "read_home", "traverse"]
    )

    if unauthorized_success:
        print("\nWARNING: Some unauthorized filesystem operations succeeded")
        sys.exit(1)
    elif not results["allowed_temp"]:
        print("\nERROR: Could not access allowed temp directory")
        sys.exit(2)
    else:
        print("\nSUCCESS: Filesystem restrictions properly enforced")
        sys.exit(0)


if __name__ == "__main__":
    main()
