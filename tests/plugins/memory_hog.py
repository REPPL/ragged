#!/usr/bin/env python3
"""Test plugin that attempts to exceed memory limits.

This plugin is designed to violate sandbox memory limits for testing
enforcement. It should be killed by the sandbox when it exceeds the
configured memory limit.

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import sys


def allocate_memory_mb(target_mb: int):
    """Attempt to allocate specified amount of memory.

    Args:
        target_mb: Amount of memory to allocate in megabytes
    """
    # Allocate memory in chunks to avoid immediate allocation failure
    chunk_size_mb = 10
    chunks = []

    try:
        allocated_mb = 0
        while allocated_mb < target_mb:
            # Allocate 10MB chunk (list of 10 million bytes)
            chunk = bytearray(chunk_size_mb * 1024 * 1024)
            chunks.append(chunk)
            allocated_mb += chunk_size_mb

            # Print progress to stdout
            print(f"Allocated: {allocated_mb} MB", flush=True)

        print(f"SUCCESS: Allocated {allocated_mb} MB (should not reach here)")
        return 0

    except MemoryError as e:
        print(f"MemoryError caught: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for memory hog test plugin."""
    # Attempt to allocate 1GB (should exceed typical 500MB limit)
    target_mb = 1000

    print(f"Memory hog starting: attempting to allocate {target_mb} MB")
    exit_code = allocate_memory_mb(target_mb)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
