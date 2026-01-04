"""Encryption key management utilities."""

from ..core.config import settings


class KeyManager:
    """Manages encryption keys for AES-GCM and HMAC operations."""

    def __init__(self):
        """Initialize key manager with AES and HMAC keys from settings."""
        aes_key_bytes = settings.aes_key.encode("utf-8")
        if len(aes_key_bytes) < 32:
            aes_key_bytes = aes_key_bytes.ljust(32, b"\x00")
        elif len(aes_key_bytes) > 32:
            aes_key_bytes = aes_key_bytes[:32]

        self._aes_key = aes_key_bytes
        self._hmac_key = settings.hmac_key.encode("utf-8")

        self._key_versions: dict[str, bytes] = {"current": self._aes_key}

    def get_aes_key(self, key_id: str = "current") -> bytes:
        """Get AES key by ID."""
        return self._key_versions.get(key_id, self._aes_key)

    def get_hmac_key(self) -> bytes:
        """Get HMAC key."""
        return self._hmac_key


key_manager = KeyManager()
