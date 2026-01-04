"""Admin service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ..core.enums import UserRole, UserStatus
from ..utils.validators import InputValidator
from .general import Message


class UserListItem(BaseModel):
    """User list item schema."""

    id: UUID = Field(
        ...,
        description="User ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    username: str = Field(
        ...,
        description="Username",
        examples=["johndoe"],
    )
    email: str | None = Field(
        None,
        description="User email",
        examples=["john.doe@example.com"],
    )
    role: UserRole = Field(
        ...,
        description="User role",
        examples=[UserRole.USER, UserRole.BANKER, UserRole.ADMIN],
    )
    status: UserStatus = Field(
        ...,
        description="User status",
        examples=[UserStatus.ENABLED, UserStatus.DISABLED],
    )
    is_locked: bool = Field(
        ...,
        description="Whether the user account is currently locked (due to failed login attempts or manual lock)",
        examples=[False, True],
    )
    has_avatar: bool = Field(
        ...,
        description="Whether user has an avatar",
        examples=[True, False],
    )
    avatar_url: str | None = Field(
        None,
        description="URL to fetch user avatar (null if no avatar)",
        examples=["/api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/avatar"],
    )
    created_at: datetime = Field(
        ...,
        description="User creation timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )

    model_config = ConfigDict(from_attributes=True, title="User List Item")

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)


class UserList(BaseModel):
    """User list schema."""

    users: list[UserListItem] = Field(
        ...,
        description="List of users",
        examples=[
            [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "johndoe",
                    "email": "john.doe@example.com",
                    "role": "USER",
                    "status": "ENABLED",
                    "is_locked": False,
                    "has_avatar": True,
                    "avatar_url": "/api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/avatar",
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ]
        ],
    )
    total: int = Field(..., description="Total number of users", examples=[100])
    limit: int = Field(..., description="Number of items per page", examples=[50])
    offset: int = Field(..., description="Number of items skipped", examples=[0])

    model_config = ConfigDict(title="User List")


class UserRoleUpdate(BaseModel):
    """User role update schema."""

    role: UserRole = Field(
        ...,
        description="New role for the user",
        examples=[UserRole.USER, UserRole.BANKER, UserRole.ADMIN],
    )

    model_config = ConfigDict(title="Update User Role")


class UserRoleUpdateResult(Message):
    """User role update result schema."""

    user: UserListItem = Field(..., description="Updated user information")

    model_config = ConfigDict(title="User Role Update Result")


class UserUnlockResult(Message):
    """User unlock result schema."""

    model_config = ConfigDict(title="User Unlock Result")


class BankCapitalBalance(BaseModel):
    """Bank capital account balance schema."""

    account_number: str = Field(
        ...,
        validation_alias="number",
        serialization_alias="account_number",
        description="Bank capital account number",
        examples=["BANK-CAPITAL-001"],
    )
    balance_cents: int = Field(
        ...,
        description="Account balance in cents",
        examples=[1000000000],
    )
    balance_dollars: float = Field(
        ...,
        description="Account balance in dollars",
        examples=[10000000.0],
    )
    updated_at: datetime | None = Field(
        None,
        description="Last update timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, title="Bank Capital Balance")


class LogFileInfo(BaseModel):
    """Log file information schema."""

    filename: str = Field(
        ...,
        description="Log file name",
        examples=["info.log", "error.log", "access.log"],
    )
    size_bytes: int = Field(
        ...,
        description="File size in bytes",
        examples=[1048576],
    )
    modified_at: datetime = Field(
        ...,
        description="Last modification timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )

    model_config = ConfigDict(title="Log File Info")


class LogFileList(BaseModel):
    """Log file list schema."""

    files: list[LogFileInfo] = Field(
        ...,
        description="List of log files",
        examples=[
            [
                {
                    "filename": "info.log",
                    "size_bytes": 1048576,
                    "modified_at": "2025-01-01T00:00:00Z",
                },
                {
                    "filename": "error.log",
                    "size_bytes": 524288,
                    "modified_at": "2025-01-01T00:00:00Z",
                },
            ]
        ],
    )
    total: int = Field(..., description="Total number of log files", examples=[5])

    model_config = ConfigDict(title="Log File List")


class LogFileContent(BaseModel):
    """Log file content schema."""

    filename: str = Field(
        ...,
        description="Log file name",
        examples=["info.log"],
    )
    lines: list[str] = Field(
        ...,
        description="Log file lines",
        examples=[
            [
                "2025-01-01 00:00:00,000 - INFO - Application started",
                "2025-01-01 00:01:00,000 - INFO - User logged in",
            ]
        ],
    )
    total_lines: int = Field(
        ...,
        description="Total number of lines in the file",
        examples=[10000],
    )
    returned_lines: int = Field(
        ...,
        description="Number of lines returned",
        examples=[1000],
    )

    model_config = ConfigDict(title="Log File Content")


class LogFileDownloadRequest(BaseModel):
    """Log file download request schema."""

    filename: str = Field(
        ...,
        description="Log file name to download",
        examples=["error.log", "access.log", "debug.log"],
    )

    model_config = ConfigDict(title="Log File Download Request")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate log filename."""
        return InputValidator.validate_log_filename(v)


class TokenBlacklist(BaseModel):
    """Token blacklist schema."""

    blacklisted_tokens: list[str] = Field(
        ...,
        description="List of blacklisted tokens",
        examples=[
            [
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            ]
        ],
    )
    count: int = Field(..., description="Total number of blacklisted tokens", examples=[2])

    model_config = ConfigDict(title="Token Blacklist")


__all__ = [
    "BankCapitalBalance",
    "LogFileContent",
    "LogFileDownloadRequest",
    "LogFileInfo",
    "LogFileList",
    "TokenBlacklist",
    "UserList",
    "UserListItem",
    "UserRoleUpdate",
    "UserRoleUpdateResult",
    "UserUnlockResult",
]
