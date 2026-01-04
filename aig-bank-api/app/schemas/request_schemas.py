"""Request service schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ..core.enums import CardBrand, RequestKind, RequestStatus, UserRole
from ..utils.validators import InputValidator
from .core import MoneyCents


class RequesterInfo(BaseModel):
    """Simplified user info for request responses."""

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

    model_config = ConfigDict(from_attributes=True, title="Requester Info")

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)


class Request(BaseModel):
    """Request schema."""

    id: UUID = Field(
        ...,
        description="Unique request identifier",
        examples=["bb0e8400-e29b-41d4-a716-446655440000"],
    )
    kind: RequestKind = Field(
        ...,
        description="Type of request",
        examples=[RequestKind.CREDIT_CARD, RequestKind.LOAN],
    )
    payload: dict[str, Any] = Field(
        ...,
        description="Request payload data",
        examples=[{"card_type": "VISA"}, {"principal_cents": 100000, "repayment_cycles": 24}],
    )
    status: RequestStatus = Field(
        ...,
        description="Request status",
        examples=[RequestStatus.PENDING, RequestStatus.APPROVED, RequestStatus.REJECTED],
    )
    requested_by: UUID = Field(
        ...,
        description="User ID who made the request",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    requester: RequesterInfo | None = Field(
        default=None,
        description="User information for the requester",
    )
    decided_by: UUID | None = Field(
        default=None,
        description="Banker ID who decided on the request",
        examples=["dd0e8400-e29b-41d4-a716-446655440000"],
    )
    decider: RequesterInfo | None = Field(
        default=None,
        description="Banker information for the decider",
    )
    decided_at: datetime | None = Field(
        default=None,
        description="When the decision was made",
        examples=["2025-01-01T01:00:00Z"],
    )
    created_at: datetime = Field(
        ...,
        description="Request creation timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )

    model_config = ConfigDict(from_attributes=True, title="Request")

    @field_serializer("id", "requested_by", "decided_by")
    def serialize_uuid_fields(self, value: UUID | None) -> str | None:
        """Convert UUID fields to strings."""
        if value is None:
            return None
        return str(value)


class RequestDecision(BaseModel):
    """Request decision schema."""

    message: str = Field(
        ...,
        description="Decision result message",
        examples=["Credit card request approved successfully", "Loan request approved and disbursed"],
    )
    request: Request = Field(..., description="Updated request")
    card: Any | None = Field(None, description="Created card (for CREDIT_CARD requests)")
    loan: Any | None = Field(None, description="Created loan (for LOAN requests)")
    disbursement_transaction: Any | None = Field(None, description="Disbursement transaction (for LOAN requests)")

    model_config = ConfigDict(title="Request Decision")


class RequestRejection(BaseModel):
    """Request rejection schema."""

    message: str = Field(
        ...,
        description="Rejection result message",
        examples=["Credit card request rejected", "Loan request rejected due to insufficient credit history"],
    )
    request: Request = Field(..., description="Updated request")

    model_config = ConfigDict(title="Request Rejection")


class LoanRequestCreate(BaseModel):
    """Loan request creation schema (non-profit bank: no interest, hourly repayments)."""

    principal_cents: MoneyCents = Field(
        ...,
        description="Loan amount in cents",
        examples=[100000, 500000],
    )
    repayment_cycles: int = Field(
        ...,
        description="Number of repayment cycles",
        examples=[24, 168, 720],
    )

    model_config = ConfigDict(title="Create Loan Request")

    @field_validator("principal_cents")
    @classmethod
    def validate_principal_cents(cls, v: int) -> int:
        """Validate principal amount is positive."""
        return InputValidator.validate_positive_amount(v, "Principal amount")

    @field_validator("repayment_cycles")
    @classmethod
    def validate_repayment_cycles(cls, v: int) -> int:
        """Validate repayment cycles (1 to 8760)."""
        return InputValidator.validate_range(v, min_val=1, max_val=8760, field_name="Repayment cycles")


class LoanRequest(BaseModel):
    """Loan request schema."""

    request: Request = Field(..., description="Created request")

    model_config = ConfigDict(title="Loan Request")


class CardRequestCreate(BaseModel):
    """Card request creation schema."""

    card_type: CardBrand = Field(
        ...,
        description="Card type/brand to request",
        examples=[CardBrand.VISA, CardBrand.MASTERCARD],
    )

    model_config = ConfigDict(title="Create Card Request")


class CardRequest(BaseModel):
    """Card request schema."""

    request: Request = Field(..., description="Created request")

    model_config = ConfigDict(title="Card Request")


class RequestList(BaseModel):
    """Request list schema."""

    requests: list[Request] = Field(
        ...,
        description="List of requests",
        examples=[
            [
                {
                    "id": "bb0e8400-e29b-41d4-a716-446655440000",
                    "kind": "CREDIT_CARD",
                    "payload": {"card_type": "VISA"},
                    "status": "PENDING",
                    "requested_by": "550e8400-e29b-41d4-a716-446655440000",
                    "decided_by": None,
                    "decided_at": None,
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ]
        ],
    )
    total: int = Field(..., description="Total number of requests", examples=[1])

    model_config = ConfigDict(title="Request List")


__all__ = [
    "CardRequest",
    "CardRequestCreate",
    "LoanRequest",
    "LoanRequestCreate",
    "Request",
    "RequestDecision",
    "RequestList",
    "RequestRejection",
    "RequesterInfo",
]
