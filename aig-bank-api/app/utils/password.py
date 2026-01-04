"""Password hashing and validation utilities."""

import bcrypt

from ..core.constants import BCRYPT_ROUNDS, PASSWORD_POLICY
from ..core.errors import PasswordPolicyError


class PasswordManager:
    """Password hashing and verification utilities."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        if not password or not hashed:
            return False

        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Validate password strength requirements. Raises ValidationError on failure."""
        if not password:
            raise PasswordPolicyError("Password cannot be empty")

        if len(password) < PASSWORD_POLICY["min_length"]:
            raise PasswordPolicyError(f"Password must be at least {PASSWORD_POLICY['min_length']} characters long")

        if len(password) > PASSWORD_POLICY["max_length"]:
            raise PasswordPolicyError(f"Password must be no more than {PASSWORD_POLICY['max_length']} characters long")

        if not any(c.isupper() for c in password):
            raise PasswordPolicyError(f"Password must contain at least {PASSWORD_POLICY['min_uppercase']} uppercase letter")

        if not any(c.islower() for c in password):
            raise PasswordPolicyError(f"Password must contain at least {PASSWORD_POLICY['min_lowercase']} lowercase letter")

        if not any(c.isdigit() for c in password):
            raise PasswordPolicyError(f"Password must contain at least {PASSWORD_POLICY['min_digits']} digit")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise PasswordPolicyError(f"Password must contain at least {PASSWORD_POLICY['min_special']} special character")

        common_patterns: list[str] = PASSWORD_POLICY["common_patterns"]

        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                raise PasswordPolicyError(f"Password contains common weak pattern: {pattern}")

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password for testing purposes."""
        import random
        import string

        min_length: int = PASSWORD_POLICY["min_length"]
        if length < min_length:
            length = min_length

        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        password_chars = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special),
        ]

        all_chars = lowercase + uppercase + digits + special
        password_chars.extend(random.choice(all_chars) for _ in range(length - 4))

        random.shuffle(password_chars)

        return "".join(password_chars)
