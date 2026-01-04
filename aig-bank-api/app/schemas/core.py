"""Core/shared schemas used across multiple services."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

MoneyCents = int
MoneyDollars = float


class Money:
    """Money type for handling cents/dollars conversion."""

    @staticmethod
    def cents_to_dollars(cents: MoneyCents) -> MoneyDollars:
        """Convert cents to dollars."""
        return cents / 100.0

    @staticmethod
    def dollars_to_cents(dollars: MoneyDollars) -> MoneyCents:
        """Convert dollars to cents."""
        return int(dollars * 100)


class PaginationParams(BaseModel):
    """Pagination parameters."""

    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Number of items per page",
        examples=[50, 100],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip",
        examples=[0, 50],
    )
    cursor: str | None = Field(
        default=None,
        description="Cursor for next page",
        examples=["2025-01-01T00:00:00Z:770e8400-e29b-41d4-a716-446655440000"],
    )

    model_config = ConfigDict(title="Pagination Parameters")


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""

    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Number of items per page",
        examples=[50, 100],
    )
    cursor: str | None = Field(
        default=None,
        description="Cursor for next page (created_at:id format)",
        examples=["2025-01-01T00:00:00Z:770e8400-e29b-41d4-a716-446655440000"],
    )

    model_config = ConfigDict(title="Cursor Pagination Parameters")


class TransactionFilterParams(BaseModel):
    """Transaction filtering parameters."""

    account_id: str | None = Field(
        default=None,
        description="Filter by account ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    transaction_type: str | None = Field(
        default=None,
        description="Filter by transaction type",
        examples=["TRANSFER_OUT", "TRANSFER_IN", "CARD_PAYMENT"],
    )
    start_date: Any | None = Field(
        default=None,
        description="Filter from date",
        examples=["2025-01-01T00:00:00Z"],
    )
    end_date: Any | None = Field(
        default=None,
        description="Filter to date",
        examples=["2025-12-31T23:59:59Z"],
    )
    min_amount: MoneyCents | None = Field(
        default=None,
        description="Minimum amount in cents",
        examples=[10000],
    )
    max_amount: MoneyCents | None = Field(
        default=None,
        description="Maximum amount in cents",
        examples=[100000],
    )

    model_config = ConfigDict(title="Transaction Filter Parameters")


__all__ = [
    "CursorPaginationParams",
    "Money",
    "MoneyCents",
    "MoneyDollars",
    "PaginationParams",
    "TransactionFilterParams",
]
