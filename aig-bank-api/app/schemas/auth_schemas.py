"""Authentication request/response schemas."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from ..utils.validators import InputValidator
from .account_schemas import AccountRead
from .api_key_schemas import APIKeyRead
from .user_schemas import UserRead


class ProfileRead(BaseModel):
    """Comprehensive user profile including user details, account, and API keys."""

    user: UserRead = Field(..., description="User details")
    account: AccountRead | None = Field(None, description="User's account (one per user)")
    api_keys: list[APIKeyRead] = Field(default_factory=list, description="User's API keys")

    model_config = ConfigDict(from_attributes=True, title="User Profile")


class AccessToken(BaseModel):
    """Access token response."""

    access_token: str = Field(
        ...,
        description="JWT access token for API authorization",
    )
    access_token_expires_at: datetime = Field(
        ...,
        description="Access token expiration timestamp (UTC)",
    )

    model_config = ConfigDict(title="Access Token")


class TokenPair(AccessToken):
    """Access and refresh token pair response."""

    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
    )
    refresh_token_expires_at: datetime = Field(
        ...,
        description="Refresh token expiration timestamp (UTC)",
    )

    model_config = ConfigDict(title="Token Pair")


class Login(BaseModel):
    """Login credentials with OTP for 2FA."""

    username: str = Field(..., description="Username for login", examples=["johndoe"])
    password: str = Field(..., description="User password", examples=["SecureP@ssw0rd123"])
    otp_code: str = Field(..., description="6-digit OTP code from authenticator app", examples=["123456"])

    model_config = ConfigDict(title="Login Credentials")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        return InputValidator.validate_username(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty."""
        return InputValidator.validate_length(v.strip() if v else "", "password", "Password")

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, v: str) -> str:
        """Validate OTP code format."""
        return InputValidator.validate_otp_code(v)


class RefreshToken(BaseModel):
    """Refresh token data."""

    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
        examples=[
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ0eXBlIjoicmVmcmVzaCIsImV4cCI6MTczNjM1MjAwMH0.xyz789"
        ],
    )

    model_config = ConfigDict(title="Refresh Token")

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        """Validate refresh token is not empty."""
        return v.strip() if v else v


class Logout(BaseModel):
    """Logout data."""

    refresh_token: str | None = Field(
        default=None,
        description="Optional refresh token to blacklist on logout",
        examples=[
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ0eXBlIjoicmVmcmVzaCIsImV4cCI6MTczNjM1MjAwMH0.xyz789"
        ],
    )

    model_config = ConfigDict(title="Logout")


class LogoutConfirmation(BaseModel):
    """Logout confirmation."""

    message: str = Field(
        default="Successfully logged out",
        description="Logout confirmation message",
    )

    model_config = ConfigDict(from_attributes=True, title="Logout Confirmation")


class SecurityQuestionsLookup(BaseModel):
    """Username for security questions lookup."""

    username: str = Field(
        ...,
        description="Username of the account",
        examples=["johndoe"],
    )

    model_config = ConfigDict(title="Security Questions Lookup")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        return InputValidator.validate_username(v)


class SecurityQuestions(BaseModel):
    """Security questions for password reset."""

    questions: list[str] = Field(
        ...,
        description="List of security questions",
        examples=[["What was the name of your first pet?", "In what city were you born?", "What is your mother's maiden name?"]],
    )
    message: str = Field(
        default="Please answer all security questions to reset your password",
        description="Instructions",
        examples=["Please answer all security questions to reset your password"],
    )

    model_config = ConfigDict(title="Security Questions")

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: list[str]) -> list[str]:
        """Validate security questions list."""
        return InputValidator.validate_list_length(v, 3, "Security questions")


class PasswordResetWithAnswers(BaseModel):
    """Password reset using security question answers."""

    username: str = Field(
        ...,
        description="Username of the account",
        examples=["johndoe"],
    )
    answers: list[str] = Field(
        ...,
        description="Answers to security questions in order",
        examples=[["Fluffy", "New York", "Smith"]],
    )
    new_password: str = Field(
        ...,
        description="New password",
        examples=["NewSecureP@ssw0rd456"],
    )

    model_config = ConfigDict(title="Password Reset")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        return InputValidator.validate_username(v)

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: list[str]) -> list[str]:
        """Validate security question answers."""
        return InputValidator.validate_string_list(v, 3, "security_answer", "Security question answers")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate password strength."""
        from ..utils.password import PasswordManager

        PasswordManager.validate_password_strength(v)
        return v


class PasswordResetConfirmation(BaseModel):
    """Confirmation after successful password reset."""

    message: str = Field(
        default="Password has been successfully reset",
        description="Success message",
    )

    model_config = ConfigDict(title="Password Reset Confirmation")


__all__ = [
    "AccessToken",
    "Login",
    "Logout",
    "LogoutConfirmation",
    "PasswordResetConfirmation",
    "PasswordResetWithAnswers",
    "ProfileRead",
    "RefreshToken",
    "SecurityQuestions",
    "SecurityQuestionsLookup",
    "TokenPair",
]
