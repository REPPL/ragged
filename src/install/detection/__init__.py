"""
Prerequisite Detection System.

PREREQ-001: Detects installed dependencies including Docker, Python, and Ollama.
Provides platform-specific detection for Windows, macOS, and Linux.
"""

from ragged.install.detection.base import DetectionResult, BaseDetector
from ragged.install.detection.docker import DockerDetector
from ragged.install.detection.python_detector import PythonDetector
from ragged.install.detection.ollama import OllamaDetector
from ragged.install.detection.environment import EnvironmentDetector


def detect_all_prerequisites() -> dict[str, DetectionResult]:
    """
    Detect all prerequisites and return results.

    Returns:
        Dictionary mapping prerequisite names to detection results.
    """
    detectors = {
        "docker": DockerDetector(),
        "python": PythonDetector(),
        "ollama": OllamaDetector(),
        "environment": EnvironmentDetector(),
    }

    results = {}
    for name, detector in detectors.items():
        results[name] = detector.detect()

    return results


__all__ = [
    "DetectionResult",
    "BaseDetector",
    "DockerDetector",
    "PythonDetector",
    "OllamaDetector",
    "EnvironmentDetector",
    "detect_all_prerequisites",
]
