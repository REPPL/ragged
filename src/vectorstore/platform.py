"""Platform detection for backend selection."""

import logging
import platform

logger = logging.getLogger(__name__)


def detect_platform_backend_support() -> dict[str, bool]:
    """Detect which backends are available on current platform.

    Returns:
        Dictionary mapping backend names to availability status
    """
    return {
        "chromadb": True,  # Always available (fallback)
        "leann": _is_leann_available(),
    }


def _is_leann_available() -> bool:
    """Check if LEANN is available on current platform.

    LEANN requires:
    - macOS or Linux (not Windows)
    - leann package installed

    Returns:
        True if LEANN can be used, False otherwise
    """
    # Check platform first
    system = platform.system()
    if system not in ("Darwin", "Linux"):
        logger.debug(f"LEANN not available on {system} (requires macOS or Linux)")
        return False

    # Check if leann package is installed
    try:
        import leann  # noqa: F401
        logger.debug(f"LEANN available on {system}")
        return True
    except ImportError:
        logger.debug(f"LEANN not installed (platform: {system})")
        return False


def get_default_backend() -> str:
    """Auto-select best available backend for current platform.

    Selection priority:
    1. LEANN (if available) - 97% storage savings
    2. ChromaDB (fallback) - universal compatibility

    Returns:
        Backend name ("leann" or "chromadb")
    """
    if _is_leann_available():
        logger.info("Auto-selected LEANN backend (97% storage savings)")
        return "leann"

    logger.info("Auto-selected ChromaDB backend (LEANN not available)")
    return "chromadb"


def get_platform_info() -> dict[str, str]:
    """Get detailed platform information.

    Returns:
        Dictionary with platform details (system, architecture, etc.)
    """
    return {
        "system": platform.system(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


def is_platform_supported_for_leann() -> bool:
    """Check if current platform can support LEANN.

    Returns:
        True if LEANN could work on this platform (regardless of installation)
    """
    system = platform.system()
    return system in ("Darwin", "Linux")
