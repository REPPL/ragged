"""
Installation Utilities.

Common utilities for downloading files, running processes with progress,
and managing temporary files during installation.
"""

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


def get_temp_dir() -> Path:
    """
    Get temporary directory for installation files.

    Returns:
        Path to temporary directory.
    """
    temp_base = Path(tempfile.gettempdir()) / "ragged_install"
    temp_base.mkdir(parents=True, exist_ok=True)
    return temp_base


def cleanup_temp_files() -> None:
    """Remove all temporary installation files."""
    temp_dir = get_temp_dir()
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


def download_file(
    url: str,
    dest: Path | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    expected_hash: str | None = None,
    hash_algorithm: str = "sha256",
) -> Path:
    """
    Download a file from URL with progress tracking.

    Args:
        url: URL to download from.
        dest: Destination path. If None, uses temp directory.
        progress_callback: Optional callback(bytes_downloaded, total_bytes).
        expected_hash: Expected hash for verification.
        hash_algorithm: Hash algorithm (sha256, sha512, md5).

    Returns:
        Path to downloaded file.

    Raises:
        DownloadError: If download fails or hash doesn't match.
    """
    if dest is None:
        filename = url.split("/")[-1].split("?")[0]
        dest = get_temp_dir() / filename

    logger.info(f"Downloading {url} to {dest}")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ragged-installer/0.8.0"},
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192

            hasher = hashlib.new(hash_algorithm) if expected_hash else None

            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    f.write(chunk)
                    downloaded += len(chunk)

                    if hasher:
                        hasher.update(chunk)

                    if progress_callback and total_size:
                        progress_callback(downloaded, total_size)

        # Verify hash if provided
        if expected_hash and hasher:
            actual_hash = hasher.hexdigest()
            if actual_hash.lower() != expected_hash.lower():
                dest.unlink()
                raise DownloadError(
                    f"Hash mismatch: expected {expected_hash}, got {actual_hash}"
                )

        logger.info(f"Download complete: {dest}")
        return dest

    except urllib.error.URLError as e:
        raise DownloadError(f"Download failed: {e}") from e
    except OSError as e:
        raise DownloadError(f"Failed to write file: {e}") from e


def run_with_progress(
    command: list[str],
    description: str,
    timeout: float = 300.0,
    capture_output: bool = True,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    """
    Run a command with logging.

    Args:
        command: Command and arguments.
        description: Description for logging.
        timeout: Maximum execution time.
        capture_output: Whether to capture stdout/stderr.
        env: Environment variables to set.
        cwd: Working directory.

    Returns:
        Tuple of (return_code, stdout, stderr).
    """
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {' '.join(command)}")

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            env=process_env,
            cwd=cwd,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Command failed with code {result.returncode}")
            if result.stderr:
                logger.warning(f"stderr: {result.stderr}")

        return result.returncode, result.stdout or "", result.stderr or ""

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s")
        return -1, "", "Command timed out"

    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        return -1, "", f"Command not found: {command[0]}"

    except Exception as e:
        logger.error(f"Command failed: {e}")
        return -1, "", str(e)


def run_with_sudo(
    command: list[str],
    description: str,
    password_prompt: Callable[[], str] | None = None,
    timeout: float = 300.0,
) -> tuple[int, str, str]:
    """
    Run a command with sudo (Linux/macOS).

    Args:
        command: Command and arguments (without sudo).
        description: Description for logging.
        password_prompt: Optional callback to get sudo password.
        timeout: Maximum execution time.

    Returns:
        Tuple of (return_code, stdout, stderr).
    """
    # Check if already running as root
    if os.geteuid() == 0:
        return run_with_progress(command, description, timeout)

    sudo_command = ["sudo", "-S"] + command
    logger.info(f"Running with sudo: {description}")

    try:
        process = subprocess.Popen(
            sudo_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # If password prompt provided, use it
        password = None
        if password_prompt:
            password = password_prompt() + "\n"

        stdout, stderr = process.communicate(input=password, timeout=timeout)
        return process.returncode, stdout, stderr

    except subprocess.TimeoutExpired:
        process.kill()
        return -1, "", "Command timed out"

    except Exception as e:
        return -1, "", str(e)


def make_executable(path: Path) -> None:
    """Make a file executable (Unix)."""
    import stat

    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def extract_archive(
    archive_path: Path,
    dest_dir: Path,
    strip_components: int = 0,
) -> Path:
    """
    Extract an archive (tar, zip, dmg).

    Args:
        archive_path: Path to archive file.
        dest_dir: Destination directory.
        strip_components: Number of leading path components to strip.

    Returns:
        Path to extracted contents.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = archive_path.suffix.lower()

    if suffix in (".gz", ".tgz") or archive_path.name.endswith(".tar.gz"):
        import tarfile

        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(dest_dir)

    elif suffix == ".zip":
        import zipfile

        with zipfile.ZipFile(archive_path, "r") as zip_file:
            zip_file.extractall(dest_dir)

    elif suffix == ".dmg":
        # macOS disk image
        mount_point = dest_dir / "mount"
        mount_point.mkdir(exist_ok=True)

        code, _, _ = run_with_progress(
            ["hdiutil", "attach", str(archive_path), "-mountpoint", str(mount_point)],
            "Mounting disk image",
        )

        if code == 0:
            # Copy contents
            for item in mount_point.iterdir():
                if item.is_dir():
                    shutil.copytree(item, dest_dir / item.name)
                else:
                    shutil.copy2(item, dest_dir)

            # Unmount
            run_with_progress(
                ["hdiutil", "detach", str(mount_point)],
                "Unmounting disk image",
            )

    else:
        raise ExtractError(f"Unsupported archive format: {suffix}")

    return dest_dir


def verify_checksum(
    file_path: Path,
    expected_hash: str,
    algorithm: str = "sha256",
) -> bool:
    """
    Verify file checksum.

    Args:
        file_path: Path to file.
        expected_hash: Expected hash value.
        algorithm: Hash algorithm.

    Returns:
        True if hash matches.
    """
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    actual_hash = hasher.hexdigest()
    return actual_hash.lower() == expected_hash.lower()


def wait_for_service(
    host: str,
    port: int,
    timeout: float = 60.0,
    interval: float = 1.0,
) -> bool:
    """
    Wait for a service to become available.

    Args:
        host: Service host.
        port: Service port.
        timeout: Maximum wait time.
        interval: Check interval.

    Returns:
        True if service is available.
    """
    import socket
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except (socket.error, socket.timeout):
            time.sleep(interval)

    return False


class DownloadError(Exception):
    """Exception raised during file download."""

    pass


class ExtractError(Exception):
    """Exception raised during archive extraction."""

    pass
