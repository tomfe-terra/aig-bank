"""General purpose schemas used across the application."""

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """API response message with optional object ID."""

    message: str = Field(
        ...,
        description="Response message",
        examples=["Operation completed successfully", "Resource created", "Resource deleted"],
    )
    id: str | None = Field(
        default=None,
        description="ID of the affected resource",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )

    model_config = ConfigDict(title="Message")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(
        ...,
        description="Error type or code",
        examples=["InsufficientFunds", "NotFound", "ValidationError"],
    )
    details: str | None = Field(
        default=None,
        description="Detailed error message",
        examples=["balance 1200 < required 2500", "Account not found"],
    )
    request_id: str | None = Field(
        default=None,
        description="Request ID for tracking",
        examples=["req_abc123xyz789"],
    )

    model_config = ConfigDict(title="Error Response")


class BaseUpdate(BaseModel):
    """Base for update models."""

    def create_update_dict(self) -> dict:
        """Create a dictionary from the model."""
        return self.model_dump(exclude_unset=True, exclude=["id", "created_at", "updated_at"])

    model_config = ConfigDict(title="Base Update", extra="forbid")


__all__ = [
    "ErrorResponse",
    "Message",
]
