#!/usr/bin/env python3
"""Test plugin that sleeps for a specified duration.

This plugin is used to test execution timeout enforcement. It performs
no CPU-intensive work, just sleeps.

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import sys
import time


def main():
    """Sleep for 10 seconds (should trigger timeout in tests)."""
    print("Sleeper starting")
    time.sleep(10)
    print("Should not print - should be killed by timeout")
    sys.exit(0)


if __name__ == "__main__":
    main()
