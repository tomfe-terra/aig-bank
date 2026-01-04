"""Card service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from ..core.enums import CardBrand, CardStatus, UserRole


class CardOwnerInfo(BaseModel):
    """Simplified user info for card owner in banker views."""

    id: UUID = Field(
        ...,
        description="User identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    username: str = Field(
        ...,
        description="Username",
        examples=["johndoe"],
    )
    first_name: str = Field(
        ...,
        description="First name",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        description="Last name",
        examples=["Doe"],
    )
    email: str | None = Field(
        None,
        description="Email address",
        examples=["john.doe@example.com"],
    )
    role: UserRole = Field(
        ...,
        description="User role",
        examples=[UserRole.USER],
    )

    model_config = ConfigDict(from_attributes=True, title="Card Owner Info")

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)


class CardRead(BaseModel):
    """Card response schema."""

    id: UUID = Field(
        ...,
        description="Unique card identifier",
        examples=["aa0e8400-e29b-41d4-a716-446655440000"],
    )
    account_id: UUID = Field(
        ...,
        description="Account ID associated with this card",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    last4: str = Field(..., description="Last 4 digits of the card number", examples=["1111"])
    brand: CardBrand = Field(
        ...,
        description="Card brand/network",
        examples=[CardBrand.VISA, CardBrand.MASTERCARD, CardBrand.DISCOVER],
    )
    exp_month: int = Field(..., description="Card expiration month", examples=[12])
    exp_year: int = Field(..., description="Card expiration year", examples=[2025])
    status: CardStatus = Field(
        ...,
        description="Card status",
        examples=[CardStatus.ACTIVE, CardStatus.CANCELLED, CardStatus.EXPIRED],
    )
    created_at: datetime = Field(..., description="Card creation timestamp", examples=["2025-01-01T00:00:00Z"])
    is_expired: bool = Field(..., description="Whether the card is expired", examples=[False])

    model_config = ConfigDict(from_attributes=True, title="Credit Card")

    @field_serializer("id", "account_id")
    def serialize_uuid_fields(self, value: UUID | None) -> str:
        """Convert UUID fields to strings."""
        if value is None:
            return ""
        return str(value)

    @field_serializer("last4")
    def serialize_last4(self, value: str) -> str:
        """Return the last 4 digits of the card number."""
        return value


class CardReveal(BaseModel):
    """Card full details reveal schema (including sensitive PAN and CVV)."""

    card_id: str = Field(
        ...,
        description="Card identifier",
        examples=["aa0e8400-e29b-41d4-a716-446655440000"],
    )
    pan: str = Field(
        ...,
        description="Full Primary Account Number (PAN)",
        examples=["4111111111111111"],
    )
    cvv: str = Field(
        ...,
        description="Card Verification Value",
        examples=["123"],
    )
    brand: str = Field(
        ...,
        description="Card brand",
        examples=["VISA", "MASTERCARD"],
    )
    exp_month: int = Field(..., description="Expiration month", examples=[12])
    exp_year: int = Field(..., description="Expiration year", examples=[2025])

    model_config = ConfigDict(title="Card Full Details Reveal")


class CardCancel(BaseModel):
    """Card cancellation schema."""

    message: str = Field(
        ...,
        description="Cancellation result message",
        examples=["Card cancelled successfully"],
    )
    card: CardRead = Field(..., description="Cancelled card")

    model_config = ConfigDict(title="Card Cancellation")


class BankerCardView(BaseModel):
    """Banker view of credit card with owner information."""

    id: UUID = Field(
        ...,
        description="Unique card identifier",
        examples=["aa0e8400-e29b-41d4-a716-446655440000"],
    )
    last4: str = Field(
        ...,
        description="Last 4 digits of the card number",
        examples=["1111"],
    )
    brand: CardBrand = Field(
        ...,
        description="Card brand/network",
        examples=[CardBrand.VISA, CardBrand.MASTERCARD],
    )
    status: CardStatus = Field(
        ...,
        description="Card status",
        examples=[CardStatus.ACTIVE, CardStatus.CANCELLED],
    )
    created_at: datetime = Field(
        ...,
        description="Card creation timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )
    owner: CardOwnerInfo = Field(
        ...,
        description="Card owner information",
    )

    model_config = ConfigDict(from_attributes=True, title="Banker Card View")

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)


class BankerCardList(BaseModel):
    """List of cards for banker view."""

    cards: list[BankerCardView] = Field(
        ...,
        description="List of credit cards",
    )
    total: int = Field(
        ...,
        description="Total number of cards",
        examples=[10],
    )

    model_config = ConfigDict(title="Banker Card List")


__all__ = [
    "BankerCardList",
    "BankerCardView",
    "CardCancel",
    "CardOwnerInfo",
    "CardRead",
    "CardReveal",
]
