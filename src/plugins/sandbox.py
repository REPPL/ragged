"""Plugin sandboxing and process isolation.

Provides secure execution environment for plugins with resource limits
and permission enforcement.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import subprocess
import resource
import os
import signal
import logging
import time
from enum import Enum

from ragged.plugins.permissions import PermissionType, PermissionManager

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
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: int = 0
    peak_memory_mb: int = 0


class PluginSandbox:
    """Isolated execution environment for plugins."""

    def __init__(
        self,
        plugin_name: str,
        config: Optional[SandboxConfig] = None,
        permission_manager: Optional[PermissionManager] = None,
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
        self._process: Optional[subprocess.Popen] = None

    def execute(
        self,
        executable: str,
        args: list[str],
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxExecutionResult:
        """Execute plugin in sandboxed environment.

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

        try:
            # Execute in separate process with limits
            self._process = subprocess.Popen(
                [executable] + args,
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

    def _prepare_environment(self, env: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Prepare restricted environment variables.

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

        # Block network if configured
        if self.config.block_network:
            # On Linux, could use network namespace
            # On macOS, more limited options
            pass

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

        Args:
            path: Path to check
            write: True if write access requested

        Returns:
            True if access allowed, False otherwise
        """
        if write:
            # Check write permission
            if not self.permission_manager:
                return False
            if not self.permission_manager.check_permission(self.plugin_name, PermissionType.WRITE_DOCUMENTS):
                return False
            return any(path.is_relative_to(p) for p in self.config.allowed_write_paths)
        else:
            # Check read permission
            if not self.permission_manager:
                return False
            if not self.permission_manager.check_permission(self.plugin_name, PermissionType.READ_DOCUMENTS):
                return False
            return any(path.is_relative_to(p) for p in self.config.allowed_read_paths)

    def check_network_access(self) -> bool:
        """Check if network access is allowed.

        Returns:
            True if network access allowed, False otherwise
        """
        if not self.permission_manager:
            return False
        return self.permission_manager.check_permission(self.plugin_name, PermissionType.NETWORK_API)
