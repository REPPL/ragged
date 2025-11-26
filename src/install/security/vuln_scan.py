"""
Vulnerability Scanning.

INSTALL-SEC-005: Dependency vulnerability scanning.
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VulnSeverity(Enum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class Vulnerability:
    """Vulnerability information."""

    id: str  # CVE ID or advisory ID
    package: str
    installed_version: str
    fixed_version: str | None
    severity: VulnSeverity
    description: str
    url: str | None = None


@dataclass
class VulnScanResult:
    """Result of vulnerability scan."""

    timestamp: str
    scanner: str
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    packages_scanned: int = 0
    scan_successful: bool = True
    error_message: str | None = None

    def has_critical(self) -> bool:
        """Check if there are critical vulnerabilities."""
        return any(v.severity == VulnSeverity.CRITICAL for v in self.vulnerabilities)

    def has_high(self) -> bool:
        """Check if there are high severity vulnerabilities."""
        return any(v.severity == VulnSeverity.HIGH for v in self.vulnerabilities)

    def get_by_severity(self, severity: VulnSeverity) -> list[Vulnerability]:
        """Get vulnerabilities by severity."""
        return [v for v in self.vulnerabilities if v.severity == severity]


def scan_python_dependencies(
    requirements_file: Path | None = None,
) -> VulnScanResult:
    """
    Scan Python dependencies for vulnerabilities.

    Uses pip-audit if available, falls back to safety.

    Args:
        requirements_file: Path to requirements.txt (optional).

    Returns:
        VulnScanResult with findings.
    """
    result = VulnScanResult(
        timestamp=datetime.now().isoformat(),
        scanner="pip-audit",
    )

    # Try pip-audit first
    try:
        cmd = ["pip-audit", "--format", "json"]
        if requirements_file:
            cmd.extend(["--requirement", str(requirements_file)])

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if proc.returncode == 0 or proc.stdout:
            return _parse_pip_audit_output(proc.stdout, result)

    except FileNotFoundError:
        logger.debug("pip-audit not installed")
    except subprocess.TimeoutExpired:
        result.error_message = "pip-audit scan timed out"
        result.scan_successful = False
        return result

    # Try safety as fallback
    result.scanner = "safety"
    try:
        cmd = ["safety", "check", "--json"]
        if requirements_file:
            cmd.extend(["--file", str(requirements_file)])

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        return _parse_safety_output(proc.stdout, result)

    except FileNotFoundError:
        result.error_message = "Neither pip-audit nor safety installed"
        result.scan_successful = False
    except subprocess.TimeoutExpired:
        result.error_message = "safety scan timed out"
        result.scan_successful = False

    return result


def _parse_pip_audit_output(
    output: str,
    result: VulnScanResult,
) -> VulnScanResult:
    """Parse pip-audit JSON output."""
    try:
        data = json.loads(output)

        # pip-audit returns list of vulnerable packages
        if isinstance(data, list):
            for item in data:
                package = item.get("name", "unknown")
                version = item.get("version", "unknown")

                for vuln in item.get("vulns", []):
                    result.vulnerabilities.append(Vulnerability(
                        id=vuln.get("id", "UNKNOWN"),
                        package=package,
                        installed_version=version,
                        fixed_version=vuln.get("fix_versions", [None])[0] if vuln.get("fix_versions") else None,
                        severity=_parse_severity(vuln.get("severity", "unknown")),
                        description=vuln.get("description", "No description available"),
                        url=vuln.get("link"),
                    ))

            result.packages_scanned = len(data)

    except json.JSONDecodeError as e:
        result.error_message = f"Failed to parse pip-audit output: {e}"
        result.scan_successful = False

    return result


def _parse_safety_output(
    output: str,
    result: VulnScanResult,
) -> VulnScanResult:
    """Parse safety JSON output."""
    try:
        data = json.loads(output)

        # safety output format varies by version
        vulns = data if isinstance(data, list) else data.get("vulnerabilities", [])

        for vuln in vulns:
            if isinstance(vuln, list):
                # Old safety format: [package, installed, affected, id, desc]
                result.vulnerabilities.append(Vulnerability(
                    id=vuln[3] if len(vuln) > 3 else "UNKNOWN",
                    package=vuln[0] if len(vuln) > 0 else "unknown",
                    installed_version=vuln[1] if len(vuln) > 1 else "unknown",
                    fixed_version=None,
                    severity=VulnSeverity.UNKNOWN,
                    description=vuln[4] if len(vuln) > 4 else "No description",
                ))
            elif isinstance(vuln, dict):
                result.vulnerabilities.append(Vulnerability(
                    id=vuln.get("vulnerability_id", vuln.get("cve", "UNKNOWN")),
                    package=vuln.get("package_name", "unknown"),
                    installed_version=vuln.get("analyzed_version", "unknown"),
                    fixed_version=vuln.get("fixed_versions", [None])[0] if vuln.get("fixed_versions") else None,
                    severity=_parse_severity(vuln.get("severity", "unknown")),
                    description=vuln.get("advisory", "No description"),
                    url=vuln.get("more_info_path"),
                ))

    except json.JSONDecodeError as e:
        result.error_message = f"Failed to parse safety output: {e}"
        result.scan_successful = False

    return result


def _parse_severity(severity_str: str) -> VulnSeverity:
    """Parse severity string to enum."""
    severity_map = {
        "critical": VulnSeverity.CRITICAL,
        "high": VulnSeverity.HIGH,
        "medium": VulnSeverity.MEDIUM,
        "moderate": VulnSeverity.MEDIUM,
        "low": VulnSeverity.LOW,
    }
    return severity_map.get(severity_str.lower(), VulnSeverity.UNKNOWN)


def scan_docker_images(
    images: list[str] | None = None,
) -> VulnScanResult:
    """
    Scan Docker images for vulnerabilities.

    Uses trivy if available.

    Args:
        images: List of image names to scan.

    Returns:
        VulnScanResult with findings.
    """
    result = VulnScanResult(
        timestamp=datetime.now().isoformat(),
        scanner="trivy",
    )

    if images is None:
        images = ["chromadb/chroma:latest"]

    try:
        for image in images:
            cmd = [
                "trivy", "image",
                "--severity", "CRITICAL,HIGH",
                "--format", "json",
                image,
            ]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if proc.returncode == 0 or proc.stdout:
                _parse_trivy_output(proc.stdout, result, image)

            result.packages_scanned += 1

    except FileNotFoundError:
        result.error_message = "trivy not installed"
        result.scan_successful = False
    except subprocess.TimeoutExpired:
        result.error_message = "trivy scan timed out"
        result.scan_successful = False

    return result


def _parse_trivy_output(
    output: str,
    result: VulnScanResult,
    image: str,
) -> None:
    """Parse trivy JSON output."""
    try:
        data = json.loads(output)

        results = data.get("Results", [])
        for target in results:
            vulns = target.get("Vulnerabilities", [])
            for vuln in vulns:
                result.vulnerabilities.append(Vulnerability(
                    id=vuln.get("VulnerabilityID", "UNKNOWN"),
                    package=f"{image}:{vuln.get('PkgName', 'unknown')}",
                    installed_version=vuln.get("InstalledVersion", "unknown"),
                    fixed_version=vuln.get("FixedVersion"),
                    severity=_parse_severity(vuln.get("Severity", "unknown")),
                    description=vuln.get("Title", vuln.get("Description", "No description")),
                    url=vuln.get("PrimaryURL"),
                ))

    except json.JSONDecodeError:
        pass


def format_vuln_report(result: VulnScanResult) -> str:
    """
    Format vulnerability scan result as report.

    Args:
        result: Scan result.

    Returns:
        Formatted report string.
    """
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("  VULNERABILITY SCAN REPORT")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"Scanner: {result.scanner}")
    lines.append(f"Timestamp: {result.timestamp}")
    lines.append(f"Packages Scanned: {result.packages_scanned}")
    lines.append("")

    if not result.scan_successful:
        lines.append(f"[!] Scan failed: {result.error_message}")
        lines.append("")
        return "\n".join(lines)

    # Summary
    critical = len(result.get_by_severity(VulnSeverity.CRITICAL))
    high = len(result.get_by_severity(VulnSeverity.HIGH))
    medium = len(result.get_by_severity(VulnSeverity.MEDIUM))
    low = len(result.get_by_severity(VulnSeverity.LOW))

    lines.append("--- SUMMARY ---")
    lines.append(f"  [!] Critical: {critical}")
    lines.append(f"  [H] High: {high}")
    lines.append(f"  [M] Medium: {medium}")
    lines.append(f"  [L] Low: {low}")
    lines.append("")

    if result.vulnerabilities:
        lines.append("--- VULNERABILITIES ---")
        lines.append("")

        # Sort by severity
        sorted_vulns = sorted(
            result.vulnerabilities,
            key=lambda v: list(VulnSeverity).index(v.severity),
        )

        for vuln in sorted_vulns:
            icon = {
                VulnSeverity.CRITICAL: "[!]",
                VulnSeverity.HIGH: "[H]",
                VulnSeverity.MEDIUM: "[M]",
                VulnSeverity.LOW: "[L]",
            }.get(vuln.severity, "[?]")

            lines.append(f"{icon} {vuln.id}")
            lines.append(f"    Package: {vuln.package} ({vuln.installed_version})")

            if vuln.fixed_version:
                lines.append(f"    Fix: Upgrade to {vuln.fixed_version}")

            if vuln.url:
                lines.append(f"    Info: {vuln.url}")

            lines.append("")

    else:
        lines.append("No vulnerabilities found.")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def run_full_scan(
    requirements_file: Path | None = None,
    docker_images: list[str] | None = None,
) -> tuple[VulnScanResult, VulnScanResult]:
    """
    Run full vulnerability scan (Python + Docker).

    Args:
        requirements_file: Path to requirements.txt.
        docker_images: Docker images to scan.

    Returns:
        Tuple of (python_result, docker_result).
    """
    python_result = scan_python_dependencies(requirements_file)
    docker_result = scan_docker_images(docker_images)

    return python_result, docker_result
