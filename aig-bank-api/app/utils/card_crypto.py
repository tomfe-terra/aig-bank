"""Credit card data encryption and processing utilities."""

from .encryption import AESGCMEncryptor, HMACManager
from .key_manager import KeyManager


class CardDataProcessor:
    """Processes credit card data with encryption and validation."""

    def __init__(self):
        """Initialize card data processor with crypto components."""
        self.key_manager = KeyManager()
        self.encryptor = AESGCMEncryptor(self.key_manager)
        self.hmac_manager = HMACManager(self.key_manager)

    def process_card_data(self, pan: str, exp_month: int, exp_year: int, cvv: str) -> tuple[str, str, str, str, str]:
        """Process card data: encrypt PAN and CVV, create fingerprint, validate card.

        Returns: (pan_ciphertext, cvv_ciphertext, pan_fingerprint, last4, brand).
        """
        from app.models.credit_card_model import CreditCard

        if not pan or len(pan) != 16:
            raise ValueError("PAN must be exactly 16 digits")

        from app.utils.luhn import validate_luhn

        if not validate_luhn(pan):
            raise ValueError("Invalid PAN (Luhn check failed)")

        if not CreditCard.validate_expiry(exp_month, exp_year):
            raise ValueError("Card has expired or expiry date is invalid")

        if not cvv or not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
            raise ValueError("Invalid CVV format")

        brand = self._get_card_brand(pan)

        pan_fingerprint = self.hmac_manager.create_fingerprint(pan)

        pan_ciphertext = self.encryptor.encrypt(pan)

        cvv_ciphertext = self.encryptor.encrypt(cvv)

        last4 = pan[-4:]

        return pan_ciphertext, cvv_ciphertext, pan_fingerprint, last4, brand

    def retrieve_pan(self, pan_ciphertext: str) -> str:
        """Retrieve and decrypt PAN from ciphertext."""
        return self.encryptor.decrypt(pan_ciphertext)

    def retrieve_cvv(self, cvv_ciphertext: str) -> str:
        """Retrieve and decrypt CVV from ciphertext."""
        return self.encryptor.decrypt(cvv_ciphertext)

    def _get_card_brand(self, pan: str) -> str:
        """Determine card brand from PAN using CreditCard model logic."""
        from app.models.credit_card_model import CreditCard

        return CreditCard.detect_brand(pan)


card_processor = CardDataProcessor()
