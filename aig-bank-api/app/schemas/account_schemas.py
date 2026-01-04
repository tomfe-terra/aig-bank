"""Account service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from .core import MoneyCents, MoneyDollars


class AccountRead(BaseModel):
    """Account read schema. Only USD currency is supported."""

    id: UUID = Field(
        ...,
        description="Unique account identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    number: str = Field(..., description="Account number (8-18 digits)", examples=["1234567890"])
    user_id: UUID = Field(
        ...,
        description="Owner user identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    balance_cents: MoneyCents = Field(..., description="Account balance in cents (USD)", examples=[150000])
    balance_dollars: MoneyDollars = Field(..., description="Account balance in dollars (USD)", examples=[1500.0])
    created_at: datetime = Field(..., description="Account creation timestamp", examples=["2025-01-01T00:00:00Z"])
    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )

    model_config = ConfigDict(from_attributes=True, title="Account")

    @field_serializer("id", "user_id")
    def serialize_uuid(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)

    @field_validator("balance_dollars", mode="before")
    @classmethod
    def calculate_balance_dollars(cls, v):
        """Calculate balance in dollars from cents."""
        return v


__all__ = [
    "AccountRead",
]
