# Plugin Sandbox

**Purpose:** Secure execution environment for plugins with resource limits and permission enforcement

**Status:** Implemented (v0.6.2 SECURITY-005)

---

## Overview

The plugin sandbox provides isolated execution of untrusted plugins with enforced resource limits, permission checks, and security boundaries. The implementation leverages OS-specific capabilities with graceful degradation on platforms with limited sandboxing support.

## Platform Capabilities

### Linux (Full Support)

**Resource Limits:**
- **Memory (RLIMIT_AS):** Enforced - processes killed when exceeding limit
- **CPU Time (RLIMIT_CPU):** Enforced - SIGXCPU delivered at limit, SIGKILL shortly after
- **Process Count (RLIMIT_NPROC):** Enforced - fork/spawn operations fail
- **Execution Timeout:** Enforced via process timeout

**Security Isolation:**
- **Network Isolation:** Available via network namespaces (CLONE_NEWNET) with CAP_NET_ADMIN
  - Complete network stack isolation
  - DNS, socket, and HTTP requests blocked
  - Falls back to environment-based blocking without privileges
- **Filesystem Restrictions:** Partial via mount namespaces (requires privileges)
  - Read/write path whitelisting supported
  - Temporary directory access allowed by default

### macOS/Darwin (Limited Support)

**Resource Limits:**
- **Memory (RLIMIT_AS):** Not reliably enforced - limit set but may not trigger OOM
- **CPU Time (RLIMIT_CPU):** Enforced - SIGXCPU delivered correctly
- **Process Count (RLIMIT_NPROC):** Partially enforced - behavior differs from Linux
- **Execution Timeout:** Enforced via process timeout

**Security Isolation:**
- **Network Isolation:** Not available without sandbox-exec or system extensions
  - Network operations proceed normally despite block_network=True
  - Requires additional tooling (sandbox-exec) for enforcement
- **Filesystem Restrictions:** Not available without sandbox-exec
  - Relies on standard Unix permissions only
  - No additional access control beyond OS defaults

### Other Platforms

Resource limits and security isolation capabilities vary by platform. The sandbox attempts to apply all limits but logs warnings when enforcement is unavailable.

## Configuration

```python
from ragged.plugins.sandbox import PluginSandbox, SandboxConfig

# Create sandbox configuration
config = SandboxConfig(
    max_memory_mb=500,              # Memory limit (Linux enforced)
    max_cpu_seconds=10,              # CPU time limit (enforced)
    max_processes=1,                 # Process limit (Linux enforced)
    execution_timeout_seconds=30,    # Wall-clock timeout (enforced)
    block_network=True,              # Network isolation (Linux only)
    allowed_read_paths=[],           # Read whitelist (Linux partial)
    allowed_write_paths=[],          # Write whitelist (Linux partial)
)

# Create sandbox instance
sandbox = PluginSandbox("my_plugin", config=config)

# Execute plugin
result = sandbox.execute("/path/to/plugin", args=[])
```

## Execution Results

```python
from ragged.plugins.sandbox import SandboxResult

# Possible results:
SandboxResult.SUCCESS           # Completed successfully
SandboxResult.TIMEOUT           # Exceeded time limit or timeout
SandboxResult.MEMORY_LIMIT      # Exceeded memory limit (Linux)
SandboxResult.PERMISSION_DENIED # Permission check failed
SandboxResult.CRASHED           # Non-zero exit code
SandboxResult.VIOLATION         # Security policy violation
```

## Security Considerations

### Linux Production Deployments

**Recommended Configuration:**
- Run with minimal privileges (no root)
- Enable network namespace isolation (requires CAP_NET_ADMIN)
- Set conservative resource limits (memory, CPU, processes)
- Use short execution timeouts (< 60s)
- Whitelist minimal filesystem paths

**Enhanced Security (Optional):**
- Use seccomp-bpf for syscall filtering
- Deploy in Docker/container with additional isolation
- Run under dedicated user with restricted permissions
- Enable audit logging for all plugin executions

### macOS Development Environments

**Limitations:**
- Memory limits advisory only
- No network isolation without sandbox-exec
- No filesystem restrictions without sandbox-exec
- Process limits partially enforced

**Mitigations:**
- Use execution timeout as primary safety mechanism
- Monitor resource usage externally
- Consider sandbox-exec profiles for enhanced isolation
- Test plugins in Linux environment before production

### Cross-Platform Development

**Best Practices:**
- Design plugins assuming Linux-level enforcement
- Test on target platform (Linux production, macOS development)
- Use conservative resource limits
- Implement application-level validation
- Log and monitor all plugin execution attempts

## Testing

**Enforcement Verification:**

The sandbox includes comprehensive test plugins to verify enforcement:

- `tests/plugins/memory_hog.py` - Attempts to exceed memory limits
- `tests/plugins/cpu_burner.py` - Attempts to exceed CPU time limits
- `tests/plugins/network_accessor.py` - Attempts network access
- `tests/plugins/fork_bomb.py` - Attempts to spawn many processes
- `tests/plugins/file_accessor.py` - Attempts unauthorized filesystem access

**Platform-Specific Tests:**

Tests are conditionally skipped on platforms where enforcement is unavailable:

```python
@pytest.mark.skipif(
    sys.platform == "darwin",
    reason="Memory limits not enforced on macOS"
)
def test_memory_limit_enforced():
    # Test memory limit enforcement
    ...
```

## Implementation Details

**Resource Limit Setup:**

Resource limits are applied in the preexec function before plugin execution:

```python
def set_limits():
    try:
        # Memory limit (may not be enforced on macOS)
        mem_bytes = config.max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except (ValueError, OSError) as e:
        logger.warning(f"Memory limit enforcement unavailable: {e}")

    try:
        # CPU time limit (enforced on most platforms)
        resource.setrlimit(resource.RLIMIT_CPU,
                          (config.max_cpu_seconds, config.max_cpu_seconds))
    except (ValueError, OSError) as e:
        logger.warning(f"CPU limit enforcement unavailable: {e}")

    # ... additional limits
```

**Network Isolation (Linux):**

```python
if config.block_network and sys.platform == "linux":
    import ctypes
    CLONE_NEWNET = 0x40000000

    libc = ctypes.CDLL(None, use_errno=True)
    if libc.unshare(CLONE_NEWNET) != 0:
        # Fallback to environment-based blocking
        logger.warning("Network namespace creation failed")
```

**Execution Flow:**

1. Validate plugin path (security check)
2. Prepare restricted environment
3. Apply resource limits (preexec)
4. Execute plugin with timeout
5. Monitor for limit violations
6. Classify result (success, timeout, limit exceeded, etc.)

## Troubleshooting

**"Memory limit enforcement unavailable" warning:**
- Expected on macOS - memory limits not enforced
- Use execution timeout as primary safety mechanism
- Test in Linux environment for production verification

**"Network namespace creation failed" warning:**
- Requires CAP_NET_ADMIN or root on Linux
- Consider running in Docker with appropriate capabilities
- Network access falls back to environment-based blocking

**Plugins succeed despite exceeded limits:**
- Verify platform capabilities (Linux vs macOS)
- Check that limits are appropriate for plugin workload
- Review execution result classification logic

**Permission denied errors:**
- Ensure plugin is in allowed directory
- Check file permissions and ownership
- Verify no security policy conflicts

---

## Related Documentation

- [Plugin System Overview](./README.md) - Overview of plugin architecture
- [Plugin Development Guide](./development.md) - Guide for plugin developers
- [Security Enforcement Tests](../../tests/security/test_plugin_sandbox_enforcement.py) - Test suite

---
