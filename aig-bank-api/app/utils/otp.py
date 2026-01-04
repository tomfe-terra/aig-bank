"""OTP (One-Time Password) management utilities."""


class OTPManager:
    """OTP (One-Time Password) manager using TOTP with pyotp."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a random base32 secret for OTP.

        Returns:
            Base32 encoded secret string
        """
        import pyotp

        return pyotp.random_base32()

    @staticmethod
    def generate_otp_uri(username: str, secret: str, issuer: str = "BankApp") -> str:
        """Generate OTP URI for QR code generation.

        Args:
            username: User's username
            secret: Base32 encoded secret
            issuer: Application name

        Returns:
            OTP URI in format: otpauth://totp/Issuer:Username?secret=SECRET&issuer=Issuer
        """
        import pyotp

        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)

    @staticmethod
    def verify_otp(secret: str, otp_code: str, window: int = 1) -> bool:
        """Verify an OTP code against a secret.

        Args:
            secret: Base32 encoded secret
            otp_code: 6-digit OTP code to verify
            window: Number of time steps to check before and after current time (default: 1)

        Returns:
            True if OTP is valid, False otherwise
        """
        import pyotp

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(otp_code, valid_window=window)
        except Exception:
            return False


otp_manager = OTPManager()
