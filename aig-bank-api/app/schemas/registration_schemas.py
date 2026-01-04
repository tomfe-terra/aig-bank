"""Multi-phase registration schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.validators import InputValidator
from .general import Message


class SecurityQuestionAnswer(BaseModel):
    """A single security question and answer."""

    question_id: int = Field(
        ...,
        description="ID of the predefined security question",
        examples=[1],
    )
    answer: str = Field(
        ...,
        description="Answer to the security question",
        examples=["Fluffy"],
    )

    model_config = ConfigDict(title="Security Question Answer")

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, v: int) -> int:
        """Validate question ID exists in predefined questions."""
        return InputValidator.validate_security_question_id(v)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v: str) -> str:
        """Validate security answer format."""
        return InputValidator.validate_security_answer(v)


class StartRegistration(BaseModel):
    """Start registration with basic info."""

    username: str = Field(
        ...,
        description="Username for login",
        examples=["johndoe"],
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecureP@ssw0rd123"],
    )
    first_name: str = Field(
        ...,
        description="User's first name",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        description="User's last name",
        examples=["Doe"],
    )
    email: str | None = Field(
        None,
        description="User's email (optional)",
        examples=["john.doe@example.com"],
    )
    phone: str | None = Field(
        None,
        description="User's phone number (optional)",
        examples=["+1-555-123-4567"],
    )
    address: str | None = Field(
        None,
        description="User's address (optional)",
        examples=["123 Main St, City, State 12345"],
    )

    model_config = ConfigDict(title="Start Registration")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        return InputValidator.validate_username(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        from ..utils.password import PasswordManager

        PasswordManager.validate_password_strength(v)
        return v

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        """Validate first name format."""
        return InputValidator.validate_name(v, "First name")

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v: str) -> str:
        """Validate last name format."""
        return InputValidator.validate_name(v, "Last name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        return InputValidator.validate_email(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone format."""
        return InputValidator.validate_phone(v)

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str | None) -> str | None:
        """Validate address format."""
        return InputValidator.validate_address(v)


class RegistrationToken(Message):
    """Registration token for next step."""

    token: str = Field(
        ...,
        description="Encrypted registration token for next step",
    )

    model_config = ConfigDict(title="Registration Token")


class SetSecurityQuestions(BaseModel):
    """Step 2: Set security questions."""

    token: str = Field(
        ...,
        description="Registration token from step 1",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG5kb2UiLCJzdGVwIjoxfQ.abc123"],
    )
    security_questions: list[SecurityQuestionAnswer] = Field(
        ...,
        description="Three security questions and answers",
        examples=[
            [
                {"question_id": 1, "answer": "Fluffy"},
                {"question_id": 5, "answer": "New York"},
                {"question_id": 10, "answer": "Smith"},
            ]
        ],
    )

    model_config = ConfigDict(title="Set Security Questions")

    @field_validator("security_questions")
    @classmethod
    def validate_security_questions(cls, v: list[SecurityQuestionAnswer]) -> list[SecurityQuestionAnswer]:
        """Validate security questions: exactly 3, all unique, and valid IDs."""
        return InputValidator.validate_security_questions_list(v)


class OTPSetup(RegistrationToken):
    """OTP setup after step 2."""

    otp_uri: str = Field(
        ...,
        description="OTP URI for QR code generation (otpauth://...)",
    )
    otp_secret: str = Field(
        ...,
        description="OTP secret key (for manual entry)",
    )

    model_config = ConfigDict(title="OTP Setup")


class VerifyOTP(BaseModel):
    """Step 3: Verify OTP code to complete registration."""

    token: str = Field(
        ...,
        description="Registration token from step 2",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG5kb2UiLCJzdGVwIjoyfQ.xyz789"],
    )
    otp_code: str = Field(
        ...,
        description="6-digit OTP code from authenticator app",
        examples=["123456"],
    )

    model_config = ConfigDict(title="Verify OTP")

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, v: str) -> str:
        """Validate OTP code format."""
        return InputValidator.validate_otp_code(v)


class RegistrationComplete(Message):
    """Registration completion status."""

    username: str = Field(
        ...,
        description="Username",
    )

    model_config = ConfigDict(from_attributes=True, title="Registration Complete")


class SecurityQuestionOption(BaseModel):
    """A predefined security question option."""

    id: int = Field(
        ...,
        description="Question ID",
    )
    question: str = Field(
        ...,
        description="Security question text",
    )

    model_config = ConfigDict(title="Security Question Option")


class SecurityQuestionsList(BaseModel):
    """List of available security questions."""

    questions: list[SecurityQuestionOption] = Field(
        ...,
        description="Available security questions",
    )

    model_config = ConfigDict(title="Security Questions List")


__all__ = [
    "OTPSetup",
    "RegistrationComplete",
    "RegistrationToken",
    "SecurityQuestionAnswer",
    "SecurityQuestionOption",
    "SecurityQuestionsList",
    "SetSecurityQuestions",
    "StartRegistration",
    "VerifyOTP",
]
