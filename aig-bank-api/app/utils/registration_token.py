"""Registration token management for multi-phase registration."""

from .encryption import AESCBCEncryptor
from .key_manager import KeyManager


class RegistrationTokenManager:
    """Manages registration tokens for multi-phase registration.

    Uses AES-256-CBC encryption with PKCS#7 padding for token security.
    """

    def __init__(self):
        """Initialize registration token manager with AES-CBC encryption."""
        self.key_manager = KeyManager()
        self.encryptor = AESCBCEncryptor(self.key_manager)

    def create_token(self, data: dict) -> str:
        """Create an encrypted registration token from data.

        Args:
            data: Dictionary containing registration data

        Returns:
            Encrypted token as base64 string
        """
        import pickle

        pickled_data = pickle.dumps(data)

        encrypted = self.encryptor.encrypt(pickled_data.decode("latin1"))

        return encrypted

    def decrypt_token(self, token: str) -> dict:
        """Decrypt and deserialize a registration token.

        Args:
            token: Encrypted token string

        Returns:
            Dictionary containing registration data

        Raises:
            InvalidPaddingError: If padding is invalid
            InvalidTokenError: If token is invalid or corrupted
        """
        import pickle

        from ..core.errors import InvalidPaddingError, InvalidTokenError

        try:
            decrypted = self.encryptor.decrypt(token)

            data = pickle.loads(decrypted.encode("latin1"))

            return data
        except InvalidPaddingError:
            raise
        except Exception as err:
            raise InvalidTokenError("Invalid or corrupted token data") from err


registration_token_manager = RegistrationTokenManager()
