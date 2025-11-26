"""
Resource Diagnostics.

REFINE-001: Diagnostics for disk space, memory,
and other system resource issues.
"""

import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ragged.install.diagnostics.framework import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticFix,
    DiagnosticResult,
    DiagnosticSeverity,
)


logger = logging.getLogger(__name__)


class DiskSpaceDiagnostic(Diagnostic):
    """Diagnose disk space issues."""

    MIN_DISK_GB = 2.0
    RECOMMENDED_DISK_GB = 10.0

    @property
    def name(self) -> str:
        return "disk_space"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.RESOURCES

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []
        ragged_home = context.get("ragged_home", Path.home() / ".ragged")

        # Check overall disk space
        space_result = self._check_disk_space(ragged_home)
        if space_result:
            results.append(space_result)

        # Check for large files
        large_files_result = self._check_large_files(ragged_home)
        if large_files_result:
            results.append(large_files_result)

        # Check Docker disk usage
        docker_result = self._check_docker_disk()
        if docker_result:
            results.append(docker_result)

        return results

    def _check_disk_space(self, path: Path) -> DiagnosticResult | None:
        """Check available disk space."""
        try:
            check_path = path if path.exists() else path.parent

            usage = shutil.disk_usage(check_path)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_pct = (usage.used / usage.total) * 100

            details = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_pct, 1),
            }

            if free_gb < self.MIN_DISK_GB:
                return DiagnosticResult(
                    name="disk_space_critical",
                    category=DiagnosticCategory.RESOURCES,
                    severity=DiagnosticSeverity.CRITICAL,
                    message=f"Critical: Only {free_gb:.1f}GB disk space available",
                    root_cause="Disk nearly full",
                    details=details,
                    fixes=[
                        DiagnosticFix(
                            description="Clear ragged cache",
                            command="rm -rf ~/.ragged/cache/*",
                            auto_fixable=True,
                        ),
                        DiagnosticFix(
                            description="Prune Docker images",
                            command="docker system prune -f",
                            auto_fixable=True,
                        ),
                        DiagnosticFix(
                            description="Clear old logs",
                            command="find ~/.ragged/logs -type f -mtime +7 -delete",
                            auto_fixable=True,
                        ),
                    ],
                )

            elif free_gb < self.RECOMMENDED_DISK_GB:
                return DiagnosticResult(
                    name="disk_space_low",
                    category=DiagnosticCategory.RESOURCES,
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Low disk space: {free_gb:.1f}GB available (recommend {self.RECOMMENDED_DISK_GB}GB)",
                    details=details,
                    fixes=[
                        DiagnosticFix(
                            description="Clear old cache files",
                            command="ragged cleanup --cache",
                            auto_fixable=False,
                        ),
                    ],
                )

        except Exception as e:
            logger.debug(f"Failed to check disk space: {e}")

        return None

    def _check_large_files(self, path: Path) -> DiagnosticResult | None:
        """Check for unexpectedly large files."""
        if not path.exists():
            return None

        try:
            large_files = []
            total_size = 0

            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        size = item.stat().st_size
                        total_size += size

                        # Flag files > 1GB
                        if size > 1024**3:
                            large_files.append({
                                "path": str(item.relative_to(path)),
                                "size_gb": round(size / (1024**3), 2),
                            })
                    except OSError:
                        continue

            if large_files:
                return DiagnosticResult(
                    name="large_files",
                    category=DiagnosticCategory.RESOURCES,
                    severity=DiagnosticSeverity.INFO,
                    message=f"Found {len(large_files)} large files (>1GB) in ragged home",
                    details={
                        "large_files": large_files[:5],
                        "total_size_gb": round(total_size / (1024**3), 2),
                    },
                )

        except Exception as e:
            logger.debug(f"Failed to check large files: {e}")

        return None

    def _check_docker_disk(self) -> DiagnosticResult | None:
        """Check Docker disk usage."""
        try:
            result = subprocess.run(
                ["docker", "system", "df", "--format", "{{.Size}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if lines:
                    total_size = lines[0]  # First line is total

                    # Check if > 10GB
                    if "GB" in total_size:
                        try:
                            size_gb = float(total_size.replace("GB", ""))
                            if size_gb > 10:
                                return DiagnosticResult(
                                    name="docker_disk",
                                    category=DiagnosticCategory.RESOURCES,
                                    severity=DiagnosticSeverity.INFO,
                                    message=f"Docker using {total_size} disk space",
                                    fixes=[
                                        DiagnosticFix(
                                            description="Prune unused Docker resources",
                                            command="docker system prune -a -f",
                                            auto_fixable=True,
                                            destructive=True,
                                        ),
                                    ],
                                )
                        except ValueError:
                            pass

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Failed to check Docker disk: {e}")

        return None


class MemoryDiagnostic(Diagnostic):
    """Diagnose memory issues."""

    MIN_MEMORY_GB = 4.0
    RECOMMENDED_MEMORY_GB = 8.0

    @property
    def name(self) -> str:
        return "memory"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.RESOURCES

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []

        # Check available memory
        memory_result = self._check_available_memory()
        if memory_result:
            results.append(memory_result)

        # Check for OOM kills (Linux)
        oom_result = self._check_oom_kills()
        if oom_result:
            results.append(oom_result)

        return results

    def _check_available_memory(self) -> DiagnosticResult | None:
        """Check available system memory."""
        try:
            import psutil

            mem = psutil.virtual_memory()
            available_gb = mem.available / (1024**3)
            total_gb = mem.total / (1024**3)
            used_pct = mem.percent

            details = {
                "available_gb": round(available_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_pct, 1),
            }

            if available_gb < 2:
                return DiagnosticResult(
                    name="memory_critical",
                    category=DiagnosticCategory.RESOURCES,
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Low memory: {available_gb:.1f}GB available",
                    root_cause="System memory nearly exhausted",
                    details=details,
                    fixes=[
                        DiagnosticFix(
                            description="Close other applications",
                            command=None,
                            auto_fixable=False,
                        ),
                        DiagnosticFix(
                            description="Use smaller LLM model",
                            command="ollama pull llama3.2:1b",
                            auto_fixable=False,
                        ),
                    ],
                )

            elif total_gb < self.MIN_MEMORY_GB:
                return DiagnosticResult(
                    name="memory_insufficient",
                    category=DiagnosticCategory.RESOURCES,
                    severity=DiagnosticSeverity.WARNING,
                    message=f"System has only {total_gb:.1f}GB RAM (recommend {self.RECOMMENDED_MEMORY_GB}GB)",
                    details=details,
                    fixes=[
                        DiagnosticFix(
                            description="Use smaller LLM model",
                            command="ollama pull llama3.2:1b",
                            auto_fixable=False,
                        ),
                    ],
                )

        except ImportError:
            logger.debug("psutil not available for memory check")
        except Exception as e:
            logger.debug(f"Failed to check memory: {e}")

        return None

    def _check_oom_kills(self) -> DiagnosticResult | None:
        """Check for recent OOM kills (Linux)."""
        if platform.system() != "Linux":
            return None

        try:
            result = subprocess.run(
                ["dmesg"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout.lower()
                if "out of memory" in output or "oom" in output:
                    # Check if recent (last 1000 lines)
                    lines = output.split("\n")[-1000:]
                    oom_count = sum(1 for line in lines if "oom" in line or "out of memory" in line)

                    if oom_count > 0:
                        return DiagnosticResult(
                            name="oom_kills",
                            category=DiagnosticCategory.RESOURCES,
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Recent OOM (out of memory) events detected",
                            root_cause="System ran out of memory and killed processes",
                            details={"oom_count": oom_count},
                            fixes=[
                                DiagnosticFix(
                                    description="Add swap space",
                                    command="sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile",
                                    auto_fixable=False,
                                    requires_sudo=True,
                                ),
                            ],
                        )

        except Exception as e:
            logger.debug(f"Failed to check OOM kills: {e}")

        return None


class ResourceDiagnostic(Diagnostic):
    """Combined resource diagnostic."""

    @property
    def name(self) -> str:
        return "resources"

    @property
    def category(self) -> DiagnosticCategory:
        return DiagnosticCategory.RESOURCES

    def run(self, context: dict[str, Any]) -> list[DiagnosticResult]:
        results = []

        disk_diag = DiskSpaceDiagnostic()
        results.extend(disk_diag.run(context))

        memory_diag = MemoryDiagnostic()
        results.extend(memory_diag.run(context))

        return results
