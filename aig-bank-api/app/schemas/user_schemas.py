"""User service schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.enums import UserRole, UserStatus


class UserRead(BaseModel):
    """User read schema."""

    id: UUID = Field(..., description="Unique user identifier", examples=["550e8400-e29b-41d4-a716-446655440000"])
    username: str = Field(..., description="Username for login", examples=["johndoe"])
    email: str | None = Field(None, description="User email address (optional)", examples=["john.doe@example.com"])
    phone: str | None = Field(None, description="User phone number (optional)", examples=["+1234567890"])
    address: str | None = Field(None, description="User address (optional)", examples=["123 Main St, City, Country"])
    first_name: str = Field(..., description="User first name", examples=["John"])
    last_name: str = Field(..., description="User last name", examples=["Doe"])
    role: UserRole = Field(..., description="User role", examples=[UserRole.USER])
    status: UserStatus = Field(..., description="User account status", examples=[UserStatus.ENABLED])
    has_avatar: bool = Field(..., description="Whether user has an avatar", examples=[True, False])

    model_config = ConfigDict(from_attributes=True, title="User")


class ProfileUpdate(BaseModel):
    """Profile update request schema."""

    first_name: str | None = Field(None, description="User first name", examples=["John"])
    last_name: str | None = Field(None, description="User last name", examples=["Doe"])
    email: str | None = Field(None, description="User email address", examples=["john.doe@example.com"])
    phone: str | None = Field(None, description="User phone number", examples=["+1234567890"])
    address: str | None = Field(None, description="User address", examples=["123 Main St, City, Country"])

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        if v is None:
            return v
        from ..utils.validators import InputValidator

        return InputValidator.validate_email(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone format."""
        if v is None:
            return v
        from ..utils.validators import InputValidator

        return InputValidator.validate_phone(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name fields."""
        if v is None:
            return v
        from ..utils.validators import InputValidator

        return InputValidator.validate_name(v)

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str | None) -> str | None:
        """Validate address field."""
        if v is None:
            return v
        from ..utils.validators import InputValidator

        return InputValidator.validate_address(v)

    model_config = ConfigDict(title="Profile Update")


class ProfileUpdateResult(BaseModel):
    """Profile update result schema."""

    message: str = Field(..., description="Success message", examples=["Profile updated successfully"])
    user: UserRead = Field(..., description="Updated user information")

    model_config = ConfigDict(title="Profile Update Result")


class AvatarUploadResult(BaseModel):
    """Avatar upload result schema."""

    message: str = Field(..., description="Success message", examples=["Avatar uploaded successfully"])
    has_avatar: bool = Field(..., description="Whether user now has an avatar", examples=[True])

    model_config = ConfigDict(title="Avatar Upload Result")


__all__ = [
    "AvatarUploadResult",
    "ProfileUpdate",
    "ProfileUpdateResult",
    "UserRead",
]
