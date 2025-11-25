#!/usr/bin/env python3
"""Test plugin that attempts to spawn many processes (fork bomb).

This plugin is designed to violate sandbox process limits for testing
enforcement. It should be blocked from creating more processes than the
configured limit (typically 1).

v0.6.2 SECURITY-005: Plugin sandbox enforcement verification.
"""

import multiprocessing
import os
import subprocess
import sys


def worker_process(worker_id: int):
    """Worker process that just sleeps.

    Args:
        worker_id: ID of this worker
    """
    print(f"Worker {worker_id} started (PID: {os.getpid()})")
    import time
    time.sleep(10)


def test_multiprocessing_spawn():
    """Attempt to spawn multiple processes using multiprocessing.

    Returns:
        int: Number of processes successfully spawned
    """
    print("Testing multiprocessing.Process spawn...")

    processes = []
    spawned = 0

    try:
        for i in range(10):
            proc = multiprocessing.Process(target=worker_process, args=(i,))
            proc.start()
            processes.append(proc)
            spawned += 1
            print(f"Spawned process {i}")

    except OSError as e:
        print(f"BLOCKED: Process spawn failed after {spawned} processes: {e}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: Unexpected error after {spawned} processes: {e}", file=sys.stderr)

    finally:
        # Clean up spawned processes
        for proc in processes:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1)

    return spawned


def test_subprocess_spawn():
    """Attempt to spawn multiple subprocesses.

    Returns:
        int: Number of subprocesses successfully spawned
    """
    print("\nTesting subprocess.Popen spawn...")

    processes = []
    spawned = 0

    try:
        for i in range(10):
            proc = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(proc)
            spawned += 1
            print(f"Spawned subprocess {i}")

    except OSError as e:
        print(f"BLOCKED: Subprocess spawn failed after {spawned} processes: {e}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: Unexpected error after {spawned} processes: {e}", file=sys.stderr)

    finally:
        # Clean up spawned processes
        for proc in processes:
            try:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                pass

    return spawned


def test_os_fork():
    """Attempt to fork processes using os.fork() (Unix only).

    Returns:
        int: Number of forks successfully created
    """
    print("\nTesting os.fork()...")

    if not hasattr(os, 'fork'):
        print("os.fork() not available on this platform (Windows?)")
        return 0

    forked = 0
    child_pids = []

    try:
        for i in range(10):
            pid = os.fork()
            if pid == 0:
                # Child process - exit immediately
                sys.exit(0)
            else:
                # Parent process
                child_pids.append(pid)
                forked += 1
                print(f"Forked child {i} (PID: {pid})")

    except OSError as e:
        print(f"BLOCKED: Fork failed after {forked} forks: {e}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: Unexpected error after {forked} forks: {e}", file=sys.stderr)

    finally:
        # Wait for child processes
        for pid in child_pids:
            try:
                os.waitpid(pid, 0)
            except Exception:
                pass

    return forked


def main():
    """Main entry point for fork bomb test plugin."""
    print("Fork bomb starting: attempting to spawn multiple processes")
    print(f"Platform: {sys.platform}")
    print(f"PID: {os.getpid()}")

    # Try different spawning methods
    results = {
        "multiprocessing": test_multiprocessing_spawn(),
        "subprocess": test_subprocess_spawn(),
        "os.fork": test_os_fork(),
    }

    print("\n--- Results ---")
    total_spawned = 0
    for method, count in results.items():
        print(f"{method}: spawned {count} processes")
        total_spawned += count

    # We expect to be limited to 1 process (the main process itself)
    # Any additional spawns indicate the limit isn't enforced
    if total_spawned > 1:
        print(f"\nWARNING: Spawned {total_spawned} processes (limit not enforced properly)")
        sys.exit(1)
    else:
        print(f"\nSUCCESS: Process limit properly enforced (spawned {total_spawned})")
        sys.exit(0)


if __name__ == "__main__":
    # Ensure we're not in a forked child that would immediately exit
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        sys.exit(0)

    main()
