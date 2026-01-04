"""AES-GCM, AES-CBC encryption and HMAC utilities."""

import base64
import hashlib
import hmac
import secrets

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .key_manager import KeyManager


class AESGCMEncryptor:
    """AES-GCM encryption/decryption for sensitive data like PAN."""

    def __init__(self, key_manager: KeyManager):
        """Initialize AES-GCM encryptor with key manager."""
        self.key_manager = key_manager

    def encrypt(self, plaintext: str, key_id: str = "current") -> str:
        """Encrypt plaintext using AES-GCM."""
        key = self.key_manager.get_aes_key(key_id)

        iv = secrets.token_bytes(12)

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()

        ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

        result = key_id.encode("utf-8") + b":" + iv + ciphertext + encryptor.tag

        return base64.b64encode(result).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt AES-GCM encrypted data."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data) if isinstance(encrypted_data, str) else encrypted_data

            parts = encrypted_bytes.split(b":", 1)
            if len(parts) != 2:
                raise ValueError("Invalid encrypted data format")

            key_id = parts[0].decode("utf-8")
            data = parts[1]

            if len(data) < 12 + 16:
                raise ValueError("Encrypted data too short")

            iv = data[:12]
            tag = data[-16:]
            ciphertext = data[12:-16]

            key = self.key_manager.get_aes_key(key_id)

            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext.decode("utf-8")

        except Exception as e:
            raise ValueError(f"Decryption failed: {e!s}") from e


class AESCBCEncryptor:
    """AES-256-CBC encryption/decryption with PKCS#7 padding.

    This class provides symmetric encryption using AES in CBC mode with PKCS#7 padding.
    CBC mode is suitable for encrypting data at rest and provides confidentiality.
    Note: CBC mode does not provide authentication, consider using GCM for authenticated encryption.
    """

    def __init__(self, key_manager: KeyManager, key_id: str = "current"):
        """Initialize AES-CBC encryptor with key manager.

        Args:
            key_manager: Key manager instance
            key_id: Key identifier to use (default: "current")
        """
        self.key_manager = key_manager
        self.key_id = key_id
        self.key = key_manager.get_aes_key(key_id)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext using AES-256-CBC with PKCS#7 padding.

        Args:
            plaintext: The text to encrypt

        Returns:
            Base64 encoded string containing: iv:ciphertext
        """
        iv = secrets.token_bytes(16)

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        result = iv + ciphertext

        return base64.b64encode(result).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt AES-256-CBC encrypted data with PKCS#7 padding.

        Args:
            encrypted_data: Base64 encoded encrypted data (format: iv:ciphertext)

        Returns:
            Decrypted plaintext string

        Raises:
            InvalidPaddingError: If padding validation fails
            ValueError: If decryption fails or data is corrupted
        """
        from ..core.errors import InvalidPaddingError

        try:
            encrypted_bytes = base64.b64decode(encrypted_data) if isinstance(encrypted_data, str) else encrypted_data
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {e!s}") from e

        if len(encrypted_bytes) < 16:
            raise ValueError("Encrypted data too short")

        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]

        try:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e!s}") from e

        try:
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        except ValueError as e:
            raise InvalidPaddingError(f"Invalid padding: {e!s}") from e

        try:
            return plaintext.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Decrypted data is not valid UTF-8: {e!s}") from e


class HMACManager:
    """HMAC-SHA256 operations for deterministic hashing."""

    def __init__(self, key_manager: KeyManager):
        """Initialize HMAC manager with key manager."""
        self.key_manager = key_manager

    def create_fingerprint(self, data: str) -> str:
        """Create HMAC-SHA256 fingerprint for deterministic lookups."""
        key = self.key_manager.get_hmac_key()
        return hmac.new(key, data.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_fingerprint(self, data: str, fingerprint: str) -> bool:
        """Verify data against HMAC fingerprint."""
        expected = self.create_fingerprint(data)
        return hmac.compare_digest(expected, fingerprint)


from .key_manager import key_manager 

aes_gcm_encryptor = AESGCMEncryptor(key_manager)
aes_cbc_encryptor = AESCBCEncryptor(key_manager)
hmac_manager = HMACManager(key_manager)
