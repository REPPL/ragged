#!/usr/bin/env python3
"""Test plugin that attempts to access the network.

This plugin is designed to violate sandbox network isolation for testing
enforcement. On Linux with proper capabilities, it should fail to connect.
On other platforms, network access may succeed (platform-dependent).

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import socket
import sys
import urllib.request


def test_socket_connection():
    """Attempt to create a raw socket connection.

    Returns:
        bool: True if connection succeeded, False otherwise
    """
    print("Testing raw socket connection to google.com:80...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("google.com", 80))
        sock.close()
        print("SUCCESS: Raw socket connection succeeded")
        return True
    except OSError as e:
        print(f"BLOCKED: Raw socket connection failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return False


def test_http_request():
    """Attempt to make an HTTP request.

    Returns:
        bool: True if request succeeded, False otherwise
    """
    print("Testing HTTP request to http://example.com...")

    try:
        response = urllib.request.urlopen("http://example.com", timeout=5)
        data = response.read()
        print(f"SUCCESS: HTTP request succeeded, received {len(data)} bytes")
        return True
    except urllib.error.URLError as e:
        print(f"BLOCKED: HTTP request failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return False


def test_dns_resolution():
    """Attempt to resolve a domain name.

    Returns:
        bool: True if resolution succeeded, False otherwise
    """
    print("Testing DNS resolution for google.com...")

    try:
        ip_address = socket.gethostbyname("google.com")
        print(f"SUCCESS: DNS resolution succeeded, IP: {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"BLOCKED: DNS resolution failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for network accessor test plugin."""
    print("Network accessor starting: attempting various network operations")
    print(f"Platform: {sys.platform}")

    # Try different network operations
    results = {
        "dns": test_dns_resolution(),
        "socket": test_socket_connection(),
        "http": test_http_request(),
    }

    print("\n--- Results ---")
    for test_name, success in results.items():
        status = "SUCCEEDED" if success else "BLOCKED"
        print(f"{test_name}: {status}")

    # Exit with failure if any test succeeded (we want them to be blocked)
    if any(results.values()):
        print("\nWARNING: Some network operations succeeded (not properly isolated)")
        sys.exit(1)
    else:
        print("\nSUCCESS: All network operations properly blocked")
        sys.exit(0)


if __name__ == "__main__":
    main()
