#!/usr/bin/env python3
"""Test plugin that attempts to exceed CPU time limits.

This plugin is designed to violate sandbox CPU limits for testing
enforcement. It should receive SIGXCPU when it exceeds the configured
CPU time limit.

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import sys
import time


def burn_cpu_seconds(target_seconds: int):
    """Burn CPU cycles for specified duration.

    Args:
        target_seconds: Number of seconds of CPU time to burn
    """
    print(f"CPU burner starting: attempting to use {target_seconds}s of CPU time")

    start_time = time.time()
    iterations = 0

    try:
        # Infinite loop doing CPU-intensive work
        while True:
            # CPU-intensive operation (calculate large factorials)
            result = 1
            for i in range(1, 100000):
                result *= i
                result %= 1000000007  # Keep numbers manageable

            iterations += 1

            # Print progress every 1M iterations
            if iterations % 1000000 == 0:
                elapsed = time.time() - start_time
                print(f"Iterations: {iterations}, Elapsed: {elapsed:.2f}s", flush=True)

    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 1


def main():
    """Main entry point for CPU burner test plugin."""
    # Attempt to use 60 seconds of CPU time (should exceed typical 10s limit)
    target_seconds = 60

    exit_code = burn_cpu_seconds(target_seconds)

    print("SUCCESS: CPU burner completed (should not reach here)")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
