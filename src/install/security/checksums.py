"""
Dependency Checksums Database.

INSTALL-SEC-001: Known checksums for dependency verification.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DependencyChecksum:
    """Checksum information for a dependency."""

    name: str
    version: str
    sha256: str
    url: str
    platform: str = "all"
    gpg_key_id: str | None = None
    signature_url: str | None = None


# Known dependency checksums
# Note: These are examples and should be updated with actual checksums
DEPENDENCY_CHECKSUMS: dict[str, DependencyChecksum] = {
    # Docker Desktop - macOS ARM64
    "docker-desktop-mac-arm64": DependencyChecksum(
        name="docker-desktop",
        version="4.25.0",
        sha256="",  # Update with actual checksum
        url="https://desktop.docker.com/mac/main/arm64/Docker.dmg",
        platform="darwin-arm64",
    ),
    # Docker Desktop - macOS x64
    "docker-desktop-mac-x64": DependencyChecksum(
        name="docker-desktop",
        version="4.25.0",
        sha256="",  # Update with actual checksum
        url="https://desktop.docker.com/mac/main/amd64/Docker.dmg",
        platform="darwin-x64",
    ),
    # Docker Desktop - Windows
    "docker-desktop-windows": DependencyChecksum(
        name="docker-desktop",
        version="4.25.0",
        sha256="",  # Update with actual checksum
        url="https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe",
        platform="win32",
    ),
    # Ollama - macOS
    "ollama-darwin": DependencyChecksum(
        name="ollama",
        version="0.1.32",
        sha256="",  # Update with actual checksum
        url="https://ollama.ai/download/Ollama-darwin.zip",
        platform="darwin",
    ),
    # Ollama - Linux
    "ollama-linux": DependencyChecksum(
        name="ollama",
        version="0.1.32",
        sha256="",  # Update with actual checksum
        url="https://ollama.ai/download/ollama-linux-amd64",
        platform="linux",
    ),
    # Ollama - Windows
    "ollama-windows": DependencyChecksum(
        name="ollama",
        version="0.1.32",
        sha256="",  # Update with actual checksum
        url="https://ollama.ai/download/OllamaSetup.exe",
        platform="win32",
    ),
}


def get_checksum(
    dependency: str,
    platform: str | None = None,
) -> DependencyChecksum | None:
    """
    Get checksum for a dependency.

    Args:
        dependency: Dependency name (e.g., "docker-desktop", "ollama").
        platform: Platform specifier (e.g., "darwin-arm64").

    Returns:
        DependencyChecksum if found, None otherwise.
    """
    # Try exact match first
    if dependency in DEPENDENCY_CHECKSUMS:
        return DEPENDENCY_CHECKSUMS[dependency]

    # Try with platform suffix
    if platform:
        key = f"{dependency}-{platform}"
        if key in DEPENDENCY_CHECKSUMS:
            return DEPENDENCY_CHECKSUMS[key]

    # Search for any matching dependency
    for key, checksum in DEPENDENCY_CHECKSUMS.items():
        if checksum.name == dependency:
            if platform is None or checksum.platform in (platform, "all"):
                return checksum

    return None


def get_current_platform() -> str:
    """Get current platform identifier."""
    import platform
    import struct

    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            return "darwin-arm64"
        return "darwin-x64"
    elif system == "linux":
        if "64" in machine:
            return "linux-x64"
        return "linux-x86"
    elif system == "windows":
        if struct.calcsize("P") * 8 == 64:
            return "win32-x64"
        return "win32-x86"

    return f"{system}-{machine}"


def update_checksums(
    checksums: dict[str, DependencyChecksum],
    save_path: Path | None = None,
) -> None:
    """
    Update checksums database.

    Args:
        checksums: New checksums to add/update.
        save_path: Path to save checksums JSON.
    """
    import json

    DEPENDENCY_CHECKSUMS.update(checksums)

    if save_path:
        data = {
            key: {
                "name": c.name,
                "version": c.version,
                "sha256": c.sha256,
                "url": c.url,
                "platform": c.platform,
                "gpg_key_id": c.gpg_key_id,
                "signature_url": c.signature_url,
            }
            for key, c in DEPENDENCY_CHECKSUMS.items()
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)


def load_checksums(checksums_path: Path) -> dict[str, DependencyChecksum]:
    """
    Load checksums from JSON file.

    Args:
        checksums_path: Path to checksums JSON file.

    Returns:
        Dictionary of checksums.
    """
    import json

    if not checksums_path.exists():
        return {}

    with open(checksums_path) as f:
        data = json.load(f)

    checksums = {}
    for key, value in data.items():
        checksums[key] = DependencyChecksum(
            name=value["name"],
            version=value["version"],
            sha256=value["sha256"],
            url=value["url"],
            platform=value.get("platform", "all"),
            gpg_key_id=value.get("gpg_key_id"),
            signature_url=value.get("signature_url"),
        )

    return checksums


def fetch_latest_checksums(
    base_url: str = "https://raw.githubusercontent.com/ragged/ragged/main/checksums.json",
) -> dict[str, DependencyChecksum] | None:
    """
    Fetch latest checksums from remote source.

    Args:
        base_url: URL to checksums JSON.

    Returns:
        Dictionary of checksums or None if fetch failed.
    """
    import json

    try:
        import httpx

        response = httpx.get(base_url, timeout=30, follow_redirects=True)

        if response.status_code == 200:
            data = response.json()
            return {
                key: DependencyChecksum(
                    name=value["name"],
                    version=value["version"],
                    sha256=value["sha256"],
                    url=value["url"],
                    platform=value.get("platform", "all"),
                    gpg_key_id=value.get("gpg_key_id"),
                    signature_url=value.get("signature_url"),
                )
                for key, value in data.items()
            }

    except Exception as e:
        logger.warning(f"Failed to fetch checksums: {e}")

    return None
