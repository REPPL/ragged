"""
Diagnostic Reports.

REFINE-001: Generate comprehensive diagnostic reports
for troubleshooting and support.
"""

import json
import logging
import platform
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib
import uuid

from ragged.install.diagnostics.framework import (
    DiagnosticResult,
    DiagnosticSeverity,
)


logger = logging.getLogger(__name__)


@dataclass
class DiagnosticReport:
    """Comprehensive diagnostic report."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    results: list[DiagnosticResult] = field(default_factory=list)
    system_info: dict[str, Any] = field(default_factory=dict)
    ragged_info: dict[str, Any] = field(default_factory=dict)
    logs: dict[str, str] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        """Count of error/critical results."""
        return sum(
            1 for r in self.results
            if r.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL)
        )

    @property
    def warning_count(self) -> int:
        """Count of warning results."""
        return sum(1 for r in self.results if r.severity == DiagnosticSeverity.WARNING)

    @property
    def has_auto_fixes(self) -> bool:
        """Check if any auto-fixes available."""
        return any(r.has_auto_fix for r in self.results)


def format_diagnostic_report(
    results: list[DiagnosticResult],
    ragged_home: Path | None = None,
    include_system_info: bool = True,
) -> str:
    """
    Format diagnostic results as human-readable report.

    Args:
        results: Diagnostic results.
        ragged_home: Path to ragged home.
        include_system_info: Whether to include system info.

    Returns:
        Formatted report string.
    """
    lines = []
    report_id = str(uuid.uuid4())[:8]

    # Header
    lines.append("=" * 60)
    lines.append(f"  DIAGNOSTIC REPORT [{report_id}]")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    error_count = sum(
        1 for r in results
        if r.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL)
    )
    warning_count = sum(1 for r in results if r.severity == DiagnosticSeverity.WARNING)

    if error_count == 0 and warning_count == 0:
        lines.append("Status: All checks passed")
    else:
        lines.append(f"Status: {error_count} errors, {warning_count} warnings")
    lines.append("")

    # System info
    if include_system_info:
        lines.append("--- SYSTEM INFO ---")
        lines.append(f"OS: {platform.system()} {platform.release()}")
        lines.append(f"Platform: {platform.platform()}")
        lines.append(f"Python: {sys.version.split()[0]}")
        lines.append(f"Architecture: {platform.machine()}")
        if ragged_home:
            lines.append(f"ragged Home: {ragged_home}")
        lines.append("")

    # Results by severity
    critical = [r for r in results if r.severity == DiagnosticSeverity.CRITICAL]
    errors = [r for r in results if r.severity == DiagnosticSeverity.ERROR]
    warnings = [r for r in results if r.severity == DiagnosticSeverity.WARNING]
    info = [r for r in results if r.severity == DiagnosticSeverity.INFO]

    if critical:
        lines.append("--- CRITICAL ISSUES ---")
        for result in critical:
            lines.extend(_format_result(result))
        lines.append("")

    if errors:
        lines.append("--- ERRORS ---")
        for result in errors:
            lines.extend(_format_result(result))
        lines.append("")

    if warnings:
        lines.append("--- WARNINGS ---")
        for result in warnings:
            lines.extend(_format_result(result))
        lines.append("")

    if info:
        lines.append("--- INFO ---")
        for result in info:
            lines.append(f"  - {result.message}")
        lines.append("")

    # Suggested fixes
    fixes = []
    for result in results:
        if result.fixes:
            for fix in result.fixes:
                if fix.command:
                    fixes.append((result.name, fix))

    if fixes:
        lines.append("--- SUGGESTED FIXES ---")
        for i, (name, fix) in enumerate(fixes, 1):
            auto = " [auto]" if fix.auto_fixable else ""
            sudo = " [sudo]" if fix.requires_sudo else ""
            lines.append(f"{i}. {fix.description}{auto}{sudo}")
            if fix.command:
                lines.append(f"   $ {fix.command}")
            lines.append("")

    # Auto-fix instruction
    has_auto_fixes = any(r.has_auto_fix for r in results)
    if has_auto_fixes:
        lines.append("--- AUTO-FIX AVAILABLE ---")
        lines.append("Run 'ragged doctor --fix' to automatically apply safe fixes")
        lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append(f"Report ID: {report_id}")
    lines.append("For support: https://github.com/ragged/ragged/issues")
    lines.append("=" * 60)

    return "\n".join(lines)


def _format_result(result: DiagnosticResult) -> list[str]:
    """Format a single result."""
    lines = []

    severity_icon = {
        DiagnosticSeverity.CRITICAL: "X",
        DiagnosticSeverity.ERROR: "X",
        DiagnosticSeverity.WARNING: "!",
        DiagnosticSeverity.INFO: "i",
    }

    icon = severity_icon.get(result.severity, "?")
    lines.append(f"[{icon}] {result.name}: {result.message}")

    if result.root_cause:
        lines.append(f"    Root cause: {result.root_cause}")

    return lines


def generate_support_bundle(
    results: list[DiagnosticResult],
    ragged_home: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """
    Generate a support bundle for troubleshooting.

    Args:
        results: Diagnostic results.
        ragged_home: Path to ragged home.
        output_path: Output path for bundle.

    Returns:
        Path to generated bundle.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path.home() / f"ragged-support-{timestamp}.tar.gz"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create diagnostic report
        report = format_diagnostic_report(results, ragged_home)
        (tmp_path / "diagnostic-report.txt").write_text(report)

        # Create JSON report
        json_report = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "system": {
                "os": platform.system(),
                "release": platform.release(),
                "platform": platform.platform(),
                "python": sys.version,
                "machine": platform.machine(),
            },
            "ragged_home": str(ragged_home),
            "results": [
                {
                    "name": r.name,
                    "category": r.category.value,
                    "severity": r.severity.value,
                    "message": r.message,
                    "root_cause": r.root_cause,
                    "details": r.details,
                    "fixes": [
                        {
                            "description": f.description,
                            "command": f.command,
                            "auto_fixable": f.auto_fixable,
                        }
                        for f in r.fixes
                    ],
                }
                for r in results
            ],
        }
        (tmp_path / "diagnostic-report.json").write_text(
            json.dumps(json_report, indent=2)
        )

        # Collect logs (last 1000 lines each)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_dir = ragged_home / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                try:
                    content = log_file.read_text()
                    lines = content.split("\n")[-1000:]
                    (logs_dir / log_file.name).write_text("\n".join(lines))
                except Exception:
                    pass

        # Collect config (sanitised)
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = ragged_home / "config.yaml"
        if config_file.exists():
            try:
                content = config_file.read_text()
                # Redact sensitive values
                import re
                content = re.sub(r"(secret|password|key|token):\s*\S+", r"\1: [REDACTED]", content, flags=re.IGNORECASE)
                (config_dir / "config.yaml").write_text(content)
            except Exception:
                pass

        # Create tarball
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(tmp_path, arcname="ragged-support")

    logger.info(f"Support bundle created: {output_path}")
    return output_path


def generate_report_id(results: list[DiagnosticResult]) -> str:
    """Generate a unique report ID based on results."""
    content = json.dumps([
        {
            "name": r.name,
            "category": r.category.value,
            "severity": r.severity.value,
        }
        for r in results
    ], sort_keys=True)

    return hashlib.sha256(content.encode()).hexdigest()[:8]
