"""
Dependency Verification.

INSTALL-SEC-001: Checksum and signature verification for dependencies.
"""

import hashlib
import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Verification status."""

    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class VerificationResult:
    """Result of verification attempt."""

    status: VerificationStatus
    file_path: Path
    expected_hash: str | None = None
    computed_hash: str | None = None
    signature_valid: bool | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def verify_checksum(
    file_path: Path,
    expected_sha256: str,
    algorithm: str = "sha256",
) -> VerificationResult:
    """
    Verify file checksum.

    Args:
        file_path: Path to file to verify.
        expected_sha256: Expected SHA256 hash.
        algorithm: Hash algorithm (default sha256).

    Returns:
        VerificationResult with status and details.
    """
    if not file_path.exists():
        return VerificationResult(
            status=VerificationStatus.ERROR,
            file_path=file_path,
            expected_hash=expected_sha256,
            message=f"File not found: {file_path}",
        )

    try:
        hasher = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        computed = hasher.hexdigest()

        if computed.lower() == expected_sha256.lower():
            logger.info(f"Checksum verified: {file_path}")
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                file_path=file_path,
                expected_hash=expected_sha256,
                computed_hash=computed,
                message="Checksum verified successfully",
            )
        else:
            logger.error(f"Checksum mismatch for {file_path}")
            return VerificationResult(
                status=VerificationStatus.FAILED,
                file_path=file_path,
                expected_hash=expected_sha256,
                computed_hash=computed,
                message=f"Checksum mismatch: expected {expected_sha256}, got {computed}",
            )

    except Exception as e:
        logger.exception(f"Checksum verification failed: {e}")
        return VerificationResult(
            status=VerificationStatus.ERROR,
            file_path=file_path,
            expected_hash=expected_sha256,
            message=f"Verification error: {e}",
        )


def verify_gpg_signature(
    file_path: Path,
    signature_path: Path | None = None,
    key_id: str | None = None,
) -> VerificationResult:
    """
    Verify GPG signature.

    Args:
        file_path: Path to file to verify.
        signature_path: Path to detached signature (if not file_path.sig).
        key_id: Expected key ID (optional).

    Returns:
        VerificationResult with signature verification status.
    """
    if signature_path is None:
        signature_path = file_path.with_suffix(file_path.suffix + ".sig")

    if not signature_path.exists():
        # Try .asc extension
        signature_path = file_path.with_suffix(file_path.suffix + ".asc")

    if not signature_path.exists():
        return VerificationResult(
            status=VerificationStatus.SKIPPED,
            file_path=file_path,
            message="No signature file found",
            details={"signature_path": str(signature_path)},
        )

    try:
        # Use gpg to verify signature
        result = subprocess.run(
            ["gpg", "--verify", str(signature_path), str(file_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            logger.info(f"GPG signature verified: {file_path}")
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                file_path=file_path,
                signature_valid=True,
                message="GPG signature verified successfully",
                details={"output": result.stderr},
            )
        else:
            logger.error(f"GPG signature verification failed for {file_path}")
            return VerificationResult(
                status=VerificationStatus.FAILED,
                file_path=file_path,
                signature_valid=False,
                message=f"GPG signature verification failed: {result.stderr}",
            )

    except FileNotFoundError:
        return VerificationResult(
            status=VerificationStatus.SKIPPED,
            file_path=file_path,
            message="GPG not installed, signature verification skipped",
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            status=VerificationStatus.ERROR,
            file_path=file_path,
            message="GPG verification timed out",
        )
    except Exception as e:
        return VerificationResult(
            status=VerificationStatus.ERROR,
            file_path=file_path,
            message=f"GPG verification error: {e}",
        )


def verify_download(
    file_path: Path,
    expected_sha256: str | None = None,
    verify_signature: bool = True,
) -> VerificationResult:
    """
    Verify downloaded file (checksum and optionally signature).

    Args:
        file_path: Path to downloaded file.
        expected_sha256: Expected SHA256 hash (if None, only signature checked).
        verify_signature: Whether to verify GPG signature.

    Returns:
        VerificationResult with overall verification status.
    """
    results: list[VerificationResult] = []

    # Checksum verification
    if expected_sha256:
        checksum_result = verify_checksum(file_path, expected_sha256)
        results.append(checksum_result)

        if checksum_result.status == VerificationStatus.FAILED:
            return checksum_result

    # Signature verification
    if verify_signature:
        sig_result = verify_gpg_signature(file_path)
        results.append(sig_result)

        if sig_result.status == VerificationStatus.FAILED:
            return sig_result

    # Overall result
    if not results:
        return VerificationResult(
            status=VerificationStatus.SKIPPED,
            file_path=file_path,
            message="No verification performed",
        )

    # Check if any verification passed
    verified = any(r.status == VerificationStatus.VERIFIED for r in results)
    failed = any(r.status == VerificationStatus.FAILED for r in results)

    if failed:
        return VerificationResult(
            status=VerificationStatus.FAILED,
            file_path=file_path,
            message="Verification failed",
            details={"results": [r.message for r in results]},
        )

    if verified:
        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            file_path=file_path,
            message="Download verified",
            details={"results": [r.message for r in results]},
        )

    return VerificationResult(
        status=VerificationStatus.SKIPPED,
        file_path=file_path,
        message="Verification skipped",
    )


class DownloadVerifier:
    """
    Download verification manager.

    Manages checksum database and verification pipeline.
    """

    def __init__(self, checksums_file: Path | None = None) -> None:
        """
        Initialise verifier.

        Args:
            checksums_file: Path to checksums database file.
        """
        self.checksums_file = checksums_file
        self._checksums: dict[str, str] = {}
        self._load_checksums()

    def _load_checksums(self) -> None:
        """Load checksums from file."""
        if self.checksums_file and self.checksums_file.exists():
            import json

            with open(self.checksums_file) as f:
                self._checksums = json.load(f)

    def add_checksum(self, name: str, sha256: str) -> None:
        """Add a checksum to the database."""
        self._checksums[name] = sha256

    def get_checksum(self, name: str) -> str | None:
        """Get checksum for a dependency."""
        return self._checksums.get(name)

    def verify(
        self,
        file_path: Path,
        name: str | None = None,
        expected_sha256: str | None = None,
    ) -> VerificationResult:
        """
        Verify a downloaded file.

        Args:
            file_path: Path to file.
            name: Dependency name (to look up checksum).
            expected_sha256: Override checksum (if provided).

        Returns:
            VerificationResult.
        """
        if expected_sha256 is None and name:
            expected_sha256 = self.get_checksum(name)

        return verify_download(file_path, expected_sha256)

    def save_checksums(self) -> None:
        """Save checksums to file."""
        if self.checksums_file:
            import json

            with open(self.checksums_file, "w") as f:
                json.dump(self._checksums, f, indent=2)


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute hash of a file.

    Args:
        file_path: Path to file.
        algorithm: Hash algorithm.

    Returns:
        Hex-encoded hash string.
    """
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()
