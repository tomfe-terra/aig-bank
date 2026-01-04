"""Global input validation utilities with pattern-based validation."""

import re
from typing import ClassVar

from ..core.errors import InputValidationError


class InputValidator:
    """Centralized input validation with pattern matching."""

    PATTERNS: ClassVar[dict[str, dict[str, str]]] = {
        "username": {
            "pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "message": "Username must be 3-50 characters, alphanumeric with underscores and hyphens only",
        },
        "email": {
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "message": "Invalid email format",
        },
        "phone": {
            "pattern": r"^[\d\s\-\+\(\)]{7,50}$",
            "message": "Phone number must be 7-50 characters, digits and common separators only",
        },
        "name": {
            "pattern": r"^[a-zA-Z\s\-']{1,255}$",
            "message": "Name must be 1-255 characters, letters, spaces, hyphens and apostrophes only",
        },
        "address": {
            "pattern": r"^[a-zA-Z0-9\s\-,.'#]{1,500}$",
            "message": "Address must be 1-500 characters, alphanumeric with common punctuation",
        },
        "security_answer": {
            "pattern": r"^.{2,255}$",
            "message": "Answer must be 2-255 characters",
        },
        "otp_code": {
            "pattern": r"^\d{6}$",
            "message": "OTP code must be exactly 6 digits",
        },
    }

    LENGTH_CONSTRAINTS: ClassVar[dict[str, tuple[int, int]]] = {
        "username": (3, 50),
        "password": (8, 128),
        "name": (1, 255),
        "email": (5, 255),
        "phone": (7, 50),
        "address": (1, 500),
        "security_answer": (2, 255),
        "otp_code": (6, 6),
        "description": (0, 1000),
    }

    @classmethod
    def validate_pattern(cls, value: str, pattern_name: str, field_name: str | None = None) -> str:
        """Validate a string against a named pattern.

        Args:
            value: The value to validate
            pattern_name: Name of the pattern from PATTERNS dict
            field_name: Optional field name for error messages

        Returns:
            The validated value (stripped)

        Raises:
            InputValidationError: If validation fails
        """
        if not value:
            raise InputValidationError(f"{field_name or pattern_name.capitalize()} cannot be empty")

        value = value.strip()

        if pattern_name not in cls.PATTERNS:
            raise InputValidationError(f"Unknown validation pattern: {pattern_name}")

        pattern_config = cls.PATTERNS[pattern_name]
        pattern = pattern_config["pattern"]
        message = pattern_config["message"]

        if not re.match(pattern, value):
            field_display = field_name or pattern_name.replace("_", " ").capitalize()
            raise InputValidationError(f"{field_display}: {message}")

        return value

    @classmethod
    def validate_length(cls, value: str, constraint_name: str, field_name: str | None = None) -> str:
        """Validate string length against named constraints.

        Args:
            value: The value to validate
            constraint_name: Name of the constraint from LENGTH_CONSTRAINTS dict
            field_name: Optional field name for error messages

        Returns:
            The validated value

        Raises:
            InputValidationError: If validation fails
        """
        if constraint_name not in cls.LENGTH_CONSTRAINTS:
            raise InputValidationError(f"Unknown length constraint: {constraint_name}")

        min_len, max_len = cls.LENGTH_CONSTRAINTS[constraint_name]
        value_len = len(value)

        field_display = field_name or constraint_name.replace("_", " ").capitalize()

        if value_len < min_len:
            raise InputValidationError(f"{field_display} must be at least {min_len} characters")

        if value_len > max_len:
            raise InputValidationError(f"{field_display} must be at most {max_len} characters")

        return value

    @classmethod
    def validate_username(cls, value: str) -> str:
        """Validate username format and length.

        Args:
            value: Username to validate

        Returns:
            Validated username (stripped)

        Raises:
            InputValidationError: If validation fails
        """
        value = value.strip()
        cls.validate_length(value, "username", "Username")
        return cls.validate_pattern(value, "username", "Username")

    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        """Validate email format and length.

        Args:
            value: Email to validate (optional)

        Returns:
            Validated email (stripped) or None

        Raises:
            InputValidationError: If validation fails
        """
        if value is None or value.strip() == "":
            return None

        value = value.strip()
        cls.validate_length(value, "email", "Email")
        return cls.validate_pattern(value, "email", "Email")

    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Validate phone number format and length.

        Args:
            value: Phone number to validate (optional)

        Returns:
            Validated phone number (stripped) or None

        Raises:
            ValidationError: If validation fails
        """
        if value is None or value.strip() == "":
            return None

        value = value.strip()
        cls.validate_length(value, "phone", "Phone")
        return cls.validate_pattern(value, "phone", "Phone")

    @classmethod
    def validate_name(cls, value: str, field_name: str = "Name") -> str:
        """Validate name (first name, last name) format and length.

        Args:
            value: Name to validate
            field_name: Display name for error messages

        Returns:
            Validated name (stripped)

        Raises:
            ValidationError: If validation fails
        """
        value = value.strip()
        cls.validate_length(value, "name", field_name)
        return cls.validate_pattern(value, "name", field_name)

    @classmethod
    def validate_address(cls, value: str | None) -> str | None:
        """Validate address format and length.

        Args:
            value: Address to validate (optional)

        Returns:
            Validated address (stripped) or None

        Raises:
            ValidationError: If validation fails
        """
        if value is None or value.strip() == "":
            return None

        value = value.strip()
        cls.validate_length(value, "address", "Address")
        return cls.validate_pattern(value, "address", "Address")

    @classmethod
    def validate_security_answer(cls, value: str) -> str:
        """Validate security question answer format and length.

        Args:
            value: Answer to validate

        Returns:
            Validated answer (stripped)

        Raises:
            ValidationError: If validation fails
        """
        value = value.strip()
        cls.validate_length(value, "security_answer", "Security answer")
        return cls.validate_pattern(value, "security_answer", "Security answer")

    @classmethod
    def validate_otp_code(cls, value: str) -> str:
        """Validate OTP code format.

        Args:
            value: OTP code to validate

        Returns:
            Validated OTP code

        Raises:
            ValidationError: If validation fails
        """
        value = value.strip()
        cls.validate_length(value, "otp_code", "OTP code")
        return cls.validate_pattern(value, "otp_code", "OTP code")

    @classmethod
    def validate_range(cls, value: int, min_val: int, max_val: int, field_name: str = "Value") -> int:
        """Validate integer is within range.

        Args:
            value: Integer to validate
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            field_name: Display name for error messages

        Returns:
            The validated value

        Raises:
            InputValidationError: If validation fails
        """
        if value < min_val or value > max_val:
            raise InputValidationError(f"{field_name} must be between {min_val} and {max_val}")
        return value

    @classmethod
    def validate_security_question_id(cls, question_id: int) -> int:
        """Validate security question ID exists in predefined questions.

        Args:
            question_id: Question ID to validate

        Returns:
            The validated question ID

        Raises:
            InputValidationError: If question ID is invalid
        """
        from ..core.constants import SECURITY_QUESTIONS

        if question_id not in SECURITY_QUESTIONS:
            raise InputValidationError(f"Invalid security question ID: {question_id}")
        return question_id

    @classmethod
    def validate_list_length(cls, value: list, expected_length: int, field_name: str = "List") -> list:
        """Validate list has exactly the expected length.

        Args:
            value: List to validate
            expected_length: Expected number of items
            field_name: Display name for error messages

        Returns:
            The validated list

        Raises:
            InputValidationError: If validation fails
        """
        if len(value) != expected_length:
            raise InputValidationError(f"{field_name} must contain exactly {expected_length} items")
        return value

    @classmethod
    def validate_string_list(cls, value: list[str], expected_length: int, validator_name: str, field_name: str = "Items") -> list[str]:
        """Validate a list of strings with length check and individual validation.

        Args:
            value: List of strings to validate
            expected_length: Expected number of items
            validator_name: Name of the validator method to apply to each item (e.g., 'security_answer')
            field_name: Display name for error messages

        Returns:
            List of validated strings

        Raises:
            InputValidationError: If validation fails
        """
        cls.validate_list_length(value, expected_length, field_name)

        validator_method = getattr(cls, f"validate_{validator_name}", None)
        if not validator_method:
            raise InputValidationError(f"Unknown validator: {validator_name}")

        return [validator_method(item) for item in value]

    @classmethod
    def validate_security_questions_list(cls, questions: list) -> list:
        """Validate list of security questions: exactly 3 and all unique.

        Args:
            questions: List of security question objects with question_id attribute

        Returns:
            The validated list

        Raises:
            InputValidationError: If validation fails
        """
        if len(questions) != 3:
            raise InputValidationError("Exactly 3 security questions are required")

        question_ids = [q.question_id for q in questions]
        if len(question_ids) != len(set(question_ids)):
            raise InputValidationError("All security questions must be unique")

        return questions

    @classmethod
    def validate_pan(cls, value: str) -> str:
        """Validate Primary Account Number (PAN) format.

        Args:
            value: PAN to validate

        Returns:
            The validated PAN

        Raises:
            InputValidationError: If validation fails
        """
        from ..utils.luhn import validate_luhn

        if not value or not value.isdigit():
            raise InputValidationError("PAN must contain only digits")

        if len(value) != 16:
            raise InputValidationError("PAN must be exactly 16 digits")

        if not validate_luhn(value):
            raise InputValidationError("Invalid PAN (Luhn check failed)")

        return value

    @classmethod
    def validate_account_number(cls, value: str, field_name: str = "Account number") -> str:
        """Validate account number format.

        Args:
            value: Account number to validate
            field_name: Name of the field for error messages

        Returns:
            The validated account number

        Raises:
            InputValidationError: If validation fails
        """
        if not value or len(value) < 8 or len(value) > 18:
            raise InputValidationError(f"{field_name} must be 8-18 characters")

        return value

    @classmethod
    def validate_cvv(cls, value: str) -> str:
        """Validate CVV format.

        Args:
            value: CVV to validate

        Returns:
            The validated CVV

        Raises:
            InputValidationError: If validation fails
        """
        if not value.isdigit() or len(value) not in (3, 4):
            raise InputValidationError("CVV must be 3 or 4 digits")

        return value

    @classmethod
    def validate_positive_amount(cls, value: int, field_name: str = "Amount") -> int:
        """Validate that an amount is positive.

        Args:
            value: Amount to validate
            field_name: Name of the field for error messages

        Returns:
            The validated amount

        Raises:
            InputValidationError: If validation fails
        """
        if value <= 0:
            raise InputValidationError(f"{field_name} must be positive")

        return value

    @classmethod
    def validate_expiration_month(cls, value: int) -> int:
        """Validate credit card expiration month.

        Args:
            value: Month to validate (1-12)

        Returns:
            The validated month

        Raises:
            InputValidationError: If validation fails
        """
        if not 1 <= value <= 12:
            raise InputValidationError("Expiration month must be between 1 and 12")

        return value

    @classmethod
    def validate_expiration_year(cls, value: int) -> int:
        """Validate credit card expiration year.

        Args:
            value: Year to validate (4 digits, 2023-2050)

        Returns:
            The validated year

        Raises:
            InputValidationError: If validation fails
        """
        if not 2023 <= value <= 2050:
            raise InputValidationError("Expiration year must be between 2023 and 2050")

        return value

    @classmethod
    def validate_log_filename(cls, value: str) -> str:
        """Validate log filename to prevent path traversal.

        Args:
            value: Filename to validate (can include subdirectories)

        Returns:
            The validated filename

        Raises:
            InputValidationError: If validation fails
        """
        if not value:
            raise InputValidationError("Filename cannot be empty")

        value = value.strip()

        normalized = value.replace("\\", "/")

        path_parts = value.split("/")
        if ".." in path_parts:
            raise InputValidationError("Filename cannot contain parent directory references")

        return normalized


__all__ = ["InputValidator"]
