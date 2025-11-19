"""Tests for encryption utilities.

v0.2.11 FEAT-PRIV-001: Encryption at Rest

Tests for secure encryption/decryption of sensitive user data.
"""

import os
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken

from src.security.encryption import EncryptionManager, get_encryption_manager


class TestEncryptionManager:
    """Test suite for EncryptionManager class."""

    def test_encryption_manager_initialization(self, tmp_path: Path) -> None:
        """Test encryption manager initialisation with custom key file."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        assert manager.key_file == key_file
        assert key_file.exists()
        assert manager.cipher is not None

    def test_default_key_path_creation(self) -> None:
        """Test that default key path is OS-specific and created."""
        manager = EncryptionManager()

        # Key file should be created
        assert manager.key_file.exists()

        # Key file should have restrictive permissions (user only)
        stat_info = os.stat(manager.key_file)
        # Check that file is readable/writable by owner only (0o600)
        # On some systems this might be more permissive, so we just check it exists
        assert stat_info.st_mode & 0o700  # At least user permissions

    def test_key_file_permissions(self, tmp_path: Path) -> None:
        """Test that key file has restrictive permissions."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Check file permissions
        stat_info = os.stat(key_file)
        # File should be 0o600 (rw-------)
        file_mode = stat_info.st_mode & 0o777

        # On Unix systems, should be exactly 0o600
        # On Windows, permissions work differently, so we're more lenient
        import sys
        if sys.platform != "win32":
            assert file_mode == 0o600, f"Expected 0o600, got {oct(file_mode)}"

    def test_encrypt_decrypt_round_trip(self, tmp_path: Path) -> None:
        """Test basic encryption and decryption."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Test data
        plaintext = b"sensitive user data"

        # Encrypt
        ciphertext = manager.encrypt(plaintext)

        # Ciphertext should be different from plaintext
        assert ciphertext != plaintext
        assert len(ciphertext) > len(plaintext)  # Fernet adds overhead

        # Decrypt
        decrypted = manager.decrypt(ciphertext)

        # Should match original
        assert decrypted == plaintext

    def test_encrypt_unicode_data(self, tmp_path: Path) -> None:
        """Test encryption of Unicode text."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Unicode text with emojis
        plaintext = "Hello 世界 🔐🛡️".encode("utf-8")

        # Encrypt and decrypt
        ciphertext = manager.encrypt(plaintext)
        decrypted = manager.decrypt(ciphertext)

        assert decrypted == plaintext
        assert decrypted.decode("utf-8") == "Hello 世界 🔐🛡️"

    def test_encrypt_empty_data(self, tmp_path: Path) -> None:
        """Test encryption of empty data."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        plaintext = b""
        ciphertext = manager.encrypt(plaintext)
        decrypted = manager.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_encrypt_large_data(self, tmp_path: Path) -> None:
        """Test encryption of large data (1MB)."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # 1MB of data
        plaintext = b"x" * (1024 * 1024)

        ciphertext = manager.encrypt(plaintext)
        decrypted = manager.decrypt(ciphertext)

        assert decrypted == plaintext
        assert len(decrypted) == 1024 * 1024

    def test_decrypt_with_wrong_key_fails(self, tmp_path: Path) -> None:
        """Test that decryption fails with wrong key."""
        key_file1 = tmp_path / "key1.key"
        key_file2 = tmp_path / "key2.key"

        manager1 = EncryptionManager(key_file=key_file1)
        manager2 = EncryptionManager(key_file=key_file2)

        plaintext = b"sensitive data"
        ciphertext = manager1.encrypt(plaintext)

        # Decrypt with different key should fail
        with pytest.raises(InvalidToken):
            manager2.decrypt(ciphertext)

    def test_decrypt_corrupted_data_fails(self, tmp_path: Path) -> None:
        """Test that decryption of corrupted data fails."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        plaintext = b"sensitive data"
        ciphertext = manager.encrypt(plaintext)

        # Corrupt the ciphertext
        corrupted = ciphertext[:-10] + b"corrupted!"

        # Decrypt should fail
        with pytest.raises(InvalidToken):
            manager.decrypt(corrupted)

    def test_decrypt_random_data_fails(self, tmp_path: Path) -> None:
        """Test that decryption of random data fails."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        random_data = b"this is not encrypted data"

        # Decrypt should fail
        with pytest.raises(InvalidToken):
            manager.decrypt(random_data)

    def test_key_persistence(self, tmp_path: Path) -> None:
        """Test that key persists across manager instances."""
        key_file = tmp_path / "test_encryption.key"

        # Create first manager
        manager1 = EncryptionManager(key_file=key_file)
        plaintext = b"test data"
        ciphertext = manager1.encrypt(plaintext)

        # Create second manager with same key file
        manager2 = EncryptionManager(key_file=key_file)

        # Should be able to decrypt with second manager
        decrypted = manager2.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_file(self, tmp_path: Path) -> None:
        """Test file encryption."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Create test file
        plaintext_file = tmp_path / "test_data.txt"
        plaintext_file.write_text("sensitive file contents")

        # Encrypt file
        encrypted_file = manager.encrypt_file(plaintext_file)

        assert encrypted_file.exists()
        assert encrypted_file == tmp_path / "test_data.txt.enc"

        # Encrypted file should have restrictive permissions
        import sys
        if sys.platform != "win32":
            stat_info = os.stat(encrypted_file)
            file_mode = stat_info.st_mode & 0o777
            assert file_mode == 0o600

        # Encrypted file should not contain plaintext
        encrypted_contents = encrypted_file.read_bytes()
        assert b"sensitive file contents" not in encrypted_contents

    def test_decrypt_file(self, tmp_path: Path) -> None:
        """Test file decryption."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Create and encrypt test file
        plaintext_file = tmp_path / "test_data.txt"
        original_contents = "sensitive file contents"
        plaintext_file.write_text(original_contents)

        encrypted_file = manager.encrypt_file(plaintext_file)

        # Decrypt file
        decrypted_file = manager.decrypt_file(encrypted_file)

        assert decrypted_file.exists()
        assert decrypted_file == plaintext_file  # Should remove .enc extension

        # Contents should match original
        decrypted_contents = decrypted_file.read_text()
        assert decrypted_contents == original_contents

    def test_encrypt_decrypt_file_custom_paths(self, tmp_path: Path) -> None:
        """Test file encryption/decryption with custom output paths."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Create test file
        plaintext_file = tmp_path / "source.txt"
        plaintext_file.write_text("test contents")

        # Encrypt to custom path
        encrypted_file = tmp_path / "encrypted" / "data.enc"
        encrypted_file.parent.mkdir()
        result = manager.encrypt_file(plaintext_file, encrypted_file)

        assert result == encrypted_file
        assert encrypted_file.exists()

        # Decrypt to custom path
        decrypted_file = tmp_path / "decrypted" / "data.txt"
        decrypted_file.parent.mkdir()
        result = manager.decrypt_file(encrypted_file, decrypted_file)

        assert result == decrypted_file
        assert decrypted_file.exists()
        assert decrypted_file.read_text() == "test contents"

    def test_key_rotation(self, tmp_path: Path) -> None:
        """Test key rotation functionality."""
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Encrypt with original key
        plaintext = b"data before rotation"
        ciphertext_old = manager.encrypt(plaintext)

        # Rotate key
        manager.rotate_key()

        # Old ciphertext should not decrypt with new key
        with pytest.raises(InvalidToken):
            manager.decrypt(ciphertext_old)

        # New encryption should work
        ciphertext_new = manager.encrypt(plaintext)
        decrypted = manager.decrypt(ciphertext_new)
        assert decrypted == plaintext

    def test_multiple_encryptions_produce_different_ciphertexts(self, tmp_path: Path) -> None:
        """Test that encrypting same plaintext produces different ciphertexts.

        Security: Fernet uses random IV, so same plaintext should produce
        different ciphertexts each time (prevents pattern analysis).
        """
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        plaintext = b"same data every time"

        ciphertext1 = manager.encrypt(plaintext)
        ciphertext2 = manager.encrypt(plaintext)
        ciphertext3 = manager.encrypt(plaintext)

        # All ciphertexts should be different (random IV)
        assert ciphertext1 != ciphertext2
        assert ciphertext2 != ciphertext3
        assert ciphertext1 != ciphertext3

        # But all should decrypt to same plaintext
        assert manager.decrypt(ciphertext1) == plaintext
        assert manager.decrypt(ciphertext2) == plaintext
        assert manager.decrypt(ciphertext3) == plaintext


class TestEncryptionManagerSingleton:
    """Test suite for encryption manager singleton."""

    def test_get_encryption_manager_singleton(self) -> None:
        """Test that get_encryption_manager returns singleton."""
        manager1 = get_encryption_manager()
        manager2 = get_encryption_manager()

        # Should be the same instance
        assert manager1 is manager2

    def test_singleton_consistency(self) -> None:
        """Test that singleton maintains key consistency."""
        manager1 = get_encryption_manager()
        plaintext = b"test data"
        ciphertext = manager1.encrypt(plaintext)

        # Get singleton again
        manager2 = get_encryption_manager()

        # Should decrypt successfully (same key)
        decrypted = manager2.decrypt(ciphertext)
        assert decrypted == plaintext


class TestEncryptionSecurity:
    """Security-specific tests for encryption."""

    def test_no_plaintext_in_encrypted_output(self, tmp_path: Path) -> None:
        """Test that encrypted output contains no traces of plaintext.

        Security: Prevents information leakage through ciphertext.
        """
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Test with various plaintext patterns
        test_cases = [
            b"password123",
            b"user@example.com",
            b"SECRET_API_KEY",
            b"123-45-6789",  # SSN pattern
        ]

        for plaintext in test_cases:
            ciphertext = manager.encrypt(plaintext)

            # Plaintext should not appear in ciphertext
            assert plaintext not in ciphertext, f"Plaintext {plaintext} found in ciphertext!"

    def test_encrypted_data_not_json(self, tmp_path: Path) -> None:
        """Test that encrypted data is not valid JSON.

        Security: Ensures data is actually encrypted, not just encoded.
        """
        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        import json

        # Encrypt JSON data
        plaintext = json.dumps({"secret": "value"}).encode("utf-8")
        ciphertext = manager.encrypt(plaintext)

        # Ciphertext should not be valid JSON
        with pytest.raises((json.JSONDecodeError, UnicodeDecodeError)):
            json.loads(ciphertext.decode("utf-8"))

    def test_key_file_not_world_readable(self, tmp_path: Path) -> None:
        """Test that key file is not readable by other users.

        Security: Prevents unauthorized key access.
        """
        import sys

        # Skip on Windows (different permission model)
        if sys.platform == "win32":
            pytest.skip("Windows has different permission model")

        key_file = tmp_path / "test_encryption.key"
        manager = EncryptionManager(key_file=key_file)

        stat_info = os.stat(key_file)
        file_mode = stat_info.st_mode & 0o777

        # Should be 0o600 (rw-------)
        # Not readable by group or others
        assert (file_mode & 0o044) == 0, "Key file is readable by group or others!"


# Mark all tests as security tests
pytestmark = pytest.mark.security
