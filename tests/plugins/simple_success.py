#!/usr/bin/env python3
"""Simple test plugin that executes successfully without violating limits.

This plugin is used to verify that the sandbox allows normal execution
when resource limits are not exceeded.

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import sys


def main():
    """Simple successful execution."""
    print("Hello from test plugin")
    print(f"Sum: {sum(range(1000))}")
    sys.exit(0)


if __name__ == "__main__":
    main()
