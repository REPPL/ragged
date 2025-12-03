# Plugin System Documentation

**Purpose:** Documentation for the ragged plugin system, including sandbox security, permissions, and development guidelines.

**Status:** Active Development (v0.6.2+)

---

## Overview

The ragged plugin system provides extensible functionality through secure, sandboxed plugin execution. All plugins run with enforced resource limits, permission checks, and security boundaries.

## Documentation Contents

### Security & Sandboxing

- **[sandbox.md](./sandbox.md)** - Plugin sandbox implementation and platform capabilities
  - Resource limits (memory, CPU, processes, timeout)
  - Network isolation (Linux) and filesystem restrictions
  - Platform-specific behaviour (Linux vs macOS)
  - Security considerations and best practices

### Core Plugin System

- **[../../../src/plugins/](../../../src/plugins/)** - Plugin system implementation
  - `sandbox.py` - Sandbox execution environment
  - `permissions.py` - Permission management system
  - `manager.py` - Plugin lifecycle management
  - `loader.py` - Plugin discovery and loading

### Testing

- **[../../../tests/plugins/](../../../tests/plugins/)** - Plugin test suite
  - Test plugins for sandbox enforcement verification
  - Permission system tests
  - Integration tests

## Plugin System Features

### Security (v0.6.2)

**Sandbox Enforcement:**
- Memory limits (RLIMIT_AS)
- CPU time limits (RLIMIT_CPU)
- Process limits (RLIMIT_NPROC)
- Execution timeouts
- Network isolation (Linux with CAP_NET_ADMIN)
- Filesystem restrictions (Linux namespaces)

**Permission Management:**
- Granular permission types (network, filesystem, system)
- User consent tracking
- Audit logging
- Permission revocation

### Platform Support

**Linux (Full Support):**
- All resource limits enforced
- Network namespace isolation available
- Mount namespace support (requires privileges)
- Complete sandbox enforcement

**macOS/Darwin (Limited Support):**
- CPU and timeout limits enforced
- Memory limits advisory only
- No network isolation without sandbox-exec
- Relies on standard Unix permissions

**Other Platforms:**
- Varies by OS capabilities
- Graceful degradation with warnings

## Development Guidelines

### Creating Plugins

Plugins must:
1. Be placed in allowed plugin directories
2. Declare required permissions
3. Handle resource limit exceptions gracefully
4. Follow security best practices

### Testing Plugins

Use the sandbox enforcement test suite:
```bash
pytest tests/security/test_plugin_sandbox_enforcement.py -v
```

Test plugins available:
- `memory_hog.py` - Memory limit testing
- `cpu_burner.py` - CPU limit testing
- `network_accessor.py` - Network isolation testing
- `fork_bomb.py` - Process limit testing
- `file_accessor.py` - Filesystem restriction testing

### Security Considerations

**Production Deployments (Linux):**
- Run with minimal privileges
- Enable network namespace isolation
- Set conservative resource limits
- Use short execution timeouts
- Whitelist minimal filesystem paths

**Development Environments (macOS):**
- Use execution timeout as primary safety
- Monitor resource usage externally
- Test in Linux environment before production
- Consider sandbox-exec for enhanced isolation

## Related Documentation

- [Security Audit Baseline](../../development/audit/security/baseline/v0.6.0-security-audit.md) - Security assessment and findings
- [v0.6.2 Roadmap](../roadmap/version/v0.6/v0.6.2.md) - Security enhancements (SECURITY-003, SECURITY-004, SECURITY-005)
- [Sandbox Implementation](sandbox.md) - Detailed sandbox documentation

---
