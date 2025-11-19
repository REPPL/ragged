"""Encryption utilities for ragged.

v0.2.11 FEAT-PRIV-001: Encryption at Rest

Provides secure encryption at rest for sensitive user data.
Uses Fernet (AES-128 in CBC mode with HMAC for integrity).

Security:
- Per-user encryption keys stored in OS-specific secure locations
- Fernet provides authenticated encryption (prevents tampering)
- File permissions set to 0o600 (user read/write only)
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption/decryption of sensitive data at rest.

    Features:
    - Automatic key generation and storage
    - OS-specific secure key locations
    - File-level encryption/decryption
    - Key rotation support

    Usage:
        >>> manager = EncryptionManager()
        >>> encrypted = manager.encrypt(b"sensitive data")
        >>> decrypted = manager.decrypt(encrypted)
        >>> assert decrypted == b"sensitive data"

    Security Properties:
    - Fernet provides authenticated encryption (AES-128 + HMAC)
    - Keys stored with 0o600 permissions (user only)
    - Automatic IV (initialization vector) generation per encryption
    """

    def __init__(self, key_file: Optional[Path] = None):
        """Initialise encryption manager.

        Args:
            key_file: Path to encryption key file
                     (default: OS-specific secure location)

        Security: If key_file is None, uses OS-specific secure locations:
        - macOS: ~/Library/Application Support/ragged/encryption.key
        - Windows: %APPDATA%/ragged/encryption.key
        - Linux: $XDG_DATA_HOME/ragged/encryption.key or ~/.local/share/ragged/encryption.key
        """
        if key_file is None:
            key_file = self._get_default_key_path()

        self.key_file = key_file
        self.cipher = self._get_or_create_cipher()

    @staticmethod
    def _get_default_key_path() -> Path:
        """Get OS-specific secure key storage location.

        Returns:
            Path to encryption key file

        Security: Uses OS-specific secure application data directories.
        Directories created with 0o700 permissions (user only).
        """
        if sys.platform == "darwin":  # macOS
            base = Path.home() / "Library" / "Application Support" / "ragged"
        elif sys.platform == "win32":  # Windows
            base = Path(os.getenv("APPDATA", str(Path.home()))) / "ragged"
        else:  # Linux/Unix
            # Follow XDG Base Directory Specification
            xdg_data_home = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
            base = Path(xdg_data_home) / "ragged"

        # Create directory with user-only permissions
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        return base / "encryption.key"

    def _get_or_create_cipher(self) -> Fernet:
        """Get or create Fernet cipher with encryption key.

        Returns:
            Fernet cipher instance

        Security:
        - Generates new key if none exists
        - Stores key with 0o600 permissions (user read/write only)
        - Loads existing key if available
        """
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, "rb") as f:
                key = f.read()
            logger.debug(f"Loaded encryption key from {self.key_file}")
        else:
            # Generate new key
            key = Fernet.generate_key()

            # Save with restrictive permissions
            self.key_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with open(self.key_file, "wb") as f:
                f.write(key)

            # Set file permissions (user read/write only)
            os.chmod(self.key_file, 0o600)

            logger.info(f"Generated new encryption key: {self.key_file}")

        return Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data.

        Args:
            data: Plaintext bytes to encrypt

        Returns:
            Encrypted ciphertext bytes

        Security:
        - Uses Fernet (AES-128 in CBC mode)
        - Includes HMAC for authentication
        - Automatic IV generation (secure random)

        Raises:
            Exception: If encryption fails
        """
        try:
            encrypted = self.cipher.encrypt(data)
            logger.debug(f"Encrypted {len(data)} bytes → {len(encrypted)} bytes")
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data.

        Args:
            ciphertext: Encrypted bytes to decrypt

        Returns:
            Decrypted plaintext bytes

        Security:
        - Verifies HMAC before decryption (prevents tampering)
        - Raises InvalidToken if data corrupted or wrong key

        Raises:
            InvalidToken: If ciphertext is corrupted or key is wrong
            Exception: If decryption fails for other reasons
        """
        try:
            decrypted = self.cipher.decrypt(ciphertext)
            logger.debug(f"Decrypted {len(ciphertext)} bytes → {len(decrypted)} bytes")
            return decrypted
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (corrupted data or wrong key)")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_file(self, plaintext_path: Path, encrypted_path: Optional[Path] = None) -> Path:
        """Encrypt a file.

        Args:
            plaintext_path: Source file to encrypt
            encrypted_path: Destination encrypted file
                          (default: plaintext_path + .enc)

        Returns:
            Path to encrypted file

        Security:
        - Encrypted file has 0o600 permissions (user only)
        - Original file not modified

        Example:
            >>> manager = EncryptionManager()
            >>> encrypted = manager.encrypt_file(Path("data.json"))
            >>> # Creates data.json.enc with encrypted contents
        """
        if encrypted_path is None:
            encrypted_path = plaintext_path.with_suffix(plaintext_path.suffix + ".enc")

        # Read plaintext
        with open(plaintext_path, "rb") as f:
            plaintext = f.read()

        # Encrypt
        ciphertext = self.encrypt(plaintext)

        # Write encrypted
        with open(encrypted_path, "wb") as f:
            f.write(ciphertext)

        # Set restrictive permissions
        os.chmod(encrypted_path, 0o600)

        logger.info(f"Encrypted file: {plaintext_path} → {encrypted_path}")
        return encrypted_path

    def decrypt_file(self, encrypted_path: Path, decrypted_path: Optional[Path] = None) -> Path:
        """Decrypt a file.

        Args:
            encrypted_path: Source encrypted file
            decrypted_path: Destination decrypted file
                          (default: encrypted_path without .enc)

        Returns:
            Path to decrypted file

        Security:
        - Verifies HMAC before decryption
        - Raises InvalidToken if file corrupted

        Example:
            >>> manager = EncryptionManager()
            >>> decrypted = manager.decrypt_file(Path("data.json.enc"))
            >>> # Creates data.json with decrypted contents
        """
        if decrypted_path is None:
            if encrypted_path.suffix == ".enc":
                decrypted_path = encrypted_path.with_suffix("")
            else:
                decrypted_path = encrypted_path.with_suffix(".dec")

        # Read ciphertext
        with open(encrypted_path, "rb") as f:
            ciphertext = f.read()

        # Decrypt
        plaintext = self.decrypt(ciphertext)

        # Write decrypted
        with open(decrypted_path, "wb") as f:
            f.write(plaintext)

        logger.info(f"Decrypted file: {encrypted_path} → {decrypted_path}")
        return decrypted_path

    def rotate_key(self, new_key_file: Optional[Path] = None) -> None:
        """Rotate encryption key (re-encrypt all data with new key).

        WARNING: This is a destructive operation. Backup data first.

        Args:
            new_key_file: Path for new key (default: generate new in default location)

        Security:
        - Generates new Fernet key
        - Saves with 0o600 permissions
        - Existing encrypted data must be manually re-encrypted

        Note:
            After key rotation, you must re-encrypt all existing encrypted files
            using the old key to decrypt and new key to encrypt.
        """
        logger.warning("Key rotation initiated - this will re-encrypt all data")

        # Generate new key
        new_key = Fernet.generate_key()
        new_cipher = Fernet(new_key)

        # Save new key
        if new_key_file is None:
            new_key_file = self.key_file

        with open(new_key_file, "wb") as f:
            f.write(new_key)
        os.chmod(new_key_file, 0o600)

        # Update cipher (note: existing encrypted data needs manual re-encryption)
        self.cipher = new_cipher

        logger.info(f"Encryption key rotated: {new_key_file}")
        logger.warning("Existing encrypted files must be re-encrypted with new key")


# Global encryption manager (singleton)
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager (singleton).

    Returns:
        EncryptionManager singleton instance

    Usage:
        >>> from src.security.encryption import get_encryption_manager
        >>> manager = get_encryption_manager()
        >>> encrypted = manager.encrypt(b"sensitive data")

    Security: Singleton ensures consistent key usage across application.
    """
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
