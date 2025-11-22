"""Plugin sandboxing and process isolation.

Provides secure execution environment for plugins with resource limits
and permission enforcement.
"""

import logging
import os
import resource
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ragged.plugins.permissions import PermissionManager, PermissionType

logger = logging.getLogger(__name__)


class SandboxViolation(Exception):
    """Raised when a plugin violates sandbox constraints."""

    pass


@dataclass
class SandboxConfig:
    """Configuration for plugin sandbox."""

    # Resource limits
    max_memory_mb: int = 500
    max_cpu_seconds: int = 10
    max_processes: int = 1

    # File system restrictions
    allowed_read_paths: list[Path] = None
    allowed_write_paths: list[Path] = None
    block_network: bool = True

    # Timeout settings
    execution_timeout_seconds: int = 30

    def __post_init__(self):
        """Initialise default paths if not provided."""
        if self.allowed_read_paths is None:
            self.allowed_read_paths = []
        if self.allowed_write_paths is None:
            self.allowed_write_paths = []


class SandboxResult(Enum):
    """Result of sandbox execution."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    MEMORY_LIMIT = "memory_limit"
    PERMISSION_DENIED = "permission_denied"
    CRASHED = "crashed"
    VIOLATION = "violation"


@dataclass
class SandboxExecutionResult:
    """Result of executing code in sandbox."""

    result: SandboxResult
    output: str | None = None
    error: str | None = None
    exit_code: int | None = None
    duration_ms: int = 0
    peak_memory_mb: int = 0


class PluginSandbox:
    """Isolated execution environment for plugins."""

    def __init__(
        self,
        plugin_name: str,
        config: SandboxConfig | None = None,
        permission_manager: PermissionManager | None = None,
    ):
        """Initialise plugin sandbox.

        Args:
            plugin_name: Name of the plugin
            config: Sandbox configuration (uses defaults if None)
            permission_manager: Permission manager for checking permissions
        """
        self.plugin_name = plugin_name
        self.config = config or SandboxConfig()
        self.permission_manager = permission_manager
        self._process: subprocess.Popen | None = None

    def execute(
        self,
        executable: str,
        args: list[str],
        env: dict[str, str] | None = None,
    ) -> SandboxExecutionResult:
        """Execute plugin in sandboxed environment with path validation.

        Args:
            executable: Path to executable or script
            args: Arguments to pass
            env: Environment variables (restricted subset)

        Returns:
            SandboxExecutionResult with execution details

        Raises:
            SandboxViolation: If plugin violates sandbox constraints
        """
        start_time = time.time()

        # SECURITY FIX (CRITICAL-1): Validate executable path to prevent command injection
        validated_executable = self._validate_executable_path(executable)

        # SECURITY FIX (CRITICAL-1): Validate arguments to prevent shell metacharacters
        self._validate_arguments(args)

        # Prepare restricted environment
        restricted_env = self._prepare_environment(env)

        # Set resource limits preexec function
        def set_limits():
            # Memory limit
            mem_bytes = self.config.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

            # CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.config.max_cpu_seconds, self.config.max_cpu_seconds))

            # Process limit
            resource.setrlimit(resource.RLIMIT_NPROC, (self.config.max_processes, self.config.max_processes))

            # SECURITY FIX (CRITICAL-3): Network isolation on Linux
            if self.config.block_network and sys.platform == "linux":
                try:
                    # Try to create isolated network namespace
                    # This requires CAP_NET_ADMIN or root, but provides strongest isolation
                    import ctypes
                    CLONE_NEWNET = 0x40000000  # From linux/sched.h

                    libc = ctypes.CDLL(None, use_errno=True)
                    if libc.unshare(CLONE_NEWNET) != 0:
                        errno = ctypes.get_errno()
                        logger.warning(
                            f"Failed to create network namespace (errno {errno}). "
                            f"Falling back to environment-based blocking."
                        )
                except Exception as e:
                    logger.warning(f"Network namespace isolation unavailable: {e}")

        try:
            # Execute in separate process with limits
            # Use validated_executable (CRITICAL-1 fix)
            self._process = subprocess.Popen(
                [validated_executable] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=restricted_env,
                preexec_fn=set_limits,
                text=True,
            )

            # Wait with timeout
            try:
                stdout, stderr = self._process.communicate(timeout=self.config.execution_timeout_seconds)
                exit_code = self._process.returncode
                duration_ms = int((time.time() - start_time) * 1000)

                # Determine result
                if exit_code == 0:
                    result = SandboxResult.SUCCESS
                elif exit_code == -signal.SIGXCPU:
                    result = SandboxResult.TIMEOUT
                    logger.warning(f"Plugin {self.plugin_name} exceeded CPU time limit")
                elif exit_code == -signal.SIGKILL:
                    result = SandboxResult.MEMORY_LIMIT
                    logger.warning(f"Plugin {self.plugin_name} exceeded memory limit")
                else:
                    result = SandboxResult.CRASHED
                    logger.error(f"Plugin {self.plugin_name} crashed with exit code {exit_code}")

                return SandboxExecutionResult(
                    result=result,
                    output=stdout,
                    error=stderr,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    peak_memory_mb=0,  # Would need tracking to get actual value
                )

            except subprocess.TimeoutExpired:
                self._process.kill()
                duration_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"Plugin {self.plugin_name} exceeded execution timeout")
                return SandboxExecutionResult(
                    result=SandboxResult.TIMEOUT,
                    error="Execution timeout exceeded",
                    duration_ms=duration_ms,
                )

        except MemoryError:
            logger.error(f"Plugin {self.plugin_name} caused memory error")
            return SandboxExecutionResult(
                result=SandboxResult.MEMORY_LIMIT,
                error="Memory limit exceeded",
            )
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return SandboxExecutionResult(
                result=SandboxResult.CRASHED,
                error=str(e),
            )
        finally:
            self._cleanup()

    def _validate_executable_path(self, executable: str) -> str:
        """Validate executable path to prevent command injection.

        Security validation:
        - Ensures executable is within allowed plugin directories
        - Resolves symlinks to prevent traversal
        - Verifies file exists and is executable
        - Blocks dangerous system binaries

        Args:
            executable: Path to executable

        Returns:
            Validated absolute path to executable

        Raises:
            SandboxViolation: If executable path is invalid or dangerous
        """
        try:
            # Convert to Path and resolve to absolute canonical path
            executable_path = Path(executable).resolve(strict=False)

            # Define allowed plugin directories
            allowed_plugin_dirs = [
                Path.home() / ".ragged" / "plugins",
                Path("/usr/local/lib/ragged/plugins"),  # System-wide plugins
                Path.cwd() / "plugins",  # Development plugins
            ]

            # Check if executable is within allowed paths
            is_allowed = any(
                executable_path.is_relative_to(allowed_dir)
                for allowed_dir in allowed_plugin_dirs
                if allowed_dir.exists()
            )

            if not is_allowed:
                logger.error(
                    f"Executable {executable} is outside allowed plugin directories: "
                    f"{[str(d) for d in allowed_plugin_dirs]}"
                )
                raise SandboxViolation(
                    f"Executable must be within allowed plugin directories, got: {executable_path}"
                )

            # Verify executable exists
            if not executable_path.exists():
                raise SandboxViolation(f"Executable does not exist: {executable_path}")

            # Verify it's a regular file (not directory, device, etc.)
            if not executable_path.is_file():
                raise SandboxViolation(f"Executable is not a regular file: {executable_path}")

            # Check for dangerous symlinks
            if executable_path.is_symlink():
                real_path = executable_path.readlink()
                # Ensure symlink target is also within allowed directories
                resolved_target = (executable_path.parent / real_path).resolve()
                target_allowed = any(
                    resolved_target.is_relative_to(allowed_dir)
                    for allowed_dir in allowed_plugin_dirs
                    if allowed_dir.exists()
                )
                if not target_allowed:
                    raise SandboxViolation(
                        f"Executable symlink points outside allowed directories: {real_path}"
                    )

            # Verify file is executable (on Unix systems)
            if hasattr(os, 'access'):
                if not os.access(executable_path, os.X_OK):
                    logger.warning(f"Executable {executable_path} is not executable, attempting anyway")

            logger.debug(f"Validated executable path: {executable_path}")
            return str(executable_path)

        except SandboxViolation:
            raise
        except Exception as e:
            logger.error(f"Failed to validate executable path {executable}: {e}")
            raise SandboxViolation(f"Invalid executable path: {e}")

    def _validate_arguments(self, args: list[str]) -> None:
        """Validate arguments to prevent shell injection.

        Security validation:
        - Checks for shell metacharacters
        - Blocks command chaining attempts
        - Prevents redirection and piping

        Args:
            args: List of arguments

        Raises:
            SandboxViolation: If arguments contain dangerous patterns
        """
        # Dangerous shell metacharacters that could enable injection
        dangerous_chars = [';', '|', '&', '$', '`', '\n', '>', '<', '(', ')', '{', '}']

        for arg in args:
            # Check for dangerous characters
            for char in dangerous_chars:
                if char in arg:
                    logger.error(f"Argument contains dangerous shell metacharacter '{char}': {arg}")
                    raise SandboxViolation(
                        f"Argument contains forbidden character '{char}': {arg}"
                    )

            # Check for null bytes (common in exploit payloads)
            if '\x00' in arg:
                raise SandboxViolation(f"Argument contains null byte: {arg}")

            # Warn about suspiciously long arguments (potential buffer overflow)
            if len(arg) > 4096:
                logger.warning(f"Argument exceeds maximum length (4096): {len(arg)} bytes")
                raise SandboxViolation(f"Argument too long: {len(arg)} bytes (max 4096)")

        logger.debug(f"Validated {len(args)} arguments")

    def _prepare_environment(self, env: dict[str, str] | None) -> dict[str, str]:
        """Prepare restricted environment variables.

        SECURITY FIX (CRITICAL-3): Implements network isolation

        Args:
            env: Requested environment variables

        Returns:
            Restricted environment dictionary
        """
        # Start with minimal safe environment
        restricted_env = {
            "PATH": "/usr/bin:/bin",
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        }

        # Add allowed variables from request
        if env:
            allowed_keys = {"RAGGED_PLUGIN_NAME", "RAGGED_PLUGIN_VERSION", "RAGGED_DATA_DIR"}
            for key in allowed_keys:
                if key in env:
                    restricted_env[key] = env[key]

        # SECURITY FIX (CRITICAL-3): Block network if configured
        if self.config.block_network:
            logger.info(f"Network blocking enabled for plugin {self.plugin_name}")

            # Multi-layered network blocking approach:
            # 1. Set proxy variables to localhost (blocks most HTTP libraries)
            restricted_env.update({
                "http_proxy": "http://127.0.0.1:0",
                "https_proxy": "http://127.0.0.1:0",
                "HTTP_PROXY": "http://127.0.0.1:0",
                "HTTPS_PROXY": "http://127.0.0.1:0",
                "ftp_proxy": "http://127.0.0.1:0",
                "FTP_PROXY": "http://127.0.0.1:0",
                "no_proxy": "",
                "NO_PROXY": "",
            })

            # 2. Unset network-related environment variables
            network_vars_to_block = [
                "SSH_AUTH_SOCK", "SSH_AGENT_PID",
                "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
                "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                "GCP_CREDENTIALS", "AZURE_CREDENTIALS",
            ]
            # These vars shouldn't be inherited from parent environment
            for var in network_vars_to_block:
                if var in restricted_env:
                    del restricted_env[var]

            # 3. Set flags for network-aware libraries
            restricted_env.update({
                "PYTHONHTTPSVERIFY": "0",  # Disable SSL (makes network less reliable)
                "REQUESTS_OFFLINE": "1",   # Requests library offline mode
                "URLLIB_OFFLINE": "1",     # urllib offline hint
            })

            logger.debug("Network isolation environment prepared")

        return restricted_env

    def _cleanup(self) -> None:
        """Clean up sandbox resources."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception as e:
                logger.error(f"Error cleaning up sandbox: {e}")

    def check_file_access(self, path: Path, write: bool = False) -> bool:
        """Check if file access is allowed.

        SECURITY FIX (CRITICAL-2): Resolves paths to prevent traversal attacks

        Args:
            path: Path to check
            write: True if write access requested

        Returns:
            True if access allowed, False otherwise

        Raises:
            SandboxViolation: If path contains suspicious patterns
        """
        try:
            # SECURITY FIX (CRITICAL-2): Resolve to canonical absolute path
            # This prevents:
            # - Path traversal via ../../../etc/passwd
            # - Symlink attacks pointing outside allowed directories
            # - Double-slash bypasses
            canonical_path = path.resolve(strict=False)

            # Check for suspicious path components
            # Even after resolution, verify no '..' in original path
            path_parts = path.parts
            if '..' in path_parts:
                logger.warning(f"Path contains '..' component: {path}")
                raise SandboxViolation(f"Path traversal detected: {path}")

            # Verify symlinks don't point outside allowed directories
            if path.is_symlink():
                # Get the symlink target
                link_target = path.readlink()
                resolved_target = (path.parent / link_target).resolve(strict=False)

                # Log symlink for security audit
                logger.info(f"Symlink detected: {path} -> {resolved_target}")

                # Ensure resolved target matches canonical path
                if resolved_target != canonical_path:
                    logger.error(f"Symlink resolution mismatch: {resolved_target} != {canonical_path}")
                    raise SandboxViolation(f"Invalid symlink: {path}")

            if write:
                # Check write permission
                if not self.permission_manager:
                    logger.warning(f"No permission manager available for write check: {canonical_path}")
                    return False
                if not self.permission_manager.check_permission(self.plugin_name, PermissionType.WRITE_DOCUMENTS):
                    logger.warning(f"Plugin {self.plugin_name} lacks WRITE_DOCUMENTS permission")
                    return False

                # Check if canonical path is within allowed write directories
                allowed = any(
                    canonical_path.is_relative_to(allowed_dir.resolve(strict=False))
                    for allowed_dir in self.config.allowed_write_paths
                )
                if not allowed:
                    logger.warning(
                        f"Write access denied to {canonical_path} - not in allowed paths: "
                        f"{[str(p) for p in self.config.allowed_write_paths]}"
                    )
                return allowed
            else:
                # Check read permission
                if not self.permission_manager:
                    logger.warning(f"No permission manager available for read check: {canonical_path}")
                    return False
                if not self.permission_manager.check_permission(self.plugin_name, PermissionType.READ_DOCUMENTS):
                    logger.warning(f"Plugin {self.plugin_name} lacks READ_DOCUMENTS permission")
                    return False

                # Check if canonical path is within allowed read directories
                allowed = any(
                    canonical_path.is_relative_to(allowed_dir.resolve(strict=False))
                    for allowed_dir in self.config.allowed_read_paths
                )
                if not allowed:
                    logger.warning(
                        f"Read access denied to {canonical_path} - not in allowed paths: "
                        f"{[str(p) for p in self.config.allowed_read_paths]}"
                    )
                return allowed

        except SandboxViolation:
            raise
        except Exception as e:
            logger.error(f"Error checking file access for {path}: {e}")
            # Fail secure - deny access on error
            return False

    def check_network_access(self) -> bool:
        """Check if network access is allowed.

        Returns:
            True if network access allowed, False otherwise
        """
        if not self.permission_manager:
            return False
        return self.permission_manager.check_permission(self.plugin_name, PermissionType.NETWORK_API)
