"""
Version Validator.

PREREQ-003: Validates dependency versions meet minimum requirements
and checks for known incompatibilities.
"""

import re
from typing import Any

from ragged.install.detection import (
    DockerDetector,
    PythonDetector,
    OllamaDetector,
)
from ragged.install.validation.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


# Version requirements
VERSION_REQUIREMENTS = {
    "docker": {
        "minimum": "20.10",
        "recommended": "24.0",
        "maximum": None,
    },
    "docker_compose": {
        "minimum": "2.0",
        "recommended": "2.20",
        "maximum": None,
    },
    "python": {
        "minimum": "3.10",
        "recommended": "3.12",
        "maximum": "3.12",
    },
    "ollama": {
        "minimum": "0.1.0",
        "recommended": "0.3.0",
        "maximum": None,
    },
}

# Known incompatible versions
INCOMPATIBLE_VERSIONS = {
    "docker": ["19.03", "18.09"],  # Old versions with security issues
    "python": ["3.8", "3.9"],  # Missing required features
}


class VersionValidator(BaseValidator):
    """
    Validator for dependency versions.

    Checks:
    - Docker version meets minimum
    - Docker Compose version meets minimum
    - Python version is in supported range
    - Ollama version meets minimum
    - No known incompatible versions
    """

    def __init__(self) -> None:
        """Initialise version validator."""
        self._docker_detector = DockerDetector()
        self._python_detector = PythonDetector()
        self._ollama_detector = OllamaDetector()

    @property
    def category(self) -> str:
        """Return category name."""
        return "versions"

    def validate(self) -> list[ValidationResult]:
        """Run all version validation checks."""
        results = []

        # Docker version
        docker_result = self._docker_detector.detect()
        if docker_result.installed:
            results.append(self._check_docker_version(docker_result.version))

            # Docker Compose version
            compose_info = docker_result.details.get("compose", {})
            if isinstance(compose_info, dict) and compose_info.get("installed"):
                compose_version = compose_info.get("version")
                if compose_version:
                    results.append(self._check_compose_version(str(compose_version)))
        else:
            results.append(self._create_not_installed_result("docker"))

        # Python version
        python_result = self._python_detector.detect()
        if python_result.installed:
            results.append(self._check_python_version(python_result.version))
        else:
            results.append(self._create_not_installed_result("python"))

        # Ollama version
        ollama_result = self._ollama_detector.detect()
        if ollama_result.installed:
            results.append(self._check_ollama_version(ollama_result.version))
        else:
            results.append(self._create_not_installed_result("ollama"))

        return results

    def _parse_version(self, version_str: str | None) -> tuple[int, ...] | None:
        """Parse version string to tuple."""
        if not version_str:
            return None

        # Remove common prefixes
        cleaned = re.sub(r"^[vV]?", "", version_str)

        # Extract numeric parts
        match = re.search(r"(\d+(?:\.\d+)*)", cleaned)
        if match:
            try:
                return tuple(int(x) for x in match.group(1).split("."))
            except ValueError:
                return None
        return None

    def _compare_versions(
        self,
        version: tuple[int, ...],
        target: str,
    ) -> int:
        """
        Compare version tuples.

        Returns:
            -1 if version < target, 0 if equal, 1 if version > target.
        """
        target_tuple = self._parse_version(target)
        if not target_tuple:
            return 0

        # Pad shorter tuple with zeros
        max_len = max(len(version), len(target_tuple))
        padded_version = version + (0,) * (max_len - len(version))
        padded_target = target_tuple + (0,) * (max_len - len(target_tuple))

        if padded_version < padded_target:
            return -1
        elif padded_version > padded_target:
            return 1
        return 0

    def _check_docker_version(self, version: str | None) -> ValidationResult:
        """Check Docker version."""
        reqs = VERSION_REQUIREMENTS["docker"]

        if not version:
            return self.create_result(
                name="docker_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message="Could not determine Docker version",
                fix_suggestion="Ensure Docker is installed and running.",
            )

        parsed = self._parse_version(version)
        if not parsed:
            return self.create_result(
                name="docker_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Could not parse Docker version: {version}",
            )

        details: dict[str, Any] = {
            "version": version,
            "minimum": reqs["minimum"],
            "recommended": reqs["recommended"],
        }

        # Check for known incompatible versions
        if self._is_incompatible("docker", version):
            return self.create_result(
                name="docker_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Docker version {version} has known issues",
                details=details,
                fix_suggestion="Upgrade Docker to version 20.10 or later.",
            )

        # Check minimum
        if self._compare_versions(parsed, str(reqs["minimum"])) < 0:
            return self.create_result(
                name="docker_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Docker version {version} below minimum {reqs['minimum']}",
                details=details,
                fix_suggestion=f"Upgrade Docker to version {reqs['minimum']} or later.",
            )

        # Check recommended
        if self._compare_versions(parsed, str(reqs["recommended"])) < 0:
            return self.create_result(
                name="docker_version",
                passed=True,
                message=f"Docker version {version} OK (recommended: {reqs['recommended']}+)",
                details=details,
            )

        return self.create_result(
            name="docker_version",
            passed=True,
            message=f"Docker version {version} OK",
            details=details,
        )

    def _check_compose_version(self, version: str | None) -> ValidationResult:
        """Check Docker Compose version."""
        reqs = VERSION_REQUIREMENTS["docker_compose"]

        if not version:
            return self.create_result(
                name="compose_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message="Could not determine Docker Compose version",
                fix_suggestion="Install Docker Compose v2+.",
            )

        parsed = self._parse_version(version)
        if not parsed:
            return self.create_result(
                name="compose_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Could not parse Docker Compose version: {version}",
            )

        details: dict[str, Any] = {
            "version": version,
            "minimum": reqs["minimum"],
            "recommended": reqs["recommended"],
        }

        if self._compare_versions(parsed, str(reqs["minimum"])) < 0:
            return self.create_result(
                name="compose_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Docker Compose {version} below minimum {reqs['minimum']}",
                details=details,
                fix_suggestion="Upgrade to Docker Compose v2+ (included in Docker Desktop).",
            )

        return self.create_result(
            name="compose_version",
            passed=True,
            message=f"Docker Compose version {version} OK",
            details=details,
        )

    def _check_python_version(self, version: str | None) -> ValidationResult:
        """Check Python version."""
        reqs = VERSION_REQUIREMENTS["python"]

        if not version:
            return self.create_result(
                name="python_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message="Could not determine Python version",
                fix_suggestion="Install Python 3.10-3.12.",
            )

        parsed = self._parse_version(version)
        if not parsed:
            return self.create_result(
                name="python_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Could not parse Python version: {version}",
            )

        details: dict[str, Any] = {
            "version": version,
            "minimum": reqs["minimum"],
            "maximum": reqs["maximum"],
            "recommended": reqs["recommended"],
        }

        # Check for known incompatible versions
        if self._is_incompatible("python", version):
            return self.create_result(
                name="python_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Python version {version} is not supported",
                details=details,
                fix_suggestion="Install Python 3.10, 3.11, or 3.12.",
            )

        # Check minimum
        if self._compare_versions(parsed, str(reqs["minimum"])) < 0:
            return self.create_result(
                name="python_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Python {version} below minimum {reqs['minimum']}",
                details=details,
                fix_suggestion=f"Upgrade Python to version {reqs['minimum']} or later.",
            )

        # Check maximum
        if reqs["maximum"] and self._compare_versions(parsed, str(reqs["maximum"])) > 0:
            return self.create_result(
                name="python_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Python {version} above tested maximum {reqs['maximum']}",
                details=details,
                fix_suggestion=f"Use Python {reqs['maximum']} for best compatibility.",
            )

        return self.create_result(
            name="python_version",
            passed=True,
            message=f"Python version {version} OK",
            details=details,
        )

    def _check_ollama_version(self, version: str | None) -> ValidationResult:
        """Check Ollama version."""
        reqs = VERSION_REQUIREMENTS["ollama"]

        if not version:
            return self.create_result(
                name="ollama_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message="Could not determine Ollama version",
                fix_suggestion="Ensure Ollama is installed and running.",
            )

        parsed = self._parse_version(version)
        if not parsed:
            return self.create_result(
                name="ollama_version",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Could not parse Ollama version: {version}",
            )

        details: dict[str, Any] = {
            "version": version,
            "minimum": reqs["minimum"],
            "recommended": reqs["recommended"],
        }

        if self._compare_versions(parsed, str(reqs["minimum"])) < 0:
            return self.create_result(
                name="ollama_version",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Ollama {version} below minimum {reqs['minimum']}",
                details=details,
                fix_suggestion="Update Ollama to the latest version.",
            )

        return self.create_result(
            name="ollama_version",
            passed=True,
            message=f"Ollama version {version} OK",
            details=details,
        )

    def _is_incompatible(self, dependency: str, version: str) -> bool:
        """Check if version is in known incompatible list."""
        incompatible = INCOMPATIBLE_VERSIONS.get(dependency, [])

        for incompat in incompatible:
            if version.startswith(incompat):
                return True

        return False

    def _create_not_installed_result(self, dependency: str) -> ValidationResult:
        """Create result for missing dependency."""
        return self.create_result(
            name=f"{dependency}_version",
            passed=False,
            severity=ValidationSeverity.CRITICAL,
            message=f"{dependency.title()} is not installed",
            fix_suggestion=f"Install {dependency.title()} before proceeding.",
        )
