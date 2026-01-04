"""API Key service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ..utils.validators import InputValidator
from .general import BaseUpdate


class APIKeyCreate(BaseModel):
    """API key creation parameters."""

    name: str = Field(
        ...,
        description="API key name",
        examples=["Production API Key", "Development Key", "Mobile App Key"],
    )
    description: str | None = Field(
        None,
        description="API key description",
        examples=["API key for production environment", "Development testing key"],
    )

    model_config = ConfigDict(title="Create API Key", description="API key creation parameters")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate API key name."""
        return InputValidator.validate_length(v, "name", "API key name")

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate API key description."""
        if v is None:
            return v
        return InputValidator.validate_length(v, "description", "API key description")


class APIKeyUpdate(BaseUpdate):
    """API key update parameters."""

    name: str | None = Field(
        None,
        description="Updated API key name",
        examples=["Updated Production Key", "Renamed Development Key"],
    )
    description: str | None = Field(
        None,
        description="Updated API key description",
        examples=["Updated description for production environment"],
    )

    model_config = ConfigDict(title="Update API Key", extra="allow")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate API key name."""
        if v is None:
            return v
        return InputValidator.validate_length(v, "name", "API key name")

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate API key description."""
        if v is None:
            return v
        return InputValidator.validate_length(v, "description", "API key description")


class APIKeyRead(BaseModel):
    """API key details."""

    id: UUID = Field(
        ...,
        description="API key ID (used for authentication)",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    name: str = Field(
        ...,
        description="API key name",
        examples=["Production API Key"],
    )
    description: str | None = Field(
        default=None,
        description="API key description",
        examples=["API key for production environment"],
    )
    user_id: UUID = Field(
        ...,
        description="User ID",
        examples=["f1e2d3c4-b5a6-7890-1234-567890abcdef"],
    )
    is_active: bool = Field(
        ...,
        description="Whether the API key is active",
        examples=[True],
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp",
        examples=["2025-10-31T12:00:00Z"],
    )
    last_used: datetime | None = Field(
        default=None,
        description="Last usage timestamp",
        examples=["2025-10-31T14:30:00Z"],
    )

    model_config = ConfigDict(from_attributes=True, title="API Key")

    @field_serializer("id", "user_id")
    def serialize_uuid(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)


class APIKeySecretRead(APIKeyRead):
    """API key & secret details."""

    secret: str = Field(
        ...,
        description="API key secret (only shown once at creation)",
        examples=["sk_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"],
    )

    model_config = ConfigDict(title="API Key with Secret", description="API key & secret details")


class APIKeyList(BaseModel):
    """List of API keys."""

    api_keys: list[APIKeyRead] = Field(
        ...,
        description="List of API keys",
        examples=[
            [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "name": "Production API Key",
                    "description": "API key for production environment",
                    "user_id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
                    "is_active": True,
                    "created_at": "2025-10-31T12:00:00Z",
                    "last_used": "2025-10-31T14:30:00Z",
                },
                {
                    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "name": "Development Key",
                    "description": "API key for development testing",
                    "user_id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
                    "is_active": True,
                    "created_at": "2025-10-30T10:00:00Z",
                    "last_used": None,
                },
            ]
        ],
    )
    total: int = Field(
        ...,
        description="Total number of API keys",
        examples=[2],
    )
    model_config = ConfigDict(from_attributes=True, title="API Keys List")


__all__ = [
    "APIKeyCreate",
    "APIKeyList",
    "APIKeyRead",
    "APIKeySecretRead",
    "APIKeyUpdate",
]
