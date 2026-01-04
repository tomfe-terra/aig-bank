"""Loan service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ..core.enums import LoanStatus
from .core import MoneyCents, MoneyDollars


class LoanRead(BaseModel):
    """Loan response schema for non-profit bank (0% interest, automatic hourly repayments)."""

    id: UUID = Field(
        ...,
        description="Unique loan identifier",
        examples=["cc0e8400-e29b-41d4-a716-446655440000"],
    )
    account_id: UUID = Field(
        ...,
        description="Account ID associated with this loan",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    principal_cents: MoneyCents = Field(..., description="Loan principal amount in cents", examples=[500000])
    principal_dollars: MoneyDollars = Field(..., description="Loan principal amount in dollars", examples=[5000.0])
    repayment_cycles: int = Field(..., description="Number of repayment cycles", examples=[24])
    installment_amount_cents: int = Field(..., description="Installment amount per cycle in cents (rounded up)", examples=[20834])
    paid_amount_cents: MoneyCents = Field(..., description="Amount repaid so far in cents", examples=[0])
    remaining_balance_cents: MoneyCents = Field(..., description="Remaining balance to repay in cents", examples=[500000])
    status: LoanStatus = Field(
        ...,
        description="Loan status",
        examples=[LoanStatus.PENDING, LoanStatus.APPROVED, LoanStatus.ACTIVE],
    )
    approved_by: UUID | None = Field(
        default=None,
        description="Banker who approved the loan",
        examples=["dd0e8400-e29b-41d4-a716-446655440000"],
    )
    next_repayment_at: datetime | None = Field(default=None, description="When next repayment is due", examples=["2025-01-01T01:00:00Z"])
    last_repayment_at: datetime | None = Field(default=None, description="When last repayment was made", examples=["2025-01-01T00:00:00Z"])
    version: int = Field(..., description="Version for optimistic concurrency control", examples=[1])
    created_at: datetime = Field(..., description="Loan creation timestamp", examples=["2025-01-01T00:00:00Z"])
    updated_at: datetime = Field(..., description="Loan last update timestamp", examples=["2025-01-01T00:00:00Z"])

    model_config = ConfigDict(from_attributes=True, title="Loan")

    @field_serializer("id", "account_id", "approved_by")
    def serialize_uuid_fields(self, value: UUID | None) -> str | None:
        """Convert UUID fields to strings."""
        if value is None:
            return None
        return str(value)

    @field_validator("principal_dollars", mode="before")
    @classmethod
    def calculate_principal_dollars(cls, v):
        """Calculate principal in dollars from cents."""
        return v


__all__ = [
    "LoanRead",
]
